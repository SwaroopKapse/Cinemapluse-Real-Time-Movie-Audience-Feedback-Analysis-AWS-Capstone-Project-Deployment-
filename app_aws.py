from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from functools import wraps
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from datetime import datetime
from decimal import Decimal
import uuid
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "cinemapulse-secret-key")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DDB_USERS_TABLE = "CinemaPulse_Users"
DDB_MOVIES_TABLE = "CinemaPulse_Movies"
DDB_FEEDBACK_TABLE = "CinemaPulse_Feedback"
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:253490788465:Cinemapulse_topic")

def get_dynamodb():
    return boto3.resource("dynamodb", region_name=AWS_REGION)

def get_users_table():
    return get_dynamodb().Table(DDB_USERS_TABLE)

def get_movies_table():
    return get_dynamodb().Table(DDB_MOVIES_TABLE)

def get_feedback_table():
    return get_dynamodb().Table(DDB_FEEDBACK_TABLE)

def get_sns():
    return boto3.client("sns", region_name=AWS_REGION)

def send_sns_notification(subject, message):
    try:
        get_sns().publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=message)
    except Exception as e:
        print(f"SNS ERROR (non-critical): {e}")

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin access required", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        
        if not username or not email or not password:
            flash("All fields required", "error")
            return redirect(url_for("signup"))
        
        if len(password) < 6:
            flash("Password must be at least 6 characters", "error")
            return redirect(url_for("signup"))
        
        try:
            response = get_users_table().query(
                IndexName="username-index",
                KeyConditionExpression=Key("username").eq(username)
            )
            if response.get("Items"):
                flash("Username already exists", "error")
                return redirect(url_for("signup"))
            
            user_id = str(uuid.uuid4())
            get_users_table().put_item(Item={
                "user_id": user_id, "username": username, "email": email,
                "password": password, "is_admin": False,
                "created_at": datetime.utcnow().isoformat()
            })
            send_sns_notification("New User Signup", f"User {username} registered with email {email}")
            flash("Signup successful! Please log in.", "success")
            return redirect(url_for("login"))
        except ClientError as e:
            print(f"Signup Error: {e}")
            flash("Signup failed. Please try again.", "error")
            return redirect(url_for("signup"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        if not username or not password:
            flash("Username and password required", "error")
            return redirect(url_for("login"))
        
        try:
            response = get_users_table().query(
                IndexName="username-index",
                KeyConditionExpression=Key("username").eq(username)
            )

            if response.get("Items"):
                user = response["Items"][0]
                if user.get("password") == password:
                    session["user_id"] = user["user_id"]
                    session["username"] = user["username"]
                    session["is_admin"] = user.get("is_admin", False)
                    send_sns_notification("User Login", f"User {username} logged in")
                    flash(f"Welcome, {username}!", "success")
                    return redirect(url_for("index"))

            flash("Invalid username or password", "error")
        except ClientError as e:
            print(f"Login Error: {e}")
            flash("Login failed. Please try again.", "error")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("index"))

@app.route("/")
def index():
    try:
        movies = get_movies_table().scan().get("Items", [])
        return render_template("index.html", movies=movies, now_showing=[], upcoming=[], 
                             total_movies=len(movies), total_feedbacks=0, avg_rating=0.0)
    except ClientError as e:
        print(f"Index Error: {e}")
        flash("Error loading home page", "error")
        return render_template("index.html", movies=[], now_showing=[], upcoming=[],
                             total_movies=0, total_feedbacks=0, avg_rating=0.0)

@app.route("/movies")
def movies():
    try:
        movies_list = get_movies_table().scan().get("Items", [])
        return render_template("movies.html", movies=movies_list)
    except ClientError as e:
        print(f"Movies Error: {e}")
        flash("Error loading movies", "error")
        return render_template("movies.html", movies=[])

@app.route("/movie/<movie_id>")
def movie_detail(movie_id):
    try:
        movie = get_movies_table().get_item(Key={"movie_id": movie_id}).get("Item")
        if not movie:
            flash("Movie not found", "error")
            return redirect(url_for("index"))
        feedbacks = get_feedback_table().query(
            IndexName="movie_id-index",
            KeyConditionExpression=Key("movie_id").eq(movie_id)
        ).get("Items", [])
        return render_template("movie.html", movie=movie, feedbacks=feedbacks)
    except ClientError as e:
        print(f"Movie Detail Error: {e}")
        flash("Error loading movie", "error")
        return redirect(url_for("index"))

@app.route("/analytics")
def analytics():
    try:
        feedbacks = get_feedback_table().scan().get("Items", [])
        movies = get_movies_table().scan().get("Items", [])
        return render_template("analytics.html", total_feedbacks=len(feedbacks),
            total_movies=len(movies), avg_rating=0.0,
            sentiment_stats={"positive": 0, "neutral": 0, "negative": 0},
            rating_dist={}, top_movies=[], recent_feedbacks=[])
    except ClientError as e:
        print(f"Analytics Error: {e}")
        flash("Error loading analytics", "error")
        return render_template("analytics.html", total_feedbacks=0, total_movies=0, avg_rating=0.0,
            sentiment_stats={"positive": 0, "neutral": 0, "negative": 0},
            rating_dist={}, top_movies=[], recent_feedbacks=[])

@app.route("/profile")
@login_required
def profile():
    try:
        user = get_users_table().get_item(Key={"user_id": session["user_id"]}).get("Item")
        feedbacks = get_feedback_table().scan().get("Items", [])
        user_feedbacks = [f for f in feedbacks if f.get("user_id") == session["user_id"]]
        return render_template("profile.html", user=user, feedbacks=user_feedbacks)
    except ClientError as e:
        print(f"Profile Error: {e}")
        flash("Error loading profile", "error")
        return render_template("profile.html", user={}, feedbacks=[])

@app.route("/feedback/<movie_id>", methods=["GET", "POST"])
@login_required
def feedback(movie_id):
    if request.method == "POST":
        try:
            feedback_id = str(uuid.uuid4())
            rating = int(request.form.get("rating", 3))
            review = request.form.get("review", "").strip()
            sentiment = request.form.get("sentiment", "neutral").strip()

            get_feedback_table().put_item(Item={
                "feedback_id": feedback_id, "movie_id": movie_id,
                "user_id": session["user_id"], "rating": Decimal(str(rating)),
                "review": review, "sentiment": sentiment,
                "created_at": datetime.utcnow().isoformat()
            })

            send_sns_notification("New Movie Feedback", f"New feedback for movie {movie_id}: {rating}/5 stars")
            flash("Feedback submitted successfully!", "success")
            return redirect(url_for("thankyou", movie_id=movie_id))
        except (ClientError, ValueError) as e:
            print(f"Feedback Error: {e}")
            flash("Error submitting feedback", "error")
            return redirect(url_for("feedback", movie_id=movie_id))

    return render_template("feedback.html")

@app.route("/thankyou/<movie_id>")
def thankyou(movie_id):
    try:
        movie = get_movies_table().get_item(Key={"movie_id": movie_id}).get("Item")
        return render_template("thankyou.html", movie=movie)
    except ClientError:
        return redirect(url_for("index"))

@app.route("/admin/create-movie", methods=["GET", "POST"])
@admin_required
def admin_create_movie():
    if request.method == "POST":
        try:
            movie_id = str(uuid.uuid4())
            title = request.form.get("title", "").strip()
            genre = request.form.get("genre", "").strip()
            status = request.form.get("status", "upcoming").strip()

            if not title or not genre:
                flash("Title and genre are required", "error")
                return redirect(url_for("admin_create_movie"))

            get_movies_table().put_item(Item={
                "movie_id": movie_id, "title": title, "genre": genre,
                "status": status, "created_at": datetime.utcnow().isoformat()
            })

            send_sns_notification("New Movie Added", f"Movie '{title}' has been added to the system")
            flash(f"Movie '{title}' created successfully!", "success")
            return redirect(url_for("index"))
        except ClientError as e:
            print(f"Admin Create Movie Error: {e}")
            flash("Error creating movie", "error")
            return redirect(url_for("admin_create_movie"))

    return render_template("admin_create_movie.html")

@app.route("/api/movies")
def api_movies():
    try:
        items = get_movies_table().scan().get("Items", [])
        return jsonify([dict(item) for item in items])
    except ClientError as e:
        print(f"API Movies Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/movie/<movie_id>/feedback")
def api_movie_feedback(movie_id):
    try:
        items = get_feedback_table().query(
            IndexName="movie_id-index",
            KeyConditionExpression=Key("movie_id").eq(movie_id)
        ).get("Items", [])
        return jsonify([dict(item) for item in items])
    except ClientError as e:
        print(f"API Feedback Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.template_filter('format_date')
def format_date(value):
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d').date()
        except:
            return value
    if hasattr(value, 'strftime'):
        return value.strftime('%B %d, %Y')
    return str(value)

@app.template_filter('format_duration')
def format_duration(minutes):
    if isinstance(minutes, (int, float)):
        hours = int(minutes) // 60
        mins = int(minutes) % 60
        return f"{hours}h {mins}m"
    return str(minutes)

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
