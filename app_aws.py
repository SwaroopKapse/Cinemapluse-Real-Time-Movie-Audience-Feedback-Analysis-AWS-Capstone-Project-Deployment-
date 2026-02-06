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

SNS_TOPIC_ARN = os.getenv(
    "SNS_TOPIC_ARN",
    "arn:aws:sns:us-east-1:253490788465:Cinemapulse_topic"
)

# ===================== AWS HELPERS =====================

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
        get_sns().publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
    except Exception as e:
        print(f"SNS ERROR (non-critical): {e}")

# ===================== AUTH DECORATORS =====================

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
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

# ===================== AUTH ROUTES =====================

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
            existing = get_users_table().get_item(
                Key={"username": username}
            ).get("Item")

            if existing:
                flash("Username already exists", "error")
                return redirect(url_for("signup"))

            get_users_table().put_item(Item={
                "username": username,
                "email": email,
                "password": password,
                "is_admin": False,
                "created_at": datetime.utcnow().isoformat()
            })

            send_sns_notification(
                "New User Signup",
                f"User {username} registered"
            )

            flash("Signup successful! Please log in.", "success")
            return redirect(url_for("login"))

        except ClientError as e:
            print(f"Signup Error: {e}")
            flash("Signup failed", "error")
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
            response = get_users_table().get_item(
                Key={"username": username}
            )
            user = response.get("Item")

            if user and user["password"] == password:
                session["username"] = user["username"]
                session["is_admin"] = user.get("is_admin", False)

                send_sns_notification(
                    "User Login",
                    f"User {username} logged in"
                )

                flash(f"Welcome, {username}!", "success")
                return redirect(url_for("index"))

            flash("Invalid username or password", "error")

        except ClientError as e:
            print(f"Login Error: {e}")
            flash("Login failed", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("index"))

# ===================== MAIN PAGES =====================

@app.route("/")
def index():
    movies = get_movies_table().scan().get("Items", [])
    return render_template(
        "index.html",
        movies=movies,
        total_movies=len(movies),
        total_feedbacks=0,
        avg_rating=0.0
    )

@app.route("/movies")
def movies():
    movies_list = get_movies_table().scan().get("Items", [])
    return render_template("movies.html", movies=movies_list)

@app.route("/movie/<movie_id>")
def movie_detail(movie_id):
    movie = get_movies_table().get_item(
        Key={"movie_id": movie_id}
    ).get("Item")

    feedbacks = get_feedback_table().scan().get("Items", [])

    movie_feedbacks = [
        f for f in feedbacks if f.get("movie_id") == movie_id
    ]

    return render_template(
        "movie.html",
        movie=movie,
        feedbacks=movie_feedbacks
    )

# ===================== ANALYTICS =====================

@app.route("/analytics")
def analytics():
    feedbacks = get_feedback_table().scan().get("Items", [])
    movies = get_movies_table().scan().get("Items", [])

    age_distribution = {
        "18-25": 0,
        "26-35": 0,
        "36-45": 0,
        "46+": 0
    }

    return render_template(
        "analytics.html",
        total_feedbacks=len(feedbacks),
        total_movies=len(movies),
        avg_rating=0.0,
        sentiment_stats={"positive": 0, "neutral": 0, "negative": 0},
        rating_dist={},
        age_distribution=age_distribution,
        top_movies=[],
        recent_feedbacks=[]
    )

# ===================== PROFILE =====================

@app.route("/profile")
@login_required
def profile():
    user = get_users_table().get_item(
        Key={"username": session["username"]}
    ).get("Item")

    feedbacks = get_feedback_table().scan().get("Items", [])
    user_feedbacks = [
        f for f in feedbacks if f.get("username") == session["username"]
    ]

    return render_template(
        "profile.html",
        user=user,
        feedbacks=user_feedbacks
    )

# ===================== FEEDBACK =====================

@app.route("/feedback/<movie_id>", methods=["GET", "POST"])
@login_required
def feedback(movie_id):
    if request.method == "POST":
        feedback_id = str(uuid.uuid4())
        rating = int(request.form.get("rating", 3))
        review = request.form.get("review", "")
        sentiment = request.form.get("sentiment", "neutral")

        get_feedback_table().put_item(Item={
            "feedback_id": feedback_id,
            "movie_id": movie_id,
            "username": session["username"],
            "rating": Decimal(str(rating)),
            "review": review,
            "sentiment": sentiment,
            "created_at": datetime.utcnow().isoformat()
        })

        send_sns_notification(
            "New Feedback",
            f"Feedback added for movie {movie_id}"
        )

        flash("Feedback submitted!", "success")
        return redirect(url_for("index"))

    return render_template("feedback.html")

# ===================== API =====================

@app.route("/api/movies")
def api_movies():
    return jsonify(get_movies_table().scan().get("Items", []))

# ===================== RUN =====================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
