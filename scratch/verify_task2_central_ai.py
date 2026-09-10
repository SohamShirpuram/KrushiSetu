import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"d:\Projects\Gram Chain 2.O")

from fastapi.testclient import TestClient
from backend.main import app
from backend.services.auth_service import create_access_token

client = TestClient(app)

def run_tests():
    print("==================================================")
    print("TASK 2: KRUSHISETU CENTRAL AI/ML ENGINE VERIFICATION")
    print("==================================================")

    # 1. Tokens for RBAC testing
    fd_token = create_access_token({"sub": "food_dept", "role": "FOOD_DEPARTMENT", "id": 2})
    admin_token = create_access_token({"sub": "admin", "role": "ADMIN", "id": 1})
    farmer_token = create_access_token({"sub": "farmer_demo", "role": "FARMER", "id": 5})

    fd_headers = {"Authorization": f"Bearer {fd_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    farmer_headers = {"Authorization": f"Bearer {farmer_token}"}

    # 2. Test Engine Stats
    print("\n--- 1. Testing Central AI Stats ---")
    r = client.get("/api/v1/ai/stats", headers=fd_headers)
    assert r.status_code == 200, f"Stats failed: {r.text}"
    stats = r.json()
    assert stats["engine_status"] == "ONLINE"
    assert stats["model_version"] == "v1.0.0-prototype"
    assert stats["total_predictions"] >= 3
    print(f"✅ Engine Status: {stats['engine_status']}, Model: {stats['model_version']}, Total Preds: {stats['total_predictions']}")

    # 3. Test Generating Prediction (POST /api/v1/ai/crop-requirement/predict)
    print("\n--- 2. Testing AI Prediction Generation (Real Database Data) ---")
    predict_payload = {
        "crop_name": "Sugarcane",
        "season": "Kharif 2026",
        "region": "Baramati Block Panchayat Samiti"
    }
    r = client.post("/api/v1/ai/crop-requirement/predict", json=predict_payload, headers=fd_headers)
    assert r.status_code == 200, f"Prediction failed: {r.text}"
    pred = r.json()
    pred_id = pred["id"]
    pred_code = pred["prediction_id"]

    assert pred["ai_recommended_crop"] == "Sugarcane"
    assert pred["ai_recommended_quantity"] > 0
    assert pred["ai_priority"] in ("NORMAL", "HIGH", "CRITICAL")
    assert pred["suitable_region"] == "Baramati Block Panchayat Samiti"
    assert "Central AI evaluated" in pred["ai_reasoning"]
    assert "current_shortage" in pred["ai_factors"]
    assert pred["ai_confidence"] >= 0.85
    assert pred["review_status"] == "PENDING_REVIEW"
    assert pred["human_final_quantity"] is None

    print(f"✅ AI Prediction Generated: #{pred_code} (DB ID: {pred_id})")
    print(f"   Recommended: {pred['ai_recommended_quantity']:,.0f} MT {pred['ai_recommended_crop']} | Priority: {pred['ai_priority']}")
    print(f"   Confidence: {pred['ai_confidence'] * 100:.1f}% | Region: {pred['suitable_region']}")

    # 4. Test Prediction Retrieval (GET /api/v1/ai/predictions & /predictions/{id})
    print("\n--- 3. Testing Prediction Retrieval ---")
    r = client.get("/api/v1/ai/predictions", headers=fd_headers)
    assert r.status_code == 200
    all_preds = r.json()
    assert len(all_preds) >= 4
    print(f"✅ Successfully retrieved {len(all_preds)} predictions.")

    r = client.get(f"/api/v1/ai/predictions/{pred_code}", headers=fd_headers)
    assert r.status_code == 200
    assert r.json()["prediction_id"] == pred_code
    print(f"✅ Retrieved single prediction by code '{pred_code}'.")

    # 5. Test One-Click Human Approval (POST /api/v1/ai/predictions/{id}/approve)
    print("\n--- 4. Testing Human Approval Workflow ---")
    r = client.post(f"/api/v1/ai/predictions/{pred_code}/approve", json={"notes": "Approved by Food Directorate"}, headers=fd_headers)
    assert r.status_code == 200, f"Approval failed: {r.text}"
    approved = r.json()
    assert approved["review_status"] == "APPROVED"
    assert approved["human_final_quantity"] == approved["ai_recommended_quantity"]
    assert approved["human_final_crop"] == approved["ai_recommended_crop"]
    assert approved["human_final_priority"] == approved["ai_priority"]
    assert approved["reviewed_by"] == "food_dept"
    print(f"✅ Approved Prediction #{pred_code}: AI and Human values identical ({approved['human_final_quantity']} MT).")

    # 6. Test Human Correction Workflow (POST /api/v1/ai/predictions/{id}/correct)
    print("\n--- 5. Testing Human Correction Workflow (Mandatory Reason + Dual Storage) ---")
    
    # Generate another prediction to test correction
    r = client.post("/api/v1/ai/crop-requirement/predict", json={"crop_name": "Wheat (Lokwan)", "season": "Rabi 2026"}, headers=fd_headers)
    assert r.status_code == 200
    pred2 = r.json()
    pred2_code = pred2["prediction_id"]
    ai_original_qty = pred2["ai_recommended_quantity"]
    ai_original_crop = pred2["ai_recommended_crop"]
    ai_original_priority = pred2["ai_priority"]

    # 6a. Should fail if correction_reason is empty/missing
    bad_correct = {
        "human_final_quantity_mt": 22000.0,
        "correction_reason": ""  # empty!
    }
    r = client.post(f"/api/v1/ai/predictions/{pred2_code}/correct", json=bad_correct, headers=fd_headers)
    assert r.status_code in (400, 422), f"Expected validation error for missing reason, got: {r.status_code}"
    print(f"✅ Rejection verified for missing correction reason (HTTP {r.status_code}).")

    # 6b. Correct with valid reason
    valid_correct = {
        "human_final_crop": "Wheat (Lokwan)",
        "human_final_quantity_mt": 22000.0,
        "human_final_priority": "HIGH",
        "correction_reason": "Adjusted downward by Directorate to prevent local grain market over-supply."
    }
    r = client.post(f"/api/v1/ai/predictions/{pred2_code}/correct", json=valid_correct, headers=fd_headers)
    assert r.status_code == 200, f"Correction failed: {r.text}"
    corrected = r.json()

    # CRITICAL DUAL-STORAGE ASSERTIONS:
    # 1. Original AI values MUST remain completely untouched!
    assert corrected["ai_recommended_quantity"] == ai_original_qty, "CRITICAL ERROR: AI original quantity was overwritten!"
    assert corrected["ai_recommended_crop"] == ai_original_crop, "CRITICAL ERROR: AI original crop was overwritten!"
    assert corrected["ai_priority"] == ai_original_priority, "CRITICAL ERROR: AI original priority was overwritten!"
    
    # 2. Human values MUST be stored in their separate dedicated fields!
    assert corrected["human_final_quantity"] == 22000.0
    assert corrected["human_final_crop"] == "Wheat (Lokwan)"
    assert corrected["human_final_priority"] == "HIGH"
    assert corrected["review_status"] == "CORRECTED"
    assert corrected["reviewed_by"] == "food_dept"
    assert corrected["correction_reason"] == "Adjusted downward by Directorate to prevent local grain market over-supply."

    print(f"✅ Correction verified with Dual-Storage Guarantee:")
    print(f"   Original AI Value:    {corrected['ai_recommended_quantity']:,.0f} MT ({corrected['ai_priority']}) [PERMANENTLY PRESERVED]")
    print(f"   Human Corrected Value: {corrected['human_final_quantity']:,.0f} MT ({corrected['human_final_priority']}) [STORED SEPARATELY]")
    print(f"   Correction Reason:     '{corrected['correction_reason']}'")

    # 7. Test Audit Log for Correction
    print("\n--- 6. Testing Audit Log for Correction ---")
    r = client.get(f"/api/records/audit/ai_prediction_records/{corrected['id']}", headers=fd_headers)
    assert r.status_code == 200
    history = r.json().get("history", [])
    assert len(history) > 0, "Expected audit entries for prediction lifecycle"
    print(f"✅ Found {len(history)} audit history entries for prediction #{corrected['id']}.")

    # 8. Test Authorization & RBAC
    print("\n--- 7. Testing RBAC / Authorization ---")
    # Farmer attempting to predict or approve should be rejected with 403 Forbidden
    r = client.post("/api/v1/ai/crop-requirement/predict", json={"crop_name": "Wheat"}, headers=farmer_headers)
    assert r.status_code == 403, f"Expected 403 Forbidden for unauthorized role, got: {r.status_code}"
    print(f"✅ Authorization verified: Farmer role correctly rejected with HTTP 403.")

    print("\n==================================================")
    print("ALL CENTRAL AI/ML ENGINE TESTS PASSED PERFECTLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
