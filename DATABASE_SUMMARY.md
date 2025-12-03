# 📊 Database Mapping Summary

## ✅ Database Connection

- **Host**: `hospital.cv8wum284gev.us-east-1.rds.amazonaws.com`
- **Database**: `hospital`
- **Type**: PostgreSQL/Aurora
- **Status**: ✅ Connected and Mapped

---

## 📋 Tables Overview

| Table Name | Rows | Columns | Primary Key | Foreign Keys |
|------------|------|---------|-------------|--------------|
| `doctors` | 23 | 9 | `doctor_id` | - |
| `insurance_plans` | 5 | 8 | `plan_id` | - |
| `appointments` | 10 | 9 | `appointment_id` | `doctor_id` → `doctors.doctor_id` |
| `availability_slots` | 200 | 7 | `slot_id` | `doctor_id` → `doctors.doctor_id`, `patient_id` → `patients.patient_id` |
| `medical_records` | 5 | 9 | `record_id` | `doctor_id` → `doctors.doctor_id` |
| `patients` | 0 | 11 | `patient_id` | - |

**Total**: 6 tables, 243 rows of data

---

## 🔍 Detailed Table Mappings

### 1. **doctors** (23 rows)

**Columns**:
- `doctor_id` (integer, PK) - Unique doctor identifier
- `name` (varchar(255)) - Doctor's full name
- `rating` (numeric) - Doctor rating (0-5)
- `experience` (integer) - Years of experience
- `doc_type` (varchar(255)) - Type: physician, gynecologist, cardiologist, etc.
- `department` (varchar(255)) - Department name
- `email` (varchar(255)) - Email address
- `phone` (varchar(50)) - Phone number
- `specialty` (varchar(255)) - Medical specialty

**Code Mapping**:
- ✅ `DatabaseHelper.get_doctors()` - Maps `doc_type` to `specialty`
- ✅ Handles missing columns: `department`, `email`, `phone`
- ✅ Uses `doc_type` column for specialty filtering

**Sample Data**:
- Dr. Rajesh Kumar (rating: 4.80, experience: 15)
- Dr. Ananya Sharma (rating: 4.50, experience: 10)
- Dr. Vikram Patel (rating: 4.20, experience: 8)

---

### 2. **insurance_plans** (5 rows)

**Columns**:
- `plan_id` (integer, PK) - Unique plan identifier
- `plan_name` (varchar(255)) - Plan name
- `monthly_premium` (numeric) - Monthly premium cost
- `deductible` (numeric) - Deductible amount
- `coverage_percentage` (integer) - Coverage percentage (0-100)
- `features` (ARRAY) - Array of plan features
- `is_active` (boolean) - Whether plan is active
- `created_at` (timestamp) - Creation timestamp

**Code Mapping**:
- ✅ `DatabaseHelper.get_insurance_plans()` - Queries with `is_active = true`
- ✅ Maps `plan_name` → `name`
- ✅ Formats `monthly_premium` as "$150.00"
- ✅ Formats `coverage_percentage` as "80%"
- ✅ Formats `deductible` as "$1000.00"
- ✅ Handles PostgreSQL array format for `features`

**Sample Plans**:
1. Basic Health Plan - $150/month, $1000 deductible, 80% coverage
2. Premium Health Plan - $300/month, $500 deductible, 90% coverage
3. Family Health Plan - $450/month, $750 deductible, 85% coverage
4. Student Health Plan - $100/month, $500 deductible, 75% coverage
5. Senior Care Plan - $250/month, $600 deductible, 88% coverage

---

### 3. **appointments** (10 rows)

**Columns**:
- `appointment_id` (integer, PK)
- `patient_id` (integer, FK → patients.patient_id)
- `doctor_id` (integer, FK → doctors.doctor_id)
- `appointment_date` (date)
- `appointment_time` (time)
- `status` (varchar(50)) - scheduled, completed, cancelled
- `symptoms` (text)
- `notes` (text)
- `created_at` (timestamp)

**Code Mapping**:
- ✅ `DatabaseHelper.get_appointments()` - Retrieves by patient_id or user_id
- ✅ `RAGRetriever.retrieve_appointments()` - Retrieves for RAG context

---

### 4. **availability_slots** (200 rows)

**Columns**:
- `slot_id` (integer, PK)
- `doctor_id` (integer, FK → doctors.doctor_id, NOT NULL)
- `date` (date, NOT NULL)
- `start_time` (time, NOT NULL)
- `end_time` (time, NOT NULL)
- `available` (boolean, default: true)
- `patient_id` (integer, FK → patients.patient_id)

**Code Mapping**:
- ✅ Used for booking appointments
- ✅ Filtered by `available = true`
- ✅ Text-to-SQL Agent can query this table

---

### 5. **medical_records** (5 rows)

**Columns**:
- `record_id` (integer, PK)
- `patient_id` (integer)
- `doctor_id` (integer, FK → doctors.doctor_id)
- `record_type` (varchar(100)) - Lab Test, Diagnosis, Treatment
- `record_date` (date)
- `diagnosis` (text)
- `treatment` (text)
- `notes` (text)
- `created_at` (timestamp)

**Code Mapping**:
- ✅ `RAGRetriever.retrieve_medical_records()` - Retrieves for RAG context
- ✅ Used for lab results, diagnosis, treatment history

---

### 6. **patients** (0 rows - Empty)

**Columns**:
- `patient_id` (integer, PK)
- `first_name` (varchar(100))
- `last_name` (varchar(100))
- `date_of_birth` (date)
- `gender` (varchar(10))
- `contact_number` (varchar(15))
- `email` (varchar(255))
- `address` (text)
- `emergency_contact_name` (varchar(100))
- `emergency_contact_number` (varchar(15))
- `date_registered` (timestamp)

**Code Mapping**:
- ✅ `DatabaseHelper.get_patient_info()` - Queries by patient_id or user_id
- ⚠️ Table is currently empty (0 rows)

---

## 🔗 Relationships

```
doctors (1) ──→ (many) appointments
doctors (1) ──→ (many) availability_slots
doctors (1) ──→ (many) medical_records
patients (1) ──→ (many) appointments
patients (1) ──→ (many) availability_slots
```

---

## ✅ Code Mapping Status

### **Doctors Table**
- ✅ `DatabaseHelper.get_doctors()` - Correctly mapped
- ✅ Handles `doc_type` → `specialty` mapping
- ✅ Handles missing columns gracefully
- ✅ Falls back to sample data if query fails

### **Insurance Plans Table**
- ✅ `DatabaseHelper.get_insurance_plans()` - Correctly mapped
- ✅ Formats values correctly (premium, coverage, deductible)
- ✅ Handles PostgreSQL array format for features
- ✅ Falls back to sample data if query fails

### **Appointments Table**
- ✅ `DatabaseHelper.get_appointments()` - Correctly mapped
- ✅ `RAGRetriever.retrieve_appointments()` - Correctly mapped

### **Availability Slots Table**
- ✅ Text-to-SQL Agent can query this table
- ✅ Used for booking logic

### **Medical Records Table**
- ✅ `RAGRetriever.retrieve_medical_records()` - Correctly mapped

### **Patients Table**
- ✅ `DatabaseHelper.get_patient_info()` - Correctly mapped
- ⚠️ Table is empty (no patient data yet)

---

## 🎯 Recommendations

1. **Patients Table**: Currently empty - consider populating with sample data
2. **Doctors Table**: Some doctors missing `department`, `email`, `phone` - code handles this gracefully
3. **Insurance Plans**: All 5 plans are active and properly formatted
4. **Appointments**: 10 appointments exist, mostly without patient_id (can be linked when patients are added)

---

## 📄 Files Created

- `DATABASE_MAPPING.md` - Complete detailed mapping
- `database_mapping.json` - JSON format mapping
- `DATABASE_SUMMARY.md` - This summary document

---

## ✅ Status

**All database tables are properly mapped and accessible!**

The bot can now:
- ✅ Query doctors from database
- ✅ Query insurance plans from database
- ✅ Query appointments
- ✅ Query availability slots
- ✅ Query medical records
- ✅ Handle missing data gracefully
- ✅ Fall back to sample data when needed

