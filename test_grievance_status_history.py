#!/usr/bin/env python3
"""
Comprehensive test script for Grievance Status History and Deletion Removal features.
Tests both features end-to-end against the FastAPI app and PostgreSQL database.
"""

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure api directory is on sys.path
api_path = Path(__file__).resolve().parent / "api"
if str(api_path) not in sys.path:
    sys.path.insert(0, str(api_path))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import AdminSession, AdminUser, GrievanceStatusHistory, InteractionLog
from app.auth import COOKIE_NAME, token_hash

def run_tests():
    print("=" * 70)
    print("RUNNING GRIEVANCE STATUS HISTORY & DELETION REMOVAL TESTS")
    print("=" * 70)

    client = TestClient(app)

    # 1. Setup authenticated admin session
    print("\n[Setup] Preparing admin session...")
    with SessionLocal() as db:
        admin_user = db.get(AdminUser, 1)
        if not admin_user:
            admin_user = AdminUser(id=1, username="admin", passwordHash="dummy_test_hash")
            db.add(admin_user)
            db.commit()

        token = "test_audit_session_token_12345"
        thash = token_hash(token)
        existing_session = db.get(AdminSession, thash)
        if not existing_session:
            db.add(AdminSession(
                tokenHash=thash,
                adminId=1,
                expiresAt=datetime.now(timezone.utc).replace(year=2030),
            ))
            db.commit()

    admin_cookies = {COOKIE_NAME: token}
    print("   ✓ Admin session active for user 'admin'")

    test_complaint = f"TEST-CMP-{int(time.time())}"

    # TEST 1: Grievance registration creates initial history entry
    print("\n[Test 1] Testing initial grievance registration history...")
    reg_payload = {
        "complaintNumber": test_complaint,
        "employeeId": "EMP001",
        "employeeName": "Test Employee",
        "employeeDept": "Manufacturing",
        "queryText": "Air conditioning unit leaking near workstation 4.",
        "departmentCategory": "Facilities",
        "status": "Pending Review",
        "timestamp": int(time.time() * 1000),
    }
    res = client.post("/api/rest/interaction-logs", json=reg_payload)
    assert res.status_code == 201, f"Expected 201 Created, got {res.status_code}: {res.text}"
    grievance = res.json()
    grievance_id = grievance["id"]
    print(f"   ✓ Grievance registered successfully (ID: {grievance_id}, Complaint: {test_complaint})")

    # Verify history entry
    hist_res = client.get(f"/api/rest/interaction-logs/{grievance_id}/history", cookies=admin_cookies)
    assert hist_res.status_code == 200, f"Expected 200 OK, got {hist_res.status_code}: {hist_res.text}"
    history = hist_res.json()
    assert len(history) == 1, f"Expected exactly 1 history record, got {len(history)}"
    h0 = history[0]
    assert h0["grievance_id"] == grievance_id, f"Mismatched grievance_id: {h0['grievance_id']}"
    assert h0["previous_status"] is None, f"Expected None previous_status for registration, got {h0['previous_status']}"
    assert h0["new_status"] == "Pending Review", f"Expected 'Pending Review', got {h0['new_status']}"
    assert h0["changed_by"] == "system", f"Expected 'system', got {h0['changed_by']}"
    assert h0["remarks"] == "Initial registration", f"Unexpected remarks: {h0['remarks']}"
    assert h0["changed_at"] is not None, "changed_at timestamp must be present"
    print("   ✓ Initial registration history record verified successfully")

    # TEST 2: Status update transition creates subsequent history entry
    print("\n[Test 2] Testing status update: Pending Review -> In Progress...")
    update_payload = {
        "status": "In Progress",
        "remarks": "Assigned to facilities engineer for inspection."
    }
    update_res = client.put(f"/api/rest/interaction-logs/{grievance_id}", json=update_payload, cookies=admin_cookies)
    assert update_res.status_code == 200, f"Expected 200 OK, got {update_res.status_code}: {update_res.text}"
    assert update_res.json()["status"] == "In Progress", "Status not updated in grievance"

    hist_res2 = client.get(f"/api/rest/interaction-logs/{grievance_id}/history", cookies=admin_cookies)
    assert hist_res2.status_code == 200
    history2 = hist_res2.json()
    assert len(history2) == 2, f"Expected 2 history records, got {len(history2)}"

    h1 = history2[1]
    assert h1["grievance_id"] == grievance_id
    assert h1["previous_status"] == "Pending Review", f"Expected 'Pending Review', got {h1['previous_status']}"
    assert h1["new_status"] == "In Progress", f"Expected 'In Progress', got {h1['new_status']}"
    assert h1["changed_by"] == "admin", f"Expected authenticated 'admin', got {h1['changed_by']}"
    assert h1["remarks"] == "Assigned to facilities engineer for inspection.", f"Unexpected remarks: {h1['remarks']}"
    print("   ✓ Transition to 'In Progress' with authenticated user and remarks verified")

    # TEST 3: Duplicate/unchanged status does NOT create redundant history entry
    print("\n[Test 3] Testing that unchanged status does not create duplicate history...")
    noop_payload = {
        "status": "In Progress",
        "remarks": "Redundant update with same status."
    }
    noop_res = client.put(f"/api/rest/interaction-logs/{grievance_id}", json=noop_payload, cookies=admin_cookies)
    assert noop_res.status_code == 200

    hist_res3 = client.get(f"/api/rest/interaction-logs/{grievance_id}/history", cookies=admin_cookies)
    history3 = hist_res3.json()
    assert len(history3) == 2, f"Duplicate history record was created! Expected 2, got {len(history3)}"
    print("   ✓ Unchanged status correctly ignored, no duplicate entry created")

    # TEST 4: Second status change: In Progress -> Resolved
    print("\n[Test 4] Testing second transition: In Progress -> Resolved...")
    resolve_payload = {
        "status": "Resolved",
        "remarks": "Leak repaired, filter replaced, work confirmed."
    }
    res_resolve = client.put(f"/api/rest/interaction-logs/{grievance_id}", json=resolve_payload, cookies=admin_cookies)
    assert res_resolve.status_code == 200

    hist_res4 = client.get(f"/api/rest/interaction-logs/{grievance_id}/history", cookies=admin_cookies)
    history4 = hist_res4.json()
    assert len(history4) == 3, f"Expected 3 history records, got {len(history4)}"

    # Check chronological ordering
    h2 = history4[2]
    assert h2["previous_status"] == "In Progress"
    assert h2["new_status"] == "Resolved"
    assert h2["changed_by"] == "admin"
    assert h2["remarks"] == "Leak repaired, filter replaced, work confirmed."

    timestamps = [h["changed_at"] for h in history4]
    assert timestamps == sorted(timestamps), "History records are not in chronological order!"
    print(f"   ✓ Complete lifecycle history verified in chronological order (3 events)")

    # TEST 5: Authentication & Authorization on history endpoint
    print("\n[Test 5] Testing history endpoint authorization...")
    unauth_res = client.get(f"/api/rest/interaction-logs/{grievance_id}/history")
    assert unauth_res.status_code == 401, f"Expected 401 Unauthorized without session, got {unauth_res.status_code}"
    print("   ✓ Unauthenticated access correctly rejected with 401")

    notfound_res = client.get("/api/rest/interaction-logs/99999999/history", cookies=admin_cookies)
    assert notfound_res.status_code == 404, f"Expected 404 for non-existent log, got {notfound_res.status_code}"
    print("   ✓ Non-existent grievance history correctly returns 404")

    # TEST 6: Grievance Deletion is permanently disabled
    print("\n[Test 6] Testing grievance deletion removal...")
    # Attempt DELETE /interaction-logs/{id}
    del_res = client.delete(f"/api/rest/interaction-logs/{grievance_id}", cookies=admin_cookies)
    assert del_res.status_code == 405, f"Expected 405 Method Not Allowed, got {del_res.status_code}: {del_res.text}"
    print("   ✓ DELETE /api/rest/interaction-logs/{id} correctly rejected with 405 Method Not Allowed")

    # Attempt POST /delete-bulk
    bulk_del_res = client.post("/api/rest/interaction-logs/delete-bulk", json=[test_complaint], cookies=admin_cookies)
    assert bulk_del_res.status_code == 405, f"Expected 405 Method Not Allowed, got {bulk_del_res.status_code}: {bulk_del_res.text}"
    print("   ✓ POST /api/rest/interaction-logs/delete-bulk correctly rejected with 405 Method Not Allowed")

    # Verify grievance is still intact in database
    verify_res = client.get(f"/api/rest/interaction-logs/{grievance_id}", cookies=admin_cookies)
    assert verify_res.status_code == 200, "Grievance was deleted or missing!"
    assert verify_res.json()["complaintNumber"] == test_complaint
    print("   ✓ Grievance verified intact in database after failed deletion attempts")

    # TEST 7: Android sync / bulk upsert workflow
    print("\n[Test 7] Testing Android sync / bulk upsert status history...")
    sync_complaint = f"SYNC-CMP-{int(time.time())}"
    sync_payload = [{
        "complaintNumber": sync_complaint,
        "employeeId": "EMP002",
        "employeeName": "Sync Tester",
        "employeeDept": "Assembly",
        "queryText": "Safety gloves restock requested at station 2.",
        "departmentCategory": "General Feedback",
        "status": "Pending Review",
        "timestamp": int(time.time() * 1000),
    }]
    sync_res = client.post("/api/rest/interaction-logs/upsert", json=sync_payload)
    assert sync_res.status_code == 200, f"Expected 200, got {sync_res.status_code}: {sync_res.text}"
    sync_item = sync_res.json()[0]
    sync_id = sync_item["id"]

    sync_hist = client.get(f"/api/rest/interaction-logs/{sync_id}/history", cookies=admin_cookies).json()
    assert len(sync_hist) == 1, f"Expected 1 history item for sync registration, got {len(sync_hist)}"
    assert sync_hist[0]["changed_by"] == "device_sync"
    assert sync_hist[0]["new_status"] == "Pending Review"
    print(f"   ✓ Device sync registration created history with changed_by='device_sync'")

    # TEST 8: Full sync snapshot endpoint works without regression
    print("\n[Test 8] Testing /api/rest/sync snapshot...")
    full_sync = client.get("/api/rest/sync")
    assert full_sync.status_code == 200, f"Sync endpoint failed: {full_sync.status_code}"
    sync_data = full_sync.json()
    assert "interaction_logs" in sync_data, "Sync snapshot missing interaction_logs"
    assert "employees" in sync_data, "Sync snapshot missing employees"
    print(f"   ✓ Full sync endpoint returned {len(sync_data['interaction_logs'])} interaction logs successfully")

    print("\n" + "=" * 70)
    print("ALL 8 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
