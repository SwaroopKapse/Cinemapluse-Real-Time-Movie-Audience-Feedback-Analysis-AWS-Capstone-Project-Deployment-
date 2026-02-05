from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    feedbacks = db.relationship('Feedback', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Movie(db.Model):
    """Movie model for storing movie information"""
    __tablename__ = 'movies'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    director = db.Column(db.String(100), nullable=False)
    cast = db.Column(db.String(300), nullable=False)
    release_date = db.Column(db.Date, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    poster_url = db.Column(db.String(500), default='https://via.placeholder.com/300x450')
    trailer_url = db.Column(db.String(500))
    status = db.Column(db.String(20), default='upcoming')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    feedbacks = db.relationship('Feedback', backref='movie', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def average_rating(self):
        avg = db.session.query(func.avg(Feedback.rating)).filter(
            Feedback.movie_id == self.id
        ).scalar()
        return round(avg, 1) if avg else 0.0
    
    @property
    def total_feedbacks(self):
        return self.feedbacks.count()
    
    @property
    def rating_distribution(self):
        distribution = {}
        for i in range(1, 6):
            count = self.feedbacks.filter_by(rating=i).count()
            distribution[i] = count
        return distribution
    
    def __repr__(self):
        return f'<Movie {self.title}>'


class Feedback(db.Model):
    """Feedback model for storing customer reviews"""
    __tablename__ = 'feedbacks'
    
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(20))
    watch_date = db.Column(db.Date, nullable=False)
    age_group = db.Column(db.String(20))
    would_recommend = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Feedback {self.id} for Movie {self.movie_id}>'
    
    def analyze_sentiment(self):
        if self.rating >= 4:
            self.sentiment = 'positive'
        elif self.rating == 3:
            self.sentiment = 'neutral'
        else:
            self.sentiment = 'negative'


class Analytics(db.Model):
    """Analytics model for storing aggregated data"""
    __tablename__ = 'analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    total_feedbacks = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Float, default=0.0)
    positive_count = db.Column(db.Integer, default=0)
    neutral_count = db.Column(db.Integer, default=0)
    negative_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Analytics {self.date}>'