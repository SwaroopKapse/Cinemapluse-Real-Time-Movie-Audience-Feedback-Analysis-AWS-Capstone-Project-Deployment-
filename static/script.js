// Auto-hide flash messages
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 5000);
    });
});

// Smooth scrolling for anchor links (only for page anchors, not navigation)
document.addEventListener('click', function(e) {
    const anchor = e.target.closest('a[href^="#"]');
    if (!anchor) return;
    
    const href = anchor.getAttribute('href');
    const target = document.querySelector(href);
    
    if (target) {
        e.preventDefault();
        target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
});

// Form validation
const feedbackForm = document.querySelector('#feedbackForm');
if (feedbackForm) {
    feedbackForm.addEventListener('submit', function(e) {
        const name = document.querySelector('#customer_name').value.trim();
        const email = document.querySelector('#customer_email').value.trim();
        const rating = document.querySelector('input[name="rating"]:checked');
        const review = document.querySelector('#review').value.trim();
        
        if (!name || !email || !rating || !review) {
            e.preventDefault();
            alert('Please fill in all required fields');
            return false;
        }
        
        // Email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            e.preventDefault();
            alert('Please enter a valid email address');
            return false;
        }
        
        return true;
    });
}

// Rating hover effect
const ratingLabels = document.querySelectorAll('.rating-input label');
ratingLabels.forEach(label => {
    label.addEventListener('mouseenter', function() {
        const value = this.getAttribute('for').split('star')[1];
        updateRatingDisplay(value);
    });
});

const ratingInput = document.querySelector('.rating-input');
if (ratingInput) {
    ratingInput.addEventListener('mouseleave', function() {
        const checked = document.querySelector('input[name="rating"]:checked');
        if (checked) {
            const value = checked.value;
            updateRatingDisplay(value);
        }
    });
}

function updateRatingDisplay(value) {
    const labels = document.querySelectorAll('.rating-input label');
    labels.forEach((label, index) => {
        if (labels.length - index <= value) {
            label.style.color = '#FDCB6E';
        } else {
            label.style.color = '#DFE6E9';
        }
    });
}

// Chart animations
function animateChart() {
    const bars = document.querySelectorAll('.bar-visual');
    bars.forEach((bar, index) => {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.transition = 'width 1s ease';
            bar.style.width = width;
        }, index * 100);
    });
}

// Call animation when page loads
if (document.querySelector('.bar-visual')) {
    window.addEventListener('load', animateChart);
}

// Filter functionality
const filterButtons = document.querySelectorAll('[data-filter]');
filterButtons.forEach(button => {
    button.addEventListener('click', function() {
        const filter = this.getAttribute('data-filter');
        const items = document.querySelectorAll('[data-category]');
        
        items.forEach(item => {
            if (filter === 'all' || item.getAttribute('data-category') === filter) {
                item.style.display = 'block';
                item.style.animation = 'fadeInUp 0.5s ease';
            } else {
                item.style.display = 'none';
            }
        });
        
        // Update active button
        filterButtons.forEach(btn => btn.classList.remove('active'));
        this.classList.add('active');
    });
});

// Search functionality
const searchInput = document.querySelector('#searchInput');
if (searchInput) {
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const items = document.querySelectorAll('.movie-card');
        
        items.forEach(item => {
            const title = item.querySelector('.movie-title').textContent.toLowerCase();
            const genre = item.querySelector('.movie-genre').textContent.toLowerCase();
            
            if (title.includes(searchTerm) || genre.includes(searchTerm)) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    });
}

// Add fade-out animation to CSS dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-20px);
        }
    }
`;
document.head.appendChild(style);

// Movie card click handler
const movieCards = document.querySelectorAll('.movie-card[data-href]');
movieCards.forEach(card => {
    card.addEventListener('click', function(e) {
        // Don't navigate if clicking on a link inside the card
        if (e.target.tagName === 'A') return;
        window.location.href = this.getAttribute('data-href');
    });
});

// Card hover effects
const cards = document.querySelectorAll('.movie-card, .stat-card, .analytics-card');
cards.forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transition = 'all 0.3s ease';
    });
});

// Dynamic date for copyright
const copyrightYear = document.querySelector('#copyrightYear');
if (copyrightYear) {
    copyrightYear.textContent = new Date().getFullYear();
}

// Loading animation
window.addEventListener('load', function() {
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.5s ease';
        document.body.style.opacity = '1';
    }, 100);
});

console.log('CinemaPulse initialized successfully!');