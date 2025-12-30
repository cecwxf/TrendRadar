#!/bin/bash
# 测试飞书 Webhook 是否配置正确

# 检查环境变量
if [ -z "$FEISHU_WEBHOOK_URL" ]; then
    echo "❌ 未设置 FEISHU_WEBHOOK_URL"
    echo ""
    echo "请先执行："
    echo "  export FEISHU_WEBHOOK_URL='https://open.feishu.cn/open-apis/bot/v2/hook/xxx'"
    echo ""
    echo "或者作为参数传入："
    echo "  ./test_feishu.sh 'https://open.feishu.cn/open-apis/bot/v2/hook/xxx'"
    exit 1
fi

# 如果有参数，使用参数作为 Webhook URL
if [ -n "$1" ]; then
    FEISHU_WEBHOOK_URL="$1"
fi

echo "🧪 测试飞书 Webhook..."
echo "URL: $FEISHU_WEBHOOK_URL"
echo ""

# 发送测试消息
response=$(curl -s -X POST "$FEISHU_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "msg_type": "text",
    "content": {
      "text": "🎉 TrendRadar 实时监控测试\n\n✅ 飞书通知配置成功！\n⏰ 测试时间: '"$(date '+%Y-%m-%d %H:%M:%S')"'"
    }
  }')

echo "响应: $response"
echo ""

# 检查响应
if echo "$response" | grep -q '"code":0'; then
    echo "✅ 测试成功！请检查飞书群聊是否收到消息"
    echo ""
    echo "下一步："
    echo "  1. 启动实时监控: ./start_realtime.sh"
    echo "  2. 查看日志: tail -f /tmp/trendradar_realtime.log"
    exit 0
else
    echo "❌ 测试失败！"
    echo ""
    echo "可能原因："
    echo "  1. Webhook URL 错误"
    echo "  2. 网络连接问题"
    echo "  3. 飞书机器人已被删除"
    echo ""
    echo "请检查 Webhook URL 是否正确"
    exit 1
fi
