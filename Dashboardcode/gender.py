from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["News"]
users_collection = db["users"]
gender_count_collection = db["User_Gender Distribution"]

# Aggregation pipeline to count users by gender
gender_counts = users_collection.aggregate([
    {
        "$group": {
            "_id": "$gender",
            "count": {"$sum": 1}
        }
    }
])

# Clear old data (optional)
gender_count_collection.delete_many({})

# Insert results into Gender_Count collection
for doc in gender_counts:
    gender_count_collection.insert_one({
        "gender": doc["_id"] if doc["_id"] else "Unspecified",
        "count": doc["count"]
    })

print("✅ Gender-wise user count stored in 'Gender_Count' collection.")