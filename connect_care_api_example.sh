QUERY="${QUERY:-apple dessert for 2 people}"
TOP_K="${TOP_K:-3}"
LANGUAGE="${LANGUAGE:-en}"
ADDRESS="${ADDRESS:-https://ready-jobs-reply.loca.lt}"
API_TOKEN="${API_TOKEN:-connect-care}"

EVENT_ID=$(
  curl -sS -X POST "$ADDRESS/gradio_api/call/v2/search" \
    -H "Content-Type: application/json" \
    -H "X-Api-Token: $API_TOKEN" \
    -d "$(jq -n \
      --arg query "$QUERY" \
      --arg language "$LANGUAGE" \
      --argjson top_k "$TOP_K" \
      '{query: $query, top_k: $top_k, language: $language}')" \
  | jq -er '.event_id // .[0]'
)

curl -sSN "$ADDRESS/gradio_api/call/v2/search/$EVENT_ID" \
  | grep '^data:' \
  | sed 's/^data: //' \
  | jq -r '.[0]'
