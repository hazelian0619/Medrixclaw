#!/bin/bash
# Daily check for OpenClaw Scientific Skill updates
# Designed to run at 08:00 Beijing time (CST/UTC+8)
# Can be scheduled via cron hourly - will only execute at the right time

set -e

# Time check: only run at Beijing time 08:00 (with 1 hour tolerance)
BEIJING_HOUR=$(TZ='Asia/Shanghai' date +%H)
if [ "$BEIJING_HOUR" != "08" ]; then
    echo "⏭️  Skipping: current Beijing time is $(TZ='Asia/Shanghai' date '+%H:%M')"
    exit 0
fi

# Configuration
SKILL_DIR="/home/astran/.openclaw/skills/scientific"
SYNC_SCRIPT="$SKILL_DIR/scripts/sync_upstream.py"
LOG_FILE="/tmp/scientific_skill_check.log"
TELEGRAM_CHAT_ID="-5216536819"

# Logging
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================"
echo "📅 Daily Scientific Skill Check"
echo "   Time: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "========================================"

cd "$SKILL_DIR"

# Check for updates
echo ""
echo "🔍 Checking for upstream updates..."

CHECK_OUTPUT=$(python3 "$SYNC_SCRIPT" --check 2>&1)
CHECK_EXIT_CODE=$?

echo "$CHECK_OUTPUT"

# Determine if updates are available
if echo "$CHECK_OUTPUT" | grep -q "Already up to date"; then
    STATUS="✅ 无更新"
    NEEDS_SYNC=false
elif echo "$CHECK_OUTPUT" | grep -q "new commits"; then
    COMMITS_COUNT=$(echo "$CHECK_OUTPUT" | grep -oP '\d+(?= new commits)' || echo "数个")
    STATUS="🔄 发现 $COMMITS_COUNT 个新提交"
    NEEDS_SYNC=true
else
    STATUS="⚠️ 检查状态未知"
    NEEDS_SYNC=false
fi

# Prepare Telegram message
MESSAGE="🔬 **Scientific Skill 每日检查报告**

$STATUS

📅 检查时间: $(date -u '+%Y-%m-%d %H:%M UTC')
🔗 上游仓库: [K-Dense-AI/claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills)"

if [ "$NEEDS_SYNC" = true ]; then
    MESSAGE="$MESSAGE

💡 建议执行同步以获取最新更新。"
fi

# Send to Telegram via OpenClaw gateway
GATEWAY_URL="${OPENCLAW_GATEWAY_URL:-http://127.0.0.1:18789}"
GATEWAY_TOKEN="${OPENCLAW_GATEWAY_TOKEN:-}"

if curl -s "$GATEWAY_URL/status" > /dev/null 2>&1; then
    echo ""
    echo "📤 发送通知到 Telegram..."
    
    AUTH_HEADER=""
    if [ -n "$GATEWAY_TOKEN" ]; then
        AUTH_HEADER="-H \"Authorization: Bearer $GATEWAY_TOKEN\""
    fi
    
    # Use message tool through gateway
    curl -s -X POST "$GATEWAY_URL/message" \
        -H "Content-Type: application/json" \
        $AUTH_HEADER \
        -d "{
            \"action\": \"send\",
            \"channel\": \"telegram\",
            \"target\": \"$TELEGRAM_CHAT_ID\",
            \"message\": $(echo "$MESSAGE" | jq -Rs .)
        }" > /dev/null
    
    echo "✅ 通知已发送"
else
    echo "⚠️ OpenClaw gateway 未运行，无法发送通知"
fi

echo ""
echo "========================================"
echo "✅ 检查完成"
echo "========================================"
