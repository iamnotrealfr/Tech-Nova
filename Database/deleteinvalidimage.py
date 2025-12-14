from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
news_db = client["News"]
article_collection = news_db["articles"]

# Update articles with invalid image URLs
for article in article_collection.find({"image_url": {"$regex": "missing.png", "$options": "i"}}):
    article_collection.update_one(
        {"_id": article["_id"]},
        {"$set": {"image_url": None}}  # Set to None or a default URL
    )
    print(f"Updated article {article['_id']} with invalid image URL")

# Optionally, set a default image for all articles without an image
article_collection.update_many(
    {"image_url": {"$exists": False}},
    {"$set": {"image_url": "/static/uploads/noimage.jpg"}}
)