from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["News"]
articles_collection = db["articles"]

# Update all articles: add "likes" field if not present, initializing to 0
articles_collection.update_many(
    {"likes": {"$exists": False}},  # Only update articles missing "likes"
    {"$set": {"likes": 0}}
)

print("Likes field added to all articles!")