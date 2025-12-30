# coding=utf-8
"""
Twitter RSS 获取器

功能：
- 通过 Nitter RSS 获取 Twitter 推文
- 免费方案，无需 API Key
- 返回标准化的 TrendRadar 格式
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class TwitterFetcher:
    """Twitter RSS 获取器（基于 Nitter）"""

    # Nitter 实例列表（公共服务）
    NITTER_INSTANCES = [
        "https://nitter.net",
        "https://nitter.privacydev.net",
        "https://nitter.poast.org",
        "https://nitter.cz",
        "https://nitter.nl",
        "https://nitter.mint.lgbt",
        "https://nitter.unixfox.eu",
    ]

    def __init__(self, proxy_url: Optional[str] = None):
        """
        初始化

        Args:
            proxy_url: 代理服务器 URL（可选）
        """
        self.proxy_url = proxy_url

    def fetch_user_tweets(
        self,
        username: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        获取指定用户的推文

        Args:
            username: Twitter 用户名（如 SiliconWang）
            limit: 获取数量

        Returns:
            推文列表，格式：
            [
                {
                    "title": "推文标题",
                    "content": "推文内容（截断到200字符）",
                    "url": "推文链接",
                    "published": "发布时间"
                }
            ]
        """
        tweets = []

        # 动态导入 feedparser（避免未安装时导入失败）
        try:
            import feedparser
        except ImportError:
            print("✗ feedparser 库未安装，请运行: pip install feedparser")
            return tweets

        # 尝试多个 Nitter 实例
        for instance in self.NITTER_INSTANCES:
            try:
                rss_url = f"{instance}/{username}/rss"

                print(f"尝试获取 @{username} 的推文: {rss_url}")

                # 先用 requests 获取 RSS 内容（带超时）
                import requests

                proxies = None
                if self.proxy_url:
                    proxies = {"http": self.proxy_url, "https": self.proxy_url}

                response = requests.get(
                    rss_url,
                    proxies=proxies,
                    timeout=10,  # 10秒超时
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                )
                response.raise_for_status()

                # 解析 RSS 内容
                feed = feedparser.parse(response.content)

                if not feed.entries:
                    print(f"  从 {instance} 获取失败: 无数据")
                    continue

                for entry in feed.entries[:limit]:
                    # 清理 HTML 标签
                    content = re.sub(r'<[^>]+>', '', entry.summary)
                    # 移除多余的空白
                    content = ' '.join(content.split())

                    tweets.append({
                        "title": entry.title[:100],  # 限制标题长度
                        "content": content[:200],  # 限制内容长度
                        "url": entry.link,
                        "published": entry.published if hasattr(entry, 'published') else "",
                    })

                print(f"✓ 成功从 {instance} 获取 {len(tweets)} 条推文")
                break  # 成功后退出循环

            except requests.exceptions.Timeout:
                print(f"  从 {instance} 获取超时 (10秒)")
                continue
            except requests.exceptions.RequestException as e:
                print(f"  从 {instance} 获取失败 (网络错误): {str(e)[:50]}")
                continue
            except Exception as e:
                print(f"  从 {instance} 获取失败: {str(e)[:50]}")
                continue

        if not tweets:
            print(f"✗ 所有 Nitter 实例都失败，无法获取 @{username} 的推文")

        return tweets

    def convert_to_news_format(
        self,
        tweets: List[Dict],
        username: str,
        crawl_time: str,
        crawl_date: str
    ) -> Tuple[Dict, Dict, List]:
        """
        转换为 TrendRadar 标准格式

        Args:
            tweets: 推文列表
            username: Twitter 用户名
            crawl_time: 抓取时间
            crawl_date: 抓取日期

        Returns:
            (results, id_to_name, failed_ids) 元组
        """
        source_id = f"twitter_{username.lower()}"
        source_name = f"Twitter @{username}"

        results = {}
        id_to_name = {source_id: source_name}
        failed_ids = []

        if not tweets:
            # 如果没有获取到推文，标记为失败
            failed_ids.append(source_id)
            return results, id_to_name, failed_ids

        # 将所有推文放在同一个 source_id 下
        results[source_id] = {}

        for idx, tweet in enumerate(tweets, 1):
            # 构建标题（包含序号和内容摘要）
            title = f"[{idx}] {tweet['content']}"

            # 按照 TrendRadar 格式存储
            results[source_id][title] = {
                "ranks": [idx],
                "url": tweet["url"],
                "mobileUrl": tweet["url"]
            }

        return results, id_to_name, failed_ids


# 测试函数
def test_twitter_fetcher():
    """测试 Twitter 数据获取"""
    print("=" * 60)
    print("测试 Twitter RSS 数据获取（硅谷王川）")
    print("=" * 60)

    fetcher = TwitterFetcher()

    # 测试获取数据
    username = "chuanwang"  # 硅谷王川的 Twitter 用户名
    print(f"\n正在获取 @{username} 的推文...")
    tweets = fetcher.fetch_user_tweets(username, limit=5)

    print(f"\n获取结果: {len(tweets)} 条推文")
    for idx, tweet in enumerate(tweets, 1):
        print(f"\n  推文 {idx}:")
        print(f"    内容: {tweet['content']}")
        print(f"    链接: {tweet['url']}")
        if tweet['published']:
            print(f"    时间: {tweet['published']}")

    # 测试数据格式转换
    if tweets:
        print(f"\n转换为 TrendRadar 格式...")
        now = datetime.now()
        crawl_time = now.strftime("%H:%M")
        crawl_date = now.strftime("%Y-%m-%d")

        results, id_to_name, failed_ids = fetcher.convert_to_news_format(
            tweets, username, crawl_time, crawl_date
        )

        print(f"\n转换结果:")
        print(f"  平台映射: {id_to_name}")
        print(f"  失败列表: {failed_ids}")
        print(f"\n数据详情:")
        for source_id, titles in results.items():
            print(f"  [{source_id}] - {len(titles)} 条推文")
            for title, data in list(titles.items())[:3]:  # 只显示前3条
                print(f"    标题: {title[:80]}...")
                print(f"    URL: {data['url']}")
    else:
        print("\n⚠️ 未获取到推文，跳过格式转换测试")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_twitter_fetcher()
