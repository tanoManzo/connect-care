QUERY="cheesecake"
TOP_K=1
API_TOKEN="connect-care"
ADDRESS="https://xxxxx.gradio.live"

EVENT_ID=$(
  curl -X POST $ADDRESS/gradio_api/call/v2/search \
    -s \
    -H "Content-Type: application/json" \
    -H "X-Api-Token: $API_TOKEN" \
    -d "{\"query\": \"$QUERY\", \"top_k\": $TOP_K, \"language\": \"en\"}" \
  | awk -F'"' '{print $4}'
)

curl -N $ADDRESS/gradio_api/call/v2/search/$EVENT_ID \
  | grep '^data:' \
  | sed 's/^data: //' \
  | jq -r '.[0]'