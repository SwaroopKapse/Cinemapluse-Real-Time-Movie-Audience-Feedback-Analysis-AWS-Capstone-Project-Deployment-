from app import app, db
from database import Movie, Feedback, Analytics, User
from datetime import datetime, date, timedelta
import random

def init_database():
    """Initialize database with sample data"""
    
    with app.app_context():
        print("Dropping existing tables...")
        db.drop_all()
        
        print("Creating new tables...")
        db.create_all()
        
        # Create admin user
        print("Creating admin user...")
        admin = User(
            username='admin',
            email='admin@cinemapulse.com',
            full_name='Admin User',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create sample users
        print("Creating sample users...")
        sample_users = [
            {'username': 'john_doe', 'email': 'john@email.com', 'full_name': 'John Doe', 'password': 'password123'},
            {'username': 'jane_smith', 'email': 'jane@email.com', 'full_name': 'Jane Smith', 'password': 'password123'},
            {'username': 'mike_wilson', 'email': 'mike@email.com', 'full_name': 'Mike Wilson', 'password': 'password123'},
            {'username': 'sarah_johnson', 'email': 'sarah@email.com', 'full_name': 'Sarah Johnson', 'password': 'password123'},
        ]
        
        users = [admin]
        for user_data in sample_users:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                full_name=user_data['full_name']
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            users.append(user)
        
        db.session.commit()
        print(f"Created {len(users)} users")
        
        # Sample movies data with WORKING poster URLs
        
        movies_data = [
            {
                'title': 'Dune: Part Two',
                'description': (
                'An epic adventure spanning across dimensions, following a group of travelers '
                'who must unite to save their world from an ancient evil.'
                 ),
                'genre': 'Action, Adventure, Fantasy',
                'director': 'Denis Villeneuve',
                'cast': 'Timothée Chalamet, Zendaya, Oscar Isaac',
                'release_date': date(2025, 12, 15),
                'duration': 166,
                'poster_url': 'https://image.tmdb.org/t/p/w500/6izwz7rsy95ARzTR3poZ8H6c5pp.jpg',
                'trailer_url': 'https://www.youtube.com/embed/Way9Dexny3w',
                'status': 'now_showing',
            },
            {
                'title': 'Pushpa 2: The Rule',
                'description': 'A crime action drama following a smuggler who rises to power in the underworld.',
                'genre': 'Action, Crime, Drama',
                'director': 'Sukumar',
                'cast': 'Allu Arjun, Rashmika Mandanna, Fahadh Faasil',
                'release_date': date(2024, 12, 5),
                'duration': 200,
                'poster_url': 'https://media.themoviedb.org/t/p/original/xkYGdKuK8jfqvGNCZV1uNdYkIfS.jpg',
                'trailer_url': 'https://www.youtube.com/embed/7n_XcJW8FEw',
                'status': 'now_showing'
            },
           {
            'title': 'Midnight in Paris',
            'description': (
                         'While on a trip to Paris with his fiancée\'s family, a nostalgic screenwriter '
                         'finds himself mysteriously going back to the 1920s every day at midnight.'
                         ),
            'genre': 'Romance, Comedy, Fantasy',
            'director': 'Woody Allen',
            'cast': 'Owen Wilson, Marion Cotillard, Rachel McAdams',
            'release_date': date(2011, 5, 11),
            'duration': 100,
            'poster_url': 'https://image.tmdb.org/t/p/w500/4wBG5kbfagTQclETblPRRGihk0I.jpg',
            'trailer_url': 'https://www.youtube.com/embed/FAfJgSxseCM',
            'status': 'released',
            },
            {
                'title': 'Blade Runner 2049',
                'description': (
                        'Thirty years after the events of the first film, a new blade runner, LAPD '
                          'Officer K, unearths a long-buried secret that has the potential to plunge '
                          'what\'s left of society into chaos. His discovery leads him on a quest to '
                         'find Rick Deckard, a former blade runner who has been missing for 30 years.'
                         ),               
                'genre': 'Sci-Fi, Thriller',
                'director': 'Denis Villeneuve',
                'cast': 'Ryan Gosling, Harrison Ford, Ana de Armas',
                'release_date': date(2025, 11, 22),
                'duration': 164,
                'poster_url': 'https://image.tmdb.org/t/p/w500/gajva2L0rPYkEWjzgFlBXCAVBE5.jpg',
                'trailer_url': 'https://www.youtube.com/embed/gCcx85zbxz4',
                'status': 'now_showing'
            },
            {
            'title': 'The Pianist',
            'description': (
                         'A Polish Jewish musician struggles to survive the destruction of the Warsaw '
                        'ghetto during World War II.'
                         ),
            'genre': 'Drama, Biography, War',
            'director': 'Roman Polanski',
            'cast': 'Adrien Brody, Thomas Kretschmann, Frank Finlay',
            'release_date': date(2002, 9, 24),
            'duration': 150,
            'poster_url': 'https://image.tmdb.org/t/p/w500/2hFvxCCWrTmCYwfy7yum0GKRi3Y.jpg',
            'trailer_url': 'https://www.youtube.com/embed/u_jE7-6Uv7E',
            'status': 'released',
            },
            {
            'title': "Ocean's Eleven",
            'description': (
                        'Danny Ocean and his crew plan an elaborate heist to rob three Las Vegas casinos '
                        'simultaneously.'
                    ),
            'genre': 'Crime, Comedy',
            'director': 'Steven Soderbergh',
            'cast': 'George Clooney, Brad Pitt, Matt Damon',
            'release_date': date(2001, 12, 7),
            'duration': 116,
            'poster_url': 'https://image.tmdb.org/t/p/w500/hQQCdZrsHtZyR6NbKH2YyCqd2fR.jpg',
            'trailer_url': 'https://www.youtube.com/embed/imm6OR605UI',
            'status': 'released',
            },
        
            {
            'title': 'Prisoners',
            'description': (
                'When two girls go missing, a father takes matters into his own hands while a '
                'detective pursues the truth.'
                ),
            'genre': 'Crime, Drama, Thriller',
            'director': 'Denis Villeneuve',
            'cast': 'Hugh Jackman, Jake Gyllenhaal, Paul Dano',
            'release_date': date(2013, 9, 20),
            'duration': 153,
            'poster_url': 'https://image.tmdb.org/t/p/w500/uhviyknTT5cEQXbn6vWIqfM4vGm.jpg',
            'trailer_url': 'https://www.youtube.com/embed/bLvqoRB4sKo',
            'status': 'released',
            },
           {
            'title': 'Dangal',
            'description': 'A father trains his daughters to become wrestlers.',
            'genre': 'Sports, Drama',
            'director': 'Nitesh Tiwari',
            'cast': 'Aamir Khan',
            'release_date': date(2016, 12, 21),
            'duration': 161,
            'poster_url': 'https://m.media-amazon.com/images/M/MV5BMTQ4MzQzMzM2Nl5BMl5BanBnXkFtZTgwMTQ1NzU3MDI@._V1_QL75_UX380_CR0,0,380,562_.jpg',
            'trailer_url': 'https://www.youtube.com/embed/x_7YlGv9u1g',
            'status': 'released'
            },
            {
            'title': '3 Idiots',
            'description': 'Three friends navigate college life and societal pressure.',
            'genre': 'Comedy, Drama',
            'director': 'Rajkumar Hirani',
            'cast': 'Aamir Khan, R. Madhavan, Sharman Joshi',
            'release_date': date(2009, 12, 25),
            'duration': 170,
            'poster_url': 'https://play-lh.googleusercontent.com/2plinRZ5j5LJ9fLBKbY8LRSmUjcHoJHQGnJtviRlhO9WF7T9eYfzMbPoGKydzKcnVZCI4Z8LXzxUV4Q10pQ=w240-h480-rw',
            'trailer_url': 'https://www.youtube.com/embed/K0eDlFX9GMc',
            'status': 'released'
            },
            {
            'title': 'RRR',
            'description': 'Two revolutionaries fight against British rule in pre-independence India.',
            'genre': 'Action, Drama',
            'director': 'S. S. Rajamouli',
            'cast': 'N. T. Rama Rao Jr., Ram Charan, Alia Bhatt',
            'release_date': date(2022, 3, 25),
            'duration': 182,
            'poster_url': 'https://image.tmdb.org/t/p/w500/wE0I6efAW4cDDmZQWtwZMOW44EJ.jpg',
            'trailer_url': 'https://www.youtube.com/embed/f_vbAtFSEc0',
            'status': 'released'
            },
            
            {
            'title': 'Salaar: Part 1 – Ceasefire',
            'description': 'A violent man rises to power in a dystopian kingdom ruled by bloodshed.',
            'genre': 'Action, Drama, Thriller',
            'director': 'Prashanth Neel',
            'cast': 'Prabhas, Prithviraj Sukumaran, Shruti Haasan',
            'release_date': date(2023, 12, 22),
            'duration': 175,
            'poster_url': 'https://image.tmdb.org/t/p/w500/5mzr6JZbrqnqD8rCEvPhuCE5Fw2.jpg',
            'trailer_url': 'https://www.youtube.com/embed/4GPvYMKtrtI',
            'status': 'released'
            },
            {
            'title': 'Pathaan',
            'description': 'An Indian spy takes on a deadly mercenary to protect national security.',
            'genre': 'Action, Thriller',
            'director': 'Siddharth Anand',
            'cast': 'Shah Rukh Khan, Deepika Padukone, John Abraham',
            'release_date': date(2023, 1, 25),
            'duration': 146,
            'poster_url': 'https://image.tmdb.org/t/p/w500/arf00BkwvXo0CFKbaD9OpqdE4Nu.jpg',
            'trailer_url': 'https://www.youtube.com/embed/vqu4z34wENw',
            'status': 'released'
            },
            {
            'title': 'Jawan',
            'description': 'A man driven by justice takes on corruption using unconventional methods.',
            'genre': 'Action, Thriller',
            'director': 'Atlee',
            'cast': 'Shah Rukh Khan, Nayanthara, Vijay Sethupathi',
            'release_date': date(2023, 9, 7),
            'duration': 169,
            'poster_url': 'https://image.tmdb.org/t/p/original/w4mPBAfZS5yIXOcqEiEOL8fnuQG.jpg',
            'trailer_url': 'https://www.youtube.com/embed/COv52Qyctws',
            'status': 'released',
            },
           
            {
            'title': 'The Shawshank Redemption',
            'description': 'Two imprisoned men bond over a number of years, finding solace and eventual redemption.',
            'genre': 'Drama',
            'director': 'Frank Darabont',
            'cast': 'Tim Robbins, Morgan Freeman',
            'release_date': date(1994, 9, 23),
            'duration': 142,
            'poster_url': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSf1DK32xKMQzqSl8wnY1BLVu_gdwsRYzVSNM6A03r6c-fEwrif8raKzkFRuerw1KHdDICvOw&s=10',
            'trailer_url': 'https://www.youtube.com/embed/6hB3S9bIaco',
            'status': 'released'
            },
            {
            'title': 'Rocketry: The Nambi Effect',
            'description': 'Based on the life of ISRO scientist Nambi Narayanan.',
            'genre': 'Biography, Drama',
            'director': 'R. Madhavan',
            'cast': 'R. Madhavan',
            'release_date': date(2022, 7, 1),
            'duration': 157,
            'poster_url': 'https://resizing.flixster.com/uFl3KWEoQIaP7EpRoUAFVN6g4uA=/ems.cHJkLWVtcy1hc3NldHMvbW92aWVzL2Q1NjdmZTUyLTgyYjgtNGQyNy04OWNjLTI2ODQyZDNkOTY1My5qcGc=',
            'trailer_url': 'https://www.youtube.com/embed/wwGzG6g6J6k',
            'status': 'released'
            },
        
            {
            'title': 'Avatar: Fire and Ash',
            'description': 'A new threat emerges on Pandora.',
            'genre': 'Sci-Fi, Action',
            'director': 'James Cameron',
            'cast': 'Sam Worthington, Zoe Saldana',
            'release_date': date(2026, 2, 19),
            'duration': 190,
            'poster_url': 'https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcQJfdu01GP05dCCbubLMIXZgxz4SqKIpQx92wu9zHT7pXovv-Sn',
            'trailer_url': 'https://www.youtube.com/embed/d9MyW72ELq0',
            'status': 'upcoming'
            },
            {
            'title': 'Vikram',
            'description': 'A covert operation uncovers a massive drug syndicate.',
            'genre': 'Action, Thriller',
            'director': 'Lokesh Kanagaraj',
            'cast': 'Kamal Haasan',
            'release_date': date(2022, 6, 3),
            'duration': 175,
            'poster_url': 'https://m.media-amazon.com/images/M/MV5BNDEyMWQ0ZDktNTY0MC00YWRkLWFlMjQtMDUxMjRlMDhmMmRlXkEyXkFqcGc@._V1_.jpg',
            'trailer_url': 'https://www.youtube.com/embed/OKBMCL-frPU',
            'status': 'released'
            },

    ]
        
        print("Adding movies...")
        movies = []
        for movie_data in movies_data:
            movie = Movie(**movie_data)
            db.session.add(movie)
            movies.append(movie)
        
        db.session.commit()
        print(f"Added {len(movies)} movies")
        
        # Sample feedback data
        print("Adding sample feedback...")
        age_groups = ['18-25', '26-35', '36-45', '46+']
        
        feedback_templates = {
            5: [
                'Absolutely phenomenal! Best movie I\'ve seen this year. The cinematography was breathtaking and the performances were outstanding.',
                'Masterpiece! Every frame was perfect. The director\'s vision was executed flawlessly.',
                'Incredible experience from start to finish! I was completely immersed in the story.',
            ],
            4: [
                'Really enjoyed it! Great performances and solid story. A few minor pacing issues but overall excellent.',
                'Very good movie with some memorable moments. Definitely recommend watching it.',
                'Impressive work! The cast delivered strong performances throughout.',
            ],
            3: [
                'Decent movie with its moments. Some parts dragged but overall watchable.',
                'It was okay. Nothing groundbreaking but entertaining enough.',
                'Average film. Has some good scenes but could have been better.',
            ],
            2: [
                'Disappointing. Expected more based on the trailers. The story felt rushed.',
                'Not great. The plot had potential but the execution fell short.',
                'Below expectations. Some good ideas but poorly developed.',
            ],
            1: [
                'Very disappointing. Weak plot and unconvincing performances.',
                'Not recommended. Struggled to stay engaged throughout.',
                'Poor execution. The movie failed to deliver on its premise.',
            ]
        }
        
        # Add feedback for movies with status 'released' or 'now_showing'
        for movie in movies:
            if movie.status in ['released', 'now_showing']:
                num_feedbacks = random.randint(5, 15)
                for _ in range(num_feedbacks):
                    user = random.choice(users[1:])  # Skip admin
                    rating = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 20, 35, 30])[0]
                    feedback = Feedback(
                        movie_id=movie.id,
                        user_id=user.id,
                        customer_name=user.full_name,
                        customer_email=user.email,
                        rating=rating,
                        review=random.choice(feedback_templates[rating]),
                        watch_date=date.today() - timedelta(days=random.randint(0, 30)),
                        age_group=random.choice(age_groups),
                        would_recommend=rating >= 3
                    )
                    feedback.analyze_sentiment()
                    db.session.add(feedback)
        
        db.session.commit()
        print("Database initialization complete!")
        
        # Print summary
        print(f"\nSummary:")
        print(f"Total Users: {User.query.count()}")
        print(f"Total Movies: {Movie.query.count()}")
        print(f"Total Feedbacks: {Feedback.query.count()}")
        print(f"Now Showing: {Movie.query.filter_by(status='now_showing').count()}")
        print(f"Upcoming: {Movie.query.filter_by(status='upcoming').count()}")
        print(f"Released: {Movie.query.filter_by(status='released').count()}")
        print(f"\nDefault Login Credentials:")
        print(f"Admin - Username: admin, Password: admin123")
        print(f"User - Username: john_doe, Password: password123")

if __name__ == '__main__':
    init_database()