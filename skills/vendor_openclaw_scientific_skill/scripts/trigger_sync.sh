#!/bin/bash
# Trigger sync via OpenClaw subagent

# Configuration
GATEWAY_URL="${OPENCLAW_GATEWAY_URL:-http://127.0.0.1:18789}"
GATEWAY_TOKEN="${OPENCLAW_GATEWAY_TOKEN:-}"

# Skill directory
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "🚀 Spawning OpenClaw subagent for sync..."
echo "   Skill dir: $SKILL_DIR"

# Check if gateway is running
if ! curl -s "$GATEWAY_URL/status" > /dev/null 2>&1; then
    echo "❌ OpenClaw gateway not running at $GATEWAY_URL"
    echo "   Start with: openclaw gateway start"
    exit 1
fi

# Prepare auth header
AUTH_HEADER=""
if [ -n "$GATEWAY_TOKEN" ]; then
    AUTH_HEADER="-H \"Authorization: Bearer $GATEWAY_TOKEN\""
fi

# Spawn subagent
RESPONSE=$(curl -s -X POST "$GATEWAY_URL/sessions/spawn" \
    -H "Content-Type: application/json" \
    $AUTH_HEADER \
    -d "{
        \"task\": \"Sync the OpenClaw Scientific Skill with upstream Claude Scientific Skills. 
        Steps:
        1. Check https://github.com/K-Dense-AI/claude-scientific-skills for recent changes
        2. Analyze what's new or changed
        3. Update the local skill files accordingly:
           - SKILL.md if core structure changed
           - references/*.md for domain updates
           - scripts/*.py for new utilities
        4. Keep changes minimal and focused
        5. Write a summary of what was updated
        
        Skill directory: $SKILL_DIR\",
        \"runtime\": \"subagent\",
        \"cwd\": \"$SKILL_DIR\",
        \"mode\": \"run\",
        \"runTimeoutSeconds\": 300
    }")

echo ""
echo "✅ Subagent spawned!"
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
