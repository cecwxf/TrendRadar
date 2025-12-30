# coding=utf-8
"""
股票数据获取器 (Yahoo Finance)

功能：
- 获取美股/港股/A股实时价格
- 使用 yfinance 库
- 返回标准化的 TrendRadar 格式
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class StockFetcher:
    """股票数据获取器（基于 yfinance）"""

    # 默认监控的股票列表
    DEFAULT_STOCKS = {
        # 美股科技巨头
        "AAPL": {"market": "US", "name": "苹果"},
        "TSLA": {"market": "US", "name": "特斯拉"},
        "NVDA": {"market": "US", "name": "英伟达"},

        # 港股
        "0700.HK": {"market": "HK", "name": "腾讯控股"},
        "9988.HK": {"market": "HK", "name": "阿里巴巴"},

        # A股（上证）
        "000001.SS": {"market": "CN", "name": "上证指数"},
    }

    def __init__(self, proxy_url: Optional[str] = None):
        """
        初始化

        Args:
            proxy_url: 代理服务器 URL（可选，yfinance 可能需要）
        """
        self.proxy_url = proxy_url

    def fetch_stocks(
        self,
        stock_config: Optional[Dict] = None
    ) -> Dict:
        """
        获取股票数据

        Args:
            stock_config: 股票配置字典，格式同 DEFAULT_STOCKS

        Returns:
            股票数据字典，格式：
            {
                "AAPL": {
                    "price": 180.0,
                    "change_pct": 2.5,
                    "open": 175.0,
                    "high": 182.0,
                    "low": 174.0,
                    "volume": 50000000,
                    "market": "US",
                    "name": "苹果"
                }
            }
        """
        if stock_config is None:
            stock_config = self.DEFAULT_STOCKS

        results = {}

        # 动态导入 yfinance（避免未安装时导入失败）
        try:
            import yfinance as yf
        except ImportError:
            print("✗ yfinance 库未安装，请运行: pip install yfinance")
            # 返回所有股票都失败的结果
            for symbol in stock_config.keys():
                results[symbol] = None
            return results

        for symbol, info in stock_config.items():
            try:
                ticker = yf.Ticker(symbol)

                # 获取实时数据（最近1天的分钟级数据）
                hist = ticker.history(period="1d", interval="1m")

                if hist.empty:
                    print(f"✗ 获取 {symbol} 失败: 无数据（可能市场未开盘）")
                    results[symbol] = None
                    continue

                # 获取最新价格
                current_price = hist['Close'].iloc[-1]
                open_price = hist['Open'].iloc[0]
                high_price = hist['High'].max()
                low_price = hist['Low'].min()
                volume = hist['Volume'].sum()

                # 计算涨跌幅
                if open_price > 0:
                    change_pct = ((current_price - open_price) / open_price) * 100
                else:
                    change_pct = 0.0

                results[symbol] = {
                    "price": float(current_price),
                    "change_pct": float(change_pct),
                    "open": float(open_price),
                    "high": float(high_price),
                    "low": float(low_price),
                    "volume": float(volume),
                    "market": info["market"],
                    "name": info["name"]
                }

                print(f"✓ 获取 {info['name']}({symbol}) 成功: "
                      f"{current_price:.2f} ({change_pct:+.2f}%)")

            except Exception as e:
                print(f"✗ 获取 {symbol} 失败: {e}")
                results[symbol] = None

        return results

    def convert_to_news_format(
        self,
        stock_data: Dict,
        crawl_time: str,
        crawl_date: str
    ) -> Tuple[Dict, Dict, List]:
        """
        转换为 TrendRadar 标准格式

        Args:
            stock_data: 股票数据字典
            crawl_time: 抓取时间 (HH:MM)
            crawl_date: 抓取日期 (YYYY-MM-DD)

        Returns:
            (results, id_to_name, failed_ids) 元组
        """
        results = {}
        id_to_name = {}
        failed_ids = []

        for symbol, data in stock_data.items():
            if data is None:
                failed_ids.append(symbol)
                continue

            # 生成 source_id（替换特殊字符）
            source_id = f"stock_{symbol.replace('.', '_').lower()}"
            source_name = f"{data['name']} ({data['market']})"

            id_to_name[source_id] = source_name

            # 构建标题
            price = data["price"]
            change = data["change_pct"]

            # 根据涨跌选择表情符号
            if change > 0:
                emoji = "📈"
                color_hint = "涨"
            elif change < 0:
                emoji = "📉"
                color_hint = "跌"
            else:
                emoji = "➡️"
                color_hint = "平"

            # 格式化标题
            title = (
                f"{data['name']} {emoji} "
                f"{price:.2f} "
                f"({change:+.2f}%) "
                f"[{color_hint}] "
                f"成交量: {data['volume']:,.0f}"
            )

            # 构建 URL
            url = f"https://finance.yahoo.com/quote/{symbol}"

            # 按照 TrendRadar 格式存储
            results[source_id] = {
                title: {
                    "ranks": [1],
                    "url": url,
                    "mobileUrl": url
                }
            }

        return results, id_to_name, failed_ids


# 测试函数
def test_stock_fetcher():
    """测试股票数据获取"""
    print("=" * 60)
    print("测试 Yahoo Finance 股票数据获取")
    print("=" * 60)

    fetcher = StockFetcher()

    # 测试获取数据（使用部分股票以加快速度）
    test_stocks = {
        "AAPL": {"market": "US", "name": "苹果"},
        "TSLA": {"market": "US", "name": "特斯拉"},
    }

    print(f"\n正在获取股票: {list(test_stocks.keys())}")
    stock_data = fetcher.fetch_stocks(test_stocks)

    print(f"\n获取结果:")
    for symbol, data in stock_data.items():
        if data:
            print(f"  {symbol} ({data['name']}): "
                  f"{data['price']:.2f} ({data['change_pct']:+.2f}%)")
        else:
            print(f"  {symbol}: 获取失败")

    # 测试数据格式转换
    print(f"\n转换为 TrendRadar 格式...")
    now = datetime.now()
    crawl_time = now.strftime("%H:%M")
    crawl_date = now.strftime("%Y-%m-%d")

    results, id_to_name, failed_ids = fetcher.convert_to_news_format(
        stock_data, crawl_time, crawl_date
    )

    print(f"\n转换结果:")
    print(f"  平台映射: {id_to_name}")
    print(f"  失败列表: {failed_ids}")
    print(f"\n数据详情:")
    for source_id, titles in results.items():
        print(f"  [{source_id}]")
        for title, data in titles.items():
            print(f"    标题: {title}")
            print(f"    URL: {data['url']}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_stock_fetcher()
