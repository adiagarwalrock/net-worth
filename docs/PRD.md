# Product Requirements Document: Net-Worth Tracking Application

**Document Version:** 1.0
**Date:** October 27, 2025
**Product Name:** Net-Worth Tracker (working title)

---

## 1. Executive Summary

A comprehensive web-based net-worth tracking application that enables individuals and families to monitor their financial health by tracking assets, liabilities, and net worth across multiple currencies. The application supports both manual data entry and automated statement parsing using LLM technology.

---

## 2. Product Vision & Goals

### Vision

Empower individuals and families to gain complete visibility into their financial position, make informed decisions, and track their wealth journey over time.

### Primary Goals

- Provide a single source of truth for personal/family net worth
- Support diverse asset and liability types with extensible architecture
- Enable effortless data entry through intelligent automation
- Deliver actionable insights through comprehensive reporting
- Support multi-currency portfolios with automatic conversion

---

## 3. Target Users

### Primary Persona: Individual User

- Age: 25-60
- Tech-savvy to moderately technical
- Manages multiple accounts, investments, and debt instruments
- Wants to track financial progress over time
- May have assets/liabilities in multiple currencies

### Secondary Persona: Household/Family Manager

- Manages finances for entire household
- Needs to track combined family net worth
- Requires ability to add family members and their assets/liabilities
- Wants individual and consolidated views
- May coordinate with spouse/partner on financial planning

---

## 4. Core Features & Requirements

### 4.1 User Management & Authentication

#### 4.1.1 User Accounts

- Email/password registration and login
- Password reset functionality
- Email verification
- User profile management

#### 4.1.2 Household/Family Management

- Create household/family groups
- Invite family members via email
- Role-based access:
  - **Owner**: Full access, can add/remove members
  - **Member**: Can view family net worth, manage own assets/liabilities
  - **Viewer**: Read-only access to family net worth
- Individual and consolidated family views
- Privacy controls (what family members can see)

### 4.2 Asset & Liability Management

#### 4.2.1 Supported Asset Classes (Phase 1)

1. **Cash & Bank Accounts**
   - Checking accounts
   - Savings accounts
   - Money market accounts
   - Fields: Account name, institution, balance, currency, last updated

2. **Investment Portfolios**
   - Stocks, bonds, mutual funds, ETFs
   - Retirement accounts (401k, IRA, etc.)
   - Brokerage accounts
   - Fields: Account name, institution, total value, currency, holdings (optional), last updated

3. **Real Estate**
   - Primary residence
   - Investment properties
   - Land
   - Fields: Property name/address, estimated value, currency, valuation date

4. **Other Assets**
   - Vehicles
   - Precious metals
   - Cryptocurrency (future consideration)
   - Collectibles
   - Personal property
   - Fields: Asset name, estimated value, currency, last updated

#### 4.2.2 Supported Liability Classes (Phase 1)

1. **Credit Cards**
   - Fields: Card name, institution, outstanding balance, credit limit, currency, APR, payment due date

2. **Loans**
   - **Mortgage/Home Loan**: Principal balance, interest rate, term, monthly payment
   - **Auto/Vehicle Loan**: Principal balance, interest rate, term, monthly payment
   - **Education/Student Loan**: Principal balance, interest rate, term, monthly payment
   - **Medical Loan**: Principal balance, interest rate, term, monthly payment
   - **Personal Loan**: Principal balance, interest rate, term, monthly payment
   - Fields: Loan name, lender, principal balance, interest rate, term remaining, monthly payment, currency

3. **Other Liabilities**
   - Lines of credit
   - Business loans
   - Other debt
   - Fields: Liability name, creditor, balance, currency, interest rate (optional)

#### 4.2.3 Extensibility Requirements

- Database schema must support easy addition of new asset/liability types
- Use polymorphic models or abstract base classes
- Support custom fields for future asset/liability classes
- Plugin architecture consideration for Phase 2

### 4.3 Data Entry Methods

#### 4.3.1 Manual Entry (Phase 1 - Priority 1)

- User-friendly forms for each asset/liability type
- Currency selector for each entry
- Bulk update capability
- Quick-add templates for common accounts
- Edit/update existing entries
- Delete entries with confirmation
- Historical value tracking (maintain history of updates)

#### 4.3.2 Automated Statement Parsing via LLM (Phase 1 - Priority 2)

- **Upload Interface**:
  - Support PDF, CSV, Excel, images (JPG, PNG)
  - Drag-and-drop upload
  - Multi-file upload support

- **LLM Processing**:
  - Use structured outputs (JSON schema) for parsing
  - Extract key data points:
    - Account name/number
    - Institution name
    - Balance/value
    - Date
    - Transaction details (optional for Phase 1)
  - Confidence scoring for extracted data

- **Review & Confirmation**:
  - Show parsed data in editable form
  - Highlight low-confidence extractions
  - Allow user to correct before saving
  - Map to existing accounts or create new

- **Supported Statement Types**:
  - Bank statements
  - Credit card statements
  - Investment account statements
  - Loan statements
  - Property valuations

#### 4.3.3 Financial API Integration (Phase 2 - Future)

- Plaid/Yodlee integration for automatic sync
- Real-time balance updates
- Transaction history import
- OAuth-based secure connection
- *Note: Documented for future reference, not in initial scope*

### 4.4 Multi-Currency Support

#### 4.4.1 Currency Management

- Support for 150+ major world currencies
- User can set primary/home currency
- Each asset/liability can be in any supported currency
- Display amounts in both original and home currency

#### 4.4.2 Currency Conversion

- Use free FX API (e.g., ExchangeRate-API, Fixer.io free tier, or CurrencyAPI)
- Update rates once daily during market hours (e.g., 9 AM UTC)
- Store historical FX rates for accurate historical calculations
- Display last updated timestamp for FX rates
- Manual refresh option for users
- Fallback mechanism if API fails

#### 4.4.3 Conversion Features

- Auto-convert all values to home currency for net worth calculation
- Show original currency alongside converted amount
- Historical net worth calculations use rates from respective dates

### 4.5 Net Worth Calculation

#### 4.5.1 Core Calculations

- **Individual Net Worth** = Total Assets - Total Liabilities
- **Family Net Worth** = Sum of all family members' net worth
- All calculations in user's home currency
- Real-time calculation on data update
- Historical net worth tracking (daily/weekly/monthly snapshots)

#### 4.5.2 Data Aggregation

- Aggregate by asset/liability class
- Aggregate by currency
- Aggregate by family member
- Percentage breakdown by category

### 4.6 Reporting & Analytics

#### 4.6.1 Dashboard (Phase 1)

- **Key Metrics**:
  - Current net worth (large, prominent display)
  - Total assets
  - Total liabilities
  - Debt-to-asset ratio
  - Month-over-month change
  - Year-over-year change

- **Visualizations**:
  - Net worth trend chart (line graph, 6M/1Y/5Y/All)
  - Asset allocation pie chart
  - Liability breakdown pie chart
  - Family member contribution (for household view)

- **Quick Stats**:
  - Largest asset
  - Largest liability
  - Number of accounts tracked
  - Last updated timestamp

#### 4.6.2 Detailed Reports

1. **Net Worth Statement**
   - Full balance sheet view
   - Assets on left, liabilities on right
   - Grouped by category
   - Totals and subtotals
   - Export to PDF/Excel

2. **Trend Analysis**
   - Net worth over time (customizable date range)
   - Asset growth trends
   - Liability reduction trends
   - Individual asset/liability history
   - Export charts as images

3. **Asset Allocation Report**
   - Breakdown by asset class (%)
   - Breakdown by currency (%)
   - Comparison to target allocation (Phase 2)
   - Diversification score (Phase 2)

4. **Debt Analysis Report**
   - Total debt by category
   - Average interest rates
   - Debt payoff timeline projections
   - Monthly payment obligations
   - Interest paid vs. principal

5. **Family Comparison Report** (Household view)
   - Side-by-side member comparison
   - Individual contributions to family net worth
   - Asset/liability distribution across family

#### 4.6.3 Export Capabilities

- Export formats: PDF, CSV, Excel (XLSX)
- Email reports (scheduled or on-demand)
- Print-friendly formatting
- Custom date ranges for exports

#### 4.6.4 Alerts & Notifications (Phase 1.5/Phase 2)

- Credit card payment reminders
- Net worth milestones achieved
- Significant portfolio value changes
- FX rate significant changes
- Data staleness warnings (accounts not updated in 30+ days)

---

## 5. Technical Architecture

### 5.1 Technology Stack

#### Backend

- **Framework**: Django 5.x (Python 3.11+)
- **Database**: PostgreSQL 15+ (for JSONB support and scalability)
- **API**: Django REST Framework (DRF) for RESTful APIs
- **Task Queue**: Celery with Redis (for async tasks like LLM parsing, FX updates)
- **Caching**: Redis (for FX rates, computed metrics)

#### LLM Integration

- **Primary**: Google Gemini 2.5 (gemini-2.5-flash or gemini-2.5-pro with structured outputs)
- **Model Options**:
  - `gemini-2.5-pro`: Advanced reasoning, best for complex document parsing
  - `gemini-2.5-flash`: Fast, cost-effective, great for high-volume processing (recommended)
  - `gemini-2.5-flash-lite`: Fastest and cheapest for simple statements
- **Advantages**: Thinking capabilities, 1M token context window, native multimodal support
- OCR: Built-in image/PDF understanding with Gemini (no separate OCR needed)

#### Currency APIs

- **Primary**: ExchangeRate-API Free Open Access (no API key required)
  - Endpoint: `https://open.exchangerate-api.com/v6/latest/{currency}`
  - Rate Limit: Once per hour (we update daily at 9 AM UTC)
  - Attribution required
  - ISO 4217 currency codes
- **Fallback**: Fixer.io or CurrencyAPI (if primary fails)
- Cache rates in database, API only for daily updates

#### Frontend (Phase 1 - Basic)

- Django templates with Bootstrap 5
- Chart.js for visualizations
- Vanilla JavaScript for interactivity

#### Frontend (Phase 2 - Enhanced)

- React/Next.js SPA
- Recharts or D3.js for advanced visualizations
- TailwindCSS for styling

### 5.2 Core Data Models

```python
# Simplified conceptual models (to be refined during development)

User (extends Django User)
├── email, password (Django default)
├── home_currency (ForeignKey to Currency)
├── created_at, updated_at
└── households (ManyToMany through HouseholdMember)

Household
├── name
├── created_by (ForeignKey to User)
├── created_at, updated_at
└── members (ManyToMany through HouseholdMember)

HouseholdMember
├── household (ForeignKey)
├── user (ForeignKey)
├── role (OWNER, MEMBER, VIEWER)
├── can_view_details (Boolean)
└── joined_at

Currency
├── code (USD, EUR, INR, etc.)
├── name
├── symbol
└── is_active

ExchangeRate
├── from_currency (ForeignKey to Currency)
├── to_currency (ForeignKey to Currency)
├── rate (Decimal)
├── date
└── source (API name)

Asset (Abstract Base)
├── user (ForeignKey to User)
├── name
├── asset_type (CASH, INVESTMENT, REAL_ESTATE, OTHER)
├── value (Decimal)
├── currency (ForeignKey to Currency)
├── institution (optional)
├── notes (TextField)
├── created_at, updated_at, last_valued_at
└── is_active (for soft delete)

AssetHistory
├── asset (ForeignKey)
├── value (Decimal)
├── currency (ForeignKey)
├── recorded_at
└── source (MANUAL, STATEMENT_UPLOAD, API)

Liability (Abstract Base)
├── user (ForeignKey to User)
├── name
├── liability_type (CREDIT_CARD, MORTGAGE, AUTO_LOAN, STUDENT_LOAN, MEDICAL_LOAN, PERSONAL_LOAN, OTHER)
├── balance (Decimal)
├── currency (ForeignKey to Currency)
├── creditor/institution
├── interest_rate (optional)
├── monthly_payment (optional)
├── notes (TextField)
├── created_at, updated_at, last_valued_at
└── is_active (for soft delete)

LiabilityHistory
├── liability (ForeignKey)
├── balance (Decimal)
├── currency (ForeignKey)
├── recorded_at
└── source (MANUAL, STATEMENT_UPLOAD, API)

StatementUpload
├── user (ForeignKey)
├── file (FileField)
├── upload_type (BANK, CREDIT_CARD, INVESTMENT, LOAN, OTHER)
├── status (PENDING, PROCESSING, COMPLETED, FAILED)
├── parsed_data (JSONField - structured output from LLM)
├── confidence_score (Decimal)
├── uploaded_at, processed_at
└── error_message (if failed)

NetWorthSnapshot
├── user (ForeignKey)
├── household (ForeignKey, nullable)
├── total_assets (Decimal)
├── total_liabilities (Decimal)
├── net_worth (Decimal)
├── currency (ForeignKey - home currency)
├── snapshot_date
└── created_at
```

### 5.3 Key Business Logic Components

#### 5.3.1 Net Worth Calculator Service

- Calculate individual net worth in home currency
- Calculate household net worth
- Generate historical snapshots
- Currency conversion using latest/historical rates

#### 5.3.2 Currency Converter Service

- Fetch and cache FX rates daily
- Convert amounts between currencies
- Historical rate lookup
- Fallback mechanisms

#### 5.3.3 Statement Parser Service

- Accept uploaded files
- Extract text/data (OCR for images)
- Call LLM API with structured output schema
- Parse JSON response
- Map to Asset/Liability models
- Return parsed data for user review

#### 5.3.4 Analytics Engine

- Generate dashboard metrics
- Compute trends and aggregations
- Create report data structures
- Cache frequently accessed calculations

### 5.4 API Endpoints (RESTful)

```
Authentication:
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/password-reset

Users & Households:
GET    /api/users/me
PATCH  /api/users/me
GET    /api/households
POST   /api/households
GET    /api/households/{id}
PATCH  /api/households/{id}
DELETE /api/households/{id}
POST   /api/households/{id}/members
DELETE /api/households/{id}/members/{user_id}

Assets:
GET    /api/assets
POST   /api/assets
GET    /api/assets/{id}
PATCH  /api/assets/{id}
DELETE /api/assets/{id}
GET    /api/assets/{id}/history

Liabilities:
GET    /api/liabilities
POST   /api/liabilities
GET    /api/liabilities/{id}
PATCH  /api/liabilities/{id}
DELETE /api/liabilities/{id}
GET    /api/liabilities/{id}/history

Net Worth:
GET    /api/net-worth/current
GET    /api/net-worth/history?start_date=X&end_date=Y
GET    /api/net-worth/household/{id}

Currency:
GET    /api/currencies
GET    /api/exchange-rates?from=USD&to=EUR&date=YYYY-MM-DD

Statements:
POST   /api/statements/upload
GET    /api/statements
GET    /api/statements/{id}
POST   /api/statements/{id}/confirm
PATCH  /api/statements/{id}/edit

Reports:
GET    /api/reports/dashboard
GET    /api/reports/net-worth-statement?format=pdf
GET    /api/reports/trend-analysis?start=X&end=Y
GET    /api/reports/asset-allocation
GET    /api/reports/debt-analysis
GET    /api/reports/family-comparison?household_id=X
```

### 5.5 Security & Privacy

#### Authentication & Authorization

- JWT-based authentication
- Role-based access control (RBAC) for households
- Session management with timeout
- Password hashing (Django's PBKDF2)

#### Data Security

- HTTPS only (enforce SSL)
- Database encryption at rest
- Sensitive field encryption (account numbers)
- API rate limiting
- CSRF protection
- SQL injection prevention (Django ORM)

#### Privacy

- Users only see their own data + household data they're part of
- Granular privacy controls within households
- Data export capability (GDPR compliance)
- Account deletion (soft delete with recovery period)
- Audit logs for sensitive operations

---

## 6. Development Phases

### Phase 1: Core MVP (8-12 weeks)

#### Phase 1.1: Foundation (Weeks 1-3)

- [ ] Django project setup
- [ ] Database models (User, Household, Asset, Liability, Currency)
- [ ] User authentication (registration, login, password reset)
- [ ] Basic admin panel customization
- [ ] PostgreSQL setup and migrations
- [ ] Redis setup for caching

#### Phase 1.2: Asset & Liability Management (Weeks 4-6)

- [ ] CRUD APIs for assets
- [ ] CRUD APIs for liabilities
- [ ] Manual data entry forms (Django templates)
- [ ] Asset/liability history tracking
- [ ] Soft delete functionality
- [ ] Basic validation and error handling

#### Phase 1.3: Multi-Currency & Net Worth (Weeks 7-8)

- [ ] Currency model and data seeding
- [ ] FX API integration (ExchangeRate-API)
- [ ] Celery task for daily FX rate updates
- [ ] Currency conversion service
- [ ] Net worth calculation engine
- [ ] Historical snapshot generation (Celery task)

#### Phase 1.4: Household Management (Weeks 9-10)

- [ ] Household CRUD operations
- [ ] Member invitation system (email)
- [ ] Role-based access control
- [ ] Family net worth calculation
- [ ] Privacy controls

#### Phase 1.5: Basic Reporting & Dashboard (Weeks 11-12)

- [ ] Dashboard with key metrics
- [ ] Basic charts (Chart.js integration)
- [ ] Net worth trend visualization
- [ ] Asset/liability breakdown charts
- [ ] Export to CSV
- [ ] Responsive UI (Bootstrap)

### Phase 2: Automation & Advanced Features (8-10 weeks)

#### Phase 2.1: Statement Parsing (Weeks 1-4)

- [ ] File upload infrastructure
- [ ] OCR integration for images
- [ ] LLM API integration (Google Gemini 2.5 structured outputs)
- [ ] Structured output schema design
- [ ] Parsing service with confidence scoring
- [ ] User review and confirmation workflow
- [ ] Auto-mapping to existing accounts

#### Phase 2.2: Advanced Reporting (Weeks 5-7)

- [ ] PDF export (ReportLab or WeasyPrint)
- [ ] Excel export with formatting
- [ ] Detailed trend analysis reports
- [ ] Debt analysis report
- [ ] Family comparison report
- [ ] Scheduled email reports

#### Phase 2.3: Notifications & UX Enhancements (Weeks 8-10)

- [ ] Email notification system
- [ ] Payment due reminders
- [ ] Milestone alerts
- [ ] Data staleness warnings
- [ ] Improved UI/UX based on user feedback
- [ ] Accessibility improvements (WCAG AA)

### Phase 3: API Integration & Advanced Features (Future)

- [ ] Plaid/Yodlee integration
- [ ] Real-time portfolio updates
- [ ] Budgeting module integration
- [ ] Goal setting and tracking
- [ ] Investment performance analytics
- [ ] Tax reporting assistance
- [ ] Mobile app (React Native or Flutter)
- [ ] Modern SPA frontend (React/Next.js)

---

## 7. Success Metrics

### User Engagement

- Daily active users (DAU)
- Weekly active users (WAU)
- Average session duration
- Number of accounts tracked per user
- Data entry frequency (manual vs. automated)

### Feature Adoption

- % of users using household feature
- % of users using statement upload
- % of users using multi-currency
- Report generation frequency
- Export usage

### Quality Metrics

- Statement parsing accuracy rate (target: >90%)
- FX rate update success rate (target: >99%)
- System uptime (target: 99.5%)
- API response time (target: <500ms for 95th percentile)
- User-reported bugs per release

### Business Metrics

- User retention rate (30-day, 90-day)
- Feature completion rate (% of onboarding completed)
- User satisfaction score (NPS)
- Support ticket volume

---

## 8. Risks & Mitigation

### Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM parsing accuracy too low | High | Medium | Start with high-quality statements, iterate on prompts, allow manual correction |
| FX API rate limits/downtime | Medium | Medium | Cache aggressively, use fallback APIs, store historical rates |
| Data breach/security issue | Critical | Low | Follow security best practices, regular audits, encryption, penetration testing |
| Performance issues with large datasets | Medium | Medium | Implement pagination, caching, database indexing, query optimization |

### Product Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Low user adoption of automated features | Medium | Medium | Ensure manual entry is excellent, make automation optional, clear value prop |
| Privacy concerns with household sharing | Medium | Low | Granular privacy controls, clear documentation, opt-in approach |
| Complex UX for non-technical users | High | Medium | User testing, progressive disclosure, excellent onboarding, help documentation |

### Compliance Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| GDPR/data protection violations | Critical | Low | Implement data export, deletion, consent management |
| Financial data handling regulations | High | Low | Consult legal, avoid storing sensitive account credentials, clear ToS |

---

## 9. Future Considerations

### Potential Enhancements

- **AI-Powered Insights**: "You're spending more on credit card interest than last quarter"
- **Forecasting**: Predict future net worth based on trends
- **Debt Payoff Optimizer**: Avalanche vs. snowball method recommendations
- **Investment Recommendations**: Based on asset allocation (requires licensing)
- **Social Features**: Anonymous benchmarking against similar demographics
- **API for Third-Party Integrations**: Allow fintech apps to integrate
- **White-Label Solution**: For financial advisors to offer clients
- **Cryptocurrency Support**: Track crypto holdings with real-time pricing
- **Blockchain Integration**: Immutable audit trail (overkill for MVP, but interesting)

### Monetization Opportunities (Post-MVP)

- Freemium model (free for individuals, paid for families/advanced features)
- Premium features: Advanced analytics, unlimited statement parsing, priority support
- B2B offering for financial advisors
- Affiliate revenue (financial products, not recommended for trust reasons)
- API access for developers

---

## 10. Open Questions & Decisions Needed

1. **Branding**: What should we name this application?
2. **Pricing Strategy**: Free forever? Freemium? Subscription?
3. **Deployment**: Cloud hosting (AWS, GCP, Azure) or self-hosted option?
4. **LLM Provider**: Using Google Gemini 2.5 (advanced reasoning, 1M context window, multimodal)
5. **Frontend Timeline**: When to transition from Django templates to React SPA?
6. **Mobile Priority**: When should mobile app development begin?
7. **Compliance**: Do we need formal legal review before launch?
8. **Beta Testing**: Closed beta or public launch?

---

## 11. Appendix

### A. Competitive Landscape

- **Personal Capital**: Comprehensive but focuses on investment tracking
- **Mint**: Budget-focused, basic net worth tracking
- **YNAB**: Budgeting tool, not net worth focus
- **Empower**: Similar to Personal Capital
- **Monarch Money**: Modern UI, subscription-based
- **Spreadsheets**: Manual, flexible but time-consuming

**Our Differentiator**: Family/household view, LLM-powered statement parsing, multi-currency support out of the box, extensible architecture for future asset classes.

### B. Technology References

- Django Documentation: <https://docs.djangoproject.com/>
- Django REST Framework: <https://www.django-rest-framework.org/>
- Google Gemini API: <https://ai.google.dev/docs>
- Gemini Structured Outputs: <https://ai.google.dev/gemini-api/docs/json-mode>
- ExchangeRate-API: <https://www.exchangerate-api.com/>
- Chart.js: <https://www.chartjs.org/>

### C. Glossary

- **Net Worth**: Total assets minus total liabilities
- **Asset**: Anything of value owned by an individual or entity
- **Liability**: Financial obligations or debts owed
- **FX Rate**: Foreign exchange rate between two currencies
- **LLM**: Large Language Model (AI for text understanding/generation)
- **Structured Output**: JSON/formatted data output from LLM
- **RBAC**: Role-Based Access Control

---

**Next Review Date:** After Phase 1 MVP completion
**Approval Required From:** Product Owner, Tech Lead
