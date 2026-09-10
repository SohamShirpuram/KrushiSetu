from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class CropRequirementPredictRequest(BaseModel):
    crop_name: Optional[str] = Field("Sugarcane", description="Target agricultural crop name")
    season: Optional[str] = Field("Kharif 2026", description="Target agricultural season")
    region: Optional[str] = Field("Baramati Block Panchayat Samiti", description="Target administrative block or region")

class ApprovePredictionRequest(BaseModel):
    notes: Optional[str] = Field("Approved without adjustment by Food Directorate", description="Officer sign-off notes")

class CorrectPredictionRequest(BaseModel):
    human_final_crop: Optional[str] = Field(None, description="Corrected crop name if changed")
    human_final_quantity_mt: float = Field(..., description="Corrected target quantity in Metric Tonnes (MT)")
    human_final_priority: Optional[str] = Field(None, description="Corrected priority: NORMAL, HIGH, or CRITICAL")
    correction_reason: str = Field(..., min_length=3, description="Mandatory official justification for overriding AI baseline")

class AIPredictionResponse(BaseModel):
    id: int
    prediction_id: str
    module_name: str
    model_name: str
    model_version: str
    input_data_reference: Dict[str, Any]
    ai_recommended_crop: str
    ai_recommended_quantity: float
    ai_priority: str
    ai_reasoning: str
    ai_factors: Dict[str, Any]
    ai_confidence: float
    suitable_region: str
    generated_at: Optional[str] = None
    review_status: str
    human_final_crop: Optional[str] = None
    human_final_quantity: Optional[float] = None
    human_final_priority: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    correction_reason: Optional[str] = None
    created_at: Optional[str] = None

class AIEngineStatsResponse(BaseModel):
    engine_status: str
    model_version: str
    total_predictions: int
    pending_reviews: int
    approved_predictions: int
    human_corrections: int
    active_modules: List[str]

# --- PANCHAYAT SAMITI -> GRAM PANCHAYAT AI ALLOCATION SCHEMAS ---

class GPAllocationPredictRequest(BaseModel):
    crop_name: str = Field(..., example="Wheat (Lokwan)", description="Target crop to allocate across Gram Panchayats")
    season: str = Field(..., example="Rabi 2026", description="Target agricultural season")
    total_quota_mt: float = Field(..., gt=0, example=12000.0, description="Approved Food Department quota in Metric Tonnes (MT)")
    panchayat_samiti_name: Optional[str] = Field("Baramati Block Panchayat Samiti", description="Jurisdiction Panchayat Samiti")
    fd_requirement_id: Optional[int] = Field(None, description="Reference Food Department Requirement or PS Allocation ID")
    priority: Optional[str] = Field("HIGH", description="Priority level: NORMAL, HIGH, or CRITICAL")
    target_year: Optional[int] = Field(2026, description="Target calendar year")

class ApproveGPAllocationRequest(BaseModel):
    notes: Optional[str] = Field("Approved without adjustment by Panchayat Samiti BDO", description="Officer review notes")

class CorrectGPAllocationRequest(BaseModel):
    human_final_quantity_mt: float = Field(..., gt=0, description="Human adjusted quota in Metric Tonnes (MT)")
    human_final_priority: Optional[str] = Field(None, description="Adjusted priority level: NORMAL, HIGH, or CRITICAL")
    correction_reason: str = Field(..., min_length=5, description="Mandatory operational justification for modifying AI recommendation")
    notes: Optional[str] = Field(None, description="Additional administrative remarks")

class AIGPAllocationResponse(BaseModel):
    id: int
    allocation_code: str
    batch_code: str
    fd_requirement_id: Optional[int] = None
    panchayat_samiti_name: str
    gp_code: str
    gp_name: str
    crop_name: str
    season: str
    target_year: int
    agricultural_area_ha: Optional[float] = None
    active_farmers_count: int = 0
    ai_recommended_quantity_mt: float
    ai_priority: str
    ai_suitability: str
    ai_reasoning: Optional[str] = None
    ai_confidence_score: float
    model_name: str
    model_version: str
    ai_factors: Dict[str, Any] = {}
    review_status: str
    human_final_quantity_mt: Optional[float] = None
    human_final_priority: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    correction_reason: Optional[str] = None
    human_review_notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class AIGPAllocationBatchResponse(BaseModel):
    batch_code: str
    crop_name: str
    season: str
    panchayat_samiti_name: str
    total_quota_mt: float
    total_ai_allocated_mt: float
    remaining_quota_mt: float
    gp_count: int
    allocations: List[AIGPAllocationResponse]


# --- GRAM PANCHAYAT -> FARMER-WISE AI RECOMMENDATION SCHEMAS ---

class FarmerRecommendationPredictRequest(BaseModel):
    crop_name: str = Field(..., example="Wheat (Lokwan)", description="Crop to allocate to farmers")
    season: str = Field(..., example="Rabi 2026", description="Agricultural season")
    gp_name: Optional[str] = Field("Shirsuphal Gram Panchayat", description="Jurisdiction Gram Panchayat")
    gp_code: Optional[str] = Field("GP-BMT-01", description="Gram Panchayat registry code")
    panchayat_samiti_name: Optional[str] = Field("Baramati Block Panchayat Samiti", description="Block Panchayat Samiti")
    gp_allocation_id: Optional[int] = Field(None, description="Reference approved PS-to-GP allocation record ID")
    gp_target_quota_mt: Optional[float] = Field(None, gt=0, description="Approved GP requirement quota in MT")
    priority: Optional[str] = Field("HIGH", description="Priority level: NORMAL, HIGH, CRITICAL")
    target_year: Optional[int] = Field(2026, description="Target calendar year")

class ApproveFarmerRecommendationRequest(BaseModel):
    notes: Optional[str] = Field("Approved without adjustment by Gram Panchayat Sarpanch/Secretary", description="Reviewer notes")

class CorrectFarmerRecommendationRequest(BaseModel):
    human_final_crop: Optional[str] = Field(None, description="Adjusted crop name if changed")
    human_final_area_acres: float = Field(..., gt=0, description="Human adjusted cultivation parcel in Acres")
    human_final_quantity_quintals: Optional[float] = Field(None, gt=0, description="Expected production in Quintals")
    human_final_priority: Optional[str] = Field(None, description="Adjusted priority level")
    correction_reason: Optional[str] = Field(None, description="Mandatory operational justification for modifying AI recommendation")
    justification: Optional[str] = Field(None, description="Alternative field for operational justification")
    notes: Optional[str] = Field(None, description="Additional administrative remarks")

class AIFarmerRecommendationResponse(BaseModel):
    id: int
    recommendation_code: str
    batch_code: str
    gp_allocation_id: Optional[int] = None
    panchayat_samiti_name: str
    gp_code: str
    gp_name: str
    farmer_id: str
    farmer_name: str
    survey_number: Optional[str] = None
    village_name: Optional[str] = None
    crop_name: str
    season: str
    target_year: int
    farmer_total_land_acres: float
    farmer_available_land_acres: float
    ai_recommended_area_acres: float
    ai_recommended_quantity_quintals: float
    ai_suitability: str
    ai_priority: str
    ai_reasoning: Optional[str] = None
    ai_confidence_score: float
    model_name: str
    model_version: str
    ai_factors: Dict[str, Any] = {}
    review_status: str
    soil_report_url: Optional[str] = None
    soil_ph: Optional[float] = None
    soil_type: Optional[str] = None
    irrigation_source: Optional[str] = None
    nitrogen_kg_ha: Optional[float] = None
    organic_carbon_pct: Optional[float] = None
    suitability_score: Optional[float] = None
    ai_rationale: Optional[str] = None
    gp_approved_quota_mt: Optional[float] = None
    human_final_crop: Optional[str] = None
    human_final_area_acres: Optional[float] = None
    human_final_quantity_quintals: Optional[float] = None
    human_final_priority: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    correction_reason: Optional[str] = None
    human_review_notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class AIFarmerRecommendationBatchResponse(BaseModel):
    batch_code: str
    crop_name: str
    season: str
    gp_name: str
    gp_approved_quota_mt: float
    total_ai_allocated_acres: float
    total_ai_allocated_quintals: float
    total_ai_allocated_mt: float
    remaining_quota_mt: float
    total_available_land_acres: float
    remaining_land_acres: float
    farmer_count: int
    recommendations: List[AIFarmerRecommendationResponse]

# --- TASK 5: MAJOR WAREHOUSE AI QUALITY & GRADING SCHEMAS ---

class WarehouseGradingAnalyzeRequest(BaseModel):
    batch_id: str = Field(..., description="Active intake batch ID, e.g. KS-BATCH-1001")
    crop_name: Optional[str] = Field(None, description="Crop variety (e.g. Wheat (Lokwan), Sugarcane, Cotton)")
    farmer_id: Optional[str] = Field(None, description="Supplying farmer ID (e.g. KS-FMR-1001)")
    farmer_name: Optional[str] = Field(None, description="Supplying farmer name")
    warehouse_id: Optional[str] = Field("MWH-PUN-01", description="Major warehouse ID")
    net_weight_kg: Optional[float] = Field(None, description="Certified intake net weight in kg")
    image_data: Optional[str] = Field(None, description="Base64 data URL or relative image URL of captured grain frame")
    
    # Manual physical measurements (explicitly segregated from optical vision parameters)
    manual_moisture_pct: Optional[float] = Field(None, description="Physical probe moisture percentage (e.g. 11.2%)")
    manual_foreign_matter_pct: Optional[float] = Field(None, description="Foreign material percentage (straw, chaff)")
    manual_broken_grain_pct: Optional[float] = Field(None, description="Broken kernel percentage")
    manual_damaged_grain_pct: Optional[float] = Field(None, description="Insect or weevil damaged grain percentage")
    
    # Optical defect inspection overrides
    has_cuts: Optional[bool] = Field(False, description="Surface cuts or mechanical thresher cuts detected")
    has_cracks: Optional[bool] = Field(False, description="Kernel stress cracks detected")
    has_spots: Optional[bool] = Field(False, description="Discoloration / fungal spotting detected")
    has_bruises: Optional[bool] = Field(False, description="Impact or handling bruises detected")
    has_pest_damage: Optional[bool] = Field(False, description="Visible insect / pest damage detected")

class ApproveWarehouseGradingRequest(BaseModel):
    notes: Optional[str] = Field("Approved without modification by Major Warehouse inspector", description="Inspector approval remarks")

class CorrectWarehouseGradingRequest(BaseModel):
    human_final_grade: str = Field(..., description="Human finalized grade: 'A', 'B', 'C', or 'REJECTED'")
    human_final_score: float = Field(..., ge=0.0, le=100.0, description="Human finalized quality score (0 - 100)")
    correction_reason: str = Field(..., min_length=5, description="Mandatory official justification for overriding AI baseline (minimum 5 characters)")
    notes: Optional[str] = Field(None, description="Additional inspection or storage instructions")

class AIWarehouseGradingResponse(BaseModel):
    id: int
    grading_code: str
    batch_id: str
    intake_id: Optional[int] = None
    farmer_id: str
    farmer_name: str
    crop_name: str
    warehouse_id: str
    warehouse_name: str
    net_weight_kg: Optional[float] = None
    image_url: Optional[str] = None
    ai_score: float
    ai_grade: str
    ai_confidence: float
    ai_quality_factors: Dict[str, Any] = {}
    ai_warnings: List[str] = []
    ai_reasoning: Optional[str] = None
    model_name: str
    model_version: str
    prototype_disclaimer: str
    review_status: str
    human_final_score: Optional[float] = None
    human_final_grade: Optional[str] = None
    effective_final_grade: str
    effective_final_score: float
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    correction_reason: Optional[str] = None
    human_notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class AIWarehouseGradingListResponse(BaseModel):
    items: List[AIWarehouseGradingResponse]
    total: int


# --- TASK 6: MAJOR WAREHOUSE STORAGE, INVENTORY & AI STOCK INTELLIGENCE SCHEMAS ---

class CreateWarehouseStorageRequest(BaseModel):
    storage_id: Optional[str] = Field(None, description="Unique storage record ID (e.g. KS-STR-8001, auto-generated if empty)")
    batch_id: str = Field(..., description="Certified intake batch ID (e.g. KS-BATCH-1001)")
    warehouse_id: Optional[str] = Field("MWH-PUN-01", description="Major warehouse identifier")
    warehouse_name: Optional[str] = Field("Pune Central Major Warehouse", description="Warehouse facility name")
    farmer_id: Optional[str] = Field(None, description="Supplying farmer ID (e.g. KS-FMR-1001)")
    farmer_name: Optional[str] = Field(None, description="Supplying farmer name")
    crop_name: str = Field(..., description="Crop variety (e.g. Wheat (Lokwan), Soybean (JS-335))")
    crop_category: Optional[str] = Field("Grains", description="Crop category: Grains, Vegetables, Fruits")
    quantity_kg: float = Field(..., gt=0, description="Certified intake quantity received into storage in kg")
    reserved_quantity_kg: Optional[float] = Field(0.0, ge=0, description="Quantity reserved for orders/allocations in kg")
    dispatched_quantity_kg: Optional[float] = Field(0.0, ge=0, description="Quantity already dispatched in kg")
    storage_section: Optional[str] = Field("SILO-A-01", description="Silo, bin, or bay location")
    storage_type: Optional[str] = Field("Silo Storage", description="Silo Storage, Cold Storage, Dry Warehouse, Pallet Rack")
    storage_status: Optional[str] = Field("Stored", description="Stored, Reserved, Dispatched, Partially Dispatched, Completed")
    storage_date: Optional[str] = Field(None, description="Entry timestamp (ISO string)")
    expiry_date: Optional[str] = Field(None, description="Estimated expiry / safe storage date")
    temperature_celsius: Optional[float] = Field(None, description="Storage ambient temperature in °C")
    humidity_percentage: Optional[float] = Field(None, description="Storage ambient relative humidity in %")
    movement_type: Optional[str] = Field("INTAKE_STORAGE", description="INTAKE_STORAGE, INTERNAL_TRANSFER, DISPATCH_PICK, COMPLETED")
    notes: Optional[str] = Field(None, description="Storage and handling remarks")

class UpdateWarehouseStorageRequest(BaseModel):
    storage_section: Optional[str] = Field(None, description="Updated section / silo location")
    storage_type: Optional[str] = Field(None, description="Updated storage type")
    storage_status: Optional[str] = Field(None, description="Updated storage status")
    reserved_quantity_kg: Optional[float] = Field(None, ge=0, description="Set new reserved quantity in kg")
    dispatched_quantity_kg: Optional[float] = Field(None, ge=0, description="Set absolute dispatched quantity in kg")
    dispatch_increment_kg: Optional[float] = Field(None, gt=0, description="Incremental quantity to dispatch now (added to dispatched_quantity_kg)")
    temperature_celsius: Optional[float] = Field(None, description="Updated temperature in °C")
    humidity_percentage: Optional[float] = Field(None, description="Updated humidity in %")
    movement_type: Optional[str] = Field(None, description="Updated movement type")
    notes: Optional[str] = Field(None, description="Updated storage notes")
    edit_reason: Optional[str] = Field(None, description="Mandatory audit justification when editing storage details")
    edited_by: Optional[str] = Field("Warehouse Supervisor", description="User identity performing edit")

class StorageRecordResponse(BaseModel):
    id: int
    storage_id: str
    batch_id: str
    warehouse_id: str
    warehouse_name: str
    farmer_id: Optional[str] = None
    farmer_name: Optional[str] = None
    crop_name: str
    crop_category: str
    quantity_kg: float
    reserved_quantity_kg: float
    dispatched_quantity_kg: float
    current_stock_kg: float
    available_quantity_kg: float
    storage_section: Optional[str] = None
    storage_type: Optional[str] = None
    storage_status: str
    storage_date: Optional[str] = None
    expiry_date: Optional[str] = None
    temperature_celsius: Optional[float] = None
    humidity_percentage: Optional[float] = None
    movement_type: Optional[str] = None
    quality_grade: Optional[str] = None
    quality_score: Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class StorageRecordListResponse(BaseModel):
    items: List[StorageRecordResponse]
    total: int

class WarehouseInventoryItem(BaseModel):
    crop_name: str
    crop_category: str
    total_received_kg: float
    total_dispatched_kg: float
    total_reserved_kg: float
    current_stock_kg: float
    available_stock_kg: float
    batches_count: int
    batch_ids: List[str]
    grades_breakdown: Dict[str, float] = {}
    storage_sections: List[str] = []
    status: str
    ai_run_rate_kg_day: Optional[str] = None
    ai_buffer_coverage_days: Optional[str] = None

class WarehouseInventorySummary(BaseModel):
    warehouse_id: str
    warehouse_name: str
    total_inventory_kg: float
    total_reserved_kg: float
    total_dispatched_kg: float
    total_available_kg: float
    crop_count: int
    items: List[WarehouseInventoryItem]
    categories_summary: Dict[str, float] = {}

class AIStockInsightsResponse(BaseModel):
    model_name: str
    model_version: str
    disclaimer: str
    status: str
    is_sparse_data: bool
    sparse_data_notice: Optional[str] = None
    overall_stock_status: str
    crop_insights: List[Dict[str, Any]]
    storage_utilization_pct: float
    generated_at: str

class AIStockRecommendationResponse(BaseModel):
    model_name: str
    model_version: str
    recommendations: List[Dict[str, Any]]
    alerts: List[str]
    generated_at: str


# --- TASK 7: MAJOR WAREHOUSE -> MINOR WAREHOUSE DISPATCH & TRUCK TRACKING SCHEMAS ---

class CreateDispatchPlanRequest(BaseModel):
    dispatch_id: Optional[str] = Field(None, description="Unique dispatch code (e.g. KS-DSP-7001, auto-generated if empty)")
    batch_id: str = Field(..., description="Certified arrival batch ID (e.g. KS-BATCH-1001)")
    storage_id: Optional[str] = Field(None, description="Source storage record ID (e.g. KS-STR-8001)")
    crop_name: str = Field(..., description="Crop variety (e.g. Wheat (Lokwan))")
    final_grade: Optional[str] = Field(None, description="Quality grade certified from Task 5 (e.g. Grade A)")
    dispatch_quantity_kg: float = Field(..., gt=0, description="Quantity to dispatch in kg (must not exceed available stock)")
    origin_warehouse: Optional[str] = Field("Pune Central Major Warehouse", description="Origin Major Warehouse name")
    origin_warehouse_id: Optional[str] = Field("MWH-PUN-01", description="Origin Major Warehouse facility ID")
    destination_minor_warehouse: str = Field(..., description="Destination Minor Warehouse / Godown name (e.g. Baramati APMC Godown No. 3)")
    destination_minor_warehouse_id: Optional[str] = Field("MIN-BMT-01", description="Destination Minor Warehouse facility ID")
    truck_id: Optional[str] = Field("TRK-001", description="Assigned transport vehicle ID")
    truck_number: str = Field(..., description="Vehicle registration number (e.g. MH-12-Q-4521)")
    driver_id: Optional[str] = Field("DRV-001", description="Assigned driver ID")
    driver_name: str = Field(..., description="Driver full name")
    driver_phone: Optional[str] = Field(None, description="Driver mobile contact phone")
    dispatch_date: Optional[str] = Field(None, description="Dispatch date (YYYY-MM-DD)")
    departure_time: Optional[str] = Field("10:30 AM", description="Planned/actual departure time")
    expected_arrival: Optional[str] = Field("02:30 PM", description="Estimated arrival time (ETA)")
    notes: Optional[str] = Field(None, description="Logistics notes / handling instructions")

class UpdateDispatchRequest(BaseModel):
    truck_id: Optional[str] = Field(None, description="Updated vehicle ID")
    truck_number: Optional[str] = Field(None, description="Updated vehicle registration number")
    driver_id: Optional[str] = Field(None, description="Updated driver ID")
    driver_name: Optional[str] = Field(None, description="Updated driver full name")
    driver_phone: Optional[str] = Field(None, description="Updated driver mobile phone")
    expected_arrival: Optional[str] = Field(None, description="Updated ETA")
    destination_minor_warehouse: Optional[str] = Field(None, description="Updated destination godown")
    departure_time: Optional[str] = Field(None, description="Updated departure time")
    status: Optional[str] = Field(None, description="Updated dispatch status")
    delivery_status: Optional[str] = Field(None, description="Updated transit delivery status")
    notes: Optional[str] = Field(None, description="Updated dispatch notes")
    edit_reason: Optional[str] = Field(None, description="Mandatory audit justification for editing dispatch details")
    edited_by: Optional[str] = Field("Logistics Officer", description="User identity performing edit")

class StartDispatchTransitRequest(BaseModel):
    departure_time: Optional[str] = Field(None, description="Actual gate departure timestamp")
    initial_location: Optional[str] = Field("Pune Hub Outward Gate", description="Starting location")
    notes: Optional[str] = Field(None, description="Gate exit remarks")

class UpdateGPSLocationRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Driver mobile GPS latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Driver mobile GPS longitude")
    current_location: Optional[str] = Field(None, description="Human-readable location or highway landmark")
    location_name: Optional[str] = Field(None, description="Human-readable location or highway landmark")
    driver_id: Optional[str] = Field(None, description="Driver identifier")

class ReceiveMinorWarehouseDispatchRequest(BaseModel):
    received_quantity_kg: float = Field(..., ge=0, description="Actual physical verified weight received at Minor Warehouse in kg")
    arrival_time: Optional[str] = Field(None, description="Actual arrival timestamp or time string")
    receiver_name: Optional[str] = Field("Minor Warehouse Manager", description="Receiving officer full name")
    discrepancy_reason: Optional[str] = Field(None, description="Mandatory reason if sent and received weights differ")
    notes: Optional[str] = Field(None, description="Unloading remarks and godown bay assignment")

class DispatchRecordResponse(BaseModel):
    id: int
    dispatch_id: str
    batch_id: str
    crop_name: str
    final_grade: str
    dispatch_quantity_kg: float
    sent_quantity_kg: float
    origin_warehouse: str
    origin_warehouse_id: str
    destination_minor_warehouse: str
    destination_minor_warehouse_id: str
    truck_id: Optional[str] = None
    truck_number: str
    driver_id: Optional[str] = None
    driver_name: str
    driver_phone: Optional[str] = None
    dispatch_date: str
    departure_time: Optional[str] = None
    expected_arrival: Optional[str] = None
    actual_arrival: Optional[str] = None
    status: str
    delivery_status: str
    current_location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    last_gps_update: Optional[str] = None
    is_gps_active: bool
    google_maps_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class DispatchRecordListResponse(BaseModel):
    dispatches: List[DispatchRecordResponse]
    total: int

class TruckRegistryResponse(BaseModel):
    id: int
    truck_id: str
    vehicle_number: str
    vehicle_type: str
    capacity_mt: float
    driver_name: str
    driver_phone: Optional[str] = None
    driver_id: Optional[str] = None
    current_status: str
    current_dispatch_id: Optional[str] = None
    origin_base: str
    destination: Optional[str] = None
    last_location: Optional[str] = None
    last_latitude: Optional[float] = None
    last_longitude: Optional[float] = None
    last_gps_update: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class CreateTruckRequest(BaseModel):
    truck_id: Optional[str] = Field(None, description="Unique vehicle ID (e.g. TRK-004, auto if empty)")
    vehicle_number: str = Field(..., description="Vehicle registration number (e.g. MH-12-AB-1234)")
    vehicle_type: Optional[str] = Field("16-Wheeler Heavy Grain Carrier", description="Vehicle type classification")
    capacity_mt: Optional[float] = Field(25.0, gt=0, description="Gross carrying capacity in MT")
    driver_name: str = Field(..., description="Driver full name")
    driver_phone: Optional[str] = Field(None, description="Driver mobile contact phone")
    driver_id: Optional[str] = Field(None, description="Driver ID code")
    current_status: Optional[str] = Field("AVAILABLE", description="Vehicle status: AVAILABLE, IN_TRANSIT, etc.")
    origin_base: Optional[str] = Field("Pune Central Major Silo Hub", description="Home base logistics depot")
    last_location: Optional[str] = Field("Pune Hub Logistics Yard", description="Initial location")
    last_latitude: Optional[float] = Field(18.5204, description="Initial latitude")
    last_longitude: Optional[float] = Field(73.8567, description="Initial longitude")

class DispatchTrackingResponse(BaseModel):
    dispatch_id: str
    batch_id: str
    crop_name: str
    final_grade: str
    sent_quantity_kg: float
    truck_id: Optional[str] = None
    truck_number: str
    driver_name: str
    driver_phone: Optional[str] = None
    origin_warehouse: str
    destination_minor_warehouse: str
    departure_time: Optional[str] = None
    expected_arrival: Optional[str] = None
    actual_arrival: Optional[str] = None
    delivery_status: str
    status: Optional[str] = None
    is_gps_active: bool
    current_location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    last_gps_update: Optional[str] = None
    google_maps_url: Optional[str] = None
    gps_available: Optional[bool] = None
    tracking_notice: Optional[str] = None
    notes: Optional[str] = None




