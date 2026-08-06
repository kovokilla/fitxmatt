#!/bin/bash
# Send the daily LinkedIn post to kovokilla@gmail.com via the AgentMail MCP.
# AgentMail inbox: fitxmatt@agentmail.to (inbox_id == email).
# Uses `hermes chat` which has the agentmail MCP tools loaded (verified working).
set -e
SUBJECT="${1:-FitXMatt LinkedIn post}"
BODY_FILE="${2:-/tmp/li_post_today.txt}"
TO="kovokilla@gmail.com"
INBOX="fitxmatt@agentmail.to"

if [ ! -f "$BODY_FILE" ]; then
  echo "EMAIL_SKIPPED (body file missing: $BODY_FILE)"
  exit 0
fi

# hermes chat has the agentmail MCP tools; ask it to send via send_message.
OUT=$(hermes chat -q "Use the agentmail MCP tool send_message to send an email with inbox_id '$INBOX', to '$TO', subject $(printf '%q' "$SUBJECT"), and text read from the file $BODY_FILE. Report only the tool's success/failure response." 2>&1) || true

if echo "$OUT" | grep -qiE "messageId|threadId|succeeded|sent"; then
  echo "EMAIL_SENT"
else
  echo "EMAIL_FAIL — agentmail send unclear; tail of output:"
  echo "$OUT" | tail -5
fi
