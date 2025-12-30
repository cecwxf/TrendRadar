#!/bin/bash
# TrendRadar 实时监控脚本 - 每 10 秒运行一次

# 项目目录
PROJECT_DIR="/home/cecwxf/workspace/agent_ref/TrendRadar"
cd "$PROJECT_DIR"

# 加载 .env 配置文件
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 飞书 Webhook URL（从环境变量获取）
export FEISHU_WEBHOOK_URL="${FEISHU_WEBHOOK_URL:-}"

# 代理配置（可被 .env 覆盖）
export HTTP_PROXY="${HTTP_PROXY:-http://127.0.0.1:7000}"
export HTTPS_PROXY="${HTTPS_PROXY:-http://127.0.0.1:7000}"

# 日志文件
LOG_FILE="/tmp/trendradar_realtime.log"

# 运行间隔（秒）
INTERVAL=10

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查飞书配置
if [ -z "$FEISHU_WEBHOOK_URL" ]; then
    echo -e "${RED}错误: 未配置 FEISHU_WEBHOOK_URL${NC}"
    echo "请执行: export FEISHU_WEBHOOK_URL='https://open.feishu.cn/open-apis/bot/v2/hook/xxx'"
    exit 1
fi

log "=========================================="
log "TrendRadar 实时监控启动"
log "运行间隔: ${INTERVAL} 秒"
log "飞书通知: 已配置"
log "按 Ctrl+C 停止"
log "=========================================="

# 运行计数
count=0

# 捕获 Ctrl+C
trap 'log "监控已停止"; exit 0' INT TERM

# 主循环
while true; do
    count=$((count + 1))

    log "第 $count 次运行..."

    # 运行爬虫
    python3 -m trendradar 2>&1 | tee -a "$LOG_FILE"

    exit_code=$?

    if [ $exit_code -eq 0 ]; then
        log "${GREEN}✓ 运行成功${NC}"
    else
        log "${RED}✗ 运行失败 (退出码: $exit_code)${NC}"
    fi

    log "等待 ${INTERVAL} 秒..."
    sleep $INTERVAL
done
