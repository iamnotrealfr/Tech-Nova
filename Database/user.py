from pymongo import MongoClient

# Step 1: Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Step 2: Access the existing database
db = client["News"]

# Step 3: Define the 'users' collection schema (no data insertion)
users_schema = {
    "_id": "ObjectId('unique_user_id')",
    "username": "",
    "email": "",
    "password": "",
    "gender": "",
    "age": None,
    "liked_articles": [],
    "reported_articles": [],
    "followed_channels": []
}

# Step 4: Create an empty 'users' collection
users_collection = db["users"]

# Step 5: Ensure indexes for unique fields
users_collection.create_index("email", unique=True)
users_collection.create_index("username", unique=True)

print("✅ Users collection schema is defined, but no data has been inserted.")