# 🏠 TrendRadar 本地部署指南

## 🎯 当前状态

✅ **Web 服务器已启动！**

访问：`http://localhost:8080`

---

## 📊 自动化部署方案

### 方案 1：使用 cron 定时任务（推荐）

#### 1. 测试运行脚本

```bash
cd /home/cecwxf/workspace/agent_ref/TrendRadar
./run_crawler.sh
```

#### 2. 添加 cron 任务

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每小时第 33 分钟运行）
33 * * * * /home/cecwxf/workspace/agent_ref/TrendRadar/run_crawler.sh >> /tmp/trendradar_cron.log 2>&1
```

#### 3. 查看 cron 日志

```bash
tail -f /tmp/trendradar_cron.log
```

---

### 方案 2：手动运行

#### 运行一次爬虫

```bash
cd /home/cecwxf/workspace/agent_ref/TrendRadar
python3 -m trendradar
```

#### 启动 Web 服务器

```bash
./start_webserver.sh
```

或者：

```bash
cd output
python3 -m http.server 8080
```

---

## 🌐 访问报告

### 本地访问

```
http://localhost:8080
```

### 局域网访问

```
http://你的IP地址:8080
```

获取 IP 地址：
```bash
hostname -I | awk '{print $1}'
```

### 外网访问（需要配置端口转发或 Nginx）

如果在 VPS 上部署，确保：
1. 防火墙开放 8080 端口
2. 使用 Nginx 反向代理（推荐）

---

## 🛠️ 管理命令

### 查看 Web 服务器状态

```bash
# 检查进程
ps aux | grep "http.server"

# 检查端口
lsof -i :8080
```

### 停止 Web 服务器

```bash
kill $(cat /tmp/trendradar_webserver.pid)
```

或：

```bash
kill $(lsof -t -i:8080)
```

### 重启 Web 服务器

```bash
./start_webserver.sh
```

---

## ⚙️ 配置

### 修改端口

编辑 `start_webserver.sh`：

```bash
PORT=9090  # 改为其他端口
```

### 配置代理

编辑 `run_crawler.sh`：

```bash
export HTTP_PROXY="http://127.0.0.1:7000"
export HTTPS_PROXY="http://127.0.0.1:7000"
```

### 配置通知渠道

编辑 `config/config.yaml` 或设置环境变量。

---

## 📈 性能优化

### 后台运行（nohup）

```bash
nohup python3 -m trendradar > /tmp/trendradar.log 2>&1 &
```

### 使用 systemd 服务（需要 root 权限）

创建 `/etc/systemd/system/trendradar.service`：

```ini
[Unit]
Description=TrendRadar News Crawler
After=network.target

[Service]
Type=simple
User=cecwxf
WorkingDirectory=/home/cecwxf/workspace/agent_ref/TrendRadar
ExecStart=/usr/bin/python3 -m trendradar
Restart=on-failure
RestartSec=300

Environment="HTTP_PROXY=http://127.0.0.1:7000"
Environment="HTTPS_PROXY=http://127.0.0.1:7000"

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable trendradar
sudo systemctl start trendradar
```

---

## 🔍 故障排查

### 问题 1：Web 服务器无法访问

**检查进程**：

```bash
ps aux | grep http.server
```

**检查端口**：

```bash
netstat -tuln | grep 8080
```

**重启服务器**：

```bash
./start_webserver.sh
```

---

### 问题 2：爬虫运行失败

**查看日志**：

```bash
# 如果使用 cron
tail -f /tmp/trendradar_cron.log

# 如果手动运行
python3 -m trendradar
```

**常见原因**：
- 未配置通知渠道
- 网络问题（无法访问数据源）
- 代理配置错误

---

### 问题 3：没有生成数据

**检查配置**：

```bash
cat config/config.yaml | grep -E "ENABLE_CRAWLER|ENABLE_NOTIFICATION"
```

**手动测试**：

```bash
python3 -m trendradar
```

---

## 📁 文件说明

| 文件 | 说明 |
|-----|------|
| `run_crawler.sh` | 爬虫运行脚本（用于 cron） |
| `start_webserver.sh` | Web 服务器启动脚本 |
| `output/` | 生成的报告目录 |
| `config/config.yaml` | 配置文件 |

---

## 🎉 部署完成！

当前状态：
- ✅ Web 服务器运行中（端口 8080）
- ✅ 可访问报告：http://localhost:8080
- ⏳ 配置 cron 定时任务后即可自动运行

下一步：
1. 访问 `http://localhost:8080` 查看报告
2. 配置 cron 定时任务（每小时自动运行）
3. 配置通知渠道（确保数据采集正常）

---

## 🆘 获取帮助

- 查看日志：`tail -f /tmp/trendradar_cron.log`
- 手动运行：`python3 -m trendradar`
- 重启服务：`./start_webserver.sh`
