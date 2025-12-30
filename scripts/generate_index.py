#!/usr/bin/env python3
"""生成 GitHub Pages 主页导航"""

import os
from pathlib import Path

INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TrendRadar - 热点新闻追踪</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            color: white;
            padding: 60px 20px;
        }

        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .content {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .stat-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 12px;
            text-align: center;
        }

        .stat-card .icon {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }

        .stat-card .label {
            font-size: 0.9em;
            color: #666;
        }

        .section {
            margin-bottom: 40px;
        }

        .section h2 {
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #333;
            border-left: 4px solid #667eea;
            padding-left: 15px;
        }

        .latest-report {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 15px;
            color: white;
            margin-bottom: 30px;
        }

        .latest-report h3 {
            font-size: 1.5em;
            margin-bottom: 15px;
        }

        .report-link {
            display: inline-block;
            background: white;
            color: #667eea;
            padding: 15px 30px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            transition: transform 0.2s;
            margin-top: 15px;
        }

        .report-link:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }

        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }

        .feature {
            padding: 20px;
            border: 2px solid #f0f0f0;
            border-radius: 10px;
            transition: all 0.3s;
        }

        .feature:hover {
            border-color: #667eea;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.1);
        }

        .feature .icon {
            font-size: 2em;
            margin-bottom: 10px;
        }

        .feature h3 {
            font-size: 1.2em;
            margin-bottom: 10px;
            color: #333;
        }

        .feature p {
            color: #666;
            line-height: 1.6;
        }

        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: white;
        }

        .footer a {
            color: white;
            text-decoration: none;
            border-bottom: 1px solid white;
        }

        .auto-redirect {
            text-align: center;
            padding: 20px;
            background: #fff3cd;
            border-radius: 10px;
            margin-bottom: 20px;
        }

        .auto-redirect p {
            margin-bottom: 10px;
            color: #856404;
        }

        #countdown {
            font-weight: bold;
            font-size: 1.2em;
            color: #667eea;
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 2em;
            }

            .stats {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 TrendRadar</h1>
            <p>实时热点新闻 · 加密货币 · 股市行情</p>
        </div>

        <div class="content">
            <div class="auto-redirect">
                <p>🚀 正在自动跳转到最新报告...</p>
                <p>将在 <span id="countdown">3</span> 秒后跳转</p>
                <p><a href="#" onclick="cancelRedirect(); return false;">取消自动跳转</a></p>
            </div>

            <div class="latest-report">
                <h3>📰 最新报告</h3>
                <p>查看今日热点新闻、加密货币行情和股市动态</p>
                <a href="#" id="latest-link" class="report-link">查看最新报告 →</a>
            </div>

            <div class="stats">
                <div class="stat-card">
                    <div class="icon">📰</div>
                    <div class="value">11</div>
                    <div class="label">新闻平台</div>
                </div>
                <div class="stat-card">
                    <div class="icon">💰</div>
                    <div class="value">3</div>
                    <div class="label">加密货币</div>
                </div>
                <div class="stat-card">
                    <div class="icon">📈</div>
                    <div class="value">6</div>
                    <div class="label">股票指数</div>
                </div>
                <div class="stat-card">
                    <div class="icon">⏱️</div>
                    <div class="value">每小时</div>
                    <div class="label">更新频率</div>
                </div>
            </div>

            <div class="section">
                <h2>✨ 核心功能</h2>
                <div class="features">
                    <div class="feature">
                        <div class="icon">📰</div>
                        <h3>多平台新闻聚合</h3>
                        <p>整合今日头条、微博、知乎、B站等11个主流平台热搜</p>
                    </div>
                    <div class="feature">
                        <div class="icon">💰</div>
                        <h3>加密货币实时行情</h3>
                        <p>追踪 BTC、ETH、BNB 等主流币种价格和24h涨跌</p>
                    </div>
                    <div class="feature">
                        <div class="icon">📈</div>
                        <h3>股市动态监控</h3>
                        <p>美股、港股、A股重点指数和科技股实时行情</p>
                    </div>
                    <div class="feature">
                        <div class="icon">🤖</div>
                        <h3>AI 智能分析</h3>
                        <p>基于 Claude AI 的市场趋势综合分析（可选）</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>📊 数据来源</h2>
                <div class="features">
                    <div class="feature">
                        <div class="icon">🌐</div>
                        <h3>新闻平台</h3>
                        <p>今日头条、百度、微博、知乎、抖音、B站、澎湃、财联社等</p>
                    </div>
                    <div class="feature">
                        <div class="icon">🔗</div>
                        <h3>金融数据</h3>
                        <p>CoinGecko (加密货币) + Yahoo Finance (股票)</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>由 <a href="https://github.com/cecwxf/TrendRadar" target="_blank">TrendRadar</a> 强力驱动</p>
            <p>每小时自动更新 | 开源免费</p>
        </div>
    </div>

    <script>
        // 自动查找最新报告
        function findLatestReport() {
            const today = new Date();
            const year = today.getFullYear();
            const month = String(today.getMonth() + 1).padStart(2, '0');
            const day = String(today.getDate()).padStart(2, '0');
            const dateStr = `${year}-${month}-${day}`;

            // 尝试查找当日汇总报告
            const summaryUrls = [
                `./${dateStr}/html/当前榜单汇总.html`,
                `./${dateStr}/html/当日汇总.html`,
            ];

            // 默认使用当前榜单汇总
            return summaryUrls[0];
        }

        // 设置最新报告链接
        const latestReportUrl = findLatestReport();
        document.getElementById('latest-link').href = latestReportUrl;

        // 自动跳转倒计时
        let countdown = 3;
        let redirectTimer;
        let isRedirecting = true;

        function updateCountdown() {
            document.getElementById('countdown').textContent = countdown;
            if (countdown > 0) {
                countdown--;
                redirectTimer = setTimeout(updateCountdown, 1000);
            } else {
                if (isRedirecting) {
                    window.location.href = latestReportUrl;
                }
            }
        }

        function cancelRedirect() {
            isRedirecting = false;
            clearTimeout(redirectTimer);
            document.querySelector('.auto-redirect').style.display = 'none';
        }

        // 启动倒计时
        updateCountdown();
    </script>
</body>
</html>
"""

def main():
    """生成主页"""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    index_file = output_dir / "index.html"
    index_file.write_text(INDEX_HTML, encoding='utf-8')

    print(f"✓ 主页已生成: {index_file}")

if __name__ == "__main__":
    main()
