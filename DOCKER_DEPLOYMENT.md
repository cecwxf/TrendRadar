# 🐳 TrendRadar Docker 部署指南

## 🎯 优势

相比 GitHub Actions：
- ✅ 更稳定可靠，不受 fork 仓库限制
- ✅ 内置 Web 服务器，可直接访问报告
- ✅ 支持自定义定时任务
- ✅ 可部署在本地/VPS，完全掌控
- ✅ 支持实时查看日志

---

## 🚀 快速部署（3 步）

### 步骤 1：配置通知渠道（必需）

编辑 `docker/.env` 文件，**至少配置一个通知渠道**：

```bash
# 方式 1：飞书
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-url

# 方式 2：钉钉
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=your-token

# 方式 3：企业微信
WEWORK_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key
```

**重要**：不配置通知渠道会跳过数据采集！

---

### 步骤 2：启动 Docker 容器

```bash
cd docker
docker-compose up -d
```

容器会自动：
- ✅ 启动时立即运行一次爬虫
- ✅ 每小时第 33 分钟自动执行
- ✅ 启动 Web 服务器（端口 8080）

---

### 步骤 3：访问 Web 界面

打开浏览器访问：
```
http://localhost:8080
```

您会看到：
- 📰 新闻热点（11 个平台）
- 💰 加密货币价格（BTC、ETH、BNB）
- 📈 股票行情（美股、港股、A股）
- 🤖 AI 分析（如果启用）

---

## 📊 管理命令

### 查看运行日志
```bash
docker logs -f trend-radar
```

### 手动执行一次爬虫
```bash
docker exec -it trend-radar python manage.py manual_run
```

### 查看 cron 任务状态
```bash
docker exec -it trend-radar python manage.py status
```

### 重启容器
```bash
cd docker
docker-compose restart
```

### 停止容器
```bash
cd docker
docker-compose down
```

---

## ⚙️ 高级配置

### 修改定时任务频率

编辑 `docker/.env`：

```bash
# 每小时第 33 分钟（默认）
CRON_SCHEDULE=33 * * * *

# 每 30 分钟
CRON_SCHEDULE=*/30 * * * *

# 每天 8:00 和 20:00
CRON_SCHEDULE=0 8,20 * * *
```

修改后重启容器：
```bash
cd docker
docker-compose restart
```

---

### 启用 AI 分析（可选）

编辑 `config/config.yaml`：

```yaml
AI_ANALYSIS:
  ENABLE: true
  PROVIDER: anthropic
  MODEL: claude-3-5-sonnet-20241022
  API_KEY: your-api-key  # 或通过环境变量设置
```

或在 `docker/.env` 添加：
```bash
CLAUDE_API_KEY=your-api-key
```

---

### 代理配置

如果需要代理访问 CoinGecko 或 Twitter，编辑 `docker/.env`：

```bash
# 已配置代理（端口 7000）
HTTP_PROXY=http://127.0.0.1:7000
HTTPS_PROXY=http://127.0.0.1:7000
```

**注意**：确保代理服务正在运行且可访问。

---

### 端口冲突

如果 8080 端口被占用，修改 `docker/.env`：

```bash
WEBSERVER_PORT=9090  # 改为其他端口
```

修改 `docker/docker-compose.yml`（第 8 行）：
```yaml
ports:
  - "127.0.0.1:9090:9090"  # 同步修改
```

重启容器生效。

---

## 🔍 故障排查

### 问题 1：容器启动失败

**检查日志**：
```bash
docker logs trend-radar
```

常见原因：
- 端口冲突 → 修改 `WEBSERVER_PORT`
- 配置错误 → 检查 `docker/.env` 和 `config/config.yaml`

---

### 问题 2：没有生成数据

**可能原因**：
- 未配置通知渠道
- Cron 表达式错误
- 网络问题（无法访问数据源）

**解决方法**：
```bash
# 手动执行查看错误
docker exec -it trend-radar python -m trendradar
```

---

### 问题 3：Web 界面无法访问

**检查服务器状态**：
```bash
docker exec -it trend-radar python manage.py status
```

**手动启动 Web 服务器**：
```bash
docker exec -it trend-radar python manage.py start_webserver
```

---

### 问题 4：加密货币/股票数据缺失

**确认配置已启用**：

检查 `config/config.yaml`：
```yaml
CRYPTO:
  ENABLE_CRYPTO: true
  USE_COINGECKO: true

STOCK:
  ENABLE_STOCK: true
```

**检查网络连接**：
```bash
# 测试 CoinGecko API
docker exec -it trend-radar curl https://api.coingecko.com/api/v3/ping
```

---

## 📁 数据持久化

生成的报告保存在：
```
TrendRadar/output/
├── 2025-12-30/
│   ├── html/
│   │   └── 当前榜单汇总.html
│   ├── txt/
│   └── news.db
└── index.html  (自动生成的导航页)
```

这些文件通过 Docker volume 映射，停止容器也不会丢失。

---

## 🌐 外网访问（可选）

### 方法 1：使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 方法 2：修改 Docker 端口绑定

编辑 `docker/docker-compose.yml`（第 8 行）：
```yaml
ports:
  - "0.0.0.0:8080:8080"  # 绑定到所有网络接口
```

**警告**：直接暴露端口可能有安全风险，建议使用 Nginx 并配置 HTTPS。

---

## 📊 性能优化

### 减少 Docker 镜像大小

使用预构建镜像（已优化）：
```bash
docker pull wantcat/trendradar:latest
```

### 限制资源使用

编辑 `docker/docker-compose.yml`，添加：
```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

---

## 🎉 部署完成！

一旦启动成功，您的 TrendRadar 将：
- ✅ 每小时自动抓取数据
- ✅ 生成精美的 HTML 报告
- ✅ 通过 Web 界面随时查看
- ✅ 推送通知到指定渠道

访问 `http://localhost:8080` 开始使用！

---

## 🆘 获取帮助

- **GitHub Issues**: https://github.com/sansan0/TrendRadar/issues
- **查看日志**: `docker logs -f trend-radar`
- **手动执行**: `docker exec -it trend-radar python -m trendradar`
