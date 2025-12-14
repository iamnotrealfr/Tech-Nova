import feedparser
from bs4 import BeautifulSoup
import re
import requests
from newspaper import Article
from pymongo import MongoClient

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
tech_nova_db = client["News"]
article_collection = tech_nova_db["articles"]

# Data Cleaning for MongoDB Compatibility
def clean_article_data(article_data):
    cleaned_data = {}
    for key, value in article_data.items():
        cleaned_key = key.replace(".", "").replace("$", "")
        cleaned_data[cleaned_key] = value if value else "Summary not available"
    return cleaned_data

rss_feeds = {
    "NDTV Gadgets 360": "https://gadgets360.com/rss/news",
    "Reuters": "https://www.reutersagency.com/feed/?best-topics=technology",
    "The New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "The Guardian": "https://www.theguardian.com/uk/technology/rss",
    "NPR": "https://feeds.npr.org/1019/rss.xml",
    "Deutsche Welle (DW)": "https://rss.dw.com/xml/rss-en-technology",
    "The Indian Express": "https://indianexpress.com/section/technology/feed/",
    "The Hindu": "https://www.thehindu.com/sci-tech/technology/feeder/default.rss",
    "India Today": "https://www.indiatoday.in/rss/1206550",
    "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/technology/rssfeed.xml",
    "Bloomberg": "https://www.bloomberg.com/technology/rss",
    "The Wall Street Journal": "https://feeds.a.dj.com/rss/RSSWSJD.xml",
}

api_sources = [
    "bbc-news", "cnn", "the-washington-post", "al-jazeera-english",
    "associated-press", "usa-today", "nbc-news", "google-news",
    "google-news-in", "the-times-of-india", "hacker-news"
]

# Categories
categories = {
    "BLOCKCHAIN": ["blockchain", "crypto", "cryptocurrency", "Bitcoin", "Ethereum"],
    "STARTUPS": ["startup", "venture capital", "seed funding", "entrepreneurship", "founder"],
    "GADGET": ["smartphone", "tablet", "laptop", "wearable", "gadget", "iPhone", "Apple"],
    "INNOVATION": ["innovation", "breakthrough", "new technology", "disruption", "research"],
    "VEHICLE": ["electric vehicle", "automobile", "self-driving car", "autonomous car"],
    "SPACE": ["space", "NASA", "rocket", "Mars", "satellite", "space exploration"],
    "TESLA": ["Tesla", "Model S", "Model 3", "Model X", "Cybertruck"],
    "GOOGLE": ["Google", "Android", "Pixel", "Google Cloud", "Alphabet"],
    "META": ["Meta", "Facebook", "Instagram", "WhatsApp", "Oculus"],
    "CYBERSECURITY": ["cybersecurity", "data breach", "hacking", "ransomware", "phishing"],
    "HACKATHON": ["hackathon", "coding competition", "developer event", "tech event"],
    "APPS": ["app", "mobile app", "iOS", "Android app", "Play Store", "App Store"],
    "NVIDIA": ["Nvidia", "GPU", "RTX", "AI chip", "GeForce", "DLSS"],
    "AI": ["artificial intelligence", "machine learning", "deep learning", "neural network", "Elon Musk", "ChatGPT", "Deepseek", "BillGates", "SteveJobs", "OpenAI", r"\bAI\b"]
}
def clean_html(html):
    return BeautifulSoup(html, "html.parser").get_text()

# Category Classification
def classify_category(title, summary):
    text = f"{title} {summary}".lower()
    for category, keywords in categories.items():
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword.lower())}\b", text):
                return category
    return None

# Content Extraction Functions
def fetch_summary(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        article.nlp()
        return article.summary
    except Exception:
        return "Summary not available"

def fetch_image(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.top_image
    except Exception:
        return "No image available"

def store_article(article_data):
    cleaned_article_data = clean_article_data(article_data)
    article_collection.insert_one(cleaned_article_data)
    print(f"✅ Stored: {cleaned_article_data['title']}")

for source_name, url in rss_feeds.items():
    feed = feedparser.parse(url)
    for entry in feed.entries:
        title = entry.get("title", "No title available").strip()
        summary = clean_html(entry.get("summary", "No summary available")).strip()
        published_at = entry.get("published", "No date available").strip()
        category = classify_category(title, summary)
        if not category:
            continue

        article_data = {
            "source": source_name,
            "title": title,
            "url": entry.get("link", "No URL available").strip(),
            "published_at": published_at,
            "category": category,
            "summary": summary,
            "image_url": fetch_image(entry.get("link", ""))
        }
        store_article(article_data)

# API-Based News Fetching
BASE_URL = "https://newsapi.org/v2/everything"
API_KEY = "57ae2db885614116b7bfb03b921e4868"

for source in api_sources:
    params = {
        "q": "technology",
        "sources": source,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 25,
        "apiKey": API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()

    for article in data.get("articles", []):
        title = article.get("title", "No title available")
        description = article.get("description", "No description available")
        published_at = article.get("publishedAt", "No date available")
        category = classify_category(title, description)
        if not category:
            continue

        article_data = {
            "source": article.get("source", {}).get("name", "Unknown Source"),
            "title": title,
            "url": article.get("url", "No URL available"),
            "category": category,
            "published_at": published_at,
            "summary": fetch_summary(article.get("url", "")),
            "image_url": article.get("urlToImage", "No image available")
        }
        store_article(article_data)

print("Successfully fetched and stored relevant tech news!")