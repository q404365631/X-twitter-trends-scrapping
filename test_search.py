"""
Tests for Advanced Search and Filtering Module
"""
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock
from search import TrendSearch, parse_date_string


class TestTrendSearch(unittest.TestCase):
    """Test cases for TrendSearch class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_collection = Mock()
        self.search = TrendSearch(self.mock_collection)
    
    def test_search_trends_with_query(self):
        """Test searching trends with text query"""
        mock_results = [
            {
                "_id": "123",
                "trends": ["Python", "Programming"],
                "date_time": datetime.now(),
                "ip_address": "192.168.1.1"
            }
        ]
        self.mock_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = mock_results
        
        results = self.search.search_trends(query="Python")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["trend_count"], 2)
    
    def test_filter_trends_by_category(self):
        """Test filtering trends by category"""
        trends = [
            "Football Match",
            "Python Programming",
            "Election Results",
            "New Movie Release"
        ]
        
        filtered = self.search.filter_trends_by_category(trends, categories=['sports'])
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0], "Football Match")
    
    def test_filter_trends_exclude_patterns(self):
        """Test excluding patterns from trends"""
        trends = ["Python", "JavaScript", "Python Tutorial"]
        
        filtered = self.search.filter_trends_by_category(
            trends,
            exclude_patterns=["Tutorial"]
        )
        
        self.assertEqual(len(filtered), 2)
        self.assertNotIn("Python Tutorial", filtered)
    
    def test_get_trending_stats(self):
        """Test getting trending statistics"""
        mock_results = [
            {
                "trends": ["Python", "AI"],
                "date_time": datetime.now()
            },
            {
                "trends": ["Python", "Machine Learning"],
                "date_time": datetime.now() - timedelta(days=1)
            }
        ]
        self.mock_collection.find.return_value = mock_results
        self.mock_collection.count_documents.return_value = 2
        
        stats = self.search.get_trending_stats(days=7, top_n=10)
        
        self.assertEqual(stats["period_days"], 7)
        self.assertEqual(stats["total_records"], 2)
        self.assertEqual(stats["unique_trends"], 3)
    
    def test_parse_date_string(self):
        """Test date string parsing"""
        date = parse_date_string("2024-01-15")
        self.assertIsNotNone(date)
        self.assertEqual(date.year, 2024)
        
        date = parse_date_string("invalid")
        self.assertIsNone(date)


if __name__ == '__main__':
    unittest.main()
