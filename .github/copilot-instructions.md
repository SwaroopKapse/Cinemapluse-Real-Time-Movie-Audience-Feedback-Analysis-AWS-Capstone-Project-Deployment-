# CinemaPulse: Copilot Instructions for AI Agents

## Project Overview

**CinemaPulse** is a Flask-based web application for real-time customer feedback analysis in the movie industry. The system tracks movies across three lifecycle stages (now showing, upcoming, released), collects user reviews with ratings and sentiment analysis, and provides dashboards with analytics insights.

### Core Technology Stack
- **Backend**: Flask (Python)
- **Frontend**: Jinja2 templates with vanilla JavaScript
- **Authentication**: Session-based (currently in-memory user storage)
- **Styling**: CSS with custom components

---

## Architecture & Data Patterns

### Backend Structure (app.py)
**Current State**: Flask app uses in-memory dictionary (`users = {}`) for user storage. Route patterns follow: authentication → dashboard/core features.

**Key Routes to Know**:
- **Auth Flow**: `/signup` → `/login` → session['user'] → `/dashboard`
- **Movie Browsing**: `/movies` (with filters) → `/movie_detail/<movie_id>`
- **Feedback**: `/feedback/<movie_id>` (form submission)
- **Analytics**: `/analytics` (future: dashboard view)
- **Admin**: `/admin` (future: management interface)

**Important Convention**: Routes check `if 'user' not in session: redirect(url_for('login'))` for protected pages. Always validate session before data access.

### Data Models (Implicit)
Movies have: `id, title, genre, status (now_showing|upcoming|released), release_date, duration, director, cast, description`

Feedbacks have: `rating (1-5), sentiment (positive|neutral|negative), text, movie_id, user_id`

Aggregations: `average_rating, total_feedbacks, rating_distribution (dict by star), sentiment_dist`

### Template Architecture
**Base Template** (../templates/base.html): Navigation bar with routes to Home, Movies, Analytics, Admin. Flash message system for user feedback. Footer with copyright year auto-update via JavaScript.

**Template Extension Pattern**: All pages extend `base.html` using `{% extends "base.html" %}` and `{% block content %}...{% endblock %}`. Custom filters like `|format_date` and `|format_duration` expected in Jinja environment.

**Current Templates** (../templates/):
- `home.html`: Hero + stats cards + movie grids (now showing/upcoming)
- `movies.html`: Browsable grid with status/genre filters
- `movie.html`: Detail view with stats, rating distribution chart, customer reviews
- `feedback.html`: (Empty - needs implementation)
- `analytics.html`: (Empty - needs implementation)
- `admin.html`: (Empty - needs implementation)

---

## Developer Workflows

### Running the Application
```bash
python app.py
```
Starts Flask dev server at `http://localhost:5000` with `debug=True` (auto-reload enabled).

### Adding New Routes
1. Define route decorator with methods: `@app.route('/path', methods=['GET', 'POST'])`
2. For protected routes, always check: `if 'user' not in session: return redirect(url_for('login'))`
3. Use `render_template('template.html', var=value)` to pass context to Jinja
4. Use `flash("message")` for user notifications (rendered in base template)

### Static Assets
- **CSS** (../static/style.css): Contains `.container`, `.form-container`, auth slide animations
- **JavaScript** (../static/script.js): Auth panel toggle (sign-in/sign-up switch)

---

## Project-Specific Patterns & Conventions

### Flask Custom Filters
Expected Jinja filters that need registration in app:
- `format_date`: Converts ISO date to readable format
- `format_duration`: Converts minutes to "Xh Xm" format

Register via: `app.jinja_env.filters['format_date'] = custom_format_date_function`

### Movie Status Lifecycle
Movies transition through three states: `upcoming` → `now_showing` → `released`
- CSS class names use: `status-{{ movie.status|replace('_', '-') }}` (hyphens, not underscores)
- Status badges styled in CSS with specific colors per state

### Authentication (In-Memory, Temporary)
Users stored as: `users[email] = {"name": name, "password": password}`
Session stores: `session['user'] = email` (not user object)
**Important**: No password hashing currently—this is development-only. Implement bcrypt for production.

### Rating & Sentiment Aggregation
Movie objects expose:
- `average_rating`: Float (1.0-5.0)
- `total_feedbacks`: Count
- `rating_distribution`: Dict `{1: count, 2: count, ..., 5: count}`
- `sentiment_dist`: Dict `{positive: count, neutral: count, negative: count}`

This data likely computed server-side before template rendering.

---

## Critical Integration Points

### Movie-to-Feedback Flow
Movie detail page links to feedback form via:
```jinja
<a href="{{ url_for('feedback', movie_id=movie.id) }}">Write a Review</a>
```
Feedback route must accept `movie_id`, validate it exists, render form, and on POST: save feedback + update movie aggregations.

### Chart Rendering
Rating distribution bar chart uses inline CSS width calculation:
```jinja
style="width: {{ (movie.rating_distribution[i] / movie.total_feedbacks * 100) ... }}%"
```
Division by zero handled with conditional `if movie.total_feedbacks > 0 else 0`.

### Navigation Context
All pages reference: `{{ url_for('index') }}`, `{{ url_for('movies') }}`, `{{ url_for('analytics') }}`, `{{ url_for('admin') }}` 
Ensure all routes have names matching these references (currently `home()` route uses `/` but is referenced as 'index' in templates—inconsistency to fix).

---

## Known Gaps & Future Work

- **Feedback & Analytics templates are empty** — implement these to complete core features
- **Data persistence**: In-memory storage only; integrate database (SQLite/PostgreSQL)
- **Sentiment analysis**: No actual NLP; placeholder for future ML integration
- **Admin interface**: Management of movies, user moderation
- **Route name mismatch**: `@app.route('/')` function is `home()` but templates expect `index`
