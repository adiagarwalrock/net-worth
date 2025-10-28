# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Net-Worth Tracker is a Django-based financial tracking application that enables users to monitor assets, liabilities, and net worth across multiple currencies. Supports household/family management with role-based access control.

**Stack:** Django 5.2.7, PostgreSQL/SQLite3, Celery + Redis, Google Gemini 2.5 (LLM), ExchangeRate-API

## Development Commands

```bash
# Initial setup
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Database operations
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations

# Celery (run in separate terminals)
celery -A config worker --loglevel=info
celery -A config beat --loglevel=info

# Testing
python manage.py test
python manage.py test <app_name>  # Test specific app
coverage run --source='.' manage.py test
coverage report

# Django shell
python manage.py shell
python manage.py dbshell
```

## Architecture

### Django Apps Structure

**Domain-driven design with 7 apps:**

1. **`accounts/`** - Custom user authentication
   - `User` extends `AbstractUser` with `home_currency`, `email_verified`
   - Methods: `get_home_currency()`, `get_total_assets()`, `get_total_liabilities()`, `get_net_worth()`
   - Custom AUTH_USER_MODEL configured in settings

2. **`currencies/`** - Multi-currency support
   - `Currency`: ISO codes (USD, EUR, etc.)
   - `ExchangeRate`: Historical FX rates with unique constraint on (from_currency, to_currency, date)
   - Static methods: `get_latest_rate()`, `get_rate_for_date()`

3. **`assets/`** - Asset tracking
   - `Asset`: 7 types (CASH, INVESTMENT, REAL_ESTATE, VEHICLE, PRECIOUS_METALS, CRYPTOCURRENCY, OTHER)
   - `AssetHistory`: Auto-created on value change via overridden `save()`
   - Method: `get_value_in_currency(target_currency)`
   - Soft delete via `is_active` field

4. **`liabilities/`** - Liability/debt tracking
   - `Liability`: 8 types (CREDIT_CARD, MORTGAGE, AUTO_LOAN, STUDENT_LOAN, MEDICAL_LOAN, PERSONAL_LOAN, LINE_OF_CREDIT, OTHER)
   - `LiabilityHistory`: Auto-created on balance change via overridden `save()`
   - Methods: `get_balance_in_currency()`, `get_credit_utilization()`
   - Soft delete via `is_active` field

5. **`households/`** - Family/household management
   - `Household`: Groups users for combined tracking
   - `HouseholdMember`: Roles (OWNER, MEMBER, VIEWER), enforces ≥1 OWNER via `clean()`
   - `HouseholdInvitation`: Email invites with token + expiration
   - Methods: `is_owner()`, `can_user_manage()`, `get_total_net_worth()`

6. **`networth/`** - Net worth snapshots
   - `NetWorthSnapshot`: Daily snapshots for trend analysis
   - Belongs to user XOR household (enforced via `clean()`)
   - Property: `debt_to_asset_ratio`
   - Class methods: `get_latest_for_user()`, `get_latest_for_household()`

7. **`reports/`** - Analytics (placeholder)

### Key Architectural Patterns

**1. Automatic History Tracking**

- `Asset.save()` and `Liability.save()` auto-create history records on value/balance changes
- Enables time-series analysis without manual snapshots

**2. Service Layer Pattern (Referenced but NOT Implemented)**

```python
# These services are referenced in models but don't exist yet:
# - AssetService.calculate_total_assets()
# - LiabilityService.calculate_total_liabilities()
# - CurrencyService.convert()
# - NetWorthService.calculate_household_net_worth()
#
# Create as <app>/services.py when implementing
```

**3. Celery Periodic Tasks (config/celery.py)**

```python
# Scheduled but tasks don't exist yet:
# - 'currencies.tasks.update_exchange_rates' (daily 9 AM UTC)
# - 'networth.tasks.create_daily_snapshots' (daily midnight UTC)
```

**4. Multi-Currency Architecture**

- All financial models have `currency` ForeignKey
- Conversion methods: `get_value_in_currency()`, `get_balance_in_currency()`
- Historical rate support for accurate backtesting
- Design expects Redis caching for FX rates

**5. Soft Delete Pattern**

- `Asset` and `Liability` use `is_active=True/False` instead of actual deletion
- Preserves historical data integrity

### Database Schema Relationships

```
User
├─→ assets (1:N)
├─→ liabilities (1:N)
├─→ networth_snapshots (1:N)
├─→ created_households (1:N)
├─→ household_memberships (1:N)
└─→ home_currency (N:1 Currency)

Currency
├─→ rates_from (1:N ExchangeRate)
└─→ rates_to (1:N ExchangeRate)

Asset/Liability
├─→ user (N:1)
├─→ currency (N:1)
└─→ history (1:N)

Household
├─→ created_by (N:1 User)
├─→ members (1:N HouseholdMember)
└─→ invitations (1:N HouseholdInvitation)
```

### Environment Configuration

Uses `python-decouple`. Create `.env` (see `.env.example`):

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL (production)
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=networth_db
DATABASE_USER=postgres
DATABASE_PASSWORD=password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# APIs
EXCHANGE_RATE_API_KEY=your-key
GOOGLE_GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-2.5-flash

# App settings
DEFAULT_CURRENCY=USD
FX_UPDATE_TIME=09:00
```

## Implementation Guidelines

### When Creating Models

- Use `DecimalField` for money (never `FloatField`)
- Include `created_at`, `updated_at` timestamps
- Add indexes for FKs and frequently queried fields
- Override `clean()` for validation, `save()` for pre/post-save logic
- Add docstrings with inputs/outputs

### When Creating Service Layers

```python
# Create <app>/services.py, example structure:
class CurrencyService:
    @staticmethod
    def convert(amount, from_currency, to_currency, date=None):
        """Convert amount between currencies using FX rates."""
        # Implementation
```

### When Creating Celery Tasks

```python
# Create <app>/tasks.py
from config.celery import app

@app.task(bind=True)
def update_exchange_rates(self):
    """Fetch latest FX rates from API."""
    # Implementation
```

### Multi-Currency Best Practices

- Always convert to `user.get_home_currency()` for aggregations
- Use historical rates for backdated calculations
- Cache FX rates in Redis (rates update once daily)
- Fallback to USD if home_currency not set

### Role-Based Access (Households)

- **OWNER**: Full access, manage members
- **MEMBER**: View household, manage own assets/liabilities
- **VIEWER**: Read-only household access

Check `household.can_user_manage(user)` before modifications.

## Current State

**Completed:**

- ✅ Django project setup with apps
- ✅ All models defined with relationships
- ✅ Database migrations applied
- ✅ Celery configuration (beat schedule defined)
- ✅ Custom User model configured

**Not Yet Implemented:**

- ❌ Django REST Framework (installed but not configured)
- ❌ URL routing beyond admin panel
- ❌ Service layers (referenced in models)
- ❌ Celery tasks (scheduled but files don't exist)
- ❌ Views, serializers, API endpoints
- ❌ FX rate fetching logic
- ❌ Statement parsing with LLM
- ❌ Tests

## Task Tracking

**Maintain `@docs/TASKS.md`** - Running checklist of tasks for MVP development. Check off items as completed.

## Useful Patterns

### Querying with Currency Conversion

```python
home = user.get_home_currency()
total = sum(
    asset.get_value_in_currency(home)
    for asset in user.assets.filter(is_active=True)
)
```

### Creating Snapshots

```python
from networth.models import NetWorthSnapshot
NetWorthSnapshot.objects.create(
    user=user,
    total_assets=user.get_total_assets(),
    total_liabilities=user.get_total_liabilities(),
    net_worth=user.get_net_worth(),
    currency=user.get_home_currency(),
    snapshot_date=timezone.now().date()
)
```

### Household Permission Check

```python
if not household.can_user_manage(request.user):
    return Response({"error": "Permission denied"}, status=403)
```
