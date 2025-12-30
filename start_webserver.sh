#!/bin/bash
# TrendRadar Web 服务器启动脚本

# 切换到项目目录
cd "$(dirname "$0")"

# 检查端口是否已被占用
PORT=8080
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "端口 $PORT 已被占用，停止旧进程..."
    kill $(lsof -t -i:$PORT) 2>/dev/null
    sleep 2
fi

# 启动 Web 服务器
echo "启动 Web 服务器在端口 $PORT..."
cd output
nohup python3 -m http.server $PORT --bind 0.0.0.0 > /tmp/trendradar_webserver.log 2>&1 &

# 保存 PID
echo $! > /tmp/trendradar_webserver.pid

echo "Web 服务器已启动！"
echo "访问: http://localhost:$PORT"
echo "日志: /tmp/trendradar_webserver.log"
echo "停止: kill \$(cat /tmp/trendradar_webserver.pid)"
