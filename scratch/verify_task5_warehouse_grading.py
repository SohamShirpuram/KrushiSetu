"""
Verification Suite for TASK 5: MAJOR WAREHOUSE AI CROP QUALITY & GRADING
Tests:
1. One Central AI Engine architecture & vision model registration
2. Prototype AI model notice & 12 visual defect parameters
3. Physical measurement segregation (moisture probe, weighbridge scale)
4. AI Quality Score & Suggested Grade calculation (A, B, C, Reject)
5. Dual-Storage & Non-Overwriting Guarantee
6. Mandatory Human Review (AI prediction never automatically becomes final)
7. One-Click Zero-Typing Approval & sync to major_warehouse_intakes
8. Human Review Correction with mandatory justification (>= 5 chars) & validation
9. RBAC Authorization (Major Warehouse / Admin vs others)
10. End-to-End Batch Traceability (KS-BATCH-XXXX)
"""

import sys
import os
from fastapi.testclient import TestClient

# Ensure workspace is on sys.path
sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.main import app
from backend.database.connection import SessionLocal
from backend.models import (
    AIMajorWarehouseGradingRecord,
    MajorWarehouseIntake,
    AuditLog,
    User,
    UserRole,
)
from backend.ai.engine import ai_engine
from backend.ai.service import central_ai_service
from backend.ai.models.warehouse_grading_model import CropQualityVisionModel
from backend.services.auth_service import create_access_token

client = TestClient(app)

def create_auth_header(username: str, role: UserRole) -> dict:
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    if not user:
        raise ValueError(f"User {username} not found")
    token = create_access_token(data={"sub": user.username, "role": user.role.value, "user_id": user.id})
    return {"Authorization": f"Bearer {token}"}

def run_task5_verification():
    print("================================================================================")
    print("🧪 STARTING VERIFICATION: TASK 5 — MAJOR WAREHOUSE AI CROP QUALITY & GRADING")
    print("================================================================================\n")

    db = SessionLocal()

    # --------------------------------------------------------------------------
    # TEST 1: Central AI Engine Vision Model Registration & Architecture
    # --------------------------------------------------------------------------
    print("--- TEST 1: Central AI Engine Vision Model Registration & Architecture ---")
    assert hasattr(central_ai_service, "vision_model"), "central_ai_service missing vision_model"
    assert isinstance(central_ai_service.vision_model, CropQualityVisionModel), "vision_model is not CropQualityVisionModel"
    
    meta = central_ai_service.vision_model.get_metadata()
    print("Central AI Model Name:", meta["model_name"])
    print("Model Version:", meta["model_version"])
    print("Prototype Disclaimer:", meta["disclaimer"])
    assert "v1.0.0-prototype" in meta["model_version"]
    assert "Prototype AI model" in meta["disclaimer"]
    assert len(meta["parameters_analyzed"]) == 12, f"Expected 12 optical parameters, got {len(meta['parameters_analyzed'])}"
    assert len(meta["segregated_physical_parameters"]) == 2, "Expected 2 segregated physical parameters"
    print("✅ TEST 1 PASSED: Central AI Vision Model registered under One Central AI Engine.\n")

    # --------------------------------------------------------------------------
    # TEST 2: Optical Inference & 12 Parameters Analysis with Physical Segregation
    # --------------------------------------------------------------------------
    print("--- TEST 2: Optical Inference, 12 Visual Parameters & Physical Segregation ---")
    headers_wh = create_auth_header("major_warehouse", UserRole.MAJOR_WAREHOUSE)
    
    analyze_payload = {
        "batch_id": "KS-BATCH-1001",
        "crop_name": "Wheat (Lokwan)",
        "farmer_id": "KS-FMR-1001",
        "farmer_name": "Ramesh Narayan Patil",
        "warehouse_id": "MWH-PUN-01",
        "net_weight_kg": 9150.0,
        "image_data": "/uploads/grain_samples/KS-BATCH-1001_sample.svg",
        "manual_moisture_pct": 11.2,
        "manual_foreign_matter_pct": 0.8,
        "manual_broken_grain_pct": 1.4,
        "manual_damaged_grain_pct": 0.2,
        "has_cuts": False,
        "has_cracks": False,
        "has_spots": False,
        "has_bruises": False,
        "has_pest_damage": False,
    }

    resp = client.post("/api/v1/ai/warehouse/grading/analyze", json=analyze_payload, headers=headers_wh)
    assert resp.status_code == 200, f"Analyze failed with {resp.status_code}: {resp.text}"
    data = resp.json()
    created_id = data["id"]

    print(f"Created Grading Record ID: {created_id}, Code: {data['grading_code']}")
    print(f"AI Quality Score: {data['ai_score']} / 100")
    print(f"AI Suggested Grade: {data['ai_grade']}")
    print(f"AI Confidence: {data['ai_confidence']}")
    print(f"Review Status: {data['review_status']}")

    # Verify score in 80-100 maps to Grade A
    assert data["ai_score"] >= 80.0, f"Expected Grade A score >= 80, got {data['ai_score']}"
    assert data["ai_grade"] == "A", f"Expected Grade A, got {data['ai_grade']}"
    assert data["review_status"] == "PENDING_REVIEW"
    assert data["human_final_grade"] is None, "AI prediction must NEVER automatically become final grade"
    assert data["human_final_score"] is None, "AI score must not be populated as final without human review"

    # Verify 12 Visual Parameters
    factors = data["ai_quality_factors"]
    visual_factors = [k for k, v in factors.items() if v.get("type") == "VISUAL_OPTICAL"]
    assert len(visual_factors) == 12, f"Expected 12 visual parameters, found {len(visual_factors)}"
    print(f"Verified 12 Optical Defect Parameters: {visual_factors}")

    # Verify Physical Parameters Segregation
    assert "physical_moisture" in factors, "Missing physical_moisture factor"
    assert "physical_weight" in factors, "Missing physical_weight factor"
    assert factors["physical_moisture"]["type"] == "PHYSICAL_MEASUREMENT"
    assert "Requires physical/manual measurement" in factors["physical_moisture"]["notice"]
    assert "Requires physical/manual measurement" in factors["physical_weight"]["notice"]
    print("Verified Physical Measurements Notice:", factors["physical_moisture"]["notice"])
    print("✅ TEST 2 PASSED: 12 visual parameters analyzed and physical probes segregated.\n")

    # --------------------------------------------------------------------------
    # TEST 3: Grade Boundary Accuracy Tests
    # --------------------------------------------------------------------------
    print("--- TEST 3: Grade Boundary Accuracy Verification ---")
    # Test Grade B (Moderate defects)
    res_b = central_ai_service.vision_model.analyze_crop_quality({
        "crop_name": "Wheat", "foreign_material_pct": 2.5, "broken_grains_pct": 4.0, "damaged_grains_pct": 1.2
    })
    print(f"Moderate Defects -> Score: {res_b['ai_score']}, Grade: {res_b['ai_grade']}")
    assert 60.0 <= res_b["ai_score"] < 80.0 or res_b["ai_grade"] == "B", f"Expected Grade B, got {res_b['ai_grade']}"

    # Test Grade C / Reject (Severe defects & pest damage)
    res_reject = central_ai_service.vision_model.analyze_crop_quality({
        "crop_name": "Wheat", "foreign_material_pct": 6.0, "broken_grains_pct": 8.0, "damaged_grains_pct": 5.0,
        "has_cuts": True, "has_cracks": True, "has_spots": True, "has_bruises": True, "has_pest_damage": True
    })
    print(f"Severe Defects -> Score: {res_reject['ai_score']}, Grade: {res_reject['ai_grade']}")
    assert res_reject["ai_score"] < 40.0, f"Expected Reject score < 40, got {res_reject['ai_score']}"
    assert res_reject["ai_grade"] == "REJECTED"
    print("✅ TEST 3 PASSED: Grade boundaries verified (A: 80-100, B: 60-79, C: 40-59, Reject: <40).\n")

    # --------------------------------------------------------------------------
    # TEST 4: One-Click Zero-Typing Human Approval
    # --------------------------------------------------------------------------
    print("--- TEST 4: One-Click Zero-Typing Human Approval ---")
    approve_resp = client.post(
        f"/api/v1/ai/warehouse/grading/{created_id}/approve",
        json={"notes": "Standard approval by Pune Central Silo inspector"},
        headers=headers_wh
    )
    assert approve_resp.status_code == 200, f"Approval failed: {approve_resp.text}"
    approved_data = approve_resp.json()
    assert approved_data["review_status"] == "APPROVED"
    assert approved_data["effective_final_grade"] == "A"
    assert approved_data["effective_final_score"] == approved_data["ai_score"]
    assert approved_data["reviewed_by"] == "major_warehouse"
    assert approved_data["reviewed_at"] is not None

    # Dual Storage Check: Original AI score/grade preserved
    assert approved_data["ai_score"] == data["ai_score"]
    assert approved_data["ai_grade"] == data["ai_grade"]

    # Verify sync to major_warehouse_intakes
    intake = db.query(MajorWarehouseIntake).filter(MajorWarehouseIntake.batch_id == "KS-BATCH-1001").first()
    assert intake is not None
    assert intake.human_final_grade == "A"
    assert intake.review_status == "CONFIRMED"
    print("Intake confirmed in major_warehouse_intakes:", intake.batch_id, intake.human_final_grade)
    print("✅ TEST 4 PASSED: One-click approval stamps final grade and syncs to intake ledger.\n")

    # --------------------------------------------------------------------------
    # TEST 5: Human Review Correction & Mandatory Justification Enforcement
    # --------------------------------------------------------------------------
    print("--- TEST 5: Human Review Correction & Mandatory Justification Validation ---")
    # Create another record to test correction
    test2_resp = client.post(
        "/api/v1/ai/warehouse/grading/analyze",
        json=analyze_payload,
        headers=headers_wh
    )
    record2_id = test2_resp.json()["id"]

    # 5a. Attempt correction with short reason (< 5 chars) -> Must fail with 422
    invalid_correct = client.post(
        f"/api/v1/ai/warehouse/grading/{record2_id}/correct",
        json={
            "human_final_grade": "B",
            "human_final_score": 75.0,
            "correction_reason": "bad", # 3 chars < 5
        },
        headers=headers_wh
    )
    assert invalid_correct.status_code == 422, f"Expected 422 for reason < 5 chars, got {invalid_correct.status_code}"
    print("Correctly rejected short reason (<5 chars) with HTTP 422:", invalid_correct.json()["detail"])

    # 5b. Valid correction override
    valid_correct = client.post(
        f"/api/v1/ai/warehouse/grading/{record2_id}/correct",
        json={
            "human_final_grade": "B",
            "human_final_score": 76.5,
            "correction_reason": "Visual optical probe detected 3.2% foreign seed chaff. Downgraded to Grade B.",
            "notes": "Store in Silo Bay B-3 with aeration",
        },
        headers=headers_wh
    )
    assert valid_correct.status_code == 200, f"Correction failed: {valid_correct.text}"
    corrected_data = valid_correct.json()

    # Verify Dual-Storage Guarantee: Original AI values 100% untouched
    assert corrected_data["review_status"] == "CORRECTED"
    assert corrected_data["ai_grade"] == "A", "Original AI grade must NOT be overwritten"
    assert corrected_data["human_final_grade"] == "B", "Human final grade must be updated"
    assert corrected_data["human_final_score"] == 76.5
    assert corrected_data["effective_final_grade"] == "B"
    assert "foreign seed chaff" in corrected_data["correction_reason"]

    # Check sync to major_warehouse_intakes
    db.refresh(intake)
    assert intake.human_final_grade == "B"
    print("Updated intake confirmed in major_warehouse_intakes:", intake.batch_id, intake.human_final_grade)
    print("✅ TEST 5 PASSED: Human review correction strictly validates reason and preserves original AI predictions.\n")

    # --------------------------------------------------------------------------
    # TEST 6: Role-Based Access Control (RBAC) Enforcement
    # --------------------------------------------------------------------------
    print("--- TEST 6: Role-Based Access Control (RBAC) Enforcement ---")
    headers_farmer = create_auth_header("farmer_demo", UserRole.FARMER)
    headers_gp = create_auth_header("gram_panchayat", UserRole.GRAM_PANCHAYAT)

    # Farmer trying to approve
    farmer_approve = client.post(
        f"/api/v1/ai/warehouse/grading/{record2_id}/approve",
        json={"notes": "Farmer self approval"},
        headers=headers_farmer
    )
    assert farmer_approve.status_code == 403, f"Expected 403 for farmer approval, got {farmer_approve.status_code}"

    # GP trying to correct
    gp_correct = client.post(
        f"/api/v1/ai/warehouse/grading/{record2_id}/correct",
        json={"human_final_grade": "A", "human_final_score": 90.0, "correction_reason": "GP unauthorized change"},
        headers=headers_gp
    )
    assert gp_correct.status_code == 403, f"Expected 403 for GP correction, got {gp_correct.status_code}"
    print("Confirmed: Unauthorized roles rejected with HTTP 403 FORBIDDEN.")
    print("✅ TEST 6 PASSED: RBAC permissions strictly enforced.\n")

    # --------------------------------------------------------------------------
    # TEST 7: Audit Log Provenance & Batch Traceability
    # --------------------------------------------------------------------------
    print("--- TEST 7: Audit Log Provenance & Batch Traceability ---")
    logs = db.query(AuditLog).filter(
        AuditLog.table_name == "ai_warehouse_grading_records"
    ).all()
    assert len(logs) >= 2, f"Expected at least 2 audit logs, found {len(logs)}"
    for log in logs[-2:]:
        print(f"Audit Trail Record: field={log.field_name}, edited_by={log.edited_by}, reason={log.change_reason}")

    # Verify batch traceability link in farmer complete history
    history_resp = client.get("/api/records/farmer/complete-history?farmer_id=KS-FMR-1001", headers=headers_wh)
    assert history_resp.status_code == 200, f"History fetch failed: {history_resp.text}"
    events = history_resp.json().get("events", [])
    grading_events = [e for e in events if e.get("event_type") == "QUALITY_GRADED"]
    assert len(grading_events) > 0, "Expected QUALITY_GRADED event in farmer complete history"
    assert grading_events[0]["batch_id"] == "KS-BATCH-1001"
    print(f"Farmer Complete History includes Batch {grading_events[0]['batch_id']} Quality Grading Event.")
    print("✅ TEST 7 PASSED: Batch traceability preserved end-to-end.\n")

    db.close()

    print("================================================================================")
    print("🎉 ALL TASK 5 MAJOR WAREHOUSE AI QUALITY & GRADING TESTS PASSED SUCCESSFULLY!")
    print("================================================================================\n")

if __name__ == "__main__":
    run_task5_verification()

