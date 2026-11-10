#!/usr/bin/env bash

SEARCH_API_ADDRESS="${SEARCH_API_ADDRESS:-http://127.0.0.1:7860}"
API_TOKEN="${API_TOKEN:-connect-care}"
USER_API_ADDRESS="${USER_API_ADDRESS:-http://127.0.0.1:8000}"
USER_ID="${USER_ID:-user_001}"
QUERY="${QUERY:-apple dessert for 2 people, no honey}"
TOP_K="${TOP_K:-3}"
LANGUAGE="${LANGUAGE:-en}"
OUTPUT_LANGUAGE="${OUTPUT_LANGUAGE:-en}"
LLM_API_ADDRESS="${LLM_API_ADDRESS:-http://127.0.0.1:3960}"
MODEL="${MODEL:-cyankiwi/gemma-4-26B-A4B-it-AWQ-4bit}"
LATEST_CALORIES="${LATEST_CALORIES:-}"

if [ -z "$LATEST_CALORIES" ]; then
  # Step 1: Load the user's latest calorie intake.
  if USER_SUMMARY_RESPONSE=$(curl --silent --show-error --fail --connect-timeout 3 --max-time 5 "$USER_API_ADDRESS/api/users/$USER_ID/summary") &&
    LATEST_CALORIES=$(jq -er '.latest_metrics.calories_in | if type == "number" then . elif type == "string" then tonumber else error("not numeric") end | select(. >= 0)' <<< "$USER_SUMMARY_RESPONSE"); then
    :
  else
    echo "Trajectory calories unavailable for $USER_ID; using 0." >&2
    LATEST_CALORIES=0
  fi
else
  LATEST_CALORIES=$(jq -en --arg value "$LATEST_CALORIES" '$value | tonumber | select(. >= 0)') || {
    echo "LATEST_CALORIES must be a non-negative number." >&2
    exit 1
  }
fi

# Step 2: Search for a recipe
EVENT_ID=$(
  curl --silent --show-error --fail -X POST "$SEARCH_API_ADDRESS/gradio_api/call/v2/search" \
    -H "Content-Type: application/json" \
    -H "X-Api-Token: $API_TOKEN" \
    -d "$(jq -n \
      --arg query "$QUERY" \
      --arg language "$LANGUAGE" \
      --argjson top_k "$TOP_K" \
      '{query: $query, top_k: $top_k, language: $language}')" \
  | jq -r '.event_id // .[0]'
)

if [ -z "$EVENT_ID" ] || [ "$EVENT_ID" = "null" ]; then
  echo "Search request did not return an event ID." >&2
  exit 1
fi

RECIPES=$(
  curl --silent --show-error --fail -N "$SEARCH_API_ADDRESS/gradio_api/call/v2/search/$EVENT_ID" \
  | grep '^data:' \
  | sed 's/^data: //' \
  | jq -c '.[0] | if (type == "array") and (length > 0) and (.[0] | type == "array") then .[0] else . end'
)

if [ -z "$RECIPES" ] || [ "$RECIPES" = "null" ] || [ "$(echo "$RECIPES" | jq 'length')" = "0" ]; then
  echo "Search did not return any recipes." >&2
  exit 1
fi

# Step 3: Ask vLLM to personalize each recipe and return JSON with the same schema.
UPDATED_RECIPE_RESPONSE=$(curl --silent --show-error --fail "$LLM_API_ADDRESS/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg recipes "$RECIPES" \
    --arg query "$QUERY" \
    --arg latest_calories "$LATEST_CALORIES" \
    --arg output_language "$OUTPUT_LANGUAGE" \
    '{
      model: $model,
      temperature: 0.1,
      max_tokens: 2000,
      messages: [
        {
          role: "system",
          content: ("You personalize recipes using the user request and the latest calorie intake. The input is a JSON array of recipes. Return only a valid JSON array with the same length and order, one personalized recipe object per input recipe, each keeping the same fields: title, servings, ingredient_sections, preparation, preparation_time, notes, source_language, target_language, and id. Preserve the original source_language of each recipe and set target_language to \"" + $output_language + "\" for the updated recipe output only. Respect explicit user requests first. Use the calorie value only as a general personalization signal; do not diagnose medical conditions or invent facts. Put explanations of substitutions in notes. Do not use Markdown or code fences.")
        },
        {
          role: "user",
          content: ("User request:\n" + $query + "\n\nLatest calorie intake: " + $latest_calories + " kcal\n\nUpdated recipe target language: " + $output_language + "\n\nRecipes JSON array:\n" + $recipes)
        }
      ]
    }' \
    --arg model "$MODEL" \
  )")
UPDATED_RECIPE_RESPONSE=$(printf '%s' "$UPDATED_RECIPE_RESPONSE" | perl -0777 -pe 's/[\x00-\x1f]//g')

UPDATED_RECIPE=$(python3 - "$UPDATED_RECIPE_RESPONSE" <<'PY'
import json
import re
import sys

payload = sys.argv[1]
try:
    data = json.loads(payload)
except json.JSONDecodeError:
    print('', end='')
    raise SystemExit(0)

content = ''
try:
    content = data['choices'][0]['message']['content']
except Exception:
    print('', end='')
    raise SystemExit(0)

text = str(content).strip()
text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
text = re.sub(r'\s*```\s*$', '', text, flags=re.IGNORECASE)
text = text.replace('\u0000', '')
text = text.replace('\x00', '')

start = text.find('[')
if start == -1:
    print('', end='')
    raise SystemExit(0)

in_string = False
escaped = False
depth = 0
end = None
for i in range(start, len(text)):
    ch = text[i]
    if in_string:
        if escaped:
            escaped = False
        elif ch == '\\':
            escaped = True
        elif ch == '"':
            in_string = False
        continue

    if ch == '"':
        in_string = True
    elif ch == '[':
        depth += 1
    elif ch == ']':
        depth -= 1
        if depth == 0:
            end = i + 1
            break

if end is None:
    text = text[start:]
else:
    text = text[start:end]

# Remove stray words immediately before a closing bracket, e.g. "} ways]" or "] ways]"
text = re.sub(r'}\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9_ -]*\s*(?=[,\]])', '}', text)
text = re.sub(r']\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9_ -]*\s*(?=[,\]])', ']', text)
text = re.sub(r'",\s*"id"\s*:\s*"[^"]+"\s*,\s*"id"\s*:', '","id":', text)

try:
    json.loads(text)
    print(text)
except json.JSONDecodeError:
    print('', end='')
PY
)

if [ -z "$UPDATED_RECIPE" ]; then
  echo "vLLM did not return a valid response." >&2
  echo "$UPDATED_RECIPE_RESPONSE" >&2
  exit 1
fi

echo "$UPDATED_RECIPE" | jq -e . >/dev/null || {
  echo "vLLM returned invalid recipe JSON." >&2
  echo "$UPDATED_RECIPE" >&2
  exit 1
}

jq -n \
  --argjson recipes "$RECIPES" \
  --argjson latest_calories "$LATEST_CALORIES" \
  --argjson updated_recipes "$UPDATED_RECIPE" \
  '{recipes: $recipes, latest_calories_in: $latest_calories, updated_recipes: $updated_recipes}'