from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["News"]

# Collections
users_collection = db["users"]
total_count_collection = db["TOTAL_USERS"]

# Step 1: Count total users
total_users = users_collection.count_documents({})

# Step 2: Clear old count data if needed
total_count_collection.delete_many({})

# Step 3: Store the count in a new collection
total_count_collection.insert_one({
    "description": "Total number of users",
    "total_users": total_users
})

print(f"✅ Total user count ({total_users}) stored in 'total_user_count' collection.")