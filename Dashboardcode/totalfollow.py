from pymongo import MongoClient

# Step 1: Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["News"]
users_collection = db["users"]
output_collection = db["Most_Followed_News_Channels"]

# Step 2: Aggregation to count how many times each news source is followed
pipeline = [
    {"$unwind": "$followed_channels"},
    {"$group": {
        "_id": "$followed_channels",
        "follow_count": {"$sum": 1}
    }},
    {"$sort": {"follow_count": -1}}
]

# Step 3: Run the aggregation
results = list(users_collection.aggregate(pipeline))

# Step 4: Insert results into Most_Followed_News_Channels collection
# (Clear the collection first to avoid duplicates if rerunning)
output_collection.delete_many({})
output_collection.insert_many(results)

print("✅ Follow count per news source stored in 'Most_Followed_News_Channels' collection.")