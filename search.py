"""
Advanced Search and Filtering Module for Twitter Trends
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import re


class TrendSearch:
    """Advanced search and filtering for Twitter trends"""
    
    def __init__(self, db_collection):
        self.collection = db_collection
    
    def search_trends(
        self,
        query: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_trend_count: Optional[int] = None,
        max_trend_count: Optional[int] = None,
        sort_by: str = "date_time",
        sort_order: str = "desc",
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Search trends with multiple filters"""
        filter_query = {}
        
        if query:
            filter_query["$or"] = [
                {"trends": {"$regex": query, "$options": "i"}},
                {"ip_address": {"$regex": query, "$options": "i"}}
            ]
        
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        if date_filter:
            filter_query["date_time"] = date_filter
        
        count_filter = {}
        if min_trend_count is not None:
            count_filter["$gte"] = min_trend_count
        if max_trend_count is not None:
            count_filter["$lte"] = max_trend_count
        if count_filter:
            filter_query["trend_count"] = count_filter
        
        sort_direction = -1 if sort_order == "desc" else 1
        
        cursor = self.collection.find(filter_query)
        cursor = cursor.sort(sort_by, sort_direction)
        cursor = cursor.skip(skip).limit(limit)
        
        results = list(cursor)
        
        for result in results:
            result["trend_count"] = len(result.get("trends", []))
        
        return results
    
    def filter_trends_by_category(
        self,
        trends: List[str],
        categories: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[str]:
        """Filter trends by category or exclude patterns"""
        filtered = trends.copy()
        
        if categories:
            category_keywords = {
                'sports': ['sports', 'game', 'match', 'team', 'player', 'football', 'basketball', 'soccer'],
                'politics': ['politics', 'election', 'vote', 'government', 'president', 'congress'],
                'technology': ['tech', 'technology', 'ai', 'software', 'app', 'digital', 'cyber'],
                'entertainment': ['movie', 'music', 'celebrity', 'show', 'film', 'album', 'concert'],
                'business': ['business', 'economy', 'market', 'stock', 'finance', 'trade']
            }
            
            filtered = [
                trend for trend in filtered
                if any(
                    keyword in trend.lower()
                    for category in categories
                    for keyword in category_keywords.get(category, [category])
                )
            ]
        
        if exclude_patterns:
            filtered = [
                trend for trend in filtered
                if not any(re.search(pattern, trend, re.IGNORECASE) for pattern in exclude_patterns)
            ]
        
        return filtered
    
    def get_trending_stats(
        self,
        days: int = 7,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """Get trending statistics for the last N days"""
        start_date = datetime.now() - timedelta(days=days)
        
        results = self.collection.find({
            "date_time": {"$gte": start_date}
        })
        
        trend_counts = {}
        for record in results:
            for trend in record.get("trends", []):
                trend_lower = trend.lower()
                trend_counts[trend_lower] = trend_counts.get(trend_lower, 0) + 1
        
        sorted_trends = sorted(
            trend_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        return {
            "period_days": days,
            "total_records": self.collection.count_documents({"date_time": {"$gte": start_date}}),
            "unique_trends": len(trend_counts),
            "top_trends": [
                {"trend": trend, "mentions": count}
                for trend, count in sorted_trends
            ]
        }
    
    def get_latest_trends(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get the most recent trend records"""
        return self.search_trends(sort_by="date_time", sort_order="desc", limit=limit)
    
    def search_trends_by_popularity(
        self,
        min_mentions: int = 2,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Find trends that appear multiple times (popular trends)"""
        start_date = datetime.now() - timedelta(days=days)
        
        pipeline = [
            {"$match": {"date_time": {"$gte": start_date}}},
            {"$unwind": "$trends"},
            {"$group": {
                "_id": {"$toLower": "$trends"},
                "mentions": {"$sum": 1},
                "first_seen": {"$min": "$date_time"},
                "last_seen": {"$max": "$date_time"}
            }},
            {"$match": {"mentions": {"$gte": min_mentions}}},
            {"$sort": {"mentions": -1}}
        ]
        
        return list(self.collection.aggregate(pipeline))


def parse_date_string(date_str: str) -> Optional[datetime]:
    """Parse date string in various formats"""
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None
