# Hakalo Verify Backend - Microfinance Loan Borrower Verification Platform

A comprehensive Django REST Framework API for managing institution verification, customer onboarding, and loan eligibility verification with complete audit trail and compliance logging.

## 🚀 Features

- **Institution Management** - Register and manage financial institutions
- **Customer Management** - Onboard borrowers with complete KYC data
- **Verification Workflow** - Multi-stage verification process with approvals
- **Audit Logging** - Immutable compliance-grade audit trail
- **JWT Authentication** - Secure API endpoints with token-based auth
- **Role-Based Access Control** - Admin and user permission levels
- **Advanced Filtering & Search** - Filter by status, institution, date range
- **RESTful API** - Full CRUD operations with custom actions

## 📋 Tech Stack

- **Backend**: Django 4.x + Django REST Framework
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Utilities**: CORS, Environment variables, Database URL support

## 🛠️ Installation & Setup

### 1. Clone Repository
```bash
git clone https://github.com/KALOKOH026/hakalo-verify-backend.git
cd hakalo-verify-backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. Run Migrations
```bash
python manage.py makemigrations api
python manage.py migrate
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
# Follow prompts to create admin account
```

### 7. Start Development Server
```bash
python manage.py runserver
```

Access the API at `http://localhost:8000/`

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Authentication
All endpoints (except token endpoints) require JWT Bearer token:
```bash
Authorization: Bearer <your_access_token>
```

### Get JWT Token
```bash
POST /api/token/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Refresh Token
```bash
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "your_refresh_token"
}
```

## 🏛️ Endpoints

### Institutions
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/institutions/` | List all institutions |
| `POST` | `/institutions/` | Create institution (Admin only) |
| `GET` | `/institutions/{id}/` | Get institution details |
| `PUT` | `/institutions/{id}/` | Update institution (Admin only) |
| `DELETE` | `/institutions/{id}/` | Delete institution (Admin only) |

**Query Parameters:**
- `?search=name` - Search by name, code, or email
- `?is_active=true` - Filter by active status
- `?country=Kenya` - Filter by country
- `?ordering=-created_at` - Sort by field

### Customers
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/customers/` | List all customers |
| `POST` | `/customers/` | Create customer (Admin only) |
| `GET` | `/customers/{id}/` | Get customer details |
| `PUT` | `/customers/{id}/` | Update customer (Admin only) |
| `DELETE` | `/customers/{id}/` | Delete customer (Admin only) |
| `GET` | `/customers/unverified/` | Get unverified customers |
| `POST` | `/customers/{id}/mark_verified/` | Mark customer as verified |

**Query Parameters:**
- `?search=name` - Search by name, email, or national ID
- `?is_verified=false` - Filter by verification status
- `?institution=1` - Filter by institution ID
- `?gender=M` - Filter by gender

**Example - Create Customer:**
```bash
POST /api/customers/
Authorization: Bearer <token>
Content-Type: application/json

{
  "institution": 1,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "+254700000000",
  "national_id": "12345678",
  "date_of_birth": "1990-01-15",
  "gender": "M",
  "address": "123 Main St",
  "city": "Nairobi",
  "country": "Kenya"
}
```

### Verification Requests
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/verifications/` | List all verification requests |
| `POST` | `/verifications/` | Create verification request (Admin only) |
| `GET` | `/verifications/{id}/` | Get verification details |
| `GET` | `/verifications/pending/` | Get pending verifications |
| `POST` | `/verifications/{id}/approve/` | Approve verification |
| `POST` | `/verifications/{id}/reject/` | Reject verification |
| `GET` | `/verifications/expired/` | Get expired verifications |

**Example - Approve Verification:**
```bash
POST /api/verifications/1/approve/
Authorization: Bearer <token>
Content-Type: application/json

{}
```

**Example - Reject Verification:**
```bash
POST /api/verifications/1/reject/
Authorization: Bearer <token>
Content-Type: application/json

{
  "reason": "Missing supporting documents"
}
```

### Audit Logs
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/audit-logs/` | List all audit logs (Admin only) |
| `GET` | `/audit-logs/{id}/` | Get audit log details (Admin only) |
| `GET` | `/audit-logs/recent/` | Get logs from last 24 hours (Admin only) |
| `GET` | `/audit-logs/by_user/?username=john` | Get logs by user (Admin only) |

**Query Parameters:**
- `?action=VERIFY` - Filter by action type
- `?model_name=Customer` - Filter by model
- `?user=1` - Filter by user ID
- `?search=description` - Search in description

## 📊 Data Models

### Institution
```python
{
  "id": 1,
  "name": "ABC Microfinance",
  "code": "ABC001",
  "country": "Kenya",
  "website": "https://abcmf.example.com",
  "email": "info@abcmf.example.com",
  "phone": "+254700000000",
  "is_active": true,
  "created_at": "2026-07-03T10:00:00Z",
  "updated_at": "2026-07-03T10:00:00Z"
}
```

### Customer
```python
{
  "id": 1,
  "institution": 1,
  "institution_name": "ABC Microfinance",
  "full_name": "John Doe",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "+254700000000",
  "national_id": "12345678",
  "date_of_birth": "1990-01-15",
  "gender": "M",
  "address": "123 Main St",
  "city": "Nairobi",
  "country": "Kenya",
  "is_verified": false,
  "created_at": "2026-07-03T10:00:00Z",
  "updated_at": "2026-07-03T10:00:00Z"
}
```

### VerificationRequest
```python
{
  "id": 1,
  "customer": 1,
  "customer_name": "John Doe",
  "verification_code": "VER-2026-000001",
  "status": "PENDING",
  "verification_method": "EMAIL",
  "verification_data": null,
  "verified_by": null,
  "verified_by_username": null,
  "verified_at": null,
  "rejection_reason": null,
  "expires_at": "2026-07-10T10:00:00Z",
  "created_at": "2026-07-03T10:00:00Z",
  "updated_at": "2026-07-03T10:00:00Z"
}
```

### AuditLog
```python
{
  "id": 1,
  "user": 1,
  "username": "admin",
  "action": "CREATE",
  "action_display": "Create",
  "model_name": "Customer",
  "object_id": "1",
  "object_repr": "John Doe (12345678)",
  "old_values": null,
  "new_values": {"email": "john@example.com"},
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "description": "Created new customer",
  "created_at": "2026-07-03T10:00:00Z"
}
```

## 🔐 Permission Levels

- **Unauthenticated**: Can only access `/health/` and `/api/token/`
- **Authenticated User**: Can read institutions, customers, verifications
- **Admin User**: Full CRUD access + audit log access

## 🧪 Example Workflows

### Workflow 1: Complete Verification Flow
```bash
# 1. Get token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# 2. Create institution
curl -X POST http://localhost:8000/api/institutions/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Bank","code":"MB001","country":"Kenya"}'

# 3. Create customer
curl -X POST http://localhost:8000/api/customers/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{...customer data...}'

# 4. Create verification request
curl -X POST http://localhost:8000/api/verifications/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"customer":1,"verification_code":"VER001"}'

# 5. Approve verification
curl -X POST http://localhost:8000/api/verifications/1/approve/ \
  -H "Authorization: Bearer <TOKEN>"
```

## 📝 Pagination & Filtering

All list endpoints support:
- **Pagination**: `?page=1&page_size=20`
- **Search**: `?search=keyword`
- **Ordering**: `?ordering=-created_at` (prefix with - for descending)
- **Filtering**: Model-specific filters (see endpoints above)

## 🐛 Error Handling

All errors follow this format:
```json
{
  "detail": "Error message",
  "error_code": "ERROR_TYPE"
}
```

Common status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Server Error

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in .env
- [ ] Generate secure `SECRET_KEY`
- [ ] Configure database (PostgreSQL recommended)
- [ ] Set up proper `ALLOWED_HOSTS`
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS appropriately
- [ ] Set up environment variables
- [ ] Run `python manage.py collectstatic`
- [ ] Use production WSGI server (Gunicorn/uWSGI)
- [ ] Set up monitoring & logging

### Docker Deployment
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "project.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 📖 Admin Interface

Access Django admin at: `http://localhost:8000/admin/`

Features:
- Institution management with search & filtering
- Customer management with full-text search
- Verification request workflow
- Read-only immutable audit logs

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

Eclipse Public License 2.0 - see LICENSE file

## 📧 Support

For issues, questions, or suggestions:
- Email: support@hakalo.example.com
- Issues: https://github.com/KALOKOH026/hakalo-verify-backend/issues

## 👤 Author

**HASSAN KALOKOH**
- GitHub: [@KALOKOH026](https://github.com/KALOKOH026)

---

**Last Updated**: July 2026
**Version**: 1.0.0
