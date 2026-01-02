# coding=utf-8
"""
图表数据提取模块

从SQLite数据库提取历史数据，生成可视化图表所需的JSON数据
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3


def get_news_trend_data(
    storage_manager,
    crawl_date: str
) -> Dict[str, List]:
    """
    提取24小时新闻趋势数据

    Args:
        storage_manager: 存储管理器实例
        crawl_date: 爬取日期 (YYYY-MM-DD)

    Returns:
        {
            'labels': ['08:00', '09:00', '10:00', ...],
            'values': [45, 52, 48, ...]
        }
    """
    try:
        backend = storage_manager.get_backend()
        conn = backend._get_connection(crawl_date)
        cursor = conn.cursor()

        # 按小时统计新闻数量
        cursor.execute("""
            SELECT
                SUBSTR(crawl_time, 1, 2) || ':00' as hour,
                COUNT(DISTINCT id) as count
            FROM news_items
            WHERE crawl_date = ?
            GROUP BY SUBSTR(crawl_time, 1, 2)
            ORDER BY hour
        """, (crawl_date,))

        rows = cursor.fetchall()

        if not rows:
            return {'labels': [], 'values': []}

        labels = [row[0] for row in rows]
        values = [row[1] for row in rows]

        return {
            'labels': labels,
            'values': values
        }
    except Exception as e:
        print(f"Warning: Failed to extract news trend data: {e}")
        return {'labels': [], 'values': []}


def get_crypto_trend_data(
    storage_manager,
    crawl_date: str,
    days: int = 7
) -> Dict[str, any]:
    """
    提取加密货币多天走势数据

    Args:
        storage_manager: 存储管理器实例
        crawl_date: 当前爬取日期 (YYYY-MM-DD)
        days: 提取最近N天的数据

    Returns:
        {
            'labels': ['2026-01-01 08:00', '2026-01-01 09:00', ...],
            'datasets': {
                'BTC': [65000, 66000, ...],
                'ETH': [3500, 3550, ...],
                'BNB': [580, 585, ...]
            }
        }
    """
    try:
        backend = storage_manager.get_backend()

        # 计算开始日期
        end_date = datetime.strptime(crawl_date, '%Y-%m-%d')
        start_date = end_date - timedelta(days=days)

        # 收集所有日期的数据
        all_data = {}

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')

            try:
                conn = backend._get_connection(date_str)
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        crawl_date,
                        crawl_time,
                        symbol,
                        price_usd
                    FROM crypto_prices
                    WHERE crawl_date = ?
                    ORDER BY crawl_time
                """, (date_str,))

                rows = cursor.fetchall()

                for row in rows:
                    crawl_date_val, crawl_time, symbol, price = row
                    timestamp = f"{crawl_date_val} {crawl_time[:5]}"  # YYYY-MM-DD HH:MM

                    # 移除USDT后缀，只保留币种符号
                    symbol_clean = symbol.replace('USDT', '').replace('usdt', '')

                    if symbol_clean not in all_data:
                        all_data[symbol_clean] = []

                    all_data[symbol_clean].append({
                        'timestamp': timestamp,
                        'price': price
                    })

            except Exception as e:
                # 某些日期可能没有数据，跳过
                pass

            current_date += timedelta(days=1)

        # 如果没有数据，返回空结构
        if not all_data:
            return {'labels': [], 'datasets': {}}

        # 格式化为Chart.js需要的格式
        # 使用第一个币种的时间轴作为标签
        labels = []
        datasets = {}

        # 获取所有时间戳（使用第一个币种的数据）
        first_symbol = list(all_data.keys())[0]
        labels = [item['timestamp'] for item in all_data[first_symbol]]

        # 构建每个币种的数据数组
        for symbol, data_points in all_data.items():
            datasets[symbol] = [item['price'] for item in data_points]

        # 数据降采样：如果数据点超过100个，只保留关键点
        if len(labels) > 100:
            step = len(labels) // 50  # 保留约50个点
            labels = labels[::step]
            for symbol in datasets:
                datasets[symbol] = datasets[symbol][::step]

        return {
            'labels': labels,
            'datasets': datasets
        }

    except Exception as e:
        print(f"Warning: Failed to extract crypto trend data: {e}")
        return {'labels': [], 'datasets': {}}


def get_stock_trend_data(
    storage_manager,
    crawl_date: str,
    days: int = 7
) -> Dict[str, any]:
    """
    提取股票多天走势数据

    Args:
        storage_manager: 存储管理器实例
        crawl_date: 当前爬取日期 (YYYY-MM-DD)
        days: 提取最近N天的数据

    Returns:
        {
            'labels': ['2026-01-01 08:00', '2026-01-01 09:00', ...],
            'datasets': {
                'AAPL': [180.5, 181.2, ...],
                'TSLA': [245.3, 247.8, ...],
                ...
            }
        }
    """
    try:
        backend = storage_manager.get_backend()

        # 计算开始日期
        end_date = datetime.strptime(crawl_date, '%Y-%m-%d')
        start_date = end_date - timedelta(days=days)

        # 收集所有日期的数据
        all_data = {}

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')

            try:
                conn = backend._get_connection(date_str)
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        crawl_date,
                        crawl_time,
                        symbol,
                        price
                    FROM stock_prices
                    WHERE crawl_date = ?
                    ORDER BY crawl_time
                """, (date_str,))

                rows = cursor.fetchall()

                for row in rows:
                    crawl_date_val, crawl_time, symbol, price = row
                    timestamp = f"{crawl_date_val} {crawl_time[:5]}"  # YYYY-MM-DD HH:MM

                    if symbol not in all_data:
                        all_data[symbol] = []

                    all_data[symbol].append({
                        'timestamp': timestamp,
                        'price': price
                    })

            except Exception as e:
                # 某些日期可能没有数据，跳过
                pass

            current_date += timedelta(days=1)

        # 如果没有数据，返回空结构
        if not all_data:
            return {'labels': [], 'datasets': {}}

        # 格式化为Chart.js需要的格式
        labels = []
        datasets = {}

        # 获取所有时间戳（使用第一个股票的数据）
        first_symbol = list(all_data.keys())[0]
        labels = [item['timestamp'] for item in all_data[first_symbol]]

        # 构建每个股票的数据数组
        for symbol, data_points in all_data.items():
            datasets[symbol] = [item['price'] for item in data_points]

        # 数据降采样：如果数据点超过100个，只保留关键点
        if len(labels) > 100:
            step = len(labels) // 50  # 保留约50个点
            labels = labels[::step]
            for symbol in datasets:
                datasets[symbol] = datasets[symbol][::step]

        return {
            'labels': labels,
            'datasets': datasets
        }

    except Exception as e:
        print(f"Warning: Failed to extract stock trend data: {e}")
        return {'labels': [], 'datasets': {}}


def generate_chart_data(
    storage_manager,
    crawl_date: str
) -> Dict:
    """
    生成所有图表数据

    Args:
        storage_manager: 存储管理器实例
        crawl_date: 爬取日期 (YYYY-MM-DD)

    Returns:
        {
            'news_trend': {
                'labels': ['08:00', '09:00', ...],
                'values': [45, 52, ...]
            },
            'crypto_trend': {
                'labels': [...],
                'datasets': {'BTC': [...], 'ETH': [...]}
            },
            'stock_trend': {
                'labels': [...],
                'datasets': {'AAPL': [...], 'TSLA': [...]}
            },
            'generated_at': '2026-01-02T14:30:00'
        }
    """
    print("📊 Generating chart data...")

    news_trend = get_news_trend_data(storage_manager, crawl_date)
    print(f"  ✓ News trend: {len(news_trend.get('labels', []))} data points")

    crypto_trend = get_crypto_trend_data(storage_manager, crawl_date, days=7)
    print(f"  ✓ Crypto trend: {len(crypto_trend.get('labels', []))} data points, {len(crypto_trend.get('datasets', {}))} symbols")

    stock_trend = get_stock_trend_data(storage_manager, crawl_date, days=7)
    print(f"  ✓ Stock trend: {len(stock_trend.get('labels', []))} data points, {len(stock_trend.get('datasets', {}))} symbols")

    return {
        'news_trend': news_trend,
        'crypto_trend': crypto_trend,
        'stock_trend': stock_trend,
        'generated_at': datetime.now().isoformat()
    }
