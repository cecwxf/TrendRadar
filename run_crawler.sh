#!/bin/bash
# TrendRadar 自动运行脚本

# 切换到项目目录
cd "$(dirname "$0")"

# 激活虚拟环境（如果使用）
# source venv/bin/activate

# 设置代理（如果需要）
export HTTP_PROXY="http://127.0.0.1:7000"
export HTTPS_PROXY="http://127.0.0.1:7000"

# 运行爬虫
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting TrendRadar crawler..."
python3 -m trendradar

# 检查退出状态
if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Crawler completed successfully"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Crawler failed with exit code $?"
fi
