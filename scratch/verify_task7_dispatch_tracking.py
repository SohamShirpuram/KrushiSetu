"""
Verification and Test Suite for Task 7:
Major Warehouse -> Minor Warehouse Dispatch, Truck Tracking & Minor Warehouse Receiving
"""

import sys
from datetime import datetime
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.connection import SessionLocal
from backend.models.user import User, UserRole
from backend.models.records_warehouse import MajorWarehouseIntake, MajorWarehouseStorage, MajorWarehouseDispatch, TruckRegistry
from backend.models.records_minor_warehouse import MinorWarehouseInward, MinorWarehouseStock
from backend.models.audit import AuditLog
from backend.services.auth_service import create_access_token

client = TestClient(app)

def print_header(title):
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)

def test_task7_complete_suite():
    db = SessionLocal()
    try:
        print_header("TASK 7: MAJOR WAREHOUSE DISPATCH, GPS TRACKING & MINOR WH RECEIVING TEST SUITE")

        # 0. Setup Auth Tokens
        major_wh_user = db.query(User).filter(User.role == UserRole.MAJOR_WAREHOUSE).first()
        if not major_wh_user:
            major_wh_user = User(
                username="mwh_supervisor_test",
                email="mwh_test@krushisetu.in",
                hashed_password="hashed_test_pass",
                role=UserRole.MAJOR_WAREHOUSE,
                full_name="Major Warehouse Supervisor",
                is_active=True
            )
            db.add(major_wh_user)
            db.commit()
            db.refresh(major_wh_user)

        minor_wh_user = db.query(User).filter(User.role == UserRole.MINOR_WAREHOUSE).first()
        if not minor_wh_user:
            minor_wh_user = User(
                username="minor_wh_manager_test",
                email="minor_test@krushisetu.in",
                hashed_password="hashed_test_pass",
                role=UserRole.MINOR_WAREHOUSE,
                full_name="Minor Warehouse Manager",
                is_active=True
            )
            db.add(minor_wh_user)
            db.commit()
            db.refresh(minor_wh_user)

        mwh_token = create_access_token({"sub": major_wh_user.username, "role": major_wh_user.role.value})
        min_token = create_access_token({"sub": minor_wh_user.username, "role": minor_wh_user.role.value})
        mwh_headers = {"Authorization": f"Bearer {mwh_token}"}
        min_headers = {"Authorization": f"Bearer {min_token}"}

        # 1. Verify / Setup Test Batch in Intake and Storage
        test_batch_id = "KS-BATCH-TASK7-01"
        intake = db.query(MajorWarehouseIntake).filter(MajorWarehouseIntake.batch_id == test_batch_id).first()
        if not intake:
            intake = MajorWarehouseIntake(
                batch_id=test_batch_id,
                farmer_id="KS-FMR-1001",
                farmer_name="Ramesh Narayan Patil",
                crop_name="Wheat (Lokwan)",
                gross_weight_kg=15000.0,
                tare_weight_kg=5000.0,
                net_weight_kg=10000.0,
                ai_predicted_score=94.5,
                ai_predicted_grade="A",
                human_final_score=95.0,
                human_final_grade="A",
                review_status="CONFIRMED",
                reviewed_by="inspector_mwh",
                storage_silo_bay="SILO-BAY-A1",
                intake_status="STORED"
            )
            db.add(intake)
            db.commit()

        storage = db.query(MajorWarehouseStorage).filter(MajorWarehouseStorage.batch_id == test_batch_id).first()
        if not storage:
            storage = MajorWarehouseStorage(
                storage_id="STR-TASK7-01",
                batch_id=test_batch_id,
                warehouse_id="MWH-PUN-01",
                warehouse_name="Pune Central Major Silo Hub",
                farmer_id="KS-FMR-1001",
                farmer_name="Ramesh Narayan Patil",
                crop_name="Wheat (Lokwan)",
                crop_category="Grains",
                quantity_kg=10000.0,
                current_stock_kg=10000.0,
                reserved_quantity_kg=0.0,
                dispatched_quantity_kg=0.0,
                storage_location="SILO-BAY-A1",
                storage_type="Silo Storage",
                storage_date=datetime.utcnow().strftime("%Y-%m-%d"),
                status="Stored"
            )
            db.add(storage)
            db.commit()
            db.refresh(storage)
        else:
            storage.current_stock_kg = 10000.0
            storage.dispatched_quantity_kg = 0.0
            storage.status = "Stored"
            db.commit()
            db.refresh(storage)

        print("[OK] Test Batch and Storage established: Batch KS-BATCH-TASK7-01 (10,000 kg Wheat, Certified Grade A)")

        # 2. Test Fleet Trucks Registry
        print("\n--- TEST 1: Transport Fleet & Trucks Registry ---")
        res = client.get("/api/v1/warehouse/trucks", headers=mwh_headers)
        assert res.status_code == 200, f"Failed to get trucks: {res.text}"
        trucks = res.json()
        print(f"[PASS] Trucks list returned {len(trucks)} fleet vehicles.")
        assert len(trucks) >= 1, "Expected at least 1 registered truck"

        # Register a new truck if not present
        truck_res = client.post("/api/v1/warehouse/trucks", json={
            "truck_id": "TRK-004",
            "vehicle_number": "MH-12-PQ-9988",
            "vehicle_type": "16-Wheeler Heavy Grain Carrier",
            "capacity_mt": 30.0,
            "driver_name": "Deepak Shinde",
            "driver_phone": "+91 98220 99887",
            "driver_id": "DRV-004",
            "current_status": "AVAILABLE",
            "origin_base": "Pune Central Major Silo Hub"
        }, headers=mwh_headers)
        if truck_res.status_code == 200:
            print("[PASS] New truck TRK-004 registered successfully.")
        else:
            assert "already registered" in truck_res.text or truck_res.status_code == 400
            print("[PASS] Truck TRK-004 verified in registry.")

        # 3. Test Strict Inventory Conservation (Disallow excess dispatch)
        print("\n--- TEST 2: Inventory Conservation & Excess Dispatch Prevention ---")
        excess_res = client.post("/api/v1/warehouse/dispatch", json={
            "batch_id": test_batch_id,
            "crop_name": "Wheat (Lokwan)",
            "dispatch_quantity_kg": 25000.0, # Available is only 10,000 kg
            "destination_minor_warehouse": "Baramati APMC Transit Godown No. 3",
            "truck_number": "MH-12-Q-4521",
            "driver_name": "Ramesh Patil"
        }, headers=mwh_headers)
        assert excess_res.status_code == 400, f"Expected 400 for excess dispatch, got: {excess_res.status_code}"
        assert "Only" in excess_res.json()["detail"] and "available" in excess_res.json()["detail"]
        print(f"[PASS] Excess dispatch strictly blocked: {excess_res.json()['detail']}")

        # 4. Test Valid Dispatch Creation & Inventory Deduction
        print("\n--- TEST 3: Create Valid Dispatch with Immutable Batch Linkage ---")
        disp_res = client.post("/api/v1/warehouse/dispatch", json={
            "batch_id": test_batch_id,
            "crop_name": "Wheat (Lokwan)",
            "final_grade": "A",
            "dispatch_quantity_kg": 6000.0,
            "origin_warehouse": "Pune Central Silo Hub",
            "origin_warehouse_id": "MWH-PUN-01",
            "destination_minor_warehouse": "Baramati APMC Transit Godown No. 3",
            "destination_minor_warehouse_id": "MIN-BMT-01",
            "truck_id": "TRK-001",
            "truck_number": "MH-12-Q-4521",
            "driver_id": "DRV-001",
            "driver_name": "Ramesh Patil",
            "driver_phone": "+91 98220 11223",
            "departure_time": "10:00 AM",
            "expected_arrival": "02:00 PM",
            "notes": "Transfer of Grade A Lokwan wheat for sub-district buffer"
        }, headers=mwh_headers)
        assert disp_res.status_code == 200, f"Failed to create dispatch: {disp_res.text}"
        disp1 = disp_res.json()
        disp_id1 = disp1["dispatch_id"]
        print(f"[PASS] Created Dispatch {disp_id1} for 6,000 kg Wheat (Grade {disp1['final_grade']}).")
        assert disp1["batch_id"] == test_batch_id
        assert disp1["final_grade"] == "A"
        assert disp1["status"] == "Pending Departure"
        assert disp1["is_gps_active"] is False

        # Verify storage stock deduction
        db.refresh(storage)
        assert storage.dispatched_quantity_kg == 6000.0
        assert storage.current_stock_kg == 4000.0
        assert storage.available_quantity_kg == 4000.0
        assert storage.status == "Partially Dispatched"
        print(f"[PASS] Major Warehouse Storage decremented: Current Stock = {storage.current_stock_kg} kg, Available = {storage.available_quantity_kg} kg.")

        # 5. Test Start Transit & GPS Activation
        print("\n--- TEST 4: Start Delivery Transit & Activate GPS Tracking ---")
        start_res = client.post(f"/api/v1/warehouse/dispatch/{disp_id1}/start-transit", json={
            "departure_time": "10:15 AM",
            "notes": "Vehicle cleared security gate and left Pune Hub"
        }, headers=mwh_headers)
        assert start_res.status_code == 200, f"Failed to start transit: {start_res.text}"
        started_disp = start_res.json()
        assert started_disp["status"] == "In Transit"
        assert started_disp["is_gps_active"] is True
        print(f"[PASS] Dispatch {disp_id1} transitioned to 'In Transit'. Live GPS tracking is ACTIVE.")

        # Verify truck in registry is marked IN_TRANSIT
        truck_rec = db.query(TruckRegistry).filter(TruckRegistry.truck_id == "TRK-001").first()
        assert truck_rec.current_status == "IN_TRANSIT"
        assert truck_rec.current_dispatch_id == disp_id1
        print(f"[PASS] Truck TRK-001 registry status updated to IN_TRANSIT on dispatch {disp_id1}.")

        # 6. Test Live GPS Telemetry Update & Google Maps Deep Link
        print("\n--- TEST 5: Real-time GPS Location Broadcast & Google Maps Link ---")
        gps_lat, gps_lng = 18.4385, 74.4172
        gps_loc = "Near Patas Toll Plaza, Solapur Expressway (Km 62)"
        gps_res = client.post(f"/api/v1/warehouse/dispatch/{disp_id1}/gps-location", json={
            "latitude": gps_lat,
            "longitude": gps_lng,
            "location_name": gps_loc
        }, headers=mwh_headers)
        assert gps_res.status_code == 200, f"GPS update failed: {gps_res.text}"
        gps_data = gps_res.json()
        assert gps_data["latitude"] == gps_lat
        assert gps_data["longitude"] == gps_lng
        assert gps_data["current_location"] == gps_loc
        assert "google_maps_url" in gps_data
        print(f"[PASS] GPS coordinate update successful: ({gps_lat}, {gps_lng}) at '{gps_loc}'.")
        print(f"[PASS] Google Maps Deep Link: {gps_data['google_maps_url']}")

        # Query tracking endpoint
        track_res = client.get(f"/api/v1/warehouse/dispatch/{disp_id1}/tracking", headers=mwh_headers)
        assert track_res.status_code == 200
        track_data = track_res.json()
        assert track_data["is_gps_active"] is True
        assert track_data["final_grade"] == "A"
        assert track_data["sent_quantity_kg"] == 6000.0
        print("[PASS] GET /tracking returned complete telemetry with certified Grade A and live coordinates.")

        # 7. Test Minor Warehouse Receiving with Weight Discrepancy
        print("\n--- TEST 6: Minor Warehouse Receiving & Discrepancy Reconciliation ---")
        # Sent: 6000 kg, Received: 5940 kg -> 60 kg difference
        rec_res = client.post(f"/api/v1/warehouse/dispatch/{disp_id1}/receive", json={
            "received_quantity_kg": 5940.0,
            "arrival_time": "02:15 PM",
            "discrepancy_reason": "Transit moisture evaporation and weighbridge tolerance difference of 60 kg",
            "receiver_name": "Prakash Kadam (Minor Godown Incharge)"
        }, headers=min_headers)
        assert rec_res.status_code == 200, f"Receiving failed: {rec_res.text}"
        rec_data = rec_res.json()
        assert rec_data["has_discrepancy"] is True
        assert rec_data["difference_kg"] == 60.0
        assert rec_data["status"] == "Discrepancy"
        print(f"[PASS] Received 5,940 kg against 6,000 kg sent. Difference = {rec_data['difference_kg']} kg. Status = {rec_data['status']}.")

        # Verify Major Warehouse sent quantity record is preserved untouched
        db.expire_all()
        dispatch_in_db = db.query(MajorWarehouseDispatch).filter(MajorWarehouseDispatch.dispatch_id == disp_id1).first()
        assert dispatch_in_db.dispatch_quantity_kg == 6000.0, "Major WH sent quantity was modified!"
        assert dispatch_in_db.status == "Discrepancy"
        assert dispatch_in_db.is_gps_active is False, "GPS should be disabled on delivery completion"
        print("[PASS] Major Warehouse sent quantity preserved UNTOUCHED (6,000 kg). GPS deactivated.")

        # Verify Minor Warehouse Inward & Stock
        inward = db.query(MinorWarehouseInward).filter(MinorWarehouseInward.dispatch_id == disp_id1).first()
        assert inward is not None
        assert inward.sent_quantity_kg == 6000.0
        assert inward.received_quantity_kg == 5940.0
        assert inward.difference_kg == 60.0
        assert inward.verification_status == "WEIGHT_MISMATCH"
        print("[PASS] Inward record logged in minor_wh_inward_records with WEIGHT_MISMATCH.")

        min_stock = db.query(MinorWarehouseStock).filter(MinorWarehouseStock.batch_id == test_batch_id).first()
        assert min_stock is not None
        assert min_stock.current_stock_kg >= 5940.0
        print(f"[PASS] Minor Godown inventory credited with received weight: {min_stock.current_stock_kg} kg.")

        # Verify Truck released to AVAILABLE
        truck_rec = db.query(TruckRegistry).filter(TruckRegistry.truck_id == "TRK-001").first()
        assert truck_rec.current_status == "AVAILABLE"
        assert truck_rec.current_dispatch_id is None
        print("[PASS] Carrier Truck TRK-001 automatically released to AVAILABLE.")

        # 8. Test GPS Privacy Enforcement (Blocked after duty completion)
        print("\n--- TEST 7: GPS Privacy Shield Enforcement ---")
        post_gps_res = client.post(f"/api/v1/warehouse/dispatch/{disp_id1}/gps-location", json={
            "latitude": 18.5000,
            "longitude": 73.8000,
            "location_name": "After Duty Private Location"
        }, headers=mwh_headers)
        assert post_gps_res.status_code == 400, f"Expected 400 for post-duty GPS, got: {post_gps_res.status_code}"
        assert "inactive" in post_gps_res.json()["detail"].lower() or "not currently" in post_gps_res.json()["detail"].lower()
        print(f"[PASS] Post-duty GPS transmission blocked: {post_gps_res.json()['detail']}")

        # 9. Test Exact Match Receiving (No Discrepancy -> Completed)
        print("\n--- TEST 8: Exact Weight Match Dispatch & Verification ---")
        # Create second dispatch for 3000 kg
        disp_res2 = client.post("/api/v1/warehouse/dispatch", json={
            "batch_id": test_batch_id,
            "crop_name": "Wheat (Lokwan)",
            "dispatch_quantity_kg": 3000.0,
            "destination_minor_warehouse": "Indapur Sub-District Godown",
            "truck_id": "TRK-002",
            "truck_number": "MH-12-TR-7788",
            "driver_name": "Suresh Kale",
            "departure_time": "11:00 AM",
            "expected_arrival": "03:00 PM"
        }, headers=mwh_headers)
        assert disp_res2.status_code == 200
        disp2 = disp_res2.json()
        disp_id2 = disp2["dispatch_id"]

        client.post(f"/api/v1/warehouse/dispatch/{disp_id2}/start-transit", headers=mwh_headers)

        # Receive with exact 3000 kg
        rec_res2 = client.post(f"/api/v1/warehouse/dispatch/{disp_id2}/receive", json={
            "received_quantity_kg": 3000.0,
            "arrival_time": "03:10 PM",
            "discrepancy_reason": "Exact Match verified on calibrated weighbridge",
            "receiver_name": "Anil Deshmukh"
        }, headers=min_headers)
        assert rec_res2.status_code == 200
        rec_data2 = rec_res2.json()
        assert rec_data2["has_discrepancy"] is False
        assert rec_data2["difference_kg"] == 0.0
        assert rec_data2["status"] == "Completed"
        print(f"[PASS] Exact match receipt verified: Status = {rec_data2['status']}, Difference = 0 kg.")

        # 10. Test Audit Logs
        print("\n--- TEST 9: Comprehensive Audit Trail Verification ---")
        audit_logs = db.query(AuditLog).filter(
            AuditLog.table_name.in_(["major_warehouse_dispatches", "minor_wh_inward_records"])
        ).all()
        print(f"[PASS] Verified {len(audit_logs)} audit records captured across dispatch and receiving events.")
        assert len(audit_logs) >= 4, "Expected multiple audit entries for dispatch and inward receipts."

        print_header("ALL TASK 7 VERIFICATION TESTS PASSED (100% GREEN)")

    finally:
        db.close()

if __name__ == "__main__":
    test_task7_complete_suite()

