from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from config import Config
from database import db, Movie, Feedback, Analytics, User
from datetime import datetime, date
from sqlalchemy import func, desc



app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        
        if not all([username, email, password, confirm_password]):
            flash('All fields are required!', 'error')
            return redirect(url_for('signup'))
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('signup'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return redirect(url_for('signup'))
        
  
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('signup'))
        
    
        new_user = User(username=username, email=email, full_name=full_name)
        new_user.set_password(password)
        
       
        if User.query.count() == 0:
            new_user.is_admin = True
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    user_feedbacks = user.feedbacks.order_by(desc(Feedback.created_at)).all()
    return render_template('profile.html', user=user, feedbacks=user_feedbacks)


@app.route('/')
def index():
    now_showing = Movie.query.filter_by(status='now_showing').limit(6).all()
    upcoming = Movie.query.filter_by(status='upcoming').limit(3).all()
    
    total_movies = Movie.query.count()
    total_feedbacks = Feedback.query.count()
    avg_rating = db.session.query(func.avg(Feedback.rating)).scalar()
    avg_rating = round(avg_rating, 1) if avg_rating else 0.0
    
    return render_template('index.html', 
                         now_showing=now_showing,
                         upcoming=upcoming,
                         total_movies=total_movies,
                         total_feedbacks=total_feedbacks,
                         avg_rating=avg_rating)

@app.route('/movies')
def movies():
    status_filter = request.args.get('status', 'all')
    genre_filter = request.args.get('genre', 'all')
    
    query = Movie.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if genre_filter != 'all':
        query = query.filter(Movie.genre.contains(genre_filter))
    
    movies_list = query.order_by(desc(Movie.release_date)).all()
    
    all_genres = set()
    for movie in Movie.query.all():
        genres = movie.genre.split(', ')
        all_genres.update(genres)
    
    return render_template('movies.html', 
                         movies=movies_list,
                         status_filter=status_filter,
                         genre_filter=genre_filter,
                         all_genres=sorted(all_genres))

@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    recent_feedbacks = movie.feedbacks.order_by(desc(Feedback.created_at)).limit(10).all()
    
    sentiment_dist = {
        'positive': movie.feedbacks.filter_by(sentiment='positive').count(),
        'neutral': movie.feedbacks.filter_by(sentiment='neutral').count(),
        'negative': movie.feedbacks.filter_by(sentiment='negative').count()
    }
    
    return render_template('movie.html',
                         movie=movie,
                         feedbacks=recent_feedbacks,
                         sentiment_dist=sentiment_dist)

@app.route('/feedback/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def feedback(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        try:
            rating = int(request.form.get('rating'))
            review = request.form.get('review')
            watch_date_str = request.form.get('watch_date')
            age_group = request.form.get('age_group')
            would_recommend = request.form.get('would_recommend') == 'yes'
            
            if not watch_date_str:
                flash('Please select a date you watched the movie.', 'error')
                return redirect(url_for('feedback', movie_id=movie_id))
            
            watch_date = datetime.strptime(watch_date_str, '%Y-%m-%d').date()
            
            new_feedback = Feedback(
                movie_id=movie_id,
                user_id=user.id,
                customer_name=user.full_name or user.username,
                customer_email=user.email,
                rating=rating,
                review=review,
                watch_date=watch_date,
                age_group=age_group,
                would_recommend=would_recommend
            )
            
            new_feedback.analyze_sentiment()
            
            # db.session.add(new_feedback)
            # db.session.commit()
            db.session.add(new_feedback)
            db.session.commit()


            flash('Thank you for your feedback!', 'success')
            return redirect(url_for('thankyou', movie_id=movie_id))
            
        except ValueError as ve:
            db.session.rollback()
            flash('Invalid date format. Please select a valid date.', 'error')
            return redirect(url_for('feedback', movie_id=movie_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting feedback: {str(e)}', 'error')
            return redirect(url_for('feedback', movie_id=movie_id))
    
    today = date.today().isoformat()
    return render_template('feedback.html', movie=movie, user=user, today=today)

@app.route('/thankyou/<int:movie_id>')
def thankyou(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    return render_template('thankyou.html', movie=movie)

@app.route('/analytics')
def analytics():
    total_movies = Movie.query.count()
    total_feedbacks = Feedback.query.count()
    avg_rating = db.session.query(func.avg(Feedback.rating)).scalar()
    avg_rating = round(avg_rating, 1) if avg_rating else 0.0
    
    top_movies = []
    for movie in Movie.query.all():
        if movie.total_feedbacks > 0:
            top_movies.append({
                'movie': movie,
                'avg_rating': movie.average_rating,
                'total_feedbacks': movie.total_feedbacks
            })
    top_movies.sort(key=lambda x: x['avg_rating'], reverse=True)
    top_movies = top_movies[:5]
    
    sentiment_stats = {
        'positive': Feedback.query.filter_by(sentiment='positive').count(),
        'neutral': Feedback.query.filter_by(sentiment='neutral').count(),
        'negative': Feedback.query.filter_by(sentiment='negative').count()
    }
    
    age_groups = db.session.query(
        Feedback.age_group, 
        func.count(Feedback.id)
    ).group_by(Feedback.age_group).all()
    
    age_distribution = {age: count for age, count in age_groups}
    
    recent_feedbacks = Feedback.query.order_by(desc(Feedback.created_at)).limit(10).all()
    
    rating_dist = {}
    for i in range(1, 6):
        rating_dist[i] = Feedback.query.filter_by(rating=i).count()
    
    return render_template('analytics.html',
                         total_movies=total_movies,
                         total_feedbacks=total_feedbacks,
                         avg_rating=avg_rating,
                         top_movies=top_movies,
                         sentiment_stats=sentiment_stats,
                         age_distribution=age_distribution,
                         recent_feedbacks=recent_feedbacks,
                         rating_dist=rating_dist)

@app.route('/admin')
@admin_required
def admin():
    movies_list = Movie.query.order_by(desc(Movie.created_at)).all()
    total_users = User.query.count()
    return render_template('admin.html', movies=movies_list, total_users=total_users)

@app.route('/api/movies')
def api_movies():
    movies_list = Movie.query.all()
    return jsonify([{
        'id': m.id,
        'title': m.title,
        'genre': m.genre,
        'status': m.status,
        'average_rating': m.average_rating,
        'total_feedbacks': m.total_feedbacks
    } for m in movies_list])

@app.route('/api/movie/<int:movie_id>/stats')
def api_movie_stats(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    
    return jsonify({
        'average_rating': movie.average_rating,
        'total_feedbacks': movie.total_feedbacks,
        'rating_distribution': movie.rating_distribution,
        'sentiment_distribution': {
            'positive': movie.feedbacks.filter_by(sentiment='positive').count(),
            'neutral': movie.feedbacks.filter_by(sentiment='neutral').count(),
            'negative': movie.feedbacks.filter_by(sentiment='negative').count()
        }
    })

@app.template_filter('format_date')
def format_date(value):
    if isinstance(value, str):
        value = datetime.strptime(value, '%Y-%m-%d').date()
    return value.strftime('%B %d, %Y')

@app.template_filter('format_duration')
def format_duration(minutes):
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)