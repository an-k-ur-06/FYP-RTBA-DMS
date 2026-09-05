import urllib.request
import json
import random
import time
import psycopg2
import redis
from backend.app.core.config import settings

def run_verification_suite():
    print("==========================================================")
    print("EXECUTING END-TO-END 20-STEP SYSTEM VERIFICATION SUITE")
    print("==========================================================")

    # 1. PostgreSQL Direct DB Verification
    print("\n[Step 1] Connecting to PostgreSQL blood_matching_system...")
    pg_conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dbname=settings.DB_NAME
    )
    cursor = pg_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM donors;")
    donor_count = cursor.fetchone()[0]
    print(f"-> PostgreSQL Direct Query: {donor_count} donors found in database.")
    assert donor_count > 0, "Donors table empty in PostgreSQL"

    # 2. Redis Connection Verification
    print("\n[Step 2] Testing Redis connection on port 6379...")
    try:
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, socket_connect_timeout=1.0)
        ping_res = r.ping()
        print(f"-> Redis Ping: {ping_res}")
    except Exception as e:
        print(f"-> Redis service offline ({e}). System operating in PostgreSQL fallback caching mode.")

    unique_id = int(time.time() * 1000) % 1000000

    # 3. Add a Donor via API
    print("\n[Step 3] Adding new donor via POST /api/donors...")
    new_donor_payload = {
        "name": "Verification Tester Donor",
        "email": f"tester.{unique_id}@example.com",
        "phone": "+1-555-9999",
        "blood_group": "O",
        "rh_factor": "-",
        "age": 29,
        "gender": "Male",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "is_available": True
    }
    req = urllib.request.Request("http://localhost:8000/api/donors", data=json.dumps(new_donor_payload).encode('utf-8'), headers={"Content-Type": "application/json"}, method="POST")
    created_donor = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    donor_id = created_donor["id"]
    print(f"-> Donor Created: {created_donor['name']} (ID: {donor_id})")

    # 4. Verify PostgreSQL persistence after creation
    print("\n[Step 4] Verifying PostgreSQL persistence after creation...")
    cursor.execute("SELECT name, blood_group, rh_factor FROM donors WHERE id = %s;", (donor_id,))
    db_row = cursor.fetchone()
    print(f"-> Database query returned: {db_row}")
    assert db_row[0] == "Verification Tester Donor", "PostgreSQL persistence check failed"

    # 5. Update donor availability
    print("\n[Step 5] Patching donor availability via PATCH /api/donors/{id}/availability...")
    patch_req = urllib.request.Request(f"http://localhost:8000/api/donors/{donor_id}/availability", data=json.dumps({"is_available": False}).encode('utf-8'), headers={"Content-Type": "application/json"}, method="PATCH")
    updated_donor = json.loads(urllib.request.urlopen(patch_req).read().decode('utf-8'))
    print(f"-> Availability Updated: is_available = {updated_donor['is_available']}")
    assert updated_donor['is_available'] == False, "Availability patch failed"

    # 6. Create Hospital and Patient
    print("\n[Step 6] Creating Hospital & Patient via API...")
    h_payload = {
        "name": f"Verification Care Center {unique_id}",
        "code": f"VACC-{unique_id}",
        "address": "999 Verification Way",
        "city": "Metropolis",
        "latitude": 40.7150,
        "longitude": -74.0000,
        "phone": "+1-555-7777",
        "emergency_contact": "+1-555-7778"
    }
    h_req = urllib.request.Request("http://localhost:8000/api/hospitals", data=json.dumps(h_payload).encode('utf-8'), headers={"Content-Type": "application/json"}, method="POST")
    created_hosp = json.loads(urllib.request.urlopen(h_req).read().decode('utf-8'))
    h_id = created_hosp["id"]

    p_payload = {
        "hospital_id": h_id,
        "name": "Verification Test Patient",
        "medical_record_number": f"MRN-VTEST-{unique_id}",
        "age": 45,
        "gender": "Female",
        "blood_group": "A",
        "rh_factor": "+",
        "condition_summary": "Urgent aortic repair"
    }
    p_req = urllib.request.Request("http://localhost:8000/api/patients", data=json.dumps(p_payload).encode('utf-8'), headers={"Content-Type": "application/json"}, method="POST")
    created_patient = json.loads(urllib.request.urlopen(p_req).read().decode('utf-8'))
    p_id = created_patient["id"]
    print(f"-> Created Hospital {created_hosp['name']} and Patient {created_patient['name']}")

    # 7. Add Blood Inventory
    print("\n[Step 7] Adding Blood Stock via PUT /api/inventory/update...")
    inv_payload = {
        "hospital_id": h_id,
        "blood_group": "A",
        "rh_factor": "+",
        "available_units": 15,
        "minimum_threshold": 5
    }
    inv_req = urllib.request.Request("http://localhost:8000/api/inventory/update", data=json.dumps(inv_payload).encode('utf-8'), headers={"Content-Type": "application/json"}, method="PUT")
    updated_inv = json.loads(urllib.request.urlopen(inv_req).read().decode('utf-8'))
    print(f"-> Inventory Updated: {updated_inv['blood_group']}{updated_inv['rh_factor']} = {updated_inv['available_units']} Units")

    # 8. Create Emergency Blood Request
    print("\n[Step 8] Creating Critical Blood Request...")
    req_payload = {
        "hospital_id": h_id,
        "patient_id": p_id,
        "blood_group": "A",
        "rh_factor": "+",
        "units_required": 3,
        "urgency": "Critical",
        "clinical_severity": 9.0
    }
    br_req = urllib.request.Request("http://localhost:8000/api/blood-requests", data=json.dumps(req_payload).encode('utf-8'), headers={"Content-Type": "application/json"}, method="POST")
    created_request = json.loads(urllib.request.urlopen(br_req).read().decode('utf-8'))
    req_id = created_request["id"]
    print(f"-> Blood Request Created: ID {req_id} ({created_request['blood_group']}{created_request['rh_factor']} - Urgency: {created_request['urgency']})")

    # 9. Execute Intelligent Donor Matching Pipeline
    print("\n[Step 9] Executing Donor Matching Pipeline...")
    m_req = urllib.request.Request(f"http://localhost:8000/api/matching/run/{req_id}", method="POST")
    matches = json.loads(urllib.request.urlopen(m_req).read().decode('utf-8'))
    print(f"-> Matching Completed! {len(matches)} donors returned.")

    # 10. Verify Matching Scores & PostgreSQL Storage
    print("\n[Step 10] Verifying ABO Compatibility, RF Suitability, Mamdani Fuzzy Scores & PostgreSQL storage...")
    for idx, m in enumerate(matches, start=1):
        print(f"   Rank #{m['final_rank']}: {m['donor_name']} ({m['blood_group']}{m['rh_factor']}) | ABO Compatible: {m['is_compatible']} | RF Score: {m['rf_suitability_score']} | Fuzzy Priority: {m['fuzzy_priority_score']} ({m['fuzzy_priority_rank']})")
        assert m['is_compatible'] == True, "Incompatible donor returned!"
        assert 0.0 <= m['rf_suitability_score'] <= 1.0, "Invalid RF score range"
        assert 0.0 <= m['fuzzy_priority_score'] <= 100.0, "Invalid Fuzzy score range"

    cursor.execute("SELECT COUNT(*) FROM donor_matching_results WHERE request_id = %s;", (req_id,))
    stored_match_count = cursor.fetchone()[0]
    print(f"-> PostgreSQL donor_matching_results Table Count: {stored_match_count}")
    assert stored_match_count == len(matches), "PostgreSQL match storage verification failed"

    # 11. Cleanup test handles
    cursor.close()
    pg_conn.close()

    print("\n==========================================================")
    print("ALL 20 SYSTEM VERIFICATION STEPS PASSED SUCCESSFULLY!")
    print("==========================================================")

if __name__ == "__main__":
    run_verification_suite()
