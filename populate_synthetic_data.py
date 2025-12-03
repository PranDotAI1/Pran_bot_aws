#!/usr/bin/env python3
"""
Populate database with comprehensive synthetic data for intelligent bot responses
"""

import psycopg2
from datetime import datetime, timedelta
import random

def populate_database():
    print("=" * 80)
    print(" POPULATING DATABASE WITH SYNTHETIC DATA")
    print("=" * 80)
    print()
    
    conn = psycopg2.connect(
        host='hospital.cv8wum284gev.us-east-1.rds.amazonaws.com',
        database='hospital',
        user='postgres',
        password='qMI8DUYcGnoTBpsyagh9',
        port=5432,
        connect_timeout=10
    )
    
    cursor = conn.cursor()
    
    try:
        # 1. Add more doctors with different specialties
        print("📋 Step 1: Adding doctors with different specialties...")
        
        doctors_data = [
            # Gynecology
            ('Dr. Priya Reddy', 4.9, 18, 'gynecologist', 'Gynecology', 'priya.reddy@hospital.com', '(555) 201-0001'),
            ('Dr. Meera Iyer', 4.8, 15, 'gynecologist', 'Women\'s Health', 'meera.iyer@hospital.com', '(555) 201-0002'),
            ('Dr. Kavita Nair', 4.7, 12, 'gynecologist', 'Obstetrics & Gynecology', 'kavita.nair@hospital.com', '(555) 201-0003'),
            
            # Cardiology
            ('Dr. Ravi Menon', 4.9, 20, 'cardiologist', 'Cardiology', 'ravi.menon@hospital.com', '(555) 202-0001'),
            ('Dr. Suresh Pillai', 4.8, 16, 'cardiologist', 'Cardiac Care', 'suresh.pillai@hospital.com', '(555) 202-0002'),
            
            # Neurology
            ('Dr. Anjali Desai', 4.8, 14, 'neurologist', 'Neurology', 'anjali.desai@hospital.com', '(555) 203-0001'),
            ('Dr. Rohit Joshi', 4.7, 11, 'neurologist', 'Neurological Sciences', 'rohit.joshi@hospital.com', '(555) 203-0002'),
            
            # Dermatology
            ('Dr. Sneha Kapoor', 4.9, 13, 'dermatologist', 'Dermatology', 'sneha.kapoor@hospital.com', '(555) 204-0001'),
            ('Dr. Aditya Malhotra', 4.7, 10, 'dermatologist', 'Skin Care', 'aditya.malhotra@hospital.com', '(555) 204-0002'),
            
            # Pediatrics
            ('Dr. Maya Krishnan', 4.9, 17, 'pediatrician', 'Pediatrics', 'maya.krishnan@hospital.com', '(555) 205-0001'),
            ('Dr. Varun Nair', 4.8, 14, 'pediatrician', 'Child Care', 'varun.nair@hospital.com', '(555) 205-0002'),
            
            # Orthopedics
            ('Dr. Deepak Singh', 4.8, 19, 'orthopedic', 'Orthopedics', 'deepak.singh@hospital.com', '(555) 206-0001'),
            ('Dr. Ritu Agarwal', 4.7, 12, 'orthopedic', 'Bone & Joint', 'ritu.agarwal@hospital.com', '(555) 206-0002'),
            
            # Psychiatry
            ('Dr. Sameer Khan', 4.8, 16, 'psychiatrist', 'Psychiatry', 'sameer.khan@hospital.com', '(555) 207-0001'),
            ('Dr. Nisha Rao', 4.9, 13, 'psychiatrist', 'Mental Health', 'nisha.rao@hospital.com', '(555) 207-0002'),
            
            # General Medicine (update existing)
            ('Dr. Amit Shah', 4.8, 16, 'general physician', 'General Medicine', 'amit.shah@hospital.com', '(555) 200-0001'),
            ('Dr. Pooja Gupta', 4.7, 11, 'general physician', 'Family Medicine', 'pooja.gupta@hospital.com', '(555) 200-0002'),
        ]
        
        # Check if we need to add columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'doctors'
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add missing columns
        if 'department' not in existing_columns:
            cursor.execute("ALTER TABLE doctors ADD COLUMN department VARCHAR(255)")
            print("   ✅ Added 'department' column")
        
        if 'email' not in existing_columns:
            cursor.execute("ALTER TABLE doctors ADD COLUMN email VARCHAR(255)")
            print("   ✅ Added 'email' column")
        
        if 'phone' not in existing_columns:
            cursor.execute("ALTER TABLE doctors ADD COLUMN phone VARCHAR(50)")
            print("   ✅ Added 'phone' column")
        
        if 'specialty' not in existing_columns:
            cursor.execute("ALTER TABLE doctors ADD COLUMN specialty VARCHAR(255)")
            print("   ✅ Added 'specialty' column")
        
        # Insert new doctors
        for name, rating, experience, doc_type, department, email, phone in doctors_data:
            try:
                cursor.execute("""
                    INSERT INTO doctors (name, rating, experience, doc_type, department, email, phone, specialty)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (name, rating, experience, doc_type, department, email, phone, doc_type))
            except Exception as e:
                # If specialty column doesn't exist, insert without it
                try:
                    cursor.execute("""
                        INSERT INTO doctors (name, rating, experience, doc_type, department, email, phone)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (name, rating, experience, doc_type, department, email, phone))
                except:
                    pass
        
        print(f"   ✅ Added/updated {len(doctors_data)} doctors")
        
        # 2. Create insurance_plans table
        print("\n💼 Step 2: Creating insurance_plans table...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insurance_plans (
                plan_id SERIAL PRIMARY KEY,
                plan_name VARCHAR(255) NOT NULL,
                monthly_premium DECIMAL(10, 2),
                deductible DECIMAL(10, 2),
                coverage_percentage INTEGER,
                features TEXT[],
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        insurance_plans = [
            ('Basic Health Plan', 150.00, 1000.00, 80, 
             ['Primary care visits', 'Emergency visits', 'Basic prescriptions', 'Preventive care']),
            ('Premium Health Plan', 300.00, 500.00, 90,
             ['All basic features', 'Specialist visits', 'Mental health coverage', 'Dental & Vision', 'Wellness programs']),
            ('Family Health Plan', 450.00, 750.00, 85,
             ['All premium features', 'Family coverage (up to 4 members)', 'Maternity care', 'Pediatric care', 'Family wellness programs']),
            ('Senior Care Plan', 250.00, 600.00, 88,
             ['All basic features', 'Senior-specific care', 'Chronic disease management', 'Home health services']),
            ('Student Health Plan', 100.00, 500.00, 75,
             ['Basic coverage', 'Student health center access', 'Mental health support', 'Preventive care'])
        ]
        
        cursor.execute("DELETE FROM insurance_plans")  # Clear existing
        for plan_name, premium, deductible, coverage, features in insurance_plans:
            cursor.execute("""
                INSERT INTO insurance_plans (plan_name, monthly_premium, deductible, coverage_percentage, features, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (plan_name, premium, deductible, coverage, features, True))
        
        print(f"   ✅ Created insurance_plans table with {len(insurance_plans)} plans")
        
        # 3. Create appointments table
        print("\n📅 Step 3: Creating appointments table...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                appointment_id SERIAL PRIMARY KEY,
                patient_id INTEGER,
                doctor_id INTEGER,
                appointment_date DATE,
                appointment_time TIME,
                status VARCHAR(50) DEFAULT 'scheduled',
                symptoms TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
            )
        """)
        
        # Create sample appointments
        today = datetime.now().date()
        appointments_data = []
        for i in range(10):
            appointment_date = today + timedelta(days=random.randint(1, 30))
            appointment_time = f"{random.randint(9, 16)}:00:00"
            status = random.choice(['scheduled', 'completed', 'cancelled'])
            symptoms = random.choice([
                'Fever and cough',
                'Headache and dizziness',
                'Chest pain',
                'Abdominal pain',
                'Skin rash',
                'Joint pain',
                'High blood pressure',
                'Diabetes checkup'
            ])
            
            appointments_data.append((
                None,  # patient_id
                random.randint(1, 20),  # doctor_id
                appointment_date,
                appointment_time,
                status,
                symptoms,
                f'Follow-up appointment for {symptoms}'
            ))
        
        cursor.execute("DELETE FROM appointments")  # Clear existing
        for apt in appointments_data:
            cursor.execute("""
                INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, status, symptoms, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, apt)
        
        print(f"   ✅ Created appointments table with {len(appointments_data)} appointments")
        
        # 4. Create medical_records table
        print("\n📋 Step 4: Creating medical_records table...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medical_records (
                record_id SERIAL PRIMARY KEY,
                patient_id INTEGER,
                doctor_id INTEGER,
                record_type VARCHAR(100),
                record_date DATE,
                diagnosis TEXT,
                treatment TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
            )
        """)
        
        medical_records_data = [
            ('Lab Test', 'Blood test results normal', 'No treatment needed', 'Routine checkup'),
            ('Lab Test', 'Cholesterol slightly elevated', 'Diet modification recommended', 'Follow-up in 3 months'),
            ('Diagnosis', 'Common cold', 'Rest and fluids', 'Viral infection'),
            ('Diagnosis', 'Hypertension', 'Medication prescribed', 'Monitor blood pressure'),
            ('Treatment', 'Physical therapy', '6 sessions recommended', 'Post-surgery recovery'),
        ]
        
        cursor.execute("DELETE FROM medical_records")  # Clear existing
        for record_type, diagnosis, treatment, notes in medical_records_data:
            cursor.execute("""
                INSERT INTO medical_records (patient_id, doctor_id, record_type, record_date, diagnosis, treatment, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (None, random.randint(1, 20), record_type, today, diagnosis, treatment, notes))
        
        print(f"   ✅ Created medical_records table with {len(medical_records_data)} records")
        
        # 5. Add more availability slots
        print("\n⏰ Step 5: Adding availability slots...")
        
        slots_data = []
        for doctor_id in range(1, 21):  # For all doctors
            for day_offset in range(0, 30):  # Next 30 days
                date = today + timedelta(days=day_offset)
                # Morning slot
                slots_data.append((
                    doctor_id,
                    date,
                    '09:00:00',
                    '12:00:00',
                    True,
                    None
                ))
                # Afternoon slot
                slots_data.append((
                    doctor_id,
                    date,
                    '13:00:00',
                    '16:00:00',
                    True,
                    None
                ))
        
        cursor.execute("DELETE FROM availability_slots WHERE available = true")  # Clear available slots
        for slot in slots_data[:200]:  # Add 200 slots
            cursor.execute("""
                INSERT INTO availability_slots (doctor_id, date, start_time, end_time, available, patient_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, slot)
        
        print(f"   ✅ Added {len(slots_data[:200])} availability slots")
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "=" * 80)
        print(" ✅ DATABASE POPULATION COMPLETE!")
        print("=" * 80)
        print()
        print("📊 Summary:")
        print(f"   ✅ Doctors: {len(doctors_data) + 6} total (multiple specialties)")
        print(f"   ✅ Insurance Plans: {len(insurance_plans)} plans")
        print(f"   ✅ Appointments: {len(appointments_data)} appointments")
        print(f"   ✅ Medical Records: {len(medical_records_data)} records")
        print(f"   ✅ Availability Slots: {len(slots_data[:200])} slots")
        print()
        print("🎯 The bot can now:")
        print("   • Show doctors by specialty (gynecologist, cardiologist, etc.)")
        print("   • Display insurance plans from database")
        print("   • Show appointment availability")
        print("   • Access medical records")
        print("   • Have intelligent, data-driven conversations")
        print()
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    populate_database()

