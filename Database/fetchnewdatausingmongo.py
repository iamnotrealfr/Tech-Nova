from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
tech_nova_db = client["News"]
article_collection = tech_nova_db["articles"]

# Fetch all articles with image URLs and count total articles
def fetch_all_articles():
    articles = list(article_collection.find())  # Convert cursor to list
    total_articles = len(articles)  # Count total articles
    
    print(f"Total Articles Found: {total_articles}\n")
    print("=" * 100)

    for article in articles:
        print(f"Title: {article.get('title', 'No title available')}")
        print(f"Source: {article.get('source', 'Unknown Source')}")
        print(f"Published At: {article.get('published_at', 'No date available')}")
        print(f"Category: {article.get('category', 'Uncategorized')}")
        print(f"Summary: {article.get('summary', 'No summary available')}")
        print(f"URL: {article.get('url', 'No URL available')}")
        print(f"Image URL: {article.get('image_url', 'No image available')}")
        print(f"Likes: {article.get('likes')}")
        print("-" * 100)

    return total_articles  # Return the count

# Run the function
total = fetch_all_articles()
print(f"\n✅ Successfully retrieved {total} articles!")