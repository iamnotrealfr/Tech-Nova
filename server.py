from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta,timezone
import random
import os
import bcrypt
import re
import requests 
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

client = MongoClient("mongodb://localhost:27017/")
news_db = client["News"]
article_collection = news_db["articles"]
users_collection = news_db["users"]

KEYWORDS = {
    "STARTUPS": ["startup", "venture capital", "seed funding", "entrepreneurship", "founder"],
    "INNOVATION": ["innovation", "breakthrough", "new technology", "disruption", "research"],
    "VEHICLE": ["electric vehicle", "automobile", "self-driving car", "autonomous car", "roadster", "SUV", "truck"],
    "SPACE": ["space", "NASA", "rocket", "Mars", "satellite", "space exploration"],
    "TESLA": ["Tesla", "Model S", "Model 3", "Model X", "Cybertruck"],
    "GOOGLE": ["Google", "Android", "Pixel", "Google Cloud", "Alphabet"],
    "META": ["Meta", "Facebook", "Instagram", "WhatsApp", "Oculus"],
    "HACKATHON": ["hackathon", "coding competition", "developer event", "tech event"],
    "NVIDIA": ["Nvidia", "GPU", "RTX", "AI chip", "GeForce", "DLSS"],
}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_image_url(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    print(f"Checking file: {upload_path}")  # Debug log
    if os.path.exists(upload_path):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    else:
        default_path = os.path.join(app.config['UPLOAD_FOLDER'], 'noimage.jpg')
        print(f"Fallback to: {default_path}")  # Debug log
        if os.path.exists(default_path):
            return send_from_directory(app.config['UPLOAD_FOLDER'], 'noimage.jpg')
        else:
            print("Error: noimage.jpg not found in uploads directory")
            return "Image not available", 404
    
@app.template_filter('truncatewords')
def truncate_at_word(text, max_length=300):
    if len(text) <= max_length:
        return text
    truncated = text[:max_length].rstrip()
    last_space = truncated.rfind(' ')
    if last_space != -1 and last_space > 0:
        truncated = truncated[:last_space]
    return truncated + "..."

@app.route("/user_dashboard")
def user_dashboard():
    if not session.get("user_email"):
        return redirect(url_for('home'))
    user_email = session.get("user_email")
    user = users_collection.find_one({"email": user_email})
    if not user:
        return redirect(url_for('home'))
    return render_template(
        "user_dashboard.html",
        username=user["username"],
        email=user["email"],
        likes=len(user["liked_articles"]),
        following=len(user["followed_channels"]),
        reports=len(user["reported_articles"]),
        age=user["age"],
        current_date=get_current_date()
    )

@app.route('/user_liked_articles', methods=['GET'])
def user_liked_articles():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    user = news_db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    liked_article_ids = [ObjectId(id) for id in user.get('liked_articles', [])]
    articles = list(news_db.articles.find({'_id': {'$in': liked_article_ids}}))
    
    # Prepare articles for frontend
    for article in articles:
        article['_id'] = str(article['_id'])
        article['is_liked'] = True
        article['is_following'] = article['source'] in user.get('followed_channels', [])
        article['is_reported'] = str(article['_id']) in user.get('reported_articles', [])
    
    return jsonify({'articles': articles})

@app.route('/user_followed_articles', methods=['GET'])
def user_followed_articles():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    user = news_db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    followed_sources = user.get('followed_channels', [])
    articles = list(news_db.articles.find({'source': {'$in': followed_sources}}).sort('published_at', -1).limit(20))
    
    for article in articles:
        article['_id'] = str(article['_id'])
        article['is_liked'] = str(article['_id']) in user.get('liked_articles', [])
        article['is_following'] = True
        article['is_reported'] = str(article['_id']) in user.get('reported_articles', [])
    
    return jsonify({'articles': articles})

@app.route('/user_reported_articles', methods=['GET'])
def user_reported_articles():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    user = news_db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    reported_article_ids = [ObjectId(id) for id in user.get('reported_articles', [])]
    articles = list(news_db.articles.find({'_id': {'$in': reported_article_ids}}))
    
    for article in articles:
        article['_id'] = str(article['_id'])
        article['is_liked'] = str(article['_id']) in user.get('liked_articles', [])
        article['is_following'] = article['source'] in user.get('followed_channels', [])
        article['is_reported'] = True
    
    return jsonify({'articles': articles})

def get_current_date():
    return datetime.now().strftime("%d-%b-%Y | %A").upper()

def get_articles(category=None, randomize=False, user_email=None):
    try:
        query = {"category": category} if category else {}
        articles_cursor = article_collection.find(query, {
            "title": 1, "source": 1, "url": 1, "category": 1,
            "published_at": 1, "summary": 1, "image_url": 1, "_id": 1, "likes": 1
        })
        articles_list = list(articles_cursor)
        
        followed_channels = []
        reported_articles = []
        liked_articles = []
        if user_email:
            user = users_collection.find_one({"email": user_email})
            if user:
                followed_channels = user.get("followed_channels", [])
                reported_articles = user.get("reported_articles", [])
                liked_articles = user.get("liked_articles", [])
        
        filtered_articles = []
        for article in articles_list:
            article["_id"] = str(article["_id"])
            image_url = article.get("image_url", "").strip()
            if (article["_id"] not in reported_articles and 
                article.get("summary", "") != "N/A" and 
                image_url and image_url.lower() not in ["no image available", "missing", "n/a"]):
                article["summary"] = truncate_at_word(article["summary"], 150)
                article["likes"] = article.get("likes", 0)  # Default to 0 if likes is missing
                article["is_following"] = article["source"] in followed_channels
                article["is_liked"] = article["_id"] in liked_articles
                if isinstance(article.get("published_at"), str):
                    try:
                        article["published_at"] = datetime.strptime(article["published_at"], "%Y-%m-%dT%H:%M:%SZ")
                    except ValueError:
                        article["published_at"] = datetime.now()
                filtered_articles.append(article)
        
        if randomize:
            random.shuffle(filtered_articles)
        
        return filtered_articles
    except Exception as e:
        print(f"Error fetching articles: {str(e)}")
        return []

def get_featured_articles(category=None, randomize=False, user_email=None):
    try:
        query = {"category": category} if category else {}
        articles_cursor = article_collection.find(query, {
            "title": 1, "source": 1, "url": 1, "category": 1,
            "published_at": 1, "summary": 1, "image_url": 1, "_id": 1, "likes": 1
        })
        articles_list = list(articles_cursor)
        
        followed_channels = []
        reported_articles = []
        liked_articles = []
        if user_email:
            user = users_collection.find_one({"email": user_email})
            if user:
                followed_channels = user.get("followed_channels", [])
                reported_articles = user.get("reported_articles", [])
                liked_articles = user.get("liked_articles", [])
        
        filtered_articles = []
        for article in articles_list:
            article["_id"] = str(article["_id"])
            image_url = article.get("image_url", "").strip()
            if (article["_id"] not in reported_articles and 
                article.get("summary", "") != "N/A" and 
                image_url and image_url.lower() not in ["no image available", "missing", "n/a"]):
                article["summary"] = truncate_at_word(article["summary"], 150)
                article["likes"] = article.get("likes", 0)  # Default to 0 if likes is missing
                article["is_following"] = article["source"] in followed_channels
                article["is_liked"] = article["_id"] in liked_articles
                if isinstance(article.get("published_at"), str):
                    try:
                        article["published_at"] = datetime.strptime(article["published_at"], "%Y-%m-%dT%H:%M:%SZ")
                    except ValueError:
                        article["published_at"] = datetime.now()
                filtered_articles.append(article)
        
        if randomize:
            random.shuffle(filtered_articles)
        
        return filtered_articles[:4]
    except Exception as e:
        print(f"Error fetching featured articles: {str(e)}")
        return []

@app.route("/register", methods=["POST"])
def register_user():
    data = request.json
    existing_user = users_collection.find_one({"email": data["email"]})
    
    if existing_user:
        return jsonify({"error": "Email already exists"}), 400

    hashed_password = bcrypt.hashpw(data["password"].encode('utf-8'), bcrypt.gensalt())
    new_user = {
        "username": data["username"],
        "email": data["email"],
        "password": hashed_password,
        "gender": data["gender"],
        "age": int(data["age"]),
        "liked_articles": [],
        "reported_articles": [],
        "followed_channels": [],
        "created_at": datetime.now()
    }
    
    result = users_collection.insert_one(new_user)
    if result.inserted_id:
        session["user_email"] = data["email"]
        return jsonify({"message": "User registered successfully", "user_id": str(result.inserted_id)}), 201
    return jsonify({"error": "Registration failed"}), 500

@app.route("/login", methods=["POST"])
def login_user():
    data = request.json
    print(f"Login attempt with usernameEmail: {data['usernameEmail']}")
    user = users_collection.find_one({
        "$or": [
            {"email": data["usernameEmail"]},
            {"username": data["usernameEmail"]}
        ]
    })
    
    if data["usernameEmail"] == "Admin" and data["password"] == "Admin":
        session["user_email"] = "admin@technova.com" 
        session["is_admin"] = True
        return redirect(url_for('dashboard'))
    
    if not user:
        print("User not found")
        return jsonify({"error": "Invalid credentials"}), 401
    
    if bcrypt.checkpw(data["password"].encode('utf-8'), user["password"]):
        print("Login successful")
        session["user_email"] = user["email"]
        return jsonify({
            "message": "Login successful",
            "user": {
                "username": user["username"],
                "email": user["email"],
                "likes": len(user["liked_articles"]),
                "following": len(user["followed_channels"]),
                "reports": len(user["reported_articles"])
            }
        }), 200
    else:
        print("Password mismatch")
        return jsonify({"error": "Invalid credentials"}), 401

@app.template_filter('format_date')
def format_date(value):
    if isinstance(value, datetime):
        return value.strftime('%d-%b-%Y')
    elif isinstance(value, str):
        try:
            # Try parsing common datetime formats
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.strftime('%d-%b-%Y')
        except ValueError:
            return value  # Return original string if parsing fails
    return value

@app.route("/dashboard")
def dashboard():
    if not session.get("is_admin"):
        return redirect(url_for('home'))
    
    total_articles = article_collection.count_documents({})
    total_users = users_collection.count_documents({})
    total_sources = len(article_collection.distinct("source"))
    user_growth_data = list(users_collection.aggregate([
        {"$group": {"_id": {"$dateToString": {"format": "%d-%b", "date": "$created_at"}}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]))
    growth_labels = [d["_id"] for d in user_growth_data]
    growth_data = [d["count"] for d in user_growth_data]

    most_followed_channels = users_collection.aggregate([
        {"$unwind": "$followed_channels"},
        {"$group": {"_id": "$followed_channels", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ])
    most_followed = list(most_followed_channels)
    channel_labels = [d["_id"] for d in most_followed]
    channel_data = [d["count"] for d in most_followed]

    category_likes = article_collection.aggregate([
        {"$group": {"_id": "$category", "likes": {"$sum": "$likes"}}},
        {"$sort": {"likes": -1}},
        {"$limit": 5}
    ])
    category_likes_list = list(category_likes)
    category_labels = [d["_id"] for d in category_likes_list]
    category_data = [d["likes"] for d in category_likes_list]

    gender_distribution = users_collection.aggregate([
        {"$group": {"_id": "$gender", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ])
    gender_data = list(gender_distribution)
    gender_labels = [d["_id"] or "Other" for d in gender_data]
    gender_values = [d["count"] for d in gender_data]

    age_distribution = users_collection.aggregate([
        {"$group": {"_id": {"$switch": {
            "branches": [
                {"case": {"$lte": ["$age", 24]}, "then": "18-24"},
                {"case": {"$lte": ["$age", 34]}, "then": "25-34"},
                {"case": {"$lte": ["$age", 44]}, "then": "35-44"},
                {"case": {"$lte": ["$age", 54]}, "then": "45-54"}
            ],
            "default": "55+"
        }}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ])
    age_data = list(age_distribution)
    age_labels = [d["_id"] for d in age_data]
    age_values = [d["count"] for d in age_data]

    return render_template(
        "dashboard.html",
        current_date=get_current_date(),
        total_articles=total_articles,
        total_users=total_users,
        total_sources=total_sources,
        growth_labels=growth_labels,
        growth_data=growth_data,
        channel_labels=channel_labels,
        channel_data=channel_data,
        category_labels=category_labels,
        category_data=category_data,
        gender_labels=gender_labels,
        gender_values=gender_values,
        age_labels=age_labels,
        age_values=age_values
    )
@app.route("/logout", methods=["GET"])
def logout():
    session.pop("user_email", None)
    return jsonify({"message": "Logged out successfully"}), 200

@app.route("/like", methods=["POST"])
def like_article():
    data = request.json
    user_email = session.get("user_email")
    if not user_email or not data.get("article_id"):
        return jsonify({"error": "User not logged in or missing article_id"}), 400
    
    try:
        # Add article to user's liked_articles
        users_collection.update_one(
            {"email": user_email}, 
            {"$addToSet": {"liked_articles": data["article_id"]}}
        )
        # Increment article's likes count
        article_collection.update_one(
            {"_id": ObjectId(data["article_id"])},
            {"$inc": {"likes": 1}}
        )
        
        user = users_collection.find_one({"email": user_email})
        return jsonify({
            "message": "Article liked",
            "user": {
                "likes": len(user["liked_articles"]),
                "following": len(user["followed_channels"]),
                "reports": len(user["reported_articles"])
            }
        }), 200
    except Exception as e:
        print(f"Error liking article: {str(e)}")
        return jsonify({"error": "Failed to like article"}), 500

@app.route("/unlike", methods=["POST"])
def unlike_article():
    data = request.json
    user_email = session.get("user_email")
    if not user_email or not data.get("article_id"):
        return jsonify({"error": "User not logged in or missing article_id"}), 400
    
    try:
        article_id = data["article_id"]
        # Validate and convert article_id to ObjectId
        object_id = ObjectId(article_id) if ObjectId.is_valid(article_id) else None
        if not object_id:
            return jsonify({"error": "Invalid article ID"}), 400

        # Remove article from user's liked_articles
        users_collection.update_one(
            {"email": user_email},
            {"$pull": {"liked_articles": article_id}}
        )

        # Decrement article's likes count, ensuring it doesn't go negative
        article_collection.update_one(
            {"_id": object_id},
            [{"$set": {"likes": {"$max": [{"$subtract": ["$likes", 1]}, 0]}}}]  # Use aggregation-style update
        )

        user = users_collection.find_one({"email": user_email})
        return jsonify({
            "message": "Article unliked",
            "user": {
                "likes": len(user["liked_articles"]),
                "following": len(user["followed_channels"]),
                "reports": len(user["reported_articles"])
            }
        }), 200
    except Exception as e:
        print(f"Error unliking article: {str(e)}")
        return jsonify({"error": "Failed to unlike article", "details": str(e)}), 500

@app.route("/follow", methods=["POST"])
def follow_channel():
    data = request.json
    user_email = session.get("user_email")
    if not user_email or not data.get("channel"):
        return jsonify({"error": "User not logged in or missing channel"}), 400
    
    result = users_collection.update_one(
        {"email": user_email},
        {"$addToSet": {"followed_channels": data["channel"]}}
    )
    
    user = users_collection.find_one({"email": user_email})
    if result.modified_count > 0 or result.matched_count > 0:
        return jsonify({
            "message": "Channel followed",
            "user": {
                "likes": len(user["liked_articles"]),
                "following": len(user["followed_channels"]),
                "reports": len(user["reported_articles"])
            }
        }), 200
    return jsonify({"error": "Failed to follow channel"}), 500
@app.route("/unfollow", methods=["POST"])

def unfollow_channel():
    data = request.json
    user_email = session.get("user_email")
    if not user_email or not data.get("channel"):
        return jsonify({"error": "User not logged in or missing channel"}), 400
    
    result = users_collection.update_one(
        {"email": user_email},
        {"$pull": {"followed_channels": data["channel"]}}
    )
    
    user = users_collection.find_one({"email": user_email})
    if result.modified_count > 0 or result.matched_count > 0:
        return jsonify({
            "message": "Channel unfollowed",
            "user": {
                "likes": len(user["liked_articles"]),
                "following": len(user["followed_channels"]),
                "reports": len(user["reported_articles"])
            }
        }), 200
    return jsonify({"error": "Failed to unfollow channel"}), 500

@app.route("/report", methods=["POST"])
def report_article():
    data = request.json
    user_email = session.get("user_email")
    if not user_email or not data.get("article_id"):
        return jsonify({"error": "User not logged in or missing article_id"}), 400
    
    user = users_collection.find_one({"email": user_email})
    article_id = data["article_id"]
    is_reported = article_id in user.get("reported_articles", [])
    
    if is_reported:
        # Remove from reported_articles
        result = users_collection.update_one(
            {"email": user_email},
            {"$pull": {"reported_articles": article_id}}
        )
        message = "Article unreported"
    else:
        # Add to reported_articles
        result = users_collection.update_one(
            {"email": user_email},
            {"$addToSet": {"reported_articles": article_id}}
        )
        message = "Article reported"
    
    user = users_collection.find_one({"email": user_email})
    return jsonify({
        "message": message,
        "user": {
            "likes": len(user["liked_articles"]),
            "following": len(user["followed_channels"]),
            "reports": len(user["reported_articles"])
        }
    }), 200

@app.route("/check_session", methods=["GET"])
def check_session():
    user_email = session.get("user_email")
    print(f"Checking session: user_email = {user_email}")
    try:
        if not user_email:
            return jsonify({"logged_in": False}), 200
        user = users_collection.find_one({"email": user_email})
        if user:
            return jsonify({
                "logged_in": True,
                "user": {
                    "username": user["username"],
                    "email": user["email"],
                    "likes": len(user["liked_articles"]),
                    "following": len(user["followed_channels"]),
                    "reports": len(user["reported_articles"])
                }
            }), 200
        return jsonify({"logged_in": False}), 200
    except Exception as e:
        print(f"Error in check_session: {str(e)}") 
        return jsonify({"logged_in": False, "error": "Internal server error"}), 500

def search_articles(query, user_email=None):
    try:
        query = query.lower().strip()
        matched_categories = []
        
        for category, keywords in KEYWORDS.items():
            if query in keywords or query == category.lower():
                matched_categories.append(category)
        
        if not matched_categories:
            articles_cursor = article_collection.find({
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"summary": {"$regex": query, "$options": "i"}},
                    {"source": {"$regex": query, "$options": "i"}}
                ]
            }, {
                "title": 1, "source": 1, "url": 1, "category": 1,
                "published_at": 1, "summary": 1, "image_url": 1, "_id": 1
            })
        else:
            articles_cursor = article_collection.find(
                {"category": {"$in": matched_categories}},
                {
                    "title": 1, "source": 1, "url": 1, "category": 1,
                    "published_at": 1, "summary": 1, "image_url": 1, "_id": 1
                }
            )
        
        articles_list = list(articles_cursor)
        
        followed_channels = []
        reported_articles = []
        if user_email:
            user = users_collection.find_one({"email": user_email})
            if user:
                followed_channels = user.get("followed_channels", [])
                reported_articles = user.get("reported_articles", [])
        
        filtered_articles = []
        for article in articles_list:
            article["_id"] = str(article["_id"])
            if article["_id"] not in reported_articles:
                article["summary"] = truncate_at_word(article["summary"], 150)
                article["likes"] = article.get("likes", 0)
                article["is_following"] = article["source"] in followed_channels
                filtered_articles.append(article)
        
        return filtered_articles
    except Exception as e:
        print(f"Error searching articles: {str(e)}")
        return []

@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query", "").strip()
    if not query:
        return render_template("search.html", search_results=[], query=query, current_date=get_current_date())
    
    user_email = session.get("user_email")
    search_results = search_articles(query, user_email=user_email)
    return render_template("search.html", search_results=search_results, query=query, current_date=get_current_date())

@app.route("/date", methods=["GET"])
def date_articles():
    selected_date = request.args.get("date", "").strip()
    if not selected_date:
        return render_template("date.html", articles=[], selected_date="No date selected", current_date=get_current_date())

    try:
        date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
        start_of_day = datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0, tzinfo=timezone.utc)
        end_of_day = datetime(date_obj.year, date_obj.month, date_obj.day, 23, 59, 59, tzinfo=timezone.utc)

        user_email = session.get("user_email")
        articles_cursor = article_collection.find({
            "published_at": {"$gte": start_of_day, "$lte": end_of_day}
        }, {
            "title": 1, "source": 1, "url": 1, "category": 1,
            "published_at": 1, "summary": 1, "image_url": 1, "_id": 1
        })
        articles_list = list(articles_cursor)

        followed_channels = []
        reported_articles = []
        if user_email:
            user = users_collection.find_one({"email": user_email})
            if user:
                followed_channels = user.get("followed_channels", [])
                reported_articles = user.get("reported_articles", [])

        filtered_articles = []
        for article in articles_list:
            article["_id"] = str(article["_id"])
            if article["_id"] not in reported_articles:
                article["summary"] = truncate_at_word(article["summary"], 150)
                article["likes"] = article.get("likes", 0)
                article["is_following"] = article["source"] in followed_channels
                filtered_articles.append(article)

        if not filtered_articles:
            return render_template(
                "date.html",
                articles=filtered_articles,
                selected_date=date_obj.strftime("%d-%b-%Y"),
                current_date=get_current_date(),
                error="No articles found for this date."
            )

        return render_template(
            "date.html",
            articles=filtered_articles,
            selected_date=date_obj.strftime("%d-%b-%Y"),
            current_date=get_current_date()
        )
    except Exception as e:
        print(f"Error fetching articles for date {selected_date}: {str(e)}")
        return render_template(
            "date.html",
            articles=[],
            selected_date=selected_date,
            current_date=get_current_date(),
            error="Invalid date or error fetching articles."
        )

@app.route("/")
def home():
    user_email = session.get("user_email") 
    articles = get_articles(randomize=True, user_email=user_email)
    featured_articles = get_featured_articles(randomize=True, user_email=user_email)
    current_date = get_current_date()
    return render_template("Home.html", articles=articles, featured_articles=featured_articles, current_date=current_date)

@app.route("/<page>")
def load_page(page):
    user_email = session.get("user_email")
    if page.lower() == "home":
        return home()
    
    category = page.upper()
    category_articles = get_articles(category, user_email=user_email)
    featured_articles = get_featured_articles(category=category, randomize=True, user_email=user_email)
    current_date = get_current_date()
    
    try:
        return render_template(
            f"{page}.html",
            articles=category_articles,
            category_articles=category_articles,
            featured_articles=featured_articles,
            current_date=current_date
        )
    except Exception as e:
        print(f"Error loading page {page}: {str(e)}")
        return f"Error loading {page}: {str(e)}", 404

@app.route("/api/articles", methods=["GET"])
def fetch_articles():
    user_email = session.get("user_email")
    return jsonify(get_articles(user_email=user_email))

if __name__ == "__main__":
    app.run(debug=True)