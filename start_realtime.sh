#!/bin/bash
# 启动实时监控（后台运行）

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 加载 .env 配置文件
if [ -f .env ]; then
    echo "📋 加载配置文件 .env..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# 检查是否已在运行
if [ -f /tmp/trendradar_realtime.pid ]; then
    OLD_PID=$(cat /tmp/trendradar_realtime.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "⚠️  实时监控已在运行 (PID: $OLD_PID)"
        echo "如需重启，请先执行: ./stop_realtime.sh"
        exit 1
    fi
fi

# 检查飞书配置
if [ -z "$FEISHU_WEBHOOK_URL" ]; then
    echo "❌ 错误: 未设置飞书 Webhook URL"
    echo ""
    echo "请在 .env 文件中配置或设置环境变量"
    exit 1
fi

echo "🚀 启动实时监控..."

# 后台运行
nohup ./realtime_monitor.sh > /dev/null 2>&1 &

# 保存 PID
echo $! > /tmp/trendradar_realtime.pid

sleep 2

if ps -p $(cat /tmp/trendradar_realtime.pid) > /dev/null 2>&1; then
    echo "✅ 实时监控已启动！"
    echo ""
    echo "PID: $(cat /tmp/trendradar_realtime.pid)"
    echo "日志: tail -f /tmp/trendradar_realtime.log"
    echo "停止: ./stop_realtime.sh"
    echo ""
    echo "访问报告: http://localhost:8080"
else
    echo "❌ 启动失败，请查看日志"
    cat /tmp/trendradar_realtime.log | tail -20
fi
