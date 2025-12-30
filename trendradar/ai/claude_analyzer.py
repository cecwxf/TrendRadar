# coding=utf-8
"""
Claude API 综合分析器

提供基于 Claude API 的市场数据综合分析功能
"""

import os
from typing import Dict, Optional, List
from datetime import datetime


class ClaudeAnalyzer:
    """Claude API 综合分析器"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        """初始化分析器

        Args:
            api_key: Anthropic API Key（可选，默认从环境变量读取）
            model: 使用的模型名称
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY')
        self.model = model
        self.last_analysis_tokens = 0

        if not self.api_key:
            raise ValueError(
                "未找到 API Key。请设置环境变量 ANTHROPIC_API_KEY 或 CLAUDE_API_KEY"
            )

    def analyze_market_trends(
        self,
        news_stats: List[Dict],
        extended_data: Optional[Dict] = None,
        date: Optional[str] = None
    ) -> Optional[Dict]:
        """综合分析市场趋势

        Args:
            news_stats: 新闻热点统计数据
            extended_data: 扩展数据（crypto, stock, twitter）
            date: 分析日期（可选）

        Returns:
            分析结果字典 {
                'analysis': str,  # 分析内容
                'tokens_used': int,  # 使用的 tokens
                'timestamp': str  # 时间戳
            }
        """
        try:
            # 导入 anthropic（延迟导入，避免未安装时报错）
            try:
                import anthropic
            except ImportError:
                print("⚠️  未安装 anthropic 库，跳过 AI 分析")
                print("   安装命令: pip install anthropic")
                return None

            # 构建分析提示词
            prompt = self._build_analysis_prompt(news_stats, extended_data, date)

            # 调用 Claude API
            client = anthropic.Anthropic(api_key=self.api_key)

            response = client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # 提取分析内容
            analysis_content = response.content[0].text

            # 统计 tokens
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens
            self.last_analysis_tokens = total_tokens

            # 返回结果
            return {
                'analysis': analysis_content,
                'tokens_used': total_tokens,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'timestamp': datetime.now().isoformat(),
                'model': self.model
            }

        except Exception as e:
            print(f"❌ AI 分析失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _build_analysis_prompt(
        self,
        news_stats: List[Dict],
        extended_data: Optional[Dict],
        date: Optional[str]
    ) -> str:
        """构建分析提示词

        Args:
            news_stats: 新闻热点统计
            extended_data: 扩展数据
            date: 分析日期

        Returns:
            提示词字符串
        """
        # 日期信息
        date_str = date or datetime.now().strftime("%Y-%m-%d")

        prompt = f"""请作为一名专业的市场分析师，综合分析以下 {date_str} 的数据，给出市场趋势分析和洞察。

## 数据概览

"""

        # 1. 新闻热点
        if news_stats:
            prompt += "### 📰 新闻热点\n\n"
            for i, stat in enumerate(news_stats[:10], 1):  # 最多分析前 10 个热点
                word = stat.get('word', '')
                count = stat.get('count', 0)
                prompt += f"{i}. **{word}**（{count} 条新闻）\n"

                # 添加代表性标题
                titles = stat.get('titles', [])
                if titles:
                    first_title = titles[0].get('title', '')
                    if first_title:
                        prompt += f"   - 代表性新闻: {first_title}\n"

            prompt += "\n"

        # 2. 加密货币数据
        if extended_data and extended_data.get('crypto'):
            prompt += "### 💰 加密货币市场\n\n"
            crypto_data = extended_data['crypto']

            # 按涨跌幅排序
            sorted_cryptos = sorted(
                [(symbol, data) for symbol, data in crypto_data.items() if data],
                key=lambda x: x[1].get('change_24h', 0),
                reverse=True
            )

            for symbol, data in sorted_cryptos[:5]:
                price = data.get('price', 0)
                change = data.get('change_24h', 0)
                display_symbol = symbol.replace('USDT', '')

                # 格式化价格
                if price >= 1000:
                    price_str = f"${price:,.0f}"
                elif price >= 1:
                    price_str = f"${price:.2f}"
                else:
                    price_str = f"${price:.4f}"

                change_str = f"{change:+.2f}%"
                prompt += f"- **{display_symbol}**: {price_str} ({change_str})\n"

            prompt += "\n"

        # 3. 股票数据
        if extended_data and extended_data.get('stock'):
            prompt += "### 📈 股票市场\n\n"
            stock_data = extended_data['stock']

            # 按涨跌幅排序
            sorted_stocks = sorted(
                [(symbol, data) for symbol, data in stock_data.items() if data],
                key=lambda x: x[1].get('change_pct', 0),
                reverse=True
            )

            for symbol, data in sorted_stocks[:5]:
                name = data.get('name', symbol)
                market = data.get('market', '')
                price = data.get('price', 0)
                change = data.get('change_pct', 0)

                price_str = f"${price:.2f}" if market == "US" else f"{price:.2f}"
                change_str = f"{change:+.2f}%"

                display_name = f"{name} ({market})" if market else name
                prompt += f"- **{display_name}**: {price_str} ({change_str})\n"

            prompt += "\n"

        # 4. Twitter 动态
        if extended_data and extended_data.get('twitter'):
            prompt += "### 🐦 社交媒体动态\n\n"
            twitter_data = extended_data['twitter']

            for author, tweets in list(twitter_data.items())[:3]:  # 最多3个账号
                if not tweets:
                    continue

                latest_tweet = tweets[0] if isinstance(tweets, list) else tweets
                content = latest_tweet.get('content', '')

                # 截取内容
                if len(content) > 200:
                    content = content[:197] + "..."

                prompt += f"- **@{author}**: {content}\n"

            prompt += "\n"

        # 分析要求
        prompt += """## 分析要求

请从以下角度进行分析：

1. **市场热点总结**：总结今日最重要的新闻热点和市场动向
2. **加密货币市场**：分析加密货币市场的整体趋势和值得关注的币种
3. **股票市场**：分析重点股票的表现和可能的原因
4. **综合洞察**：结合新闻、加密货币、股票和社交媒体数据，给出市场综合洞察
5. **风险提示**：指出当前市场的主要风险因素

## 输出格式

请使用 Markdown 格式输出，包含以下部分：

### 📊 市场概况

[简要概述今日市场整体情况，1-2 句话]

### 🔥 热点事件

[列出 2-3 个最重要的热点事件及其影响]

### 💰 加密货币分析

[分析加密货币市场趋势]

### 📈 股票市场分析

[分析股票市场表现]

### 💡 综合洞察

[结合所有数据的综合分析和洞察]

### ⚠️ 风险提示

[当前市场主要风险]

---

**注意**：
- 保持客观中立，基于数据分析
- 避免过度乐观或悲观的判断
- 不提供具体投资建议，仅供参考
- 控制篇幅在 500-800 字之间
"""

        return prompt

    def get_last_tokens_used(self) -> int:
        """获取上次分析使用的 tokens 数量"""
        return self.last_analysis_tokens

    def estimate_cost(self, tokens: int) -> float:
        """估算成本（美元）

        Args:
            tokens: Token 数量

        Returns:
            成本（美元）
        """
        # Claude 3.5 Sonnet 定价（截至 2024-12）
        # 输入: $3/M tokens
        # 输出: $15/M tokens
        # 这里简化为平均成本
        average_cost_per_million = 9.0  # (3 + 15) / 2
        return (tokens / 1_000_000) * average_cost_per_million
