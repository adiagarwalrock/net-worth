# Centralized Enum Mapping Documentation

This document verifies that LLM extraction schemas match database model choices exactly.

## Purpose

All type choices across the application are centralized in `common/enums.py` to ensure:
1. **Consistency**: LLM extraction and database use identical values
2. **Maintainability**: Single source of truth for all type definitions
3. **Accuracy**: No mismatches between Pydantic schemas and Django models

## Enum Classes

### 1. AssetType

**Used by:**
- `assets/models.py` - Asset.ASSET_TYPE_CHOICES
- `reports/schemas.py` - (indirectly via AccountType mapping)

**Values:**
```python
CASH = 'CASH'                      # Cash & Bank Accounts
INVESTMENT = 'INVESTMENT'          # Investment Portfolio
REAL_ESTATE = 'REAL_ESTATE'        # Real Estate
VEHICLE = 'VEHICLE'                # Vehicle
PRECIOUS_METALS = 'PRECIOUS_METALS' # Precious Metals
CRYPTOCURRENCY = 'CRYPTOCURRENCY'   # Cryptocurrency
OTHER = 'OTHER'                    # Other
```

**Mapping:**
- All deposit account types (CHECKING, SAVINGS, CURRENT, MONEY_MARKET) map to `AssetType.CASH`

---

### 2. LiabilityType

**Used by:**
- `liabilities/models.py` - Liability.LIABILITY_TYPE_CHOICES
- `reports/schemas.py` - (indirectly via AccountType mapping)

**Values:**
```python
CREDIT_CARD = 'CREDIT_CARD'        # Credit Card
MORTGAGE = 'MORTGAGE'              # Mortgage/Home Loan
AUTO_LOAN = 'AUTO_LOAN'            # Auto/Vehicle Loan
STUDENT_LOAN = 'STUDENT_LOAN'      # Student/Education Loan
MEDICAL_LOAN = 'MEDICAL_LOAN'      # Medical Loan
PERSONAL_LOAN = 'PERSONAL_LOAN'    # Personal Loan
LINE_OF_CREDIT = 'LINE_OF_CREDIT'  # Line of Credit
OTHER = 'OTHER'                    # Other
```

**Mapping:**
- `AccountType.CREDIT_CARD` → `LiabilityType.CREDIT_CARD`
- `AccountType.LOAN` → `LiabilityType.PERSONAL_LOAN` (inferred from keywords)
- `AccountType.MORTGAGE` → `LiabilityType.MORTGAGE`
- `AccountType.AUTO_LOAN` → `LiabilityType.AUTO_LOAN`
- `AccountType.STUDENT_LOAN` → `LiabilityType.STUDENT_LOAN`

---

### 3. AccountType

**Used by:**
- `reports/schemas.py` - AccountSummary.account_type (LLM extraction)
- `reports/services.py` - Statement data population routing

**Values:**
```python
# Deposit accounts (map to Asset.CASH)
CHECKING = 'CHECKING'
SAVINGS = 'SAVINGS'
CURRENT = 'CURRENT'
MONEY_MARKET = 'MONEY_MARKET'

# Credit accounts (map to Liability.CREDIT_CARD)
CREDIT_CARD = 'CREDIT_CARD'

# Loan accounts (map to various Liability types)
LOAN = 'LOAN'
MORTGAGE = 'MORTGAGE'
AUTO_LOAN = 'AUTO_LOAN'
STUDENT_LOAN = 'STUDENT_LOAN'
PERSONAL_LOAN = 'PERSONAL_LOAN'
```

**Routing Logic (reports/services.py:163-177):**
```python
if account_type == AccountType.CREDIT_CARD:
    → _populate_credit_card() → Liability(type=CREDIT_CARD)

elif account_type in [LOAN, MORTGAGE, AUTO_LOAN, STUDENT_LOAN, PERSONAL_LOAN]:
    → _populate_loan() → Liability(type=inferred from keywords)

elif account_type in [CHECKING, SAVINGS, CURRENT, MONEY_MARKET]:
    → _populate_deposit_account() → Asset(type=CASH)
```

---

### 4. TransactionType

**Used by:**
- `reports/schemas.py` - Transaction.transaction_type (LLM extraction)

**Values:**
```python
DEBIT = 'DEBIT'
CREDIT = 'CREDIT'
FEE = 'FEE'
INTEREST = 'INTEREST'
TRANSFER = 'TRANSFER'
PAYMENT = 'PAYMENT'
WITHDRAWAL = 'WITHDRAWAL'
DEPOSIT = 'DEPOSIT'
PURCHASE = 'PURCHASE'
REFUND = 'REFUND'
OTHER = 'OTHER'
```

**Note:** Currently used for statement parsing metadata only, not stored in database.

---

### 5. HistorySource

**Used by:**
- `assets/models.py` - AssetHistory.SOURCE_CHOICES
- `liabilities/models.py` - LiabilityHistory.SOURCE_CHOICES

**Values:**
```python
MANUAL = 'MANUAL'                    # Manual Entry
STATEMENT_UPLOAD = 'STATEMENT_UPLOAD' # Statement Upload
API_SYNC = 'API_SYNC'                # API Sync
```

**Usage:**
- Manual entry via admin: `MANUAL`
- Statement parser: `STATEMENT_UPLOAD`
- Future API integrations: `API_SYNC`

---

### 6. HouseholdRole

**Used by:**
- `households/models.py` - HouseholdMember.ROLE_CHOICES

**Values:**
```python
OWNER = 'OWNER'      # Owner
MEMBER = 'MEMBER'    # Member
VIEWER = 'VIEWER'    # Viewer
```

---

### 7. InvitationStatus

**Used by:**
- `households/models.py` - HouseholdInvitation.STATUS_CHOICES

**Values:**
```python
PENDING = 'PENDING'     # Pending
ACCEPTED = 'ACCEPTED'   # Accepted
DECLINED = 'DECLINED'   # Declined
EXPIRED = 'EXPIRED'     # Expired
```

---

### 8. StatementUploadStatus

**Used by:**
- `reports/models.py` - StatementUpload.STATUS_CHOICES

**Values:**
```python
PENDING = 'PENDING'         # Pending
PROCESSING = 'PROCESSING'   # Processing
COMPLETED = 'COMPLETED'     # Completed
FAILED = 'FAILED'          # Failed
```

---

## Verification Checklist

### ✅ Asset Model
- [x] Import from `common.enums`
- [x] Use `AssetType.choices()` for `ASSET_TYPE_CHOICES`
- [x] Use `HistorySource.choices()` for `SOURCE_CHOICES`
- [x] Constants reference enum values (e.g., `CASH = AssetType.CASH.value`)

### ✅ Liability Model
- [x] Import from `common.enums`
- [x] Use `LiabilityType.choices()` for `LIABILITY_TYPE_CHOICES`
- [x] Use `HistorySource.choices()` for `SOURCE_CHOICES`
- [x] Constants reference enum values (e.g., `CREDIT_CARD = LiabilityType.CREDIT_CARD.value`)

### ✅ Pydantic Schemas (reports/schemas.py)
- [x] Import from `common.enums`
- [x] Use `AccountType` for `account_type` field
- [x] Use `TransactionType` for `transaction_type` field

### ✅ Services (reports/services.py)
- [x] Import from `common.enums`
- [x] Route using `AccountType` enum values
- [x] Handle both enum objects and string values
- [x] Map AccountType → AssetType/LiabilityType correctly

## Testing Recommendations

1. **Unit Tests**: Verify enum value equality
   ```python
   assert AssetType.CASH.value == 'CASH'
   assert Asset.CASH == 'CASH'
   ```

2. **Integration Tests**: Test statement parsing end-to-end
   - Parse sample statements with all account types
   - Verify correct Asset/Liability creation
   - Verify history source is STATEMENT_UPLOAD

3. **LLM Output Validation**: Test Pydantic schema validation
   - Generate test JSONs with all enum values
   - Verify Pydantic accepts all valid values
   - Verify Pydantic rejects invalid values

## Migration Guide

If you need to add a new type:

1. **Add to `common/enums.py`**:
   ```python
   class AssetType(str, Enum):
       NEW_TYPE = 'NEW_TYPE'

       @classmethod
       def choices(cls):
           return [
               ...
               (cls.NEW_TYPE.value, 'New Type Display'),
           ]
   ```

2. **Update relevant models**:
   - Constants will automatically include new value
   - No changes needed if using `AssetType.choices()`

3. **Update schemas if needed**:
   - Pydantic will automatically accept new enum value

4. **Update services if needed**:
   - Add routing logic for new account type mapping

5. **Create migration**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

## Benefits

1. **Single Source of Truth**: All type definitions in one place
2. **Type Safety**: Enums provide IDE autocomplete and type checking
3. **Consistency**: LLM and database always match
4. **Maintainability**: Changes propagate automatically
5. **Documentation**: Self-documenting with enum names and choices
