# coding=utf-8
"""
TrendRadar 主程序

热点新闻聚合与分析工具
支持: python -m trendradar
"""

import os
import webbrowser
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import requests

from trendradar.context import AppContext
from trendradar import __version__
from trendradar.core import load_config
from trendradar.crawler import DataFetcher
from trendradar.storage import convert_crawl_results_to_news_data


def check_version_update(
    current_version: str, version_url: str, proxy_url: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """检查版本更新"""
    try:
        proxies = None
        if proxy_url:
            proxies = {"http": proxy_url, "https": proxy_url}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/plain, */*",
            "Cache-Control": "no-cache",
        }

        response = requests.get(
            version_url, proxies=proxies, headers=headers, timeout=10
        )
        response.raise_for_status()

        remote_version = response.text.strip()
        print(f"当前版本: {current_version}, 远程版本: {remote_version}")

        # 比较版本
        def parse_version(version_str):
            try:
                parts = version_str.strip().split(".")
                if len(parts) != 3:
                    raise ValueError("版本号格式不正确")
                return int(parts[0]), int(parts[1]), int(parts[2])
            except:
                return 0, 0, 0

        current_tuple = parse_version(current_version)
        remote_tuple = parse_version(remote_version)

        need_update = current_tuple < remote_tuple
        return need_update, remote_version if need_update else None

    except Exception as e:
        print(f"版本检查失败: {e}")
        return False, None


# === 主分析器 ===
class NewsAnalyzer:
    """新闻分析器"""

    # 模式策略定义
    MODE_STRATEGIES = {
        "incremental": {
            "mode_name": "增量模式",
            "description": "增量模式（只关注新增新闻，无新增时不推送）",
            "realtime_report_type": "实时增量",
            "summary_report_type": "当日汇总",
            "should_send_realtime": True,
            "should_generate_summary": True,
            "summary_mode": "daily",
        },
        "current": {
            "mode_name": "当前榜单模式",
            "description": "当前榜单模式（当前榜单匹配新闻 + 新增新闻区域 + 按时推送）",
            "realtime_report_type": "实时当前榜单",
            "summary_report_type": "当前榜单汇总",
            "should_send_realtime": True,
            "should_generate_summary": True,
            "summary_mode": "current",
        },
        "daily": {
            "mode_name": "当日汇总模式",
            "description": "当日汇总模式（所有匹配新闻 + 新增新闻区域 + 按时推送）",
            "realtime_report_type": "",
            "summary_report_type": "当日汇总",
            "should_send_realtime": False,
            "should_generate_summary": True,
            "summary_mode": "daily",
        },
    }

    def __init__(self):
        # 加载配置
        print("正在加载配置...")
        config = load_config()
        print(f"TrendRadar v{__version__} 配置加载完成")
        print(f"监控平台数量: {len(config['PLATFORMS'])}")
        print(f"时区: {config.get('TIMEZONE', 'Asia/Shanghai')}")

        # 创建应用上下文
        self.ctx = AppContext(config)

        self.request_interval = self.ctx.config["REQUEST_INTERVAL"]
        self.report_mode = self.ctx.config["REPORT_MODE"]
        self.rank_threshold = self.ctx.rank_threshold
        self.is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"
        self.is_docker_container = self._detect_docker_environment()
        self.update_info = None
        self.proxy_url = None
        self._setup_proxy()
        self.data_fetcher = DataFetcher(self.proxy_url)

        # 初始化存储管理器（使用 AppContext）
        self._init_storage_manager()

        if self.is_github_actions:
            self._check_version_update()

    def _init_storage_manager(self) -> None:
        """初始化存储管理器（使用 AppContext）"""
        # 获取数据保留天数（支持环境变量覆盖）
        env_retention = os.environ.get("STORAGE_RETENTION_DAYS", "").strip()
        if env_retention:
            # 环境变量覆盖配置
            self.ctx.config["STORAGE"]["RETENTION_DAYS"] = int(env_retention)

        self.storage_manager = self.ctx.get_storage_manager()
        print(f"存储后端: {self.storage_manager.backend_name}")

        retention_days = self.ctx.config.get("STORAGE", {}).get("RETENTION_DAYS", 0)
        if retention_days > 0:
            print(f"数据保留天数: {retention_days} 天")

    def _detect_docker_environment(self) -> bool:
        """检测是否运行在 Docker 容器中"""
        try:
            if os.environ.get("DOCKER_CONTAINER") == "true":
                return True

            if os.path.exists("/.dockerenv"):
                return True

            return False
        except Exception:
            return False

    def _should_open_browser(self) -> bool:
        """判断是否应该打开浏览器"""
        return not self.is_github_actions and not self.is_docker_container

    def _setup_proxy(self) -> None:
        """设置代理配置"""
        if not self.is_github_actions and self.ctx.config["USE_PROXY"]:
            self.proxy_url = self.ctx.config["DEFAULT_PROXY"]
            print("本地环境，使用代理")
        elif not self.is_github_actions and not self.ctx.config["USE_PROXY"]:
            print("本地环境，未启用代理")
        else:
            print("GitHub Actions环境，不使用代理")

    def _check_version_update(self) -> None:
        """检查版本更新"""
        try:
            need_update, remote_version = check_version_update(
                __version__, self.ctx.config["VERSION_CHECK_URL"], self.proxy_url
            )

            if need_update and remote_version:
                self.update_info = {
                    "current_version": __version__,
                    "remote_version": remote_version,
                }
                print(f"发现新版本: {remote_version} (当前: {__version__})")
            else:
                print("版本检查完成，当前为最新版本")
        except Exception as e:
            print(f"版本检查出错: {e}")

    def _get_mode_strategy(self) -> Dict:
        """获取当前模式的策略配置"""
        return self.MODE_STRATEGIES.get(self.report_mode, self.MODE_STRATEGIES["daily"])

    def _has_notification_configured(self) -> bool:
        """检查是否配置了任何通知渠道"""
        cfg = self.ctx.config
        return any(
            [
                cfg["FEISHU_WEBHOOK_URL"],
                cfg["DINGTALK_WEBHOOK_URL"],
                cfg["WEWORK_WEBHOOK_URL"],
                (cfg["TELEGRAM_BOT_TOKEN"] and cfg["TELEGRAM_CHAT_ID"]),
                (
                    cfg["EMAIL_FROM"]
                    and cfg["EMAIL_PASSWORD"]
                    and cfg["EMAIL_TO"]
                ),
                (cfg["NTFY_SERVER_URL"] and cfg["NTFY_TOPIC"]),
                cfg["BARK_URL"],
                cfg["SLACK_WEBHOOK_URL"],
            ]
        )

    def _has_valid_content(
        self, stats: List[Dict], new_titles: Optional[Dict] = None
    ) -> bool:
        """检查是否有有效的新闻内容"""
        if self.report_mode == "incremental":
            # 增量模式：必须有新增标题且匹配了关键词才推送
            has_new_titles = bool(
                new_titles and any(len(titles) > 0 for titles in new_titles.values())
            )
            has_matched_news = any(stat["count"] > 0 for stat in stats)
            return has_new_titles and has_matched_news
        elif self.report_mode == "current":
            # current模式：只要stats有内容就说明有匹配的新闻
            return any(stat["count"] > 0 for stat in stats)
        else:
            # 当日汇总模式下，检查是否有匹配的频率词新闻或新增新闻
            has_matched_news = any(stat["count"] > 0 for stat in stats)
            has_new_news = bool(
                new_titles and any(len(titles) > 0 for titles in new_titles.values())
            )
            return has_matched_news or has_new_news

    def _load_analysis_data(
        self,
        quiet: bool = False,
    ) -> Optional[Tuple[Dict, Dict, Dict, Dict, List, List]]:
        """统一的数据加载和预处理，使用当前监控平台列表过滤历史数据"""
        try:
            # 获取当前配置的监控平台ID列表
            current_platform_ids = self.ctx.platform_ids
            if not quiet:
                print(f"当前监控平台: {current_platform_ids}")

            all_results, id_to_name, title_info = self.ctx.read_today_titles(
                current_platform_ids, quiet=quiet
            )

            if not all_results:
                print("没有找到当天的数据")
                return None

            total_titles = sum(len(titles) for titles in all_results.values())
            if not quiet:
                print(f"读取到 {total_titles} 个标题（已按当前监控平台过滤）")

            new_titles = self.ctx.detect_new_titles(current_platform_ids, quiet=quiet)
            word_groups, filter_words, global_filters = self.ctx.load_frequency_words()

            return (
                all_results,
                id_to_name,
                title_info,
                new_titles,
                word_groups,
                filter_words,
                global_filters,
            )
        except Exception as e:
            print(f"数据加载失败: {e}")
            return None

    def _prepare_current_title_info(self, results: Dict, time_info: str) -> Dict:
        """从当前抓取结果构建标题信息"""
        title_info = {}
        for source_id, titles_data in results.items():
            title_info[source_id] = {}
            for title, title_data in titles_data.items():
                ranks = title_data.get("ranks", [])
                url = title_data.get("url", "")
                mobile_url = title_data.get("mobileUrl", "")

                title_info[source_id][title] = {
                    "first_time": time_info,
                    "last_time": time_info,
                    "count": 1,
                    "ranks": ranks,
                    "url": url,
                    "mobileUrl": mobile_url,
                }
        return title_info

    def _run_analysis_pipeline(
        self,
        data_source: Dict,
        mode: str,
        title_info: Dict,
        new_titles: Dict,
        word_groups: List[Dict],
        filter_words: List[str],
        id_to_name: Dict,
        failed_ids: Optional[List] = None,
        is_daily_summary: bool = False,
        global_filters: Optional[List[str]] = None,
        quiet: bool = False,
    ) -> Tuple[List[Dict], Optional[str]]:
        """统一的分析流水线：数据处理 → 统计计算 → HTML生成"""

        # 统计计算（使用 AppContext）
        stats, total_titles = self.ctx.count_frequency(
            data_source,
            word_groups,
            filter_words,
            id_to_name,
            title_info,
            new_titles,
            mode=mode,
            global_filters=global_filters,
            quiet=quiet,
        )

        # HTML生成（如果启用）
        html_file = None
        if self.ctx.config["STORAGE"]["FORMATS"]["HTML"]:
            # 获取扩展数据（用于 HTML 报告）
            from trendradar.notification.extended_renderer import get_latest_extended_data_from_storage
            extended_data = get_latest_extended_data_from_storage(self.storage_manager)

            # 添加股票名称（从配置中获取）
            if extended_data and extended_data.get('stock'):
                stock_config = self.ctx.config.get('STOCK', {}).get('SYMBOLS', {})
                for symbol in extended_data['stock']:
                    if symbol in stock_config:
                        extended_data['stock'][symbol]['name'] = stock_config[symbol].get('name', symbol)

            html_file = self.ctx.generate_html(
                stats,
                total_titles,
                failed_ids=failed_ids,
                new_titles=new_titles,
                id_to_name=id_to_name,
                mode=mode,
                is_daily_summary=is_daily_summary,
                update_info=self.update_info if self.ctx.config["SHOW_VERSION_UPDATE"] else None,
                extended_data=extended_data,
            )

        return stats, html_file

    def _send_notification_if_needed(
        self,
        stats: List[Dict],
        report_type: str,
        mode: str,
        failed_ids: Optional[List] = None,
        new_titles: Optional[Dict] = None,
        id_to_name: Optional[Dict] = None,
        html_file_path: Optional[str] = None,
    ) -> bool:
        """统一的通知发送逻辑，包含所有判断条件"""
        has_notification = self._has_notification_configured()
        cfg = self.ctx.config

        if (
            cfg["ENABLE_NOTIFICATION"]
            and has_notification
            and self._has_valid_content(stats, new_titles)
        ):
            # 推送窗口控制
            if cfg["PUSH_WINDOW"]["ENABLED"]:
                push_manager = self.ctx.create_push_manager()
                time_range_start = cfg["PUSH_WINDOW"]["TIME_RANGE"]["START"]
                time_range_end = cfg["PUSH_WINDOW"]["TIME_RANGE"]["END"]

                if not push_manager.is_in_time_range(time_range_start, time_range_end):
                    now = self.ctx.get_time()
                    print(
                        f"推送窗口控制：当前时间 {now.strftime('%H:%M')} 不在推送时间窗口 {time_range_start}-{time_range_end} 内，跳过推送"
                    )
                    return False

                if cfg["PUSH_WINDOW"]["ONCE_PER_DAY"]:
                    if push_manager.has_pushed_today():
                        print(f"推送窗口控制：今天已推送过，跳过本次推送")
                        return False
                    else:
                        print(f"推送窗口控制：今天首次推送")

            # 准备报告数据
            report_data = self.ctx.prepare_report(stats, failed_ids, new_titles, id_to_name, mode)

            # 添加扩展数据到报告数据
            self._add_extended_data_to_report(report_data)

            # 添加 AI 分析到报告数据
            self._add_ai_analysis_to_report(report_data, stats)

            # 是否发送版本更新信息
            update_info_to_send = self.update_info if cfg["SHOW_VERSION_UPDATE"] else None

            # 使用 NotificationDispatcher 发送到所有渠道
            dispatcher = self.ctx.create_notification_dispatcher()
            results = dispatcher.dispatch_all(
                report_data=report_data,
                report_type=report_type,
                update_info=update_info_to_send,
                proxy_url=self.proxy_url,
                mode=mode,
                html_file_path=html_file_path,
            )

            if not results:
                print("未配置任何通知渠道，跳过通知发送")
                return False

            # 如果成功发送了任何通知，且启用了每天只推一次，则记录推送
            if (
                cfg["PUSH_WINDOW"]["ENABLED"]
                and cfg["PUSH_WINDOW"]["ONCE_PER_DAY"]
                and any(results.values())
            ):
                push_manager = self.ctx.create_push_manager()
                push_manager.record_push(report_type)

            return True

        elif cfg["ENABLE_NOTIFICATION"] and not has_notification:
            print("⚠️ 警告：通知功能已启用但未配置任何通知渠道，将跳过通知发送")
        elif not cfg["ENABLE_NOTIFICATION"]:
            print(f"跳过{report_type}通知：通知功能已禁用")
        elif (
            cfg["ENABLE_NOTIFICATION"]
            and has_notification
            and not self._has_valid_content(stats, new_titles)
        ):
            mode_strategy = self._get_mode_strategy()
            if "实时" in report_type:
                if self.report_mode == "incremental":
                    has_new = bool(
                        new_titles and any(len(titles) > 0 for titles in new_titles.values())
                    )
                    if not has_new:
                        print("跳过实时推送通知：增量模式下未检测到新增的新闻")
                    else:
                        print("跳过实时推送通知：增量模式下新增新闻未匹配到关键词")
                else:
                    print(
                        f"跳过实时推送通知：{mode_strategy['mode_name']}下未检测到匹配的新闻"
                    )
            else:
                print(
                    f"跳过{mode_strategy['summary_report_type']}通知：未匹配到有效的新闻内容"
                )

        return False

    def _generate_summary_report(self, mode_strategy: Dict) -> Optional[str]:
        """生成汇总报告（带通知）"""
        summary_type = (
            "当前榜单汇总" if mode_strategy["summary_mode"] == "current" else "当日汇总"
        )
        print(f"生成{summary_type}报告...")

        # 加载分析数据
        analysis_data = self._load_analysis_data()
        if not analysis_data:
            return None

        all_results, id_to_name, title_info, new_titles, word_groups, filter_words, global_filters = (
            analysis_data
        )

        # 运行分析流水线
        stats, html_file = self._run_analysis_pipeline(
            all_results,
            mode_strategy["summary_mode"],
            title_info,
            new_titles,
            word_groups,
            filter_words,
            id_to_name,
            is_daily_summary=True,
            global_filters=global_filters,
        )

        if html_file:
            print(f"{summary_type}报告已生成: {html_file}")

        # 发送通知
        self._send_notification_if_needed(
            stats,
            mode_strategy["summary_report_type"],
            mode_strategy["summary_mode"],
            failed_ids=[],
            new_titles=new_titles,
            id_to_name=id_to_name,
            html_file_path=html_file,
        )

        return html_file

    def _generate_summary_html(self, mode: str = "daily") -> Optional[str]:
        """生成汇总HTML"""
        summary_type = "当前榜单汇总" if mode == "current" else "当日汇总"
        print(f"生成{summary_type}HTML...")

        # 加载分析数据（静默模式，避免重复输出日志）
        analysis_data = self._load_analysis_data(quiet=True)
        if not analysis_data:
            return None

        all_results, id_to_name, title_info, new_titles, word_groups, filter_words, global_filters = (
            analysis_data
        )

        # 运行分析流水线（静默模式，避免重复输出日志）
        _, html_file = self._run_analysis_pipeline(
            all_results,
            mode,
            title_info,
            new_titles,
            word_groups,
            filter_words,
            id_to_name,
            is_daily_summary=True,
            global_filters=global_filters,
            quiet=True,
        )

        if html_file:
            print(f"{summary_type}HTML已生成: {html_file}")
        return html_file

    def _initialize_and_check_config(self) -> None:
        """通用初始化和配置检查"""
        now = self.ctx.get_time()
        print(f"当前北京时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        if not self.ctx.config["ENABLE_CRAWLER"]:
            print("爬虫功能已禁用（ENABLE_CRAWLER=False），程序退出")
            return

        has_notification = self._has_notification_configured()
        if not self.ctx.config["ENABLE_NOTIFICATION"]:
            print("通知功能已禁用（ENABLE_NOTIFICATION=False），将只进行数据抓取")
        elif not has_notification:
            print("未配置任何通知渠道，将只进行数据抓取，不发送通知")
        else:
            print("通知功能已启用，将发送通知")

        mode_strategy = self._get_mode_strategy()
        print(f"报告模式: {self.report_mode}")
        print(f"运行模式: {mode_strategy['description']}")

    def _crawl_data(self) -> Tuple[Dict, Dict, List]:
        """执行数据爬取"""
        ids = []
        for platform in self.ctx.platforms:
            if "name" in platform:
                ids.append((platform["id"], platform["name"]))
            else:
                ids.append(platform["id"])

        print(
            f"配置的监控平台: {[p.get('name', p['id']) for p in self.ctx.platforms]}"
        )
        print(f"开始爬取数据，请求间隔 {self.request_interval} 毫秒")
        Path("output").mkdir(parents=True, exist_ok=True)

        results, id_to_name, failed_ids = self.data_fetcher.crawl_websites(
            ids, self.request_interval
        )

        # 转换为 NewsData 格式并保存到存储后端
        crawl_time = self.ctx.format_time()
        crawl_date = self.ctx.format_date()
        news_data = convert_crawl_results_to_news_data(
            results, id_to_name, failed_ids, crawl_time, crawl_date
        )

        # 保存到存储后端（SQLite）
        if self.storage_manager.save_news_data(news_data):
            print(f"数据已保存到存储后端: {self.storage_manager.backend_name}")

        # 保存 TXT 快照（如果启用）
        txt_file = self.storage_manager.save_txt_snapshot(news_data)
        if txt_file:
            print(f"TXT 快照已保存: {txt_file}")

        # 兼容：同时保存到原有 TXT 格式（确保向后兼容）
        if self.ctx.config["STORAGE"]["FORMATS"]["TXT"]:
            title_file = self.ctx.save_titles(results, id_to_name, failed_ids)
            print(f"标题已保存到: {title_file}")

        return results, id_to_name, failed_ids

    def _crawl_extended_data(self) -> Dict:
        """
        爬取扩展数据源（加密货币、股票、Twitter）

        Returns:
            扩展数据字典 {
                'crypto': {symbol: data},
                'stock': {symbol: data},
                'twitter': {author: [tweets]}
            }
        """
        extended_data = {
            'crypto': {},
            'stock': {},
            'twitter': {}
        }

        cfg = self.ctx.config

        # 1. 获取加密货币数据
        if cfg.get('CRYPTO', {}).get('ENABLE_CRYPTO', False):
            try:
                # 优先使用 CoinGecko（无地区限制），失败时回退到 Binance
                use_coingecko = cfg.get('CRYPTO', {}).get('USE_COINGECKO', False)

                if use_coingecko:
                    from trendradar.crawler.crypto_fetcher_coingecko import CryptoFetcherCoinGecko
                    fetcher_class = CryptoFetcherCoinGecko
                    print("使用 CoinGecko API（无地区限制）")
                else:
                    from trendradar.crawler.crypto_fetcher import CryptoFetcher
                    fetcher_class = CryptoFetcher
                    print("使用 Binance API")

                symbols = cfg['CRYPTO'].get('SYMBOLS', ['BTCUSDT', 'ETHUSDT'])
                print(f"正在获取加密货币数据: {symbols}")

                fetcher = fetcher_class(proxy_url=self.proxy_url if self.proxy_url else None)
                crypto_data = fetcher.fetch_ticker_24h(symbols)

                success_count = sum(1 for v in crypto_data.values() if v is not None)
                print(f"加密货币数据获取完成: {success_count}/{len(symbols)} 成功")

                extended_data['crypto'] = crypto_data
            except Exception as e:
                print(f"获取加密货币数据失败: {e}")

        # 2. 获取股票数据
        if cfg.get('STOCK', {}).get('ENABLE_STOCK', False):
            try:
                from trendradar.crawler.stock_fetcher import StockFetcher

                stock_config = cfg['STOCK'].get('SYMBOLS', {})
                if stock_config:
                    print(f"正在获取股票数据: {list(stock_config.keys())}")

                    fetcher = StockFetcher()
                    stock_data = fetcher.fetch_stocks(stock_config)

                    success_count = sum(1 for v in stock_data.values() if v is not None)
                    print(f"股票数据获取完成: {success_count}/{len(stock_config)} 成功")

                    extended_data['stock'] = stock_data
            except Exception as e:
                print(f"获取股票数据失败: {e}")

        # 3. 获取 Twitter 数据
        if cfg.get('TWITTER', {}).get('ENABLE_TWITTER', False):
            try:
                from trendradar.crawler.twitter_fetcher import TwitterFetcher

                users = cfg['TWITTER'].get('USERS', [])
                if users:
                    print(f"正在获取 Twitter 数据: {users}")

                    fetcher = TwitterFetcher()
                    for username in users:
                        tweets = fetcher.fetch_user_tweets(username, limit=5)
                        if tweets:
                            extended_data['twitter'][username] = tweets
                            print(f"Twitter @{username}: 获取到 {len(tweets)} 条推文")
                        else:
                            print(f"Twitter @{username}: 未获取到推文")
            except Exception as e:
                print(f"获取 Twitter 数据失败: {e}")

        return extended_data

    def _save_extended_data(self, extended_data: Dict) -> None:
        """
        保存扩展数据到数据库

        Args:
            extended_data: 扩展数据字典
        """
        if not extended_data:
            return

        crawl_time = self.ctx.format_time()
        crawl_date = self.ctx.format_date()

        # 保存加密货币数据
        if extended_data.get('crypto'):
            self.storage_manager.save_crypto_prices(
                extended_data['crypto'],
                crawl_time,
                crawl_date
            )

        # 保存股票数据
        if extended_data.get('stock'):
            self.storage_manager.save_stock_prices(
                extended_data['stock'],
                crawl_time,
                crawl_date
            )

        # 保存 Twitter 数据
        if extended_data.get('twitter'):
            for author, tweets in extended_data['twitter'].items():
                self.storage_manager.save_twitter_posts(
                    tweets,
                    author,
                    crawl_time,
                    crawl_date
                )

    def _run_ai_analysis(self, stats: List[Dict], extended_data: Optional[Dict] = None) -> Optional[Dict]:
        """
        运行 AI 综合分析

        Args:
            stats: 新闻热点统计
            extended_data: 扩展数据（可选）

        Returns:
            AI 分析结果字典或 None
        """
        # 检查是否启用 AI 分析
        ai_config = self.ctx.config.get('AI_ANALYSIS', {})
        if not ai_config.get('ENABLE_AI_ANALYSIS', False):
            return None

        try:
            from trendradar.ai import ClaudeAnalyzer

            print("\n运行 AI 综合分析...")

            # 获取配置
            api_key = ai_config.get('API_KEY') or ai_config.get('ANTHROPIC_API_KEY')
            model = ai_config.get('MODEL', 'claude-3-5-sonnet-20241022')

            # 创建分析器
            analyzer = ClaudeAnalyzer(api_key=api_key, model=model)

            # 运行分析
            result = analyzer.analyze_market_trends(
                news_stats=stats,
                extended_data=extended_data,
                date=self.ctx.format_date()
            )

            if result:
                # 保存分析结果
                crawl_time = self.ctx.format_time()
                crawl_date = self.ctx.format_date()

                self.storage_manager.save_ai_analysis(
                    analysis_content=result['analysis'],
                    analysis_type='comprehensive',
                    model=result['model'],
                    tokens_used=result['tokens_used'],
                    crawl_time=crawl_time,
                    crawl_date=crawl_date
                )

                # 估算成本
                cost = analyzer.estimate_cost(result['tokens_used'])
                print(f"✅ AI 分析完成")
                print(f"   - Tokens: {result['input_tokens']} 输入 + {result['output_tokens']} 输出 = {result['tokens_used']} 总计")
                print(f"   - 成本: ~${cost:.4f}")

                return result
            else:
                print("⚠️  AI 分析未生成结果")
                return None

        except ImportError:
            print("⚠️  未安装 anthropic 库，跳过 AI 分析")
            print("   安装命令: pip install anthropic")
            return None
        except ValueError as e:
            print(f"⚠️  {e}")
            return None
        except Exception as e:
            print(f"❌ AI 分析失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _add_extended_data_to_report(self, report_data: Dict) -> None:
        """
        从数据库获取最新扩展数据并添加到报告数据中

        Args:
            report_data: 报告数据字典（会被直接修改）
        """
        try:
            from trendradar.notification.extended_renderer import get_latest_extended_data_from_storage

            # 从存储中获取最新扩展数据
            extended_data = get_latest_extended_data_from_storage(self.storage_manager)

            if extended_data:
                # 添加股票名称（从配置中获取）
                if extended_data.get('stock'):
                    stock_config = self.ctx.config.get('STOCK', {}).get('SYMBOLS', {})
                    for symbol in extended_data['stock']:
                        if symbol in stock_config:
                            extended_data['stock'][symbol]['name'] = stock_config[symbol].get('name', symbol)

                report_data['extended_data'] = extended_data
                print("扩展数据已添加到推送报告")
            else:
                report_data['extended_data'] = None

        except Exception as e:
            print(f"获取扩展数据失败: {e}")
            report_data['extended_data'] = None

    def _add_ai_analysis_to_report(self, report_data: Dict, stats: List[Dict]) -> None:
        """
        运行 AI 分析并添加到报告数据中

        Args:
            report_data: 报告数据字典（会被直接修改）
            stats: 新闻热点统计数据
        """
        try:
            # 获取扩展数据（用于AI分析）
            extended_data = report_data.get('extended_data')

            # 运行 AI 分析
            ai_result = self._run_ai_analysis(stats, extended_data)

            # 添加到报告数据
            if ai_result:
                report_data['ai_analysis'] = ai_result.get('analysis', '')
            else:
                report_data['ai_analysis'] = None

        except Exception as e:
            print(f"添加 AI 分析失败: {e}")
            report_data['ai_analysis'] = None

    def _execute_mode_strategy(
        self, mode_strategy: Dict, results: Dict, id_to_name: Dict, failed_ids: List
    ) -> Optional[str]:
        """执行模式特定逻辑"""
        # 获取当前监控平台ID列表
        current_platform_ids = self.ctx.platform_ids

        new_titles = self.ctx.detect_new_titles(current_platform_ids)
        time_info = self.ctx.format_time()
        if self.ctx.config["STORAGE"]["FORMATS"]["TXT"]:
            self.ctx.save_titles(results, id_to_name, failed_ids)
        word_groups, filter_words, global_filters = self.ctx.load_frequency_words()

        # current模式下，实时推送需要使用完整的历史数据来保证统计信息的完整性
        if self.report_mode == "current":
            # 加载完整的历史数据（已按当前平台过滤）
            analysis_data = self._load_analysis_data()
            if analysis_data:
                (
                    all_results,
                    historical_id_to_name,
                    historical_title_info,
                    historical_new_titles,
                    _,
                    _,
                    _,
                ) = analysis_data

                print(
                    f"current模式：使用过滤后的历史数据，包含平台：{list(all_results.keys())}"
                )

                stats, html_file = self._run_analysis_pipeline(
                    all_results,
                    self.report_mode,
                    historical_title_info,
                    historical_new_titles,
                    word_groups,
                    filter_words,
                    historical_id_to_name,
                    failed_ids=failed_ids,
                    global_filters=global_filters,
                )

                combined_id_to_name = {**historical_id_to_name, **id_to_name}

                if html_file:
                    print(f"HTML报告已生成: {html_file}")

                # 发送实时通知（使用完整历史数据的统计结果）
                summary_html = None
                if mode_strategy["should_send_realtime"]:
                    self._send_notification_if_needed(
                        stats,
                        mode_strategy["realtime_report_type"],
                        self.report_mode,
                        failed_ids=failed_ids,
                        new_titles=historical_new_titles,
                        id_to_name=combined_id_to_name,
                        html_file_path=html_file,
                    )
            else:
                print("❌ 严重错误：无法读取刚保存的数据文件")
                raise RuntimeError("数据一致性检查失败：保存后立即读取失败")
        else:
            title_info = self._prepare_current_title_info(results, time_info)
            stats, html_file = self._run_analysis_pipeline(
                results,
                self.report_mode,
                title_info,
                new_titles,
                word_groups,
                filter_words,
                id_to_name,
                failed_ids=failed_ids,
                global_filters=global_filters,
            )
            if html_file:
                print(f"HTML报告已生成: {html_file}")

            # 发送实时通知（如果需要）
            summary_html = None
            if mode_strategy["should_send_realtime"]:
                self._send_notification_if_needed(
                    stats,
                    mode_strategy["realtime_report_type"],
                    self.report_mode,
                    failed_ids=failed_ids,
                    new_titles=new_titles,
                    id_to_name=id_to_name,
                    html_file_path=html_file,
                )

        # 生成汇总报告（如果需要）
        summary_html = None
        if mode_strategy["should_generate_summary"]:
            if mode_strategy["should_send_realtime"]:
                # 如果已经发送了实时通知，汇总只生成HTML不发送通知
                summary_html = self._generate_summary_html(
                    mode_strategy["summary_mode"]
                )
            else:
                # daily模式：直接生成汇总报告并发送通知
                summary_html = self._generate_summary_report(mode_strategy)

        # 打开浏览器（仅在非容器环境）
        if self._should_open_browser() and html_file:
            if summary_html:
                summary_url = "file://" + str(Path(summary_html).resolve())
                print(f"正在打开汇总报告: {summary_url}")
                webbrowser.open(summary_url)
            else:
                file_url = "file://" + str(Path(html_file).resolve())
                print(f"正在打开HTML报告: {file_url}")
                webbrowser.open(file_url)
        elif self.is_docker_container and html_file:
            if summary_html:
                print(f"汇总报告已生成（Docker环境）: {summary_html}")
            else:
                print(f"HTML报告已生成（Docker环境）: {html_file}")

        return summary_html

    def run(self) -> None:
        """执行分析流程"""
        try:
            self._initialize_and_check_config()

            mode_strategy = self._get_mode_strategy()

            # 爬取新闻数据
            results, id_to_name, failed_ids = self._crawl_data()

            # 爬取扩展数据源（加密货币、股票、Twitter）
            print("\n" + "=" * 60)
            print("开始爬取扩展数据源...")
            print("=" * 60)
            extended_data = self._crawl_extended_data()

            # 保存扩展数据
            if any(extended_data.values()):
                print("\n保存扩展数据到数据库...")
                self._save_extended_data(extended_data)
                print("扩展数据保存完成")
            else:
                print("未启用任何扩展数据源或数据获取失败")

            self._execute_mode_strategy(mode_strategy, results, id_to_name, failed_ids)

        except Exception as e:
            print(f"分析流程执行出错: {e}")
            raise
        finally:
            # 清理资源（包括过期数据清理和数据库连接关闭）
            self.ctx.cleanup()


def main():
    """主程序入口"""
    try:
        analyzer = NewsAnalyzer()
        analyzer.run()
    except FileNotFoundError as e:
        print(f"❌ 配置文件错误: {e}")
        print("\n请确保以下文件存在:")
        print("  • config/config.yaml")
        print("  • config/frequency_words.txt")
        print("\n参考项目文档进行正确配置")
    except Exception as e:
        print(f"❌ 程序运行错误: {e}")
        raise


if __name__ == "__main__":
    main()
