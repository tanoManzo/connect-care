#!/bin/sh
set -eu

ADDRESS=${ADDRESS:-https://tangy-pots-relax.loca.lt}
USER_ID="user_001"
QUERY="apple dessert for 2 people, no honey"
OUTPUT_LANGUAGE=${OUTPUT_LANGUAGE:-en}
TOP_K=4

EVENT_ID=$(
  curl --silent --show-error --fail --max-time 30 \
    -X POST "$ADDRESS/gradio_api/call/run_recipe_search" \
    -H "Content-Type: application/json" \
    -H "bypass-tunnel-reminder: true" \
    -d "$(jq -n --arg user_id "$USER_ID" --arg query "$QUERY" \
      --arg output_language "$OUTPUT_LANGUAGE" --argjson top_k "$TOP_K" \
      '{data: [$user_id, $query, $output_language, $top_k]}')" \
    | jq -er '.event_id'
)

RESPONSE=$(curl --silent --show-error --fail --max-time 240 -N \
  -H "bypass-tunnel-reminder: true" \
  "$ADDRESS/gradio_api/call/run_recipe_search/$EVENT_ID")
printf '%s\n' "$RESPONSE" | sed -n 's/^data: //p' \
  | jq -es 'map(select(type == "array" and (.[0] | type == "object") and (.[0] | has("updated_recipe")))) | if length > 0 then last[0] else error("Recommendation failed; check server logs") end'