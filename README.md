# Hakalo Verify Backend

Django REST Framework backend with JWT authentication, CORS support, and environment-based configuration.

## Setup

### 1. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in values:

```bash
cp .env.example .env
```

Edit `.env`:
```
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3  # or postgres://user:password@localhost:5432/dbname
CORS_ALLOW_ALL_ORIGINS=True
```

For production:
- Set DEBUG=False
- Use a strong SECRET_KEY
- Set CORS_ALLOWED_ORIGINS to specific domains (not CORS_ALLOW_ALL_ORIGINS=True)
- Use a real database (PostgreSQL recommended)

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to set username and password.

### 5. Start Development Server

```bash
python manage.py runserver
```

The server runs at `http://127.0.0.1:8000`

---

## JWT Authentication

This project uses Simple JWT for token-based authentication.

### Obtain Tokens

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-username",
    "password": "your-password"
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Use Access Token

Include the `access` token in the `Authorization` header:

```bash
curl -X GET http://127.0.0.1:8000/api/your-endpoint/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### Refresh Access Token

When the access token expires, use the `refresh` token to get a new one:

```bash
curl -X POST http://127.0.0.1:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## Project Structure

```
project/
  settings.py       # Django settings (DRF, CORS, SimpleJWT, dj-database-url, python-dotenv)
  urls.py           # URL routing with JWT endpoints
  wsgi.py           # WSGI application

requirements.txt    # Project dependencies
.env.example        # Environment variables template
.env                # Local environment (git-ignored)
```

---

## Configuration Details

### Django REST Framework
- **Default Authentication:** JWT (via SimpleJWT)
- **Default Permission:** IsAuthenticated (protected endpoints require valid token)
- See `project/settings.py` for customization

### Simple JWT
- **Access Token Lifetime:** 5 minutes
- **Refresh Token Lifetime:** 1 day
- Customize in `project/settings.py` under `SIMPLE_JWT`

### CORS
- **Development:** All origins allowed (CORS_ALLOW_ALL_ORIGINS=True in .env)
- **Production:** Restrict to specific domains in `project/settings.py` (CORS_ALLOWED_ORIGINS)

---

## Adding API Routes

Edit `project/urls.py` and uncomment or add your app's URL routes:

```python
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # JWT endpoints
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # Your API routes:
    path("api/", include("your_app.api_urls")),  # uncomment and set your app
]
```

---

## Common Commands

```bash
# Run development server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Access Django admin
# http://127.0.0.1:8000/admin/
```

---

## Next Steps

- Add your Django apps to `INSTALLED_APPS` in `project/settings.py`
- Create API serializers and viewsets for your models
- Protect endpoints with `@permission_classes` or `IsAuthenticated` permission
- Test authentication with the provided curl examples or use Postman/Insomnia

---

## Troubleshooting

**Problem:** `ModuleNotFoundError: No module named 'djangorestframework'`
- **Solution:** Run `pip install -r requirements.txt`

**Problem:** `Invalid token` or `Token is blacklisted`
- **Solution:** Ensure you're using the latest access token. Tokens expire after 5 minutes.

**Problem:** CORS errors in browser
- **Solution:** Check that `CORS_ALLOW_ALL_ORIGINS=True` in `.env` (development) or `CORS_ALLOWED_ORIGINS` is set correctly (production)

**Problem:** Database connection error
- **Solution:** Check `DATABASE_URL` in `.env`. For SQLite, ensure the path is writable.

---

## References

- [Django REST Framework Docs](https://www.django-rest-framework.org/)
- [Simple JWT Docs](https://django-rest-framework-simplejwt.readthedocs.io/)
- [django-cors-headers Docs](https://github.com/adamchainz/django-cors-headers)
- [dj-database-url Docs](https://github.com/jacobian/dj-database-url)
- [python-dotenv Docs](https://github.com/theskumar/python-dotenv)
