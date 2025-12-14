from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["News"]
articles_collection = db["articles"]
likes_count_collection = db["Likes_By_Category"]  # New collection

# Define specific categories to include
target_categories = ["AI", "Blockchain", "Cyber-Security", "Gadgets", "Apps"]

# Aggregation pipeline: Sum likes per category for selected ones only
likes_by_category = articles_collection.aggregate([
    {
        "$match": {
            "category": {"$in": target_categories}
        }
    },
    {
        "$group": {
            "_id": "$category",
            "total_likes": {"$sum": "$likes_count"}
        }
    },
    {
        "$sort": {"total_likes": -1}
    }
])

# Clear existing data in Likes_Count collection (optional)
likes_count_collection.delete_many({})

# Insert aggregated results into Likes_Count collection
for doc in likes_by_category:
    # Rename _id to category for better clarity
    likes_count_collection.insert_one({
        "category": doc["_id"],
        "total_likes": doc["total_likes"]
    })

print("✅ Likes count per category stored in 'Likes_Count' collection.")