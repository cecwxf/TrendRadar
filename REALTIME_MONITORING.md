# ⚡ 实时监控部署指南（10 秒/次 + 飞书通知）

## 🎯 功能说明

- **运行频率**：每 10 秒运行一次
- **通知方式**：飞书机器人推送
- **运行方式**：后台持续运行
- **数据展示**：http://localhost:8080

---

## 🚀 快速部署（3 步）

### 步骤 1：获取飞书 Webhook URL

1. **打开飞书群聊**
2. 点击右上角 **···** → **设置** → **群机器人**
3. 点击 **添加机器人** → **自定义机器人**
4. 设置机器人名称：`TrendRadar 监控`
5. **复制 Webhook URL**：
   ```
   https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx
   ```

---

### 步骤 2：配置 Webhook URL

**方法 A：临时配置（推荐快速测试）**

```bash
cd /home/cecwxf/workspace/agent_ref/TrendRadar
export FEISHU_WEBHOOK_URL='https://open.feishu.cn/open-apis/bot/v2/hook/你的webhook'
```

**方法 B：永久配置（推荐生产环境）**

编辑 `~/.bashrc` 或 `~/.zshrc`：

```bash
echo 'export FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/你的webhook"' >> ~/.bashrc
source ~/.bashrc
```

**方法 C：配置文件（最推荐）**

创建 `.env` 文件：

```bash
cat > .env <<EOF
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/你的webhook
HTTP_PROXY=http://127.0.0.1:7000
HTTPS_PROXY=http://127.0.0.1:7000
EOF
```

---

### 步骤 3：启动实时监控

```bash
./start_realtime.sh
```

---

## 📊 管理命令

### 查看运行状态

```bash
ps aux | grep realtime_monitor
```

### 查看实时日志

```bash
tail -f /tmp/trendradar_realtime.log
```

### 停止监控

```bash
./stop_realtime.sh
```

### 重启监控

```bash
./stop_realtime.sh && ./start_realtime.sh
```

---

## ⚙️ 调整运行频率

编辑 `realtime_monitor.sh`，修改第 16 行：

```bash
# 运行间隔（秒）
INTERVAL=10   # 改为其他值

# 示例：
INTERVAL=30   # 30 秒
INTERVAL=60   # 1 分钟
INTERVAL=300  # 5 分钟
```

修改后重启生效：

```bash
./stop_realtime.sh
./start_realtime.sh
```

---

## ⚠️ 重要提示

### 关于 10 秒频率

**优点**：
- ✅ 极高的实时性
- ✅ 第一时间获取热点

**风险**：
- ⚠️ 可能被目标网站限流/封禁
- ⚠️ 浪费资源（新闻不会 10 秒更新）
- ⚠️ 飞书消息过多（可能被折叠）

**建议频率**：
- **1-3 分钟**：适合重大事件监控
- **5-10 分钟**：平衡实时性和稳定性
- **30-60 分钟**：日常监控

---

## 🔧 高级配置

### 限制推送时间窗口

编辑 `config/config.yaml`：

```yaml
notification:
  push_window:
    enabled: true
    start_time: "08:00"  # 开始时间
    end_time: "22:00"    # 结束时间
    once_per_day: false  # 不限制每天只推送一次
```

这样只在工作时间推送通知。

---

### 增量模式（只推送新增）

编辑 `config/config.yaml`：

```yaml
crawler:
  report_mode: "incremental"  # 只推送新增新闻
```

这样避免重复推送相同新闻。

---

### 关键词过滤

编辑 `config/config.yaml`，配置只关注特定关键词：

```yaml
keywords:
  frequency_words:
    - "人工智能"
    - "科技"
    - "特斯拉"
    # ... 只推送包含这些关键词的新闻
```

---

## 📈 监控面板

### 访问 Web 界面

```
http://localhost:8080
```

实时查看：
- 最新新闻热点
- 加密货币价格
- 股票行情
- 历史报告

### 自动刷新

在浏览器安装自动刷新插件，设置每 10 秒刷新页面。

---

## 🛠️ 故障排查

### 问题 1：启动失败

**检查飞书 Webhook**：

```bash
# 测试 Webhook 是否有效
curl -X POST "$FEISHU_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{"msg_type":"text","content":{"text":"测试消息"}}'
```

应该返回：`{"code":0}`

---

### 问题 2：没有收到通知

**原因**：
- 飞书 Webhook 配置错误
- 网络问题
- 消息被折叠

**解决**：

```bash
# 查看日志中的错误信息
tail -f /tmp/trendradar_realtime.log | grep -i "error\|fail"
```

---

### 问题 3：CPU 占用过高

**原因**：10 秒太频繁

**解决**：

1. 增加运行间隔（改为 30-60 秒）
2. 减少监控平台数量
3. 禁用不需要的功能（如 AI 分析）

---

### 问题 4：被网站封禁

**现象**：
- 日志显示 403/429 错误
- 数据获取失败

**解决**：

1. **增加间隔**：改为 1-5 分钟
2. **启用代理**：配置多个代理轮换
3. **减少平台**：只监控重要平台

---

## 📊 性能数据

| 频率 | CPU 占用 | 带宽消耗 | 被封风险 |
|-----|---------|---------|---------|
| 10 秒 | ~30% | ~100MB/天 | ⚠️ 高 |
| 30 秒 | ~15% | ~50MB/天 | ⚠️ 中 |
| 1 分钟 | ~8% | ~30MB/天 | ✅ 低 |
| 5 分钟 | ~3% | ~10MB/天 | ✅ 极低 |

---

## 🎯 推荐配置

### 配置 1：激进监控（重大事件）

```bash
INTERVAL=30  # 30 秒
报告模式: incremental  # 只推送新增
推送窗口: 全天
```

### 配置 2：平衡监控（日常使用）

```bash
INTERVAL=300  # 5 分钟
报告模式: incremental
推送窗口: 08:00-22:00
```

### 配置 3：温和监控（低频）

```bash
INTERVAL=1800  # 30 分钟
报告模式: current
推送窗口: 09:00-18:00
```

---

## 🚀 开机自启动

### 使用 systemd（推荐）

创建服务文件 `/etc/systemd/system/trendradar-realtime.service`：

```ini
[Unit]
Description=TrendRadar Realtime Monitor
After=network.target

[Service]
Type=simple
User=cecwxf
WorkingDirectory=/home/cecwxf/workspace/agent_ref/TrendRadar
Environment="FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
Environment="HTTP_PROXY=http://127.0.0.1:7000"
Environment="HTTPS_PROXY=http://127.0.0.1:7000"
ExecStart=/home/cecwxf/workspace/agent_ref/TrendRadar/realtime_monitor.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable trendradar-realtime
sudo systemctl start trendradar-realtime
```

---

## 🎉 部署完成！

现在执行：

```bash
# 1. 设置飞书 Webhook
export FEISHU_WEBHOOK_URL='你的webhook'

# 2. 启动监控
./start_realtime.sh

# 3. 查看日志
tail -f /tmp/trendradar_realtime.log

# 4. 访问报告
# 浏览器打开: http://localhost:8080
```

**期待结果**：
- ✅ 每 10 秒运行一次爬虫
- ✅ 飞书实时推送新闻
- ✅ Web 界面实时更新
- ✅ 后台稳定运行

---

## 🆘 获取帮助

- **查看日志**：`tail -f /tmp/trendradar_realtime.log`
- **测试飞书**：见"故障排查"章节
- **停止监控**：`./stop_realtime.sh`
