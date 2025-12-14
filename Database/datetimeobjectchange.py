from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
tech_nova_db = client["News"]
article_collection = tech_nova_db["articles"]

# Update existing documents
for article in article_collection.find():
    published_at_str = article.get("published_at", "No date available")
    try:
        published_at = datetime.strptime(published_at_str, "%Y-%m-%dT%H:%M:%SZ")
        article_collection.update_one(
            {"_id": article["_id"]},
            {"$set": {"published_at": published_at}}
        )
        print(f"Updated: {article['title']}")
    except ValueError:
        print(f"Skipping invalid date for: {article['title']}")

