# Films Platform - REST API Usage Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Apply Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 4. Start Development Server
```bash
python manage.py runserver
```

The API will be available at: `http://127.0.0.1:8000/api/`

### API Documentation (Browsable API)
Navigate to any endpoint in your browser to see interactive documentation:
- Example: http://127.0.0.1:8000/api/films/

---

## Authentication

The API supports two authentication methods:

### 1. Session Authentication (Default)
- Automatically used when logged in via web interface
- CSRF protection enabled
- Recommended for web frontend

**Login endpoint** (via web auth):
```
POST /accounts/login/  (Django auth)
```

**Get CSRF token** (for AJAX requests):
```javascript
// Get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');
```

### 2. Basic Authentication
```
Authorization: Basic <base64-encoded-username:password>
```

**Note**: Basic Auth is only enabled for development. Use session auth or token auth in production.

---

## API Endpoints Reference

### 📁 Films (`/api/films/`)

#### List Films
```
GET /api/films/
```
**Query Parameters:**
- `genre=<id>` - Filter by genre ID
- `search=<query>` - Search in title, description, director
- `ordering=-release_date` - Sort (e.g., title, -release_date)
- `page=1` - Pagination
- `page_size=20` - Items per page (max 100)

**Example:**
```
GET /api/films/?genre=1&ordering=-release_date&search=action
```

**Response:**
```json
{
    "count": 45,
    "next": "http://127.0.0.1:8000/api/films/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Inception",
            "genre": {"id": 1, "name": "Sci-Fi"},
            "description": "A thief who steals corporate secrets...",
            "release_date": "2010-07-16",
            "director": "Christopher Nolan",
            "duration_minutes": 148,
            "poster": "http://127.0.0.1:8000/media/posters/inception.jpg",
            "average_rating": 4.5,
            "review_count": 24,
            "is_in_watchlist": false,
            "created_at": "2026-05-08T17:35:00Z",
            "updated_at": "2026-05-08T17:35:00Z"
        }
    ]
}
```

#### Create Film (Admin Only)
```
POST /api/films/
Content-Type: multipart/form-data

{
    "title": "New Film",
    "genre_id": 1,
    "description": "Film description...",
    "release_date": "2024-12-25",
    "director": "John Doe",
    "duration_minutes": 120,
    "poster": <file>,
    "trailer_url": "https://youtube.com/watch?v=..."
}
```

#### Retrieve Film
```
GET /api/films/{id}/
```

#### Update Film (Admin Only)
```
PUT /api/films/{id}/
PATCH /api/films/{id}/
```

#### Delete Film (Admin Only)
```
DELETE /api/films/{id}/
```

#### Toggle Watchlist (Authenticated)
```
POST /api/films/{id}/toggle_watchlist/
```

**Response:**
```json
{"message": "Added to watchlist", "in_watchlist": true}
```

#### Film Statistics
```
GET /api/films/{id}/stats/
```

**Response:**
```json
{
    "average_rating": 4.2,
    "review_count": 15,
    "rating_distribution": {"5": 8, "4": 4, "3": 2, "2": 1, "1": 0}
}
```

#### Featured Films
```
GET /api/films/featured/
```

#### Recent Films
```
GET /api/films/recent/
```

---

### 📁 Genres (`/api/genres/`)

#### List Genres
```
GET /api/genres/
```

#### Create Genre (Admin Only)
```
POST /api/genres/
{
    "name": "Horror",
    "description": "Films intended to scare..."
}
```

---

### 📁 Reviews (`/api/reviews/`)

#### List Reviews
```
GET /api/reviews/?film=1&ordering=-created_at
```

#### Create Review (Authenticated)
```
POST /api/reviews/
{
    "film_id": 1,
    "rating": 5,
    "comment": "Excellent film!"
}
```

**Validation:** One review per user per film.

#### Update Review
Users can update their own reviews:
```
PUT /api/reviews/{id}/
```

#### Delete Review
Users can delete their own reviews:
```
DELETE /api/reviews/{id}/
```

---

### 📁 Watchlist (`/api/watchlist/`)

#### List Watchlist (Authenticated)
```
GET /api/watchlist/my_watchlist/
```

#### Add to Watchlist
```
POST /api/watchlist/
{
    "film_id": 1
}
```

#### Remove from Watchlist
```
DELETE /api/watchlist/{id}/
```

---

### 📁 Users (`/api/users/`)

#### Register User
```
POST /api/users/
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password123",
    "role": "SPECTATOR"
}
```

#### Get User Profile
```
GET /api/users/{username}/
```

#### Update Profile (Own or Admin)
```
PATCH /api/users/{username}/
{
    "bio": "Updated bio",
    "favorite_genres": [1, 2, 3]
}
```

#### User's Reviews
```
GET /api/users/{username}/reviews/
```

#### User's Watchlist
```
GET /api/users/{username}/watchlist/  (Own or admin only)
```

#### User Statistics
```
GET /api/users/{username}/stats/
```

---

### 📁 Statistics (`/api/stats/`)

#### Top Rated Films (min 5 reviews)
```
GET /api/stats/top_rated/
```

#### Most Reviewed Films
```
GET /api/stats/most_reviewed/
```

#### Genre Statistics
```
GET /api/stats/genre_stats/
```

---

## Error Handling

### Standard HTTP Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `204 No Content` - Resource deleted
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Error Response Format
```json
{
    "detail": "Authentication credentials were not provided.",
    "code": "not_authenticated"
}
```

---

## Rate Limiting

Default limits (configurable in settings.py):
- Anonymous users: 100 requests/day
- Authenticated users: 1000 requests/day

**Headers returned:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1620000000
```

---

## Filtering Examples

### Search Films by Multiple Fields
```
GET /api/films/?search=quantum
# Searches title, description, director
```

### Filter Reviews by Film and Rating
```
GET /api/reviews/?film=1&rating=5
```

### Filter Users by Role (Admin only)
```
GET /api/users/?role=ADMIN
```

---

## Testing with cURL

### Get CSRF Token and Login
```bash
# Get CSRF token
curl -c cookies.txt http://127.0.0.1:8000/

# Login
curl -b cookies.txt -c cookies.txt -X POST http://127.0.0.1:8000/accounts/login/ \
  -d "username=admin&password=admin123" \
  -H "X-CSRFToken: <token>"
```

### List Films (Authenticated)
```bash
curl -b cookies.txt http://127.0.0.1:8000/api/films/
```

### Create Film (Admin)
```bash
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/films/ \
  -F "title=Test Film" \
  -F "genre_id=1" \
  -F "description=Test description" \
  -F "release_date=2024-01-01" \
  -F "director=Test Director"
```

### Create Review (Authenticated)
```bash
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/reviews/ \
  -H "Content-Type: application/json" \
  -d '{"film_id": 1, "rating": 5, "comment": "Great!"}'
```

---

## Testing with Python Requests

```python
import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://127.0.0.1:8000/api"

# Authentication
response = requests.post(
    f"{BASE_URL}/users/",
    json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }
)

# List films
response = requests.get(f"{BASE_URL}/films/")
films = response.json()['results']

# Create review
response = requests.post(
    f"{BASE_URL}/reviews/",
    json={"film_id": 1, "rating": 4, "comment": "Good movie"},
    cookies=session_cookies  # or use auth
)
```

---

## Production Considerations

### 1. Enable HTTPS
Update `settings.py`:
```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### 2. Use Stronger Authentication
Consider:
- JWT tokens (djangorestframework-simplejwt)
- OAuth2 (django-oauth-toolkit)
- API keys for service accounts

### 3. Increase Caching
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'user': '10000/day',  # Increase for production
    },
    'DEFAULT_CACHE_RESPONSE_TIMEOUT': 60 * 15,  # 15 minutes cache
}
```

### 4. Add CORS Headers (for SPA frontend)
```bash
pip install django-cors-headers
```
In settings.py:
```python
INSTALLED_APPS += ['corsheaders']
MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware'] + MIDDLEWARE
CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
```

### 5. Use PostgreSQL in Production
Update `settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'films_platform',
        'USER': 'films_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 6. Enable Gzip Compression
```bash
pip install django-compressor
```

### 7. Set Up Monitoring
- Log all API requests
- Monitor response times with Django Debug Toolbar (dev) or custom middleware
- Set up alerts for 5xx errors

---

## API Testing Checklist

- [ ] Film listing with filters
- [ ] Film creation (admin only, reject non-admin)
- [ ] Film update (admin only)
- [ ] Film deletion (admin only)
- [ ] Genre CRUD (admin only)
- [ ] Review creation (one per user per film)
- [ ] Review update (own only)
- [ ] Review deletion (own or admin)
- [ ] Watchlist toggle
- [ ] User registration with validation
- [ ] Rate limiting enforced
- [ ] Pagination working
- [ ] Search functionality
- [ ] Ordering works
- [ ] CSRF protection active
- [ ] SQL injection protection (parameterized queries used)

---

## Additional Resources

- Django REST Framework: https://www.django-rest-framework.org/
- API Browsable Interface: Built-in to DRF
- Schema generation: Available at `/api/schema/` if using DRF schema generation
- ReDoc documentation: Available at `/api/docs/` if configured

---

## Support

For issues or feature requests, open an issue on GitHub or contact the development team.
