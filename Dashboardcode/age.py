from pymongo import MongoClient
import math

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["News"]
users_collection = db["users"]
age_groups_collection = db["User_Age_Distribution"]

# Clear old data if the collection already exists
age_groups_collection.delete_many({})

# Aggregation: Group by age bucket (10-year gaps)
pipeline = [
    {
        "$match": {
            "age": {"$type": "int"}  # Ensure age is a number
        }
    },
    {
        "$project": {
            "age_group": {
                "$concat": [
                    {"$toString": {"$multiply": [{"$floor": {"$divide": ["$age", 10]}}, 10]}},
                    "-",
                    {"$toString": {"$add": [{"$multiply": [{"$floor": {"$divide": ["$age", 10]}}, 10]}, 9]}}
                ]
            }
        }
    },
    {
        "$group": {
            "_id": "$age_group",
            "count": {"$sum": 1}
        }
    },
    {
        "$sort": {"_id": 1}
    }
]

# Run the aggregation
results = list(users_collection.aggregate(pipeline))

# Insert into a new collection
age_groups_collection.insert_many(results)

print("✅ Age group user counts stored in 'age_groups_count' collection.")