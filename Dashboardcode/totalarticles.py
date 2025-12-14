from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["News"]

# Collections
articles_collection = db["articles"]
article_count_collection = db["TOTAL_ARTICLES"]

# Step 1: Count total articles
total_articles = articles_collection.count_documents({})

# Step 2: Clear previous records (optional)
article_count_collection.delete_many({})

# Step 3: Insert the result into total_articles_count collection
article_count_collection.insert_one({
    "total_articles": total_articles
})

print(f"✅ Total articles ({total_articles}) stored in 'total_articles_count' collection.")