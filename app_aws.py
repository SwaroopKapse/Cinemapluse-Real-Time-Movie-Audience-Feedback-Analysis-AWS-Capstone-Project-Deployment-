from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from functools import wraps
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from datetime import datetime
from decimal import Decimal
import uuid
import os

# ===================== APP INIT =====================

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "cinemapulse-secret-key")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

DDB_USERS_TABLE = "Cinemapulse_Users"
DDB_MOVIES_TABLE = "Cinemapulse_Movies"
DDB_FEEDBACK_TABLE = "Cinemapulse_Feedback"

SNS_TOPIC_ARN = os.getenv(
    "SNS_TOPIC_ARN",
    "arn:aws:sns:us-east-1:253490788465:Cinemapulse_topic"
)

# ===================== JINJA FILTERS  =====================

@app.template_filter("format_date")
def format_date(value):
    if not value:
        return ""
    try:
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        return value.strftime("%B %d, %Y")
    except Exception:
        return value

@app.template_filter("format_duration")
def format_duration(minutes):
    try:
        minutes = int(minutes)
        return f"{minutes // 60}h {minutes % 60}m"
    except Exception:
        return minutes

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
        print(f"SNS ERROR (ignored): {e}")

# ===================== AUTH DECORATORS =====================

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper

# ===================== AUTH =====================

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        if not username or not email or not password:
            flash("All fields required", "error")
            return redirect(url_for("signup"))

        try:
            if get_users_table().get_item(Key={"username": username}).get("Item"):
                flash("Username already exists", "error")
                return redirect(url_for("signup"))

            get_users_table().put_item(Item={
                "username": username,
                "email": email,
                "password": password,
                "is_admin": False,
                "created_at": datetime.utcnow().isoformat()
            })

            send_sns_notification("New Signup", f"{username} registered")
            flash("Signup successful", "success")
            return redirect(url_for("login"))

        except ClientError as e:
            print(e)
            flash("Signup failed", "error")

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        try:
            user = get_users_table().get_item(Key={"username": username}).get("Item")
            if user and user["password"] == password:
                session["username"] = username
                session["is_admin"] = user.get("is_admin", False)
                flash("Login successful", "success")
                return redirect(url_for("index"))
        except ClientError as e:
            print(e)

        flash("Invalid credentials", "error")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ===================== MAIN =====================

@app.route("/")
def index():
    try:
        movies = get_movies_table().scan().get("Items", [])
    except ClientError:
        movies = []

    return render_template(
        "index.html",
        movies=movies,
        total_movies=len(movies),
        total_feedbacks=0,
        avg_rating=0.0
    )

@app.route("/movies")
def movies():
    try:
        movies = get_movies_table().scan().get("Items", [])
    except ClientError:
        movies = []
    return render_template("movies.html", movies=movies)

@app.route("/movie/<movie_id>")
def movie_detail(movie_id):
    movie = get_movies_table().get_item(Key={"movie_id": movie_id}).get("Item")

    try:
        feedbacks = get_feedback_table().scan().get("Items", [])
    except ClientError:
        feedbacks = []

    movie_feedbacks = [f for f in feedbacks if f.get("movie_id") == movie_id]

    return render_template("movie.html", movie=movie, feedbacks=movie_feedbacks)

# ===================== ANALYTICS =====================

@app.route("/analytics")
def analytics():
    age_distribution = {"18-25": 0, "26-35": 0, "36-45": 0, "46+": 0}

    try:
        feedbacks = get_feedback_table().scan().get("Items", [])
        movies = get_movies_table().scan().get("Items", [])
    except ClientError:
        feedbacks, movies = [], []

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

# ===================== FEEDBACK =====================

@app.route("/feedback/<movie_id>", methods=["GET", "POST"])
@login_required
def feedback(movie_id):
    if request.method == "POST":
        get_feedback_table().put_item(Item={
            "feedback_id": str(uuid.uuid4()),
            "movie_id": movie_id,
            "username": session["username"],
            "rating": Decimal(request.form.get("rating", "3")),
            "review": request.form.get("review", ""),
            "sentiment": request.form.get("sentiment", "neutral"),
            "created_at": datetime.utcnow().isoformat()
        })

        send_sns_notification("New Feedback", f"Feedback for {movie_id}")
        return redirect(url_for("index"))

    return render_template("feedback.html")

# ===================== API =====================

@app.route("/api/movies")
def api_movies():
    try:
        return jsonify(get_movies_table().scan().get("Items", []))
    except ClientError:
        return jsonify([])

# ===================== RUN =====================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
