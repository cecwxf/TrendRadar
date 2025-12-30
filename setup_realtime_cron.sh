#!/bin/bash
# 设置实时抓取（高频模式）

echo "配置实时抓取 cron 任务..."

# 备份现有 crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true

# 创建新的 crontab（每 5 分钟运行一次）
(crontab -l 2>/dev/null | grep -v "run_crawler.sh"; echo "*/5 * * * * /home/cecwxf/workspace/agent_ref/TrendRadar/run_crawler.sh >> /tmp/trendradar_cron.log 2>&1") | crontab -

echo "✅ 实时抓取已配置！"
echo ""
echo "运行频率: 每 5 分钟"
echo "日志文件: /tmp/trendradar_cron.log"
echo ""
echo "其他频率选项："
echo "- 每 1 分钟: */1 * * * *"
echo "- 每 3 分钟: */3 * * * *"
echo "- 每 10 分钟: */10 * * * *"
echo "- 每 30 分钟: */30 * * * *"
echo ""
echo "查看 cron 任务: crontab -l"
echo "查看日志: tail -f /tmp/trendradar_cron.log"
