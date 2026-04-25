import subprocess
import time
from flask import Flask, render_template, jsonify
from pymongo import MongoClient
from search import TrendSearch, parse_date_string
from datetime import datetime, timedelta

app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017/")
db = client.twitter_trends

# Initialize search module
trend_search = TrendSearch(db.trends)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch-trends', methods=['GET'])
def fetch_trends():
    
    subprocess.run(['python', 'selenium_script.py'], check=True)  

    
    time.sleep(5)

    latest = db.trends.find_one(sort=[("date_time", -1)])

    return jsonify({
        "trends": latest["trends"],
        "date_time": latest["date_time"].strftime('%Y-%m-%d %H:%M:%S'),
        "ip_address": latest["ip_address"]
    })

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/search-trends', methods=['GET'])
def search_trends():
    """Advanced search endpoint for trends"""
    from flask import request
    
    query = request.args.get('q')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    min_count = request.args.get('min_count', type=int)
    max_count = request.args.get('max_count', type=int)
    sort_by = request.args.get('sort_by', 'date_time')
    sort_order = request.args.get('sort_order', 'desc')
    limit = request.args.get('limit', 50, type=int)
    skip = request.args.get('skip', 0, type=int)
    
    start_date = parse_date_string(start_date_str) if start_date_str else None
    end_date = parse_date_string(end_date_str) if end_date_str else None
    
    results = trend_search.search_trends(
        query=query,
        start_date=start_date,
        end_date=end_date,
        min_trend_count=min_count,
        max_trend_count=max_count,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        skip=skip
    )
    
    for result in results:
        result['_id'] = str(result['_id'])
        if 'date_time' in result:
            result['date_time'] = result['date_time'].strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify({
        "results": results,
        "total": len(results),
        "query": {
            "q": query,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
    })

@app.route('/trend-stats', methods=['GET'])
def trend_stats():
    """Get trending statistics"""
    from flask import request
    
    days = request.args.get('days', 7, type=int)
    top_n = request.args.get('top_n', 10, type=int)
    
    stats = trend_search.get_trending_stats(days=days, top_n=top_n)
    
    return jsonify(stats)

@app.route('/popular-trends', methods=['GET'])
def popular_trends():
    """Get popular trends (mentioned multiple times)"""
    from flask import request
    
    min_mentions = request.args.get('min_mentions', 2, type=int)
    days = request.args.get('days', 30, type=int)
    
    results = trend_search.search_trends_by_popularity(
        min_mentions=min_mentions,
        days=days
    )
    
    return jsonify({
        "results": results,
        "total": len(results)
    })

@app.route('/latest-trends', methods=['GET'])
def latest_trends():
    """Get latest trend records"""
    from flask import request
    
    limit = request.args.get('limit', 5, type=int)
    
    results = trend_search.get_latest_trends(limit=limit)
    
    for result in results:
        result['_id'] = str(result['_id'])
        if 'date_time' in result:
            result['date_time'] = result['date_time'].strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify({
        "results": results,
        "total": len(results)
    })
