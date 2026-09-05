import random
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.db import sync_engine, Base
from backend.app.models.entities import Hospital, Doctor, Patient, Donor, BloodInventory, BloodRequest, Donation, DonorMatchingResult

def seed_database():
    print("Seeding PostgreSQL database with realistic healthcare operational data...")
    Base.metadata.create_all(bind=sync_engine)
    
    session = Session(bind=sync_engine)
    
    try:
        # Check if hospitals exist
        if session.query(Hospital).count() > 0:
            print("Database already contains data. Skipping seed generation.")
            return

        # 1. Create Hospitals
        hospitals_data = [
            {
                "name": "St. Jude Memorial Hospital & Medical Center",
                "code": "HOSP-001",
                "address": "100 Medical Center Way",
                "city": "Metropolis",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "phone": "+1-555-0100",
                "emergency_contact": "+1-555-0199"
            },
            {
                "name": "Metro Regional Trauma Center",
                "code": "HOSP-002",
                "address": "450 Emergency Boulevard",
                "city": "Metropolis",
                "latitude": 40.7306,
                "longitude": -73.9352,
                "phone": "+1-555-0200",
                "emergency_contact": "+1-555-0299"
            },
            {
                "name": "City Care Blood Bank & Institute",
                "code": "HOSP-003",
                "address": "78 Life Saving Lane",
                "city": "Downtown",
                "latitude": 40.7589,
                "longitude": -73.9851,
                "phone": "+1-555-0300",
                "emergency_contact": "+1-555-0399"
            }
        ]

        hospitals = [Hospital(**h) for h in hospitals_data]
        session.add_all(hospitals)
        session.commit()
        for h in hospitals:
            session.refresh(h)
            
        print(f"Created {len(hospitals)} Hospitals.")

        # 2. Create Doctors
        doctors_data = [
            {"hospital_id": hospitals[0].id, "name": "Dr. Sarah Jenkins", "license_number": "DOC-9901", "specialization": "Trauma Surgery", "phone": "+1-555-1001", "email": "sjenkins@stjude.org"},
            {"hospital_id": hospitals[0].id, "name": "Dr. Robert Vance", "license_number": "DOC-9902", "specialization": "Hematology", "phone": "+1-555-1002", "email": "rvance@stjude.org"},
            {"hospital_id": hospitals[1].id, "name": "Dr. Elena Rostova", "license_number": "DOC-9903", "specialization": "Critical Care", "phone": "+1-555-1003", "email": "erostova@metro.org"},
            {"hospital_id": hospitals[2].id, "name": "Dr. Marcus Thorne", "license_number": "DOC-9904", "specialization": "Transfusion Medicine", "phone": "+1-555-1004", "email": "mthorne@citycare.org"}
        ]
        doctors = [Doctor(**d) for d in doctors_data]
        session.add_all(doctors)
        session.commit()
        for d in doctors:
            session.refresh(d)
            
        print(f"Created {len(doctors)} Doctors.")

        # 3. Create Patients
        patients_data = [
            {"hospital_id": hospitals[0].id, "name": "John Doe", "medical_record_number": "MRN-1001", "age": 42, "gender": "Male", "blood_group": "O", "rh_factor": "-", "condition_summary": "Acute hemoperitoneum secondary to blunt trauma"},
            {"hospital_id": hospitals[0].id, "name": "Emily Watson", "medical_record_number": "MRN-1002", "age": 29, "gender": "Female", "blood_group": "A", "rh_factor": "+", "condition_summary": "Postpartum hemorrhage requiring urgent blood volume restoration"},
            {"hospital_id": hospitals[1].id, "name": "Michael Chang", "medical_record_number": "MRN-1003", "age": 61, "gender": "Male", "blood_group": "B", "rh_factor": "+", "condition_summary": "Open heart surgery vascular bypass bypass procedure"},
            {"hospital_id": hospitals[2].id, "name": "Sophia Martinez", "medical_record_number": "MRN-1004", "age": 35, "gender": "Female", "blood_group": "AB", "rh_factor": "-", "condition_summary": "Severe aplastic anemia red cell exchange protocol"}
        ]
        patients = [Patient(**p) for p in patients_data]
        session.add_all(patients)
        session.commit()
        for p in patients:
            session.refresh(p)
            
        print(f"Created {len(patients)} Patients.")

        # 4. Create Blood Inventory (All 8 blood groups for each hospital)
        blood_types = [
            ("A", "+"), ("A", "-"),
            ("B", "+"), ("B", "-"),
            ("AB", "+"), ("AB", "-"),
            ("O", "+"), ("O", "-")
        ]
        
        inventory_list = []
        for h in hospitals:
            for bg, rh in blood_types:
                available = random.randint(3, 25)
                # Intentionally create a couple low stock records for testing alerts
                if (bg, rh) in [("O", "-"), ("AB", "-")]:
                    available = random.randint(1, 4)
                inventory_list.append(BloodInventory(
                    hospital_id=h.id,
                    blood_group=bg,
                    rh_factor=rh,
                    available_units=available,
                    reserved_units=random.randint(0, 3),
                    minimum_threshold=5
                ))
                
        session.add_all(inventory_list)
        session.commit()
        print(f"Created {len(inventory_list)} Inventory records.")

        # 5. Create Donors
        donors_data = [
            {"name": "Alexander Wright", "email": "alex.wright@example.com", "phone": "+1-555-8001", "blood_group": "O", "rh_factor": "-", "age": 34, "gender": "Male", "latitude": 40.7200, "longitude": -74.0000, "is_available": True, "last_donation_date": date.today() - timedelta(days=90), "total_donations": 12},
            {"name": "Beatrice Vance", "email": "beatrice.vance@example.com", "phone": "+1-555-8002", "blood_group": "O", "rh_factor": "+", "age": 28, "gender": "Female", "latitude": 40.7150, "longitude": -74.0100, "is_available": True, "last_donation_date": date.today() - timedelta(days=65), "total_donations": 5},
            {"name": "Charles Lindqvist", "email": "charles.l@example.com", "phone": "+1-555-8003", "blood_group": "A", "rh_factor": "+", "age": 45, "gender": "Male", "latitude": 40.7320, "longitude": -73.9900, "is_available": True, "last_donation_date": date.today() - timedelta(days=120), "total_donations": 18},
            {"name": "Diana Prince", "email": "diana.prince@example.com", "phone": "+1-555-8004", "blood_group": "A", "rh_factor": "-", "age": 31, "gender": "Female", "latitude": 40.7400, "longitude": -73.9800, "is_available": True, "last_donation_date": date.today() - timedelta(days=70), "total_donations": 8},
            {"name": "Edward Norton", "email": "edward.n@example.com", "phone": "+1-555-8005", "blood_group": "B", "rh_factor": "+", "age": 52, "gender": "Male", "latitude": 40.7100, "longitude": -73.9500, "is_available": True, "last_donation_date": date.today() - timedelta(days=150), "total_donations": 22},
            {"name": "Fiona Gallagher", "email": "fiona.g@example.com", "phone": "+1-555-8006", "blood_group": "B", "rh_factor": "-", "age": 26, "gender": "Female", "latitude": 40.7250, "longitude": -73.9700, "is_available": True, "last_donation_date": date.today() - timedelta(days=85), "total_donations": 4},
            {"name": "George Miller", "email": "george.m@example.com", "phone": "+1-555-8007", "blood_group": "AB", "rh_factor": "+", "age": 39, "gender": "Male", "latitude": 40.7500, "longitude": -73.9600, "is_available": True, "last_donation_date": date.today() - timedelta(days=200), "total_donations": 14},
            {"name": "Hannah Abbott", "email": "hannah.a@example.com", "phone": "+1-555-8008", "blood_group": "AB", "rh_factor": "-", "age": 30, "gender": "Female", "latitude": 40.7300, "longitude": -74.0200, "is_available": True, "last_donation_date": date.today() - timedelta(days=110), "total_donations": 7},
            {"name": "Ian Malcolm", "email": "ian.m@example.com", "phone": "+1-555-8009", "blood_group": "O", "rh_factor": "-", "age": 48, "gender": "Male", "latitude": 40.7050, "longitude": -74.0050, "is_available": True, "last_donation_date": date.today() - timedelta(days=95), "total_donations": 19},
            {"name": "Julia Roberts", "email": "julia.r@example.com", "phone": "+1-555-8010", "blood_group": "A", "rh_factor": "+", "age": 24, "gender": "Female", "latitude": 40.7180, "longitude": -73.9850, "is_available": False, "last_donation_date": date.today() - timedelta(days=20), "total_donations": 2}
        ]

        donors = [Donor(**d) for d in donors_data]
        session.add_all(donors)
        session.commit()
        print(f"Created {len(donors)} Donors.")

        # 6. Create Initial Blood Requests
        requests_data = [
            {
                "hospital_id": hospitals[0].id,
                "patient_id": patients[0].id,
                "doctor_id": doctors[0].id,
                "blood_group": "O",
                "rh_factor": "-",
                "units_required": 4,
                "urgency": "Critical",
                "status": "Pending",
                "clinical_severity": 9.5
            },
            {
                "hospital_id": hospitals[0].id,
                "patient_id": patients[1].id,
                "doctor_id": doctors[1].id,
                "blood_group": "A",
                "rh_factor": "+",
                "units_required": 2,
                "urgency": "High",
                "status": "Pending",
                "clinical_severity": 7.8
            },
            {
                "hospital_id": hospitals[1].id,
                "patient_id": patients[2].id,
                "doctor_id": doctors[2].id,
                "blood_group": "B",
                "rh_factor": "+",
                "units_required": 3,
                "urgency": "Medium",
                "status": "Pending",
                "clinical_severity": 5.5
            }
        ]

        blood_requests = [BloodRequest(**r) for r in requests_data]
        session.add_all(blood_requests)
        session.commit()
        print(f"Created {len(blood_requests)} Blood Requests.")

        print("Database seed completed successfully!")
    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
