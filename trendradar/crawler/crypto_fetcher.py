# coding=utf-8
"""
加密货币数据获取器 (Binance API)

功能：
- 获取 BTC/ETH 等加密货币实时价格
- 支持多币种并发查询
- 返回标准化的 NewsData 格式
"""

import json
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class CryptoFetcher:
    """加密货币数据获取器（基于 Binance Public API）"""

    # Binance API 地址（免费，无需 API Key）
    BASE_URL = "https://api.binance.com/api/v3"

    DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT"]  # BTC 和 ETH

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Connection": "keep-alive",
    }

    def __init__(self, proxy_url: Optional[str] = None):
        """
        初始化

        Args:
            proxy_url: 代理服务器 URL（可选）
        """
        self.proxy_url = proxy_url
        self.proxies = None
        if proxy_url:
            self.proxies = {"http": proxy_url, "https": proxy_url}

    def fetch_ticker_24h(self, symbols: Optional[List[str]] = None) -> Dict:
        """
        获取 24 小时价格统计

        Args:
            symbols: 交易对列表，默认 BTC 和 ETH

        Returns:
            价格数据字典，格式：
            {
                "BTCUSDT": {
                    "price": 50000.0,
                    "change_24h": 2.5,
                    "volume_24h": 1000000.0,
                    "high_24h": 51000.0,
                    "low_24h": 49000.0
                }
            }
        """
        if symbols is None:
            symbols = self.DEFAULT_SYMBOLS

        results = {}

        for symbol in symbols:
            try:
                url = f"{self.BASE_URL}/ticker/24hr"
                params = {"symbol": symbol}

                response = requests.get(
                    url,
                    params=params,
                    proxies=self.proxies,
                    headers=self.DEFAULT_HEADERS,
                    timeout=10
                )
                response.raise_for_status()

                data = response.json()

                # 标准化数据
                results[symbol] = {
                    "price": float(data["lastPrice"]),
                    "change_24h": float(data["priceChangePercent"]),
                    "volume_24h": float(data["volume"]),
                    "high_24h": float(data["highPrice"]),
                    "low_24h": float(data["lowPrice"]),
                }

                print(f"✓ 获取 {symbol} 成功: ${results[symbol]['price']:,.2f} "
                      f"({results[symbol]['change_24h']:+.2f}%)")

            except requests.exceptions.RequestException as e:
                print(f"✗ 获取 {symbol} 失败 (网络错误): {e}")
                results[symbol] = None
            except (KeyError, ValueError) as e:
                print(f"✗ 获取 {symbol} 失败 (数据格式错误): {e}")
                results[symbol] = None
            except Exception as e:
                print(f"✗ 获取 {symbol} 失败 (未知错误): {e}")
                results[symbol] = None

        return results

    def convert_to_news_format(
        self,
        price_data: Dict,
        crawl_time: str,
        crawl_date: str
    ) -> Tuple[Dict, Dict, List]:
        """
        转换为 TrendRadar 标准格式（兼容现有架构）

        Args:
            price_data: 价格数据字典
            crawl_time: 抓取时间 (HH:MM 格式)
            crawl_date: 抓取日期 (YYYY-MM-DD 格式)

        Returns:
            (results, id_to_name, failed_ids) 元组
            - results: {source_id: {title: {ranks, url, mobileUrl}}}
            - id_to_name: {source_id: source_name}
            - failed_ids: [失败的 symbol 列表]
        """
        results = {}
        id_to_name = {}
        failed_ids = []

        for symbol, data in price_data.items():
            if data is None:
                # 记录失败的币种
                failed_ids.append(symbol)
                continue

            # 映射到友好名称
            if symbol == "BTCUSDT":
                source_id = "crypto_btc"
                source_name = "比特币 BTC"
                short_name = "BTC"
            elif symbol == "ETHUSDT":
                source_id = "crypto_eth"
                source_name = "以太坊 ETH"
                short_name = "ETH"
            elif symbol == "BNBUSDT":
                source_id = "crypto_bnb"
                source_name = "币安币 BNB"
                short_name = "BNB"
            else:
                # 通用处理
                base_symbol = symbol.replace("USDT", "")
                source_id = f"crypto_{base_symbol.lower()}"
                source_name = f"{base_symbol}"
                short_name = base_symbol

            id_to_name[source_id] = source_name

            # 构建标题（模拟新闻标题格式）
            price = data["price"]
            change = data["change_24h"]
            volume = data["volume_24h"]

            # 根据涨跌选择表情符号
            emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"

            # 格式化标题
            title = (
                f"{short_name} {emoji} "
                f"${price:,.2f} "
                f"({change:+.2f}%) "
                f"24h成交量: {volume:,.0f}"
            )

            # 构建 URL
            url = f"https://www.binance.com/zh-CN/trade/{symbol}"

            # 按照 TrendRadar 格式存储
            results[source_id] = {
                title: {
                    "ranks": [1],  # 加密货币只有一条数据，固定排名 1
                    "url": url,
                    "mobileUrl": url
                }
            }

        return results, id_to_name, failed_ids


# 测试函数
def test_crypto_fetcher():
    """测试加密货币数据获取"""
    print("=" * 60)
    print("测试 Binance 加密货币数据获取")
    print("=" * 60)

    fetcher = CryptoFetcher()

    # 测试获取数据
    symbols = ["BTCUSDT", "ETHUSDT"]
    print(f"\n正在获取币种: {symbols}")
    price_data = fetcher.fetch_ticker_24h(symbols)

    print(f"\n获取结果:")
    for symbol, data in price_data.items():
        if data:
            print(f"  {symbol}: ${data['price']:,.2f} ({data['change_24h']:+.2f}%)")
        else:
            print(f"  {symbol}: 获取失败")

    # 测试数据格式转换
    print(f"\n转换为 TrendRadar 格式...")
    now = datetime.now()
    crawl_time = now.strftime("%H:%M")
    crawl_date = now.strftime("%Y-%m-%d")

    results, id_to_name, failed_ids = fetcher.convert_to_news_format(
        price_data, crawl_time, crawl_date
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
    test_crypto_fetcher()
