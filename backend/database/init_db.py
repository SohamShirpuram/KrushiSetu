"""
Database initialization and seeding script for KrushiSetu.
Creates all schema tables and pre-seeds rich operational records across all sectors.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.connection import engine, SessionLocal, Base
from backend.models import (
    User,
    UserRole,
    AuditLog,
    FDCropRequirement,
    FDCrisisRecord,
    FDDemandProjection,
    FDWeatherData,
    FDPSAllocation,
    PanchayatSamiti,
    PSGPRegistry,
    PSSoilSuitability,
    PSGPAllocation,
    GramPanchayat,
    FarmerRegistry,
    FarmerLandRecord,
    SoilTestRecord,
    GPCropAssignment,
    FarmerHarvestRecord,
    FarmerDeliveryRecord,
    FarmerPaymentRecord,
    MajorWarehouseIntake,
    MajorWarehouseDispatch,
    MajorWarehouseStorage,
    MinorWarehouseInward,
    MinorWarehouseStock,
    MinorWarehouseDemand,
    MinorWarehouseDistribution,
    MinorWarehouseRestock,
    BulkBuyerRegistry,
    BulkBuyerEntry,
    AIPredictionRecord,
    AIGPAllocationRecord,
    AIFarmerRecommendationRecord,
    AIMajorWarehouseGradingRecord,
)
import json
from backend.services.auth_service import hash_password

INITIAL_USERS = [
    {
        "username": "admin",
        "email": "admin@krushisetu.gov.in",
        "password": "Krushi@123",
        "role": UserRole.ADMIN,
        "full_name": "KrushiSetu Administrator",
        "jurisdiction_or_location": "Central Directorate, Krishi Bhavan",
        "farmer_id": None,
        "buyer_id": None,
    },
    {
        "username": "food_dept",
        "email": "director.food@krushisetu.gov.in",
        "password": "Krushi@123",
        "role": UserRole.FOOD_DEPARTMENT,
        "full_name": "State Food & Civil Supplies Directorate",
        "jurisdiction_or_location": "State Headquarters",
        "farmer_id": None,
        "buyer_id": None,
    },
    {
        "username": "panchayat_samiti",
        "email": "bdo.samiti@krushisetu.gov.in",
        "password": "Krushi@123",
        "role": UserRole.PANCHAYAT_SAMITI,
        "full_name": "Taluka Panchayat Samiti Office",
        "jurisdiction_or_location": "Baramati Block, Pune District",
        "farmer_id": None,
        "buyer_id": None,
    },
    {
        "username": "gram_panchayat",
        "email": "sarpanch.shirsuphal@krushisetu.gov.in",
        "password": "Krushi@123",
        "role": UserRole.GRAM_PANCHAYAT,
        "full_name": "Shirsuphal Gram Panchayat Council",
        "jurisdiction_or_location": "Shirsuphal Village, Baramati",
        "farmer_id": None,
        "buyer_id": None,
    },
    {
        "username": "farmer_demo",
        "email": "ramesh.patil@krushisetu.gov.in",
        "password": "Krushi@123",
        "role": UserRole.FARMER,
        "full_name": "Ramesh Narayan Patil",
        "jurisdiction_or_location": "Plot No. 42, Shirsuphal Village",
        "farmer_id": "KS-FMR-1001",
        "buyer_id": None,
    },
    {
        "username": "major_warehouse",
        "email": "wh.central.pune@krushisetu.gov.in",
        "password": "Krushi@123",
        "role": UserRole.MAJOR_WAREHOUSE,
        "full_name": "Central Grain Silo Complex (50,000 MT)",
        "jurisdiction_or_location": "Pune Industrial Logistics Hub",
        "farmer_id": None,
        "buyer_id": None,
    },
    {
        "username": "minor_warehouse",
        "email": "wh.mandi.baramati@krushisetu.gov.in",
        "password": "Krushi@123",
        "role": UserRole.MINOR_WAREHOUSE,
        "full_name": "Baramati Block APMC Transit Godown",
        "jurisdiction_or_location": "APMC Yard, Baramati",
        "farmer_id": None,
        "buyer_id": None,
    },
    {
        "username": "bulk_buyer_demo",
        "email": "procurement@agrocorpfoods.com",
        "password": "Krushi@123",
        "role": UserRole.BULK_BUYER,
        "full_name": "AgroCorp Foods Processing Ltd",
        "jurisdiction_or_location": "MIDC Food Park, Chakan",
        "farmer_id": None,
        "buyer_id": "KS-BYR-5001",
    },
]

def init_db(seed: bool = True):
    """Initializes tables and optionally seeds default role accounts & records."""
    print("Creating database schema...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

    if not seed:
        return

    db: Session = SessionLocal()
    try:
        # 1. Seed Users
        for user_data in INITIAL_USERS:
            existing = db.query(User).filter(User.username == user_data["username"]).first()
            if not existing:
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=hash_password(user_data["password"]),
                    role=user_data["role"],
                    full_name=user_data["full_name"],
                    jurisdiction_or_location=user_data["jurisdiction_or_location"],
                    farmer_id=user_data["farmer_id"],
                    buyer_id=user_data["buyer_id"],
                    is_active=True,
                )
                db.add(user)
        db.commit()

        # 2. Seed Food Department Records
        if db.query(FDCropRequirement).count() == 0:
            sugarcane_req = FDCropRequirement(
                crop_name="Sugarcane",
                season="Kharif 2026",
                target_quantity_mt=22000.0,
                priority="HIGH",
                status="APPROVED",
                # AI Recommendation (Preserved)
                ai_crop_name="Sugarcane",
                ai_recommended_quantity_mt=25000.0,
                ai_priority="HIGH",
                ai_confidence_score=0.96,
                ai_rationale="Current shortage + predicted future demand + suitable regions across Pune & Solapur clusters.",
                # Human Final Decision
                human_final_quantity_mt=22000.0,
                human_final_priority="HIGH",
                finalized_by="food_dept",
                finalized_at=datetime.utcnow(),
                human_review_notes="Approved after 3,000 MT reduction due to inter-state procurement agreement.",
                notes="State strategic buffer requirement for sugar cooperative processing.",
            )
            db.add(sugarcane_req)

            wheat_ai_req = FDCropRequirement(
                crop_name="Wheat (Lokwan)",
                season="Rabi 2026",
                target_quantity_mt=50000.0,
                priority="HIGH",
                status="AI_GENERATED",
                # AI Recommendation
                ai_crop_name="Wheat (Lokwan)",
                ai_recommended_quantity_mt=50000.0,
                ai_priority="HIGH",
                ai_confidence_score=0.94,
                ai_rationale="High industrial demand forecast FY27 (55,000 MT) + 8,500 MT Marathwada chana deficit offset.",
                human_final_quantity_mt=None,
                human_final_priority=None,
                finalized_by=None,
                notes="Awaiting Food Directorate human officer review.",
            )
            db.add(wheat_ai_req)
            db.commit()

            # Seed Audit Log for Sugarcane human edit
            db.add(AuditLog(
                table_name="fd_crop_requirements",
                record_id=str(sugarcane_req.id),
                field_name="target_quantity_mt",
                old_value="25000.0",
                new_value="22000.0",
                edited_by="food_dept",
                edited_by_role="FOOD_DEPARTMENT",
                change_reason="Adjusted down by 3,000 MT based on neighboring state surplus import agreement.",
            ))
            db.commit()

            db.add_all([
                FDCrisisRecord(
                    crop_name="Gram / Chana",
                    region_or_district="Marathwada Division",
                    deficit_amount_mt=8500.0,
                    severity="SEVERE",
                    mitigation_strategy="Inter-district buffer transfer from western Maharashtra storage hubs.",
                    status="UNDER_MANAGEMENT",
                ),
                FDDemandProjection(
                    crop_name="Wheat",
                    time_period="FY 2026-27",
                    current_demand_mt=48000.0,
                    future_demand_mt=55000.0,
                    projected_growth_pct=14.5,
                    remarks="Growing industrial flour mill procurement demand in Pune and Thane clusters.",
                ),
                FDWeatherData(
                    region="Pune & Western Ghats Foothills",
                    season="Rabi 2026",
                    rainfall_mm=680.0,
                    avg_temperature_c=27.4,
                    soil_moisture_index=0.72,
                    climate_alert="NORMAL",
                ),
                FDPSAllocation(
                    panchayat_samiti_name="Baramati Block Panchayat Samiti",
                    crop_name="Wheat (Lokwan)",
                    target_quota_mt=12000.0,
                    ai_suggested_quota_mt=11500.0,
                    human_final_quota_mt=12000.0,
                    ai_rationale="High soil suitability index in Baramati eastern canal zone.",
                    review_status="CONFIRMED",
                    status="ASSIGNED",
                )
            ])
            db.commit()

        # 3. Seed Panchayat Samiti Records
        if db.query(PSGPRegistry).count() == 0:
            db.add_all([
                PSGPRegistry(
                    gp_code="GP-BMT-01",
                    gp_name="Shirsuphal Gram Panchayat",
                    panchayat_samiti_name="Baramati Block Panchayat Samiti",
                    total_area_hectares=1450.0,
                    cultivable_area_hectares=1120.0,
                    active_farmers_count=340,
                ),
                PSGPRegistry(
                    gp_code="GP-BMT-02",
                    gp_name="Songaon Gram Panchayat",
                    panchayat_samiti_name="Baramati Block Panchayat Samiti",
                    total_area_hectares=1280.0,
                    cultivable_area_hectares=950.0,
                    active_farmers_count=295,
                ),
                PSSoilSuitability(
                    gp_name="Shirsuphal Gram Panchayat",
                    soil_type="Medium Deep Black Cotton Soil",
                    primary_crops="Wheat, Soybean, Bengal Gram",
                    irrigation_coverage_pct=78.5,
                    organic_matter_rating="HIGH",
                ),
                PSGPAllocation(
                    panchayat_samiti_name="Baramati Block Panchayat Samiti",
                    gp_name="Shirsuphal Gram Panchayat",
                    crop_name="Wheat (Lokwan)",
                    allocated_quantity_mt=2500.0,
                    season="Rabi 2026",
                    status="ASSIGNED",
                )
            ])
            db.commit()

        # 4. Seed Gram Panchayat Records (Linking Farmer ID: KS-FMR-1001)
        if db.query(FarmerRegistry).count() == 0:
            db.add_all([
                FarmerRegistry(
                    farmer_id="KS-FMR-1001",
                    farmer_name="Ramesh Narayan Patil",
                    contact_phone="+91 98220 44556",
                    aadhaar_masked="XXXX-XXXX-8921",
                    gp_name="Shirsuphal Gram Panchayat",
                    panchayat_samiti_name="Baramati Block Panchayat Samiti",
                    district="Pune",
                    village_name="Shirsuphal",
                    total_land_acres=4.5,
                    bank_account_masked="SBIN000XXXX4412",
                    soil_health_card_no="SHC-MH-BMT-1001",
                ),
                FarmerRegistry(
                    farmer_id="KS-FMR-1002",
                    farmer_name="Dattatray Keshav Jagtap",
                    contact_phone="+91 94230 77889",
                    aadhaar_masked="XXXX-XXXX-3341",
                    gp_name="Shirsuphal Gram Panchayat",
                    panchayat_samiti_name="Baramati Block Panchayat Samiti",
                    district="Pune",
                    village_name="Shirsuphal",
                    total_land_acres=6.0,
                    bank_account_masked="MAHG000XXXX1190",
                    soil_health_card_no="SHC-MH-BMT-1002",
                ),
            ])
            db.commit()

        if db.query(FarmerLandRecord).count() == 0:
            db.add_all([
                FarmerLandRecord(
                    farmer_id="KS-FMR-1001",
                    farmer_name="Ramesh Narayan Patil",
                    survey_number="Gat No. 42/1",
                    village_name="Shirsuphal",
                    land_area_acres=4.5,
                    soil_type="Deep Black Loamy Soil",
                    irrigation_source="Nira Left Bank Canal",
                ),
                SoilTestRecord(
                    farmer_id="KS-FMR-1001",
                    survey_number="Gat No. 42/1",
                    sample_date="2026-08-15",
                    ph_level=7.3,
                    nitrogen_kg_ha=260.0,
                    phosphorus_kg_ha=38.0,
                    potassium_kg_ha=290.0,
                    organic_carbon_pct=0.68,
                    soil_test_doc_url="soil_test_shirsuphal_42.jpg",
                    testing_lab="Baramati Agricultural Research Center",
                ),
                GPCropAssignment(
                    farmer_id="KS-FMR-1001",
                    farmer_name="Ramesh Narayan Patil",
                    crop_name="Wheat (Lokwan)",
                    season="Rabi 2026",
                    assigned_acres=4.5,
                    required_quantity_quintals=90.0,
                    status="ASSIGNED",
                )
            ])
            db.commit()

        # 5. Seed Farmer Operational Records
        if db.query(FarmerHarvestRecord).count() == 0:
            db.add_all([
                FarmerHarvestRecord(
                    farmer_id="KS-FMR-1001",
                    crop_name="Wheat (Lokwan)",
                    season="Rabi 2026",
                    harvest_date="2026-09-02",
                    actual_yield_kg=9200.0,
                    quality_condition="GOOD",
                    notes="Harvested with combine harvester at 11% grain moisture.",
                ),
                FarmerDeliveryRecord(
                    farmer_id="KS-FMR-1001",
                    crop_name="Wheat (Lokwan)",
                    target_warehouse_name="Central Strategic Silo Complex Pune",
                    vehicle_slip_number="MH-12-TR-4028",
                    declared_weight_kg=9200.0,
                    weighbridge_net_weight_kg=9150.0,
                    batch_id="KS-BATCH-1001",
                    delivery_date="2026-09-05",
                    status="GRADED",
                ),
                FarmerPaymentRecord(
                    farmer_id="KS-FMR-1001",
                    batch_id="KS-BATCH-1001",
                    crop_name="Wheat (Lokwan)",
                    net_weight_kg=9150.0,
                    confirmed_grade="B",
                    rate_per_kg=28.0,
                    total_amount=256200.0,
                    payment_status="APPROVED",
                    transaction_ref="DBT-GOV-2026-88392",
                    payment_date="2026-09-07",
                )
            ])
            db.commit()

        # 6. Seed Major Warehouse Records (Batch ID: KS-BATCH-1001, Dual Grading)
        if db.query(MajorWarehouseIntake).count() == 0:
            major_intake = MajorWarehouseIntake(
                batch_id="KS-BATCH-1001",
                farmer_id="KS-FMR-1001",
                farmer_name="Ramesh Narayan Patil",
                crop_name="Wheat (Lokwan)",
                gross_weight_kg=14250.0,
                tare_weight_kg=5100.0,
                net_weight_kg=9150.0,
                crop_image_url="wheat_batch_1001.jpg",
                # AI Predicted Quality
                ai_predicted_score=86.0,
                ai_predicted_grade="A",
                # Human Confirmed Result
                human_final_score=78.0,
                human_final_grade="B",
                grading_notes="Visual inspection detected 2.8% foreign grain matter. Downgraded from AI prediction A to Grade B.",
                review_status="CONFIRMED",
                reviewed_by="major_warehouse",
                reviewed_at=datetime.utcnow(),
                storage_silo_bay="Silo-North-B2",
                storage_temp_celsius=21.2,
                storage_humidity_pct=56.5,
                intake_status="GRADED_STORED",
            )
            db.add(major_intake)

            major_dispatch = MajorWarehouseDispatch(
                dispatch_id="KS-DSP-7001",
                batch_id="KS-BATCH-1001",
                crop_name="Wheat (Lokwan)",
                dispatch_quantity_kg=4000.0,
                destination_minor_warehouse="Baramati APMC Godown No. 3",
                truck_number="MH-12-AB-9876",
                driver_name="Suresh Kisan Rathod",
                driver_phone="+91 98220 54321",
                dispatch_date="2026-09-08",
                status="RECEIVED_AT_DESTINATION",
            )
            db.add(major_dispatch)

            major_storage = MajorWarehouseStorage(
                storage_id="KS-STR-8001",
                batch_id="KS-BATCH-1001",
                crop_name="Wheat (Lokwan)",
                quantity_kg=9150.0,
                current_stock_kg=5150.0,
                storage_location="Central Silo Complex Bay A-3",
                movement_type="INTAKE_STORAGE",
                status="STORED",
                storage_date="2026-09-08",
            )
            db.add(major_storage)
            db.commit()

            # Seed an initial audit log entry demonstrating the user's required dual grading review
            db.add(AuditLog(
                table_name="major_warehouse_intakes",
                record_id=str(major_intake.id),
                field_name="human_final_grade",
                old_value="A",
                new_value="B",
                edited_by="major_warehouse",
                edited_by_role="MAJOR_WAREHOUSE",
                change_reason="Human inspection detected 2.8% foreign grain matter. Confirmed final grade B.",
            ))
            db.commit()

        # 7. Seed Minor Warehouse Records (Receiving from Major WH Dispatch)
        if db.query(MinorWarehouseInward).count() == 0:
            db.add_all([
                MinorWarehouseInward(
                    dispatch_id="KS-DSP-7001",
                    batch_id="KS-BATCH-1001",
                    crop_name="Wheat (Lokwan)",
                    source_major_wh="Pune Central Silo Hub",
                    truck_number="MH-12-AB-9876",
                    driver_name="Suresh Kisan Rathod",
                    received_quantity_kg=4000.0,
                    intake_date="2026-09-08",
                    verification_status="VERIFIED_IN_STOCK",
                ),
                MinorWarehouseStock(
                    crop_name="Wheat (Lokwan)",
                    batch_id="KS-BATCH-1001",
                    current_stock_kg=2800.0,
                    warehouse_location="Baramati APMC Godown No. 3",
                    last_replenished="2026-09-08",
                ),
                MinorWarehouseDemand(
                    region_name="Baramati Cluster Mandi",
                    crop_name="Wheat",
                    monthly_demand_kg=6500.0,
                    urgency_level="NORMAL",
                    notes="Steady weekly distribution to regional Fair Price Shops.",
                ),
                MinorWarehouseDistribution(
                    batch_id="KS-BATCH-1001",
                    crop_name="Wheat (Lokwan)",
                    recipient_center="Shirsuphal Fair Price Distribution Shop #12",
                    quantity_kg=1200.0,
                    receipt_no="RCPT-BMT-2026-081",
                    distribution_date="2026-09-09",
                    status="COMPLETED",
                ),
                MinorWarehouseRestock(
                    crop_name="Wheat (Lokwan)",
                    requested_quantity_kg=3500.0,
                    urgency="HIGH",
                    request_date="2026-09-09",
                    status="PENDING_MAJOR_DISPATCH",
                )
            ])
            db.commit()

        # 8. Seed Bulk Buyer Records
        if db.query(BulkBuyerRegistry).count() == 0:
            db.add_all([
                BulkBuyerRegistry(
                    buyer_id="KS-BYR-5001",
                    company_name="AgroCorp Foods Processing Ltd",
                    business_type="Agro Industrial Processor",
                    gst_number="27AAACA1234F1Z5",
                    contact_person="Vikram Malhotra",
                    contact_phone="+91 98210 11223",
                    official_email="procurement@agrocorpfoods.com",
                    status="VERIFIED_BUYER",
                ),
                BulkBuyerEntry(
                    buyer_id="KS-BYR-5001",
                    crop_name="Wheat (Lokwan)",
                    required_quantity_mt=500.0,
                    target_grade="B",
                    max_price_offer_per_quintal=3050.0,
                    delivery_hub="Pune Central Logistics Hub",
                    required_by_date="2026-09-25",
                    status="ENTRY_RECORDED",
                    notes="Procurement for central wheat flour processing mill.",
                )
            ])
            db.commit()

        # 9. Seed Central AI Prediction Records
        if db.query(AIPredictionRecord).count() == 0:
            db.add_all([
                AIPredictionRecord(
                    prediction_id="PRED-CR-2026-0001",
                    module_name="crop_requirement_recommendation",
                    model_name="ExplainableCropRequirementModel",
                    model_version="v1.0.0-prototype",
                    input_data_reference=json.dumps({
                        "data_sources": ["fd_crisis_records", "major_warehouse_storage", "fd_demand_projections", "ps_soil_suitability"],
                        "provenance": {"crisis_deficit": "5000 MT reported", "warehouse_stock": "4000 MT"},
                        "metrics": {"active_crisis_deficit_mt": 5000.0, "warehouse_reserves_mt": 4000.0}
                    }),
                    ai_recommended_crop="Sugarcane",
                    ai_recommended_quantity=25000.0,
                    ai_priority="HIGH",
                    ai_reasoning="Central AI evaluated 12 cross-sector datasets for 'Sugarcane' (Kharif 2026). Net demand deficit (23,500 MT) and active crisis shortage (5,000 MT) amplified by +12.0% future demand growth factor. Favorable seasonal rainfall (640.0 mm, +4.2%) and 90% soil suitability across 4,280 Ha justify a baseline production quota of 25,000 MT with HIGH priority.",
                    ai_factors=json.dumps({
                        "current_shortage": "5,000 MT active deficit across civil supplies",
                        "increased_demand": "15,000 MT current with +12.0% projected future demand",
                        "existing_warehouse_stock": "4,000.0 MT in Central Silos & Mandi Godowns",
                        "historical_production": "18,200.0 MT recorded in previous local harvests",
                        "weather_climate": "640.0 mm seasonal rainfall (+4.2% vs normal)",
                        "land_suitability": "90% soil suitability across 4,280 cultivable hectares",
                    }),
                    ai_confidence=0.94,
                    suitable_region="Baramati Block Panchayat Samiti",
                    generated_at=datetime(2026, 9, 8, 14, 0),
                    review_status="APPROVED",
                    human_final_crop="Sugarcane",
                    human_final_quantity=25000.0,
                    human_final_priority="HIGH",
                    reviewed_by="food_dept",
                    reviewed_at=datetime(2026, 9, 8, 14, 30),
                    correction_reason="Approved as recommended by AI",
                ),
                AIPredictionRecord(
                    prediction_id="PRED-CR-2026-0002",
                    module_name="crop_requirement_recommendation",
                    model_name="ExplainableCropRequirementModel",
                    model_version="v1.0.0-prototype",
                    input_data_reference=json.dumps({
                        "data_sources": ["fd_crisis_records", "fd_demand_projections", "fd_weather_data"],
                        "provenance": {"crisis_deficit": "8500 MT reported"},
                        "metrics": {"active_crisis_deficit_mt": 8500.0, "warehouse_reserves_mt": 4000.0}
                    }),
                    ai_recommended_crop="Wheat (Lokwan)",
                    ai_recommended_quantity=57900.0,
                    ai_priority="CRITICAL",
                    ai_reasoning="Central AI computed baseline of 57,900 MT due to acute drought risk in adjacent Marathwada division and depleted transit godown buffers.",
                    ai_factors=json.dumps({
                        "current_shortage": "8,500 MT active deficit across civil supplies",
                        "increased_demand": "18,000 MT current with +15.0% projected future demand",
                        "existing_warehouse_stock": "4,000.0 MT in Central Silos & Mandi Godowns",
                        "historical_production": "9,200.0 MT recorded in previous local harvests",
                        "weather_climate": "610.0 mm seasonal rainfall (-5.1% vs normal)",
                        "land_suitability": "88% soil suitability across 4,280 cultivable hectares",
                    }),
                    ai_confidence=0.92,
                    suitable_region="Baramati Block Panchayat Samiti",
                    generated_at=datetime(2026, 9, 9, 9, 45),
                    review_status="CORRECTED",
                    human_final_crop="Wheat (Lokwan)",
                    human_final_quantity=52000.0,
                    human_final_priority="HIGH",
                    reviewed_by="food_dept",
                    reviewed_at=datetime(2026, 9, 9, 10, 15),
                    correction_reason="Adjusted downward by 5,900 MT to match local seed availability and avoid over-allocation in single block.",
                ),
                AIPredictionRecord(
                    prediction_id="PRED-CR-2026-0003",
                    module_name="crop_requirement_recommendation",
                    model_name="ExplainableCropRequirementModel",
                    model_version="v1.0.0-prototype",
                    input_data_reference=json.dumps({
                        "data_sources": ["fd_crisis_records", "fd_demand_projections", "ps_soil_suitability"],
                        "metrics": {"active_crisis_deficit_mt": 3200.0, "warehouse_reserves_mt": 2800.0}
                    }),
                    ai_recommended_crop="Paddy / Rice",
                    ai_recommended_quantity=20000.0,
                    ai_priority="HIGH",
                    ai_reasoning="Central AI computed baseline of 20,000 MT Paddy / Rice for Kharif 2026 based on Shirsuphal canal irrigation capacity and regional consumer preference trends.",
                    ai_factors=json.dumps({
                        "current_shortage": "3,200 MT reported in regional civil distribution",
                        "increased_demand": "12,000 MT state PDS requirement",
                        "existing_warehouse_stock": "2,800.0 MT in APMC buffer",
                        "historical_production": "14,000.0 MT recorded in previous Kharif",
                        "weather_climate": "Adequate canal discharge anticipated",
                        "land_suitability": "Shirsuphal Canal Lowlands rated Highly Suitable",
                    }),
                    ai_confidence=0.91,
                    suitable_region="Shirsuphal Canal Belt",
                    generated_at=datetime(2026, 9, 9, 11, 0),
                    review_status="PENDING_REVIEW",
                ),
            ])
            db.commit()

        # 9. Seed Central AI Panchayat Samiti -> Gram Panchayat Allocations
        if db.query(AIGPAllocationRecord).count() == 0:
            db.add_all([
                AIGPAllocationRecord(
                    allocation_code="GPA-2026-0001",
                    batch_code="BATCH-GPA-2026-001",
                    fd_requirement_id=1,
                    panchayat_samiti_name="Baramati Block Panchayat Samiti",
                    gp_code="GP-BMT-01",
                    gp_name="Shirsuphal Gram Panchayat",
                    crop_name="Wheat (Lokwan)",
                    season="Rabi 2026",
                    target_year=2026,
                    agricultural_area_ha=1120.0,
                    active_farmers_count=340,
                    ai_recommended_quantity_mt=4200.0,
                    ai_priority="HIGH",
                    ai_suitability="HIGH_SUITABILITY",
                    ai_reasoning="Top canal-fed black cotton soil area with 78.5% irrigation coverage and high organic matter. Strong historical yield.",
                    ai_confidence_score=0.95,
                    model_name="Central AI - PSToGPAllocationModel",
                    model_version="v1.0.0-prototype",
                    ai_factors={
                        "soil_type": "Medium Deep Black Cotton Soil",
                        "irrigation_pct": 78.5,
                        "organic_matter": "HIGH",
                        "cultivable_ha": 1120.0,
                        "share_pct": 35.0,
                    },
                    review_status="APPROVED",
                    human_final_quantity_mt=4200.0,
                    human_final_priority="HIGH",
                    reviewed_by="panchayat_samiti",
                    reviewed_at=datetime(2026, 9, 9, 12, 0),
                    human_review_notes="Approved directly. Optimal soil and irrigation.",
                ),
                AIGPAllocationRecord(
                    allocation_code="GPA-2026-0002",
                    batch_code="BATCH-GPA-2026-001",
                    fd_requirement_id=1,
                    panchayat_samiti_name="Baramati Block Panchayat Samiti",
                    gp_code="GP-BMT-02",
                    gp_name="Songaon Gram Panchayat",
                    crop_name="Wheat (Lokwan)",
                    season="Rabi 2026",
                    target_year=2026,
                    agricultural_area_ha=950.0,
                    active_farmers_count=295,
                    ai_recommended_quantity_mt=3600.0,
                    ai_priority="HIGH",
                    ai_suitability="HIGH_SUITABILITY",
                    ai_reasoning="Strong lift-irrigation capacity from Karha river basin. Highly suitable loamy black soil.",
                    ai_confidence_score=0.94,
                    model_name="Central AI - PSToGPAllocationModel",
                    model_version="v1.0.0-prototype",
                    ai_factors={
                        "soil_type": "Loamy Black Soil",
                        "irrigation_pct": 72.0,
                        "organic_matter": "MEDIUM",
                        "cultivable_ha": 950.0,
                        "share_pct": 30.0,
                    },
                    review_status="APPROVED",
                    human_final_quantity_mt=3600.0,
                    human_final_priority="HIGH",
                    reviewed_by="panchayat_samiti",
                    reviewed_at=datetime(2026, 9, 9, 12, 10),
                    human_review_notes="Approved without modification.",
                ),
                AIGPAllocationRecord(
                    allocation_code="GPA-2026-0003",
                    batch_code="BATCH-GPA-2026-001",
                    fd_requirement_id=1,
                    panchayat_samiti_name="Baramati Block Panchayat Samiti",
                    gp_code="GP-BMT-03",
                    gp_name="Karanje Gram Panchayat",
                    crop_name="Wheat (Lokwan)",
                    season="Rabi 2026",
                    target_year=2026,
                    agricultural_area_ha=820.0,
                    active_farmers_count=210,
                    ai_recommended_quantity_mt=2400.0,
                    ai_priority="NORMAL",
                    ai_suitability="MEDIUM_SUITABILITY",
                    ai_reasoning="Moderate borewell irrigation with medium clay-loam profile. Supports standard winter wheat quota.",
                    ai_confidence_score=0.92,
                    model_name="Central AI - PSToGPAllocationModel",
                    model_version="v1.0.0-prototype",
                    ai_factors={
                        "soil_type": "Clay Loam Soil",
                        "irrigation_pct": 60.0,
                        "organic_matter": "MEDIUM",
                        "cultivable_ha": 820.0,
                        "share_pct": 20.0,
                    },
                    review_status="PENDING_REVIEW",
                ),
                AIGPAllocationRecord(
                    allocation_code="GPA-2026-0004",
                    batch_code="BATCH-GPA-2026-001",
                    fd_requirement_id=1,
                    panchayat_samiti_name="Baramati Block Panchayat Samiti",
                    gp_code="GP-BMT-04",
                    gp_name="Murum Gram Panchayat",
                    crop_name="Wheat (Lokwan)",
                    season="Rabi 2026",
                    target_year=2026,
                    agricultural_area_ha=740.0,
                    active_farmers_count=185,
                    ai_recommended_quantity_mt=1800.0,
                    ai_priority="NORMAL",
                    ai_suitability="MEDIUM_SUITABILITY",
                    ai_reasoning="Suitable black soil parcel with minor seasonal water rationing constraint.",
                    ai_confidence_score=0.91,
                    model_name="Central AI - PSToGPAllocationModel",
                    model_version="v1.0.0-prototype",
                    ai_factors={
                        "soil_type": "Medium Black Soil",
                        "irrigation_pct": 55.0,
                        "organic_matter": "MEDIUM",
                        "cultivable_ha": 740.0,
                        "share_pct": 15.0,
                    },
                    review_status="CORRECTED",
                    human_final_quantity_mt=1800.0,
                    human_final_priority="NORMAL",
                    reviewed_by="panchayat_samiti",
                    reviewed_at=datetime(2026, 9, 9, 12, 25),
                    correction_reason="Confirmed at 1,800 MT after reviewing minor irrigation canal maintenance schedule.",
                    human_review_notes="Adjusted to align with seasonal tail-end canal water rotations.",
                ),
            ])
            db.commit()

        # 10. Seed Central AI Gram Panchayat -> Farmer Crop Recommendations
        if db.query(AIFarmerRecommendationRecord).count() == 0:
            db.add_all([
                AIFarmerRecommendationRecord(
                    recommendation_code="REC-FMR-2026-0001",
                    batch_code="BATCH-FRA-2026-001",
                    gp_allocation_id=1,
                    panchayat_samiti_name="Baramati Block Panchayat Samiti",
                    gp_code="GP-BMT-01",
                    gp_name="Shirsuphal Gram Panchayat",
                    farmer_id="KS-FMR-1001",
                    farmer_name="Ramesh Narayan Patil",
                    survey_number="Gat No. 42/1",
                    village_name="Shirsuphal",
                    crop_name="Wheat (Lokwan)",
                    season="Rabi 2026",
                    target_year=2026,
                    farmer_total_land_acres=4.5,
                    farmer_available_land_acres=4.5,
                    ai_recommended_area_acres=3.5,
                    ai_recommended_quantity_quintals=70.0,
                    ai_suitability="HIGH",
                    ai_priority="HIGH",
                    ai_reasoning="Deep black loamy soil with optimal neutral pH 7.3 and high organic carbon (0.68%). Direct Nira Left Bank canal irrigation security matches Rabi wheat cultivation target.",
                    ai_confidence_score=0.95,
                    model_name="Central AI - GPToFarmerRecommendationModel",
                    model_version="v1.0.0-prototype",
                    ai_factors={
                        "soil_type": "Deep Black Loamy Soil",
                        "ph_level": 7.3,
                        "nitrogen_kg_ha": 260.0,
                        "phosphorus_kg_ha": 38.0,
                        "potassium_kg_ha": 290.0,
                        "organic_carbon_pct": 0.68,
                        "irrigation_source": "Nira Left Bank Canal",
                        "soil_test_doc_url": "/uploads/soil_reports/soil_health_card_KS-FMR-1001.svg",
                        "historical_yield_kg": 9200.0,
                        "allocated_share_pct": 77.8,
                    },
                    review_status="APPROVED",
                    human_final_crop="Wheat (Lokwan)",
                    human_final_area_acres=3.5,
                    human_final_quantity_quintals=70.0,
                    human_final_priority="HIGH",
                    reviewed_by="gram_panchayat",
                    reviewed_at=datetime(2026, 9, 9, 14, 30),
                    human_review_notes="Approved as recommended. Soil health card verified.",
                ),
                AIFarmerRecommendationRecord(
                    recommendation_code="REC-FMR-2026-0002",
                    batch_code="BATCH-FRA-2026-001",
                    gp_allocation_id=1,
                    panchayat_samiti_name="Baramati Block Panchayat Samiti",
                    gp_code="GP-BMT-01",
                    gp_name="Shirsuphal Gram Panchayat",
                    farmer_id="KS-FMR-1002",
                    farmer_name="Dattatray Keshav Jagtap",
                    survey_number="Gat No. 45/2",
                    village_name="Shirsuphal",
                    crop_name="Wheat (Lokwan)",
                    season="Rabi 2026",
                    target_year=2026,
                    farmer_total_land_acres=6.0,
                    farmer_available_land_acres=6.0,
                    ai_recommended_area_acres=4.5,
                    ai_recommended_quantity_quintals=90.0,
                    ai_suitability="HIGH",
                    ai_priority="HIGH",
                    ai_reasoning="Medium deep black cotton soil with high canal water availability. Suitable for high-density Lokwan wheat seed drill sowing.",
                    ai_confidence_score=0.93,
                    model_name="Central AI - GPToFarmerRecommendationModel",
                    model_version="v1.0.0-prototype",
                    ai_factors={
                        "soil_type": "Medium Deep Black Cotton Soil",
                        "ph_level": 7.4,
                        "nitrogen_kg_ha": 245.0,
                        "phosphorus_kg_ha": 32.0,
                        "potassium_kg_ha": 280.0,
                        "organic_carbon_pct": 0.62,
                        "irrigation_source": "Canal Lift Irrigation",
                        "soil_test_doc_url": "/uploads/soil_reports/soil_health_card_KS-FMR-1001.svg",
                        "allocated_share_pct": 75.0,
                    },
                    review_status="PENDING_REVIEW",
                ),
                AIFarmerRecommendationRecord(
                    recommendation_code="REC-FMR-2026-0003",
                    batch_code="BATCH-FRA-2026-001",
                    gp_allocation_id=1,
                    panchayat_samiti_name="Baramati Block Panchayat Samiti",
                    gp_code="GP-BMT-01",
                    gp_name="Shirsuphal Gram Panchayat",
                    farmer_id="KS-FMR-1003",
                    farmer_name="Anil R. Shinde",
                    survey_number="Gat No. 19/1",
                    village_name="Shirsuphal",
                    crop_name="Wheat (Lokwan)",
                    season="Rabi 2026",
                    target_year=2026,
                    farmer_total_land_acres=5.8,
                    farmer_available_land_acres=5.8,
                    ai_recommended_area_acres=4.0,
                    ai_recommended_quantity_quintals=80.0,
                    ai_suitability="HIGH",
                    ai_priority="HIGH",
                    ai_reasoning="Strong nitrogen-potash balance in soil parcel with borewell and canal dual-source irrigation.",
                    ai_confidence_score=0.92,
                    model_name="Central AI - GPToFarmerRecommendationModel",
                    model_version="v1.0.0-prototype",
                    ai_factors={
                        "soil_type": "Medium Deep Black Cotton Soil",
                        "ph_level": 7.3,
                        "nitrogen_kg_ha": 260.0,
                        "phosphorus_kg_ha": 38.0,
                        "potassium_kg_ha": 290.0,
                        "organic_carbon_pct": 0.68,
                        "irrigation_source": "CANAL",
                        "soil_test_doc_url": "/uploads/soil_reports/soil_health_card_KS-FMR-1001.svg",
                        "allocated_share_pct": 69.0,
                    },
                    review_status="CORRECTED",
                    human_final_crop="Wheat (Lokwan)",
                    human_final_area_acres=3.5,
                    human_final_quantity_quintals=70.0,
                    human_final_priority="HIGH",
                    reviewed_by="gram_panchayat",
                    reviewed_at=datetime(2026, 9, 9, 15, 10),
                    correction_reason="Adjusted downward to 3.5 acres to reserve 2.3 acres for multi-cut green fodder clover cultivation.",
                    human_review_notes="Farmer requested parcel split for dairy fodder rotation.",
                ),
            ])
            db.commit()

        # 10. Seed Major Warehouse AI Quality Grading Records (Task 5 Dual-Storage)
        if db.query(AIMajorWarehouseGradingRecord).count() == 0:
            wh_grading = AIMajorWarehouseGradingRecord(
                grading_code="GRD-1001-0001",
                batch_id="KS-BATCH-1001",
                farmer_id="KS-FMR-1001",
                farmer_name="Ramesh Narayan Patil",
                crop_name="Wheat (Lokwan)",
                warehouse_id="MWH-PUN-01",
                warehouse_name="Pune Central Silo Complex",
                net_weight_kg=9150.0,
                image_url="/uploads/grain_samples/KS-BATCH-1001_sample.svg",
                ai_score=86.0,
                ai_grade="A",
                ai_confidence=0.94,
                ai_quality_factors={
                    "1_size": {"name": "Size & Screen Uniformity", "value": "6.8 mm (94.2% screen retention)", "status": "PASS", "type": "VISUAL_OPTICAL"},
                    "2_shape": {"name": "Shape & Kernel Symmetry", "value": "Ovate Conformant (Length/Width ratio: 2.3)", "status": "PASS", "type": "VISUAL_OPTICAL"},
                    "3_colour_and_appearance": {"name": "Colour & Visual Appearance", "value": "Amber Gold, Lustrous", "status": "PASS", "type": "VISUAL_OPTICAL"},
                    "4_visible_defects": {"name": "Visible Defects", "value": "1.7% total visual defects", "status": "PASS", "type": "VISUAL_OPTICAL"},
                    "5_cuts": {"name": "Mechanical / Thresher Cuts", "value": "None detected", "status": "PASS", "type": "VISUAL_OPTICAL"},
                    "6_cracks": {"name": "Kernel Stress Cracks", "value": "None detected", "status": "PASS", "type": "VISUAL_OPTICAL"},
                    "7_bruises": {"name": "Handling / Impact Bruises", "value": "None detected", "status": "PASS", "type": "VISUAL_OPTICAL"},
                    "8_spots": {"name": "Discoloration / Fungal Spots", "value": "None detected", "status": "PASS", "type": "VISUAL_OPTICAL"},
                    "9_pest_disease_damage": {"name": "Pest & Disease Damage", "value": "0.2% weevil/insect damage", "status": "PASS", "type": "VISUAL_OPTICAL"},
                    "10_foreign_materials": {"name": "Foreign Materials (Chaff/Straw)", "value": "2.8% chaff and non-grain particles", "status": "ATTENTION", "type": "VISUAL_OPTICAL"},
                    "11_dirt_stones_leaves": {"name": "Dirt, Stones & Organic Debris", "value": "< 0.1% mineral debris detected", "status": "PASS", "type": "VISUAL_OPTICAL"},
                    "12_crop_specific_visual_quality": {"name": "Crop-Specific Visual Factor", "value": "93.5% Vitreous Hard Endosperm", "status": "PASS", "type": "VISUAL_OPTICAL"},
                    "physical_moisture": {
                        "name": "Moisture Content (%)",
                        "value": "11.3%",
                        "status": "OPTIMAL",
                        "type": "PHYSICAL_MEASUREMENT",
                        "notice": "Requires physical/manual measurement (e.g. calibrated digital moisture probe meter)"
                    },
                    "physical_weight": {
                        "name": "Certified Net Weight (kg)",
                        "value": "9,150.0 kg",
                        "status": "CONFIRMED",
                        "type": "PHYSICAL_MEASUREMENT",
                        "notice": "Requires physical/manual measurement (e.g. certified weighbridge platform scale)"
                    }
                },
                ai_warnings=["Visual defect check: elevated foreign grain matter detected (2.8%)."],
                ai_reasoning="Central AI vision analyzed Lokwan Wheat sample for Batch KS-BATCH-1001. Score 86.0/100, Suggested Grade A. Human inspector inspection confirmed Grade B adjustment.",
                model_name="Central AI - CropQualityVisionModel",
                model_version="v1.0.0-prototype",
                prototype_disclaimer="Prototype AI model — requires real crop image training dataset for production accuracy.",
                review_status="CORRECTED",
                human_final_score=78.0,
                human_final_grade="B",
                reviewed_by="major_warehouse",
                reviewed_at=datetime(2026, 9, 8, 11, 30),
                correction_reason="Visual inspection detected 2.8% foreign grain matter. Downgraded from AI prediction A to Grade B.",
                human_notes="Standard commercial intake accepted into Silo Bay B-2.",
            )
            db.add(wh_grading)
            db.commit()

        print("Comprehensive operational records and initial audit history seeded successfully.")
    except Exception as exc:
        db.rollback()
        print(f"Error seeding database records: {exc}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_db(seed=True)
