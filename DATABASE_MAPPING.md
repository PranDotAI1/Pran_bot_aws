# 📊 Complete Database Mapping

**Database**: `hospital`
**Host**: `hospital.cv8wum284gev.us-east-1.rds.amazonaws.com`

**Total Tables**: 6

---

## 📋 Table: `appointments`

### Columns

| Column Name | Data Type | Nullable | Default | Description |
|------------|-----------|----------|---------|-------------|
| `appointment_id` | `integer` | NO | nextval('appointments_appointment_id_seq'::regclass) | - |
| `patient_id` | `integer` | YES | - | - |
| `doctor_id` | `integer` | YES | - | - |
| `appointment_date` | `date` | YES | - | - |
| `appointment_time` | `time without time zone` | YES | - | - |
| `status` | `character varying(50)` | YES | 'scheduled'::character varying | - |
| `symptoms` | `text` | YES | - | - |
| `notes` | `text` | YES | - | - |
| `created_at` | `timestamp without time zone` | YES | CURRENT_TIMESTAMP | - |

**Row Count**: 10

**Primary Key**: `appointment_id`

**Foreign Keys**:

- `doctor_id` → `doctors.doctor_id`

### Sample Data

| appointment_id | patient_id | doctor_id | appointment_date | appointment_time | status | symptoms | notes | created_at |
|---|---|---|---|---|---|---|---|---|
| 1 | NULL | 3 | 2025-12-04 | 14:00:00 | completed | Abdominal pain | Follow-up appointment for Abdominal pain | 2025-12-03 09:23:12.494683 |
| 2 | NULL | 6 | 2025-12-26 | 09:00:00 | cancelled | Chest pain | Follow-up appointment for Chest pain | 2025-12-03 09:23:12.494683 |
| 3 | NULL | 17 | 2025-12-29 | 13:00:00 | scheduled | Headache and dizziness | Follow-up appointment for Headache and dizziness | 2025-12-03 09:23:12.494683 |
| 4 | NULL | 19 | 2025-12-11 | 14:00:00 | scheduled | Headache and dizziness | Follow-up appointment for Headache and dizziness | 2025-12-03 09:23:12.494683 |
| 5 | NULL | 13 | 2025-12-23 | 15:00:00 | cancelled | Chest pain | Follow-up appointment for Chest pain | 2025-12-03 09:23:12.494683 |

---

## 📋 Table: `availability_slots`

### Columns

| Column Name | Data Type | Nullable | Default | Description |
|------------|-----------|----------|---------|-------------|
| `slot_id` | `integer` | NO | nextval('availability_slots_slot_id_seq'::regclass) | - |
| `doctor_id` | `integer` | NO | - | - |
| `date` | `date` | NO | - | - |
| `start_time` | `time without time zone` | NO | - | - |
| `end_time` | `time without time zone` | NO | - | - |
| `available` | `boolean` | YES | true | - |
| `patient_id` | `integer` | YES | - | - |

**Row Count**: 200

**Primary Key**: `slot_id`

**Foreign Keys**:

- `doctor_id` → `doctors.doctor_id`
- `patient_id` → `patients.patient_id`

### Sample Data

| slot_id | doctor_id | date | start_time | end_time | available | patient_id |
|---|---|---|---|---|---|---|
| 5 | 1 | 2025-12-03 | 09:00:00 | 12:00:00 | True | NULL |
| 6 | 1 | 2025-12-03 | 13:00:00 | 16:00:00 | True | NULL |
| 7 | 1 | 2025-12-04 | 09:00:00 | 12:00:00 | True | NULL |
| 8 | 1 | 2025-12-04 | 13:00:00 | 16:00:00 | True | NULL |
| 9 | 1 | 2025-12-05 | 09:00:00 | 12:00:00 | True | NULL |

---

## 📋 Table: `doctors`

### Columns

| Column Name | Data Type | Nullable | Default | Description |
|------------|-----------|----------|---------|-------------|
| `doctor_id` | `integer` | NO | nextval('doctors_id_seq'::regclass) | - |
| `name` | `character varying(255)` | NO | - | - |
| `rating` | `numeric` | YES | - | - |
| `experience` | `integer` | YES | - | - |
| `doc_type` | `character varying(255)` | YES | 'physician'::character varying | - |
| `department` | `character varying(255)` | YES | - | - |
| `email` | `character varying(255)` | YES | - | - |
| `phone` | `character varying(50)` | YES | - | - |
| `specialty` | `character varying(255)` | YES | - | - |

**Row Count**: 23

**Primary Key**: `doctor_id`

### Sample Data

| doctor_id | name | rating | experience | doc_type | department | email | phone | specialty |
|---|---|---|---|---|---|---|---|---|
| 1 | Dr. Rajesh Kumar | 4.80 | 15 | physician | NULL | NULL | NULL | NULL |
| 2 | Dr. Ananya Sharma | 4.50 | 10 | physician | NULL | NULL | NULL | NULL |
| 3 | Dr. Vikram Patel | 4.20 | 8 | physician | NULL | NULL | NULL | NULL |
| 4 | Dr. Neha Verma | 4.70 | 12 | physician | NULL | NULL | NULL | NULL |
| 5 | Dr. Arjun Mehta | 4.60 | 9 | physician | NULL | NULL | NULL | NULL |

---

## 📋 Table: `insurance_plans`

### Columns

| Column Name | Data Type | Nullable | Default | Description |
|------------|-----------|----------|---------|-------------|
| `plan_id` | `integer` | NO | nextval('insurance_plans_plan_id_seq'::regclass) | - |
| `plan_name` | `character varying(255)` | NO | - | - |
| `monthly_premium` | `numeric` | YES | - | - |
| `deductible` | `numeric` | YES | - | - |
| `coverage_percentage` | `integer` | YES | - | - |
| `features` | `ARRAY` | YES | - | - |
| `is_active` | `boolean` | YES | true | - |
| `created_at` | `timestamp without time zone` | YES | CURRENT_TIMESTAMP | - |

**Row Count**: 5

**Primary Key**: `plan_id`

### Sample Data

| plan_id | plan_name | monthly_premium | deductible | coverage_percentage | features | is_active | created_at |
|---|---|---|---|---|---|---|---|
| 1 | Basic Health Plan | 150.00 | 1000.00 | 80 | ['Primary care visits', 'Emergency visits', 'Basic | True | 2025-12-03 09:23:12.494683 |
| 2 | Premium Health Plan | 300.00 | 500.00 | 90 | ['All basic features', 'Specialist visits', 'Menta | True | 2025-12-03 09:23:12.494683 |
| 3 | Family Health Plan | 450.00 | 750.00 | 85 | ['All premium features', 'Family coverage (up to 4 | True | 2025-12-03 09:23:12.494683 |
| 4 | Senior Care Plan | 250.00 | 600.00 | 88 | ['All basic features', 'Senior-specific care', 'Ch | True | 2025-12-03 09:23:12.494683 |
| 5 | Student Health Plan | 100.00 | 500.00 | 75 | ['Basic coverage', 'Student health center access', | True | 2025-12-03 09:23:12.494683 |

---

## 📋 Table: `medical_records`

### Columns

| Column Name | Data Type | Nullable | Default | Description |
|------------|-----------|----------|---------|-------------|
| `record_id` | `integer` | NO | nextval('medical_records_record_id_seq'::regclass) | - |
| `patient_id` | `integer` | YES | - | - |
| `doctor_id` | `integer` | YES | - | - |
| `record_type` | `character varying(100)` | YES | - | - |
| `record_date` | `date` | YES | - | - |
| `diagnosis` | `text` | YES | - | - |
| `treatment` | `text` | YES | - | - |
| `notes` | `text` | YES | - | - |
| `created_at` | `timestamp without time zone` | YES | CURRENT_TIMESTAMP | - |

**Row Count**: 5

**Primary Key**: `record_id`

**Foreign Keys**:

- `doctor_id` → `doctors.doctor_id`

### Sample Data

| record_id | patient_id | doctor_id | record_type | record_date | diagnosis | treatment | notes | created_at |
|---|---|---|---|---|---|---|---|---|
| 1 | NULL | 16 | Lab Test | 2025-12-03 | Blood test results normal | No treatment needed | Routine checkup | 2025-12-03 09:23:12.494683 |
| 2 | NULL | 14 | Lab Test | 2025-12-03 | Cholesterol slightly elevated | Diet modification recommended | Follow-up in 3 months | 2025-12-03 09:23:12.494683 |
| 3 | NULL | 9 | Diagnosis | 2025-12-03 | Common cold | Rest and fluids | Viral infection | 2025-12-03 09:23:12.494683 |
| 4 | NULL | 16 | Diagnosis | 2025-12-03 | Hypertension | Medication prescribed | Monitor blood pressure | 2025-12-03 09:23:12.494683 |
| 5 | NULL | 1 | Treatment | 2025-12-03 | Physical therapy | 6 sessions recommended | Post-surgery recovery | 2025-12-03 09:23:12.494683 |

---

## 📋 Table: `patients`

### Columns

| Column Name | Data Type | Nullable | Default | Description |
|------------|-----------|----------|---------|-------------|
| `patient_id` | `integer` | NO | nextval('patients_patient_id_seq'::regclass) | - |
| `first_name` | `character varying(100)` | NO | - | - |
| `last_name` | `character varying(100)` | NO | - | - |
| `date_of_birth` | `date` | NO | - | - |
| `gender` | `character varying(10)` | YES | - | - |
| `contact_number` | `character varying(15)` | NO | - | - |
| `email` | `character varying(255)` | YES | - | - |
| `address` | `text` | YES | - | - |
| `emergency_contact_name` | `character varying(100)` | YES | - | - |
| `emergency_contact_number` | `character varying(15)` | YES | - | - |
| `date_registered` | `timestamp without time zone` | YES | CURRENT_TIMESTAMP | - |

**Row Count**: 0

**Primary Key**: `patient_id`


---

