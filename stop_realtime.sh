#!/bin/bash
# 停止实时监控

if [ ! -f /tmp/trendradar_realtime.pid ]; then
    echo "⚠️  实时监控未运行"
    exit 0
fi

PID=$(cat /tmp/trendradar_realtime.pid)

if ps -p $PID > /dev/null 2>&1; then
    echo "🛑 停止实时监控 (PID: $PID)..."
    kill $PID
    sleep 2

    # 强制结束子进程
    pkill -P $PID 2>/dev/null || true

    if ps -p $PID > /dev/null 2>&1; then
        echo "强制终止..."
        kill -9 $PID 2>/dev/null || true
    fi

    rm -f /tmp/trendradar_realtime.pid
    echo "✅ 实时监控已停止"
else
    echo "⚠️  进程不存在，清理 PID 文件"
    rm -f /tmp/trendradar_realtime.pid
fi
