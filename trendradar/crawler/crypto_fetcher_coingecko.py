# coding=utf-8
"""
加密货币数据获取器 (CoinGecko API - 无地区限制)

功能：
- 使用 CoinGecko API 获取加密货币价格
- 无需代理，全球可用
- 免费，无需 API Key
"""

import requests
from typing import Dict, List, Optional, Tuple


class CryptoFetcherCoinGecko:
    """加密货币数据获取器（基于 CoinGecko API）"""

    BASE_URL = "https://api.coingecko.com/api/v3"

    # 符号映射（Binance 格式 -> CoinGecko ID）
    SYMBOL_MAP = {
        "BTCUSDT": "bitcoin",
        "ETHUSDT": "ethereum",
        "BNBUSDT": "binancecoin",
        "SOLUSDT": "solana",
        "ADAUSDT": "cardano",
        "DOGEUSDT": "dogecoin",
    }

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    def __init__(self, proxy_url: Optional[str] = None):
        """初始化"""
        self.proxy_url = proxy_url
        self.proxies = None
        if proxy_url:
            self.proxies = {"http": proxy_url, "https": proxy_url}

    def fetch_ticker_24h(self, symbols: Optional[List[str]] = None) -> Dict:
        """
        获取 24 小时价格统计

        Args:
            symbols: 交易对列表（Binance 格式，如 ["BTCUSDT", "ETHUSDT"]）

        Returns:
            价格数据字典
        """
        if symbols is None:
            symbols = ["BTCUSDT", "ETHUSDT"]

        # 转换为 CoinGecko IDs
        coin_ids = []
        symbol_to_id = {}
        for symbol in symbols:
            if symbol in self.SYMBOL_MAP:
                coin_id = self.SYMBOL_MAP[symbol]
                coin_ids.append(coin_id)
                symbol_to_id[coin_id] = symbol
            else:
                print(f"⚠️  未知符号: {symbol}，跳过")

        if not coin_ids:
            return {}

        results = {}

        try:
            # CoinGecko API: 批量获取价格
            url = f"{self.BASE_URL}/simple/price"
            params = {
                "ids": ",".join(coin_ids),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_24hr_vol": "true",
            }

            response = requests.get(
                url,
                params=params,
                proxies=self.proxies,
                headers=self.DEFAULT_HEADERS,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            # 处理每个币种
            for coin_id, coin_data in data.items():
                symbol = symbol_to_id.get(coin_id)
                if not symbol:
                    continue

                try:
                    results[symbol] = {
                        "price": float(coin_data["usd"]),
                        "change_24h": float(coin_data.get("usd_24h_change", 0)),
                        "volume_24h": float(coin_data.get("usd_24h_vol", 0)),
                        "high_24h": 0,  # CoinGecko 免费 API 不提供
                        "low_24h": 0,   # CoinGecko 免费 API 不提供
                    }

                    print(f"✓ 获取 {symbol} 成功: ${results[symbol]['price']:,.2f} "
                          f"({results[symbol]['change_24h']:+.2f}%)")

                except (KeyError, ValueError) as e:
                    print(f"✗ 解析 {symbol} 数据失败: {e}")
                    results[symbol] = None

        except requests.exceptions.RequestException as e:
            print(f"✗ CoinGecko API 请求失败: {e}")
            for symbol in symbols:
                results[symbol] = None

        # 添加未获取到的币种
        for symbol in symbols:
            if symbol not in results:
                results[symbol] = None

        return results

    def convert_to_news_format(
        self,
        price_data: Dict,
        crawl_time: str,
        crawl_date: str
    ) -> Tuple[Dict, Dict, List]:
        """
        转换为 TrendRadar 标准格式

        （与 Binance 版本完全一致）
        """
        results = {}
        id_to_name = {}
        failed_ids = []

        for symbol, data in price_data.items():
            if data is None:
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
                base_symbol = symbol.replace("USDT", "")
                source_id = f"crypto_{base_symbol.lower()}"
                source_name = f"{base_symbol}"
                short_name = base_symbol

            id_to_name[source_id] = source_name

            # 构建标题
            price = data["price"]
            change = data["change_24h"]
            volume = data["volume_24h"]

            emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"

            title = (
                f"{short_name} {emoji} "
                f"${price:,.2f} "
                f"({change:+.2f}%) "
                f"24h成交量: {volume:,.0f}"
            )

            url = f"https://www.coingecko.com/zh/数字货币/{self.SYMBOL_MAP.get(symbol, '')}"

            results[source_id] = {
                title: {
                    "ranks": [1],
                    "url": url,
                    "mobileUrl": url
                }
            }

        return results, id_to_name, failed_ids


# 测试函数
if __name__ == "__main__":
    print("=" * 60)
    print("测试 CoinGecko 加密货币数据获取")
    print("=" * 60)

    fetcher = CryptoFetcherCoinGecko()
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

    print(f"\n正在获取币种: {symbols}")
    price_data = fetcher.fetch_ticker_24h(symbols)

    print(f"\n获取结果:")
    for symbol, data in price_data.items():
        if data:
            print(f"  {symbol}: ${data['price']:,.2f} ({data['change_24h']:+.2f}%)")
        else:
            print(f"  {symbol}: 获取失败")
