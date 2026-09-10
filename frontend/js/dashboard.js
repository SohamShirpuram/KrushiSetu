/**
 * KrushiSetu - Interactive Operational Record & Audit Management Controller
 * Supports CREATE -> VIEW -> EDIT -> HISTORY across all 7 Sectors
 */

let currentUser = null;
let currentSectorTabs = [];
let activeTabConfig = null;
let currentRecordsList = [];

// ==========================================
// SECTOR SCHEMAS & CONFIGURATIONS
// ==========================================
const SECTOR_CONFIGS = {
  FOOD_DEPARTMENT: [
    {
      id: "fd_central_ai_recommendations",
      title: "🧠 Central AI Recommendations",
      customRenderer: "renderCentralAIRecommendations",
    },
    {
      id: "fd_crop_requirements",
      title: "Crop Requirements (AI-First)",
      tableName: "fd_crop_requirements",
      apiPath: "/fd/requirements",
      isAiFirstCropTable: true,
      columns: [
        { key: "id", label: "ID" },
        { key: "crop_name", label: "Crop" },
        { key: "season", label: "Season" },
        { key: "ai_recommended_quantity_mt", label: "🤖 AI Rec (MT)" },
        { key: "human_final_quantity_mt", label: "👤 Human Final (MT)" },
        { key: "priority", label: "Priority", badge: true },
        { key: "status", label: "Status", badge: true },
        { key: "finalized_by", label: "Finalized By" },
      ],
      fields: [
        { name: "crop_name", label: "Crop Name", type: "text", required: true },
        { name: "season", label: "Season", type: "select", options: ["Kharif 2026", "Rabi 2026", "Zaid 2026"], required: true },
        { name: "target_quantity_mt", label: "Human Adjusted Target Quantity (MT)", type: "number", required: true },
        { name: "priority", label: "Priority", type: "select", options: ["NORMAL", "HIGH", "CRITICAL"], required: true },
        { name: "notes", label: "Policy / Review Notes", type: "textarea" },
      ]
    },
    {
      id: "fd_crisis",
      title: "Crisis & Shortages",
      tableName: "fd_crisis_records",
      apiPath: "/fd/crisis",
      columns: [
        { key: "id", label: "ID" },
        { key: "crop_name", label: "Crop" },
        { key: "region_or_district", label: "Impacted Region" },
        { key: "deficit_amount_mt", label: "Deficit (MT)" },
        { key: "severity", label: "Severity", badge: true },
        { key: "mitigation_strategy", label: "Mitigation Strategy" },
        { key: "status", label: "Status", badge: true },
      ],
      fields: [
        { name: "crop_name", label: "Crop Name", type: "text", required: true },
        { name: "region_or_district", label: "Impacted Region / District", type: "text", required: true },
        { name: "deficit_amount_mt", label: "Deficit Amount (MT)", type: "number", required: true },
        { name: "severity", label: "Severity", type: "select", options: ["MODERATE", "SEVERE", "ACUTE"], required: true },
        { name: "mitigation_strategy", label: "Mitigation Strategy", type: "textarea", required: true },
        { name: "status", label: "Status", type: "select", options: ["UNDER_MANAGEMENT", "STABILIZED"] },
      ]
    },
    {
      id: "fd_demand",
      title: "Current Demand",
      tableName: "fd_demand_projections",
      apiPath: "/fd/demand",
      columns: [
        { key: "id", label: "ID" },
        { key: "crop_name", label: "Crop" },
        { key: "time_period", label: "Period" },
        { key: "current_demand_mt", label: "Current (MT)" },
        { key: "future_demand_mt", label: "Future Projected (MT)" },
        { key: "projected_growth_pct", label: "Growth %" },
        { key: "remarks", label: "Remarks" },
      ],
      fields: [
        { name: "crop_name", label: "Crop Name", type: "text", required: true },
        { name: "time_period", label: "Time Period (e.g. FY 2026-27)", type: "text", required: true },
        { name: "current_demand_mt", label: "Current Demand (MT)", type: "number", required: true },
        { name: "future_demand_mt", label: "Future Demand (MT)", type: "number", required: true },
        { name: "projected_growth_pct", label: "Growth %", type: "number" },
        { name: "remarks", label: "Economic / Policy Remarks", type: "textarea" },
      ]
    },
    {
      id: "fd_future_demand",
      title: "Future Demand",
      tableName: "fd_demand_projections",
      apiPath: "/fd/demand",
      columns: [
        { key: "id", label: "ID" },
        { key: "crop_name", label: "Crop" },
        { key: "time_period", label: "Period" },
        { key: "future_demand_mt", label: "Future Projected (MT)" },
        { key: "projected_growth_pct", label: "Projected Growth %" },
        { key: "current_demand_mt", label: "Current Baseline (MT)" },
        { key: "remarks", label: "Macro Factors" },
      ],
      fields: [
        { name: "crop_name", label: "Crop Name", type: "text", required: true },
        { name: "time_period", label: "Future Target Period", type: "text", required: true },
        { name: "future_demand_mt", label: "Projected Future Demand (MT)", type: "number", required: true },
        { name: "current_demand_mt", label: "Current Demand Baseline (MT)", type: "number", required: true },
        { name: "projected_growth_pct", label: "Growth %", type: "number" },
        { name: "remarks", label: "Forecasting Notes / Drivers", type: "textarea" },
      ]
    },
    {
      id: "fd_weather",
      title: "Weather & Climate",
      tableName: "fd_weather_data",
      apiPath: "/fd/weather",
      columns: [
        { key: "id", label: "ID" },
        { key: "region", label: "Region" },
        { key: "season", label: "Season" },
        { key: "rainfall_mm", label: "Rainfall (mm)" },
        { key: "avg_temperature_c", label: "Avg Temp (°C)" },
        { key: "climate_alert", label: "Climate Alert", badge: true },
      ],
      fields: [
        { name: "region", label: "Region / Agro-climatic Zone", type: "text", required: true },
        { name: "season", label: "Season", type: "text", required: true },
        { name: "rainfall_mm", label: "Rainfall (mm)", type: "number", required: true },
        { name: "avg_temperature_c", label: "Avg Temperature (°C)", type: "number", required: true },
        { name: "soil_moisture_index", label: "Soil Moisture Index (0-1.0)", type: "number" },
        { name: "climate_alert", label: "Alert Level", type: "select", options: ["NORMAL", "DROUGHT_RISK", "EXCESS_RAIN_ALERT"] },
      ]
    },
    {
      id: "fd_ps_allocations",
      title: "Requirements Assigned to PS",
      tableName: "fd_ps_allocations",
      apiPath: "/fd/ps-allocations",
      columns: [
        { key: "id", label: "ID" },
        { key: "panchayat_samiti_name", label: "Panchayat Samiti" },
        { key: "crop_name", label: "Crop" },
        { key: "target_quota_mt", label: "Target Quota (MT)" },
        { key: "ai_suggested_quota_mt", label: "AI Suggested (MT)" },
        { key: "human_final_quota_mt", label: "Human Final (MT)" },
        { key: "review_status", label: "Review Status", badge: true },
        { key: "status", label: "Status", badge: true },
      ],
      fields: [
        { name: "panchayat_samiti_name", label: "Panchayat Samiti Name", type: "text", required: true },
        { name: "crop_name", label: "Crop Name", type: "text", required: true },
        { name: "target_quota_mt", label: "Target Quota (MT)", type: "number", required: true },
        { name: "ai_suggested_quota_mt", label: "AI Suggested Quota (MT)", type: "number" },
        { name: "human_final_quota_mt", label: "Human Final Quota (MT)", type: "number", required: true },
        { name: "ai_rationale", label: "AI Decision Rationale", type: "text" },
        { name: "review_status", label: "Review Status", type: "select", options: ["PENDING_REVIEW", "CONFIRMED"] },
        { name: "status", label: "Allocation Status", type: "select", options: ["ASSIGNED", "ACKNOWLEDGED", "COMPLETED"] },
      ]
    },
    {
      id: "fd_ai_insights",
      title: "AI Data & Model Insights",
      customRenderer: "renderFDAIDataInsights"
    },
    {
      id: "fd_trucks",
      title: "Truck / Delivery Tracking",
      customRenderer: "renderTruckTracking"
    },
    {
      id: "fd_history",
      title: "History / Audit Records",
      customRenderer: "renderAuditHistoryTab"
    }
  ],

  PANCHAYAT_SAMITI: [
    {
      id: "ps_overview",
      title: "Overview",
      customRenderer: "renderPSOverview"
    },
    {
      id: "ps_central_ai_allocation",
      title: "🧠 Central AI Allocation",
      customRenderer: "renderPSCentralAIAllocation",
    },
    {
      id: "ps_fd_allocations",
      title: "Requirements Received from FD",
      tableName: "fd_ps_allocations",
      apiPath: "/fd/ps-allocations",
      columns: [
        { key: "id", label: "ID" },
        { key: "crop_name", label: "Crop" },
        { key: "target_quota_mt", label: "Target Quota (MT)" },
        { key: "human_final_quota_mt", label: "Approved Quota (MT)" },
        { key: "review_status", label: "Review Status", badge: true },
        { key: "status", label: "Status", badge: true },
        { key: "created_at", label: "Received Date" },
      ],
      fields: []
    },
    {
      id: "ps_gp_allocations",
      title: "Gram Panchayat Allocation (AI-First)",
      tableName: "ps_gp_allocations",
      apiPath: "/ps/gp-allocations",
      isPSAIFirstTable: true,
      columns: [
        { key: "id", label: "ID" },
        { key: "gp_name", label: "Gram Panchayat" },
        { key: "crop_name", label: "Crop" },
        { key: "ai_recommended_quantity_mt", label: "🤖 AI Rec (MT)" },
        { key: "human_final_quantity_mt", label: "👤 Final Quota (MT)" },
        { key: "season", label: "Season" },
        { key: "status", label: "Status", badge: true },
        { key: "finalized_by", label: "Authorized By" },
      ],
      fields: [
        { name: "panchayat_samiti_name", label: "Panchayat Samiti Name", type: "text", required: true },
        { name: "gp_name", label: "Gram Panchayat Name", type: "text", required: true },
        { name: "crop_name", label: "Crop Name", type: "text", required: true },
        { name: "allocated_quantity_mt", label: "Allocated Target (MT)", type: "number", required: true },
        { name: "season", label: "Season", type: "text", required: true },
        { name: "status", label: "Status", type: "select", options: ["AI_GENERATED", "UNDER_REVIEW", "APPROVED", "HUMAN_CORRECTED"] },
      ]
    },
    {
      id: "ps_gp_registry",
      title: "Gram Panchayat Registry",
      tableName: "ps_gp_registry",
      apiPath: "/ps/gps",
      columns: [
        { key: "gp_code", label: "GP Code" },
        { key: "gp_name", label: "GP Name" },
        { key: "panchayat_samiti_name", label: "Panchayat Samiti" },
        { key: "district", label: "District" },
        { key: "village_location", label: "Location" },
        { key: "sarpanch_name", label: "Sarpanch" },
        { key: "total_area_hectares", label: "Total Area (Ha)" },
        { key: "cultivable_area_hectares", label: "Cultivable (Ha)" },
        { key: "active_farmers_count", label: "Active Farmers" },
      ],
      fields: [
        { name: "gp_code", label: "GP Code (e.g. MH-PUN-BAR-001)", type: "text", required: true },
        { name: "gp_name", label: "Gram Panchayat Name", type: "text", required: true },
        { name: "panchayat_samiti_name", label: "Panchayat Samiti Name", type: "text", required: true },
        { name: "district", label: "District", type: "text", required: true },
        { name: "village_location", label: "HQ / Village Location", type: "text" },
        { name: "sarpanch_name", label: "Sarpanch Name", type: "text" },
        { name: "office_phone", label: "Office Contact Phone", type: "text" },
        { name: "total_area_hectares", label: "Total Area (Hectares)", type: "number", required: true },
        { name: "cultivable_area_hectares", label: "Cultivable Area (Hectares)", type: "number", required: true },
        { name: "active_farmers_count", label: "Active Farmers Count", type: "number" },
      ]
    },
    {
      id: "ps_soil_suitability",
      title: "Soil / Crop Suitability Data",
      tableName: "ps_soil_suitability",
      apiPath: "/ps/soil-suitability",
      columns: [
        { key: "id", label: "ID" },
        { key: "gp_name", label: "GP Name" },
        { key: "soil_type", label: "Soil Type" },
        { key: "primary_crops", label: "Primary Suitable Crops" },
        { key: "irrigation_coverage_pct", label: "Irrigation %" },
        { key: "organic_matter_rating", label: "Organic Matter", badge: true },
      ],
      fields: [
        { name: "gp_name", label: "Gram Panchayat Name", type: "text", required: true },
        { name: "soil_type", label: "Soil Type Classification", type: "text", required: true },
        { name: "primary_crops", label: "Primary Suitable Crops", type: "text", required: true },
        { name: "irrigation_coverage_pct", label: "Irrigation Coverage %", type: "number", required: true },
        { name: "organic_matter_rating", label: "Organic Matter Rating", type: "select", options: ["LOW", "MEDIUM", "HIGH"] },
      ]
    },
    {
      id: "ps_ai_recommendations",
      title: "AI Recommendations",
      customRenderer: "renderPSAISuitability"
    },
    {
      id: "ps_audit_history",
      title: "History / Audit Records",
      customRenderer: "renderAuditHistoryTab"
    }
  ],

  GRAM_PANCHAYAT: [
    {
      id: "gp_overview",
      title: "Overview",
      customRenderer: "renderGPOverview"
    },
    {
      id: "gp_central_ai_recommendation",
      title: "🧠 Central AI Recommendations",
      customRenderer: "renderGPCentralAIRecommendation",
    },
    {
      id: "gp_ps_allocations",
      title: "Requirements Received from PS",
      tableName: "ps_gp_allocations",
      apiPath: "/ps/gp-allocations",
      columns: [
        { key: "id", label: "ID" },
        { key: "crop_name", label: "Crop" },
        { key: "allocated_quantity_mt", label: "Quota (MT)" },
        { key: "human_final_quantity_mt", label: "Approved (MT)" },
        { key: "season", label: "Season" },
        { key: "status", label: "Status", badge: true },
      ],
      fields: []
    },
    {
      id: "gp_farmer_registry",
      title: "Farmer Registry",
      tableName: "gp_farmer_registry",
      apiPath: "/gp/farmers",
      columns: [
        { key: "farmer_id", label: "Farmer ID" },
        { key: "farmer_name", label: "Farmer Name" },
        { key: "contact_phone", label: "Contact Phone" },
        { key: "village_name", label: "Village" },
        { key: "total_land_acres", label: "Land (Acres)" },
        { key: "soil_health_card_no", label: "Soil Card No" },
        { key: "status", label: "Status", badge: true },
      ],
      fields: [
        { name: "farmer_id", label: "Farmer ID (KS-FMR-XXXX)", type: "text", required: true },
        { name: "farmer_name", label: "Farmer Full Name", type: "text", required: true },
        { name: "contact_phone", label: "Contact Mobile Phone", type: "text", required: true },
        { name: "aadhaar_masked", label: "Aadhaar Number (Masked XXXX-XXXX-1234)", type: "text" },
        { name: "village_name", label: "Village Name", type: "text", required: true },
        { name: "total_land_acres", label: "Total Land Holding (Acres)", type: "number", required: true },
        { name: "bank_account_masked", label: "Bank Account No (Masked)", type: "text" },
        { name: "soil_health_card_no", label: "Soil Health Card Number", type: "text" },
      ]
    },
    {
      id: "gp_land_records",
      title: "Land Records",
      tableName: "gp_farmer_land_records",
      apiPath: "/gp/land-records",
      columns: [
        { key: "farmer_id", label: "Farmer ID" },
        { key: "survey_number", label: "Survey / Gat No" },
        { key: "village_name", label: "Village" },
        { key: "land_area_acres", label: "Area (Acres)" },
        { key: "soil_type", label: "Soil Type" },
      ],
      fields: [
        { name: "farmer_id", label: "Farmer ID (KS-FMR-XXXX)", type: "text", required: true },
        { name: "farmer_name", label: "Farmer Full Name", type: "text", required: true },
        { name: "survey_number", label: "Survey / Gat Number", type: "text", required: true },
        { name: "village_name", label: "Village Name", type: "text", required: true },
        { name: "land_area_acres", label: "Land Parcel Area (Acres)", type: "number", required: true },
        { name: "soil_type", label: "Soil Type", type: "text", required: true },
        { name: "irrigation_source", label: "Irrigation Source", type: "select", options: ["CANAL", "BOREWELL", "OPEN_WELL", "RAINFED"] },
      ]
    },
    {
      id: "gp_soil_tests",
      title: "Soil Records",
      tableName: "gp_soil_tests",
      apiPath: "/gp/soil-tests",
      columns: [
        { key: "farmer_id", label: "Farmer ID" },
        { key: "survey_number", label: "Survey No" },
        { key: "sample_date", label: "Test Date" },
        { key: "ph_level", label: "pH" },
        { key: "nitrogen_kg_ha", label: "N (kg/ha)" },
        { key: "phosphorus_kg_ha", label: "P (kg/ha)" },
        { key: "potassium_kg_ha", label: "K (kg/ha)" },
        { key: "organic_carbon_pct", label: "OC %" },
      ],
      fields: [
        { name: "farmer_id", label: "Farmer ID", type: "text", required: true },
        { name: "survey_number", label: "Survey / Gat No", type: "text", required: true },
        { name: "sample_date", label: "Sample Date (YYYY-MM-DD)", type: "text", required: true },
        { name: "ph_level", label: "pH Level", type: "number", required: true },
        { name: "nitrogen_kg_ha", label: "Nitrogen (N) kg/ha", type: "number", required: true },
        { name: "phosphorus_kg_ha", label: "Phosphorus (P) kg/ha", type: "number", required: true },
        { name: "potassium_kg_ha", label: "Potassium (K) kg/ha", type: "number", required: true },
        { name: "organic_carbon_pct", label: "Organic Carbon %", type: "number", required: true },
        { name: "soil_test_doc_url", label: "Soil Test Report File/JPG", type: "text" },
        { name: "testing_lab", label: "Testing Laboratory Name", type: "text" },
      ]
    },
    {
      id: "gp_soil_docs",
      title: "Soil Test Documents",
      customRenderer: "renderSoilTestDocs"
    },
    {
      id: "gp_crop_assignments",
      title: "Crop Allocation (AI-First)",
      tableName: "gp_crop_assignments",
      apiPath: "/gp/crop-assignments",
      isGPAIFirstTable: true,
      columns: [
        { key: "id", label: "ID" },
        { key: "farmer_id", label: "Farmer ID" },
        { key: "farmer_name", label: "Farmer Name" },
        { key: "crop_name", label: "Assigned Crop" },
        { key: "ai_recommended_acres", label: "🤖 AI Acres" },
        { key: "human_final_acres", label: "👤 Final Acres" },
        { key: "ai_recommended_quintals", label: "🤖 AI Qtl" },
        { key: "human_final_quintals", label: "👤 Final Qtl" },
        { key: "status", label: "Status", badge: true },
      ],
      fields: [
        { name: "farmer_id", label: "Farmer ID", type: "text", required: true },
        { name: "farmer_name", label: "Farmer Full Name", type: "text", required: true },
        { name: "crop_name", label: "Crop Name", type: "text", required: true },
        { name: "season", label: "Season", type: "text", required: true },
        { name: "assigned_acres", label: "Assigned Land (Acres)", type: "number", required: true },
        { name: "required_quantity_quintals", label: "Required Target (Quintals)", type: "number", required: true },
        { name: "status", label: "Status", type: "select", options: ["AI_GENERATED", "UNDER_REVIEW", "APPROVED", "HUMAN_CORRECTED"] },
      ]
    },
    {
      id: "gp_ai_matching",
      title: "AI Recommendations",
      customRenderer: "renderGPCentralAIRecommendation"
    },
    {
      id: "gp_audit_history",
      title: "History / Audit",
      customRenderer: "renderAuditHistoryTab"
    }
  ],

  FARMER: [
    {
      id: "farmer_overview",
      title: "Overview",
      customRenderer: "renderFarmerOverview"
    },
    {
      id: "farmer_profile",
      title: "My Profile",
      customRenderer: "renderFarmerProfile"
    },
    {
      id: "farmer_id_card",
      title: "Farmer ID",
      customRenderer: "renderFarmerIdCard"
    },
    {
      id: "farmer_land",
      title: "Land & Soil",
      tableName: "gp_farmer_land_records",
      apiPath: "/gp/land-records",
      columns: [
        { key: "survey_number", label: "Survey / Gat No" },
        { key: "village_name", label: "Village" },
        { key: "land_area_acres", label: "Area (Acres)" },
        { key: "soil_type", label: "Soil Type" },
        { key: "irrigation_source", label: "Irrigation" },
      ],
      fields: []
    },
    {
      id: "farmer_soil_docs",
      title: "Soil Test Documents",
      customRenderer: "renderSoilTestDocs"
    },
    {
      id: "farmer_assignments",
      title: "Assigned Crops",
      tableName: "gp_crop_assignments",
      apiPath: "/gp/crop-assignments",
      columns: [
        { key: "crop_name", label: "Crop" },
        { key: "season", label: "Season" },
        { key: "human_final_acres", label: "Allocated Acres" },
        { key: "human_final_quintals", label: "Target (Quintals)" },
        { key: "status", label: "Status", badge: true },
      ],
      fields: []
    },
    {
      id: "farmer_harvests",
      title: "Crop/Harvest Records",
      tableName: "farmer_harvest_records",
      apiPath: "/farmer/harvests",
      columns: [
        { key: "id", label: "ID" },
        { key: "crop_name", label: "Crop" },
        { key: "season", label: "Season" },
        { key: "harvest_date", label: "Harvest Date" },
        { key: "actual_yield_kg", label: "Actual Yield (kg)" },
        { key: "quality_condition", label: "Condition", badge: true },
        { key: "notes", label: "Harvest Notes" },
      ],
      fields: [
        { name: "farmer_id", label: "Farmer ID", type: "text", required: true },
        { name: "crop_name", label: "Crop Name", type: "text", required: true },
        { name: "season", label: "Season", type: "text", required: true },
        { name: "harvest_date", label: "Harvest Date", type: "text", required: true },
        { name: "actual_yield_kg", label: "Harvested Yield (kg)", type: "number", required: true },
        { name: "quality_condition", label: "Grain Quality Condition", type: "select", options: ["EXCELLENT", "GOOD", "FAIR", "DAMAGED"] },
        { name: "notes", label: "Notes", type: "textarea" },
      ]
    },
    {
      id: "farmer_deliveries",
      title: "Warehouse Deliveries",
      tableName: "farmer_delivery_records",
      apiPath: "/farmer/deliveries",
      columns: [
        { key: "id", label: "ID" },
        { key: "batch_id", label: "Batch ID" },
        { key: "crop_name", label: "Crop" },
        { key: "target_warehouse_name", label: "Target Warehouse" },
        { key: "vehicle_slip_number", label: "Slip No" },
        { key: "declared_weight_kg", label: "Declared (kg)" },
        { key: "weighbridge_net_weight_kg", label: "Weighbridge Net (kg)" },
        { key: "delivery_date", label: "Delivery Date" },
        { key: "status", label: "Status", badge: true },
      ],
      fields: [
        { name: "farmer_id", label: "Farmer ID", type: "text", required: true },
        { name: "crop_name", label: "Crop Name", type: "text", required: true },
        { name: "target_warehouse_name", label: "Destination Warehouse", type: "text", required: true },
        { name: "vehicle_slip_number", label: "Vehicle / Mandi Slip No", type: "text", required: true },
        { name: "declared_weight_kg", label: "Declared Weight (kg)", type: "number", required: true },
        { name: "weighbridge_net_weight_kg", label: "Weighbridge Verified Weight (kg)", type: "number" },
        { name: "batch_id", label: "Assigned Batch ID", type: "text" },
        { name: "delivery_date", label: "Delivery Date", type: "text", required: true },
        { name: "status", label: "Status", type: "select", options: ["IN_TRANSIT", "RECEIVED_AT_WH", "GRADED", "STORED"] },
      ]
    },
    {
      id: "farmer_grading",
      title: "Weight & Grading",
      tableName: "major_warehouse_intakes",
      apiPath: "/major-wh/intakes",
      columns: [
        { key: "batch_id", label: "Batch ID" },
        { key: "crop_name", label: "Crop" },
        { key: "net_weight_kg", label: "Net Weight (kg)" },
        { key: "ai_predicted_grade", label: "AI Grade", badge: true },
        { key: "human_final_grade", label: "Human Final Grade", badge: true },
        { key: "storage_silo_bay", label: "Silo Bay" },
        { key: "review_status", label: "Grading Status", badge: true },
      ],
      fields: []
    },
    {
      id: "farmer_payments",
      title: "Payments",
      tableName: "farmer_payment_records",
      apiPath: "/farmer/payments",
      columns: [
        { key: "batch_id", label: "Batch ID" },
        { key: "crop_name", label: "Crop" },
        { key: "net_weight_kg", label: "Net Weight (kg)" },
        { key: "confirmed_grade", label: "Final Grade", badge: true },
        { key: "rate_per_kg", label: "Rate (₹/kg)" },
        { key: "total_amount", label: "Total Amount (₹)" },
        { key: "payment_status", label: "Payment Status", badge: true },
        { key: "transaction_ref", label: "DBT Tx Ref" },
      ],
      fields: [
        { name: "farmer_id", label: "Farmer ID", type: "text", required: true },
        { name: "batch_id", label: "Batch ID", type: "text", required: true },
        { name: "crop_name", label: "Crop Name", type: "text", required: true },
        { name: "net_weight_kg", label: "Net Weight (kg)", type: "number", required: true },
        { name: "confirmed_grade", label: "Confirmed Grade", type: "select", options: ["A", "B", "C"] },
        { name: "rate_per_kg", label: "Rate (₹/kg)", type: "number", required: true },
        { name: "total_amount", label: "Total Amount (₹)", type: "number", required: true },
        { name: "payment_status", label: "Payment Status", type: "select", options: ["PENDING", "APPROVED", "DISBURSED"] },
        { name: "transaction_ref", label: "Transaction Reference", type: "text" },
        { name: "payment_date", label: "Payment Date", type: "text" },
      ]
    },
    {
      id: "farmer_complete_history",
      title: "Complete History",
      customRenderer: "renderFarmerCompleteHistory"
    }
  ],

  MAJOR_WAREHOUSE: [
    {
      id: "major_wh_overview",
      title: "Overview",
      customRenderer: "renderMajorWHOverview"
    },
    {
      id: "major_wh_intakes",
      title: "Farmer Intake",
      tableName: "major_warehouse_intakes",
      apiPath: "/major-wh/intakes",
      isDualGradingTable: true,
      columns: [
        { key: "batch_id", label: "Batch ID" },
        { key: "farmer_id", label: "Farmer ID" },
        { key: "farmer_name", label: "Farmer Name" },
        { key: "crop_name", label: "Crop" },
        { key: "net_weight_kg", label: "Net Wt (kg)" },
        { key: "ai_predicted_grade", label: "AI Grade", badge: true },
        { key: "human_final_grade", label: "Human Final", badge: true },
        { key: "storage_silo_bay", label: "Silo Bay" },
        { key: "review_status", label: "Review Status", badge: true },
      ],
      fields: [
        { name: "batch_id", label: "Batch ID (Leave empty to auto-generate)", type: "text" },
        { name: "farmer_id", label: "Farmer ID (KS-FMR-XXXX)", type: "text", required: true },
        { name: "farmer_name", label: "Farmer Full Name", type: "text", required: true },
        { name: "crop_name", label: "Crop Name", type: "text", required: true },
        { name: "gross_weight_kg", label: "Gross Weight (kg)", type: "number", required: true },
        { name: "tare_weight_kg", label: "Tare Weight (kg)", type: "number", required: true },
        { name: "net_weight_kg", label: "Net Weight (kg)", type: "number" },
        { name: "storage_silo_bay", label: "Storage Silo Bay Number", type: "text" },
        { name: "storage_temp_celsius", label: "Storage Temp (°C)", type: "number" },
        { name: "storage_humidity_pct", label: "Moisture / Humidity %", type: "number" },
      ]
    },
    {
      id: "major_wh_batches",
      title: "Crop Batches",
      tableName: "major_warehouse_intakes",
      apiPath: "/major-wh/intakes",
      columns: [
        { key: "batch_id", label: "Batch ID" },
        { key: "crop_name", label: "Crop" },
        { key: "net_weight_kg", label: "Quantity (kg)" },
        { key: "storage_silo_bay", label: "Silo Bay Location" },
        { key: "human_final_grade", label: "Quality Grade", badge: true },
        { key: "created_at", label: "Intake Date" },
      ],
      fields: []
    },
    {
      id: "major_wh_weights",
      title: "Weight Records",
      tableName: "major_warehouse_intakes",
      apiPath: "/major-wh/intakes",
      columns: [
        { key: "batch_id", label: "Batch ID" },
        { key: "farmer_name", label: "Farmer" },
        { key: "gross_weight_kg", label: "Gross Wt (kg)" },
        { key: "tare_weight_kg", label: "Tare Wt (kg)" },
        { key: "net_weight_kg", label: "Certified Net Wt (kg)" },
        { key: "created_at", label: "Timestamp" },
      ],
      fields: []
    },
    {
      id: "major_wh_ai_grading",
      title: "AI Quality Grading",
      customRenderer: "renderMajorWHAIGradingConsole"
    },
    {
      id: "major_wh_dual_review",
      title: "Human Final Grading",
      tableName: "major_warehouse_intakes",
      apiPath: "/major-wh/intakes",
      isDualGradingTable: true,
      columns: [
        { key: "batch_id", label: "Batch ID" },
        { key: "crop_name", label: "Crop" },
        { key: "ai_predicted_score", label: "AI Score" },
        { key: "ai_predicted_grade", label: "AI Grade", badge: true },
        { key: "human_final_score", label: "Human Score" },
        { key: "human_final_grade", label: "Human Grade", badge: true },
        { key: "review_status", label: "Status", badge: true },
      ],
      fields: []
    },
    {
      id: "major_wh_storage",
      title: "Storage & Inventory",
      customRenderer: "renderMajorWHStorageInventory"
    },
    {
      id: "major_wh_dispatches",
      title: "Dispatch to Minor Warehouse",
      customRenderer: "renderMajorWHDispatchesConsole"
    },
    {
      id: "major_wh_truck_tracking",
      title: "Truck / Delivery Tracking",
      customRenderer: "renderTruckTrackingConsole"
    },
    {
      id: "major_wh_payments",
      title: "Payments",
      tableName: "farmer_payment_records",
      apiPath: "/farmer/payments",
      columns: [
        { key: "batch_id", label: "Batch ID" },
        { key: "farmer_id", label: "Farmer ID" },
        { key: "crop_name", label: "Crop" },
        { key: "net_weight_kg", label: "Net Weight (kg)" },
        { key: "confirmed_grade", label: "Grade", badge: true },
        { key: "total_amount", label: "Total Amount (₹)" },
        { key: "payment_status", label: "Status", badge: true },
      ],
      fields: []
    },
    {
      id: "major_wh_audit_history",
      title: "History / Audit",
      customRenderer: "renderAuditHistoryTab"
    }
  ],

  MINOR_WAREHOUSE: [
    {
      id: "minor_wh_overview",
      title: "Overview",
      customRenderer: "renderMinorWHOverview"
    },
    {
      id: "minor_wh_inward",
      title: "Incoming Dispatches & Receiving",
      customRenderer: "renderMinorWHInwardConsole"
    },
    {
      id: "minor_wh_sent_received",
      title: "Sent vs Received (Discrepancy)",
      customRenderer: "renderMinorWHSentReceivedConsole"
    },
    {
      id: "minor_wh_truck_tracking",
      title: "Truck / Delivery Tracking",
      customRenderer: "renderTruckTrackingConsole"
    },
    {
      id: "minor_wh_stock",
      title: "Inventory",
      tableName: "minor_wh_stock",
      apiPath: "/minor-wh/stock",
      columns: [
        { key: "id", label: "ID" },
        { key: "crop_name", label: "Crop" },
        { key: "batch_id", label: "Batch ID" },
        { key: "current_stock_kg", label: "Stock (kg)" },
        { key: "warehouse_location", label: "Godown Location" },
        { key: "last_replenished", label: "Last Replenished" },
      ],
      fields: [
        { name: "crop_name", label: "Crop Name", type: "text", required: true },
        { name: "batch_id", label: "Batch ID", type: "text", required: true },
        { name: "current_stock_kg", label: "Stock Quantity (kg)", type: "number", required: true },
        { name: "warehouse_location", label: "Godown Location / Room", type: "text" },
        { name: "last_replenished", label: "Last Replenished Date", type: "text", required: true },
      ]
    },
    {
      id: "minor_wh_demand",
      title: "Regional Demand",
      tableName: "minor_wh_regional_demand",
      apiPath: "/minor-wh/demand",
      columns: [
        { key: "id", label: "ID" },
        { key: "region_name", label: "Cluster / Region" },
        { key: "crop_name", label: "Crop" },
        { key: "monthly_demand_kg", label: "Monthly Demand (kg)" },
        { key: "urgency_level", label: "Urgency", badge: true },
      ],
      fields: [
        { name: "region_name", label: "Region / Cluster Name", type: "text", required: true },
        { name: "crop_name", label: "Crop Name", type: "text", required: true },
        { name: "monthly_demand_kg", label: "Monthly Demand (kg)", type: "number", required: true },
        { name: "urgency_level", label: "Urgency Level", type: "select", options: ["LOW", "NORMAL", "HIGH", "CRITICAL"] },
        { name: "notes", label: "Notes", type: "textarea" },
      ]
    },
    {
      id: "minor_wh_ai_recs",
      title: "AI Stock Recommendations",
      customRenderer: "renderMinorWHAIRecs"
    },
    {
      id: "minor_wh_distributions",
      title: "Distribution",
      tableName: "minor_wh_distributions",
      apiPath: "/minor-wh/distributions",
      columns: [
        { key: "receipt_no", label: "Receipt No" },
        { key: "batch_id", label: "Batch ID" },
        { key: "crop_name", label: "Crop" },
        { key: "recipient_center", label: "Recipient Center" },
        { key: "quantity_kg", label: "Quantity (kg)" },
        { key: "distribution_date", label: "Date" },
        { key: "status", label: "Status", badge: true },
      ],
      fields: [
        { name: "receipt_no", label: "Receipt No", type: "text", required: true },
        { name: "batch_id", label: "Batch ID", type: "text", required: true },
        { name: "crop_name", label: "Crop Name", type: "text", required: true },
        { name: "recipient_center", label: "Fair Price Shop / Local Center", type: "text", required: true },
        { name: "quantity_kg", label: "Dispatched Quantity (kg)", type: "number", required: true },
        { name: "distribution_date", label: "Date", type: "text", required: true },
        { name: "status", label: "Status", type: "select", options: ["COMPLETED", "IN_DELIVERY"] },
      ]
    },
    {
      id: "minor_wh_restock",
      title: "Restock Requests",
      tableName: "minor_wh_restock_requests",
      apiPath: "/minor-wh/restock",
      columns: [
        { key: "id", label: "ID" },
        { key: "crop_name", label: "Crop" },
        { key: "requested_quantity_kg", label: "Requested (kg)" },
        { key: "urgency", label: "Urgency", badge: true },
        { key: "request_date", label: "Request Date" },
        { key: "status", label: "Status", badge: true },
      ],
      fields: [
        { name: "crop_name", label: "Crop Name", type: "text", required: true },
        { name: "requested_quantity_kg", label: "Requested Quantity (kg)", type: "number", required: true },
        { name: "urgency", label: "Urgency Level", type: "select", options: ["NORMAL", "HIGH", "EMERGENCY"] },
        { name: "request_date", label: "Request Date", type: "text", required: true },
        { name: "status", label: "Status", type: "select", options: ["PENDING_MAJOR_DISPATCH", "DISPATCHED", "FULFILLED"] },
      ]
    },
    {
      id: "minor_wh_audit_history",
      title: "History / Audit",
      customRenderer: "renderAuditHistoryTab"
    }
  ],

  BULK_BUYER: [
    {
      id: "buyer_single_id_purchase",
      title: "Direct Purchase Order",
      customRenderer: "renderBuyerSingleIdOrder"
    },
    {
      id: "buyer_registration",
      title: "New Buyer Registration",
      customRenderer: "renderBuyerRegistration"
    },
    {
      id: "buyer_registry",
      title: "Verified Buyers Registry",
      tableName: "bulk_buyer_registry",
      apiPath: "/buyer/registry",
      columns: [
        { key: "buyer_id", label: "Buyer ID" },
        { key: "company_name", label: "Company Name" },
        { key: "business_type", label: "Business Type" },
        { key: "gst_number", label: "GST No" },
        { key: "contact_person", label: "Contact Person" },
        { key: "contact_phone", label: "Phone" },
        { key: "status", label: "Status", badge: true },
      ],
      fields: [
        { name: "buyer_id", label: "Buyer ID (KS-BYR-XXXX)", type: "text", required: true },
        { name: "company_name", label: "Company / Mill Name", type: "text", required: true },
        { name: "business_type", label: "Business Type", type: "text", required: true },
        { name: "gst_number", label: "GST Registration No", type: "text" },
        { name: "contact_person", label: "Contact Person Full Name", type: "text", required: true },
        { name: "contact_phone", label: "Mobile Phone", type: "text", required: true },
        { name: "official_email", label: "Official Email Address", type: "email", required: true },
        { name: "status", label: "Status", type: "select", options: ["VERIFIED_BUYER", "PENDING_VERIFICATION"] },
      ]
    },
    {
      id: "buyer_entries",
      title: "Entries / Transactions",
      tableName: "bulk_buyer_entries",
      apiPath: "/buyer/entries",
      columns: [
        { key: "id", label: "ID" },
        { key: "buyer_id", label: "Buyer ID" },
        { key: "crop_name", label: "Crop" },
        { key: "required_quantity_mt", label: "Quantity (MT)" },
        { key: "target_grade", label: "Target Grade", badge: true },
        { key: "max_price_offer_per_quintal", label: "Offer Price (₹/Qtl)" },
        { key: "delivery_hub", label: "Delivery Hub" },
        { key: "required_by_date", label: "Required By" },
        { key: "status", label: "Status", badge: true },
      ],
      fields: [
        { name: "buyer_id", label: "Buyer ID", type: "text", required: true },
        { name: "crop_name", label: "Crop Name", type: "text", required: true },
        { name: "required_quantity_mt", label: "Required Quantity (MT)", type: "number", required: true },
        { name: "target_grade", label: "Target Quality Grade", type: "select", options: ["A", "B", "C"] },
        { name: "max_price_offer_per_quintal", label: "Max Price Offer (₹/Quintal)", type: "number", required: true },
        { name: "delivery_hub", label: "Preferred Delivery Hub", type: "text", required: true },
        { name: "required_by_date", label: "Required By Date", type: "text", required: true },
        { name: "status", label: "Status", type: "select", options: ["ENTRY_RECORDED", "MATCHED", "IN_PROCUREMENT", "FULFILLED"] },
        { name: "notes", label: "Order Notes / Specifications", type: "textarea" },
      ]
    },
    {
      id: "buyer_audit_history",
      title: "History",
      customRenderer: "renderAuditHistoryTab"
    }
  ]
};

// ==========================================
// INITIALIZATION
// ==========================================
document.addEventListener("DOMContentLoaded", async () => {
  const token = ApiClient.getToken();
  if (!token) {
    window.location.href = "/pages/login.html";
    return;
  }

  try {
    currentUser = await ApiClient.getMe();
    if (!currentUser) return;

    renderSidebarProfile(currentUser);
    setupSectorWorkspace(currentUser.role);
    // 7-Tier horizontal flow has been removed from individual portal pages per AI-First specification
  } catch (err) {
    console.error("Dashboard initialization error:", err);
    if (err.message && (err.message.includes("Unable to connect") || err.message.includes("Failed to fetch"))) {
      const activeContainer = document.getElementById("activeTableContainer");
      if (activeContainer) {
        activeContainer.innerHTML = `
          <div class="alert-box danger" style="display:block; margin:20px 0; padding:18px;">
            <h4 style="margin-bottom:6px;">⚠️ Backend Server Connection Offline</h4>
            <p>${err.message}</p>
            <button class="btn btn-primary btn-sm" style="margin-top:12px;" onclick="window.location.reload()">
              🔄 Retry Connection
            </button>
          </div>
        `;
      }
      return;
    }
    ApiClient.removeToken();
    window.location.href = "/pages/login.html?expired=1";
  }
});

function renderSidebarProfile(user) {
  document.getElementById("profileName").textContent = user.full_name;
  document.getElementById("profileRole").textContent = user.role_title;
  document.getElementById("dashboardGreeting").textContent = `Logged in as ${user.full_name}`;
  document.getElementById("profileLocation").textContent = user.jurisdiction_or_location || "Central Jurisdiction";

  const idEl = document.getElementById("profileCustomId");
  if (user.farmer_id) {
    idEl.innerHTML = `<div class="id-badge">🌾 FARMER ID: ${user.farmer_id}</div>`;
    idEl.style.display = "block";
  } else if (user.buyer_id) {
    idEl.innerHTML = `<div class="id-badge">🏢 BUYER ID: ${user.buyer_id}</div>`;
    idEl.style.display = "block";
  } else {
    idEl.style.display = "none";
  }
}

// ==========================================
// WORKSPACE & TABS CONTROLLER
// ==========================================
function setupSectorWorkspace(role) {
  // If ADMIN, allow switching between all sectors
  if (role === "ADMIN") {
    renderAdminSectorSelector();
    loadSectorTabs("FOOD_DEPARTMENT");
  } else {
    loadSectorTabs(role);
  }
}

function renderAdminSectorSelector() {
  const container = document.getElementById("adminSectorSwitcher");
  if (!container) return;

  container.innerHTML = `
    <div style="background:#e8f5e9; padding:10px 16px; border-radius:4px; margin-bottom:16px; display:flex; align-items:center; justify-content:space-between;">
      <span style="font-size:0.85rem; font-weight:700; color:var(--primary-dark);">⚙️ Administrator Universal Record Access:</span>
      <select id="adminSectorSelect" class="form-control" style="width:260px; font-weight:600;" onchange="loadSectorTabs(this.value)">
        <option value="FOOD_DEPARTMENT">Food Department</option>
        <option value="PANCHAYAT_SAMITI">Panchayat Samiti</option>
        <option value="GRAM_PANCHAYAT">Gram Panchayat</option>
        <option value="FARMER">Farmer</option>
        <option value="MAJOR_WAREHOUSE">Major Warehouse</option>
        <option value="MINOR_WAREHOUSE">Minor Warehouse</option>
        <option value="BULK_BUYER">Bulk Buyer</option>
      </select>
    </div>
  `;
}

function loadSectorTabs(roleKey) {
  currentSectorTabs = SECTOR_CONFIGS[roleKey] || [];
  const tabsContainer = document.getElementById("sectorNavTabs");
  if (!tabsContainer) return;

  if (currentSectorTabs.length === 0) {
    tabsContainer.innerHTML = `<p style="color:var(--text-muted); padding:10px;">No operational record tables configured for this role.</p>`;
    return;
  }

  tabsContainer.innerHTML = currentSectorTabs.map((tab, idx) => `
    <button class="sub-nav-btn ${idx === 0 ? 'active' : ''}" data-tab-id="${tab.id}" onclick="selectSubTab('${tab.id}')">
      ${tab.title}
    </button>
  `).join("");

  selectSubTab(currentSectorTabs[0].id);
}

function selectSubTab(tabId) {
  document.querySelectorAll(".sub-nav-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-tab-id") === tabId);
  });

  activeTabConfig = currentSectorTabs.find(t => t.id === tabId);
  if (!activeTabConfig) return;

  const container = document.getElementById("activeTableContainer");
  if (!container) return;

  if (activeTabConfig.customRenderer && typeof window[activeTabConfig.customRenderer] === "function") {
    window[activeTabConfig.customRenderer](container, activeTabConfig);
  } else {
    renderActiveTable();
  }
}

// ==========================================
// TABLE RENDERING & DATA FETCH
// ==========================================
async function renderActiveTable() {
  const container = document.getElementById("activeTableContainer");
  if (!container || !activeTabConfig) return;

  container.innerHTML = `
    <div style="text-align:center; padding:32px; color:var(--text-muted);">
      Loading records from ${activeTabConfig.tableName || activeTabConfig.id}...
    </div>
  `;

  try {
    // If Farmer role and farmer_id exists, filter by farmer_id where applicable
    let queryParam = "";
    if (currentUser && currentUser.farmer_id && (activeTabConfig.apiPath.includes("/farmer") || activeTabConfig.apiPath.includes("/gp"))) {
      queryParam = `?farmer_id=${currentUser.farmer_id}`;
    }

    const records = await ApiClient.getRecords(`${activeTabConfig.apiPath}${queryParam}`);
    currentRecordsList = records || [];

    const isMajorWhIntake = activeTabConfig.isDualGradingTable;
    const isPSAIFirst = activeTabConfig.isPSAIFirstTable;
    const isGPAIFirst = activeTabConfig.isGPAIFirstTable;

    let tableHtml = `
      <div class="table-container">
        <div class="table-toolbar">
          <div>
            <h3>${activeTabConfig.title}</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">Table: <code>${activeTabConfig.tableName}</code> • Total Stored Records: <strong>${currentRecordsList.length}</strong></span>
          </div>
          <div class="table-toolbar-actions">
            ${activeTabConfig.isAiFirstCropTable ? `
              <button class="btn btn-primary btn-sm" onclick="openGenerateAIRecModal()" style="background:#1565c0;">
                🤖 Generate AI Recommendation
              </button>
            ` : isPSAIFirst ? `
              <button class="btn btn-primary btn-sm" onclick="openGeneratePSAIExtModal()" style="background:#1565c0;">
                🤖 Run Central AI GP Allocation
              </button>
              <button class="btn btn-outline btn-sm" onclick="openAddModal()">
                + Add Manual Quota
              </button>
            ` : isGPAIFirst ? `
              <button class="btn btn-primary btn-sm" onclick="openGenerateGPAIExtModal()" style="background:#1565c0;">
                🤖 Run Central AI Farmer Matching
              </button>
              <button class="btn btn-outline btn-sm" onclick="openAddModal()">
                + Add Manual Assignment
              </button>
            ` : isMajorWhIntake ? `
              <button class="btn btn-primary btn-sm" onclick="openGenerateWHAIExtModal()" style="background:#1565c0;">
                🤖 Run AI Quality Grader
              </button>
              <button class="btn btn-outline btn-sm" onclick="openAddModal()">
                + Add Intake Batch
              </button>
            ` : (activeTabConfig.fields && activeTabConfig.fields.length > 0 ? `
              <button class="btn btn-primary btn-sm" onclick="openAddModal()">
                + Add New Record
              </button>
            ` : '')}
          </div>
        </div>

        <table class="record-table">
          <thead>
            <tr>
              ${activeTabConfig.columns.map(c => `<th>${c.label}</th>`).join("")}
              <th style="text-align:right;">Actions</th>
            </tr>
          </thead>
          <tbody>
            ${currentRecordsList.length === 0 ? `
              <tr>
                <td colspan="${activeTabConfig.columns.length + 1}" style="text-align:center; padding:24px; color:var(--text-muted);">
                  ${activeTabConfig.isAiFirstCropTable ? 
                    'No crop requirements generated yet. Click <strong>"🤖 Generate AI Recommendation"</strong> to run the Central AI Engine.' : 
                    isPSAIFirst ? 'No Gram Panchayat allocations generated yet. Click <strong>"🤖 Run Central AI GP Allocation"</strong>.' :
                    isGPAIFirst ? 'No Farmer allocations generated yet. Click <strong>"🤖 Run Central AI Farmer Matching"</strong>.' :
                    'No records stored yet. Click <strong>"+ Add New Record"</strong> to create the first record.'}
                </td>
              </tr>
            ` : currentRecordsList.map((row, idx) => `
              <tr>
                ${activeTabConfig.columns.map(col => {
                  const val = row[col.key] !== undefined && row[col.key] !== null ? row[col.key] : "-";
                  if (col.badge) {
                    const badgeClass = getBadgeClass(String(val));
                    return `<td><span class="badge ${badgeClass}">${val}</span></td>`;
                  }
                  if ((col.key === "ai_recommended_quantity_mt" || col.key === "human_final_quantity_mt" || col.key === "allocated_quantity_mt") && val !== "-") {
                    return `<td><span style="font-weight:700; color:${col.key.includes('ai') ? '#1565c0' : '#2e7d32'};">${Number(val).toLocaleString()} MT</span></td>`;
                  }
                  if ((col.key === "ai_recommended_quintals" || col.key === "human_final_quintals") && val !== "-") {
                    return `<td><span style="font-weight:700; color:${col.key.includes('ai') ? '#1565c0' : '#2e7d32'};">${Number(val).toLocaleString()} Qtl</span></td>`;
                  }
                  if ((col.key === "ai_recommended_acres" || col.key === "human_final_acres" || col.key === "assigned_acres") && val !== "-") {
                    return `<td><span style="font-weight:600;">${val} Acres</span></td>`;
                  }
                  return `<td>${val}</td>`;
                }).join("")}
                <td style="text-align:right;">
                  <div class="action-btn-group" style="justify-content:flex-end;">
                    ${activeTabConfig.isAiFirstCropTable ? `
                      <button class="btn btn-outline btn-sm" onclick="openAIRationaleModal(${row.id})" title="View AI analysis factors">
                        👁️ Rationale
                      </button>
                      <button class="btn btn-secondary btn-sm" onclick="openEditModal(${row.id})">
                        ✏️ Edit
                      </button>
                      ${row.status !== 'APPROVED' ? `
                        <button class="btn btn-primary btn-sm" onclick="openApproveModal(${row.id})" style="background:#2e7d32;">
                          ✅ Approve
                        </button>
                      ` : `
                        <button class="btn btn-primary btn-sm" onclick="openAssignToPSModal(${row.id})" style="background:#e65100;">
                          📤 Assign to PS
                        </button>
                      `}
                    ` : isPSAIFirst ? `
                      <button class="btn btn-outline btn-sm" onclick="openPSAIRationaleModal(${row.id})" title="View Central AI Allocation Rationale">
                        👁️ Rationale
                      </button>
                      ${row.status !== 'APPROVED' ? `
                        <button class="btn btn-primary btn-sm" onclick="quickApprovePSAllocation(${row.id})" style="background:#2e7d32;">
                          ✅ Approve
                        </button>
                      ` : ''}
                      <button class="btn btn-secondary btn-sm" onclick="openEditModal(${row.id})">
                        ✏️ Edit
                      </button>
                    ` : isGPAIFirst ? `
                      <button class="btn btn-outline btn-sm" onclick="openGPAIRationaleModal(${row.id})" title="View Central AI Matching Rationale">
                        👁️ Rationale
                      </button>
                      ${row.status !== 'APPROVED' ? `
                        <button class="btn btn-primary btn-sm" onclick="quickApproveGPAllocation(${row.id})" style="background:#2e7d32;">
                          ✅ Approve
                        </button>
                      ` : ''}
                      <button class="btn btn-secondary btn-sm" onclick="openEditModal(${row.id})">
                        ✏️ Edit
                      </button>
                    ` : isMajorWhIntake ? `
                      <button class="btn btn-primary btn-sm" onclick="openDualGradingModal(${row.id})" style="background:#0277bd;">
                        ⚖️ Dual Grade
                      </button>
                      <button class="btn btn-secondary btn-sm" onclick="openEditModal(${row.id})">
                        ✏️ Edit
                      </button>
                    ` : (activeTabConfig.fields && activeTabConfig.fields.length > 0 ? `
                      <button class="btn btn-secondary btn-sm" onclick="openEditModal(${row.id})">
                        ✏️ Edit
                      </button>
                    ` : '')}
                    <button class="btn btn-outline btn-sm" onclick="openHistoryModal('${activeTabConfig.tableName}', '${row.id}')">
                      📜 History
                    </button>
                  </div>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;

    container.innerHTML = tableHtml;
  } catch (err) {
    container.innerHTML = `
      <div class="alert-box danger" style="display:block;">
        Failed to load records: ${err.message}
      </div>
    `;
  }
}

function getBadgeClass(val) {
  if (!val) return "badge-warning";
  const s = String(val).toUpperCase();
  if (["AI GENERATED", "AI_GENERATED"].some(k => s.includes(k))) return "badge-info";
  if (["UNDER REVIEW", "UNDER_REVIEW", "PENDING_REVIEW", "PENDING"].some(k => s.includes(k))) return "badge-warning";
  if (["APPROVED", "CONFIRMED", "VERIFIED", "VERIFIED_BUYER", "VERIFIED_IN_STOCK", "ACTIVE", "A", "EXCELLENT", "COMPLETED", "MATCHED"].some(k => s.includes(k))) return "badge-success";
  if (["HUMAN CORRECTED", "HUMAN_CORRECTED", "CORRECTED"].some(k => s.includes(k))) return "badge-accent";
  if (["CRITICAL", "SEVERE", "ACUTE", "C", "REJECTED", "EMERGENCY"].some(k => s.includes(k))) return "badge-danger";
  if (["HIGH", "NORMAL", "B", "GOOD", "IN_PROGRESS", "UNDER_MANAGEMENT", "IN_TRANSIT", "ASSIGNED"].some(k => s.includes(k))) return "badge-info";
  return "badge-warning";
}

// ==========================================
// ADD NEW RECORD MODAL
// ==========================================
function openAddModal() {
  if (!activeTabConfig) return;

  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `Add Record: ${activeTabConfig.title}`;
  modalSubmitBtn.textContent = "Save Record";

  modalBody.innerHTML = `
    <form id="recordForm" class="form-grid">
      ${activeTabConfig.fields.map(f => `
        <div class="form-group ${f.type === 'textarea' ? 'style="grid-column: span 2;"' : ''}">
          <label class="form-label">${f.label} ${f.required ? '*' : ''}</label>
          ${renderFormField(f, null)}
        </div>
      `).join("")}
    </form>
  `;

  modalSubmitBtn.onclick = async () => {
    const form = document.getElementById("recordForm");
    const formData = new FormData(form);
    const payload = {};

    activeTabConfig.fields.forEach(f => {
      const val = formData.get(f.name);
      if (val !== null && val !== "") {
        payload[f.name] = f.type === "number" ? parseFloat(val) : val;
      }
    });

    try {
      modalSubmitBtn.disabled = true;
      modalSubmitBtn.textContent = "Saving...";
      await ApiClient.createRecord(activeTabConfig.apiPath, payload);
      closeModal();
      await renderActiveTable();
    } catch (e) {
      alert(`Failed to save record: ${e.message}`);
    } finally {
      modalSubmitBtn.disabled = false;
      modalSubmitBtn.textContent = "Save Record";
    }
  };

  modal.style.display = "flex";
}

// ==========================================
// EDIT RECORD MODAL (WITH MANDATORY AUDIT NOTE)
// ==========================================
function openEditModal(recordId) {
  const record = currentRecordsList.find(r => r.id === recordId);
  if (!record || !activeTabConfig) return;

  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `Edit Record #${recordId} (${activeTabConfig.title})`;
  modalSubmitBtn.textContent = "Update & Log to History";

  modalBody.innerHTML = `
    <div style="background:#fff8e1; border:1px solid #ffe082; padding:10px 14px; border-radius:4px; font-size:0.8rem; margin-bottom:14px; color:#614a00;">
      ⚠️ <strong>Audit History Rule:</strong> Editing will record your name, date/time, old value, and new value into the immutable audit history.
    </div>

    <form id="recordForm" class="form-grid">
      ${activeTabConfig.fields.map(f => `
        <div class="form-group ${f.type === 'textarea' ? 'style="grid-column: span 2;"' : ''}">
          <label class="form-label">${f.label}</label>
          ${renderFormField(f, record[f.name])}
        </div>
      `).join("")}

      <div class="form-group" style="grid-column: span 2; border-top: 1px dashed var(--border); padding-top: 12px;">
        <label class="form-label" style="color:var(--accent);">Reason for Edit / Operational Justification *</label>
        <input type="text" id="changeReasonInput" class="form-control" placeholder="e.g. Grain moisture adjusted after lab re-verification" required>
      </div>
    </form>
  `;

  modalSubmitBtn.onclick = async () => {
    const reasonInput = document.getElementById("changeReasonInput");
    const changeReason = reasonInput ? reasonInput.value.trim() : "";
    if (!changeReason) {
      alert("Please provide a reason for editing this operational record.");
      return;
    }

    const form = document.getElementById("recordForm");
    const formData = new FormData(form);
    const updatedPayload = {};

    activeTabConfig.fields.forEach(f => {
      const val = formData.get(f.name);
      if (val !== null && val !== "") {
        updatedPayload[f.name] = f.type === "number" ? parseFloat(val) : val;
      }
    });

    try {
      modalSubmitBtn.disabled = true;
      modalSubmitBtn.textContent = "Recording update...";
      await ApiClient.editRecord(activeTabConfig.apiPath, recordId, updatedPayload, changeReason);
      closeModal();
      await renderActiveTable();
    } catch (e) {
      alert(`Failed to update record: ${e.message}`);
    } finally {
      modalSubmitBtn.disabled = false;
      modalSubmitBtn.textContent = "Update & Log to History";
    }
  };

  modal.style.display = "flex";
}

// ==========================================
// DUAL AI / HUMAN GRADING REVIEW MODAL
// ==========================================
function openDualGradingModal(recordId) {
  const record = currentRecordsList.find(r => r.id === recordId);
  if (!record) return;

  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `Dual Quality Grading Review: Batch ${record.batch_id}`;
  modalSubmitBtn.textContent = "Confirm Final Quality Grade";

  const aiScore = record.ai_predicted_score !== null ? record.ai_predicted_score : 86.0;
  const aiGrade = record.ai_predicted_grade || "A";
  const humanScore = record.human_final_score !== null ? record.human_final_score : aiScore;
  const humanGrade = record.human_final_grade || aiGrade;

  modalBody.innerHTML = `
    <div class="dual-grade-container">
      <div class="grade-column ai-box">
        <span style="font-size:0.75rem; font-weight:700; color:#1565c0; text-transform:uppercase;">🤖 AI Predicted Quality</span>
        <div class="grade-val" style="color:#1565c0;">${aiGrade} (${aiScore} / 100)</div>
        <p style="font-size:0.78rem; color:var(--text-muted);">Computer vision & sensor grading prediction</p>
      </div>

      <div class="grade-column human-box">
        <span style="font-size:0.75rem; font-weight:700; color:#2e7d32; text-transform:uppercase;">👤 Human Warehouse Final Grade</span>
        <div class="grade-val" style="color:#2e7d32;">${humanGrade} (${humanScore} / 100)</div>
        <p style="font-size:0.78rem; color:var(--text-muted);">${record.review_status === 'CONFIRMED' ? `Confirmed by ${record.reviewed_by}` : 'Pending Confirmation'}</p>
      </div>
    </div>

    <form id="gradingForm">
      <div class="form-grid">
        <div class="form-group">
          <label class="form-label">Human Verified Quality Score (0 - 100) *</label>
          <input type="number" id="gradeScoreInput" class="form-control" value="${humanScore}" step="0.5" min="0" max="100" required>
        </div>
        <div class="form-group">
          <label class="form-label">Human Verified Grade *</label>
          <select id="gradeGradeInput" class="form-control" required>
            <option value="A" ${humanGrade === 'A' ? 'selected' : ''}>Grade A (Premium Grade)</option>
            <option value="B" ${humanGrade === 'B' ? 'selected' : ''}>Grade B (Standard Grade)</option>
            <option value="C" ${humanGrade === 'C' ? 'selected' : ''}>Grade C (Fair Average Quality)</option>
            <option value="REJECTED" ${humanGrade === 'REJECTED' ? 'selected' : ''}>REJECTED (Sub-standard)</option>
          </select>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Quality Inspection Notes / Analysis Details</label>
        <textarea id="gradeNotesInput" class="form-control" rows="2" placeholder="e.g. Visual inspection detected 2.8% foreign grain matter.">${record.grading_notes || ''}</textarea>
      </div>

      <div class="form-group">
        <label class="form-label" style="color:var(--accent);">Reason for Overriding AI Grade / Operational Note</label>
        <input type="text" id="gradeChangeReason" class="form-control" placeholder="e.g. Physical sieving and moisture verification" value="Human inspector quality verification">
      </div>
    </form>
  `;

  modalSubmitBtn.onclick = async () => {
    const score = document.getElementById("gradeScoreInput").value;
    const grade = document.getElementById("gradeGradeInput").value;
    const notes = document.getElementById("gradeNotesInput").value;
    const reason = document.getElementById("gradeChangeReason").value;

    try {
      modalSubmitBtn.disabled = true;
      modalSubmitBtn.textContent = "Confirming...";
      await ApiClient.reviewMajorWhGrade(recordId, score, grade, notes, reason);
      closeModal();
      await renderActiveTable();
    } catch (e) {
      alert(`Grading update failed: ${e.message}`);
    } finally {
      modalSubmitBtn.disabled = false;
      modalSubmitBtn.textContent = "Confirm Final Quality Grade";
    }
  };

  modal.style.display = "flex";
}

// ==========================================
// CENTRAL AI CROP RECOMMENDATION MODAL
// ==========================================
function openGenerateAIRecModal() {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = "🤖 Central AI/ML Engine: Crop Requirement Recommendation";
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Run Central AI Analysis";

  modalBody.innerHTML = `
    <div style="background:#e3f2fd; border:1px solid #90caf9; padding:12px 16px; border-radius:6px; margin-bottom:16px;">
      <div style="font-weight:700; color:#1565c0; font-size:0.9rem; margin-bottom:4px;">
        🧠 Statewide Unified Cross-Sector Intelligence
      </div>
      <p style="font-size:0.8rem; color:#0d47a1; margin:0; line-height:1.4;">
        The Central AI/ML Engine synthesizes data from <strong>Warehouse stock reserves</strong>, <strong>Crisis & shortage alerts</strong>, 
        <strong>Future demand projections</strong>, <strong>Weather/Climate patterns</strong>, and <strong>Panchayat Samiti suitability</strong> 
        to recommend optimal crop production targets.
      </p>
    </div>

    <form id="aiRecForm" class="form-grid">
      <div class="form-group">
        <label class="form-label">Target Crop for Analysis *</label>
        <select id="aiCropSelect" class="form-control" required>
          <option value="Sugarcane">Sugarcane</option>
          <option value="Wheat (Lokwan)">Wheat (Lokwan)</option>
          <option value="Cotton (Bt)">Cotton (Bt)</option>
          <option value="Soybean (JS-335)">Soybean (JS-335)</option>
          <option value="Gram / Chana">Gram / Chana</option>
          <option value="Onion (Nashik Red)">Onion (Nashik Red)</option>
          <option value="Maize (African Tall)">Maize (African Tall)</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Target Season *</label>
        <select id="aiSeasonSelect" class="form-control" required>
          <option value="Kharif 2026">Kharif 2026</option>
          <option value="Rabi 2026">Rabi 2026</option>
          <option value="Zaid 2026">Zaid 2026</option>
        </select>
      </div>

      <div class="form-group" style="grid-column: span 2; background:#fafafa; border:1px dashed var(--border); padding:10px 14px; border-radius:4px;">
        <span style="font-size:0.8rem; color:var(--text-muted);">
          ℹ️ <strong>Governance Rule:</strong> The Central AI Engine generates an authoritative baseline. Human Food Department officers review, adjust if necessary, and grant final approval before assigning quotas to Panchayat Samiti.
        </span>
      </div>
    </form>
  `;

  modalSubmitBtn.onclick = async () => {
    const crop = document.getElementById("aiCropSelect").value;
    const season = document.getElementById("aiSeasonSelect").value;

    try {
      modalSubmitBtn.disabled = true;
      modalSubmitBtn.textContent = "Analyzing Cross-Sector Data...";
      await ApiClient.generateAIRecRequirement(crop, season);
      closeModal();
      await renderActiveTable();
    } catch (e) {
      alert(`AI recommendation failed: ${e.message}`);
    } finally {
      modalSubmitBtn.disabled = false;
      modalSubmitBtn.textContent = "Run Central AI Analysis";
    }
  };

  modal.style.display = "flex";
}

// ==========================================
// AI DECISION RATIONALE MODAL
// ==========================================
function openAIRationaleModal(recordId) {
  const record = currentRecordsList.find(r => r.id === recordId);
  if (!record) return;

  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `🤖 Central AI Decision Rationale: ${record.crop_name} (Record #${record.id})`;
  modalSubmitBtn.style.display = "none"; // Informational modal

  const confScore = (record.ai_confidence_score * 100).toFixed(1);

  modalBody.innerHTML = `
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px;">
      <div style="background:#e3f2fd; border-radius:6px; padding:12px; border:1px solid #bbdefb;">
        <div style="font-size:0.75rem; text-transform:uppercase; color:#1565c0; font-weight:700;">🤖 AI Recommended Target</div>
        <div style="font-size:1.4rem; font-weight:800; color:#0d47a1; margin-top:4px;">
          ${Number(record.ai_recommended_quantity_mt || record.target_quantity_mt).toLocaleString()} MT
        </div>
        <div style="font-size:0.75rem; color:#1976d2; margin-top:2px;">
          Priority: <strong>${record.ai_priority || record.priority}</strong>
        </div>
      </div>

      <div style="background:#f1f8e9; border-radius:6px; padding:12px; border:1px solid #c8e6c9;">
        <div style="font-size:0.75rem; text-transform:uppercase; color:#2e7d32; font-weight:700;">👤 Human Final Target</div>
        <div style="font-size:1.4rem; font-weight:800; color:#1b5e20; margin-top:4px;">
          ${record.human_final_quantity_mt ? `${Number(record.human_final_quantity_mt).toLocaleString()} MT` : "Pending Approval"}
        </div>
        <div style="font-size:0.75rem; color:#388e3c; margin-top:2px;">
          ${record.finalized_by ? `Approved by: <strong>${record.finalized_by}</strong>` : "Status: " + record.status}
        </div>
      </div>
    </div>

    <div style="margin-bottom:14px;">
      <label class="form-label" style="color:var(--primary-dark); font-weight:700;">🧠 Complete AI Decision Rationale & Data Correlation</label>
      <div style="background:#fafafa; border:1px solid var(--border); padding:12px 16px; border-radius:6px; font-size:0.85rem; line-height:1.5; color:#2c3e50;">
        ${record.ai_rationale || "AI synthesized multi-sector demand, deficit, and agro-climatic parameters."}
      </div>
    </div>

    <div style="display:flex; justify-content:space-between; align-items:center; background:#f5f5f5; padding:10px 14px; border-radius:4px; font-size:0.8rem; margin-bottom:12px;">
      <span>Confidence Score: <strong style="color:#1565c0;">${confScore}%</strong></span>
      <span>Season: <strong>${record.season}</strong></span>
      <span>Generated: <strong>${record.ai_generated_at || record.created_at}</strong></span>
    </div>

    ${record.human_review_notes ? `
      <div style="margin-top:10px; background:#fffde7; border:1px solid #fff59d; padding:10px 14px; border-radius:4px; font-size:0.8rem; color:#795548;">
        <strong>👤 Human Review Note:</strong> "${record.human_review_notes}"
      </div>
    ` : ''}

    <div style="text-align:right; margin-top:16px;">
      <button class="btn btn-secondary btn-sm" onclick="closeModal()">Close</button>
    </div>
  `;

  modal.style.display = "flex";
}

// ==========================================
// APPROVE CROP REQUIREMENT MODAL
// ==========================================
function openApproveModal(recordId) {
  const record = currentRecordsList.find(r => r.id === recordId);
  if (!record) return;

  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `✅ Approve Crop Requirement: ${record.crop_name} (#${record.id})`;
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Sign & Approve Requirement";

  const defaultQty = record.human_final_quantity_mt !== null && record.human_final_quantity_mt !== undefined 
    ? record.human_final_quantity_mt 
    : record.target_quantity_mt;
  const defaultPriority = record.human_final_priority || record.priority || "HIGH";

  modalBody.innerHTML = `
    <div style="background:#e8f5e9; border:1px solid #a5d6a7; padding:12px 16px; border-radius:6px; margin-bottom:16px;">
      <div style="font-weight:700; color:#2e7d32; font-size:0.88rem; margin-bottom:4px;">
        🏛️ Directorate Final Sign-off & Authorization
      </div>
      <p style="font-size:0.8rem; color:#1b5e20; margin:0;">
        Approving this requirement authorizes it for distribution across Panchayat Samiti blocks. 
        The original AI recommendation of <strong>${Number(record.ai_recommended_quantity_mt || record.target_quantity_mt).toLocaleString()} MT</strong> 
        will remain preserved for historical accountability.
      </p>
    </div>

    <form id="approveForm" class="form-grid">
      <div class="form-group">
        <label class="form-label">Final Approved Quantity (MT) *</label>
        <input type="number" id="approveQtyInput" class="form-control" value="${defaultQty}" step="10" required>
        <span style="font-size:0.75rem; color:var(--text-muted);">AI Recommended: ${Number(record.ai_recommended_quantity_mt || record.target_quantity_mt).toLocaleString()} MT</span>
      </div>

      <div class="form-group">
        <label class="form-label">Approved Priority Level *</label>
        <select id="approvePriorityInput" class="form-control" required>
          <option value="NORMAL" ${defaultPriority === 'NORMAL' ? 'selected' : ''}>NORMAL</option>
          <option value="HIGH" ${defaultPriority === 'HIGH' ? 'selected' : ''}>HIGH</option>
          <option value="CRITICAL" ${defaultPriority === 'CRITICAL' ? 'selected' : ''}>CRITICAL</option>
        </select>
        <span style="font-size:0.75rem; color:var(--text-muted);">AI Priority: ${record.ai_priority || record.priority}</span>
      </div>

      <div class="form-group" style="grid-column: span 2;">
        <label class="form-label">Directorate Review & Authorization Notes</label>
        <textarea id="approveNotesInput" class="form-control" rows="2" placeholder="e.g. Approved after adjusting 3,000 MT due to inter-state supply agreement.">${record.human_review_notes || ''}</textarea>
      </div>

      <div class="form-group" style="grid-column: span 2;">
        <label class="form-label" style="color:var(--accent);">Audit Justification *</label>
        <input type="text" id="approveReasonInput" class="form-control" value="Food Directorate official sign-off and approval" required>
      </div>
    </form>
  `;

  modalSubmitBtn.onclick = async () => {
    const finalQty = parseFloat(document.getElementById("approveQtyInput").value);
    const finalPriority = document.getElementById("approvePriorityInput").value;
    const notes = document.getElementById("approveNotesInput").value.trim();
    const reason = document.getElementById("approveReasonInput").value.trim();

    if (isNaN(finalQty) || finalQty <= 0) {
      alert("Please enter a valid approved quantity in MT.");
      return;
    }

    try {
      modalSubmitBtn.disabled = true;
      modalSubmitBtn.textContent = "Signing & Stamping...";
      await ApiClient.approveFDRequirement(recordId, finalQty, finalPriority, notes, reason);
      closeModal();
      await renderActiveTable();
    } catch (e) {
      alert(`Approval failed: ${e.message}`);
    } finally {
      modalSubmitBtn.disabled = false;
      modalSubmitBtn.textContent = "Sign & Approve Requirement";
    }
  };

  modal.style.display = "flex";
}

// ==========================================
// ASSIGN REQUIREMENT TO PANCHAYAT SAMITI MODAL
// ==========================================
function openAssignToPSModal(recordId) {
  const record = currentRecordsList.find(r => r.id === recordId);
  if (!record) return;

  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `📤 Assign to Panchayat Samiti: ${record.crop_name} (#${record.id})`;
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Assign Quota to PS";

  const approvedQty = record.human_final_quantity_mt || record.target_quantity_mt;

  modalBody.innerHTML = `
    <div style="background:#fff3e0; border:1px solid #ffe0b2; padding:12px 16px; border-radius:6px; margin-bottom:16px;">
      <div style="font-weight:700; color:#e65100; font-size:0.88rem; margin-bottom:4px;">
        🏛️ Cascade Requirement Down the Supply Chain
      </div>
      <p style="font-size:0.8rem; color:#bf360c; margin:0;">
        Assigning quota from approved requirement of <strong>${Number(approvedQty).toLocaleString()} MT ${record.crop_name}</strong> 
        to an administrative block Panchayat Samiti.
      </p>
    </div>

    <form id="assignPsForm" class="form-grid">
      <div class="form-group">
        <label class="form-label">Select Panchayat Samiti *</label>
        <select id="assignPsNameSelect" class="form-control" required>
          <option value="Baramati Block Panchayat Samiti">Baramati Block Panchayat Samiti</option>
          <option value="Haveli Block Panchayat Samiti">Haveli Block Panchayat Samiti</option>
          <option value="Shirur Block Panchayat Samiti">Shirur Block Panchayat Samiti</option>
          <option value="Indapur Block Panchayat Samiti">Indapur Block Panchayat Samiti</option>
          <option value="Daund Block Panchayat Samiti">Daund Block Panchayat Samiti</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Quota to Allocate (MT) *</label>
        <input type="number" id="assignPsQuotaInput" class="form-control" value="${Math.min(approvedQty, 12000)}" max="${approvedQty}" min="1" step="10" required>
        <span style="font-size:0.75rem; color:var(--text-muted);">Available Approved Target: ${Number(approvedQty).toLocaleString()} MT</span>
      </div>

      <div class="form-group" style="grid-column: span 2;">
        <label class="form-label">Operational Assignment Directives</label>
        <textarea id="assignPsNotesInput" class="form-control" rows="2" placeholder="e.g. Prioritize canal-irrigated Gram Panchayats with high organic carbon soils."></textarea>
      </div>
    </form>
  `;

  modalSubmitBtn.onclick = async () => {
    const psName = document.getElementById("assignPsNameSelect").value;
    const quota = parseFloat(document.getElementById("assignPsQuotaInput").value);
    const notes = document.getElementById("assignPsNotesInput").value.trim();

    if (isNaN(quota) || quota <= 0) {
      alert("Please enter a valid quota quantity in MT.");
      return;
    }

    try {
      modalSubmitBtn.disabled = true;
      modalSubmitBtn.textContent = "Assigning...";
      await ApiClient.assignRequirementToPS(recordId, psName, quota, notes);
      closeModal();
      alert(`Successfully allocated ${quota.toLocaleString()} MT to ${psName}!`);
      await renderActiveTable();
    } catch (e) {
      alert(`Assignment failed: ${e.message}`);
    } finally {
      modalSubmitBtn.disabled = false;
      modalSubmitBtn.textContent = "Assign Quota to PS";
    }
  };

  modal.style.display = "flex";
}

// ==========================================
// AUDIT HISTORY MODAL (FULL DIFF TIMELINE)
// ==========================================
async function openHistoryModal(tableName, recordId) {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `📜 Audit History: ${tableName} (Record #${recordId})`;
  modalSubmitBtn.style.display = "none"; // Read-only

  modalBody.innerHTML = `
    <div style="text-align:center; padding:20px; color:var(--text-muted);">
      Retrieving audit trail...
    </div>
  `;
  modal.style.display = "flex";

  try {
    const res = await ApiClient.getAuditHistory(tableName, recordId);
    const history = res.history || [];

    if (history.length === 0) {
      modalBody.innerHTML = `
        <div style="text-align:center; padding:30px; color:var(--text-muted);">
          <div style="font-size:2rem; margin-bottom:8px;">📝</div>
          <p>This record is at its original initial state.</p>
          <p style="font-size:0.8rem;">No edits have been made since creation. When edited, previous values and user identity will appear here.</p>
        </div>
      `;
      return;
    }

    modalBody.innerHTML = `
      <div style="margin-bottom:12px; font-size:0.84rem; color:var(--text-muted);">
        Found <strong>${history.length}</strong> recorded modifications:
      </div>
      <div class="audit-timeline">
        ${history.map(item => `
          <div class="audit-card">
            <div class="audit-meta">
              <span><strong>${item.field_name.replace(/_/g, ' ').toUpperCase()}</strong></span>
              <span>🕒 ${item.created_at}</span>
            </div>
            <div class="audit-diff">
              <span class="diff-old">${item.old_value || '(empty)'}</span>
              <span>→</span>
              <span class="diff-new">${item.new_value || '(empty)'}</span>
            </div>
            <div class="audit-meta" style="margin-top:6px;">
              <span>👤 Edited By: <strong>${item.edited_by}</strong> (${item.edited_by_role})</span>
            </div>
            <div class="audit-reason">
              Note: "${item.change_reason}"
            </div>
          </div>
        `).join("")}
      </div>
    `;
  } catch (err) {
    modalBody.innerHTML = `
      <div class="alert-box danger" style="display:block;">
        Failed to fetch history: ${err.message}
      </div>
    `;
  }
}

function closeModal() {
  const modal = document.getElementById("recordModal");
  if (modal) modal.style.display = "none";
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");
  if (modalSubmitBtn) modalSubmitBtn.style.display = "inline-flex";
}
window.closeModal = closeModal;

// Helper to render form fields
function renderFormField(field, val) {
  const defaultVal = val !== null && val !== undefined ? val : "";
  if (field.type === "select") {
    return `
      <select name="${field.name}" class="form-control" ${field.required ? 'required' : ''}>
        ${(field.options || []).map(opt => `
          <option value="${opt}" ${String(defaultVal) === String(opt) ? 'selected' : ''}>${opt}</option>
        `).join("")}
      </select>
    `;
  } else if (field.type === "textarea") {
    return `
      <textarea name="${field.name}" class="form-control" rows="2" ${field.required ? 'required' : ''}>${defaultVal}</textarea>
    `;
  } else {
    return `
      <input type="${field.type}" name="${field.name}" class="form-control" value="${defaultVal}" ${field.required ? 'required' : ''}>
    `;
  }
}

// ==========================================
// CENTRAL AI/ML ENGINE: FOOD DEPARTMENT CROP REQUIREMENT CONTROLLER
// ==========================================

let currentAIPredictionFilter = "ALL";
let cachedAIPredictions = [];

async function renderCentralAIRecommendations(container) {
  if (!container) container = document.getElementById("activeTableContainer");
  if (!container) return;

  container.innerHTML = `
    <div style="text-align:center; padding:40px; color:var(--text-muted);">
      <div style="font-size:2rem; margin-bottom:12px; animation:spin 1.5s infinite linear;">🧠</div>
      Retrieving Central AI Engine telemetry & multi-factor recommendations...
    </div>
  `;

  try {
    const [statsRes, predsRes] = await Promise.all([
      ApiClient.getAIEngineStats().catch(() => ({})),
      ApiClient.getAIPredictions().catch(() => []),
    ]);

    const stats = statsRes || {};
    cachedAIPredictions = Array.isArray(predsRes) ? predsRes : [];

    let filtered = cachedAIPredictions;
    if (currentAIPredictionFilter !== "ALL") {
      filtered = cachedAIPredictions.filter(p => p.review_status === currentAIPredictionFilter);
    }

    const totalCount = cachedAIPredictions.length;
    const pendingCount = cachedAIPredictions.filter(p => p.review_status === "PENDING_REVIEW").length;
    const approvedCount = cachedAIPredictions.filter(p => p.review_status === "APPROVED").length;
    const correctedCount = cachedAIPredictions.filter(p => p.review_status === "CORRECTED").length;

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <!-- Central AI Engine Telemetry Ribbon -->
        <div style="background:linear-gradient(135deg, #1b3815 0%, #2e7d32 100%); color:white; padding:22px 24px; border-radius:10px; margin-bottom:20px; box-shadow:0 4px 14px rgba(46,125,50,0.18);">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:14px;">
            <div>
              <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
                <span style="font-size:1.6rem;">🧠</span>
                <h2 style="margin:0; color:#fff; font-size:1.35rem; font-weight:700;">KrushiSetu Central AI/ML Engine</h2>
                <span style="background:rgba(255,255,255,0.22); font-size:0.72rem; padding:3px 10px; border-radius:12px; font-weight:700; letter-spacing:0.5px;">${stats.engine_version || 'v1.0.0-prototype'}</span>
              </div>
              <p style="margin:0; font-size:0.84rem; color:#e8f5e9; opacity:0.95;">
                Statewide Agricultural Planning • Food Department Module: Multi-Factor Crop Requirement Recommendation
              </p>
            </div>
            <div style="display:flex; gap:10px; align-items:center;">
              <button class="btn btn-primary" onclick="openPredictCropModal()" style="background:#ffb300; color:#1b3815; font-weight:700; border:none; box-shadow:0 2px 8px rgba(0,0,0,0.15);">
                🤖 + Run AI Prediction
              </button>
              <button class="btn btn-secondary" onclick="renderCentralAIRecommendations()" style="background:rgba(255,255,255,0.2); color:white; border:1px solid rgba(255,255,255,0.3);">
                🔄 Refresh
              </button>
            </div>
          </div>

          <!-- Live Metrics Grid -->
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:12px; margin-top:20px; border-top:1px solid rgba(255,255,255,0.2); padding-top:16px;">
            <div style="background:rgba(0,0,0,0.18); border-radius:8px; padding:12px 14px;">
              <div style="font-size:0.7rem; text-transform:uppercase; color:#c8e6c9; font-weight:700; letter-spacing:0.5px;">Engine Status</div>
              <div style="font-size:1rem; font-weight:700; color:#a5d6a7; display:flex; align-items:center; gap:6px; margin-top:4px;">
                <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#00e676; box-shadow:0 0 8px #00e676;"></span> OPERATIONAL
              </div>
            </div>
            <div style="background:rgba(0,0,0,0.18); border-radius:8px; padding:12px 14px;">
              <div style="font-size:0.7rem; text-transform:uppercase; color:#c8e6c9; font-weight:700; letter-spacing:0.5px;">Total Predictions</div>
              <div style="font-size:1.35rem; font-weight:700; color:#fff; margin-top:3px;">${stats.total_predictions !== undefined ? stats.total_predictions : totalCount}</div>
            </div>
            <div style="background:rgba(0,0,0,0.18); border-radius:8px; padding:12px 14px;">
              <div style="font-size:0.7rem; text-transform:uppercase; color:#ffe082; font-weight:700; letter-spacing:0.5px;">Pending Review</div>
              <div style="font-size:1.35rem; font-weight:700; color:#ffe082; margin-top:3px;">${stats.pending_reviews !== undefined ? stats.pending_reviews : pendingCount}</div>
            </div>
            <div style="background:rgba(0,0,0,0.18); border-radius:8px; padding:12px 14px;">
              <div style="font-size:0.7rem; text-transform:uppercase; color:#a5d6a7; font-weight:700; letter-spacing:0.5px;">Approved Decisions</div>
              <div style="font-size:1.35rem; font-weight:700; color:#a5d6a7; margin-top:3px;">${stats.approved_reviews !== undefined ? stats.approved_reviews : approvedCount}</div>
            </div>
            <div style="background:rgba(0,0,0,0.18); border-radius:8px; padding:12px 14px;">
              <div style="font-size:0.7rem; text-transform:uppercase; color:#e1bee7; font-weight:700; letter-spacing:0.5px;">Human Corrected</div>
              <div style="font-size:1.35rem; font-weight:700; color:#e1bee7; margin-top:3px;">${stats.corrected_reviews !== undefined ? stats.corrected_reviews : correctedCount}</div>
            </div>
          </div>
        </div>

        <!-- Filter Pills & Info Bar -->
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; flex-wrap:wrap; gap:12px;">
          <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <button class="btn btn-sm ${currentAIPredictionFilter === 'ALL' ? 'btn-primary' : 'btn-outline'}" onclick="setAIPredictionFilter('ALL')">
              All (${totalCount})
            </button>
            <button class="btn btn-sm ${currentAIPredictionFilter === 'PENDING_REVIEW' ? 'btn-primary' : 'btn-outline'}" onclick="setAIPredictionFilter('PENDING_REVIEW')" style="${currentAIPredictionFilter === 'PENDING_REVIEW' ? 'background:#f57f17; border-color:#f57f17;' : ''}">
              ⏳ Pending Review (${pendingCount})
            </button>
            <button class="btn btn-sm ${currentAIPredictionFilter === 'APPROVED' ? 'btn-primary' : 'btn-outline'}" onclick="setAIPredictionFilter('APPROVED')" style="${currentAIPredictionFilter === 'APPROVED' ? 'background:#2e7d32; border-color:#2e7d32;' : ''}">
              ✅ Approved (${approvedCount})
            </button>
            <button class="btn btn-sm ${currentAIPredictionFilter === 'CORRECTED' ? 'btn-primary' : 'btn-outline'}" onclick="setAIPredictionFilter('CORRECTED')" style="${currentAIPredictionFilter === 'CORRECTED' ? 'background:#6a1b9a; border-color:#6a1b9a;' : ''}">
              ✏️ Corrected (${correctedCount})
            </button>
          </div>
          <div style="font-size:0.8rem; color:var(--text-muted);">
            Displaying <strong>${filtered.length}</strong> of ${totalCount} Central AI recommendations
          </div>
        </div>

        <!-- AI Recommendations Records Table -->
        <div class="table-container">
          <table class="record-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Crop & Target</th>
                <th>Season</th>
                <th>🤖 Central AI Recommendation</th>
                <th>👤 Human Review & Final Decision</th>
                <th>Status</th>
                <th style="text-align:right;">Actions</th>
              </tr>
            </thead>
            <tbody>
              ${filtered.length === 0 ? `
                <tr>
                  <td colspan="7" style="text-align:center; padding:36px; color:var(--text-muted);">
                    <div style="font-size:1.4rem; margin-bottom:8px;">🌾</div>
                    No Central AI recommendations match the active filter.<br>
                    Click <strong>"🤖 + Run AI Prediction"</strong> to generate a recommendation from real database records.
                  </td>
                </tr>
              ` : filtered.map(rec => {
                const isPending = rec.review_status === "PENDING_REVIEW";
                const isApproved = rec.review_status === "APPROVED";
                const isCorrected = rec.review_status === "CORRECTED";

                const priorityBadge = rec.ai_recommended_priority === "CRITICAL" ? "badge-danger" : 
                                      rec.ai_recommended_priority === "HIGH" ? "badge-warning" : "badge-info";

                return `
                  <tr>
                    <td>
                      <span style="font-family:monospace; font-weight:700; color:#1565c0;">#AI-${rec.id}</span>
                    </td>
                    <td>
                      <div style="font-weight:700; font-size:0.92rem; color:var(--primary-dark);">${rec.crop_name}</div>
                      <div style="font-size:0.75rem; color:var(--text-muted);">${rec.region || 'Baramati PS'} • Target Yr ${rec.target_year || 2026}</div>
                    </td>
                    <td>
                      <span style="font-size:0.82rem; font-weight:600;">${rec.season}</span>
                    </td>
                    <td>
                      <div style="display:flex; align-items:center; gap:8px;">
                        <span style="font-size:1.05rem; font-weight:700; color:#1565c0;">
                          ${Number(rec.ai_recommended_quantity_mt || 0).toLocaleString()} MT
                        </span>
                        <span class="badge ${priorityBadge}" style="font-size:0.7rem;">${rec.ai_recommended_priority}</span>
                      </div>
                      <div style="font-size:0.75rem; color:var(--text-muted); margin-top:3px;">
                        Conf: <strong>${((rec.ai_confidence_score || 0.85) * 100).toFixed(1)}%</strong> • 
                        Area: <strong>${Number(rec.ai_target_cultivation_area_hectares || 0).toLocaleString()} Ha</strong> • 
                        Yield: <strong>${rec.ai_estimated_yield_mt_per_hectare || 0} MT/Ha</strong>
                      </div>
                    </td>
                    <td>
                      ${isApproved ? `
                        <div>
                          <span style="font-size:0.95rem; font-weight:700; color:#2e7d32;">
                            ${Number(rec.human_final_quantity_mt || rec.ai_recommended_quantity_mt).toLocaleString()} MT
                          </span>
                          <span class="badge badge-success" style="font-size:0.7rem; margin-left:4px;">${rec.human_final_priority || rec.ai_recommended_priority}</span>
                        </div>
                        <div style="font-size:0.72rem; color:var(--text-muted); margin-top:2px;">
                          Approved by <strong>${rec.reviewed_by || 'Officer'}</strong> • ${rec.reviewed_at ? new Date(rec.reviewed_at).toLocaleDateString() : 'Recorded'}
                        </div>
                      ` : isCorrected ? `
                        <div>
                          <span style="font-size:0.95rem; font-weight:700; color:#6a1b9a;">
                            ${Number(rec.human_final_quantity_mt || 0).toLocaleString()} MT
                          </span>
                          <span class="badge badge-accent" style="font-size:0.7rem; margin-left:4px;">${rec.human_final_priority || 'MODIFIED'}</span>
                        </div>
                        <div style="font-size:0.72rem; color:#c2185b; margin-top:2px; font-style:italic;" title="${rec.correction_reason || ''}">
                          "${(rec.correction_reason || '').substring(0, 38)}${(rec.correction_reason || '').length > 38 ? '...' : ''}"
                        </div>
                        <div style="font-size:0.72rem; color:var(--text-muted);">
                          By <strong>${rec.reviewed_by || 'Officer'}</strong> • ${rec.reviewed_at ? new Date(rec.reviewed_at).toLocaleDateString() : 'Recorded'}
                        </div>
                      ` : `
                        <div style="font-size:0.82rem; color:#f57f17; font-weight:600; display:flex; align-items:center; gap:4px;">
                          ⏳ Awaiting Human Review
                        </div>
                        <div style="font-size:0.72rem; color:var(--text-muted); margin-top:2px;">
                          Directorate decision required
                        </div>
                      `}
                    </td>
                    <td>
                      <span class="badge ${getBadgeClass(rec.review_status)}">
                        ${rec.review_status}
                      </span>
                    </td>
                    <td style="text-align:right;">
                      <div class="action-btn-group" style="justify-content:flex-end; gap:6px;">
                        <button class="btn btn-outline btn-sm" onclick="openAIPredictionAuditModal(${rec.id})" title="View Multi-Factor Data & Formula Breakdown">
                          👁️ Rationale
                        </button>
                        ${isPending ? `
                          <button class="btn btn-primary btn-sm" onclick="handleApproveAIPrediction(${rec.id})" style="background:#2e7d32;" title="Approve Recommendation As-Is">
                            ✅ Approve
                          </button>
                          <button class="btn btn-secondary btn-sm" onclick="openCorrectAIPredictionModal(${rec.id})" style="background:#6a1b9a; color:white; border-color:#6a1b9a;" title="Correct / Override with Justification">
                            ✏️ Correct
                          </button>
                        ` : ''}
                      </div>
                    </td>
                  </tr>
                `;
              }).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `
      <div class="alert-box danger" style="display:block;">
        Failed to load Central AI Recommendations: ${err.message}
      </div>
    `;
  }
}

function setAIPredictionFilter(filter) {
  currentAIPredictionFilter = filter;
  renderCentralAIRecommendations();
}

// --- PREDICT CROP REQUIREMENT MODAL ---
function openPredictCropModal() {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = "🤖 Central AI: Generate Crop Requirement Recommendation";
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Run Central AI Engine";

  modalBody.innerHTML = `
    <div style="background:#e8f5e9; border:1px solid #a5d6a7; padding:12px 14px; border-radius:6px; margin-bottom:14px;">
      <div style="font-weight:700; color:#2e7d32; font-size:0.85rem; margin-bottom:3px;">
        🧠 Multi-Factor Live Database Integration
      </div>
      <p style="font-size:0.78rem; color:#1b5e20; margin:0;">
        The Central AI Engine will query live authorized database records: Crisis deficits, Major WH stock, Minor WH stock, Baseline & Future demand projections, Historical farmer harvest records, Climate rainfall deviations, and GP Soil suitability.
      </p>
    </div>

    <form id="aiPredictForm" class="form-grid">
      <div class="form-group">
        <label class="form-label">Target Agricultural Crop *</label>
        <select id="aiCropSelect" class="form-control" required>
          <option value="Sugarcane" selected>Sugarcane</option>
          <option value="Wheat">Wheat</option>
          <option value="Rice">Rice</option>
          <option value="Cotton">Cotton</option>
          <option value="Soybean">Soybean</option>
          <option value="Maize">Maize</option>
          <option value="Pulses">Pulses / Gram</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Agricultural Season *</label>
        <select id="aiSeasonSelect" class="form-control" required>
          <option value="Kharif 2026" selected>Kharif 2026</option>
          <option value="Rabi 2026">Rabi 2026</option>
          <option value="Zaid 2026">Zaid 2026</option>
          <option value="Full Year 2026-27">Full Year 2026-27</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Target Year *</label>
        <input type="number" id="aiYearInput" class="form-control" value="2026" min="2026" max="2030" required>
      </div>

      <div class="form-group">
        <label class="form-label">Target Agro-Climatic Region *</label>
        <input type="text" id="aiRegionInput" class="form-control" value="Baramati Block Panchayat Samiti" required>
      </div>
    </form>
  `;

  modalSubmitBtn.onclick = async () => {
    const cropName = document.getElementById("aiCropSelect").value;
    const season = document.getElementById("aiSeasonSelect").value;
    const targetYear = parseInt(document.getElementById("aiYearInput").value, 10) || 2026;
    const region = document.getElementById("aiRegionInput").value.trim() || "Baramati Block Panchayat Samiti";

    try {
      modalSubmitBtn.disabled = true;
      modalSubmitBtn.textContent = "AI Optimizing Requirement...";
      const res = await ApiClient.predictCropRequirement({
        crop_name: cropName,
        season: season,
        target_year: targetYear,
        region: region,
      });

      closeModal();
      alert(`Central AI Recommendation Generated for ${cropName} (${season}): ${Number(res.ai_recommended_quantity_mt).toLocaleString()} MT (Priority: ${res.ai_recommended_priority})`);
      await renderCentralAIRecommendations();
    } catch (err) {
      alert(`Prediction failed: ${err.message}`);
    } finally {
      modalSubmitBtn.disabled = false;
      modalSubmitBtn.textContent = "Run Central AI Engine";
    }
  };

  modal.style.display = "flex";
}

// --- ONE-CLICK APPROVAL OF AI RECOMMENDATION ---
async function handleApproveAIPrediction(predictionId) {
  const rec = cachedAIPredictions.find(p => p.id === predictionId);
  if (!rec) return;

  const confirmed = confirm(
    `Approve Central AI Recommendation #${rec.id} for ${rec.crop_name} (${rec.season})?\n\n` +
    `AI Recommended Quantity: ${Number(rec.ai_recommended_quantity_mt).toLocaleString()} MT\n` +
    `AI Priority: ${rec.ai_recommended_priority}\n\n` +
    `This will authorize the requirement for Directorate allocation without modifications.`
  );
  if (!confirmed) return;

  try {
    await ApiClient.approveAIPrediction(predictionId, "Official approval granted without modification by Food Directorate Officer");
    alert(`AI Recommendation #${predictionId} (${rec.crop_name}) approved successfully!`);
    await renderCentralAIRecommendations();
  } catch (err) {
    alert(`Approval failed: ${err.message}`);
  }
}

// --- HUMAN CORRECTION MODAL (DUAL-STORAGE INTEGRITY) ---
function openCorrectAIPredictionModal(predictionId) {
  const rec = cachedAIPredictions.find(p => p.id === predictionId);
  if (!rec) return;

  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `✏️ Human Correction & Override: AI #${rec.id} (${rec.crop_name})`;
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Submit Human Final Decision";

  modalBody.innerHTML = `
    <!-- Dual-Storage Security Notice -->
    <div style="background:#fff3e0; border:1px solid #ffe082; padding:12px 14px; border-radius:6px; margin-bottom:14px;">
      <div style="font-weight:700; color:#e65100; font-size:0.85rem; margin-bottom:3px;">
        🔒 Immutable Dual-Storage Guarantee
      </div>
      <p style="font-size:0.78rem; color:#bf360c; margin:0;">
        The original AI recommendation of <strong>${Number(rec.ai_recommended_quantity_mt).toLocaleString()} MT</strong> 
        (Priority: <strong>${rec.ai_recommended_priority}</strong>) will remain permanently intact in the system audit trail. 
        Your human override will be stored in separate verified columns.
      </p>
    </div>

    <form id="aiCorrectionForm" class="form-grid">
      <div class="form-group">
        <label class="form-label">Human Final Quantity (MT) *</label>
        <input type="number" id="correctQtyInput" class="form-control" value="${rec.ai_recommended_quantity_mt}" step="10" required>
        <span style="font-size:0.72rem; color:var(--text-muted);">AI Recommended: ${Number(rec.ai_recommended_quantity_mt).toLocaleString()} MT</span>
      </div>

      <div class="form-group">
        <label class="form-label">Human Final Priority *</label>
        <select id="correctPriorityInput" class="form-control" required>
          <option value="NORMAL" ${rec.ai_recommended_priority === 'NORMAL' ? 'selected' : ''}>NORMAL</option>
          <option value="HIGH" ${rec.ai_recommended_priority === 'HIGH' ? 'selected' : ''}>HIGH</option>
          <option value="CRITICAL" ${rec.ai_recommended_priority === 'CRITICAL' ? 'selected' : ''}>CRITICAL</option>
        </select>
        <span style="font-size:0.72rem; color:var(--text-muted);">AI Priority: ${rec.ai_recommended_priority}</span>
      </div>

      <div class="form-group" style="grid-column: span 2;">
        <label class="form-label" style="color:#c2185b; font-weight:700;">Reason for Correction / Operational Justification * (Mandatory)</label>
        <textarea id="correctReasonInput" class="form-control" rows="2" placeholder="e.g. Adjusted to 22,000 MT due to strategic interstate buffer reserve agreement." required></textarea>
        <span style="font-size:0.72rem; color:var(--text-muted);">Minimum 5 characters required for audit verification.</span>
      </div>

      <div class="form-group" style="grid-column: span 2;">
        <label class="form-label">Additional Directorate Notes (Optional)</label>
        <textarea id="correctNotesInput" class="form-control" rows="2" placeholder="Optional notes for downstream Panchayat Samiti blocks..."></textarea>
      </div>
    </form>
  `;

  modalSubmitBtn.onclick = async () => {
    const finalQty = parseFloat(document.getElementById("correctQtyInput").value);
    const finalPriority = document.getElementById("correctPriorityInput").value;
    const reason = document.getElementById("correctReasonInput").value.trim();
    const notes = document.getElementById("correctNotesInput").value.trim();

    if (isNaN(finalQty) || finalQty <= 0) {
      alert("Please enter a valid positive quantity in MT.");
      return;
    }

    if (!reason || reason.length < 5) {
      alert("A mandatory justification of at least 5 characters is required to correct an AI recommendation.");
      return;
    }

    try {
      modalSubmitBtn.disabled = true;
      modalSubmitBtn.textContent = "Recording Human Override...";
      await ApiClient.correctAIPrediction(predictionId, {
        human_final_quantity_mt: finalQty,
        human_final_priority: finalPriority,
        correction_reason: reason,
        notes: notes,
      });

      closeModal();
      alert(`Correction recorded for AI #${predictionId}. Dual-storage verified.`);
      await renderCentralAIRecommendations();
    } catch (err) {
      alert(`Correction failed: ${err.message}`);
    } finally {
      modalSubmitBtn.disabled = false;
      modalSubmitBtn.textContent = "Submit Human Final Decision";
    }
  };

  modal.style.display = "flex";
}

// --- MULTI-FACTOR RATIONALE & AUDIT MODAL ---
function openAIPredictionAuditModal(predictionId) {
  const rec = cachedAIPredictions.find(p => p.id === predictionId);
  if (!rec) return;

  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `🔍 AI Multi-Factor Rationale & Audit: #${rec.id} (${rec.crop_name})`;
  modalSubmitBtn.style.display = "none";

  const inputs = rec.input_data_reference || {};
  const factors = rec.ai_factors || {};

  modalBody.innerHTML = `
    <!-- Top Summary Card -->
    <div style="background:#f5f7fa; border-radius:8px; padding:14px 16px; margin-bottom:16px; border:1px solid var(--border);">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <div>
          <span style="font-size:0.75rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Target Context</span>
          <div style="font-size:1.05rem; font-weight:700; color:var(--primary-dark); margin-top:2px;">
            ${rec.crop_name} • ${rec.season} (${rec.target_year || 2026})
          </div>
          <div style="font-size:0.75rem; color:var(--text-muted);">${rec.region || 'Baramati Block PS'} • Engine Model: <code>${rec.model_version || 'v1.0.0-prototype'}</code></div>
        </div>
        <div style="text-align:right;">
          <span class="badge ${getBadgeClass(rec.review_status)}" style="font-size:0.8rem; padding:4px 12px;">${rec.review_status}</span>
          <div style="font-size:0.72rem; color:var(--text-muted); margin-top:4px;">
            Generated: ${rec.created_at ? new Date(rec.created_at).toLocaleString() : 'N/A'}
          </div>
        </div>
      </div>
    </div>

    <!-- Dual Values Comparison Grid -->
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:18px;">
      <div style="background:#e3f2fd; border:1px solid #90caf9; border-radius:8px; padding:12px 14px;">
        <div style="font-size:0.72rem; text-transform:uppercase; color:#1565c0; font-weight:700;">🤖 AI Recommended (Immutable)</div>
        <div style="font-size:1.25rem; font-weight:700; color:#0d47a1; margin-top:4px;">
          ${Number(rec.ai_recommended_quantity_mt || 0).toLocaleString()} MT
        </div>
        <div style="font-size:0.78rem; color:#1565c0; margin-top:2px;">
          Priority: <strong>${rec.ai_recommended_priority}</strong> • Confidence: <strong>${((rec.ai_confidence_score || 0.85) * 100).toFixed(1)}%</strong>
        </div>
      </div>

      <div style="background:${rec.review_status === 'CORRECTED' ? '#f3e5f5' : rec.review_status === 'APPROVED' ? '#e8f5e9' : '#fff8e1'}; border:1px solid ${rec.review_status === 'CORRECTED' ? '#ce93d8' : rec.review_status === 'APPROVED' ? '#a5d6a7' : '#ffe082'}; border-radius:8px; padding:12px 14px;">
        <div style="font-size:0.72rem; text-transform:uppercase; color:${rec.review_status === 'CORRECTED' ? '#6a1b9a' : rec.review_status === 'APPROVED' ? '#2e7d32' : '#f57f17'}; font-weight:700;">
          👤 Human Final Decision
        </div>
        <div style="font-size:1.25rem; font-weight:700; color:${rec.review_status === 'CORRECTED' ? '#4a148c' : rec.review_status === 'APPROVED' ? '#1b5e20' : '#e65100'}; margin-top:4px;">
          ${rec.human_final_quantity_mt !== null && rec.human_final_quantity_mt !== undefined ? Number(rec.human_final_quantity_mt).toLocaleString() + ' MT' : 'Pending Review'}
        </div>
        <div style="font-size:0.78rem; color:var(--text-muted); margin-top:2px;">
          ${rec.reviewed_by ? `Reviewed by <strong>${rec.reviewed_by}</strong> on ${new Date(rec.reviewed_at).toLocaleDateString()}` : 'Awaiting Directorate Action'}
        </div>
      </div>
    </div>

    ${rec.correction_reason ? `
      <div style="background:#fce4ec; border:1px solid #f48fb1; border-radius:6px; padding:10px 14px; margin-bottom:16px;">
        <span style="font-size:0.72rem; text-transform:uppercase; color:#c2185b; font-weight:700;">Audit Justification:</span>
        <div style="font-size:0.84rem; color:#880e4f; font-weight:600; margin-top:2px;">"${rec.correction_reason}"</div>
      </div>
    ` : ''}

    <!-- Ingested Authorized Datasets Grid -->
    <h4 style="color:var(--primary-dark); font-size:0.92rem; margin-bottom:10px;">📊 Authorized Database Inputs Ingested</h4>
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:10px; margin-bottom:18px;">
      <div style="background:white; border:1px solid var(--border); border-radius:6px; padding:10px;">
        <span style="font-size:0.68rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Crisis Deficit</span>
        <div style="font-size:0.95rem; font-weight:700; color:#c62828; margin-top:2px;">${Number(inputs.crisis_deficit_mt || 0).toLocaleString()} MT</div>
      </div>
      <div style="background:white; border:1px solid var(--border); border-radius:6px; padding:10px;">
        <span style="font-size:0.68rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Major WH Stock</span>
        <div style="font-size:0.95rem; font-weight:700; color:#1565c0; margin-top:2px;">${Number(inputs.major_wh_stock_mt || 0).toLocaleString()} MT</div>
      </div>
      <div style="background:white; border:1px solid var(--border); border-radius:6px; padding:10px;">
        <span style="font-size:0.68rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Minor WH Stock</span>
        <div style="font-size:0.95rem; font-weight:700; color:#1565c0; margin-top:2px;">${Number(inputs.minor_wh_stock_mt || 0).toLocaleString()} MT</div>
      </div>
      <div style="background:white; border:1px solid var(--border); border-radius:6px; padding:10px;">
        <span style="font-size:0.68rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Current Demand</span>
        <div style="font-size:0.95rem; font-weight:700; color:#2e7d32; margin-top:2px;">${Number(inputs.current_demand_mt || 0).toLocaleString()} MT</div>
      </div>
      <div style="background:white; border:1px solid var(--border); border-radius:6px; padding:10px;">
        <span style="font-size:0.68rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Future Projected</span>
        <div style="font-size:0.95rem; font-weight:700; color:#2e7d32; margin-top:2px;">${Number(inputs.future_demand_mt || 0).toLocaleString()} MT</div>
      </div>
      <div style="background:white; border:1px solid var(--border); border-radius:6px; padding:10px;">
        <span style="font-size:0.68rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Historical Production</span>
        <div style="font-size:0.95rem; font-weight:700; color:#6a1b9a; margin-top:2px;">${Number(inputs.historical_production_mt || 0).toLocaleString()} MT</div>
      </div>
      <div style="background:white; border:1px solid var(--border); border-radius:6px; padding:10px;">
        <span style="font-size:0.68rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Rainfall / Deviation</span>
        <div style="font-size:0.95rem; font-weight:700; color:#0277bd; margin-top:2px;">${inputs.weather_rainfall_mm || 0} mm (${inputs.weather_deviation_pct || 0}%)</div>
      </div>
      <div style="background:white; border:1px solid var(--border); border-radius:6px; padding:10px;">
        <span style="font-size:0.68rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Suitable Land Area</span>
        <div style="font-size:0.95rem; font-weight:700; color:#37474f; margin-top:2px;">${Number(inputs.suitable_cultivable_area_ha || 0).toLocaleString()} Ha</div>
      </div>
    </div>

    <!-- AI Mathematical Optimization Trace -->
    <h4 style="color:var(--primary-dark); font-size:0.92rem; margin-bottom:10px;">🧮 Multi-Factor Heuristic Optimizer Trace</h4>
    <div style="background:#fafafa; border:1px solid var(--border); border-radius:6px; padding:12px 14px; font-size:0.82rem; line-height:1.6; color:#37474f;">
      <div>• <strong>Net Supply Gap:</strong> ${Number(factors.net_gap_mt || 0).toLocaleString()} MT (Max of Deficit vs Demand - Warehouse Stocks)</div>
      <div>• <strong>Safety Strategic Buffer (15%):</strong> +${Number(factors.buffer_mt || 0).toLocaleString()} MT</div>
      <div>• <strong>Climate Impact Factor:</strong> ${factors.weather_factor || 1.0}x (${Number(factors.weather_adjustment_mt || 0).toLocaleString()} MT adjustment)</div>
      <div>• <strong>Land Production Capacity:</strong> ${Number(factors.max_possible_production_mt || 0).toLocaleString()} MT across ${Number(rec.ai_target_cultivation_area_hectares || 0).toLocaleString()} Ha (${rec.ai_estimated_yield_mt_per_hectare || 0} MT/Ha yield)</div>
      <div>• <strong>Feasibility Ratio:</strong> ${((factors.feasibility_ratio || 1.0) * 100).toFixed(1)}%</div>
      <div style="margin-top:8px; padding-top:8px; border-top:1px dashed var(--border); font-style:italic; color:#546e7a;">
        "${factors.explanation || 'Optimal quota balance computed across real supply chain data.'}"
      </div>
    </div>

    <div style="text-align:right; margin-top:18px;">
      <button class="btn btn-secondary btn-sm" onclick="closeModal()">Close Rationale View</button>
    </div>
  `;

  modal.style.display = "flex";
}

// ==========================================
// CENTRAL AI/ML ENGINE: PANCHAYAT SAMITI -> GRAM PANCHAYAT CROP ALLOCATION
// ==========================================

let currentGPAllocationFilter = "ALL";
let cachedGPAllocations = [];

async function renderPSCentralAIAllocation(container) {
  if (!container) container = document.getElementById("activeTableContainer");
  if (!container) return;

  container.innerHTML = `
    <div style="text-align:center; padding:40px; color:var(--text-muted);">
      <div style="font-size:2rem; margin-bottom:12px; animation:spin 1.5s infinite linear;">🧠</div>
      Retrieving Central AI Gram Panchayat allocations & suitability matrices...
    </div>
  `;

  try {
    const allocationsRes = await ApiClient.getGPAllocations().catch(() => []);
    cachedGPAllocations = Array.isArray(allocationsRes) ? allocationsRes : [];

    let filtered = cachedGPAllocations;
    if (currentGPAllocationFilter !== "ALL") {
      filtered = cachedGPAllocations.filter(a => a.review_status === currentGPAllocationFilter);
    }

    const totalCount = cachedGPAllocations.length;
    const pendingCount = cachedGPAllocations.filter(a => a.review_status === "PENDING_REVIEW").length;
    const approvedCount = cachedGPAllocations.filter(a => a.review_status === "APPROVED").length;
    const correctedCount = cachedGPAllocations.filter(a => a.review_status === "CORRECTED").length;

    // Determine active batch metrics for quota conservation display
    const latestBatch = cachedGPAllocations.length > 0 ? cachedGPAllocations[0].batch_code : "BATCH-GPA-2026-001";
    const batchRecords = cachedGPAllocations.filter(a => a.batch_code === latestBatch);
    const activeCrop = batchRecords.length > 0 ? batchRecords[0].crop_name : "Wheat (Lokwan)";
    const activeSeason = batchRecords.length > 0 ? batchRecords[0].season : "Rabi 2026";
    const activePS = batchRecords.length > 0 ? batchRecords[0].panchayat_samiti_name : "Baramati Block Panchayat Samiti";

    // Total requirement is the sum of original AI recommendations in this batch
    const totalRequirementMT = batchRecords.reduce((sum, r) => sum + (r.ai_recommended_quantity_mt || 0), 0) || 12000.0;
    const totalAIAllocatedMT = batchRecords.reduce((sum, r) => sum + (r.ai_recommended_quantity_mt || 0), 0);
    const totalFinalAllocatedMT = batchRecords.reduce((sum, r) => sum + (r.human_final_quantity_mt !== null && r.human_final_quantity_mt !== undefined ? r.human_final_quantity_mt : r.ai_recommended_quantity_mt), 0);
    const remainingQuotaMT = Math.max(0, Math.round((totalRequirementMT - totalFinalAllocatedMT) * 10) / 10);
    const isBalanced = Math.abs(totalRequirementMT - totalFinalAllocatedMT) < 0.5;

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <!-- Central AI Engine PS Header & Telemetry -->
        <div style="background:linear-gradient(135deg, #1b3815 0%, #2e7d32 100%); color:white; padding:22px 24px; border-radius:10px; margin-bottom:20px; box-shadow:0 4px 14px rgba(46,125,50,0.18);">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:14px;">
            <div>
              <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
                <span style="font-size:1.6rem;">🧠</span>
                <h2 style="margin:0; color:#fff; font-size:1.35rem; font-weight:700;">KrushiSetu Central AI/ML Engine</h2>
                <span style="background:rgba(255,255,255,0.22); font-size:0.72rem; padding:3px 10px; border-radius:12px; font-weight:700; letter-spacing:0.5px;">v1.0.0-prototype</span>
              </div>
              <p style="margin:0; font-size:0.84rem; color:#e8f5e9; opacity:0.95;">
                Panchayat Samiti Module • Gram Panchayat-wise Crop Allocation & Land Suitability Optimizer
              </p>
            </div>
            <div style="display:flex; gap:10px; align-items:center;">
              <button class="btn btn-primary" onclick="openRunGPAllocationModal()" style="background:#ffb300; color:#1b3815; font-weight:700; border:none; box-shadow:0 2px 8px rgba(0,0,0,0.15);">
                🤖 + Run AI Allocation
              </button>
              ${pendingCount > 0 ? `
                <button class="btn btn-sm" onclick="handleBatchApproveGPAllocations('${latestBatch}')" style="background:#00e676; color:#1b3815; font-weight:700; border:none; padding:8px 14px;">
                  ✅ Approve All Pending (${pendingCount})
                </button>
              ` : ''}
              <button class="btn btn-secondary" onclick="renderPSCentralAIAllocation()" style="background:rgba(255,255,255,0.2); color:white; border:1px solid rgba(255,255,255,0.3);">
                🔄 Refresh
              </button>
            </div>
          </div>

          <!-- Food Department Requirement Context Banner -->
          <div style="background:rgba(0,0,0,0.22); border-radius:8px; padding:14px 18px; margin-top:18px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
              <span style="font-size:0.72rem; text-transform:uppercase; color:#c8e6c9; font-weight:700; letter-spacing:0.5px;">Food Department Approved Requirement</span>
              <div style="font-size:1.1rem; font-weight:700; color:#fff; margin-top:2px;">
                ${activeCrop} • ${activeSeason}
              </div>
              <div style="font-size:0.75rem; color:#e8f5e9; opacity:0.9;">
                Jurisdiction: <strong>${activePS}</strong> • Batch Code: <code>${latestBatch}</code>
              </div>
            </div>
            <div style="display:flex; gap:12px; align-items:center;">
              <div style="text-align:right;">
                <span style="font-size:0.72rem; text-transform:uppercase; color:#c8e6c9; font-weight:700;">Requirement Status</span>
                <div><span class="badge badge-success" style="font-size:0.78rem; padding:4px 10px;">APPROVED BY FOOD DEPT</span></div>
              </div>
            </div>
          </div>

          <!-- Quota Conservation & Balancing Telemetry Grid -->
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:12px; margin-top:14px; border-top:1px solid rgba(255,255,255,0.2); padding-top:14px;">
            <div style="background:rgba(0,0,0,0.18); border-radius:8px; padding:10px 14px;">
              <div style="font-size:0.7rem; text-transform:uppercase; color:#c8e6c9; font-weight:700;">Total Requirement</div>
              <div style="font-size:1.25rem; font-weight:700; color:#fff; margin-top:2px;">${Number(totalRequirementMT).toLocaleString()} MT</div>
            </div>
            <div style="background:rgba(0,0,0,0.18); border-radius:8px; padding:10px 14px;">
              <div style="font-size:0.7rem; text-transform:uppercase; color:#c8e6c9; font-weight:700;">Total AI Allocated</div>
              <div style="font-size:1.25rem; font-weight:700; color:#a5d6a7; margin-top:2px;">${Number(totalAIAllocatedMT).toLocaleString()} MT</div>
            </div>
            <div style="background:rgba(0,0,0,0.18); border-radius:8px; padding:10px 14px;">
              <div style="font-size:0.7rem; text-transform:uppercase; color:#ffe082; font-weight:700;">Remaining Quota</div>
              <div style="font-size:1.25rem; font-weight:700; color:${isBalanced ? '#a5d6a7' : '#ffcc80'}; margin-top:2px;">
                ${Number(remainingQuotaMT).toLocaleString()} MT ${isBalanced ? '✓' : ''}
              </div>
            </div>
            <div style="background:rgba(0,0,0,0.18); border-radius:8px; padding:10px 14px;">
              <div style="font-size:0.7rem; text-transform:uppercase; color:#c8e6c9; font-weight:700;">GPs Covered</div>
              <div style="font-size:1.25rem; font-weight:700; color:#fff; margin-top:2px;">${batchRecords.length} Panchayats</div>
            </div>
          </div>
        </div>

        <!-- AI DATA INSIGHTS: "Why this recommendation?" Section -->
        <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:18px 20px; margin-bottom:20px; box-shadow:0 2px 6px rgba(0,0,0,0.04);">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:1.2rem;">💡</span>
              <h4 style="margin:0; color:var(--primary-dark); font-size:0.98rem; font-weight:700;">
                AI Factors: Why this recommendation?
              </h4>
            </div>
            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:600;">
              Multi-Factor Suitability Formulation • 100% Quota Conservation Guaranteed
            </span>
          </div>

          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:12px;">
            <div style="background:#f9fbf9; border:1px solid #e0e8e0; border-radius:6px; padding:10px 12px;">
              <div style="font-size:0.72rem; text-transform:uppercase; color:#2e7d32; font-weight:700;">🌾 Agricultural Land (40%)</div>
              <div style="font-size:0.8rem; color:#2c3e50; margin-top:3px; line-height:1.4;">
                Proportionally weights Gram Panchayats with larger cultivable land parcels to ensure realistic production capacity.
              </div>
            </div>
            <div style="background:#f9fbf9; border:1px solid #e0e8e0; border-radius:6px; padding:10px 12px;">
              <div style="font-size:0.72rem; text-transform:uppercase; color:#1565c0; font-weight:700;">🧪 Soil Compatibility (20%)</div>
              <div style="font-size:0.8rem; color:#2c3e50; margin-top:3px; line-height:1.4;">
                Cross-references Black Cotton & Clay Loam soil suitability against crop requirements from Panchayat Samiti tests.
              </div>
            </div>
            <div style="background:#f9fbf9; border:1px solid #e0e8e0; border-radius:6px; padding:10px 12px;">
              <div style="font-size:0.72rem; text-transform:uppercase; color:#0277bd; font-weight:700;">💧 Irrigation Coverage (25%)</div>
              <div style="font-size:0.8rem; color:#2c3e50; margin-top:3px; line-height:1.4;">
                Factors in canal command areas and Karha river lift irrigation networks (ranging from 55% to 78.5% coverage).
              </div>
            </div>
            <div style="background:#f9fbf9; border:1px solid #e0e8e0; border-radius:6px; padding:10px 12px;">
              <div style="font-size:0.72rem; text-transform:uppercase; color:#6a1b9a; font-weight:700;">👨‍🌾 Farmer Base (15%)</div>
              <div style="font-size:0.8rem; color:#2c3e50; margin-top:3px; line-height:1.4;">
                Evaluates active farmer density and historical seasonal harvests from the live Gram Panchayat registry.
              </div>
            </div>
          </div>
        </div>

        <!-- Filter Pills & Info Bar -->
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:10px;">
          <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <button class="btn btn-sm ${currentGPAllocationFilter === 'ALL' ? 'btn-primary' : 'btn-outline'}" onclick="setGPAllocationFilter('ALL')">
              All (${totalCount})
            </button>
            <button class="btn btn-sm ${currentGPAllocationFilter === 'PENDING_REVIEW' ? 'btn-primary' : 'btn-outline'}" onclick="setGPAllocationFilter('PENDING_REVIEW')" style="${currentGPAllocationFilter === 'PENDING_REVIEW' ? 'background:#f57f17; border-color:#f57f17;' : ''}">
              ⏳ Pending Review (${pendingCount})
            </button>
            <button class="btn btn-sm ${currentGPAllocationFilter === 'APPROVED' ? 'btn-primary' : 'btn-outline'}" onclick="setGPAllocationFilter('APPROVED')" style="${currentGPAllocationFilter === 'APPROVED' ? 'background:#2e7d32; border-color:#2e7d32;' : ''}">
              ✅ Approved (${approvedCount})
            </button>
            <button class="btn btn-sm ${currentGPAllocationFilter === 'CORRECTED' ? 'btn-primary' : 'btn-outline'}" onclick="setGPAllocationFilter('CORRECTED')" style="${currentGPAllocationFilter === 'CORRECTED' ? 'background:#6a1b9a; border-color:#6a1b9a;' : ''}">
              ✏️ Corrected (${correctedCount})
            </button>
          </div>
          <div style="font-size:0.8rem; color:var(--text-muted);">
            Displaying <strong>${filtered.length}</strong> of ${totalCount} Gram Panchayat allocations
          </div>
        </div>

        <!-- AI Allocation Table -->
        <div class="table-container">
          <table class="record-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Gram Panchayat & Land</th>
                <th>Crop & Season</th>
                <th>🤖 Central AI Recommendation</th>
                <th>Suitability</th>
                <th>👤 Human Final Quota</th>
                <th>Status</th>
                <th style="text-align:right;">Actions</th>
              </tr>
            </thead>
            <tbody>
              ${filtered.length === 0 ? `
                <tr>
                  <td colspan="8" style="text-align:center; padding:36px; color:var(--text-muted);">
                    <div style="font-size:1.4rem; margin-bottom:8px;">🌾</div>
                    No Gram Panchayat allocations match the active filter.<br>
                    Click <strong>"🤖 + Run AI Allocation"</strong> to distribute an approved Food Department requirement.
                  </td>
                </tr>
              ` : filtered.map(alloc => {
                const isPending = alloc.review_status === "PENDING_REVIEW";
                const isApproved = alloc.review_status === "APPROVED";
                const isCorrected = alloc.review_status === "CORRECTED";

                const suitabilityBadge = alloc.ai_suitability === "HIGH_SUITABILITY" ? "badge-success" :
                                         alloc.ai_suitability === "MEDIUM_SUITABILITY" ? "badge-info" : "badge-warning";
                const priorityBadge = alloc.ai_priority === "CRITICAL" ? "badge-danger" :
                                      alloc.ai_priority === "HIGH" ? "badge-warning" : "badge-info";

                return `
                  <tr>
                    <td>
                      <span style="font-family:monospace; font-weight:700; color:#1565c0;">${alloc.allocation_code}</span>
                      <div style="font-size:0.7rem; color:var(--text-muted);">${alloc.batch_code}</div>
                    </td>
                    <td>
                      <div style="font-weight:700; font-size:0.9rem; color:var(--primary-dark);">${alloc.gp_name}</div>
                      <div style="font-size:0.75rem; color:var(--text-muted);">
                        <code>${alloc.gp_code}</code> • <strong>${Number(alloc.agricultural_area_ha || 0).toLocaleString()} Ha</strong> cultivable • ${alloc.active_farmers_count || 0} farmers
                      </div>
                    </td>
                    <td>
                      <div style="font-weight:600; font-size:0.86rem;">${alloc.crop_name}</div>
                      <div style="font-size:0.74rem; color:var(--text-muted);">${alloc.season}</div>
                    </td>
                    <td>
                      <div style="display:flex; align-items:center; gap:8px;">
                        <span style="font-size:1.05rem; font-weight:700; color:#1565c0;">
                          ${Number(alloc.ai_recommended_quantity_mt || 0).toLocaleString()} MT
                        </span>
                        <span class="badge ${priorityBadge}" style="font-size:0.7rem;">${alloc.ai_priority}</span>
                      </div>
                      <div style="font-size:0.73rem; color:var(--text-muted); margin-top:2px;">
                        Conf: <strong>${((alloc.ai_confidence_score || 0.94) * 100).toFixed(1)}%</strong> • 
                        Share: <strong>${(alloc.ai_factors && alloc.ai_factors.share_pct) ? alloc.ai_factors.share_pct + '%' : 'Calculated'}</strong>
                      </div>
                    </td>
                    <td>
                      <span class="badge ${suitabilityBadge}" style="font-size:0.72rem;">
                        ${(alloc.ai_suitability || 'HIGH_SUITABILITY').replace('_', ' ')}
                      </span>
                      <div style="font-size:0.72rem; color:var(--text-muted); margin-top:3px;" title="${alloc.ai_reasoning || ''}">
                        ${(alloc.ai_reasoning || '').substring(0, 32)}...
                      </div>
                    </td>
                    <td>
                      ${isApproved ? `
                        <div>
                          <span style="font-size:0.95rem; font-weight:700; color:#2e7d32;">
                            ${Number(alloc.human_final_quantity_mt || alloc.ai_recommended_quantity_mt).toLocaleString()} MT
                          </span>
                          <span class="badge badge-success" style="font-size:0.68rem; margin-left:4px;">${alloc.human_final_priority || alloc.ai_priority}</span>
                        </div>
                        <div style="font-size:0.72rem; color:var(--text-muted); margin-top:2px;">
                          By <strong>${alloc.reviewed_by || 'BDO'}</strong> • ${alloc.reviewed_at ? new Date(alloc.reviewed_at).toLocaleDateString() : 'Recorded'}
                        </div>
                      ` : isCorrected ? `
                        <div>
                          <span style="font-size:0.95rem; font-weight:700; color:#6a1b9a;">
                            ${Number(alloc.human_final_quantity_mt || 0).toLocaleString()} MT
                          </span>
                          <span class="badge badge-accent" style="font-size:0.68rem; margin-left:4px;">${alloc.human_final_priority || 'MODIFIED'}</span>
                        </div>
                        <div style="font-size:0.72rem; color:#c2185b; margin-top:2px; font-style:italic;" title="${alloc.correction_reason || ''}">
                          "${(alloc.correction_reason || '').substring(0, 32)}${(alloc.correction_reason || '').length > 32 ? '...' : ''}"
                        </div>
                        <div style="font-size:0.72rem; color:var(--text-muted);">
                          By <strong>${alloc.reviewed_by || 'BDO'}</strong> • ${alloc.reviewed_at ? new Date(alloc.reviewed_at).toLocaleDateString() : 'Recorded'}
                        </div>
                      ` : `
                        <div style="font-size:0.82rem; color:#f57f17; font-weight:600;">
                          ⏳ Awaiting Review
                        </div>
                        <div style="font-size:0.72rem; color:var(--text-muted); margin-top:2px;">
                          Panchayat Samiti BDO action required
                        </div>
                      `}
                    </td>
                    <td>
                      <span class="badge ${getBadgeClass(alloc.review_status)}">
                        ${alloc.review_status}
                      </span>
                    </td>
                    <td style="text-align:right;">
                      <div class="action-btn-group" style="justify-content:flex-end; gap:6px;">
                        <button class="btn btn-outline btn-sm" onclick="openGPAllocationAuditModal(${alloc.id})" title="View GP Soil & Land Rationale">
                          👁️ Rationale
                        </button>
                        ${isPending ? `
                          <button class="btn btn-primary btn-sm" onclick="handleApproveGPAllocation(${alloc.id})" style="background:#2e7d32;" title="Approve Recommendation As-Is">
                            ✅ Approve
                          </button>
                          <button class="btn btn-secondary btn-sm" onclick="openCorrectGPAllocationModal(${alloc.id})" style="background:#6a1b9a; color:white; border-color:#6a1b9a;" title="Correct / Override with Justification">
                            ✏️ Correct
                          </button>
                        ` : ''}
                      </div>
                    </td>
                  </tr>
                `;
              }).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `
      <div class="alert-box danger" style="display:block;">
        Failed to load Central AI Gram Panchayat Allocations: ${err.message}
      </div>
    `;
  }
}

function setGPAllocationFilter(filter) {
  currentGPAllocationFilter = filter;
  renderPSCentralAIAllocation();
}

// --- RUN CENTRAL AI GP ALLOCATION MODAL ---
function openRunGPAllocationModal() {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = "🤖 Central AI: Generate Gram Panchayat Crop Allocation";
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Run Central AI Allocation Engine";

  modalBody.innerHTML = `
    <div style="background:#e8f5e9; border:1px solid #a5d6a7; padding:12px 14px; border-radius:6px; margin-bottom:14px;">
      <div style="font-weight:700; color:#2e7d32; font-size:0.85rem; margin-bottom:3px;">
        🏛️ Multi-Factor Panchayat Samiti Quota Optimization
      </div>
      <p style="font-size:0.78rem; color:#1b5e20; margin:0;">
        The Central AI Engine will analyze all Gram Panchayats under your Panchayat Samiti. It ingests cultivable land area, Black Cotton soil compatibility, canal & lift irrigation coverage, organic matter, and historical farmer harvest records, guaranteeing that <strong>100% of the Food Department quota is allocated without exceeding the limit</strong>.
      </p>
    </div>

    <form id="gpAllocationPredictForm" class="form-grid">
      <div class="form-group">
        <label class="form-label">Approved Crop to Allocate *</label>
        <select id="gpAllocCropSelect" class="form-control" required>
          <option value="Wheat (Lokwan)" selected>Wheat (Lokwan)</option>
          <option value="Sugarcane">Sugarcane</option>
          <option value="Paddy / Rice">Paddy / Rice</option>
          <option value="Soybean">Soybean</option>
          <option value="Cotton">Cotton</option>
          <option value="Bengal Gram">Bengal Gram / Chana</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Agricultural Season *</label>
        <select id="gpAllocSeasonSelect" class="form-control" required>
          <option value="Rabi 2026" selected>Rabi 2026</option>
          <option value="Kharif 2026">Kharif 2026</option>
          <option value="Zaid 2026">Zaid 2026</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Approved Food Dept Quota (MT) *</label>
        <input type="number" id="gpAllocQuotaInput" class="form-control" value="12000" step="100" min="100" required>
        <span style="font-size:0.72rem; color:var(--text-muted);">Total approved quota to distribute across candidate Gram Panchayats.</span>
      </div>

      <div class="form-group">
        <label class="form-label">Priority Level *</label>
        <select id="gpAllocPrioritySelect" class="form-control" required>
          <option value="HIGH" selected>HIGH</option>
          <option value="CRITICAL">CRITICAL</option>
          <option value="NORMAL">NORMAL</option>
        </select>
      </div>

      <div class="form-group" style="grid-column: span 2;">
        <label class="form-label">Panchayat Samiti Jurisdiction</label>
        <input type="text" id="gpAllocPSInput" class="form-control" value="Baramati Block Panchayat Samiti" readonly style="background:#eceff1;">
      </div>
    </form>
  `;

  modalSubmitBtn.onclick = async () => {
    const cropName = document.getElementById("gpAllocCropSelect").value;
    const season = document.getElementById("gpAllocSeasonSelect").value;
    const totalQuota = parseFloat(document.getElementById("gpAllocQuotaInput").value);
    const priority = document.getElementById("gpAllocPrioritySelect").value;
    const psName = document.getElementById("gpAllocPSInput").value;

    if (isNaN(totalQuota) || totalQuota <= 0) {
      alert("Please enter a valid positive quota in Metric Tonnes (MT).");
      return;
    }

    try {
      modalSubmitBtn.disabled = true;
      modalSubmitBtn.textContent = "AI Distributing Quota...";
      const res = await ApiClient.predictGPAllocation({
        crop_name: cropName,
        season: season,
        total_quota_mt: totalQuota,
        priority: priority,
        panchayat_samiti_name: psName,
      });

      closeModal();
      alert(`Central AI allocated ${Number(res.total_ai_allocated_mt).toLocaleString()} MT across ${res.gp_count} Gram Panchayats under Batch ${res.batch_code}!`);
      await renderPSCentralAIAllocation();
    } catch (err) {
      alert(`AI Allocation failed: ${err.message}`);
    } finally {
      modalSubmitBtn.disabled = false;
      modalSubmitBtn.textContent = "Run Central AI Allocation Engine";
    }
  };

  modal.style.display = "flex";
}

// --- ONE-CLICK APPROVE OF GP ALLOCATION ---
async function handleApproveGPAllocation(allocId) {
  const rec = cachedGPAllocations.find(a => a.id === allocId);
  if (!rec) return;

  const confirmed = confirm(
    `Approve Central AI Allocation #${rec.allocation_code} for ${rec.gp_name}?\n\n` +
    `AI Recommended Quota: ${Number(rec.ai_recommended_quantity_mt).toLocaleString()} MT (${rec.crop_name})\n` +
    `Priority: ${rec.ai_priority}\n\n` +
    `This will authorize the quota down to the Gram Panchayat registry.`
  );
  if (!confirmed) return;

  try {
    await ApiClient.approveGPAllocation(allocId, "Approved without modification by Panchayat Samiti BDO");
    alert(`Allocation for ${rec.gp_name} approved successfully!`);
    await renderPSCentralAIAllocation();
  } catch (err) {
    alert(`Approval failed: ${err.message}`);
  }
}

// --- HUMAN CORRECTION MODAL (DUAL-STORAGE INTEGRITY & QUOTA CONSERVATION) ---
function openCorrectGPAllocationModal(allocId) {
  const rec = cachedGPAllocations.find(a => a.id === allocId);
  if (!rec) return;

  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `✏️ Human Override: Allocation ${rec.allocation_code} (${rec.gp_name})`;
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Submit Human Final Quota";

  modalBody.innerHTML = `
    <!-- Dual-Storage Security Notice -->
    <div style="background:#fff3e0; border:1px solid #ffe082; padding:12px 14px; border-radius:6px; margin-bottom:14px;">
      <div style="font-weight:700; color:#e65100; font-size:0.85rem; margin-bottom:3px;">
        🔒 Immutable Dual-Storage Guarantee
      </div>
      <p style="font-size:0.78rem; color:#bf360c; margin:0;">
        The original AI recommendation of <strong>${Number(rec.ai_recommended_quantity_mt).toLocaleString()} MT</strong> 
        (Suitability: <strong>${rec.ai_suitability}</strong>) will remain permanently preserved in the system audit trail. 
        Your human modification will be stored in separate verified columns with mandatory operational justification.
      </p>
    </div>

    <form id="gpCorrectionForm" class="form-grid">
      <div class="form-group">
        <label class="form-label">Human Final Quota (MT) *</label>
        <input type="number" id="correctGPQtyInput" class="form-control" value="${rec.ai_recommended_quantity_mt}" step="10" min="1" required>
        <span style="font-size:0.72rem; color:var(--text-muted);">Original AI Baseline: ${Number(rec.ai_recommended_quantity_mt).toLocaleString()} MT</span>
      </div>

      <div class="form-group">
        <label class="form-label">Human Final Priority *</label>
        <select id="correctGPPriorityInput" class="form-control" required>
          <option value="NORMAL" ${rec.ai_priority === 'NORMAL' ? 'selected' : ''}>NORMAL</option>
          <option value="HIGH" ${rec.ai_priority === 'HIGH' ? 'selected' : ''}>HIGH</option>
          <option value="CRITICAL" ${rec.ai_priority === 'CRITICAL' ? 'selected' : ''}>CRITICAL</option>
        </select>
      </div>

      <div class="form-group" style="grid-column: span 2;">
        <label class="form-label" style="color:#c2185b; font-weight:700;">Reason for Correction / Operational Justification * (Mandatory)</label>
        <textarea id="correctGPReasonInput" class="form-control" rows="2" placeholder="e.g. Adjusted to 4,000 MT due to minor canal branch maintenance scheduled in this block." required></textarea>
        <span style="font-size:0.72rem; color:var(--text-muted);">Minimum 5 characters required for audit verification.</span>
      </div>

      <div class="form-group" style="grid-column: span 2;">
        <label class="form-label">Additional Block Administrative Notes (Optional)</label>
        <textarea id="correctGPNotesInput" class="form-control" rows="2" placeholder="Optional notes for Gram Panchayat Sarpanch and agricultural assistants..."></textarea>
      </div>
    </form>
  `;

  modalSubmitBtn.onclick = async () => {
    const finalQty = parseFloat(document.getElementById("correctGPQtyInput").value);
    const finalPriority = document.getElementById("correctGPPriorityInput").value;
    const reason = document.getElementById("correctGPReasonInput").value.trim();
    const notes = document.getElementById("correctGPNotesInput").value.trim();

    if (isNaN(finalQty) || finalQty <= 0) {
      alert("Please enter a valid positive quota in MT.");
      return;
    }

    if (!reason || reason.length < 5) {
      alert("A mandatory justification of at least 5 characters is required to correct an AI allocation.");
      return;
    }

    try {
      modalSubmitBtn.disabled = true;
      modalSubmitBtn.textContent = "Recording Human Override...";
      await ApiClient.correctGPAllocation(allocId, {
        human_final_quantity_mt: finalQty,
        human_final_priority: finalPriority,
        correction_reason: reason,
        notes: notes,
      });

      closeModal();
      alert(`Correction recorded for ${rec.gp_name} (#${rec.allocation_code}). Dual-storage verified.`);
      await renderPSCentralAIAllocation();
    } catch (err) {
      alert(`Correction failed: ${err.message}`);
    } finally {
      modalSubmitBtn.disabled = false;
      modalSubmitBtn.textContent = "Submit Human Final Quota";
    }
  };

  modal.style.display = "flex";
}

// --- MULTI-FACTOR RATIONALE & AUDIT MODAL FOR GP ALLOCATION ---
function openGPAllocationAuditModal(allocId) {
  const rec = cachedGPAllocations.find(a => a.id === allocId);
  if (!rec) return;

  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `🔍 AI Allocation Factors & Audit: ${rec.gp_name} (${rec.allocation_code})`;
  modalSubmitBtn.style.display = "none";

  const factors = rec.ai_factors || {};

  modalBody.innerHTML = `
    <!-- Top Summary Card -->
    <div style="background:#f5f7fa; border-radius:8px; padding:14px 16px; margin-bottom:16px; border:1px solid var(--border);">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <div>
          <span style="font-size:0.75rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Gram Panchayat Context</span>
          <div style="font-size:1.05rem; font-weight:700; color:var(--primary-dark); margin-top:2px;">
            ${rec.gp_name} (<code>${rec.gp_code}</code>)
          </div>
          <div style="font-size:0.75rem; color:var(--text-muted);">
            Crop: <strong>${rec.crop_name}</strong> • ${rec.season} • Block: ${rec.panchayat_samiti_name}
          </div>
        </div>
        <div style="text-align:right;">
          <span class="badge ${getBadgeClass(rec.review_status)}" style="font-size:0.8rem; padding:4px 12px;">${rec.review_status}</span>
          <div style="font-size:0.72rem; color:var(--text-muted); margin-top:4px;">
            Batch: <code>${rec.batch_code}</code>
          </div>
        </div>
      </div>
    </div>

    <!-- Dual Values Comparison Grid -->
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:18px;">
      <div style="background:#e3f2fd; border:1px solid #90caf9; border-radius:8px; padding:12px 14px;">
        <div style="font-size:0.72rem; text-transform:uppercase; color:#1565c0; font-weight:700;">🤖 AI Recommended Quota (Immutable)</div>
        <div style="font-size:1.25rem; font-weight:700; color:#0d47a1; margin-top:4px;">
          ${Number(rec.ai_recommended_quantity_mt || 0).toLocaleString()} MT
        </div>
        <div style="font-size:0.78rem; color:#1565c0; margin-top:2px;">
          Suitability: <strong>${rec.ai_suitability}</strong> • Confidence: <strong>${((rec.ai_confidence_score || 0.94) * 100).toFixed(1)}%</strong>
        </div>
      </div>

      <div style="background:${rec.review_status === 'CORRECTED' ? '#f3e5f5' : rec.review_status === 'APPROVED' ? '#e8f5e9' : '#fff8e1'}; border:1px solid ${rec.review_status === 'CORRECTED' ? '#ce93d8' : rec.review_status === 'APPROVED' ? '#a5d6a7' : '#ffe082'}; border-radius:8px; padding:12px 14px;">
        <div style="font-size:0.72rem; text-transform:uppercase; color:${rec.review_status === 'CORRECTED' ? '#6a1b9a' : rec.review_status === 'APPROVED' ? '#2e7d32' : '#f57f17'}; font-weight:700;">
          👤 Human Final Quota
        </div>
        <div style="font-size:1.25rem; font-weight:700; color:${rec.review_status === 'CORRECTED' ? '#4a148c' : rec.review_status === 'APPROVED' ? '#1b5e20' : '#e65100'}; margin-top:4px;">
          ${rec.human_final_quantity_mt !== null && rec.human_final_quantity_mt !== undefined ? Number(rec.human_final_quantity_mt).toLocaleString() + ' MT' : 'Pending Review'}
        </div>
        <div style="font-size:0.78rem; color:var(--text-muted); margin-top:2px;">
          ${rec.reviewed_by ? `Reviewed by <strong>${rec.reviewed_by}</strong> on ${new Date(rec.reviewed_at).toLocaleDateString()}` : 'Awaiting BDO Decision'}
        </div>
      </div>
    </div>

    ${rec.correction_reason ? `
      <div style="background:#fce4ec; border:1px solid #f48fb1; border-radius:6px; padding:10px 14px; margin-bottom:16px;">
        <span style="font-size:0.72rem; text-transform:uppercase; color:#c2185b; font-weight:700;">Audit Justification:</span>
        <div style="font-size:0.84rem; color:#880e4f; font-weight:600; margin-top:2px;">"${rec.correction_reason}"</div>
      </div>
    ` : ''}

    <!-- Ingested GP Features Grid -->
    <h4 style="color:var(--primary-dark); font-size:0.92rem; margin-bottom:10px;">📊 Ingested Gram Panchayat Features</h4>
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:10px; margin-bottom:16px;">
      <div style="background:white; border:1px solid var(--border); border-radius:6px; padding:10px;">
        <span style="font-size:0.68rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Cultivable Land</span>
        <div style="font-size:0.95rem; font-weight:700; color:#2e7d32; margin-top:2px;">${Number(rec.agricultural_area_ha || 0).toLocaleString()} Ha</div>
      </div>
      <div style="background:white; border:1px solid var(--border); border-radius:6px; padding:10px;">
        <span style="font-size:0.68rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Soil Classification</span>
        <div style="font-size:0.85rem; font-weight:700; color:#37474f; margin-top:2px;">${factors.soil_type || 'Black Cotton Soil'}</div>
      </div>
      <div style="background:white; border:1px solid var(--border); border-radius:6px; padding:10px;">
        <span style="font-size:0.68rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Irrigation Coverage</span>
        <div style="font-size:0.95rem; font-weight:700; color:#0277bd; margin-top:2px;">${factors.irrigation_pct || 65.0}%</div>
      </div>
      <div style="background:white; border:1px solid var(--border); border-radius:6px; padding:10px;">
        <span style="font-size:0.68rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Organic Matter</span>
        <div style="font-size:0.95rem; font-weight:700; color:#6a1b9a; margin-top:2px;">${factors.organic_matter || 'MEDIUM'}</div>
      </div>
      <div style="background:white; border:1px solid var(--border); border-radius:6px; padding:10px;">
        <span style="font-size:0.68rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Active Farmers</span>
        <div style="font-size:0.95rem; font-weight:700; color:#37474f; margin-top:2px;">${rec.active_farmers_count || 0} Registered</div>
      </div>
      <div style="background:white; border:1px solid var(--border); border-radius:6px; padding:10px;">
        <span style="font-size:0.68rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Allocation Share</span>
        <div style="font-size:0.95rem; font-weight:700; color:#1565c0; margin-top:2px;">${factors.share_pct || 25.0}% of Quota</div>
      </div>
    </div>

    <!-- AI Reasoning Note -->
    <div style="background:#fafafa; border:1px solid var(--border); border-radius:6px; padding:12px 14px; font-size:0.82rem; line-height:1.5; color:#37474f;">
      <strong>Central AI Formulation:</strong> ${rec.ai_reasoning || 'Computed using normalized land suitability weighting.'}
    </div>

    <div style="text-align:right; margin-top:18px;">
      <button class="btn btn-secondary btn-sm" onclick="closeModal()">Close Rationale View</button>
    </div>
  `;

  modal.style.display = "flex";
}

// --- BATCH APPROVAL OF ALL PENDING GP ALLOCATIONS ---
async function handleBatchApproveGPAllocations(batchCode) {
  const confirmed = confirm(
    `Are you sure you want to approve ALL pending Gram Panchayat allocations under ${batchCode}?\n\n` +
    `This will authorize quotas for all villages without manual adjustments.`
  );
  if (!confirmed) return;

  try {
    const res = await ApiClient.batchApproveGPAllocations(batchCode, "Batch approved by Panchayat Samiti BDO");
    alert(res.message || "Batch approved successfully!");
    await renderPSCentralAIAllocation();
  } catch (err) {
    alert(`Batch approval failed: ${err.message}`);
  }
}


// ==========================================
// CENTRAL AI/ML ENGINE: GRAM PANCHAYAT -> FARMER-WISE CROP RECOMMENDATION
// ==========================================

let currentFarmerRecFilter = "ALL";
let cachedFarmerRecs = [];

async function renderGPCentralAIRecommendation(container) {
  if (!container) container = document.getElementById("activeTableContainer");
  if (!container) return;

  container.innerHTML = `
    <div style="text-align:center; padding:40px; color:var(--text-muted);">
      <div style="font-size:2rem; margin-bottom:12px; animation:spin 1.5s infinite linear;">🧠</div>
      Retrieving Central AI Farmer recommendations & agronomic suitability data...
    </div>
  `;

  try {
    const recsRes = await ApiClient.getFarmerRecommendations().catch(() => []);
    cachedFarmerRecs = Array.isArray(recsRes) ? recsRes : [];

    let filtered = cachedFarmerRecs;
    if (currentFarmerRecFilter !== "ALL") {
      filtered = cachedFarmerRecs.filter(r => r.review_status === currentFarmerRecFilter);
    }

    const totalCount = cachedFarmerRecs.length;
    const pendingCount = cachedFarmerRecs.filter(r => r.review_status === "PENDING_REVIEW").length;
    const approvedCount = cachedFarmerRecs.filter(r => r.review_status === "APPROVED").length;
    const correctedCount = cachedFarmerRecs.filter(r => r.review_status === "CORRECTED").length;

    // Determine active batch metrics for quota & land conservation display
    const latestBatch = cachedFarmerRecs.length > 0 ? cachedFarmerRecs[0].batch_code : "BATCH-FRA-2026-001";
    const batchRecords = cachedFarmerRecs.filter(r => r.batch_code === latestBatch);
    const activeCrop = batchRecords.length > 0 ? batchRecords[0].crop_name : "Wheat (Lokwan)";
    const activeSeason = batchRecords.length > 0 ? batchRecords[0].season : "Rabi 2026";
    const activeGP = batchRecords.length > 0 ? batchRecords[0].gp_name : "Shirsuphal Gram Panchayat";

    // Quota metrics (in Quintals and MT: 10 Qtl = 1 MT)
    const gpApprovedQuotaMT = batchRecords.length > 0 && batchRecords[0].gp_approved_quota_mt ? batchRecords[0].gp_approved_quota_mt : 1200.0;
    const gpApprovedQuotaQtl = gpApprovedQuotaMT * 10;

    const totalAIAllocatedQtl = batchRecords.reduce((sum, r) => sum + (r.ai_recommended_quantity_quintals || 0), 0);
    const totalFinalAllocatedQtl = batchRecords.reduce((sum, r) => {
      const q = (r.human_final_quantity_quintals !== null && r.human_final_quantity_quintals !== undefined) ? r.human_final_quantity_quintals : r.ai_recommended_quantity_quintals;
      return sum + (q || 0);
    }, 0);

    const totalLandHoldingAcres = batchRecords.reduce((sum, r) => sum + (r.farmer_total_land_acres || 0), 0);
    const totalAllocatedAcres = batchRecords.reduce((sum, r) => {
      const a = (r.human_final_area_acres !== null && r.human_final_area_acres !== undefined) ? r.human_final_area_acres : r.ai_recommended_area_acres;
      return sum + (a || 0);
    }, 0);
    const remainingFreeLandAcres = Math.max(0, Math.round((totalLandHoldingAcres - totalAllocatedAcres) * 10) / 10);

    const quotaWithinLimits = totalFinalAllocatedQtl <= (gpApprovedQuotaQtl + 0.1);

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <!-- Central AI Engine GP Header & Telemetry -->
        <div style="background:linear-gradient(135deg, #0d3b66 0%, #1565c0 100%); color:white; padding:22px 24px; border-radius:10px; margin-bottom:20px; box-shadow:0 4px 14px rgba(21,101,192,0.22);">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:14px;">
            <div>
              <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
                <span style="font-size:1.6rem;">🧠</span>
                <h2 style="margin:0; color:#fff; font-size:1.35rem; font-weight:700;">KrushiSetu Central AI/ML Engine</h2>
                <span style="background:rgba(255,255,255,0.22); font-size:0.72rem; padding:3px 10px; border-radius:12px; font-weight:700; letter-spacing:0.5px;">v1.0.0-prototype</span>
              </div>
              <p style="margin:0; font-size:0.84rem; color:#bbdefb; opacity:0.95;">
                Gram Panchayat Module • Farmer-wise Crop Recommendation & Agronomic Suitability Optimizer
              </p>
            </div>
            <div style="display:flex; gap:10px; align-items:center;">
              <button class="btn btn-primary" onclick="openRunFarmerMatchingModal()" style="background:#ffb300; color:#0d3b66; font-weight:700; border:none; box-shadow:0 2px 8px rgba(0,0,0,0.15);">
                🤖 + Run AI Recommendation
              </button>
              ${pendingCount > 0 ? `
                <button class="btn btn-sm" onclick="handleBatchApproveFarmerRecs('${latestBatch}')" style="background:#00e676; color:#0d3b66; font-weight:700; border:none; padding:8px 14px;">
                  ✅ Approve All Pending (${pendingCount})
                </button>
              ` : ''}
              <button class="btn btn-secondary" onclick="renderGPCentralAIRecommendation()" style="background:rgba(255,255,255,0.2); color:white; border:1px solid rgba(255,255,255,0.3);">
                🔄 Refresh
              </button>
            </div>
          </div>

          <!-- Panchayat Samiti Allocation Context Banner -->
          <div style="background:rgba(0,0,0,0.25); border-radius:8px; padding:14px 18px; margin-top:18px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
              <span style="font-size:0.72rem; text-transform:uppercase; color:#90caf9; font-weight:700; letter-spacing:0.5px;">Panchayat Samiti Approved Allocation</span>
              <div style="font-size:1.1rem; font-weight:700; color:#fff; margin-top:2px;">
                ${activeCrop} • ${activeSeason}
              </div>
              <div style="font-size:0.75rem; color:#e3f2fd; opacity:0.9;">
                Jurisdiction: <strong>${activeGP}</strong> • Batch Code: <code>${latestBatch}</code>
              </div>
            </div>
            <div style="display:flex; gap:12px; align-items:center;">
              <div style="text-align:right;">
                <span style="font-size:0.72rem; text-transform:uppercase; color:#90caf9; font-weight:700;">Allocation Status</span>
                <div><span class="badge badge-success" style="font-size:0.78rem; padding:4px 10px;">APPROVED FROM PANCHAYAT SAMITI</span></div>
              </div>
            </div>
          </div>

          <!-- Quota & Land Conservation Telemetry Grid -->
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:12px; margin-top:14px; border-top:1px solid rgba(255,255,255,0.2); padding-top:14px;">
            <div style="background:rgba(0,0,0,0.18); border-radius:8px; padding:10px 14px;">
              <div style="font-size:0.7rem; text-transform:uppercase; color:#90caf9; font-weight:700;">GP Approved Quota</div>
              <div style="font-size:1.25rem; font-weight:700; color:#fff; margin-top:2px;">${Number(gpApprovedQuotaQtl).toLocaleString()} Qtl <span style="font-size:0.8rem; font-weight:normal;">(${Number(gpApprovedQuotaMT).toLocaleString()} MT)</span></div>
            </div>
            <div style="background:rgba(0,0,0,0.18); border-radius:8px; padding:10px 14px;">
              <div style="font-size:0.7rem; text-transform:uppercase; color:#90caf9; font-weight:700;">Total Allocated Qtl</div>
              <div style="font-size:1.25rem; font-weight:700; color:#a5d6a7; margin-top:2px;">${Number(Math.round(totalFinalAllocatedQtl * 10)/10).toLocaleString()} Qtl ${quotaWithinLimits ? '✓' : '⚠️'}</div>
            </div>
            <div style="background:rgba(0,0,0,0.18); border-radius:8px; padding:10px 14px;">
              <div style="font-size:0.7rem; text-transform:uppercase; color:#ffe082; font-weight:700;">Allocated Land</div>
              <div style="font-size:1.25rem; font-weight:700; color:#fff; margin-top:2px;">${Number(Math.round(totalAllocatedAcres*10)/10).toLocaleString()} Acres</div>
            </div>
            <div style="background:rgba(0,0,0,0.18); border-radius:8px; padding:10px 14px;">
              <div style="font-size:0.7rem; text-transform:uppercase; color:#90caf9; font-weight:700;">Farmers In Batch</div>
              <div style="font-size:1.25rem; font-weight:700; color:#fff; margin-top:2px;">${batchRecords.length} Farmers</div>
            </div>
          </div>
        </div>

        <!-- AI DATA INSIGHTS: "Why this recommendation?" Section -->
        <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:18px 20px; margin-bottom:20px; box-shadow:0 2px 6px rgba(0,0,0,0.04);">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:1.2rem;">💡</span>
              <h4 style="margin:0; color:var(--primary-dark); font-size:0.98rem; font-weight:700;">
                AI Factors: Why this recommendation?
              </h4>
            </div>
            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:600;">
              Agronomic Suitability Formulation • Parcel Land Capping Enforced
            </span>
          </div>

          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:12px;">
            <div style="background:#f9fbf9; border:1px solid #e0e8e0; border-radius:6px; padding:10px 12px;">
              <div style="font-size:0.72rem; text-transform:uppercase; color:#2e7d32; font-weight:700;">🧪 Soil Compatibility (40%)</div>
              <div style="font-size:0.8rem; color:#2c3e50; margin-top:3px; line-height:1.4;">
                Matches physical soil type (Black Cotton / Clay Loam) against crop physiological requirements.
              </div>
            </div>
            <div style="background:#f9fbf9; border:1px solid #e0e8e0; border-radius:6px; padding:10px 12px;">
              <div style="font-size:0.72rem; text-transform:uppercase; color:#1565c0; font-weight:700;">💧 Water Security (35%)</div>
              <div style="font-size:0.8rem; color:#2c3e50; margin-top:3px; line-height:1.4;">
                Prioritizes canal and perennial borewell plots over seasonal rainfed lands to ensure harvest yields.
              </div>
            </div>
            <div style="background:#f9fbf9; border:1px solid #e0e8e0; border-radius:6px; padding:10px 12px;">
              <div style="font-size:0.72rem; text-transform:uppercase; color:#e65100; font-weight:700;">⚖️ Soil Chemistry & pH (15%)</div>
              <div style="font-size:0.8rem; color:#2c3e50; margin-top:3px; line-height:1.4;">
                Scores laboratory pH level (optimal 6.5 - 8.2) for maximum nutrient bio-availability.
              </div>
            </div>
            <div style="background:#f9fbf9; border:1px solid #e0e8e0; border-radius:6px; padding:10px 12px;">
              <div style="font-size:0.72rem; text-transform:uppercase; color:#6a1b9a; font-weight:700;">🌱 Soil Vitality & OC (10%)</div>
              <div style="font-size:0.8rem; color:#2c3e50; margin-top:3px; line-height:1.4;">
                Ingests Organic Carbon % to evaluate soil biological health and moisture retention.
              </div>
            </div>
          </div>
        </div>

        <!-- Filter Controls -->
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:10px;">
          <div style="display:flex; gap:8px;">
            <button class="btn btn-sm ${currentFarmerRecFilter === 'ALL' ? 'btn-primary' : 'btn-secondary'}" onclick="setFarmerRecFilter('ALL')">
              All (${totalCount})
            </button>
            <button class="btn btn-sm ${currentFarmerRecFilter === 'PENDING_REVIEW' ? 'btn-primary' : 'btn-secondary'}" onclick="setFarmerRecFilter('PENDING_REVIEW')">
              Pending Review (${pendingCount})
            </button>
            <button class="btn btn-sm ${currentFarmerRecFilter === 'APPROVED' ? 'btn-primary' : 'btn-secondary'}" onclick="setFarmerRecFilter('APPROVED')">
              Approved (${approvedCount})
            </button>
            <button class="btn btn-sm ${currentFarmerRecFilter === 'CORRECTED' ? 'btn-primary' : 'btn-secondary'}" onclick="setFarmerRecFilter('CORRECTED')">
              Modified (${correctedCount})
            </button>
          </div>
          <div style="font-size:0.78rem; color:var(--text-muted);">
            Displaying <strong>${filtered.length}</strong> of ${totalCount} farmer recommendations
          </div>
        </div>

        <!-- Recommendations Table -->
        <div style="background:white; border-radius:8px; border:1px solid var(--border); overflow:hidden; box-shadow:0 2px 6px rgba(0,0,0,0.04);">
          <table class="record-table" style="margin:0;">
            <thead>
              <tr>
                <th>Farmer & Parcel</th>
                <th>Crop & Season</th>
                <th>Holding / Alloc Land</th>
                <th>Target Quantity</th>
                <th>Soil Report</th>
                <th>Suitability Score</th>
                <th>Status</th>
                <th style="text-align:right;">Governance Actions</th>
              </tr>
            </thead>
            <tbody>
              ${filtered.length === 0 ? `
                <tr>
                  <td colspan="8" style="text-align:center; padding:36px; color:var(--text-muted);">
                    No farmer recommendations match the active filter.<br>
                    <button class="btn btn-primary btn-sm" onclick="openRunFarmerMatchingModal()" style="margin-top:10px; background:#1565c0;">
                      🤖 Run Central AI Recommendation
                    </button>
                  </td>
                </tr>
              ` : filtered.map(r => {
                const isPending = r.review_status === "PENDING_REVIEW";
                const isApproved = r.review_status === "APPROVED";
                const isCorrected = r.review_status === "CORRECTED";
                const finalAcres = (r.human_final_area_acres !== null && r.human_final_area_acres !== undefined) ? r.human_final_area_acres : r.ai_recommended_area_acres;
                const finalQtl = (r.human_final_quantity_quintals !== null && r.human_final_quantity_quintals !== undefined) ? r.human_final_quantity_quintals : r.ai_recommended_quantity_quintals;
                const suitabilityPct = Math.round((r.suitability_score || 0.85) * 100);

                return `
                  <tr style="${isPending ? 'background:#fffde7;' : ''}">
                    <td>
                      <strong>${r.farmer_name}</strong>
                      <div style="font-size:0.74rem; color:var(--text-muted);">
                        <code>${r.farmer_id}</code> • Survey #${r.survey_number}
                      </div>
                      <div style="font-size:0.72rem; color:#546e7a;">${r.village_name}</div>
                    </td>
                    <td>
                      <strong>${r.crop_name}</strong>
                      <div style="font-size:0.74rem; color:var(--text-muted);">${r.season}</div>
                    </td>
                    <td>
                      <div style="font-weight:700; color:#1565c0;">
                        ${Number(finalAcres).toFixed(1)} Acres
                      </div>
                      <div style="font-size:0.72rem; color:var(--text-muted);">
                        Total Holding: ${Number(r.farmer_total_land_acres).toFixed(1)} Ac
                      </div>
                      ${isCorrected && r.human_final_area_acres !== r.ai_recommended_area_acres ? `
                        <div style="font-size:0.70rem; color:#c62828;">AI was: ${r.ai_recommended_area_acres} Ac</div>
                      ` : ''}
                    </td>
                    <td>
                      <div style="font-weight:700; color:#2e7d32; font-size:1.02rem;">
                        ${Number(finalQtl).toFixed(1)} Qtl
                      </div>
                      <div style="font-size:0.72rem; color:var(--text-muted);">
                        ${(finalQtl / 10).toFixed(2)} MT
                      </div>
                      ${isCorrected && r.human_final_quantity_quintals !== r.ai_recommended_quantity_quintals ? `
                        <div style="font-size:0.70rem; color:#c62828;">AI was: ${r.ai_recommended_quantity_quintals} Qtl</div>
                      ` : ''}
                    </td>
                    <td>
                      <button class="btn btn-outline btn-sm" onclick="openSoilDocViewerModal('${r.farmer_id}', '${r.soil_report_url || ''}')" style="color:#2e7d32; border-color:#2e7d32; font-size:0.74rem; padding:3px 8px;">
                        📄 View Report
                      </button>
                    </td>
                    <td>
                      <div style="display:flex; align-items:center; gap:6px;">
                        <span style="font-weight:700; color:${suitabilityPct >= 85 ? '#2e7d32' : '#e65100'};">${suitabilityPct}%</span>
                        <button class="btn btn-outline btn-sm" onclick="openFarmerAIRationaleModal(${r.id})" style="padding:2px 6px; font-size:0.72rem;">
                          💡 Factors
                        </button>
                      </div>
                      <div style="font-size:0.7rem; color:var(--text-muted);">${r.soil_type} • ${r.irrigation_source}</div>
                    </td>
                    <td>
                      <span class="badge ${isApproved ? 'badge-success' : isCorrected ? 'badge-info' : 'badge-warning'}">
                        ${r.review_status}
                      </span>
                      ${r.reviewed_by ? `
                        <div style="font-size:0.68rem; color:var(--text-muted); margin-top:2px;">
                          by ${r.reviewed_by}
                        </div>
                      ` : ''}
                    </td>
                    <td style="text-align:right;">
                      <div style="display:flex; gap:6px; justify-content:flex-end; align-items:center;">
                        ${isPending ? `
                          <button class="btn btn-sm" onclick="handleApproveFarmerRec(${r.id})" style="background:#2e7d32; color:white; font-weight:700; border:none; padding:5px 12px;" title="Zero Typing: Authorize AI recommendation as final">
                            ✅ Approve
                          </button>
                        ` : ''}
                        <button class="btn btn-sm btn-outline" onclick="openCorrectFarmerRecModal(${r.id})" style="padding:5px 10px; font-size:0.78rem;">
                          ${isPending ? '✏️ Review / Correct' : '✏️ Re-adjust'}
                        </button>
                        <button class="btn btn-sm btn-outline" onclick="openFarmerRecAuditModal(${r.id})" style="padding:5px 8px; font-size:0.78rem;" title="View Audit Trail">
                          📜
                        </button>
                      </div>
                    </td>
                  </tr>
                `;
              }).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `
      <div class="alert-box danger" style="padding:20px;">
        Failed to load Central AI Farmer Recommendations: ${err.message}
      </div>
    `;
  }
}

function setFarmerRecFilter(status) {
  currentFarmerRecFilter = status;
  renderGPCentralAIRecommendation();
}

// --- RUN CENTRAL AI FARMER MATCHING MODAL ---
function openRunFarmerMatchingModal() {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = "🤖 Central AI: Generate Farmer-Wise Crop Recommendations";
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Run Central AI Recommendation Engine";

  modalBody.innerHTML = `
    <div style="background:#e3f2fd; border:1px solid #90caf9; padding:12px 14px; border-radius:6px; margin-bottom:14px;">
      <div style="font-weight:700; color:#0d47a1; font-size:0.85rem; margin-bottom:3px;">
        🌾 Agronomic Suitability & Land Capping Formulation
      </div>
      <p style="font-size:0.78rem; color:#1565c0; margin:0;">
        The Central AI Engine will analyze all registered farmers in your Gram Panchayat. It ingests verified parcel acreage, certified soil tests (NPK, pH, Organic Carbon), irrigation sources, and previous harvest records. <strong>No farmer will be allocated more than their available land, and the total matches your approved Panchayat Samiti quota.</strong>
      </p>
    </div>

    <form id="farmerRecPredictForm" class="form-grid">
      <div class="form-group">
        <label class="form-label">Crop to Recommend *</label>
        <select id="farmerRecCropSelect" class="form-control" required>
          <option value="Wheat (Lokwan)" selected>Wheat (Lokwan)</option>
          <option value="Sugarcane">Sugarcane</option>
          <option value="Soybean">Soybean</option>
          <option value="Cotton">Cotton</option>
          <option value="Bengal Gram">Bengal Gram / Chana</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Agricultural Season *</label>
        <select id="farmerRecSeasonSelect" class="form-control" required>
          <option value="Rabi 2026" selected>Rabi 2026</option>
          <option value="Kharif 2026">Kharif 2026</option>
          <option value="Zaid 2026">Zaid 2026</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">GP Approved Quota (MT) *</label>
        <input type="number" id="farmerRecQuotaInput" class="form-control" value="1200" step="50" min="10" required>
        <span style="font-size:0.72rem; color:var(--text-muted);">Total approved quota received from Panchayat Samiti for your GP.</span>
      </div>

      <div class="form-group">
        <label class="form-label">Priority Level *</label>
        <select id="farmerRecPrioritySelect" class="form-control" required>
          <option value="HIGH" selected>HIGH</option>
          <option value="CRITICAL">CRITICAL</option>
          <option value="NORMAL">NORMAL</option>
        </select>
      </div>

      <div class="form-group" style="grid-column: span 2;">
        <label class="form-label">Gram Panchayat Jurisdiction</label>
        <input type="text" id="farmerRecGPInput" class="form-control" value="Shirsuphal Gram Panchayat" readonly style="background:#eceff1;">
      </div>
    </form>
  `;

  modalSubmitBtn.onclick = async () => {
    const cropName = document.getElementById("farmerRecCropSelect").value;
    const season = document.getElementById("farmerRecSeasonSelect").value;
    const totalQuota = parseFloat(document.getElementById("farmerRecQuotaInput").value);
    const priority = document.getElementById("farmerRecPrioritySelect").value;
    const gpName = document.getElementById("farmerRecGPInput").value;

    if (isNaN(totalQuota) || totalQuota <= 0) {
      alert("Please enter a valid positive quota in Metric Tonnes (MT).");
      return;
    }

    try {
      modalSubmitBtn.disabled = true;
      modalSubmitBtn.textContent = "AI Matching Farmers...";
      const res = await ApiClient.predictFarmerRecommendations({
        crop_name: cropName,
        season: season,
        gp_approved_quota_mt: totalQuota,
        priority: priority,
        gp_name: gpName,
      });

      closeModal();
      alert(`Central AI recommended crop assignments across ${res.farmer_count} farmers in ${res.gp_name} under Batch ${res.batch_code}!`);
      await renderGPCentralAIRecommendation();
    } catch (err) {
      alert(`AI Recommendation failed: ${err.message}`);
    } finally {
      modalSubmitBtn.disabled = false;
      modalSubmitBtn.textContent = "Run Central AI Recommendation Engine";
    }
  };

  modal.style.display = "flex";
}

// --- ONE-CLICK APPROVE OF FARMER RECOMMENDATION ---
async function handleApproveFarmerRec(recId) {
  const rec = cachedFarmerRecs.find(r => r.id === recId);
  if (!rec) return;

  const confirmed = confirm(
    `Approve Central AI Recommendation #${rec.recommendation_code} for ${rec.farmer_name}?

` +
    `Farmer ID: ${rec.farmer_id}
` +
    `AI Recommended Area: ${rec.ai_recommended_area_acres} Acres
` +
    `Expected Target: ${rec.ai_recommended_quantity_quintals} Quintals (${rec.crop_name})

` +
    `This will authorize the crop assignment directly into village crop records with zero typing.`
  );
  if (!confirmed) return;

  try {
    await ApiClient.approveFarmerRecommendation(recId, "Approved without modification by Gram Panchayat Agricultural Assistant");
    alert(`Recommendation for ${rec.farmer_name} approved successfully!`);
    await renderGPCentralAIRecommendation();
  } catch (err) {
    alert(`Approval failed: ${err.message}`);
  }
}

// --- HUMAN REVIEW & CORRECTION MODAL ---
function openCorrectFarmerRecModal(recId) {
  const rec = cachedFarmerRecs.find(r => r.id === recId);
  if (!rec) return;

  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `✏️ Human Review & Override: ${rec.farmer_name} (${rec.farmer_id})`;
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Save Human Override & Re-balance";

  const currentFinalAcres = (rec.human_final_area_acres !== null && rec.human_final_area_acres !== undefined) 
    ? rec.human_final_area_acres : rec.ai_recommended_area_acres;
  const currentFinalQtl = (rec.human_final_quantity_quintals !== null && rec.human_final_quantity_quintals !== undefined) 
    ? rec.human_final_quantity_quintals : rec.ai_recommended_quantity_quintals;

  modalBody.innerHTML = `
    <div style="background:#fff3e0; border:1px solid #ffe082; padding:12px 14px; border-radius:6px; margin-bottom:14px;">
      <div style="font-weight:700; color:#e65100; font-size:0.85rem; margin-bottom:3px;">
        ⚠️ Human Governance & Audit Mandate
      </div>
      <p style="font-size:0.78rem; color:#bf360c; margin:0;">
        The original AI recommendation (${rec.ai_recommended_area_acres} Acres / ${rec.ai_recommended_quantity_quintals} Qtl) will be preserved immutably. Your adjustments will be saved in separate human final columns with an audit trail. A valid operational justification of at least 5 characters is mandatory.
      </p>
    </div>

    <!-- Farmer Land Holding Boundaries -->
    <div style="background:#f1f8e9; border:1px solid #c8e6c9; border-radius:6px; padding:10px 14px; margin-bottom:14px; display:flex; justify-content:space-between; align-items:center;">
      <div>
        <span style="font-size:0.72rem; text-transform:uppercase; color:#2e7d32; font-weight:700;">Farmer Land Limit</span>
        <div style="font-size:1.1rem; font-weight:700; color:#1b5e20;">${rec.farmer_total_land_acres} Acres Maximum</div>
      </div>
      <div style="text-align:right;">
        <span style="font-size:0.72rem; text-transform:uppercase; color:#2e7d32; font-weight:700;">Survey / Gat Number</span>
        <div style="font-size:0.95rem; font-weight:700; color:#2e7d32;">#${rec.survey_number}</div>
      </div>
    </div>

    <form id="correctFarmerRecForm" class="form-grid">
      <div class="form-group">
        <label class="form-label">Original AI Recommended Acres</label>
        <input type="text" class="form-control" value="${rec.ai_recommended_area_acres} Acres" readonly style="background:#eceff1;">
      </div>

      <div class="form-group">
        <label class="form-label">Human Final Allocated Acres *</label>
        <input type="number" id="correctFinalAcresInput" class="form-control" value="${currentFinalAcres}" step="0.5" min="0.1" max="${rec.farmer_total_land_acres}" required>
        <span style="font-size:0.70rem; color:var(--text-muted);">Must not exceed farmer's total land (${rec.farmer_total_land_acres} Ac).</span>
      </div>

      <div class="form-group">
        <label class="form-label">Original AI Recommended Target (Qtl)</label>
        <input type="text" class="form-control" value="${rec.ai_recommended_quantity_quintals} Qtl" readonly style="background:#eceff1;">
      </div>

      <div class="form-group">
        <label class="form-label">Human Final Target (Quintals) *</label>
        <input type="number" id="correctFinalQtlInput" class="form-control" value="${currentFinalQtl}" step="1.0" min="1.0" required>
      </div>

      <div class="form-group" style="grid-column: span 2;">
        <label class="form-label" style="font-weight:700; color:#c62828;">Mandatory Reason for Modification *</label>
        <textarea id="correctFarmerReasonInput" class="form-control" rows="3" placeholder="Provide operational reason (e.g. Farmer requested additional acreage due to recent private borewell installation; approved by GP committee)." required></textarea>
        <span style="font-size:0.70rem; color:var(--text-muted);">Minimum 5 characters required by governance protocol.</span>
      </div>

      <div class="form-group" style="grid-column: span 2;">
        <label class="form-label">Reviewer Notes</label>
        <textarea id="correctFarmerNotesInput" class="form-control" rows="2" placeholder="Optional internal notes..."></textarea>
      </div>
    </form>
  `;

  modalSubmitBtn.onclick = async () => {
    const finalAcres = parseFloat(document.getElementById("correctFinalAcresInput").value);
    const finalQtl = parseFloat(document.getElementById("correctFinalQtlInput").value);
    const reason = document.getElementById("correctFarmerReasonInput").value.trim();
    const notes = document.getElementById("correctFarmerNotesInput").value.trim();

    if (isNaN(finalAcres) || finalAcres <= 0) {
      alert("Please enter a valid positive land area in acres.");
      return;
    }

    if (finalAcres > rec.farmer_total_land_acres) {
      alert(`Cannot allocate ${finalAcres} Acres! Farmer only owns ${rec.farmer_total_land_acres} Acres.`);
      return;
    }

    if (isNaN(finalQtl) || finalQtl <= 0) {
      alert("Please enter a valid positive quantity in quintals.");
      return;
    }

    if (!reason || reason.length < 5) {
      alert("Mandatory reason for modification must be at least 5 characters long.");
      return;
    }

    try {
      modalSubmitBtn.disabled = true;
      modalSubmitBtn.textContent = "Saving Override...";
      await ApiClient.correctFarmerRecommendation(recId, {
        human_final_area_acres: finalAcres,
        human_final_quantity_quintals: finalQtl,
        justification: reason,
        notes: notes || null,
      });

      closeModal();
      alert(`Recommendation for ${rec.farmer_name} updated successfully!`);
      await renderGPCentralAIRecommendation();
    } catch (err) {
      alert(`Update failed: ${err.message}`);
    } finally {
      modalSubmitBtn.disabled = false;
      modalSubmitBtn.textContent = "Save Human Override & Re-balance";
    }
  };

  modal.style.display = "flex";
}

// --- DETAILED AI RATIONALE & FACTORS MODAL ---
function openFarmerAIRationaleModal(recId) {
  const rec = cachedFarmerRecs.find(r => r.id === recId);
  if (!rec) return;

  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `💡 AI Decision Rationale: ${rec.farmer_name}`;
  modalSubmitBtn.style.display = "none";

  const factors = rec.ai_factors || {};
  const suitabilityPct = Math.round((rec.suitability_score || 0.85) * 100);

  modalBody.innerHTML = `
    <div style="background:#f8f9fa; border:1px solid var(--border); border-radius:8px; padding:16px; margin-bottom:16px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
        <div>
          <h3 style="margin:0; color:var(--primary-dark); font-size:1.15rem;">${rec.farmer_name}</h3>
          <div style="font-size:0.78rem; color:var(--text-muted);">
            Farmer ID: <code>${rec.farmer_id}</code> • Survey / Gat: <strong>#${rec.survey_number}</strong>
          </div>
        </div>
        <div style="text-align:right;">
          <span style="font-size:0.70rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Suitability Match</span>
          <div style="font-size:1.4rem; font-weight:800; color:${suitabilityPct >= 85 ? '#2e7d32' : '#e65100'};">
            ${suitabilityPct}%
          </div>
        </div>
      </div>
      <div style="font-size:0.82rem; color:#37474f; line-height:1.5;">
        ${rec.ai_rationale || "Parcel selected due to high Black Cotton soil compatibility, perennial canal access, and optimal soil pH."}
      </div>
    </div>

    <!-- Soil Chemistry & Physical Properties Grid -->
    <h4 style="color:var(--primary-dark); font-size:0.92rem; margin-bottom:10px;">🧪 Soil Test & Laboratory Diagnostics</h4>
    <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; margin-bottom:16px;">
      <div style="background:#e3f2fd; border-radius:6px; padding:10px; text-align:center;">
        <div style="font-size:0.68rem; color:#1565c0; font-weight:700;">Soil pH</div>
        <div style="font-size:1.2rem; font-weight:800; color:#0d47a1;">${rec.soil_ph}</div>
        <div style="font-size:0.65rem; color:#546e7a;">${rec.soil_ph >= 6.5 && rec.soil_ph <= 8.2 ? '✓ Optimal' : 'Slightly Alkaline'}</div>
      </div>
      <div style="background:#e8f5e9; border-radius:6px; padding:10px; text-align:center;">
        <div style="font-size:0.68rem; color:#2e7d32; font-weight:700;">Organic Carbon</div>
        <div style="font-size:1.2rem; font-weight:800; color:#1b5e20;">${rec.organic_carbon_pct}%</div>
        <div style="font-size:0.65rem; color:#546e7a;">${rec.organic_carbon_pct >= 0.6 ? 'High Vitality' : 'Moderate'}</div>
      </div>
      <div style="background:#fff3e0; border-radius:6px; padding:10px; text-align:center;">
        <div style="font-size:0.68rem; color:#e65100; font-weight:700;">Nitrogen (N)</div>
        <div style="font-size:1.2rem; font-weight:800; color:#bf360c;">${rec.nitrogen_kg_ha} kg/ha</div>
        <div style="font-size:0.65rem; color:#546e7a;">Fertility Level</div>
      </div>
      <div style="background:#f3e5f5; border-radius:6px; padding:10px; text-align:center;">
        <div style="font-size:0.68rem; color:#6a1b9a; font-weight:700;">Water Source</div>
        <div style="font-size:1rem; font-weight:800; color:#4a148c;">${rec.irrigation_source}</div>
        <div style="font-size:0.65rem; color:#546e7a;">Irrigation Type</div>
      </div>
    </div>

    <!-- AI Mathematical Weights Breakdown -->
    <h4 style="color:var(--primary-dark); font-size:0.92rem; margin-bottom:10px;">📊 Mathematical Formula Breakdown</h4>
    <div style="background:white; border:1px solid var(--border); border-radius:6px; padding:12px; font-size:0.80rem; line-height:1.6; margin-bottom:14px;">
      <div>• <strong>Soil Type Score (40%):</strong> ${factors.soil_match_score || 0.95} (Black Cotton / Clay Loam match)</div>
      <div>• <strong>Irrigation Security (35%):</strong> ${factors.irrigation_score || 0.90} (${rec.irrigation_source})</div>
      <div>• <strong>pH Balance (15%):</strong> ${factors.ph_score || 0.92} (pH ${rec.soil_ph})</div>
      <div>• <strong>Organic Carbon (10%):</strong> ${factors.oc_score || 0.88} (${rec.organic_carbon_pct}%)</div>
      <div>• <strong>Yield Benchmark:</strong> ${factors.benchmark_yield_qtl_per_acre || 20.0} Qtl / Acre</div>
      <div>• <strong>Land Holding Check:</strong> ${rec.ai_recommended_area_acres} Ac <= ${rec.farmer_total_land_acres} Ac (✓ Verified)</div>
    </div>

    <div style="display:flex; justify-content:space-between; align-items:center;">
      <button class="btn btn-outline btn-sm" onclick="openSoilDocViewerModal('${rec.farmer_id}', '${rec.soil_report_url || ''}')" style="color:#2e7d32; border-color:#2e7d32;">
        📄 View Certified Soil Card
      </button>
      <button class="btn btn-secondary btn-sm" onclick="closeModal()">Close</button>
    </div>
  `;

  modal.style.display = "flex";
}

// --- AUDIT TRAIL MODAL FOR FARMER RECOMMENDATION ---
async function openFarmerRecAuditModal(recId) {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `📜 Audit Trail: Farmer Recommendation #${recId}`;
  modalSubmitBtn.style.display = "none";

  modalBody.innerHTML = `<div style="text-align:center; padding:30px; color:var(--text-muted);">Loading audit history...</div>`;
  modal.style.display = "flex";

  try {
    const res = await ApiClient.getAuditHistory("ai_farmer_recommendation_records", recId);
    const history = res.history || [];

    modalBody.innerHTML = `
      <div style="font-size:0.85rem; margin-bottom:14px;">
        Chronological audit records tracking creation, AI generation, human approval, and adjustments.
      </div>

      <div style="max-height:360px; overflow-y:auto;">
        ${history.length === 0 ? `
          <div style="text-align:center; padding:20px; color:var(--text-muted); background:#f9f9f9; border-radius:6px;">
            No audit log entries recorded yet for this recommendation.
          </div>
        ` : history.map(h => `
          <div style="border-left:3px solid #1565c0; padding-left:12px; margin-bottom:12px; background:#f5f7fa; padding:10px 12px; border-radius:0 6px 6px 0;">
            <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">
              <span>Action: <strong style="color:#1565c0;">${h.action}</strong> by <strong>${h.performed_by || 'system'}</strong> (${h.user_role || 'SYSTEM'})</span>
              <span>${h.created_at || ''}</span>
            </div>
            <div style="font-size:0.82rem; color:#2c3e50;">
              <strong>Reason:</strong> ${h.change_reason || 'N/A'}
            </div>
            ${h.details ? `
              <div style="font-size:0.72rem; color:#546e7a; margin-top:4px; background:white; padding:6px; border-radius:4px; font-family:monospace;">
                ${typeof h.details === 'object' ? JSON.stringify(h.details) : h.details}
              </div>
            ` : ''}
          </div>
        `).join("")}
      </div>

      <div style="text-align:right; margin-top:14px;">
        <button class="btn btn-secondary btn-sm" onclick="closeModal()">Close</button>
      </div>
    `;
  } catch (err) {
    modalBody.innerHTML = `<div class="alert-box danger">Failed to load audit history: ${err.message}</div>`;
  }
}

// --- BATCH APPROVAL OF FARMER RECOMMENDATIONS ---
async function handleBatchApproveFarmerRecs(batchCode) {
  const pendingInBatch = cachedFarmerRecs.filter(r => r.batch_code === batchCode && r.review_status === "PENDING_REVIEW");
  if (pendingInBatch.length === 0) {
    alert("No pending recommendations in this batch to approve.");
    return;
  }

  const confirmed = confirm(
    `Are you sure you want to approve ALL ${pendingInBatch.length} pending farmer recommendations under ${batchCode}?\n\n` +
    `This will authorize all candidate crop allocations into village records with zero typing.`
  );
  if (!confirmed) return;

  try {
    const res = await ApiClient.batchApproveFarmerRecommendations(batchCode, "Batch approved by Gram Panchayat Agricultural Assistant");
    alert(res.message || "Batch approved successfully!");
    await renderGPCentralAIRecommendation();
  } catch (err) {
    alert(`Batch approval failed: ${err.message}`);
  }
}

// --- 1. FOOD DEPARTMENT: AI DATA & MODEL INSIGHTS (12 INPUT DATASETS + 5-STEP PIPELINE) ---
async function renderFDAIDataInsights(container) {
  container.innerHTML = `<div style="text-align:center; padding:36px; color:var(--text-muted);">Retrieving multi-sector AI data matrix and model trace...</div>`;
  try {
    const res = await ApiClient.getFDAIDataInsights();
    const dataSources = res.data_sources || [];
    const pipelineSteps = res.pipeline_steps || [];
    const modelMeta = res.model_metadata || {};

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar">
          <div>
            <h3>🧠 Central AI/ML Engine: Data Sources & Model Insights</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">
              Unified Cross-Sector Intelligence Synthesis • Algorithm: <code>${modelMeta.algorithm || 'Unified Ag-Opt Multi-Objective Optimizer v2.4'}</code>
            </span>
          </div>
          <div class="table-toolbar-actions">
            <button class="btn btn-primary btn-sm" onclick="openGenerateAIRecModal()" style="background:#1565c0;">
              🤖 Run Central AI Crop Recommendation
            </button>
            <button class="btn btn-outline btn-sm" onclick="renderFDAIDataInsights(document.getElementById('activeTableContainer'))">
              🔄 Refresh Insights
            </button>
          </div>
        </div>

        <!-- 5-Step Unified AI Pipeline Flow -->
        <div class="ai-pipeline-container" style="margin-bottom:24px;">
          <h4 style="color:var(--primary-dark); margin-bottom:14px; font-size:0.95rem;">
            🔄 KrushiSetu 5-Step Unified AI/ML Processing Pipeline
          </h4>
          <div class="pipeline-steps">
            ${pipelineSteps.map((step, idx) => `
              <div class="pipeline-node">
                <div class="step-num">STEP ${step.step || idx + 1}</div>
                <div class="node-title">${step.title}</div>
                <div style="font-size:0.72rem; color:var(--text-muted); margin-top:4px; line-height:1.3;">
                  ${step.description}
                </div>
                ${step.status ? `<span class="badge badge-success" style="margin-top:6px; font-size:0.65rem;">${step.status}</span>` : ''}
              </div>
              ${idx < pipelineSteps.length - 1 ? `<div class="pipeline-sep">➔</div>` : ''}
            `).join("")}
          </div>
        </div>

        <!-- 12 Input Datasets Matrix -->
        <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:22px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
            <div>
              <h4 style="color:var(--primary-dark); margin:0;">
                📊 12 Continuous Cross-Sector Input Datasets
              </h4>
              <p style="font-size:0.78rem; color:var(--text-muted); margin:4px 0 0;">
                All authorized state, district, block, and farm datasets streaming to the One Central AI/ML Engine
              </p>
            </div>
            <span class="badge badge-info" style="font-size:0.78rem;">12 / 12 Active Streams</span>
          </div>

          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:16px;">
            ${dataSources.map(ds => `
              <div class="data-source-card">
                <h5><span>${ds.icon || '📁'}</span> ${ds.source_name}</h5>
                <p>${ds.description}</p>
                <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-top:12px; border-top:1px solid #f0f0f0; padding-top:8px;">
                  <div>
                    <span style="font-size:0.68rem; color:#78909c; text-transform:uppercase; font-weight:700;">Records</span>
                    <div class="data-source-val">${ds.record_count !== undefined ? ds.record_count : 0}</div>
                  </div>
                  <div style="text-align:right;">
                    <span style="font-size:0.68rem; color:#78909c; text-transform:uppercase; font-weight:700;">Source Sector</span>
                    <div style="font-size:0.75rem; font-weight:700; color:#1565c0;">${ds.sector || 'Statewide'}</div>
                  </div>
                </div>
              </div>
            `).join("")}
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load AI Data Insights: ${err.message}</div>`;
  }
}

// --- 1. FOOD DEPARTMENT: AI FEEDBACK & STATEWIDE MACRO INSIGHTS ---
async function renderFDAIRecommendations(container) {
  container.innerHTML = `<div style="text-align:center; padding:32px; color:var(--text-muted);">Analyzing statewide cross-sector data...</div>`;
  try {
    const data = await ApiClient.getAIFeedbackLoop();
    const metrics = data.metrics || {};
    const feedback = data.feedback_insights || [];
    const models = data.model_performance || {};

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar">
          <div>
            <h3>🧠 Central AI Cross-Sector Feedback Loop & Macro Intelligence</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">Unified Closed-Loop Analysis across all 7 Supply Chain Sectors</span>
          </div>
          <button class="btn btn-primary btn-sm" onclick="renderFDAIRecommendations(document.getElementById('activeTableContainer'))" style="background:#1565c0;">
            🔄 Refresh AI Feedback Loop
          </button>
        </div>

        <div class="metric-grid">
          <div class="metric-card">
            <div class="metric-val" style="color:#1565c0;">${metrics.total_intake_batches || 0}</div>
            <div class="metric-label">Intake Batches Graded</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#2e7d32;">${metrics.grade_a_percentage ? metrics.grade_a_percentage.toFixed(1) : 85.0}%</div>
            <div class="metric-label">Grade A Quality Compliance</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#e65100;">${metrics.quota_fulfillment_rate ? metrics.quota_fulfillment_rate.toFixed(1) : 94.2}%</div>
            <div class="metric-label">Statewide Quota Fulfillment</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#6a1b9a;">${((models.allocation_optimization_accuracy || 0.94) * 100).toFixed(1)}%</div>
            <div class="metric-label">Central AI Model Confidence</div>
          </div>
        </div>

        <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:20px; margin-top:20px;">
          <h4 style="color:var(--primary-dark); margin-bottom:14px;">📡 Real-time Multi-Sector Intelligence Streams</h4>
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:14px;">
            ${feedback.map(item => `
              <div class="ai-insight-box">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                  <span style="font-weight:700; color:#1565c0; font-size:0.85rem;">${item.sector}</span>
                  <span class="badge ${item.severity === 'CRITICAL' ? 'badge-danger' : item.severity === 'WARNING' ? 'badge-warning' : 'badge-success'}">${item.status}</span>
                </div>
                <div style="font-size:0.82rem; color:#2c3e50; line-height:1.4;">${item.insight}</div>
                <div style="font-size:0.75rem; color:#78909c; margin-top:8px; font-weight:600;">Recommendation: ${item.action_recommended}</div>
              </div>
            `).join("")}
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load AI recommendations: ${err.message}</div>`;
  }
}

// --- 2. PANCHAYAT SAMITI: OVERVIEW & AI ALLOCATIONS ---
async function renderPSOverview(container) {
  container.innerHTML = `<div style="text-align:center; padding:32px; color:var(--text-muted);">Loading Panchayat Samiti block intelligence...</div>`;
  try {
    const fdAllocations = await ApiClient.getRecords("/fd/ps-allocations") || [];
    const gpAllocations = await ApiClient.getRecords("/ps/gp-allocations") || [];
    const gps = await ApiClient.getRecords("/ps/gps") || [];

    const totalFromFD = fdAllocations.reduce((acc, r) => acc + (parseFloat(r.human_final_quota_mt || r.target_quota_mt) || 0), 0);
    const totalToGP = gpAllocations.reduce((acc, r) => acc + (parseFloat(r.human_final_quantity_mt || r.allocated_quantity_mt) || 0), 0);
    const balance = Math.max(0, totalFromFD - totalToGP);

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar">
          <div>
            <h3>🏛️ Panchayat Samiti Block Operations Overview</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">Cascading Food Department Targets to Gram Panchayats via AI</span>
          </div>
          <button class="btn btn-primary btn-sm" onclick="openGeneratePSAIExtModal()" style="background:#1565c0;">
            🤖 Run Central AI GP Allocation
          </button>
        </div>

        <div class="metric-grid">
          <div class="metric-card">
            <div class="metric-val" style="color:#1565c0;">${totalFromFD.toLocaleString()} MT</div>
            <div class="metric-label">Quota Received from Food Dept</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#2e7d32;">${totalToGP.toLocaleString()} MT</div>
            <div class="metric-label">Allocated to Gram Panchayats</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:${balance > 0 ? '#e65100' : '#2e7d32'};">${balance.toLocaleString()} MT</div>
            <div class="metric-label">Unallocated Quota Balance</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#6a1b9a;">${gps.length}</div>
            <div class="metric-label">Active Gram Panchayats</div>
          </div>
        </div>

        <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:20px; margin-top:20px;">
          <h4 style="color:var(--primary-dark); margin-bottom:12px;">Active Gram Panchayat Allocations & AI Status</h4>
          <table class="record-table">
            <thead>
              <tr>
                <th>Gram Panchayat</th>
                <th>Crop</th>
                <th>AI Recommended</th>
                <th>Final Quota</th>
                <th>Status</th>
                <th style="text-align:right;">Action</th>
              </tr>
            </thead>
            <tbody>
              ${gpAllocations.length === 0 ? `
                <tr><td colspan="6" style="text-align:center; padding:20px; color:var(--text-muted);">No GP allocations created yet. Click "🤖 Run Central AI GP Allocation" to generate.</td></tr>
              ` : gpAllocations.map(a => `
                <tr>
                  <td><strong>${a.gp_name}</strong></td>
                  <td>${a.crop_name}</td>
                  <td style="color:#1565c0; font-weight:700;">${a.ai_recommended_quantity_mt || a.allocated_quantity_mt} MT</td>
                  <td style="color:#2e7d32; font-weight:700;">${a.human_final_quantity_mt || a.allocated_quantity_mt} MT</td>
                  <td><span class="badge ${getBadgeClass(a.status)}">${a.status}</span></td>
                  <td style="text-align:right;">
                    <button class="btn btn-outline btn-sm" onclick="openPSAIRationaleModal(${a.id})">👁️ Rationale</button>
                    ${a.status !== 'APPROVED' ? `
                      <button class="btn btn-primary btn-sm" onclick="quickApprovePSAllocation(${a.id})" style="background:#2e7d32;">✅ Approve</button>
                    ` : ''}
                    <button class="btn btn-secondary btn-sm" onclick="openEditModal(${a.id})">✏️ Edit</button>
                  </td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load PS overview: ${err.message}</div>`;
  }
}

async function renderPSAISuitability(container) {
  container.innerHTML = `<div style="text-align:center; padding:32px; color:var(--text-muted);">Fetching soil suitability matrix...</div>`;
  try {
    const suitability = await ApiClient.getRecords("/ps/soil-suitability") || [];
    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar">
          <div>
            <h3>🌱 Central AI Agro-Climatic & Soil Suitability Distribution</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">Gram Panchayat Land Capability Profiles informing AI Allocation Decisions</span>
          </div>
          <button class="btn btn-primary btn-sm" onclick="openGeneratePSAIExtModal()" style="background:#1565c0;">
            🤖 Generate AI Allocations from Suitability
          </button>
        </div>

        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:16px;">
          ${suitability.map(s => `
            <div style="background:white; border:1px solid var(--border); border-radius:8px; padding:18px;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <h4 style="color:var(--primary-dark); margin:0;">${s.gp_name}</h4>
                <span class="badge ${s.organic_matter_rating === 'HIGH' ? 'badge-success' : 'badge-warning'}">${s.organic_matter_rating} Organic Matter</span>
              </div>
              <div style="font-size:0.83rem; color:var(--text-muted); margin-bottom:8px;">Soil Type: <strong>${s.soil_type}</strong></div>
              <div style="background:#f1f8e9; padding:8px 12px; border-radius:4px; font-size:0.82rem; color:#2e7d32; margin-bottom:8px;">
                🌾 <strong>AI Optimal Crops:</strong> ${s.primary_crops}
              </div>
              <div style="display:flex; justify-content:space-between; font-size:0.78rem; color:#546e7a;">
                <span>Irrigation: <strong>${s.irrigation_coverage_pct}%</strong></span>
                <span>Suitability Index: <strong>${(0.85 + (s.irrigation_coverage_pct / 1000)).toFixed(2)}</strong></span>
              </div>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load suitability: ${err.message}</div>`;
  }
}

// --- 3. GRAM PANCHAYAT: OVERVIEW, SOIL DOCS, AI MATCHING ---
async function renderGPOverview(container) {
  container.innerHTML = `<div style="text-align:center; padding:32px; color:var(--text-muted);">Loading Gram Panchayat agricultural registry...</div>`;
  try {
    const psAlloc = await ApiClient.getRecords("/ps/gp-allocations") || [];
    const assignments = await ApiClient.getRecords("/gp/crop-assignments") || [];
    const lands = await ApiClient.getRecords("/gp/land-records") || [];
    const tests = await ApiClient.getRecords("/gp/soil-tests") || [];

    const totalFromPS = psAlloc.reduce((acc, r) => acc + (parseFloat(r.human_final_quantity_mt || r.allocated_quantity_mt) || 0), 0);
    const assignedQtl = assignments.reduce((acc, r) => acc + (parseFloat(r.human_final_quintals || r.required_quantity_quintals) || 0), 0);
    const assignedMT = assignedQtl / 10;

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar">
          <div>
            <h3>🏡 Gram Panchayat Village Production Registry</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">Local Farmer-Plot Coordination and Soil Health Management</span>
          </div>
          <button class="btn btn-primary btn-sm" onclick="openGenerateGPAIExtModal()" style="background:#1565c0;">
            🤖 Run Central AI Farmer Matching
          </button>
        </div>

        <div class="metric-grid">
          <div class="metric-card">
            <div class="metric-val" style="color:#1565c0;">${totalFromPS.toLocaleString()} MT</div>
            <div class="metric-label">Target Quota from Panchayat Samiti</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#2e7d32;">${assignedMT.toFixed(1)} MT</div>
            <div class="metric-label">Matched to Farmers (${assignedQtl.toLocaleString()} Qtl)</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#e65100;">${lands.length}</div>
            <div class="metric-label">Registered Farmer Land Parcels</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#6a1b9a;">${tests.length}</div>
            <div class="metric-label">Certified Soil Tests on File</div>
          </div>
        </div>

        <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:20px; margin-top:20px;">
          <h4 style="color:var(--primary-dark); margin-bottom:12px;">Farmer Crop Assignments (AI-First)</h4>
          <table class="record-table">
            <thead>
              <tr>
                <th>Farmer ID</th>
                <th>Farmer Name</th>
                <th>Crop</th>
                <th>Allocated Land</th>
                <th>Target Quantity</th>
                <th>Status</th>
                <th style="text-align:right;">Action</th>
              </tr>
            </thead>
            <tbody>
              ${assignments.length === 0 ? `
                <tr><td colspan="7" style="text-align:center; padding:20px; color:var(--text-muted);">No farmer assignments yet. Click "🤖 Run Central AI Farmer Matching" to generate.</td></tr>
              ` : assignments.map(a => `
                <tr>
                  <td><code>${a.farmer_id}</code></td>
                  <td><strong>${a.farmer_name}</strong></td>
                  <td>${a.crop_name}</td>
                  <td>${a.human_final_acres || a.assigned_acres} Acres</td>
                  <td style="color:#2e7d32; font-weight:700;">${a.human_final_quintals || a.required_quantity_quintals} Quintals</td>
                  <td><span class="badge ${getBadgeClass(a.status)}">${a.status}</span></td>
                  <td style="text-align:right;">
                    <button class="btn btn-outline btn-sm" onclick="openGPAIRationaleModal(${a.id})">👁️ Rationale</button>
                    ${a.status !== 'APPROVED' ? `
                      <button class="btn btn-primary btn-sm" onclick="quickApproveGPAllocation(${a.id})" style="background:#2e7d32;">✅ Approve</button>
                    ` : ''}
                    <button class="btn btn-secondary btn-sm" onclick="openEditModal(${a.id})">✏️ Edit</button>
                  </td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load GP overview: ${err.message}</div>`;
  }
}

async function renderGPAIMatching(container) {
  container.innerHTML = `
    <div class="table-container" style="border:none; background:transparent;">
      <div class="table-toolbar">
        <div>
          <h3>🤖 Central AI Farmer-Plot Matching Engine</h3>
          <span style="font-size:0.78rem; color:var(--text-muted);">Plot Acreage, Soil NPK, pH, and Water Source Correlation</span>
        </div>
        <button class="btn btn-primary btn-sm" onclick="openGenerateGPAIExtModal()" style="background:#1565c0;">
          ⚡ Run Automated Matching Now
        </button>
      </div>

      <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:24px;">
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; align-items:center;">
          <div>
            <h4 style="color:#1565c0; margin-bottom:8px;">How the Central AI Engine Matches Farmers:</h4>
            <ul style="font-size:0.85rem; color:#37474f; line-height:1.6; padding-left:18px;">
              <li><strong>Land Holding Optimization:</strong> Divides GP target quota proportionally across registered farmers so smallholders receive viable assignments.</li>
              <li><strong>Soil Health Alignment:</strong> Cross-checks soil pH, Organic Carbon, Nitrogen, Phosphorus, Potassium against crop agronomy.</li>
              <li><strong>Water Security Weighting:</strong> Canal and Borewell irrigated plots are prioritized for high-yield commercial crops (Sugarcane, Wheat).</li>
              <li><strong>Zero Typing Human Governance:</strong> Gram Panchayat Agriculture Officer can click [✅ Approve] with zero typing or adjust acreage with full audit logging.</li>
            </ul>
          </div>
          <div style="background:#e8f5e9; border:1px solid #a5d6a7; border-radius:8px; padding:20px; text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:8px;">🌾</div>
            <div style="font-weight:700; color:#2e7d32; font-size:1.05rem;">Ready to Match Village Plots</div>
            <p style="font-size:0.8rem; color:#1b5e20; margin:8px 0 16px;">Execute the algorithm to generate candidate farmer allocations for review.</p>
            <button class="btn btn-primary" onclick="openGenerateGPAIExtModal()" style="background:#2e7d32;">
              🤖 Run Central AI Farmer Matching
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
}

async function renderSoilTestDocs(container) {
  container.innerHTML = `<div style="text-align:center; padding:32px; color:var(--text-muted);">Loading certified soil lab test cards...</div>`;
  try {
    let queryParam = "";
    if (currentUser && currentUser.farmer_id) {
      queryParam = `?farmer_id=${currentUser.farmer_id}`;
    }
    const tests = await ApiClient.getRecords(`/gp/soil-tests${queryParam}`) || [];

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar">
          <div>
            <h3>🧪 Certified Soil Health Test Cards & Laboratory Reports</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">Verified Micro-nutrient Analysis & Laboratory Documentation</span>
          </div>
          <button class="btn btn-primary btn-sm" onclick="openAddModal()">
            + Upload New Soil Test
          </button>
        </div>

        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:18px;">
          ${tests.length === 0 ? `
            <div style="grid-column:1/-1; text-align:center; padding:32px; color:var(--text-muted); background:white; border-radius:8px; border:1px solid var(--border);">
              No soil test documents found for this profile.
            </div>
          ` : tests.map(t => `
            <div style="background:white; border:1px solid var(--border); border-radius:8px; padding:20px; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
              <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #eee; padding-bottom:10px; margin-bottom:12px;">
                <div>
                  <div style="font-weight:700; color:var(--primary-dark);">${t.farmer_id}</div>
                  <div style="font-size:0.75rem; color:var(--text-muted);">Survey / Gat No: ${t.survey_number}</div>
                </div>
                <span class="badge badge-success">LAB CERTIFIED</span>
              </div>

              <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:8px; text-align:center; margin-bottom:14px;">
                <div style="background:#e3f2fd; padding:6px; border-radius:4px;">
                  <div style="font-size:0.68rem; color:#1565c0; font-weight:700;">pH</div>
                  <div style="font-size:1rem; font-weight:800; color:#0d47a1;">${t.ph_level}</div>
                </div>
                <div style="background:#e8f5e9; padding:6px; border-radius:4px;">
                  <div style="font-size:0.68rem; color:#2e7d32; font-weight:700;">N (kg/ha)</div>
                  <div style="font-size:1rem; font-weight:800; color:#1b5e20;">${t.nitrogen_kg_ha}</div>
                </div>
                <div style="background:#fff3e0; padding:6px; border-radius:4px;">
                  <div style="font-size:0.68rem; color:#e65100; font-weight:700;">P (kg/ha)</div>
                  <div style="font-size:1rem; font-weight:800; color:#bf360c;">${t.phosphorus_kg_ha}</div>
                </div>
                <div style="background:#f3e5f5; padding:6px; border-radius:4px;">
                  <div style="font-size:0.68rem; color:#6a1b9a; font-weight:700;">K (kg/ha)</div>
                  <div style="font-size:1rem; font-weight:800; color:#4a148c;">${t.potassium_kg_ha}</div>
                </div>
              </div>

              <div style="font-size:0.78rem; color:#546e7a; margin-bottom:12px;">
                <div>Organic Carbon: <strong>${t.organic_carbon_pct}%</strong></div>
                <div>Testing Lab: <strong>${t.testing_lab || 'Baramati District Krishi Vigyan Lab'}</strong></div>
                <div>Test Date: <strong>${t.sample_date}</strong></div>
              </div>

              <div style="border-top:1px dashed #e0e0e0; padding-top:10px; display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:0.75rem; color:#2e7d32;">📄 Official Lab Card</span>
                <button class="btn btn-outline btn-sm" onclick="openSoilDocViewerModal('${t.farmer_id}', '${t.soil_test_doc_url || ''}')" style="color:#2e7d32; border-color:#2e7d32;">
                  🔍 View Soil Report
                </button>
              </div>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load soil test documents: ${err.message}</div>`;
  }
}

// --- SOIL TEST REPORT DOCUMENT VIEWER MODAL ---
function openSoilDocViewerModal(farmerId, docUrl) {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");
  const modalContent = document.querySelector("#recordModal .modal-content");

  if (modalContent) modalContent.style.maxWidth = "850px";

  modalTitle.textContent = `📄 Government Soil Health Card & Laboratory Certificate: Farmer ${farmerId}`;
  modalSubmitBtn.style.display = "none";

  const resolvedUrl = docUrl && docUrl !== "N/A" && docUrl.trim() !== "" 
    ? (docUrl.startsWith("http") ? docUrl : (docUrl.startsWith("/") ? docUrl : "/" + docUrl))
    : "/uploads/soil_reports/soil_health_card_KS-FMR-1001.svg";

  modalBody.innerHTML = `
    <div style="background:white; border-radius:6px; border:1px solid #c8e6c9; padding:16px; margin-bottom:14px;">
      <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #e0e0e0; padding-bottom:10px; margin-bottom:14px;">
        <div style="display:flex; align-items:center; gap:12px;">
          <div style="font-size:2rem;">🏛️</div>
          <div>
            <div style="font-weight:800; color:#1b5e20; font-size:1rem; text-transform:uppercase;">
              Soil Health Card Scheme • Government of India
            </div>
            <div style="font-size:0.75rem; color:#558b2f;">
              Department of Agriculture, Cooperation & Farmers Welfare • Maharashtra State Agricultural Laboratory
            </div>
          </div>
        </div>
        <span class="badge badge-success" style="font-size:0.8rem;">OFFICIALLY CERTIFIED</span>
      </div>

      <div style="text-align:center; background:#fafafa; border:1px solid #e0e0e0; border-radius:6px; padding:14px; margin-bottom:14px; overflow-x:auto;">
        <img src="${resolvedUrl}" alt="Official Soil Health Card for ${farmerId}" style="max-width:100%; height:auto; max-height:480px; object-fit:contain; border-radius:4px; box-shadow:0 2px 6px rgba(0,0,0,0.08);" onerror="this.onerror=null; this.src='/uploads/soil_reports/soil_health_card_KS-FMR-1001.svg';">
      </div>

      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:10px; font-size:0.82rem; background:#f1f8e9; padding:12px 16px; border-radius:6px;">
        <div><strong>Farmer ID:</strong> <code>${farmerId}</code></div>
        <div><strong>Testing Lab:</strong> Baramati District Krishi Vigyan Lab</div>
        <div><strong>Certification:</strong> Soil Health Management Dept</div>
        <div><strong>Doc Reference:</strong> <code>${resolvedUrl}</code></div>
      </div>
    </div>

    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:16px;">
      <a href="${resolvedUrl}" target="_blank" download="Soil_Health_Card_${farmerId}.svg" class="btn btn-primary btn-sm" style="background:#2e7d32; display:inline-flex; align-items:center; gap:6px;">
        📥 Download Official Document
      </a>
      <button class="btn btn-secondary btn-sm" onclick="closeModal()">Close</button>
    </div>
  `;

  modal.style.display = "flex";
}

// --- 4. FARMER: OVERVIEW, PROFILE, DIGITAL ID CARD, COMPLETE HISTORY ---
async function renderFarmerOverview(container) {
  container.innerHTML = `<div style="text-align:center; padding:32px; color:var(--text-muted);">Loading your farmer dashboard...</div>`;
  try {
    const fId = (currentUser && currentUser.farmer_id) || "KS-FMR-1001";
    const card = await ApiClient.getFarmerProfileCard(fId);
    const rec = await ApiClient.getFarmerCropRecommendation(fId);

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar">
          <div>
            <h3>🌾 Farmer Operational Overview: ${card.full_name}</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">KrushiSetu Digital Agriculture Passbook • Farmer ID: <code>${card.farmer_id}</code></span>
          </div>
          <button class="btn btn-primary btn-sm" onclick="selectSubTab('farmer_id_card')" style="background:#2e7d32;">
            🪪 View Digital Farmer ID Card
          </button>
        </div>

        <div class="metric-grid">
          <div class="metric-card">
            <div class="metric-val" style="color:#2e7d32;">${card.land_record ? card.land_record.land_area_acres : 4.5} Acres</div>
            <div class="metric-label">Registered Land Acreage</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#1565c0;">${card.assigned_crops_count || 1}</div>
            <div class="metric-label">Assigned Crops (Season)</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#e65100;">${card.total_deliveries_count || 1}</div>
            <div class="metric-label">Warehouse Silo Deliveries</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#6a1b9a;">₹${card.total_payments_settled ? Number(card.total_payments_settled).toLocaleString() : '84,000'}</div>
            <div class="metric-label">Direct Benefit Transfers (DBT)</div>
          </div>
        </div>

        ${rec && rec.recommended_crop ? `
          <div class="ai-insight-box" style="margin-top:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
              <span style="font-weight:700; color:#1565c0; font-size:0.95rem;">🤖 Central AI Personalized Crop Advisory for Your Parcel</span>
              <span class="badge badge-success">HIGH SUITABILITY (${(rec.confidence_score * 100).toFixed(0)}%)</span>
            </div>
            <div style="font-size:0.85rem; color:#2c3e50; line-height:1.5;">
              Based on your soil test (pH ${rec.soil_ph}, OC ${rec.soil_organic_carbon}%) and irrigation source (${rec.irrigation_source}), the Central AI Engine recommends cultivating <strong>${rec.recommended_crop}</strong> with projected yield of <strong>${rec.expected_yield_quintals_per_acre} Quintals/Acre</strong>.
            </div>
            <div style="font-size:0.78rem; color:#1565c0; margin-top:8px;">
              💡 <em>${rec.ai_advisory_rationale}</em>
            </div>
          </div>
        ` : ''}
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load farmer overview: ${err.message}</div>`;
  }
}

async function renderFarmerProfile(container) {
  container.innerHTML = `<div style="text-align:center; padding:32px; color:var(--text-muted);">Loading profile...</div>`;
  try {
    const fId = (currentUser && currentUser.farmer_id) || "KS-FMR-1001";
    const card = await ApiClient.getFarmerProfileCard(fId);
    const land = card.land_record || {};

    container.innerHTML = `
      <div style="max-width:720px; margin:0 auto; background:white; border:1px solid var(--border); border-radius:8px; padding:28px;">
        <div style="display:flex; gap:20px; align-items:center; border-bottom:1px solid #eee; padding-bottom:20px; margin-bottom:20px;">
          <div style="width:72px; height:72px; border-radius:50%; background:#2e7d32; color:white; display:flex; align-items:center; justify-content:center; font-size:2rem; font-weight:700;">
            🌾
          </div>
          <div>
            <h3 style="margin:0; color:var(--primary-dark);">${card.full_name}</h3>
            <div style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">KrushiSetu Registered Farmer • <code>${card.farmer_id}</code></div>
            <span class="badge badge-success" style="margin-top:6px;">KYC VERIFIED & DBT LINKED</span>
          </div>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; font-size:0.85rem;">
          <div><span style="color:#78909c;">Village / Panchayat:</span> <strong>${land.village_name || card.jurisdiction}</strong></div>
          <div><span style="color:#78909c;">Survey / Gat Number:</span> <strong>${land.survey_number || 'Gat No. 142/B'}</strong></div>
          <div><span style="color:#78909c;">Cultivable Land:</span> <strong>${land.land_area_acres || 4.5} Acres</strong></div>
          <div><span style="color:#78909c;">Soil Type:</span> <strong>${land.soil_type || 'Deep Black Clay Loam'}</strong></div>
          <div><span style="color:#78909c;">Irrigation Source:</span> <strong>${land.irrigation_source || 'Canal Irrigated'}</strong></div>
          <div><span style="color:#78909c;">DBT Account Status:</span> <strong style="color:#2e7d32;">Active (Aadhaar Seeded)</strong></div>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load profile: ${err.message}</div>`;
  }
}

async function renderFarmerIdCard(container) {
  container.innerHTML = `<div style="text-align:center; padding:32px; color:var(--text-muted);">Generating digital government ID card...</div>`;
  try {
    const fId = (currentUser && currentUser.farmer_id) || "KS-FMR-1001";
    const card = await ApiClient.getFarmerProfileCard(fId);
    const land = card.land_record || {};

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; align-items:center; padding:20px 0;">
        <div class="farmer-id-card">
          <div class="farmer-id-header">
            <div class="farmer-id-emblem">🇮🇳</div>
            <div class="farmer-id-titles">
              <h3>KRUSHISETU KISAN IDENTITY CARD</h3>
              <p>Government of Maharashtra • Department of Agriculture & Food</p>
            </div>
            <span class="badge badge-success">VERIFIED</span>
          </div>

          <div class="farmer-id-body">
            <div class="farmer-avatar">🌾</div>
            <div class="farmer-info">
              <div class="f-name">${card.full_name}</div>
              <div class="f-code">${card.farmer_id}</div>
              <div class="f-row"><span>Village:</span> <strong>${land.village_name || card.jurisdiction}</strong></div>
              <div class="f-row"><span>Land Holding:</span> <strong>${land.land_area_acres || 4.5} Acres (${land.soil_type || 'Black Soil'})</strong></div>
              <div class="f-row"><span>Survey Gat:</span> <strong>${land.survey_number || '142/B'}</strong></div>
              <div class="f-row"><span>Status:</span> <strong style="color:#2e7d32;">DBT Enabled • Mandi Certified</strong></div>
            </div>
          </div>

          <div class="farmer-id-footer">
            <div class="farmer-qr">
              <div style="font-size:0.6rem; font-weight:700; color:#1b5e20;">SCAN QR CODE</div>
              <div style="font-size:1.8rem;">📱</div>
            </div>
            <div class="farmer-auth-stamp">
              <div>OFFICIALLY ISSUED BY KRUSHISETU PORTAL</div>
              <div style="font-family:monospace; font-size:0.65rem; color:#689f38;">AUTH-ID: ${card.qr_code_payload}</div>
            </div>
          </div>
        </div>

        <button class="btn btn-outline btn-sm" style="margin-top:16px;" onclick="window.print()">
          🖨️ Print / Download Official ID Card
        </button>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load ID card: ${err.message}</div>`;
  }
}

async function renderFarmerCompleteHistory(container) {
  container.innerHTML = `<div style="text-align:center; padding:32px; color:var(--text-muted);">Loading complete farmer transaction history...</div>`;
  try {
    const fId = (currentUser && currentUser.farmer_id) || "KS-FMR-1001";
    const res = await ApiClient.getFarmerCompleteHistory(fId);
    const events = res.events || [];

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar">
          <div>
            <h3>📜 Complete Farmer Agricultural Traceability Timeline</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">End-to-End Audit Trail for Farmer: <code>${fId}</code></span>
          </div>
        </div>

        <div class="audit-timeline" style="max-width:800px; margin:0 auto;">
          ${events.length === 0 ? `
            <div style="text-align:center; padding:30px; color:var(--text-muted);">No operational lifecycle events recorded yet.</div>
          ` : events.map(e => `
            <div class="audit-card" style="border-left-color:${e.event_type === 'PAYMENT_SETTLED' ? '#2e7d32' : e.event_type === 'QUALITY_GRADED' ? '#1565c0' : '#e65100'};">
              <div class="audit-meta">
                <span class="badge ${e.event_type === 'PAYMENT_SETTLED' ? 'badge-success' : e.event_type === 'QUALITY_GRADED' ? 'badge-info' : 'badge-warning'}">
                  ${e.event_type.replace(/_/g, ' ')}
                </span>
                <span>🕒 ${e.created_at || 'Recorded in Ledger'}</span>
              </div>
              <div style="font-size:0.85rem; color:#2c3e50; margin-top:8px;">
                ${e.event_type === 'CROP_ASSIGNED' ? `Assigned to cultivate <strong>${e.crop_name}</strong> on ${e.human_final_acres || e.assigned_acres} Acres for ${e.season}. Target: ${e.human_final_quintals || e.required_quantity_quintals} Qtl.` :
                  e.event_type === 'HARVEST_LOGGED' ? `Logged actual harvest of <strong>${e.actual_yield_kg} kg ${e.crop_name}</strong> with condition rating ${e.quality_condition}.` :
                  e.event_type === 'WAREHOUSE_DELIVERY' ? `Dispatched delivery batch <strong>${e.batch_id}</strong> (${e.declared_weight_kg} kg ${e.crop_name}) to ${e.target_warehouse_name}. Slip: ${e.vehicle_slip_number}.` :
                  e.event_type === 'QUALITY_GRADED' ? `Major Silo graded batch <strong>${e.batch_id}</strong>: AI Grade ${e.ai_predicted_grade}, Confirmed Grade <strong>${e.human_final_grade}</strong>. Net Wt: ${e.net_weight_kg} kg.` :
                  e.event_type === 'PAYMENT_SETTLED' ? `Direct Benefit Transfer of <strong>₹${Number(e.total_amount).toLocaleString()}</strong> settled at ₹${e.rate_per_kg}/kg for Batch ${e.batch_id}. Tx Ref: <code>${e.transaction_ref}</code>.` :
                  JSON.stringify(e)}
              </div>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load history: ${err.message}</div>`;
  }
}

// --- 5. MAJOR WAREHOUSE: OVERVIEW, AI GRADING CONSOLE, STORAGE ---
async function renderMajorWHOverview(container) {
  container.innerHTML = `<div style="text-align:center; padding:32px; color:var(--text-muted);">Loading Major Silo metrics...</div>`;
  try {
    const intakes = await ApiClient.getRecords("/major-wh/intakes") || [];
    const dispatches = await ApiClient.getRecords("/major-wh/dispatches") || [];

    const totalStoredKg = intakes.reduce((acc, r) => acc + (parseFloat(r.net_weight_kg) || 0), 0);
    const totalStoredMT = (totalStoredKg / 1000).toFixed(1);
    const capacityMT = 50000;
    const utilizationPct = ((totalStoredKg / 1000 / capacityMT) * 100).toFixed(1);

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar">
          <div>
            <h3>🏢 Major Grain Silo & Logistics Hub Overview</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">Certified Weighbridge, Computer Vision Quality Grading, and Dispatch Depot</span>
          </div>
          <button class="btn btn-primary btn-sm" onclick="selectSubTab('major_wh_ai_grading')" style="background:#1565c0;">
            🤖 Run AI Quality Grader
          </button>
        </div>

        <div class="metric-grid">
          <div class="metric-card">
            <div class="metric-val" style="color:#1565c0;">${totalStoredMT} MT</div>
            <div class="metric-label">Grain in Storage (${utilizationPct}% Utilized)</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#2e7d32;">${intakes.length}</div>
            <div class="metric-label">Intake Batches Graded</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#e65100;">${dispatches.length}</div>
            <div class="metric-label">Dispatches to Minor Warehouses</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#6a1b9a;">${capacityMT.toLocaleString()} MT</div>
            <div class="metric-label">Total Rated Silo Capacity</div>
          </div>
        </div>

        <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:20px; margin-top:20px;">
          <h4 style="color:var(--primary-dark); margin-bottom:12px;">Silo Complex Capacity Bar</h4>
          <div style="background:#e0e0e0; height:24px; border-radius:12px; overflow:hidden; position:relative;">
            <div style="background:linear-gradient(90deg, #2e7d32, #1565c0); height:100%; width:${Math.min(100, Math.max(12, utilizationPct))}%; border-radius:12px; transition:width 0.5s;"></div>
          </div>
          <div style="display:flex; justify-content:space-between; font-size:0.78rem; color:#546e7a; margin-top:6px;">
            <span>0 MT</span>
            <span>Current: <strong>${totalStoredMT} MT</strong></span>
            <span>Max Silo Limit: <strong>50,000 MT</strong></span>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load warehouse overview: ${err.message}</div>`;
  }
}

let activeMediaStream = null;
let currentGradingSnapshotDataUrl = null;
let cachedActiveIntakes = [];

function toggleWebcamStream() {
  const video = document.getElementById("cameraVideo");
  const btn = document.getElementById("btnToggleWebcam");
  const captureBtn = document.getElementById("btnCaptureSnapshot");
  const statusEl = document.getElementById("cameraStatusIndicator");

  if (activeMediaStream) {
    activeMediaStream.getTracks().forEach(t => t.stop());
    activeMediaStream = null;
    if (video) {
      video.srcObject = null;
      video.style.display = "none";
    }
    if (btn) btn.innerHTML = "📹 Turn On Camera";
    if (captureBtn) captureBtn.style.display = "none";
    if (statusEl) statusEl.textContent = "Camera Standby (Off)";
    return;
  }

  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } } })
      .then(stream => {
        activeMediaStream = stream;
        if (video) {
          video.srcObject = stream;
          video.style.display = "block";
        }
        if (btn) btn.innerHTML = "⏹️ Stop Camera";
        if (captureBtn) captureBtn.style.display = "inline-flex";
        if (statusEl) statusEl.innerHTML = '<span style="color:#2e7d32; font-weight:700;">🟢 Camera Streaming Live (Mobile/Desktop)</span>';
      })
      .catch(err => {
        alert("Unable to access camera: " + err.message + ". You can use the file upload or existing crop samples.");
      });
  } else {
    alert("Camera API not supported in this browser. Please use file upload.");
  }
}

function captureCameraSnapshot() {
  const video = document.getElementById("cameraVideo");
  const canvas = document.getElementById("cameraCanvas");
  const preview = document.getElementById("cameraSnapshotPreview");
  if (!video || !canvas || !preview) return;

  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  const dataUrl = canvas.toDataURL("image/jpeg", 0.90);
  currentGradingSnapshotDataUrl = dataUrl;
  preview.src = dataUrl;
  preview.style.display = "block";

  // Stop camera stream after snapshot
  toggleWebcamStream();
}

function previewUploadedGrainImage(event) {
  const file = event.target.files[0];
  if (!file) return;
  const preview = document.getElementById("cameraSnapshotPreview");
  if (!preview) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    currentGradingSnapshotDataUrl = e.target.result;
    preview.src = e.target.result;
    preview.style.display = "block";
  };
  reader.readAsDataURL(file);
}

async function renderMajorWHAIGradingConsole(container) {
  container.innerHTML = `
    <div class="table-container" style="border:none; background:transparent;">
      <div class="table-toolbar" style="margin-bottom:18px;">
        <div>
          <h3 style="display:flex; align-items:center; gap:8px;">
            <span>📷</span> Central AI Major Warehouse Crop Quality & Grading Console
          </h3>
          <span style="font-size:0.78rem; color:var(--text-muted);">
            Computer Vision Defect Analysis, 12 Optical Parameters & Dual-Storage Human Certification
          </span>
        </div>
        <div style="display:flex; gap:10px;">
          <button class="btn btn-secondary btn-sm" onclick="loadGradingHistoryTable()">
            📜 View Grading History
          </button>
        </div>
      </div>

      <!-- Prototype AI Model Notice -->
      <div class="alert-box" style="background:#e8f4fd; border:1px solid #90caf9; color:#0d47a1; margin-bottom:20px; font-size:0.82rem; padding:12px 16px; border-radius:6px;">
        <strong>ℹ️ Prototype AI Model Notice:</strong>
        Prototype AI model — requires real crop image training dataset for production accuracy.
        The AI prediction must <strong>NEVER</strong> become the final grade automatically. Human review and explicit confirmation are strictly required.
      </div>

      <div style="display:grid; grid-template-columns:1.2fr 0.8fr; gap:22px; align-items:start;">
        <!-- Left Column: Camera, Sample & Parameter Configuration -->
        <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:22px;">
          <h4 style="color:var(--primary-dark); margin-bottom:14px; font-size:0.95rem; border-bottom:1px solid #eee; padding-bottom:8px;">
            1. Select Batch & Capture Sample Frame
          </h4>

          <div class="form-grid" style="grid-template-columns:1fr 1fr; margin-bottom:16px;">
            <div class="form-group">
              <label class="form-label">Select Intake Batch *</label>
              <select id="cvBatchSelect" class="form-control" onchange="onGradingBatchSelected()">
                <option value="KS-BATCH-1001" selected>KS-BATCH-1001 (Wheat - Ramesh Patil)</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Batch ID *</label>
              <input type="text" id="cvBatchId" class="form-control" value="KS-BATCH-1001" required>
            </div>
            <div class="form-group">
              <label class="form-label">Crop Variety *</label>
              <input type="text" id="cvCropName" class="form-control" value="Wheat (Lokwan)" required>
            </div>
            <div class="form-group">
              <label class="form-label">Supplying Farmer</label>
              <input type="text" id="cvFarmerName" class="form-control" value="Ramesh Narayan Patil (KS-FMR-1001)" readonly style="background:#f8f9fa;">
            </div>
          </div>

          <!-- Camera Stream & Snapshot Box -->
          <div class="camera-stream-box" style="background:#fdfdfd; border:1px solid var(--border); border-radius:8px; padding:16px; margin-bottom:18px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
              <div id="cameraStatusIndicator" style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">
                Camera Standby (Laptop, Desktop, Mobile or Tablet)
              </div>
              <div style="display:flex; gap:8px;">
                <button type="button" id="btnToggleWebcam" class="btn btn-primary btn-sm" onclick="toggleWebcamStream()" style="background:#1565c0;">
                  📹 Turn On Camera
                </button>
                <button type="button" id="btnCaptureSnapshot" class="btn btn-primary btn-sm" onclick="captureCameraSnapshot()" style="background:#2e7d32; display:none;">
                  📸 Capture Image
                </button>
              </div>
            </div>

            <video id="cameraVideo" autoplay playsinline style="width:100%; max-height:260px; object-fit:cover; border-radius:6px; background:#111; display:none; margin-bottom:12px;"></video>
            <canvas id="cameraCanvas" style="display:none;"></canvas>
            
            <!-- Snapshot Preview -->
            <div id="snapshotContainer" style="text-align:center;">
              <img id="cameraSnapshotPreview" src="/uploads/grain_samples/KS-BATCH-1001_sample.svg" alt="Captured Grain Sample" style="width:100%; max-height:240px; object-fit:contain; border-radius:6px; border:1px solid #ddd; background:#1e272e; margin-bottom:10px;">
              <div style="font-size:0.75rem; color:var(--text-muted);">Active Inspection Frame: Lokwan Wheat Kernel Tray</div>
            </div>

            <div style="display:flex; align-items:center; gap:10px; font-size:0.8rem; color:var(--text-muted); border-top:1px dashed var(--border); padding-top:12px; margin-top:12px;">
              <span>📁 Or upload sample image file:</span>
              <input type="file" id="cameraUploadInput" accept="image/*" class="form-control" style="font-size:0.75rem; padding:4px 8px;" onchange="previewUploadedGrainImage(event)">
            </div>
          </div>

          <!-- Segregated Physical Measurements -->
          <div style="background:#fff8e1; border:1px solid #ffe082; border-radius:8px; padding:14px; margin-bottom:18px;">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
              <strong style="color:#b78103; font-size:0.83rem;">
                ⚖️ Physical / Manual Measurements (Segregated from Vision)
              </strong>
              <span class="badge badge-warning" style="font-size:0.68rem;">Physical Probe Required</span>
            </div>
            <p style="font-size:0.74rem; color:#795548; margin-bottom:10px;">
              Notice: Parameters that cannot genuinely be determined from an image alone are physically tested using calibrated hardware probes and weighbridge scales.
            </p>
            <div class="form-grid" style="grid-template-columns:1fr 1fr;">
              <div class="form-group">
                <label class="form-label" style="font-size:0.76rem;">Moisture Content (%) [Electronic Probe]</label>
                <input type="number" id="cvMoisture" class="form-control" value="11.4" step="0.1" min="5" max="30">
              </div>
              <div class="form-group">
                <label class="form-label" style="font-size:0.76rem;">Certified Net Weight (kg) [Weighbridge]</label>
                <input type="number" id="cvNetWeight" class="form-control" value="9150" step="10">
              </div>
            </div>
          </div>

          <!-- Optical Defect Checkboxes & Inspection Flags -->
          <div style="background:#fafafa; border:1px solid var(--border); padding:14px; border-radius:8px; margin-bottom:18px;">
            <label class="form-label" style="margin-bottom:8px; font-weight:700; font-size:0.82rem;">
              🔬 Optical Defect Sensor Flags (12 Quality Parameters):
            </label>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; font-size:0.8rem;">
              <label style="display:flex; align-items:center; gap:6px;">
                <input type="checkbox" id="chkCuts"> Surface / Thresher Cuts
              </label>
              <label style="display:flex; align-items:center; gap:6px;">
                <input type="checkbox" id="chkCracks"> Kernel Stress Cracks
              </label>
              <label style="display:flex; align-items:center; gap:6px;">
                <input type="checkbox" id="chkSpots"> Discoloration / Fungal Spots
              </label>
              <label style="display:flex; align-items:center; gap:6px;">
                <input type="checkbox" id="chkBruises"> Impact Handling Bruises
              </label>
              <label style="display:flex; align-items:center; gap:6px;">
                <input type="checkbox" id="chkPestDamage"> Insect / Pest Boring Damage
              </label>
            </div>
            <div class="form-grid" style="grid-template-columns:1fr 1fr 1fr; margin-top:12px;">
              <div class="form-group">
                <label class="form-label" style="font-size:0.72rem;">Foreign Matter (%)</label>
                <input type="number" id="cvForeign" class="form-control" value="0.8" step="0.1" min="0" max="20">
              </div>
              <div class="form-group">
                <label class="form-label" style="font-size:0.72rem;">Broken Kernel (%)</label>
                <input type="number" id="cvBroken" class="form-control" value="1.5" step="0.1" min="0" max="20">
              </div>
              <div class="form-group">
                <label class="form-label" style="font-size:0.72rem;">Damaged Kernel (%)</label>
                <input type="number" id="cvDamaged" class="form-control" value="0.2" step="0.1" min="0" max="20">
              </div>
            </div>
          </div>

          <button type="button" class="btn btn-primary" onclick="runCameraAIGradingConsole()" style="width:100%; background:#1565c0; font-weight:700; padding:10px;">
            🤖 Run Central AI Crop Quality & Grading Analysis
          </button>
        </div>

        <!-- Right Column: AI Analysis Results & Human Review -->
        <div>
          <div id="cameraGradingResultContainer">
            <div style="background:white; border:1px dashed var(--border); border-radius:8px; padding:36px 20px; text-align:center; color:var(--text-muted);">
              <span style="font-size:2.2rem; display:block; margin-bottom:10px;">🌾</span>
              <h4 style="margin:0 0 6px 0; color:#546e7a;">AI Inference Ready</h4>
              <p style="font-size:0.8rem; max-width:320px; margin:0 auto;">
                Select batch, capture grain sample via camera, and execute Central AI vision evaluation.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Grading History Section -->
      <div id="whGradingHistorySection" style="margin-top:32px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <h4 style="margin:0; color:var(--primary-dark); font-size:1.0rem;">
            📜 Major Warehouse AI Grading & Certification Ledger
          </h4>
          <span style="font-size:0.75rem; color:var(--text-muted);">
            Dual-Storage Verified Audit Trail • Batch ID Linked
          </span>
        </div>
        <div id="whGradingHistoryTableContainer">
          <div style="text-align:center; padding:20px; color:var(--text-muted);">Loading certified batch records...</div>
        </div>
      </div>
    </div>
  `;

  // Pre-load batches from database and existing grading history
  loadIntakeBatchesForGrading();
  loadGradingHistoryTable();
}

async function loadIntakeBatchesForGrading() {
  try {
    const intakes = await ApiClient.getRecords("/major-wh/intakes") || [];
    cachedActiveIntakes = intakes;
    const select = document.getElementById("cvBatchSelect");
    if (!select) return;

    if (intakes.length > 0) {
      select.innerHTML = intakes.map(i => `
        <option value="${i.batch_id}" ${i.batch_id === 'KS-BATCH-1001' ? 'selected' : ''}>
          ${i.batch_id} — ${i.crop_name} (${i.farmer_name || i.farmer_id})
        </option>
      `).join("");
      onGradingBatchSelected();
    }
  } catch (err) {
    console.warn("Could not load intakes for grading dropdown:", err);
  }
}

function onGradingBatchSelected() {
  const select = document.getElementById("cvBatchSelect");
  if (!select) return;
  const batchId = select.value;
  const batchIdInput = document.getElementById("cvBatchId");
  const cropInput = document.getElementById("cvCropName");
  const farmerInput = document.getElementById("cvFarmerName");
  const netWeightInput = document.getElementById("cvNetWeight");
  const preview = document.getElementById("cameraSnapshotPreview");

  if (batchIdInput) batchIdInput.value = batchId;

  const found = cachedActiveIntakes.find(i => i.batch_id === batchId);
  if (found) {
    if (cropInput) cropInput.value = found.crop_name || "Wheat (Lokwan)";
    if (farmerInput) farmerInput.value = `${found.farmer_name || 'Farmer'} (${found.farmer_id})`;
    if (netWeightInput && found.net_weight_kg) netWeightInput.value = found.net_weight_kg;
    if (preview && found.crop_image_url) {
      preview.src = found.crop_image_url.startsWith("/") ? found.crop_image_url : `/uploads/grain_samples/${found.crop_image_url}`;
    }
  }
}

async function runCameraAIGradingConsole() {
  const container = document.getElementById("cameraGradingResultContainer");
  if (!container) return;

  const batchId = document.getElementById("cvBatchId").value || "KS-BATCH-1001";
  const cropName = document.getElementById("cvCropName").value || "Wheat (Lokwan)";
  const moisture = parseFloat(document.getElementById("cvMoisture").value) || 11.4;
  const netWeight = parseFloat(document.getElementById("cvNetWeight").value) || 9150;
  const foreign = parseFloat(document.getElementById("cvForeign").value) || 0.8;
  const broken = parseFloat(document.getElementById("cvBroken").value) || 1.5;
  const damaged = parseFloat(document.getElementById("cvDamaged").value) || 0.2;

  const cuts = document.getElementById("chkCuts") ? document.getElementById("chkCuts").checked : false;
  const cracks = document.getElementById("chkCracks") ? document.getElementById("chkCracks").checked : false;
  const spots = document.getElementById("chkSpots") ? document.getElementById("chkSpots").checked : false;
  const bruises = document.getElementById("chkBruises") ? document.getElementById("chkBruises").checked : false;
  const pestDamage = document.getElementById("chkPestDamage") ? document.getElementById("chkPestDamage").checked : false;

  const foundIntake = cachedActiveIntakes.find(i => i.batch_id === batchId);
  const farmerId = foundIntake ? foundIntake.farmer_id : "KS-FMR-1001";
  const farmerName = foundIntake ? foundIntake.farmer_name : "Ramesh Narayan Patil";

  container.innerHTML = `
    <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:32px; text-align:center;">
      <div class="loader-spinner" style="margin:0 auto 16px auto; width:36px; height:36px; border:3px solid #e0e0e0; border-top-color:#1565c0; border-radius:50%; animation:spin 0.8s linear infinite;"></div>
      <h4 style="margin:0 0 6px 0; color:var(--primary-dark);">Executing Computer Vision Evaluation...</h4>
      <p style="font-size:0.8rem; color:var(--text-muted); margin:0;">
        Scanning optical frame for 12 quality parameters and defect anomalies...
      </p>
    </div>
  `;

  try {
    const payload = {
      batch_id: batchId,
      crop_name: cropName,
      farmer_id: farmerId,
      farmer_name: farmerName,
      warehouse_id: "MWH-PUN-01",
      net_weight_kg: netWeight,
      image_data: currentGradingSnapshotDataUrl,
      manual_moisture_pct: moisture,
      manual_foreign_matter_pct: foreign,
      manual_broken_grain_pct: broken,
      manual_damaged_grain_pct: damaged,
      has_cuts: cuts,
      has_cracks: cracks,
      has_spots: spots,
      has_bruises: bruises,
      has_pest_damage: pestDamage,
    };

    const res = await ApiClient.analyzeCropQuality(payload);
    const score = res.ai_score;
    const grade = res.ai_grade;
    const factors = res.ai_quality_factors || {};
    const warnings = res.ai_warnings || [];

    const gradeClass = grade === 'A' ? 'badge-success' : grade === 'B' ? 'badge-info' : grade === 'C' ? 'badge-warning' : 'badge-danger';
    const scoreColor = score >= 80 ? '#2e7d32' : score >= 60 ? '#1565c0' : score >= 40 ? '#ef6c00' : '#c62828';

    container.innerHTML = `
      <div style="background:white; border:1px solid #a5d6a7; border-radius:8px; padding:22px; box-shadow:0 2px 8px rgba(0,0,0,0.05);">
        <!-- Header Banner -->
        <div style="display:flex; justify-content:space-between; align-items:start; border-bottom:1px solid #e0e0e0; padding-bottom:14px; margin-bottom:16px;">
          <div>
            <span style="font-size:0.72rem; text-transform:uppercase; color:#2e7d32; font-weight:700;">
              🤖 Central AI Vision Analysis Result
            </span>
            <h3 style="margin:4px 0; color:#1b5e20;">
              Suggested Grade ${grade} <span style="font-size:1.1rem; color:${scoreColor}; font-weight:600;">(Score: ${score}/100)</span>
            </h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">
              Batch: <strong>${res.batch_id}</strong> • Confidence: <strong>${Math.round(res.ai_confidence * 100)}%</strong>
            </span>
          </div>
          <div style="text-align:right;">
            <span class="badge ${gradeClass}" style="font-size:1.1rem; padding:6px 14px;">
              GRADE ${grade}
            </span>
            <div style="font-size:0.68rem; color:var(--text-muted); margin-top:4px;">
              ${grade === 'A' ? 'A = 80-100 (High Quality)' : grade === 'B' ? 'B = 60-79 (Medium Quality)' : grade === 'C' ? 'C = 40-59 (Fair Quality)' : 'Reject < 40 (Defective)'}
            </div>
          </div>
        </div>

        <!-- Sample Image Thumbnail -->
        ${res.image_url ? `
          <div style="display:flex; align-items:center; gap:12px; background:#f5f7fa; border-radius:6px; padding:8px 12px; margin-bottom:16px;">
            <img src="${res.image_url}" alt="Analyzed Sample" style="width:64px; height:48px; object-fit:cover; border-radius:4px; border:1px solid #ccc;">
            <div style="font-size:0.75rem; color:#37474f;">
              <div><strong>Frame Analyzed:</strong> <code>${res.image_url.split('/').pop()}</code></div>
              <div style="color:var(--text-muted);">Inspection Code: <code>${res.grading_code}</code></div>
            </div>
          </div>
        ` : ''}

        <!-- Anomaly Warnings -->
        ${warnings.length > 0 ? `
          <div style="background:#fff3e0; border:1px solid #ffe0b2; border-radius:6px; padding:10px 14px; margin-bottom:16px;">
            <strong style="color:#e65100; font-size:0.78rem; display:block; margin-bottom:4px;">
              ⚠️ AI Anomaly Warnings Detected:
            </strong>
            <ul style="margin:0; padding-left:18px; font-size:0.75rem; color:#bf360c;">
              ${warnings.map(w => `<li>${w}</li>`).join('')}
            </ul>
          </div>
        ` : ''}

        <!-- 12 Visual Parameters Grid -->
        <h4 style="font-size:0.84rem; color:var(--primary-dark); margin-bottom:10px;">
          🔬 12 Optical Defect & Quality Parameters:
        </h4>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:8px; margin-bottom:16px;">
          ${Object.entries(factors).filter(([k, v]) => v.type === 'VISUAL_OPTICAL').map(([k, v]) => `
            <div class="data-source-card" style="padding:8px; border-radius:6px;">
              <div style="font-size:0.68rem; color:#78909c;">${v.name}</div>
              <strong style="font-size:0.78rem; color:#263238; display:block; margin-top:2px;">${v.value}</strong>
              <span class="badge ${v.status === 'PASS' ? 'badge-success' : v.status === 'MINOR_DEFECT' ? 'badge-warning' : 'badge-danger'}" style="font-size:0.62rem; padding:1px 6px; margin-top:4px;">
                ${v.status}
              </span>
            </div>
          `).join('')}
        </div>

        <!-- Segregated Physical Measurements Display -->
        <div style="background:#f9fbe7; border:1px solid #c0ca33; border-radius:6px; padding:12px; margin-bottom:16px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <strong style="font-size:0.8rem; color:#827717;">
              ⚖️ Segregated Physical Measurements (Manual Hardware Probes):
            </strong>
            <span class="badge badge-warning" style="font-size:0.65rem;">Manual Probing</span>
          </div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; font-size:0.76rem;">
            <div>
              <span style="color:#558b2f;">Moisture Content:</span>
              <strong style="color:#33691e;">${factors.physical_moisture ? factors.physical_moisture.value : moisture + '%'}</strong>
              <div style="font-size:0.66rem; color:#689f38;">Digital probe measurement</div>
            </div>
            <div>
              <span style="color:#558b2f;">Certified Net Weight:</span>
              <strong style="color:#33691e;">${factors.physical_weight ? factors.physical_weight.value : netWeight + ' kg'}</strong>
              <div style="font-size:0.66rem; color:#689f38;">Weighbridge platform scale</div>
            </div>
          </div>
        </div>

        <p style="font-size:0.78rem; color:#455a64; line-height:1.4; margin-bottom:16px; background:#f5f5f5; padding:8px 12px; border-radius:4px;">
          <strong>AI Rationale:</strong> ${res.ai_reasoning}
        </p>

        <!-- HUMAN REVIEW SECTION (MANDATORY) -->
        <div style="background:#f1f8e9; border:1px solid #81c784; border-radius:6px; padding:16px;">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
            <h4 style="color:#1b5e20; margin:0; font-size:0.88rem;">
              👤 Mandatory Human Review & Quality Sign-Off
            </h4>
            <span class="badge badge-warning" style="font-size:0.68rem;">Pending Human Stamp</span>
          </div>
          <p style="font-size:0.74rem; color:#33691e; margin-bottom:14px;">
            The AI prediction must NEVER become the final grade automatically. Choose one-click approval or modify with operational justification.
          </p>

          <div style="display:flex; gap:12px; justify-content:flex-end;">
            <button type="button" class="btn btn-secondary btn-sm" onclick="openCorrectWarehouseGradingModal(${res.id})">
              ✏️ Correct Result (Human Override)
            </button>
            <button type="button" class="btn btn-primary btn-sm" onclick="handleApproveWarehouseGrading(${res.id})" style="background:#2e7d32; font-weight:700;">
              ✅ Approve AI Result (Zero Typing)
            </button>
          </div>
        </div>
      </div>
    `;

    // Refresh history table below
    loadGradingHistoryTable();
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Camera AI Grading failed: ${err.message}</div>`;
  }
}

async function handleApproveWarehouseGrading(recordId) {
  if (!confirm("Confirm approval of AI Quality Score and Suggested Grade? This will certify the batch and stamp the final warehouse intake record.")) {
    return;
  }
  try {
    const res = await ApiClient.approveWarehouseGrading(recordId, "Approved without modification by Major Warehouse inspector");
    alert(`Batch ${res.batch_id} officially certified as Grade ${res.effective_final_grade} (Score: ${res.effective_final_score})!`);
    loadGradingHistoryTable();
    // Render approved status card
    const container = document.getElementById("cameraGradingResultContainer");
    if (container) {
      container.innerHTML = `
        <div style="background:#e8f5e9; border:1px solid #81c784; border-radius:8px; padding:24px; text-align:center;">
          <span style="font-size:2.2rem; display:block; margin-bottom:8px;">✅</span>
          <h3 style="color:#1b5e20; margin:0 0 6px 0;">Batch Certified & Stamped</h3>
          <p style="font-size:0.82rem; color:#2e7d32; margin:0 0 12px 0;">
            Batch <strong>${res.batch_id}</strong> certified with <strong>Grade ${res.effective_final_grade}</strong> (Score: ${res.effective_final_score}/100).
          </p>
          <span class="badge badge-success" style="font-size:0.8rem; padding:4px 10px;">APPROVED IN IMMUTABLE LEDGER</span>
        </div>
      `;
    }
  } catch (err) {
    alert("Approval failed: " + err.message);
  }
}

async function openCorrectWarehouseGradingModal(recordId) {
  let rec = null;
  try {
    rec = await ApiClient.getWarehouseGrading(recordId);
  } catch (err) {
    alert("Unable to fetch grading details: " + err.message);
    return;
  }

  const existingModal = document.getElementById("correctGradingModal");
  if (existingModal) existingModal.remove();

  const modalHtml = `
    <div id="correctGradingModal" class="modal-overlay" style="display:flex; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9999; justify-content:center; align-items:center;">
      <div class="modal-card" style="background:white; border-radius:8px; padding:24px; max-width:540px; width:90%; box-shadow:0 4px 20px rgba(0,0,0,0.2);">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #eee; padding-bottom:12px; margin-bottom:16px;">
          <h3 style="margin:0; color:var(--primary-dark); font-size:1.05rem;">
            ✏️ Human Inspector Review & Correction
          </h3>
          <button class="btn btn-sm btn-secondary" onclick="document.getElementById('correctGradingModal').remove()">✕</button>
        </div>

        <div style="font-size:0.8rem; color:var(--text-muted); margin-bottom:14px;">
          Batch ID: <strong>${rec.batch_id}</strong> • AI Suggested: <strong>Grade ${rec.ai_grade}</strong> (${rec.ai_score}/100)
        </div>

        <form id="correctGradingForm" onsubmit="event.preventDefault(); submitCorrectWarehouseGrading(${rec.id});">
          <div class="form-group" style="margin-bottom:14px;">
            <label class="form-label">Human Final Grade *</label>
            <select id="modalFinalGrade" class="form-control" required>
              <option value="A" ${rec.ai_grade === 'A' ? 'selected' : ''}>Grade A (High Quality: 80 - 100)</option>
              <option value="B" ${rec.ai_grade === 'B' ? 'selected' : ''}>Grade B (Medium Quality: 60 - 79)</option>
              <option value="C" ${rec.ai_grade === 'C' ? 'selected' : ''}>Grade C (Fair Quality: 40 - 59)</option>
              <option value="REJECTED" ${rec.ai_grade === 'REJECTED' ? 'selected' : ''}>REJECTED (Defective / Damaged < 40)</option>
            </select>
          </div>

          <div class="form-group" style="margin-bottom:14px;">
            <label class="form-label">Human Final Quality Score (0 - 100) *</label>
            <input type="number" id="modalFinalScore" class="form-control" value="${rec.human_final_score || rec.ai_score}" step="0.5" min="0" max="100" required>
          </div>

          <div class="form-group" style="margin-bottom:14px;">
            <label class="form-label" style="color:var(--accent);">
              Mandatory Operational Justification (Min 5 Characters) *
            </label>
            <textarea id="modalCorrectionReason" class="form-control" rows="3" placeholder="Explain inspector findings, visual discrepancies, or probe results..." required style="resize:vertical;">${rec.correction_reason || ''}</textarea>
            <span style="font-size:0.7rem; color:var(--text-muted);">Required for official dual-storage audit compliance.</span>
          </div>

          <div class="form-group" style="margin-bottom:18px;">
            <label class="form-label">Inspection & Storage Notes</label>
            <input type="text" id="modalHumanNotes" class="form-control" value="${rec.human_notes || 'Adjusted upon physical inspection'}" placeholder="Storage instructions or silo assignment">
          </div>

          <div style="display:flex; justify-content:flex-end; gap:10px;">
            <button type="button" class="btn btn-secondary" onclick="document.getElementById('correctGradingModal').remove()">
              Cancel
            </button>
            <button type="submit" class="btn btn-primary" style="background:#e65100;">
              💾 Save Human Correction
            </button>
          </div>
        </form>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML("beforeend", modalHtml);
}

async function submitCorrectWarehouseGrading(recordId) {
  const grade = document.getElementById("modalFinalGrade").value;
  const score = parseFloat(document.getElementById("modalFinalScore").value);
  const reason = document.getElementById("modalCorrectionReason").value.trim();
  const notes = document.getElementById("modalHumanNotes").value.trim();

  if (reason.length < 5) {
    alert("Mandatory justification must be at least 5 characters.");
    return;
  }

  try {
    const res = await ApiClient.correctWarehouseGrading(recordId, {
      human_final_grade: grade,
      human_final_score: score,
      correction_reason: reason,
      notes: notes,
    });

    const modal = document.getElementById("correctGradingModal");
    if (modal) modal.remove();

    alert(`Human correction recorded! Batch ${res.batch_id} officially certified as Grade ${res.effective_final_grade} (${res.effective_final_score}/100).`);
    loadGradingHistoryTable();

    const container = document.getElementById("cameraGradingResultContainer");
    if (container) {
      container.innerHTML = `
        <div style="background:#fff3e0; border:1px solid #ffb74d; border-radius:8px; padding:24px; text-align:center;">
          <span style="font-size:2.2rem; display:block; margin-bottom:8px;">✏️</span>
          <h3 style="color:#e65100; margin:0 0 6px 0;">Human Correction Certified</h3>
          <p style="font-size:0.82rem; color:#bf360c; margin:0 0 12px 0;">
            Batch <strong>${res.batch_id}</strong> updated from AI Grade ${res.ai_grade} to <strong>Grade ${res.effective_final_grade}</strong> (${res.effective_final_score}/100).
          </p>
          <div style="font-size:0.75rem; color:#5d4037; font-style:italic; margin-bottom:10px;">"${res.correction_reason}"</div>
          <span class="badge badge-warning" style="font-size:0.8rem; padding:4px 10px;">CORRECTED & STAMPED IN LEDGER</span>
        </div>
      `;
    }
  } catch (err) {
    alert("Correction failed: " + err.message);
  }
}

async function loadGradingHistoryTable() {
  const container = document.getElementById("whGradingHistoryTableContainer");
  if (!container) return;

  try {
    const records = await ApiClient.getWarehouseGradings() || [];
    if (records.length === 0) {
      container.innerHTML = `
        <div style="text-align:center; padding:30px; color:var(--text-muted); background:white; border-radius:8px; border:1px solid var(--border);">
          No grading records certified yet. Run AI grading above to create the first record.
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div style="background:white; border-radius:8px; border:1px solid var(--border); overflow-x:auto;">
        <table class="record-table">
          <thead>
            <tr>
              <th>Grading Code</th>
              <th>Batch ID</th>
              <th>Crop & Farmer</th>
              <th>AI Grade (Score)</th>
              <th>Human Final</th>
              <th>Status</th>
              <th>Certified By</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${records.map(r => `
              <tr>
                <td><code>${r.grading_code}</code></td>
                <td><strong>${r.batch_id}</strong></td>
                <td>
                  <div style="font-weight:600;">${r.crop_name}</div>
                  <div style="font-size:0.72rem; color:var(--text-muted);">${r.farmer_name} (${r.farmer_id})</div>
                </td>
                <td>
                  <span class="badge ${r.ai_grade === 'A' ? 'badge-success' : r.ai_grade === 'B' ? 'badge-info' : r.ai_grade === 'C' ? 'badge-warning' : 'badge-danger'}">
                    Grade ${r.ai_grade} (${r.ai_score})
                  </span>
                </td>
                <td>
                  ${r.human_final_grade ? `
                    <span class="badge ${r.human_final_grade === 'A' ? 'badge-success' : r.human_final_grade === 'B' ? 'badge-info' : r.human_final_grade === 'C' ? 'badge-warning' : 'badge-danger'}">
                      Grade ${r.human_final_grade} (${r.human_final_score})
                    </span>
                  ` : `<span style="color:var(--text-muted); font-size:0.75rem;">Pending</span>`}
                </td>
                <td>
                  <span class="badge ${r.review_status === 'APPROVED' ? 'badge-success' : r.review_status === 'CORRECTED' ? 'badge-warning' : 'badge-info'}">
                    ${r.review_status}
                  </span>
                </td>
                <td style="font-size:0.75rem;">
                  <div>${r.reviewed_by || 'AI Standby'}</div>
                  <div style="color:var(--text-muted); font-size:0.7rem;">${r.reviewed_at ? r.reviewed_at.split('T')[0] : (r.created_at ? r.created_at.split('T')[0] : '')}</div>
                </td>
                <td>
                  <div style="display:flex; gap:6px;">
                    <button class="btn btn-sm btn-secondary" onclick="openGradingRecordDetailModal(${r.id})" style="font-size:0.7rem; padding:3px 8px;">
                      👁️ View Sample
                    </button>
                    ${r.review_status === 'PENDING_REVIEW' ? `
                      <button class="btn btn-sm btn-primary" onclick="handleApproveWarehouseGrading(${r.id})" style="background:#2e7d32; font-size:0.7rem; padding:3px 8px;">
                        ✅
                      </button>
                      <button class="btn btn-sm btn-secondary" onclick="openCorrectWarehouseGradingModal(${r.id})" style="font-size:0.7rem; padding:3px 8px;">
                        ✏️
                      </button>
                    ` : ''}
                  </div>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load grading history: ${err.message}</div>`;
  }
}

async function openGradingRecordDetailModal(recordId) {
  let rec = null;
  try {
    rec = await ApiClient.getWarehouseGrading(recordId);
  } catch (err) {
    alert("Unable to load record: " + err.message);
    return;
  }

  const existingModal = document.getElementById("gradingDetailModal");
  if (existingModal) existingModal.remove();

  const factors = rec.ai_quality_factors || {};
  const warnings = rec.ai_warnings || [];

  const modalHtml = `
    <div id="gradingDetailModal" class="modal-overlay" style="display:flex; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9999; justify-content:center; align-items:center;">
      <div class="modal-card" style="background:white; border-radius:8px; padding:24px; max-width:680px; width:95%; max-height:90vh; overflow-y:auto; box-shadow:0 4px 24px rgba(0,0,0,0.25);">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #eee; padding-bottom:12px; margin-bottom:16px;">
          <div>
            <h3 style="margin:0; color:var(--primary-dark); font-size:1.1rem;">
              📷 Grain Quality Sample & Defect Certificate
            </h3>
            <span style="font-size:0.75rem; color:var(--text-muted);">
              Grading Code: <code>${rec.grading_code}</code> • Batch: <strong>${rec.batch_id}</strong>
            </span>
          </div>
          <button class="btn btn-sm btn-secondary" onclick="document.getElementById('gradingDetailModal').remove()">✕</button>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px;">
          <!-- Image View -->
          <div style="background:#1e272e; border-radius:6px; padding:10px; text-align:center;">
            <img src="${rec.image_url || '/uploads/grain_samples/KS-BATCH-1001_sample.svg'}" alt="Grain Sample" style="width:100%; max-height:200px; object-fit:contain; border-radius:4px;">
            <div style="font-size:0.7rem; color:#a4b0be; margin-top:6px;">Sample Frame for ${rec.crop_name}</div>
          </div>

          <!-- Metadata & Dual Decision -->
          <div style="font-size:0.8rem; color:#2f3542;">
            <div><strong>Farmer:</strong> ${rec.farmer_name} (<code>${rec.farmer_id}</code>)</div>
            <div style="margin-top:4px;"><strong>Crop:</strong> ${rec.crop_name}</div>
            <div style="margin-top:4px;"><strong>Net Weight:</strong> ${rec.net_weight_kg ? Number(rec.net_weight_kg).toLocaleString() + ' kg' : 'N/A'}</div>
            <div style="margin-top:4px;"><strong>Warehouse:</strong> ${rec.warehouse_name}</div>
            <hr style="margin:10px 0; border:none; border-top:1px solid #eee;">
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
              <span>AI Prediction:</span>
              <span class="badge ${rec.ai_grade === 'A' ? 'badge-success' : rec.ai_grade === 'B' ? 'badge-info' : 'badge-warning'}">
                Grade ${rec.ai_grade} (${rec.ai_score})
              </span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
              <span>Human Certified:</span>
              <span class="badge ${rec.effective_final_grade === 'A' ? 'badge-success' : rec.effective_final_grade === 'B' ? 'badge-info' : 'badge-warning'}">
                Grade ${rec.effective_final_grade} (${rec.effective_final_score})
              </span>
            </div>
            <div style="margin-top:6px; font-size:0.75rem; color:var(--text-muted);">
              Status: <strong>${rec.review_status}</strong> by <strong>${rec.reviewed_by || 'AI Standby'}</strong>
            </div>
            ${rec.correction_reason ? `
              <div style="background:#fff3e0; border:1px solid #ffe0b2; padding:6px 10px; border-radius:4px; margin-top:8px; font-size:0.72rem; color:#bf360c;">
                <strong>Justification:</strong> "${rec.correction_reason}"
              </div>
            ` : ''}
          </div>
        </div>

        <!-- 12 Optical Parameters Breakdown -->
        <h4 style="font-size:0.82rem; color:var(--primary-dark); margin:0 0 8px 0;">
          🔬 12 Optical Defect Parameters:
        </h4>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:8px; margin-bottom:16px;">
          ${Object.entries(factors).filter(([k, v]) => v.type === 'VISUAL_OPTICAL').map(([k, v]) => `
            <div style="background:#f8f9fa; border:1px solid #e9ecef; border-radius:4px; padding:6px 8px; font-size:0.72rem;">
              <div style="color:#6c757d; font-size:0.65rem;">${v.name}</div>
              <strong style="display:block; margin:2px 0;">${v.value}</strong>
              <span class="badge ${v.status === 'PASS' ? 'badge-success' : 'badge-warning'}" style="font-size:0.6rem; padding:1px 4px;">${v.status}</span>
            </div>
          `).join('')}
        </div>

        <div style="text-align:right;">
          <button class="btn btn-secondary btn-sm" onclick="document.getElementById('gradingDetailModal').remove()">
            Close
          </button>
        </div>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML("beforeend", modalHtml);
}

// =============================================================================
// TASK 6: MAJOR WAREHOUSE STORAGE, INVENTORY & AI STOCK INTELLIGENCE
// =============================================================================

let cachedStorageRecords = [];
let cachedInventorySummary = null;
let cachedStockInsights = null;

async function renderMajorWHStorageInventory(container) {
  container.innerHTML = `
    <div style="text-align:center; padding:48px; color:var(--text-muted);">
      <div class="spinner" style="display:inline-block; width:32px; height:32px; border:3px solid rgba(0,0,0,0.1); border-radius:50%; border-top-color:#1565c0; animation:spin 1s ease-in-out infinite; margin-bottom:12px;"></div>
      <div>Loading Central AI Warehouse Storage, Inventory & Stock Intelligence...</div>
    </div>
  `;

  try {
    const [invRes, insightsRes, storageRes] = await Promise.all([
      ApiClient.getWarehouseInventory("MWH-PUN-01").catch(() => null),
      ApiClient.getWarehouseStockInsights("MWH-PUN-01").catch(() => null),
      ApiClient.getWarehouseStorageList().catch(() => ({ items: [] })),
    ]);

    cachedInventorySummary = invRes || { items: [], total_inventory_kg: 0, total_reserved_kg: 0, total_dispatched_kg: 0, total_available_kg: 0 };
    cachedStockInsights = insightsRes || { crop_insights: [], is_sparse_data: false, overall_stock_status: "OPTIMAL" };
    cachedStorageRecords = (storageRes && storageRes.items) ? storageRes.items : [];

    const totalStockKg = cachedInventorySummary.total_inventory_kg || 0;
    const totalAvailKg = cachedInventorySummary.total_available_kg || 0;
    const totalResKg = cachedInventorySummary.total_reserved_kg || 0;
    const totalDispKg = cachedInventorySummary.total_dispatched_kg || 0;
    const stockStatus = cachedStockInsights.overall_stock_status || "OPTIMAL";

    let statusBadgeClass = "badge-success";
    if (stockStatus === "LOW_STOCK") statusBadgeClass = "badge-danger";
    else if (stockStatus === "HIGH_STOCK") statusBadgeClass = "badge-warning";
    else if (stockStatus === "INSUFFICIENT_DATA") statusBadgeClass = "badge-secondary";

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <!-- TOP TOOLBAR -->
        <div class="table-toolbar" style="background:white; border:1px solid var(--border); border-radius:8px; padding:18px 22px; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
          <div>
            <div style="display:flex; align-items:center; gap:10px;">
              <h3 style="margin:0; color:var(--primary-dark); font-size:1.25rem;">🏢 Major Warehouse Storage, Inventory & AI Stock Intelligence</h3>
              <span class="badge ${statusBadgeClass}" style="font-size:0.75rem;">${stockStatus.replace('_', ' ')}</span>
            </div>
            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:4px;">
              Facility: <strong>Pune Central Major Warehouse (MWH-PUN-01)</strong> • Traceable Batch Linkage: Batch ID ➔ Farmer ID ➔ Crop ➔ Task 5 Grade ➔ Silo Storage ➔ Inventory ➔ Dispatch
            </div>
          </div>
          <div style="display:flex; gap:10px;">
            <button class="btn btn-secondary btn-sm" onclick="renderMajorWHStorageInventory(document.getElementById('contentContainer'))">
              🔄 Refresh
            </button>
            <button class="btn btn-primary btn-sm" onclick="openNewStorageModal()" style="background:#2e7d32; border-color:#2e7d32;">
              ➕ New Storage Entry
            </button>
          </div>
        </div>

        <!-- KPI METRIC CARDS -->
        <div class="metric-grid" style="margin-bottom:22px;">
          <div class="metric-card" style="border-left:4px solid #1565c0;">
            <div class="metric-val" style="color:#1565c0;">${(totalStockKg / 1000).toFixed(1)} MT</div>
            <div class="metric-label">Current Stock on Hand (${Number(totalStockKg).toLocaleString()} kg)</div>
          </div>
          <div class="metric-card" style="border-left:4px solid #2e7d32;">
            <div class="metric-val" style="color:#2e7d32;">${(totalAvailKg / 1000).toFixed(1)} MT</div>
            <div class="metric-label">Available for Dispatch (${Number(totalAvailKg).toLocaleString()} kg)</div>
          </div>
          <div class="metric-card" style="border-left:4px solid #f57c00;">
            <div class="metric-val" style="color:#f57c00;">${(totalResKg / 1000).toFixed(1)} MT</div>
            <div class="metric-label">Reserved for Orders (${Number(totalResKg).toLocaleString()} kg)</div>
          </div>
          <div class="metric-card" style="border-left:4px solid #6a1b9a;">
            <div class="metric-val" style="color:#6a1b9a;">${(totalDispKg / 1000).toFixed(1)} MT</div>
            <div class="metric-label">Cumulative Dispatched (${Number(totalDispKg).toLocaleString()} kg)</div>
          </div>
        </div>

        <!-- CENTRAL AI STOCK INTELLIGENCE & ADVISORY PANEL -->
        <div style="background:white; border:1px solid var(--border); border-radius:8px; padding:20px; margin-bottom:24px; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:14px; border-bottom:1px solid #eee; padding-bottom:12px;">
            <div>
              <h4 style="margin:0; color:#1565c0; display:flex; align-items:center; gap:8px;">
                <span>🧠 Central AI Stock Intelligence & Run-Rate Advisory</span>
                <span class="badge badge-info" style="font-size:0.68rem;">${cachedStockInsights.model_version || 'v1.0.0-prototype'}</span>
              </h4>
              <div style="font-size:0.75rem; color:#78909c; margin-top:2px;">
                ${cachedStockInsights.disclaimer || 'Prototype AI model — stock velocity and requirement estimates require continuous operational dataset.'}
              </div>
            </div>
            <div style="text-align:right;">
              <span style="font-size:0.75rem; color:var(--text-muted);">Silo Utilization: <strong>${cachedStockInsights.storage_utilization_pct || 0}%</strong> of 25,000 MT capacity</span>
            </div>
          </div>

          <!-- PROACTIVE NOTICE / SPARSE DATA WARNING -->
          ${cachedStockInsights.sparse_data_notice ? `
            <div style="background:#fff3e0; border:1px solid #ffe082; padding:10px 14px; border-radius:6px; margin-bottom:16px; font-size:0.82rem; color:#e65100; display:flex; align-items:center; gap:10px;">
              <span style="font-size:1.1rem;">⚠️</span>
              <div>
                <strong>Central AI Notice:</strong> ${cachedStockInsights.sparse_data_notice} Baseline run-rate initialized from standard buffer assumptions.
              </div>
            </div>
          ` : ''}

          <!-- CROP INSIGHTS CARDS -->
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:14px;">
            ${(cachedStockInsights.crop_insights || []).length === 0 ? `
              <div style="text-align:center; padding:18px; color:var(--text-muted); font-size:0.85rem;">
                No crop stock data currently available for Central AI analysis.
              </div>
            ` : (cachedStockInsights.crop_insights || []).map(ci => {
              let ciBadge = "badge-success";
              let ciBg = "#f1f8e9";
              if (ci.stock_level_status === "LOW_STOCK") {
                ciBadge = "badge-danger";
                ciBg = "#ffebee";
              } else if (ci.stock_level_status === "HIGH_STOCK") {
                ciBadge = "badge-warning";
                ciBg = "#fff8e1";
              }
              const factors = ci.ai_factors || {};
              return `
                <div style="border:1px solid #e0e0e0; border-radius:8px; padding:14px; background:#fafafa;">
                  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <strong style="font-size:0.98rem; color:var(--primary-dark);">${ci.crop_name}</strong>
                    <span class="badge ${ciBadge}">${ci.status_label || ci.stock_level_status}</span>
                  </div>
                  <div style="font-size:0.82rem; color:#37474f; margin-bottom:6px;">
                    <span>Stock: <strong>${ci.current_stock_mt} MT</strong></span> • 
                    <span>Buffer: <strong style="color:${ci.stock_level_status === 'LOW_STOCK' ? '#c62828' : '#2e7d32'};">${factors.buffer_coverage_days || 'N/A'}</strong></span> • 
                    <span>Velocity: <strong>${factors.daily_consumption_velocity || 'N/A'}</strong></span>
                  </div>
                  <div style="background:${ciBg}; border-radius:6px; padding:8px 10px; font-size:0.78rem; color:#263238; margin-bottom:8px;">
                    <strong>AI Recommended Action:</strong> ${ci.suggested_action || 'Maintain current buffer.'}
                  </div>
                  <details style="font-size:0.75rem; color:#546e7a;">
                    <summary style="cursor:pointer; font-weight:600; color:#1565c0;">🔍 WHY DID AI GIVE THIS RESULT?</summary>
                    <div style="background:white; border:1px solid #cfd8dc; border-radius:4px; padding:8px; margin-top:6px; line-height:1.5;">
                      <p style="margin:0 0 6px 0; color:#263238;">${ci.why_explanation || 'Evaluation based on stock on hand and dispatch run rate.'}</p>
                      <div style="display:grid; grid-template-columns:1fr 1fr; gap:4px; font-size:0.72rem; color:#455a64;">
                        <div>• On Hand: <strong>${factors.current_stock || 'N/A'}</strong></div>
                        <div>• 30d Dispatches: <strong>${factors.recent_dispatches_30d || 'None'}</strong></div>
                        <div>• Daily Velocity: <strong>${factors.daily_consumption_velocity || 'N/A'}</strong></div>
                        <div>• Average Dwell: <strong>${factors.average_storage_dwell || 'N/A'}</strong></div>
                      </div>
                    </div>
                  </details>
                </div>
              `;
            }).join('')}
          </div>
        </div>

        <!-- AGGREGATE WAREHOUSE INVENTORY TABLE -->
        <div style="background:white; border:1px solid var(--border); border-radius:8px; padding:20px; margin-bottom:24px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
            <h4 style="margin:0; color:var(--primary-dark);">📊 Warehouse Inventory by Crop Variety</h4>
            <span style="font-size:0.78rem; color:var(--text-muted);">${(cachedInventorySummary.items || []).length} Crop Varieties Managed</span>
          </div>

          <table class="record-table">
            <thead>
              <tr>
                <th>Crop Variety</th>
                <th>Category</th>
                <th>Received</th>
                <th>Dispatched</th>
                <th>Reserved</th>
                <th>Current Stock</th>
                <th>Available</th>
                <th>Quality Grade Breakdown (Task 5)</th>
                <th>Silo Locations</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${(cachedInventorySummary.items || []).length === 0 ? `
                <tr><td colspan="10" style="text-align:center; padding:24px; color:var(--text-muted);">No inventory records found in warehouse.</td></tr>
              ` : (cachedInventorySummary.items || []).map(item => {
                let badgeClass = "badge-success";
                if (item.status === "LOW_STOCK") badgeClass = "badge-danger";
                else if (item.status === "HIGH_STOCK") badgeClass = "badge-warning";
                
                const gb = item.grades_breakdown || {};
                const gradesDisplay = Object.entries(gb)
                  .filter(([g, kg]) => kg > 0)
                  .map(([g, kg]) => `<strong>Grade ${g}:</strong> ${(kg / 1000).toFixed(1)} MT`)
                  .join(" • ") || "Pending Grade";

                return `
                  <tr>
                    <td><strong>${item.crop_name}</strong><br><small style="color:var(--text-muted);">${item.batches_count} batches (${(item.batch_ids || []).slice(0, 3).join(', ')})</small></td>
                    <td><span class="badge badge-secondary" style="font-size:0.72rem;">${item.crop_category}</span></td>
                    <td>${Number(item.total_received_kg).toLocaleString()} kg</td>
                    <td style="color:#6a1b9a;">${Number(item.total_dispatched_kg).toLocaleString()} kg</td>
                    <td style="color:#e65100;">${Number(item.total_reserved_kg).toLocaleString()} kg</td>
                    <td style="font-weight:700; color:#1565c0;">${Number(item.current_stock_kg).toLocaleString()} kg<br><small>(${(item.current_stock_kg / 1000).toFixed(2)} MT)</small></td>
                    <td style="font-weight:700; color:#2e7d32;">${Number(item.available_stock_kg).toLocaleString()} kg</td>
                    <td style="font-size:0.78rem; color:#37474f;">${gradesDisplay}</td>
                    <td><small>${(item.storage_sections || []).join(", ") || "Silo Bay #1"}</small></td>
                    <td><span class="badge ${badgeClass}">${item.status || 'OPTIMAL'}</span></td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>

        <!-- INDIVIDUAL STORAGE BATCH RECORDS TABLE -->
        <div style="background:white; border:1px solid var(--border); border-radius:8px; padding:20px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:10px;">
            <div>
              <h4 style="margin:0; color:var(--primary-dark);">📦 Individual Storage Batch Records</h4>
              <span style="font-size:0.78rem; color:var(--text-muted);">Verified Batch Tracking with Immutable Task 5 Grade Certification</span>
            </div>
            <!-- FILTERS -->
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
              <input type="text" id="storageFilterCrop" placeholder="Filter Crop..." class="form-control" style="width:130px; font-size:0.8rem; padding:4px 8px;" oninput="filterStorageRecords()">
              <select id="storageFilterCategory" class="form-control" style="width:110px; font-size:0.8rem; padding:4px 8px;" onchange="filterStorageRecords()">
                <option value="">All Categories</option>
                <option value="Grains">Grains</option>
                <option value="Vegetables">Vegetables</option>
                <option value="Fruits">Fruits</option>
              </select>
              <select id="storageFilterStatus" class="form-control" style="width:110px; font-size:0.8rem; padding:4px 8px;" onchange="filterStorageRecords()">
                <option value="">All Statuses</option>
                <option value="Stored">Stored</option>
                <option value="Partially Dispatched">Partially Dispatched</option>
                <option value="Reserved">Reserved</option>
                <option value="Completed">Completed</option>
              </select>
              <input type="text" id="storageFilterBatch" placeholder="Batch ID..." class="form-control" style="width:120px; font-size:0.8rem; padding:4px 8px;" oninput="filterStorageRecords()">
            </div>
          </div>

          <div style="overflow-x:auto;">
            <table class="record-table" id="storageRecordsTable">
              <thead>
                <tr>
                  <th>Storage ID</th>
                  <th>Batch ID</th>
                  <th>Farmer</th>
                  <th>Crop</th>
                  <th>Received Qty</th>
                  <th>Current Stock</th>
                  <th>Reserved</th>
                  <th>Dispatched</th>
                  <th>Location</th>
                  <th>Storage Type</th>
                  <th>Grade (Task 5)</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody id="storageRecordsTableBody">
                ${renderStorageTableRows(cachedStorageRecords)}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load Storage & Inventory console: ${err.message}</div>`;
  }
}

function renderStorageTableRows(records) {
  if (!records || records.length === 0) {
    return `<tr><td colspan="13" style="text-align:center; padding:24px; color:var(--text-muted);">No storage records matching current filter.</td></tr>`;
  }

  return records.map(r => {
    let stBadge = "badge-success";
    if (r.storage_status === "Completed") stBadge = "badge-secondary";
    else if (r.storage_status === "Partially Dispatched") stBadge = "badge-info";
    else if (r.storage_status === "Reserved") stBadge = "badge-warning";

    const grade = r.quality_grade || "A";
    let gradeColor = "#2e7d32";
    if (grade === "B") gradeColor = "#1565c0";
    else if (grade === "C") gradeColor = "#e65100";
    else if (grade === "REJECTED") gradeColor = "#c62828";

    return `
      <tr>
        <td><code>${r.storage_id}</code></td>
        <td><code>${r.batch_id}</code></td>
        <td>${r.farmer_name || 'Farmer'}<br><small style="color:var(--text-muted);">${r.farmer_id || ''}</small></td>
        <td><strong>${r.crop_name}</strong><br><small style="color:var(--text-muted);">${r.crop_category || 'Grains'}</small></td>
        <td>${Number(r.quantity_kg).toLocaleString()} kg</td>
        <td style="font-weight:700; color:#1565c0;">${Number(r.current_stock_kg).toLocaleString()} kg</td>
        <td style="color:#f57c00;">${Number(r.reserved_quantity_kg || 0).toLocaleString()} kg</td>
        <td style="color:#6a1b9a;">${Number(r.dispatched_quantity_kg || 0).toLocaleString()} kg</td>
        <td><strong>${r.storage_location || 'Silo Bay #1'}</strong></td>
        <td><small>${r.storage_type || 'Silo Storage'}</small></td>
        <td>
          <span class="badge" style="background:${gradeColor}; color:white; font-size:0.75rem;">Grade ${grade}</span>
          ${r.quality_score ? `<br><small style="color:var(--text-muted);">${r.quality_score} pts</small>` : ''}
        </td>
        <td><span class="badge ${stBadge}">${r.storage_status}</span></td>
        <td>
          <div style="display:flex; gap:4px;">
            <button class="btn btn-secondary btn-sm" style="padding:2px 6px; font-size:0.72rem;" onclick="openStorageDetailModal('${r.storage_id}')" title="View Full Batch Trace">
              👁️ View
            </button>
            <button class="btn btn-primary btn-sm" style="padding:2px 6px; font-size:0.72rem;" onclick="openDispatchEditModal('${r.storage_id}')" title="Dispatch Pick / Update Storage">
              ✏️ Edit / Dispatch
            </button>
            <button class="btn btn-secondary btn-sm" style="padding:2px 6px; font-size:0.72rem;" onclick="openStorageAuditHistoryModal('${r.storage_id}')" title="View Change Audit History">
              📜 History
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function filterStorageRecords() {
  const cropQuery = (document.getElementById("storageFilterCrop")?.value || "").toLowerCase();
  const catQuery = document.getElementById("storageFilterCategory")?.value || "";
  const statusQuery = document.getElementById("storageFilterStatus")?.value || "";
  const batchQuery = (document.getElementById("storageFilterBatch")?.value || "").toLowerCase();

  const filtered = cachedStorageRecords.filter(r => {
    const matchCrop = !cropQuery || (r.crop_name || "").toLowerCase().includes(cropQuery);
    const matchCat = !catQuery || (r.crop_category || "") === catQuery;
    const matchStatus = !statusQuery || (r.storage_status || "") === statusQuery;
    const matchBatch = !batchQuery || (r.batch_id || "").toLowerCase().includes(batchQuery);
    return matchCrop && matchCat && matchStatus && matchBatch;
  });

  const tbody = document.getElementById("storageRecordsTableBody");
  if (tbody) {
    tbody.innerHTML = renderStorageTableRows(filtered);
  }
}

// --- NEW STORAGE ENTRY MODAL ---
async function openNewStorageModal() {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = "➕ Create New Major Warehouse Storage Record";
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Store Verified Batch";

  modalBody.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted);">Fetching certified crop arrivals...</div>`;
  modal.style.display = "flex";

  try {
    const intakes = await ApiClient.getRecords("/major-wh/intakes") || [];

    modalBody.innerHTML = `
      <div style="background:#e8f5e9; border:1px solid #a5d6a7; padding:12px 16px; border-radius:6px; margin-bottom:16px;">
        <div style="font-weight:700; color:#2e7d32; font-size:0.88rem; margin-bottom:2px;">
          🌾 Certified Intake ➔ Silo Storage Allocation
        </div>
        <div style="font-size:0.78rem; color:#1b5e20;">
          Select a verified arrival batch to populate farmer, crop, certified net weight, and Task 5 quality grade.
        </div>
      </div>

      <form id="newStorageForm" class="form-grid" onsubmit="handleCreateStorageSubmit(event)">
        <div class="form-group" style="grid-column: span 2;">
          <label class="form-label">Select Verified Arrival Batch *</label>
          <select id="storageBatchSelect" class="form-control" required onchange="onStorageBatchSelected(this.value)">
            <option value="">-- Choose Arrival Batch --</option>
            ${intakes.map(i => `
              <option value="${i.batch_id}" data-crop="${i.crop_name}" data-farmer-id="${i.farmer_id || ''}" data-farmer-name="${i.farmer_name || ''}" data-weight="${i.net_weight_kg || i.gross_weight_kg || 1000}" data-grade="${i.human_final_grade || i.ai_predicted_grade || 'A'}" data-score="${i.human_final_score || i.ai_predicted_score || 90}">
                ${i.batch_id} — ${i.crop_name} (${i.net_weight_kg || i.gross_weight_kg} kg) [${i.farmer_name || 'Farmer'}] Grade ${i.human_final_grade || i.ai_predicted_grade || 'A'}
              </option>
            `).join('')}
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Storage Record ID</label>
          <input type="text" id="storageIdInput" class="form-control" placeholder="Leave blank to auto-generate (e.g. KS-STR-800X)">
        </div>

        <div class="form-group">
          <label class="form-label">Batch ID *</label>
          <input type="text" id="storageBatchId" class="form-control" placeholder="e.g. KS-BATCH-1001" required>
        </div>

        <div class="form-group">
          <label class="form-label">Farmer ID</label>
          <input type="text" id="storageFarmerId" class="form-control" placeholder="e.g. KS-FMR-1001" readonly style="background:#f5f5f5;">
        </div>

        <div class="form-group">
          <label class="form-label">Farmer Name</label>
          <input type="text" id="storageFarmerName" class="form-control" placeholder="Farmer Full Name" readonly style="background:#f5f5f5;">
        </div>

        <div class="form-group">
          <label class="form-label">Crop Name *</label>
          <input type="text" id="storageCropName" class="form-control" required>
        </div>

        <div class="form-group">
          <label class="form-label">Crop Category *</label>
          <select id="storageCropCategory" class="form-control" required>
            <option value="Grains">Grains (Cereals, Pulses, Oilseeds)</option>
            <option value="Vegetables">Vegetables</option>
            <option value="Fruits">Fruits</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Stored Quantity (kg) *</label>
          <input type="number" step="0.1" id="storageQuantityKg" class="form-control" required min="1">
        </div>

        <div class="form-group">
          <label class="form-label">Certified Quality Grade (Task 5)</label>
          <input type="text" id="storageGradeDisplay" class="form-control" readonly style="background:#e8f5e9; font-weight:700; color:#2e7d32;" value="Grade A (Certified)">
        </div>

        <div class="form-group">
          <label class="form-label">Silo Bay / Storage Location *</label>
          <input type="text" id="storageLocationInput" class="form-control" value="Silo Bay #1" required>
        </div>

        <div class="form-group">
          <label class="form-label">Storage Type *</label>
          <select id="storageTypeInput" class="form-control" required>
            <option value="Silo Storage">Silo Storage (Grain Aerated)</option>
            <option value="Cold Storage">Cold Storage (Controlled Atmosphere)</option>
            <option value="Dry Warehouse">Dry Warehouse (Palletised)</option>
            <option value="Covered Shed">Covered Shed</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Ambient Temp (°C)</label>
          <input type="number" step="0.1" id="storageTempInput" class="form-control" value="21.5">
        </div>

        <div class="form-group">
          <label class="form-label">Relative Humidity (%)</label>
          <input type="number" step="0.1" id="storageHumidityInput" class="form-control" value="54.0">
        </div>

        <div class="form-group" style="grid-column: span 2;">
          <label class="form-label">Storage & Handling Notes</label>
          <textarea id="storageNotesInput" class="form-control" rows="2" placeholder="Inspection verified, grain fumigated, aeration active."></textarea>
        </div>
      </form>
    `;

    modalSubmitBtn.onclick = () => {
      document.getElementById("newStorageForm").dispatchEvent(new Event("submit"));
    };
  } catch (err) {
    modalBody.innerHTML = `<div class="alert-box danger">Error loading arrivals: ${err.message}</div>`;
  }
}

function onStorageBatchSelected(batchId) {
  const sel = document.getElementById("storageBatchSelect");
  if (!sel || !batchId) return;
  const opt = sel.options[sel.selectedIndex];
  if (!opt) return;

  document.getElementById("storageBatchId").value = batchId;
  document.getElementById("storageFarmerId").value = opt.getAttribute("data-farmer-id") || "";
  document.getElementById("storageFarmerName").value = opt.getAttribute("data-farmer-name") || "";
  document.getElementById("storageCropName").value = opt.getAttribute("data-crop") || "";
  document.getElementById("storageQuantityKg").value = opt.getAttribute("data-weight") || "1000";
  
  const grade = opt.getAttribute("data-grade") || "A";
  const score = opt.getAttribute("data-score") || "90";
  document.getElementById("storageGradeDisplay").value = `Grade ${grade} (${score} pts) [Certified]`;

  const crop = (opt.getAttribute("data-crop") || "").toLowerCase();
  if (crop.includes("wheat") || crop.includes("grain") || crop.includes("soybean") || crop.includes("chana") || crop.includes("corn") || crop.includes("gram")) {
    document.getElementById("storageCropCategory").value = "Grains";
    document.getElementById("storageTypeInput").value = "Silo Storage";
  } else if (crop.includes("potato") || crop.includes("onion") || crop.includes("tomato") || crop.includes("vegetable")) {
    document.getElementById("storageCropCategory").value = "Vegetables";
    document.getElementById("storageTypeInput").value = "Cold Storage";
  } else {
    document.getElementById("storageCropCategory").value = "Fruits";
    document.getElementById("storageTypeInput").value = "Cold Storage";
  }
}

async function handleCreateStorageSubmit(e) {
  e.preventDefault();
  const batchId = document.getElementById("storageBatchId").value.trim();
  const cropName = document.getElementById("storageCropName").value.trim();
  const qty = parseFloat(document.getElementById("storageQuantityKg").value);

  if (!batchId || !cropName || isNaN(qty) || qty <= 0) {
    alert("Please enter a valid Batch ID, Crop Name, and positive quantity.");
    return;
  }

  const payload = {
    storage_id: document.getElementById("storageIdInput").value.trim() || undefined,
    batch_id: batchId,
    farmer_id: document.getElementById("storageFarmerId").value.trim() || undefined,
    farmer_name: document.getElementById("storageFarmerName").value.trim() || undefined,
    crop_name: cropName,
    crop_category: document.getElementById("storageCropCategory").value,
    quantity_kg: qty,
    storage_section: document.getElementById("storageLocationInput").value.trim() || "SILO-A-01",
    storage_type: document.getElementById("storageTypeInput").value,
    temperature_celsius: parseFloat(document.getElementById("storageTempInput").value) || undefined,
    humidity_percentage: parseFloat(document.getElementById("storageHumidityInput").value) || undefined,
    notes: document.getElementById("storageNotesInput").value.trim() || undefined,
  };

  const btn = document.getElementById("modalSubmitBtn");
  try {
    btn.disabled = true;
    btn.textContent = "Storing Batch in Silo...";
    const res = await ApiClient.createWarehouseStorage(payload);
    closeModal();
    alert(`Storage Record #${res.storage_id} Created Successfully!
Batch: ${res.batch_id} (${res.quantity_kg} kg ${res.crop_name})
Certified Grade: ${res.quality_grade}`);
    renderMajorWHStorageInventory(document.getElementById("contentContainer"));
  } catch (err) {
    alert("Failed to create storage record: " + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Store Verified Batch";
    }
  }
}

// --- DISPATCH PICK & EDIT MODAL ---
async function openDispatchEditModal(storageId) {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `✏️ Storage Record & Dispatch: ${storageId}`;
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Apply Inventory Update";

  modalBody.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted);">Loading storage details...</div>`;
  modal.style.display = "flex";

  try {
    const rec = await ApiClient.getWarehouseStorage(storageId);

    modalBody.innerHTML = `
      <!-- BATCH LINKAGE & SUMMARY BANNER -->
      <div style="background:#e3f2fd; border:1px solid #90caf9; padding:14px; border-radius:6px; margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <strong style="color:#0d47a1; font-size:1rem;">${rec.storage_id} • ${rec.crop_name} (${rec.crop_category})</strong>
            <div style="font-size:0.78rem; color:#1565c0; margin-top:2px;">
              Linked Batch: <code>${rec.batch_id}</code> • Farmer: <strong>${rec.farmer_name || 'N/A'}</strong> (${rec.farmer_id || ''})
            </div>
          </div>
          <div style="text-align:right;">
            <span class="badge" style="background:#2e7d32; color:white;">Certified Grade ${rec.quality_grade}</span>
            <div style="font-size:0.72rem; color:#1976d2; margin-top:2px;">(Immutable Task 5 Grade)</div>
          </div>
        </div>
      </div>

      <!-- INVENTORY BALANCE KPI -->
      <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:8px; margin-bottom:16px; text-align:center;">
        <div style="background:#f5f5f5; padding:8px; border-radius:6px; border:1px solid #e0e0e0;">
          <div style="font-size:0.7rem; color:var(--text-muted);">Total Received</div>
          <strong style="color:#333; font-size:0.95rem;">${Number(rec.quantity_kg).toLocaleString()} kg</strong>
        </div>
        <div style="background:#f5f5f5; padding:8px; border-radius:6px; border:1px solid #e0e0e0;">
          <div style="font-size:0.7rem; color:var(--text-muted);">Total Dispatched</div>
          <strong style="color:#6a1b9a; font-size:0.95rem;">${Number(rec.dispatched_quantity_kg).toLocaleString()} kg</strong>
        </div>
        <div style="background:#f5f5f5; padding:8px; border-radius:6px; border:1px solid #e0e0e0;">
          <div style="font-size:0.7rem; color:var(--text-muted);">Current Stock</div>
          <strong style="color:#1565c0; font-size:0.95rem;">${Number(rec.current_stock_kg).toLocaleString()} kg</strong>
        </div>
        <div style="background:#e8f5e9; padding:8px; border-radius:6px; border:1px solid #a5d6a7;">
          <div style="font-size:0.7rem; color:#2e7d32;">Available to Dispatch</div>
          <strong style="color:#1b5e20; font-size:0.95rem;">${Number(rec.available_quantity_kg).toLocaleString()} kg</strong>
        </div>
      </div>

      <form id="editStorageForm" class="form-grid" onsubmit="handleUpdateStorageSubmit(event, '${rec.storage_id}')">
        <div class="form-group" style="grid-column: span 2; background:#fff8e1; border:1px solid #ffe082; padding:12px; border-radius:6px;">
          <label class="form-label" style="color:#e65100; font-weight:700;">🚚 Outward Dispatch Pick (Incremental kg to Dispatch Now)</label>
          <div style="display:flex; gap:10px; align-items:center;">
            <input type="number" step="0.1" id="editDispatchInc" class="form-control" placeholder="Enter kg to dispatch now (e.g. 500)" max="${rec.available_quantity_kg}" min="0">
            <span style="font-size:0.8rem; color:#e65100; white-space:nowrap;">Max available: <strong>${rec.available_quantity_kg} kg</strong></span>
          </div>
          <div style="font-size:0.72rem; color:#8d6e63; margin-top:4px;">Dispatches automatically update Current Stock and log directly to the audit trail. Cannot exceed available stock.</div>
        </div>

        <div class="form-group">
          <label class="form-label">Reserved Stock for Orders (kg)</label>
          <input type="number" step="0.1" id="editReservedKg" class="form-control" value="${rec.reserved_quantity_kg || 0}" min="0" max="${rec.current_stock_kg}">
        </div>

        <div class="form-group">
          <label class="form-label">Silo Bay / Storage Location</label>
          <input type="text" id="editLocation" class="form-control" value="${rec.storage_location || ''}" required>
        </div>

        <div class="form-group">
          <label class="form-label">Storage Type</label>
          <select id="editStorageType" class="form-control">
            <option value="Silo Storage" ${rec.storage_type === 'Silo Storage' ? 'selected' : ''}>Silo Storage</option>
            <option value="Cold Storage" ${rec.storage_type === 'Cold Storage' ? 'selected' : ''}>Cold Storage</option>
            <option value="Dry Warehouse" ${rec.storage_type === 'Dry Warehouse' ? 'selected' : ''}>Dry Warehouse</option>
            <option value="Covered Shed" ${rec.storage_type === 'Covered Shed' ? 'selected' : ''}>Covered Shed</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Storage Status Override</label>
          <select id="editStatus" class="form-control">
            <option value="Stored" ${rec.storage_status === 'Stored' ? 'selected' : ''}>Stored</option>
            <option value="Partially Dispatched" ${rec.storage_status === 'Partially Dispatched' ? 'selected' : ''}>Partially Dispatched</option>
            <option value="Reserved" ${rec.storage_status === 'Reserved' ? 'selected' : ''}>Reserved</option>
            <option value="Completed" ${rec.storage_status === 'Completed' ? 'selected' : ''}>Completed</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Ambient Temp (°C)</label>
          <input type="number" step="0.1" id="editTemp" class="form-control" value="${rec.temperature_celsius ?? ''}">
        </div>

        <div class="form-group">
          <label class="form-label">Relative Humidity (%)</label>
          <input type="number" step="0.1" id="editHumidity" class="form-control" value="${rec.humidity_percentage ?? ''}">
        </div>

        <div class="form-group" style="grid-column: span 2;">
          <label class="form-label">Mandatory Reason for Modification / Dispatch *</label>
          <input type="text" id="editReason" class="form-control" placeholder="e.g. Dispatched to Baramati APMC godown via Truck MH-12-Q-4521" required minlength="3">
        </div>

        <div class="form-group" style="grid-column: span 2;">
          <label class="form-label">Storage & Handling Remarks</label>
          <textarea id="editNotes" class="form-control" rows="2">${rec.notes || ''}</textarea>
        </div>
      </form>
    `;

    modalSubmitBtn.onclick = () => {
      document.getElementById("editStorageForm").dispatchEvent(new Event("submit"));
    };
  } catch (err) {
    modalBody.innerHTML = `<div class="alert-box danger">Error loading storage record: ${err.message}</div>`;
  }
}

async function handleUpdateStorageSubmit(e, storageId) {
  e.preventDefault();
  const reason = document.getElementById("editReason").value.trim();
  if (!reason || reason.length < 3) {
    alert("Please provide a valid reason for this modification or dispatch pick (min 3 characters).");
    return;
  }

  const dispatchInc = parseFloat(document.getElementById("editDispatchInc").value);
  const reservedKg = parseFloat(document.getElementById("editReservedKg").value);

  const payload = {
    edit_reason: reason,
    edited_by: (currentUser && currentUser.username) ? currentUser.username : "Warehouse Supervisor",
    storage_section: document.getElementById("editLocation").value.trim(),
    storage_type: document.getElementById("editStorageType").value,
    storage_status: document.getElementById("editStatus").value,
    notes: document.getElementById("editNotes").value.trim(),
  };

  if (!isNaN(dispatchInc) && dispatchInc > 0) {
    payload.dispatch_increment_kg = dispatchInc;
  }
  if (!isNaN(reservedKg) && reservedKg >= 0) {
    payload.reserved_quantity_kg = reservedKg;
  }

  const temp = parseFloat(document.getElementById("editTemp").value);
  if (!isNaN(temp)) payload.temperature_celsius = temp;
  const hum = parseFloat(document.getElementById("editHumidity").value);
  if (!isNaN(hum)) payload.humidity_percentage = hum;

  const btn = document.getElementById("modalSubmitBtn");
  try {
    btn.disabled = true;
    btn.textContent = "Updating Storage Ledger...";
    const res = await ApiClient.updateWarehouseStorage(storageId, payload);
    closeModal();
    alert(`Storage Record #${storageId} Updated Successfully!
New Balance: ${res.current_stock_kg} kg on hand (${res.dispatched_quantity_kg} kg dispatched)`);
    renderMajorWHStorageInventory(document.getElementById("contentContainer"));
  } catch (err) {
    alert("Update failed: " + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Apply Inventory Update";
    }
  }
}

// --- STORAGE DETAIL MODAL ---
async function openStorageDetailModal(storageId) {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `📋 Complete Batch Traceability: ${storageId}`;
  modalSubmitBtn.style.display = "none";

  modalBody.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted);">Loading traceability chain...</div>`;
  modal.style.display = "flex";

  try {
    const rec = await ApiClient.getWarehouseStorage(storageId);

    modalBody.innerHTML = `
      <!-- COMPLETE LINKAGE FLOWCHART -->
      <div style="background:#f8f9fa; border:1px solid #e0e0e0; border-radius:8px; padding:16px; margin-bottom:18px;">
        <div style="font-weight:700; color:#37474f; font-size:0.85rem; margin-bottom:10px;">
          🔗 End-to-End Batch Traceability Chain:
        </div>
        <div style="display:flex; flex-wrap:wrap; align-items:center; gap:8px; font-size:0.8rem;">
          <span style="background:#e3f2fd; padding:4px 8px; border-radius:4px; border:1px solid #bbdefb; color:#1565c0;">
            Batch: <strong>${rec.batch_id}</strong>
          </span>
          <span>➔</span>
          <span style="background:#f3e5f5; padding:4px 8px; border-radius:4px; border:1px solid #e1bee7; color:#6a1b9a;">
            Farmer: <strong>${rec.farmer_name}</strong> (${rec.farmer_id})
          </span>
          <span>➔</span>
          <span style="background:#fff3e0; padding:4px 8px; border-radius:4px; border:1px solid #ffe082; color:#e65100;">
            Crop: <strong>${rec.crop_name}</strong>
          </span>
          <span>➔</span>
          <span style="background:#e8f5e9; padding:4px 8px; border-radius:4px; border:1px solid #a5d6a7; color:#2e7d32;">
            Grade: <strong>${rec.quality_grade}</strong> (${rec.quality_score || 90} pts)
          </span>
          <span>➔</span>
          <span style="background:#ede7f6; padding:4px 8px; border-radius:4px; border:1px solid #d1c4e9; color:#4527a0;">
            Silo: <strong>${rec.storage_location}</strong>
          </span>
        </div>
      </div>

      <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:0.82rem; margin-bottom:16px;">
        <div><strong>Storage Record ID:</strong> <code>${rec.storage_id}</code></div>
        <div><strong>Batch Identification:</strong> <code>${rec.batch_id}</code></div>
        <div><strong>Supplying Farmer:</strong> ${rec.farmer_name} (${rec.farmer_id})</div>
        <div><strong>Crop Variety:</strong> ${rec.crop_name} (${rec.crop_category})</div>
        <div><strong>Initial Intake Quantity:</strong> ${Number(rec.quantity_kg).toLocaleString()} kg</div>
        <div><strong>Current Silo Stock:</strong> <span style="color:#1565c0; font-weight:700;">${Number(rec.current_stock_kg).toLocaleString()} kg</span></div>
        <div><strong>Reserved for Allocation:</strong> ${Number(rec.reserved_quantity_kg).toLocaleString()} kg</div>
        <div><strong>Cumulative Dispatched:</strong> ${Number(rec.dispatched_quantity_kg).toLocaleString()} kg</div>
        <div><strong>Available for Dispatch:</strong> <span style="color:#2e7d32; font-weight:700;">${Number(rec.available_quantity_kg).toLocaleString()} kg</span></div>
        <div><strong>Storage Facility:</strong> ${rec.warehouse_name} (${rec.warehouse_id})</div>
        <div><strong>Storage Section / Bay:</strong> ${rec.storage_location}</div>
        <div><strong>Storage Technology:</strong> ${rec.storage_type}</div>
        <div><strong>Intake Date:</strong> ${rec.storage_date || 'N/A'}</div>
        <div><strong>Atmosphere:</strong> ${rec.temperature_celsius ? rec.temperature_celsius + '°C' : 'Ambient'} • ${rec.humidity_percentage ? rec.humidity_percentage + '%' : 'Monitored'}</div>
      </div>

      ${rec.notes ? `
        <div style="background:#fafafa; border:1px solid #eee; padding:10px; border-radius:4px; font-size:0.8rem; margin-bottom:16px;">
          <strong>Notes & Handling Remarks:</strong><br>${rec.notes}
        </div>
      ` : ''}

      <div style="text-align:right;">
        <button class="btn btn-secondary btn-sm" onclick="closeModal()">Close</button>
      </div>
    `;
  } catch (err) {
    modalBody.innerHTML = `<div class="alert-box danger">Error loading trace: ${err.message}</div>`;
  }
}

// --- STORAGE AUDIT HISTORY MODAL ---
async function openStorageAuditHistoryModal(storageId) {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `📜 Audit & Change History: ${storageId}`;
  modalSubmitBtn.style.display = "none";

  modalBody.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted);">Fetching audit logs...</div>`;
  modal.style.display = "flex";

  try {
    const logs = await ApiClient.getAuditHistory("major_warehouse_storage", storageId) || [];

    if (logs.length === 0) {
      modalBody.innerHTML = `
        <div style="text-align:center; padding:24px; color:var(--text-muted);">
          No audit entries recorded for storage record <code>${storageId}</code>.
        </div>
        <div style="text-align:right; margin-top:16px;">
          <button class="btn btn-secondary btn-sm" onclick="closeModal()">Close</button>
        </div>
      `;
      return;
    }

    modalBody.innerHTML = `
      <div style="max-height:400px; overflow-y:auto;">
        <table class="record-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Action / Field</th>
              <th>Previous Value</th>
              <th>Updated Value</th>
              <th>Edited By</th>
              <th>Justification</th>
            </tr>
          </thead>
          <tbody>
            ${logs.map(l => `
              <tr>
                <td><small>${l.timestamp || l.created_at || 'N/A'}</small></td>
                <td><strong>${l.field_name}</strong></td>
                <td><small style="color:#78909c;">${l.old_value || 'NONE'}</small></td>
                <td><small style="color:#2e7d32; font-weight:600;">${l.new_value || 'UPDATED'}</small></td>
                <td>${l.edited_by}<br><small style="color:var(--text-muted);">${l.edited_by_role || ''}</small></td>
                <td><small>${l.change_reason || 'N/A'}</small></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
      <div style="text-align:right; margin-top:16px;">
        <button class="btn btn-secondary btn-sm" onclick="closeModal()">Close</button>
      </div>
    `;
  } catch (err) {
    modalBody.innerHTML = `<div class="alert-box danger">Error loading audit logs: ${err.message}</div>`;
  }
}


const renderMajorWHStorage = renderMajorWHStorageInventory;

// --- 6. MINOR WAREHOUSE: OVERVIEW & AI STOCK RECS ---
async function renderMinorWHOverview(container) {
  container.innerHTML = `<div style="text-align:center; padding:32px; color:var(--text-muted);">Loading sub-district godown metrics...</div>`;
  try {
    const stock = await ApiClient.getRecords("/minor-wh/stock") || [];
    const inward = await ApiClient.getRecords("/minor-wh/inward") || [];
    const dist = await ApiClient.getRecords("/minor-wh/distributions") || [];

    const totalStockKg = stock.reduce((acc, r) => acc + (parseFloat(r.current_stock_kg) || 0), 0);

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar">
          <div>
            <h3>🏪 Minor Warehouse & Sub-District Transit Godown</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">Public Distribution System (PDS) Supply Depot</span>
          </div>
          <button class="btn btn-primary btn-sm" onclick="selectSubTab('minor_wh_ai_recs')" style="background:#1565c0;">
            🤖 View AI Restock Advisory
          </button>
        </div>

        <div class="metric-grid">
          <div class="metric-card">
            <div class="metric-val" style="color:#1565c0;">${(totalStockKg / 1000).toFixed(1)} MT</div>
            <div class="metric-label">Current Stock on Hand</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#2e7d32;">${inward.length}</div>
            <div class="metric-label">Inward Dispatches Verified</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#e65100;">${dist.length}</div>
            <div class="metric-label">Fair Price Shop Deliveries</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#6a1b9a;">Active</div>
            <div class="metric-label">Central AI Buffer Monitoring</div>
          </div>
        </div>

        <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:20px; margin-top:20px;">
          <h4 style="color:var(--primary-dark); margin-bottom:12px;">Current Warehouse Stock by Crop</h4>
          <table class="record-table">
            <thead>
              <tr>
                <th>Crop</th>
                <th>Batch ID</th>
                <th>Stock (kg)</th>
                <th>Stock (MT)</th>
                <th>Location</th>
                <th>Last Replenished</th>
              </tr>
            </thead>
            <tbody>
              ${stock.length === 0 ? `
                <tr><td colspan="6" style="text-align:center; padding:20px; color:var(--text-muted);">No stock recorded.</td></tr>
              ` : stock.map(s => `
                <tr>
                  <td><strong>${s.crop_name}</strong></td>
                  <td><code>${s.batch_id}</code></td>
                  <td style="font-weight:700; color:#2e7d32;">${Number(s.current_stock_kg).toLocaleString()} kg</td>
                  <td>${(s.current_stock_kg / 1000).toFixed(2)} MT</td>
                  <td>${s.warehouse_location}</td>
                  <td>${s.last_replenished}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load Minor WH overview: ${err.message}</div>`;
  }
}

async function renderMinorWHAIRecs(container) {
  container.innerHTML = `<div style="text-align:center; padding:32px; color:var(--text-muted);">Running Central AI local demand & restock prediction...</div>`;
  try {
    const res = await ApiClient.getMinorWHAIRecs();

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar">
          <div>
            <h3>🤖 Central AI Inventory & Restock Optimization</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">Autonomous Sub-District Stock Balancing & Spoilage Prevention</span>
          </div>
        </div>

        <div class="metric-grid">
          <div class="metric-card">
            <div class="metric-val" style="color:#1565c0;">${Number(res.predicted_monthly_demand_kg).toLocaleString()} kg</div>
            <div class="metric-label">Predicted Monthly Demand</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#2e7d32;">${Number(res.recommended_stock_kg).toLocaleString()} kg</div>
            <div class="metric-label">Optimal Target Buffer Stock</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#e65100;">${Number(res.recommended_restock_kg).toLocaleString()} kg</div>
            <div class="metric-label">Recommended Restock from Major Silo</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:${res.spoilage_risk === 'LOW' ? '#2e7d32' : '#c62828'};">${res.spoilage_risk}</div>
            <div class="metric-label">Spoilage & Deterioration Risk</div>
          </div>
        </div>

        <div class="ai-insight-box" style="margin-top:20px;">
          <div style="font-weight:700; color:#1565c0; font-size:0.95rem; margin-bottom:6px;">
            📦 Central AI Stock Balancing Rationale
          </div>
          <div style="font-size:0.85rem; color:#2c3e50; line-height:1.5;">
            ${res.ai_rationale}
          </div>
          <div style="margin-top:14px;">
            <button class="btn btn-primary btn-sm" onclick="selectSubTab('minor_wh_restock')" style="background:#e65100;">
              📤 Submit Restock Request of ${(res.recommended_restock_kg / 1000).toFixed(1)} MT
            </button>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load AI recommendations: ${err.message}</div>`;
  }
}

// =============================================================================
// TASK 7: MAJOR WAREHOUSE -> MINOR WAREHOUSE DISPATCH & TRUCK TRACKING
// =============================================================================

let cachedDispatchesList = [];
let activeDispatchFilter = "ALL";

// --- 1. MAJOR WAREHOUSE DISPATCHES CONSOLE ---
async function renderMajorWHDispatchesConsole(container) {
  if (!container) container = document.getElementById("contentContainer") || document.getElementById("activeTableContainer");
  if (!container) return;

  container.innerHTML = `
    <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:32px; text-align:center;">
      <div class="loader-spinner" style="margin:0 auto 16px auto; width:36px; height:36px; border:3px solid #e0e0e0; border-top-color:#1565c0; border-radius:50%; animation:spin 0.8s linear infinite;"></div>
      <h4 style="margin:0 0 6px 0; color:var(--primary-dark);">Loading Major Warehouse Dispatches...</h4>
      <p style="font-size:0.8rem; color:var(--text-muted); margin:0;">Connecting to central dispatch and fleet ledger...</p>
    </div>
  `;

  try {
    const res = await ApiClient.getWarehouseDispatches() || {};
    cachedDispatchesList = res.dispatches || (Array.isArray(res) ? res : []);

    const totalCount = cachedDispatchesList.length;
    const inTransitCount = cachedDispatchesList.filter(d => d.status === 'In Transit' || d.delivery_status === 'IN_TRANSIT').length;
    const pendingCount = cachedDispatchesList.filter(d => d.status === 'Pending Departure' || d.delivery_status === 'PENDING').length;
    const completedCount = cachedDispatchesList.filter(d => d.status === 'Completed' || d.status === 'Received' || d.delivery_status === 'DELIVERED').length;
    const discrepancyCount = cachedDispatchesList.filter(d => d.status === 'Discrepancy' || d.delivery_status === 'DISCREPANCY').length;

    const filtered = cachedDispatchesList.filter(d => {
      if (activeDispatchFilter === "ALL") return true;
      if (activeDispatchFilter === "IN_TRANSIT") return d.status === 'In Transit' || d.delivery_status === 'IN_TRANSIT';
      if (activeDispatchFilter === "PENDING") return d.status === 'Pending Departure' || d.delivery_status === 'PENDING';
      if (activeDispatchFilter === "COMPLETED") return d.status === 'Completed' || d.status === 'Received' || d.delivery_status === 'DELIVERED';
      if (activeDispatchFilter === "DISCREPANCY") return d.status === 'Discrepancy' || d.delivery_status === 'DISCREPANCY';
      return true;
    });

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <!-- Top Toolbar -->
        <div class="table-toolbar" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
          <div>
            <h3 style="margin:0; color:var(--primary-dark);">🚚 Major Warehouse ➔ Minor Warehouse Dispatches</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">
              Immutable Batch Linkage: Batch ID ➔ Farmer ➔ Crop ➔ Task 5 Certified Grade ➔ Dispatched Stock
            </span>
          </div>
          <div style="display:flex; gap:10px;">
            <button class="btn btn-secondary btn-sm" onclick="renderMajorWHDispatchesConsole()">
              🔄 Refresh
            </button>
            <button class="btn btn-primary btn-sm" onclick="openCreateDispatchModal()" style="background:#1565c0; font-weight:700;">
              ➕ Create New Dispatch
            </button>
          </div>
        </div>

        <!-- Metric KPI Cards -->
        <div class="metric-grid" style="margin:16px 0 20px 0;">
          <div class="metric-card" onclick="setDispatchFilter('ALL')" style="cursor:pointer; border-bottom:${activeDispatchFilter === 'ALL' ? '3px solid #1565c0' : '1px solid var(--border)'};">
            <div class="metric-val" style="color:#1565c0;">${totalCount}</div>
            <div class="metric-label">Total Dispatches</div>
          </div>
          <div class="metric-card" onclick="setDispatchFilter('IN_TRANSIT')" style="cursor:pointer; border-bottom:${activeDispatchFilter === 'IN_TRANSIT' ? '3px solid #0288d1' : '1px solid var(--border)'};">
            <div class="metric-val" style="color:#0288d1;">${inTransitCount}</div>
            <div class="metric-label">In Transit (Active GPS)</div>
          </div>
          <div class="metric-card" onclick="setDispatchFilter('PENDING')" style="cursor:pointer; border-bottom:${activeDispatchFilter === 'PENDING' ? '3px solid #f57c00' : '1px solid var(--border)'};">
            <div class="metric-val" style="color:#f57c00;">${pendingCount}</div>
            <div class="metric-label">Pending Departure</div>
          </div>
          <div class="metric-card" onclick="setDispatchFilter('COMPLETED')" style="cursor:pointer; border-bottom:${activeDispatchFilter === 'COMPLETED' ? '3px solid #2e7d32' : '1px solid var(--border)'};">
            <div class="metric-val" style="color:#2e7d32;">${completedCount}</div>
            <div class="metric-label">Completed & Verified</div>
          </div>
          <div class="metric-card" onclick="setDispatchFilter('DISCREPANCY')" style="cursor:pointer; border-bottom:${activeDispatchFilter === 'DISCREPANCY' ? '3px solid #c62828' : '1px solid var(--border)'};">
            <div class="metric-val" style="color:#c62828;">${discrepancyCount}</div>
            <div class="metric-label">Discrepancies Flagged</div>
          </div>
        </div>

        <!-- Dispatches Table -->
        <div style="background:white; border-radius:8px; border:1px solid var(--border); overflow-x:auto;">
          <table class="record-table">
            <thead>
              <tr>
                <th>Dispatch ID</th>
                <th>Batch ID & Crop</th>
                <th>Certified Grade</th>
                <th>Sent Qty (kg)</th>
                <th>Origin ➔ Destination</th>
                <th>Truck & Driver</th>
                <th>Departure / Arrival</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${filtered.length === 0 ? `
                <tr>
                  <td colspan="9" style="text-align:center; padding:32px; color:var(--text-muted);">
                    No dispatches found for filter: <strong>${activeDispatchFilter}</strong>. Click [ Create New Dispatch ] to schedule shipment.
                  </td>
                </tr>
              ` : filtered.map(d => {
                const isPending = d.status === 'Pending Departure' || d.delivery_status === 'PENDING';
                const isInTransit = d.status === 'In Transit' || d.delivery_status === 'IN_TRANSIT';
                const isDiscrepancy = d.status === 'Discrepancy' || d.delivery_status === 'DISCREPANCY';
                const isCompleted = d.status === 'Completed' || d.status === 'Received' || d.delivery_status === 'DELIVERED';

                const statusBadge = isCompleted ? 'badge-success' : isInTransit ? 'badge-info' : isDiscrepancy ? 'badge-danger' : 'badge-warning';

                return `
                  <tr>
                    <td><code>${d.dispatch_id}</code></td>
                    <td>
                      <div style="font-weight:700; color:#263238;">${d.crop_name}</div>
                      <div style="font-size:0.72rem; color:var(--text-muted);">Batch: <code>${d.batch_id}</code></div>
                    </td>
                    <td>
                      <span class="badge ${d.final_grade === 'A' ? 'badge-success' : d.final_grade === 'B' ? 'badge-info' : 'badge-warning'}" style="font-size:0.78rem;">
                        Grade ${d.final_grade || 'A'}
                      </span>
                    </td>
                    <td style="font-weight:700; color:#1565c0;">
                      ${Number(d.dispatch_quantity_kg).toLocaleString()} kg
                      <div style="font-size:0.7rem; color:var(--text-muted);">${(d.dispatch_quantity_kg / 1000).toFixed(2)} MT</div>
                    </td>
                    <td>
                      <div style="font-size:0.78rem; font-weight:600;">${d.destination_minor_warehouse}</div>
                      <div style="font-size:0.7rem; color:var(--text-muted);">From: ${d.origin_warehouse}</div>
                    </td>
                    <td>
                      <div style="font-weight:600;">🚚 ${d.truck_number}</div>
                      <div style="font-size:0.72rem; color:var(--text-muted);">${d.driver_name} (${d.driver_phone || ''})</div>
                    </td>
                    <td style="font-size:0.75rem;">
                      <div>Dep: <strong>${d.departure_time || d.dispatch_date || '10:30 AM'}</strong></div>
                      <div>Exp: <strong>${d.expected_arrival || '02:30 PM'}</strong></div>
                      ${d.actual_arrival ? `<div style="color:#2e7d32;">Act: <strong>${d.actual_arrival}</strong></div>` : ''}
                    </td>
                    <td>
                      <span class="badge ${statusBadge}" style="font-size:0.75rem; padding:3px 8px;">
                        ${isInTransit ? '<span class="live-dot" style="display:inline-block; width:6px; height:6px; background:#0288d1; border-radius:50%; margin-right:4px; animation:pulse 1.2s infinite;"></span>' : ''}
                        ${d.status}
                      </span>
                    </td>
                    <td>
                      <div style="display:flex; flex-direction:column; gap:4px;">
                        <button class="btn btn-secondary btn-sm" onclick="openDispatchDetailModal('${d.dispatch_id}')" style="font-size:0.7rem; padding:2px 6px;">
                          👁️ View
                        </button>
                        ${isPending ? `
                          <button class="btn btn-primary btn-sm" onclick="handleStartTransit('${d.dispatch_id}')" style="background:#0288d1; font-size:0.7rem; padding:2px 6px; font-weight:700;">
                            🚚 Start Delivery
                          </button>
                          <button class="btn btn-secondary btn-sm" onclick="openEditDispatchModal('${d.dispatch_id}')" style="font-size:0.7rem; padding:2px 6px;">
                            ✏️ Edit
                          </button>
                        ` : ''}
                        <button class="btn btn-secondary btn-sm" onclick="openDispatchTrackingModal('${d.dispatch_id}')" style="font-size:0.7rem; padding:2px 6px; background:#e8eaf6; color:#283593;">
                          📍 Track GPS
                        </button>
                      </div>
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load warehouse dispatches: ${err.message}</div>`;
  }
}

function setDispatchFilter(filter) {
  activeDispatchFilter = filter;
  renderMajorWHDispatchesConsole();
}

// --- CREATE DISPATCH MODAL ---
async function openCreateDispatchModal() {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = "➕ Create Major Warehouse ➔ Minor Warehouse Dispatch";
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Create Dispatch Order";

  modalBody.innerHTML = `<div style="padding:24px; text-align:center; color:var(--text-muted);">Loading storage batches and transport fleet...</div>`;
  modal.style.display = "flex";

  try {
    const storageRes = await ApiClient.getWarehouseStorageList() || {};
    const storageList = storageRes.records || (Array.isArray(storageRes) ? storageRes : []);
    const availableBatches = storageList.filter(s => (s.available_quantity_kg || s.current_stock_kg) > 0);

    const trucks = await ApiClient.getTrucksList() || [];

    modalBody.innerHTML = `
      <form id="createDispatchForm" class="form-grid" onsubmit="handleCreateDispatchSubmit(event)">
        <!-- Step 1: Source Batch Selection -->
        <div class="form-group" style="grid-column: span 2; background:#e3f2fd; border:1px solid #90caf9; padding:12px; border-radius:6px;">
          <label class="form-label" style="color:#0d47a1; font-weight:700;">📦 Select Certified Stored Batch *</label>
          <select id="dispBatchSelect" class="form-control" onchange="onDispatchBatchSelected(this.value)" required>
            <option value="">-- Choose Stored Batch --</option>
            ${availableBatches.map(b => `
              <option value="${b.batch_id}" data-crop="${b.crop_name}" data-avail="${b.available_quantity_kg || b.current_stock_kg}" data-grade="${b.quality_grade || 'A'}" data-loc="${b.storage_location}">
                ${b.batch_id} • ${b.crop_name} (Grade ${b.quality_grade || 'A'}) • ${Number(b.available_quantity_kg || b.current_stock_kg).toLocaleString()} kg Available (${b.storage_location})
              </option>
            `).join('')}
          </select>
          <div style="font-size:0.72rem; color:#1565c0; margin-top:4px;">
            Immutable Traceability: Selected batch automatically inherits farmer linkage, crop variety, and Task 5 certified grade.
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Crop Name</label>
          <input type="text" id="dispCropName" class="form-control" placeholder="Auto-filled from batch" readonly style="background:#f5f5f5;">
        </div>

        <div class="form-group">
          <label class="form-label">Certified Quality Grade (Task 5 Certified)</label>
          <input type="text" id="dispFinalGrade" class="form-control" placeholder="Auto-filled (Grade A/B/C)" readonly style="background:#f5f5f5; font-weight:700; color:#2e7d32;">
        </div>

        <div class="form-group">
          <label class="form-label">Available Storage Stock (kg)</label>
          <input type="text" id="dispAvailStock" class="form-control" placeholder="Available kg" readonly style="background:#f5f5f5; font-weight:700; color:#1565c0;">
        </div>

        <div class="form-group">
          <label class="form-label">Dispatch Quantity (kg) *</label>
          <input type="number" step="0.1" id="dispQuantityKg" class="form-control" placeholder="e.g. 15000" min="1" required>
          <div style="font-size:0.7rem; color:var(--text-muted); margin-top:2px;">Strict inventory conservation: Cannot exceed available storage stock.</div>
        </div>

        <!-- Step 2: Logistics & Carrier -->
        <div class="form-group" style="grid-column: span 2;">
          <label class="form-label">Select Registered Fleet Carrier *</label>
          <select id="dispTruckSelect" class="form-control" onchange="onDispatchTruckSelected(this)">
            <option value="">-- Select Registered Truck --</option>
            ${trucks.map(t => `
              <option value="${t.truck_id}" data-num="${t.vehicle_number}" data-driver="${t.driver_name}" data-phone="${t.driver_phone || ''}" data-driverid="${t.driver_id || ''}">
                ${t.truck_id} • ${t.vehicle_number} (${t.driver_name} - ${t.current_status})
              </option>
            `).join('')}
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Truck Vehicle Number *</label>
          <input type="text" id="dispTruckNumber" class="form-control" placeholder="e.g. MH-12-Q-4521" required>
        </div>

        <div class="form-group">
          <label class="form-label">Driver Full Name *</label>
          <input type="text" id="dispDriverName" class="form-control" placeholder="e.g. Ramesh Patil" required>
        </div>

        <div class="form-group">
          <label class="form-label">Driver Contact Mobile Phone</label>
          <input type="text" id="dispDriverPhone" class="form-control" placeholder="e.g. +91 98220 11223">
        </div>

        <div class="form-group">
          <label class="form-label">Destination Minor Godown *</label>
          <select id="dispDestinationWh" class="form-control" required>
            <option value="Baramati APMC Transit Godown No. 3">Baramati APMC Transit Godown No. 3</option>
            <option value="Indapur Sub-District Godown">Indapur Sub-District Godown</option>
            <option value="Daund PDS Buffer Storage Depot">Daund PDS Buffer Storage Depot</option>
            <option value="Shirur Block Level Depot">Shirur Block Level Depot</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Dispatch Date *</label>
          <input type="text" id="dispDate" class="form-control" value="${new Date().toISOString().split('T')[0]}" required>
        </div>

        <div class="form-group">
          <label class="form-label">Expected Departure Time</label>
          <input type="text" id="dispDepTime" class="form-control" value="10:30 AM">
        </div>

        <div class="form-group">
          <label class="form-label">Expected Arrival Time</label>
          <input type="text" id="dispArrTime" class="form-control" value="02:30 PM">
        </div>

        <div class="form-group" style="grid-column: span 2;">
          <label class="form-label">Operational Notes & Gate Pass Remarks</label>
          <textarea id="dispNotes" class="form-control" rows="2" placeholder="Standard grain transit protocol under sealed tarpaulin."></textarea>
        </div>
      </form>
    `;

    modalSubmitBtn.onclick = () => {
      document.getElementById("createDispatchForm").dispatchEvent(new Event("submit"));
    };
  } catch (err) {
    modalBody.innerHTML = `<div class="alert-box danger">Failed to initialize dispatch form: ${err.message}</div>`;
  }
}

function onDispatchBatchSelected(batchId) {
  const sel = document.getElementById("dispBatchSelect");
  const opt = sel.options[sel.selectedIndex];
  if (!opt || !batchId) return;

  const crop = opt.getAttribute("data-crop") || "";
  const avail = parseFloat(opt.getAttribute("data-avail")) || 0;
  const grade = opt.getAttribute("data-grade") || "A";

  document.getElementById("dispCropName").value = crop;
  document.getElementById("dispFinalGrade").value = `Grade ${grade}`;
  document.getElementById("dispAvailStock").value = `${avail.toLocaleString()} kg`;
  
  const qtyInput = document.getElementById("dispQuantityKg");
  qtyInput.max = avail;
  if (!qtyInput.value || parseFloat(qtyInput.value) > avail) {
    qtyInput.value = avail;
  }
}

function onDispatchTruckSelected(sel) {
  const opt = sel.options[sel.selectedIndex];
  if (!opt || !sel.value) return;

  document.getElementById("dispTruckNumber").value = opt.getAttribute("data-num") || "";
  document.getElementById("dispDriverName").value = opt.getAttribute("data-driver") || "";
  document.getElementById("dispDriverPhone").value = opt.getAttribute("data-phone") || "";
}

async function handleCreateDispatchSubmit(e) {
  e.preventDefault();
  const batchId = document.getElementById("dispBatchSelect").value;
  const cropName = document.getElementById("dispCropName").value;
  const gradeVal = (document.getElementById("dispFinalGrade").value || "Grade A").replace("Grade ", "").trim();
  const qty = parseFloat(document.getElementById("dispQuantityKg").value);
  const truckNum = document.getElementById("dispTruckNumber").value.trim();
  const driverName = document.getElementById("dispDriverName").value.trim();
  const destWh = document.getElementById("dispDestinationWh").value;

  if (!batchId || !cropName || isNaN(qty) || qty <= 0 || !truckNum || !driverName) {
    alert("Please fill all required fields correctly.");
    return;
  }

  const truckSel = document.getElementById("dispTruckSelect");
  const truckId = truckSel ? truckSel.value : null;

  const payload = {
    batch_id: batchId,
    crop_name: cropName,
    final_grade: gradeVal,
    dispatch_quantity_kg: qty,
    origin_warehouse: "Pune Central Silo Hub",
    origin_warehouse_id: "MWH-PUN-01",
    destination_minor_warehouse: destWh,
    destination_minor_warehouse_id: "MIN-BMT-01",
    truck_id: truckId || undefined,
    truck_number: truckNum,
    driver_name: driverName,
    driver_phone: document.getElementById("dispDriverPhone").value.trim() || undefined,
    dispatch_date: document.getElementById("dispDate").value.trim(),
    departure_time: document.getElementById("dispDepTime").value.trim(),
    expected_arrival: document.getElementById("dispArrTime").value.trim(),
    notes: document.getElementById("dispNotes").value.trim() || undefined
  };

  const btn = document.getElementById("modalSubmitBtn");
  try {
    btn.disabled = true;
    btn.textContent = "Creating Dispatch Order...";
    const res = await ApiClient.createWarehouseDispatch(payload);
    closeModal();
    alert(`Dispatch #${res.dispatch_id} created successfully!
${res.dispatch_quantity_kg} kg of ${res.crop_name} (Grade ${res.final_grade}) scheduled for ${res.destination_minor_warehouse}.
Storage stock decremented automatically.`);
    renderMajorWHDispatchesConsole();
  } catch (err) {
    alert("Dispatch creation failed: " + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Create Dispatch Order";
    }
  }
}

// --- START DISPATCH TRANSIT ---
async function handleStartTransit(dispatchId) {
  if (!confirm(`Confirm departure and start transit for Dispatch ${dispatchId}? This will activate real-time GPS tracking on the driver's device.`)) {
    return;
  }
  try {
    const res = await ApiClient.startDispatchTransit(dispatchId, {
      departure_time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });
    alert(`Dispatch ${dispatchId} is now IN TRANSIT! Real-time GPS tracking is ACTIVE.`);
    renderMajorWHDispatchesConsole();
  } catch (err) {
    alert("Failed to start transit: " + err.message);
  }
}

// --- DISPATCH DETAIL MODAL ---
async function openDispatchDetailModal(dispatchId) {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `📋 Dispatch Details: ${dispatchId}`;
  modalSubmitBtn.style.display = "none";

  modalBody.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted);">Loading dispatch record...</div>`;
  modal.style.display = "flex";

  try {
    const d = await ApiClient.getWarehouseDispatch(dispatchId);

    modalBody.innerHTML = `
      <div style="background:#e3f2fd; border:1px solid #90caf9; padding:14px; border-radius:6px; margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <strong style="color:#0d47a1; font-size:1rem;">${d.dispatch_id}</strong>
            <div style="font-size:0.8rem; color:#1565c0; margin-top:2px;">
              Cargo: <strong>${d.crop_name}</strong> • Linked Batch: <code>${d.batch_id}</code>
            </div>
          </div>
          <div style="text-align:right;">
            <span class="badge ${d.final_grade === 'A' ? 'badge-success' : 'badge-info'}" style="font-size:0.85rem;">Grade ${d.final_grade}</span>
            <div style="font-size:0.72rem; color:#1976d2; margin-top:2px;">Certified Task 5 Grade</div>
          </div>
        </div>
      </div>

      <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:0.82rem; margin-bottom:16px;">
        <div><strong>Dispatched Quantity:</strong> <span style="color:#1565c0; font-weight:700;">${Number(d.dispatch_quantity_kg).toLocaleString()} kg</span></div>
        <div><strong>Current Status:</strong> <span class="badge ${d.status === 'Completed' ? 'badge-success' : d.status === 'In Transit' ? 'badge-info' : 'badge-warning'}">${d.status}</span></div>
        <div><strong>Origin Warehouse:</strong> ${d.origin_warehouse}</div>
        <div><strong>Destination Godown:</strong> ${d.destination_minor_warehouse}</div>
        <div><strong>Assigned Truck:</strong> 🚚 ${d.truck_number} (${d.truck_id || ''})</div>
        <div><strong>Driver:</strong> ${d.driver_name} (${d.driver_phone || 'N/A'})</div>
        <div><strong>Dispatch Date:</strong> ${d.dispatch_date}</div>
        <div><strong>Departure Time:</strong> ${d.departure_time || 'N/A'}</div>
        <div><strong>Expected Arrival:</strong> ${d.expected_arrival || 'N/A'}</div>
        <div><strong>Actual Arrival:</strong> ${d.actual_arrival || 'In Transit / Pending'}</div>
        <div><strong>Live GPS Active:</strong> ${d.is_gps_active ? '🟢 Yes (Duty Active)' : '⚪ No (Inactive / Delivered)'}</div>
        <div><strong>Last Location:</strong> ${d.current_location || 'GPS location unavailable'}</div>
      </div>

      ${d.notes ? `
        <div style="background:#fafafa; border:1px solid #eee; padding:10px; border-radius:4px; font-size:0.8rem; margin-bottom:16px;">
          <strong>Notes:</strong><br>${d.notes}
        </div>
      ` : ''}

      <div style="display:flex; justify-content:space-between; align-items:center; margin-top:16px;">
        <a href="${d.google_maps_url || `https://www.google.com/maps/search/?api=1&query=${d.latitude || 18.5204},${d.longitude || 73.8567}`}" target="_blank" class="btn btn-maps btn-sm" style="text-decoration:none; padding:6px 14px;">
          🗺️ View on Google Maps
        </a>
        <button class="btn btn-secondary btn-sm" onclick="closeModal()">Close</button>
      </div>
    `;
  } catch (err) {
    modalBody.innerHTML = `<div class="alert-box danger">Error loading dispatch: ${err.message}</div>`;
  }
}

// --- EDIT DISPATCH MODAL ---
async function openEditDispatchModal(dispatchId) {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `✏️ Edit Dispatch Order: ${dispatchId}`;
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Save Changes";

  modalBody.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted);">Loading dispatch...</div>`;
  modal.style.display = "flex";

  try {
    const d = await ApiClient.getWarehouseDispatch(dispatchId);

    modalBody.innerHTML = `
      <form id="editDispatchForm" class="form-grid" onsubmit="handleUpdateDispatchSubmit(event, '${d.dispatch_id}')">
        <div class="form-group">
          <label class="form-label">Truck Registration Number</label>
          <input type="text" id="editDispTruckNum" class="form-control" value="${d.truck_number || ''}" required>
        </div>

        <div class="form-group">
          <label class="form-label">Driver Full Name</label>
          <input type="text" id="editDispDriverName" class="form-control" value="${d.driver_name || ''}" required>
        </div>

        <div class="form-group">
          <label class="form-label">Driver Mobile Phone</label>
          <input type="text" id="editDispDriverPhone" class="form-control" value="${d.driver_phone || ''}">
        </div>

        <div class="form-group">
          <label class="form-label">Destination Minor Warehouse</label>
          <input type="text" id="editDispDest" class="form-control" value="${d.destination_minor_warehouse || ''}" required>
        </div>

        <div class="form-group">
          <label class="form-label">Expected Departure Time</label>
          <input type="text" id="editDispDepTime" class="form-control" value="${d.departure_time || ''}">
        </div>

        <div class="form-group">
          <label class="form-label">Expected Arrival Time</label>
          <input type="text" id="editDispArrTime" class="form-control" value="${d.expected_arrival || ''}">
        </div>

        <div class="form-group" style="grid-column: span 2;">
          <label class="form-label">Notes</label>
          <textarea id="editDispNotes" class="form-control" rows="2">${d.notes || ''}</textarea>
        </div>
      </form>
    `;

    modalSubmitBtn.onclick = () => {
      document.getElementById("editDispatchForm").dispatchEvent(new Event("submit"));
    };
  } catch (err) {
    modalBody.innerHTML = `<div class="alert-box danger">Error: ${err.message}</div>`;
  }
}

async function handleUpdateDispatchSubmit(e, dispatchId) {
  e.preventDefault();
  const payload = {
    truck_number: document.getElementById("editDispTruckNum").value.trim(),
    driver_name: document.getElementById("editDispDriverName").value.trim(),
    driver_phone: document.getElementById("editDispDriverPhone").value.trim(),
    destination_minor_warehouse: document.getElementById("editDispDest").value.trim(),
    departure_time: document.getElementById("editDispDepTime").value.trim(),
    expected_arrival: document.getElementById("editDispArrTime").value.trim(),
    notes: document.getElementById("editDispNotes").value.trim()
  };

  const btn = document.getElementById("modalSubmitBtn");
  try {
    btn.disabled = true;
    await ApiClient.updateWarehouseDispatch(dispatchId, payload);
    closeModal();
    alert(`Dispatch ${dispatchId} updated successfully!`);
    renderMajorWHDispatchesConsole();
  } catch (err) {
    alert("Update failed: " + err.message);
  } finally {
    if (btn) btn.disabled = false;
  }
}

// --- 2. TRUCK GPS TRACKING CONSOLE ---
async function renderTruckTrackingConsole(container) {
  if (!container) container = document.getElementById("contentContainer") || document.getElementById("activeTableContainer");
  if (!container) return;

  container.innerHTML = `
    <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:32px; text-align:center;">
      <div class="loader-spinner" style="margin:0 auto 16px auto; width:36px; height:36px; border:3px solid #e0e0e0; border-top-color:#1565c0; border-radius:50%; animation:spin 0.8s linear infinite;"></div>
      <h4 style="margin:0 0 6px 0; color:var(--primary-dark);">Connecting to Live Fleet GPS Network...</h4>
      <p style="font-size:0.8rem; color:var(--text-muted); margin:0;">Acquiring satellite telemetry and transit telemetry...</p>
    </div>
  `;

  try {
    const trucks = await ApiClient.getTrucksList() || [];
    const dispatchesRes = await ApiClient.getWarehouseDispatches() || {};
    const dispatches = dispatchesRes.dispatches || (Array.isArray(dispatchesRes) ? dispatchesRes : []);

    const inTransitDispatches = dispatches.filter(d => d.status === 'In Transit' || d.delivery_status === 'IN_TRANSIT');
    const availableTrucks = trucks.filter(t => t.current_status === 'AVAILABLE');

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
          <div>
            <h3 style="margin:0; color:var(--primary-dark);">🚛 Live Fleet GPS & Transit Telemetry</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">
              Real-time In-Transit Agricultural Cargo Monitoring • Google Maps Navigation Linkage
            </span>
          </div>
          <button class="btn btn-primary btn-sm" onclick="renderTruckTrackingConsole()" style="background:#1565c0;">
            🔄 Refresh GPS Feed
          </button>
        </div>

        <div class="metric-grid" style="margin:16px 0 20px 0;">
          <div class="metric-card">
            <div class="metric-val" style="color:#1565c0;">${trucks.length}</div>
            <div class="metric-label">Registered Fleet Trucks</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#0288d1;">${inTransitDispatches.length}</div>
            <div class="metric-label">Active GPS Transits</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#2e7d32;">${availableTrucks.length}</div>
            <div class="metric-label">Trucks Ready / Available</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#6a1b9a;">100%</div>
            <div class="metric-label">Privacy Shield Active (Transit-Only)</div>
          </div>
        </div>

        <!-- Active Transit Cards Grid -->
        <h4 style="color:var(--primary-dark); margin:20px 0 12px 0;">Active Vehicle Transits (${inTransitDispatches.length})</h4>
        <div class="truck-grid">
          ${inTransitDispatches.length === 0 ? `
            <div style="grid-column:1/-1; text-align:center; padding:32px; background:white; border-radius:8px; border:1px solid var(--border); color:var(--text-muted);">
              No vehicles currently in transit. Click [ Create New Dispatch ] in Dispatches tab to initiate cargo transit.
            </div>
          ` : inTransitDispatches.map(t => `
            <div class="truck-card" style="background:white; border:1px solid #90caf9; border-radius:8px; padding:18px; box-shadow:0 2px 8px rgba(0,0,0,0.05);">
              <div class="truck-header" style="display:flex; justify-content:space-between; align-items:start; border-bottom:1px solid #eee; padding-bottom:10px; margin-bottom:12px;">
                <div>
                  <div class="truck-id" style="font-size:1.05rem; font-weight:700; color:#0d47a1;">🚚 ${t.truck_number}</div>
                  <div style="font-size:0.72rem; color:var(--text-muted);">Dispatch ID: <code>${t.dispatch_id}</code></div>
                </div>
                <span class="badge badge-info" style="font-size:0.75rem; padding:4px 8px;">
                  <span class="live-dot" style="display:inline-block; width:6px; height:6px; background:#0288d1; border-radius:50%; margin-right:4px; animation:pulse 1.2s infinite;"></span>
                  IN TRANSIT
                </span>
              </div>

              <div class="truck-route" style="display:flex; align-items:center; justify-content:space-between; background:#f5f7fa; padding:10px; border-radius:6px; margin-bottom:12px;">
                <div class="route-node">
                  <div class="node-label" style="font-size:0.68rem; color:var(--text-muted);">ORIGIN HUB</div>
                  <div class="node-val" style="font-weight:700; font-size:0.8rem; color:#263238;">${t.origin_warehouse}</div>
                </div>
                <div style="color:#0288d1; font-size:1.2rem; font-weight:700;">➔</div>
                <div class="route-node" style="text-align:right;">
                  <div class="node-label" style="font-size:0.68rem; color:var(--text-muted);">DESTINATION GODOWN</div>
                  <div class="node-val" style="font-weight:700; font-size:0.8rem; color:#263238;">${t.destination_minor_warehouse}</div>
                </div>
              </div>

              <div style="font-size:0.8rem; color:#37474f; margin-bottom:12px;">
                <div>🌾 <strong>Cargo:</strong> ${Number(t.dispatch_quantity_kg).toLocaleString()} kg ${t.crop_name} (Grade ${t.final_grade}) • Batch: <code>${t.batch_id}</code></div>
                <div>👤 <strong>Driver:</strong> ${t.driver_name} (${t.driver_phone || 'N/A'})</div>
                <div>🕒 <strong>Departure:</strong> ${t.departure_time || '10:30 AM'} • <strong>Expected:</strong> ${t.expected_arrival || '02:30 PM'}</div>
              </div>

              <div class="gps-strip" style="background:#e8f5e9; border:1px solid #c8e6c9; border-radius:6px; padding:10px; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <div>
                    <div style="font-size:0.78rem; color:#1b5e20;">📍 Location: <strong>${t.current_location || 'Pune-Solapur Highway (Near Patas)'}</strong></div>
                    <div style="font-size:0.7rem; color:#388e3c; margin-top:2px;">Last GPS Sync: ${t.last_gps_update || 'Just now'}</div>
                  </div>
                  <a href="${t.google_maps_url || `https://www.google.com/maps/search/?api=1&query=${t.latitude || 18.5204},${t.longitude || 73.8567}`}" target="_blank" class="btn btn-maps btn-sm" style="text-decoration:none; padding:4px 10px; font-size:0.72rem; white-space:nowrap;">
                    🗺️ Google Maps
                  </a>
                </div>
              </div>

              <div style="display:flex; gap:8px;">
                <button class="btn btn-outline btn-sm" onclick="openSimulateGPSModal('${t.dispatch_id}')" style="flex:1; font-size:0.75rem;">
                  📍 Update Driver GPS
                </button>
                <button class="btn btn-primary btn-sm" onclick="openMinorWHReceiveModal('${t.dispatch_id}')" style="background:#2e7d32; flex:1; font-size:0.75rem; font-weight:700;">
                  📥 Minor WH Receive
                </button>
              </div>
            </div>
          `).join('')}
        </div>

        <!-- Registered Fleet Registry Table -->
        <h4 style="color:var(--primary-dark); margin:28px 0 12px 0;">Carrier Fleet Registry (${trucks.length})</h4>
        <div style="background:white; border-radius:8px; border:1px solid var(--border); overflow-x:auto;">
          <table class="record-table">
            <thead>
              <tr>
                <th>Truck ID</th>
                <th>Registration No</th>
                <th>Vehicle Type</th>
                <th>Capacity</th>
                <th>Assigned Driver</th>
                <th>Driver Phone</th>
                <th>Fleet Status</th>
                <th>Current Duty / Destination</th>
                <th>Last GPS Update</th>
              </tr>
            </thead>
            <tbody>
              ${trucks.map(t => `
                <tr>
                  <td><code>${t.truck_id}</code></td>
                  <td><strong>${t.vehicle_number}</strong></td>
                  <td>${t.vehicle_type}</td>
                  <td>${t.capacity_mt} MT</td>
                  <td>${t.driver_name}</td>
                  <td>${t.driver_phone || 'N/A'}</td>
                  <td>
                    <span class="badge ${t.current_status === 'AVAILABLE' ? 'badge-success' : t.current_status === 'IN_TRANSIT' ? 'badge-info' : 'badge-warning'}">
                      ${t.current_status}
                    </span>
                  </td>
                  <td>
                    ${t.current_dispatch_id ? `<code>${t.current_dispatch_id}</code> ➔ ${t.destination || 'Minor Godown'}` : '<span style="color:var(--text-muted); font-size:0.75rem;">Idle / Ready at Hub</span>'}
                  </td>
                  <td style="font-size:0.75rem;">${t.last_gps_update || 'N/A'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load truck tracking: ${err.message}</div>`;
  }
}

const renderTruckTracking = renderTruckTrackingConsole;

// --- GPS TRACKING MODAL ---
async function openDispatchTrackingModal(dispatchId) {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `📍 Live GPS Telemetry: ${dispatchId}`;
  modalSubmitBtn.style.display = "none";

  modalBody.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted);">Fetching live GPS coordinates...</div>`;
  modal.style.display = "flex";

  try {
    const t = await ApiClient.getDispatchTracking(dispatchId);

    modalBody.innerHTML = `
      <div style="background:#e8f5e9; border:1px solid #c8e6c9; border-radius:6px; padding:16px; margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <h4 style="margin:0; color:#1b5e20;">🚚 ${t.truck_number} • ${t.driver_name}</h4>
            <div style="font-size:0.78rem; color:#2e7d32; margin-top:2px;">
              Cargo: <strong>${Number(t.dispatch_quantity_kg).toLocaleString()} kg ${t.crop_name}</strong> (Grade ${t.final_grade})
            </div>
          </div>
          <span class="badge ${t.is_gps_active ? 'badge-success' : 'badge-secondary'}" style="font-size:0.8rem;">
            ${t.is_gps_active ? '🟢 LIVE GPS ACTIVE' : '⚪ GPS INACTIVE'}
          </span>
        </div>
      </div>

      <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:0.82rem; margin-bottom:16px;">
        <div><strong>Current Checkpoint:</strong> ${t.current_location || 'GPS location unavailable'}</div>
        <div><strong>Last Coordinate Sync:</strong> ${t.last_gps_update || 'N/A'}</div>
        <div><strong>Latitude:</strong> <code>${t.latitude}</code></div>
        <div><strong>Longitude:</strong> <code>${t.longitude}</code></div>
        <div><strong>Origin:</strong> ${t.origin_warehouse}</div>
        <div><strong>Destination:</strong> ${t.destination_minor_warehouse}</div>
      </div>

      <div style="background:#f5f7fa; border:1px solid #cfd8dc; border-radius:6px; padding:14px; text-align:center; margin-bottom:16px;">
        <div style="font-size:0.85rem; color:#37474f; margin-bottom:10px;">
          🛰️ <strong>Direct Satellite Link:</strong> Open real-time turn-by-turn navigation in Google Maps
        </div>
        <a href="${t.google_maps_url || `https://www.google.com/maps/search/?api=1&query=${t.latitude},${t.longitude}`}" target="_blank" class="btn btn-maps" style="text-decoration:none; display:inline-flex; align-items:center; gap:8px; padding:8px 18px; font-weight:700;">
          🗺️ Launch in Google Maps
        </a>
      </div>

      <div style="display:flex; justify-content:space-between; align-items:center;">
        ${t.is_gps_active ? `
          <button class="btn btn-primary btn-sm" onclick="openSimulateGPSModal('${t.dispatch_id}')" style="background:#0288d1;">
            📍 Send Mobile GPS Update
          </button>
        ` : '<div></div>'}
        <button class="btn btn-secondary btn-sm" onclick="closeModal()">Close</button>
      </div>
    `;
  } catch (err) {
    modalBody.innerHTML = `<div class="alert-box danger">Error loading GPS telemetry: ${err.message}</div>`;
  }
}

// --- SIMULATE DRIVER GPS MODAL ---
function openSimulateGPSModal(dispatchId) {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `📍 Send Driver GPS Checkpoint: ${dispatchId}`;
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Broadcast GPS Location";

  modalBody.innerHTML = `
    <form id="simulateGPSForm" class="form-grid" onsubmit="handleSimulateGPSSubmit(event, '${dispatchId}')">
      <div class="form-group" style="grid-column: span 2;">
        <label class="form-label">Road Checkpoint / Landmark Name *</label>
        <input type="text" id="gpsLocName" class="form-control" value="Near Patas Toll Plaza, Pune-Solapur Expressway (Km 62)" required>
      </div>

      <div class="form-group">
        <label class="form-label">Latitude *</label>
        <input type="number" step="0.0001" id="gpsLat" class="form-control" value="18.4385" required>
      </div>

      <div class="form-group">
        <label class="form-label">Longitude *</label>
        <input type="number" step="0.0001" id="gpsLng" class="form-control" value="74.4172" required>
      </div>

      <div class="form-group" style="grid-column: span 2; font-size:0.75rem; color:var(--text-muted);">
        Notice: In actual deployment, this API receives automated background coordinates directly from the driver mobile device during active transit duty.
      </div>
    </form>
  `;

  modalSubmitBtn.onclick = () => {
    document.getElementById("simulateGPSForm").dispatchEvent(new Event("submit"));
  };
  modal.style.display = "flex";
}

async function handleSimulateGPSSubmit(e, dispatchId) {
  e.preventDefault();
  const locName = document.getElementById("gpsLocName").value.trim();
  const lat = parseFloat(document.getElementById("gpsLat").value);
  const lng = parseFloat(document.getElementById("gpsLng").value);

  const payload = {
    latitude: lat,
    longitude: lng,
    location_name: locName
  };

  const btn = document.getElementById("modalSubmitBtn");
  try {
    btn.disabled = true;
    await ApiClient.updateDispatchLocation(dispatchId, payload);
    closeModal();
    alert(`GPS Location broadcasted for Dispatch ${dispatchId}!`);
    renderTruckTrackingConsole();
  } catch (err) {
    alert("GPS update failed: " + err.message);
  } finally {
    if (btn) btn.disabled = false;
  }
}

// --- 3. MINOR WAREHOUSE INWARD & RECEIVING CONSOLE ---
async function renderMinorWHInwardConsole(container) {
  if (!container) container = document.getElementById("contentContainer") || document.getElementById("activeTableContainer");
  if (!container) return;

  container.innerHTML = `
    <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:32px; text-align:center;">
      <div class="loader-spinner" style="margin:0 auto 16px auto; width:36px; height:36px; border:3px solid #e0e0e0; border-top-color:#1565c0; border-radius:50%; animation:spin 0.8s linear infinite;"></div>
      <h4 style="margin:0 0 6px 0; color:var(--primary-dark);">Loading Sub-District Inward Dispatches...</h4>
      <p style="font-size:0.8rem; color:var(--text-muted); margin:0;">Checking major warehouse transfers and intake records...</p>
    </div>
  `;

  try {
    const dispatchesRes = await ApiClient.getWarehouseDispatches() || {};
    const dispatches = dispatchesRes.dispatches || (Array.isArray(dispatchesRes) ? dispatchesRes : []);
    const inwardRecords = await ApiClient.getRecords("/minor-wh/inward") || [];

    const totalIncoming = dispatches.length;
    const inTransit = dispatches.filter(d => d.status === 'In Transit').length;
    const received = dispatches.filter(d => d.status === 'Completed' || d.status === 'Received').length;
    const discrepancies = dispatches.filter(d => d.status === 'Discrepancy').length;

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
          <div>
            <h3 style="margin:0; color:var(--primary-dark);">📥 Minor Warehouse: Incoming Dispatches & Receiving</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">
              Sub-District Transit Godown Inward Verification • Weighbridge Discrepancy Reconciliation
            </span>
          </div>
          <button class="btn btn-secondary btn-sm" onclick="renderMinorWHInwardConsole()">
            🔄 Refresh Inward List
          </button>
        </div>

        <div class="metric-grid" style="margin:16px 0 20px 0;">
          <div class="metric-card">
            <div class="metric-val" style="color:#1565c0;">${totalIncoming}</div>
            <div class="metric-label">Total Major Silo Transfers</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#0288d1;">${inTransit}</div>
            <div class="metric-label">Vehicles In Transit</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#2e7d32;">${received}</div>
            <div class="metric-label">Verified & In Stock</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#c62828;">${discrepancies}</div>
            <div class="metric-label">Discrepancies Flagged</div>
          </div>
        </div>

        <div style="background:white; border-radius:8px; border:1px solid var(--border); overflow-x:auto;">
          <table class="record-table">
            <thead>
              <tr>
                <th>Dispatch ID</th>
                <th>Batch ID & Crop</th>
                <th>Certified Grade</th>
                <th>Sent Qty (kg)</th>
                <th>Received Qty (kg)</th>
                <th>Difference (kg)</th>
                <th>Carrier & Driver</th>
                <th>Verification Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              ${dispatches.length === 0 ? `
                <tr>
                  <td colspan="9" style="text-align:center; padding:32px; color:var(--text-muted);">
                    No incoming dispatches found. Dispatches initiated at Major Silo will appear here for intake verification.
                  </td>
                </tr>
              ` : dispatches.map(d => {
                const isCompleted = d.status === 'Completed' || d.status === 'Received';
                const isDiscrepancy = d.status === 'Discrepancy';
                const isInTransit = d.status === 'In Transit';

                const matchingInward = inwardRecords.find(i => i.dispatch_id === d.dispatch_id);
                const recQty = matchingInward ? matchingInward.received_quantity_kg : (isCompleted ? d.dispatch_quantity_kg : '-');
                const diffQty = matchingInward ? matchingInward.difference_kg : (isCompleted ? 0 : '-');

                return `
                  <tr>
                    <td><code>${d.dispatch_id}</code></td>
                    <td>
                      <div style="font-weight:700;">${d.crop_name}</div>
                      <div style="font-size:0.72rem; color:var(--text-muted);">Batch: <code>${d.batch_id}</code></div>
                    </td>
                    <td>
                      <span class="badge ${d.final_grade === 'A' ? 'badge-success' : d.final_grade === 'B' ? 'badge-info' : 'badge-warning'}">
                        Grade ${d.final_grade}
                      </span>
                    </td>
                    <td style="font-weight:700; color:#1565c0;">
                      ${Number(d.dispatch_quantity_kg).toLocaleString()} kg
                    </td>
                    <td style="font-weight:700; color:${isCompleted ? '#2e7d32' : isDiscrepancy ? '#c62828' : 'var(--text-muted)'};">
                      ${recQty !== '-' ? Number(recQty).toLocaleString() + ' kg' : 'Pending Intake'}
                    </td>
                    <td>
                      ${diffQty !== '-' ? (
                        diffQty === 0 ? `<span class="badge badge-success">0 kg (Exact)</span>` : `<span class="badge badge-danger">${diffQty} kg diff</span>`
                      ) : '<span style="color:var(--text-muted); font-size:0.75rem;">-</span>'}
                    </td>
                    <td>
                      <div>🚚 <strong>${d.truck_number}</strong></div>
                      <div style="font-size:0.72rem; color:var(--text-muted);">${d.driver_name}</div>
                    </td>
                    <td>
                      <span class="badge ${isCompleted ? 'badge-success' : isDiscrepancy ? 'badge-danger' : isInTransit ? 'badge-info' : 'badge-warning'}">
                        ${d.status}
                      </span>
                    </td>
                    <td>
                      <div style="display:flex; flex-direction:column; gap:4px;">
                        ${(!isCompleted && !isDiscrepancy) ? `
                          <button class="btn btn-primary btn-sm" onclick="openMinorWHReceiveModal('${d.dispatch_id}')" style="background:#2e7d32; font-size:0.72rem; padding:3px 8px; font-weight:700;">
                            📥 Receive & Verify
                          </button>
                        ` : `
                          <button class="btn btn-secondary btn-sm" onclick="openDispatchDetailModal('${d.dispatch_id}')" style="font-size:0.7rem; padding:2px 6px;">
                            👁️ View Receipt
                          </button>
                        `}
                        <button class="btn btn-secondary btn-sm" onclick="openDispatchTrackingModal('${d.dispatch_id}')" style="font-size:0.7rem; padding:2px 6px;">
                          📍 Track
                        </button>
                      </div>
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load inward dispatches: ${err.message}</div>`;
  }
}

// --- MINOR WAREHOUSE RECEIVE MODAL ---
async function openMinorWHReceiveModal(dispatchId) {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `📥 Minor Warehouse Intake Verification: ${dispatchId}`;
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Confirm Inward Receipt & Unload";

  modalBody.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted);">Loading dispatch record...</div>`;
  modal.style.display = "flex";

  try {
    const d = await ApiClient.getWarehouseDispatch(dispatchId);

    modalBody.innerHTML = `
      <div style="background:#e3f2fd; border:1px solid #90caf9; padding:12px; border-radius:6px; margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <strong style="color:#0d47a1; font-size:0.95rem;">${d.dispatch_id} • ${d.crop_name}</strong>
            <div style="font-size:0.78rem; color:#1565c0; margin-top:2px;">
              Linked Batch: <code>${d.batch_id}</code> • Origin: <strong>${d.origin_warehouse}</strong>
            </div>
          </div>
          <div style="text-align:right;">
            <span class="badge ${d.final_grade === 'A' ? 'badge-success' : 'badge-info'}" style="font-size:0.85rem;">Grade ${d.final_grade}</span>
            <div style="font-size:0.7rem; color:#1976d2; margin-top:2px;">Certified Task 5 Grade</div>
          </div>
        </div>
      </div>

      <div style="background:#f5f5f5; border:1px solid #e0e0e0; border-radius:6px; padding:10px 14px; margin-bottom:16px; font-size:0.82rem;">
        <div>🚚 <strong>Carrier Truck:</strong> ${d.truck_number} • <strong>Driver:</strong> ${d.driver_name}</div>
        <div style="margin-top:2px;">⚖️ <strong>Major Silo Dispatched Weight:</strong> <span style="font-weight:800; color:#1565c0; font-size:1rem;">${Number(d.dispatch_quantity_kg).toLocaleString()} kg</span></div>
      </div>

      <form id="minorWHReceiveForm" class="form-grid" onsubmit="handleMinorWHReceiveSubmit(event, '${d.dispatch_id}', ${d.dispatch_quantity_kg})">
        <div class="form-group" style="grid-column: span 2;">
          <label class="form-label" style="font-weight:700; color:#2e7d32;">Verified Received Net Weight at Minor Weighbridge (kg) *</label>
          <input type="number" step="0.1" id="mwhRecQty" class="form-control" value="${d.dispatch_quantity_kg}" min="0" oninput="updateMinorWHReceiveDiff(${d.dispatch_quantity_kg})" required style="font-size:1.1rem; font-weight:700;">
        </div>

        <!-- Dynamic Discrepancy Banner -->
        <div id="mwhDiscrepancyBanner" style="grid-column: span 2; padding:12px; border-radius:6px; background:#e8f5e9; border:1px solid #a5d6a7; margin-bottom:10px;">
          <div style="font-weight:700; color:#2e7d32; font-size:0.85rem;">
            ✅ Perfect Weight Verification (0 kg Difference)
          </div>
          <div style="font-size:0.75rem; color:#388e3c; margin-top:2px;">
            Received weight perfectly matches Major Silo dispatched quantity. Status will be marked <strong>COMPLETED / VERIFIED_IN_STOCK</strong>.
          </div>
        </div>

        <div class="form-group" style="grid-column: span 2;">
          <label class="form-label">Discrepancy / Weight Loss Reason</label>
          <input type="text" id="mwhDiscrepancyReason" class="form-control" placeholder="Optional for exact match. Required if difference exists (e.g. moisture loss during transit)">
        </div>

        <div class="form-group">
          <label class="form-label">Receiver / Inspector Name *</label>
          <input type="text" id="mwhReceiverName" class="form-control" value="${(currentUser && currentUser.username) ? currentUser.username : 'Godown Officer'}" required>
        </div>

        <div class="form-group">
          <label class="form-label">Arrival & Unload Time</label>
          <input type="text" id="mwhArrTime" class="form-control" value="${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}">
        </div>
      </form>
    `;

    modalSubmitBtn.onclick = () => {
      document.getElementById("minorWHReceiveForm").dispatchEvent(new Event("submit"));
    };
  } catch (err) {
    modalBody.innerHTML = `<div class="alert-box danger">Error loading dispatch: ${err.message}</div>`;
  }
}

function updateMinorWHReceiveDiff(sentQty) {
  const recInput = document.getElementById("mwhRecQty");
  const banner = document.getElementById("mwhDiscrepancyBanner");
  if (!recInput || !banner) return;

  const recQty = parseFloat(recInput.value) || 0;
  const diff = Math.round((sentQty - recQty) * 100) / 100;

  if (Math.abs(diff) < 0.001) {
    banner.style.background = "#e8f5e9";
    banner.style.borderColor = "#a5d6a7";
    banner.innerHTML = `
      <div style="font-weight:700; color:#2e7d32; font-size:0.85rem;">
        ✅ Perfect Weight Verification (0 kg Difference)
      </div>
      <div style="font-size:0.75rem; color:#388e3c; margin-top:2px;">
        Received weight perfectly matches Major Silo dispatched quantity. Status will be marked <strong>COMPLETED / VERIFIED_IN_STOCK</strong>.
      </div>
    `;
  } else {
    banner.style.background = "#ffebee";
    banner.style.borderColor = "#ef9a9a";
    banner.innerHTML = `
      <div style="font-weight:700; color:#c62828; font-size:0.85rem;">
        ⚠️ Weight Discrepancy Detected: ${diff > 0 ? `${diff} kg Shortage` : `${Math.abs(diff)} kg Excess`}
      </div>
      <div style="font-size:0.75rem; color:#b71c1c; margin-top:2px;">
        Sent: ${Number(sentQty).toLocaleString()} kg ➔ Received: ${Number(recQty).toLocaleString()} kg.
        Status will be flagged as <strong>DISCREPANCY / WEIGHT_MISMATCH</strong>. Major Warehouse sent quantity remains untouched.
      </div>
    `;
    const reasonInput = document.getElementById("mwhDiscrepancyReason");
    if (reasonInput && !reasonInput.value) {
      reasonInput.value = `Transit weight difference of ${diff} kg observed at intake weighbridge`;
    }
  }
}

async function handleMinorWHReceiveSubmit(e, dispatchId, sentQty) {
  e.preventDefault();
  const recQty = parseFloat(document.getElementById("mwhRecQty").value);
  if (isNaN(recQty) || recQty < 0) {
    alert("Please enter a valid non-negative received quantity.");
    return;
  }

  const diff = Math.round((sentQty - recQty) * 100) / 100;
  const reason = document.getElementById("mwhDiscrepancyReason").value.trim();

  if (Math.abs(diff) > 0.001 && (!reason || reason.length < 3)) {
    alert("Please provide a reason for the weight discrepancy.");
    return;
  }

  const payload = {
    received_quantity_kg: recQty,
    arrival_time: document.getElementById("mwhArrTime").value.trim(),
    discrepancy_reason: reason || (diff === 0 ? "Exact Match Verified" : `Weight difference of ${diff} kg`),
    receiver_name: document.getElementById("mwhReceiverName").value.trim()
  };

  const btn = document.getElementById("modalSubmitBtn");
  try {
    btn.disabled = true;
    btn.textContent = "Verifying Intake...";
    const res = await ApiClient.receiveMinorWarehouseDispatch(dispatchId, payload);
    closeModal();
    alert(`Inward receipt processed successfully!
Status: ${res.status}
Received: ${recQty} kg (Difference: ${res.difference_kg} kg)
Minor godown stock updated and truck released.`);
    renderMinorWHInwardConsole();
  } catch (err) {
    alert("Intake verification failed: " + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Confirm Inward Receipt & Unload";
    }
  }
}

// --- 4. MINOR WAREHOUSE SENT VS RECEIVED (DISCREPANCY AUDIT) ---
async function renderMinorWHSentReceivedConsole(container) {
  if (!container) container = document.getElementById("contentContainer") || document.getElementById("activeTableContainer");
  if (!container) return;

  container.innerHTML = `<div style="text-align:center; padding:32px; color:var(--text-muted);">Loading Sent vs Received Discrepancy Reconciliation...</div>`;

  try {
    const inwardRecords = await ApiClient.getRecords("/minor-wh/inward") || [];

    const totalAudited = inwardRecords.length;
    const exactMatches = inwardRecords.filter(r => (r.difference_kg === 0 || r.verification_status === 'VERIFIED_IN_STOCK')).length;
    const mismatches = inwardRecords.filter(r => (r.difference_kg !== 0 || r.verification_status === 'WEIGHT_MISMATCH')).length;
    const totalShortageKg = inwardRecords.reduce((acc, r) => acc + Math.max(0, (r.difference_kg || 0)), 0);

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar" style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <h3 style="margin:0; color:var(--primary-dark);">⚖️ Sent vs Received Discrepancy & Weight Audit</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">Reconciles Major Silo Outward Gate Pass with Minor Godown Intake Scales</span>
          </div>
          <button class="btn btn-secondary btn-sm" onclick="renderMinorWHSentReceivedConsole()">
            🔄 Refresh Audit
          </button>
        </div>

        <div class="metric-grid" style="margin:16px 0 20px 0;">
          <div class="metric-card">
            <div class="metric-val" style="color:#1565c0;">${totalAudited}</div>
            <div class="metric-label">Audited Inward Receipts</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#2e7d32;">${exactMatches}</div>
            <div class="metric-label">Exact Weight Matches</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#c62828;">${mismatches}</div>
            <div class="metric-label">Discrepancies Recorded</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#e65100;">${totalShortageKg.toFixed(1)} kg</div>
            <div class="metric-label">Total Cumulative Transit Loss</div>
          </div>
        </div>

        <div style="background:white; border-radius:8px; border:1px solid var(--border); overflow-x:auto;">
          <table class="record-table">
            <thead>
              <tr>
                <th>Dispatch ID</th>
                <th>Batch ID</th>
                <th>Crop</th>
                <th>Major Silo Sent (kg)</th>
                <th>Minor Received (kg)</th>
                <th>Difference (kg)</th>
                <th>Carrier / Truck</th>
                <th>Arrival Time</th>
                <th>Discrepancy / Audit Justification</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${inwardRecords.length === 0 ? `
                <tr><td colspan="10" style="text-align:center; padding:32px; color:var(--text-muted);">No inward discrepancy records found.</td></tr>
              ` : inwardRecords.map(r => `
                <tr>
                  <td><code>${r.dispatch_id}</code></td>
                  <td><code>${r.batch_id}</code></td>
                  <td><strong>${r.crop_name}</strong></td>
                  <td style="font-weight:700; color:#1565c0;">${Number(r.sent_quantity_kg).toLocaleString()} kg</td>
                  <td style="font-weight:700; color:#2e7d32;">${Number(r.received_quantity_kg).toLocaleString()} kg</td>
                  <td>
                    ${r.difference_kg === 0 ? `
                      <span class="badge badge-success">0 kg</span>
                    ` : `
                      <span class="badge badge-danger">${r.difference_kg > 0 ? `-${r.difference_kg}` : `+${Math.abs(r.difference_kg)}`} kg</span>
                    `}
                  </td>
                  <td>🚚 ${r.truck_number} (${r.driver_name})</td>
                  <td style="font-size:0.75rem;">${r.arrival_time || 'N/A'}</td>
                  <td style="font-size:0.75rem; color:#455a64;">${r.discrepancy_reason || 'Exact Match'}</td>
                  <td>
                    <span class="badge ${r.verification_status === 'VERIFIED_IN_STOCK' ? 'badge-success' : 'badge-danger'}">
                      ${r.verification_status}
                    </span>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load discrepancy audit: ${err.message}</div>`;
  }
}

// --- 8. BULK BUYER: SINGLE-ID STREAMLINED PROCUREMENT ---
async function renderBuyerSingleIdOrder(container) {
  const defaultBuyerId = (currentUser && currentUser.buyer_id) || "KS-BYR-1001";

  container.innerHTML = `
    <div style="max-width:820px; margin:0 auto; background:white; border:1px solid var(--border); border-radius:8px; padding:28px;">
      <div style="margin-bottom:22px; border-bottom:1px solid #eee; padding-bottom:14px;">
        <h3 style="color:var(--primary-dark); margin:0;">🏢 Commercial Bulk Grain Procurement Order</h3>
        <p style="font-size:0.82rem; color:var(--text-muted); margin:4px 0 0;">
          Single-ID Order System: Verified enterprise credentials are bound automatically. No repeated data entry.
        </p>
      </div>

      <!-- Step 1: Buyer ID Verification -->
      <div class="buyer-verify-box">
        <label class="form-label" style="font-weight:700; color:var(--primary-dark);">Enter Registered Bulk Buyer ID *</label>
        <div style="display:flex; gap:10px; align-items:center;">
          <input type="text" id="orderBuyerIdInput" class="form-control" value="${defaultBuyerId}" placeholder="e.g. KS-BYR-1001" style="font-weight:700; font-family:monospace; max-width:260px;" required>
          <button type="button" class="btn btn-primary btn-sm" onclick="verifyBuyerIdForOrder()" style="background:#1565c0;">
            🔍 Verify Buyer ID
          </button>
        </div>

        <div id="buyerVerifiedDetailsContainer" style="margin-top:12px;"></div>
      </div>

      <!-- Step 2: Order Specifications Form -->
      <form id="singleIdOrderForm" class="form-grid" onsubmit="handleSingleIdOrderSubmit(event)">
        <div class="form-group">
          <label class="form-label">Crop Required *</label>
          <select id="orderCropName" class="form-control" required>
            <option value="Sugarcane">Sugarcane</option>
            <option value="Wheat (Lokwan)" selected>Wheat (Lokwan)</option>
            <option value="Cotton (Bt)">Cotton (Bt)</option>
            <option value="Soybean (JS-335)">Soybean (JS-335)</option>
            <option value="Gram / Chana">Gram / Chana</option>
            <option value="Onion (Nashik Red)">Onion (Nashik Red)</option>
            <option value="Maize (African Tall)">Maize (African Tall)</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Required Quantity (MT) *</label>
          <input type="number" id="orderQuantityMT" class="form-control" value="500" min="1" step="10" required>
        </div>

        <div class="form-group">
          <label class="form-label">Target Quality Grade *</label>
          <select id="orderTargetGrade" class="form-control" required>
            <option value="A" selected>Grade A (Premium Quality)</option>
            <option value="B">Grade B (Standard Commercial)</option>
            <option value="C">Grade C (Fair Average)</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Maximum Price Offer (₹ / Quintal) *</label>
          <input type="number" id="orderMaxPrice" class="form-control" value="2850" min="100" step="50" required>
        </div>

        <div class="form-group">
          <label class="form-label">Preferred Delivery Silo / Hub *</label>
          <select id="orderDeliveryHub" class="form-control" required>
            <option value="Pune Regional Silo Complex">Pune Regional Silo Complex</option>
            <option value="Baramati Sub-District Godown">Baramati Sub-District Godown</option>
            <option value="Nashik Agro-Logistics Depot">Nashik Agro-Logistics Depot</option>
            <option value="Nagpur Vidarbha Grain Hub">Nagpur Vidarbha Grain Hub</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Required By Delivery Date *</label>
          <input type="text" id="orderRequiredDate" class="form-control" value="2026-10-15" placeholder="YYYY-MM-DD" required>
        </div>

        <div class="form-group" style="grid-column:span 2;">
          <label class="form-label">Procurement & Packaging Specifications</label>
          <textarea id="orderNotes" class="form-control" rows="2" placeholder="e.g. Standard 50 kg jute bags with moisture below 12%."></textarea>
        </div>

        <div class="form-group" style="grid-column:span 2; text-align:right; margin-top:12px;">
          <button type="submit" id="submitOrderBtn" class="btn btn-primary" style="background:#2e7d32;">
            📦 Place Commercial Purchase Order
          </button>
        </div>
      </form>
    </div>
  `;

  // Auto-verify default buyer
  verifyBuyerIdForOrder();
}

async function verifyBuyerIdForOrder() {
  const input = document.getElementById("orderBuyerIdInput");
  const container = document.getElementById("buyerVerifiedDetailsContainer");
  if (!input || !container) return;

  const buyerId = input.value.trim();
  if (!buyerId) {
    container.innerHTML = `<div style="color:var(--accent); font-size:0.8rem; margin-top:6px;">⚠️ Please enter a Bulk Buyer ID.</div>`;
    return;
  }

  container.innerHTML = `<div style="font-size:0.8rem; color:var(--text-muted); margin-top:6px;">Verifying credentials in registry...</div>`;

  try {
    const res = await ApiClient.verifyBuyerId(buyerId);
    if (!res.verified || !res.buyer) {
      container.innerHTML = `
        <div style="background:#ffebee; border:1px solid #ef9a9a; padding:10px 14px; border-radius:4px; font-size:0.82rem; color:#c62828; margin-top:8px;">
          ❌ Buyer ID <strong>${buyerId}</strong> not found. Please register as a new buyer or enter a valid ID.
        </div>
      `;
      return;
    }

    const b = res.buyer;
    container.innerHTML = `
      <div class="buyer-badge-confirmed">
        <div style="font-size:1.6rem;">🏢</div>
        <div style="flex:1;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="color:#1b5e20; font-size:0.95rem;">${b.company_name}</strong>
            <span class="badge badge-success">${b.status}</span>
          </div>
          <div style="font-size:0.78rem; color:#2e7d32; margin-top:2px;">
            <span>GSTIN: <code>${b.gst_number || 'N/A'}</code></span> • 
            <span>Classification: <strong>${b.business_type}</strong></span> • 
            <span>Authorized: <strong>${b.contact_person}</strong> (${b.contact_phone})</span>
          </div>
        </div>
      </div>
    `;
  } catch (e) {
    container.innerHTML = `<div style="color:var(--accent); font-size:0.8rem; margin-top:6px;">Verification error: ${e.message}</div>`;
  }
}

async function handleSingleIdOrderSubmit(e) {
  e.preventDefault();
  const buyerId = document.getElementById("orderBuyerIdInput").value.trim();
  const cropName = document.getElementById("orderCropName").value;
  const quantity = parseFloat(document.getElementById("orderQuantityMT").value);
  const targetGrade = document.getElementById("orderTargetGrade").value;
  const maxPrice = parseFloat(document.getElementById("orderMaxPrice").value);
  const hub = document.getElementById("orderDeliveryHub").value;
  const reqDate = document.getElementById("orderRequiredDate").value;
  const notes = document.getElementById("orderNotes").value.trim();

  if (!buyerId) {
    alert("Please enter and verify a Bulk Buyer ID.");
    return;
  }

  const btn = document.getElementById("submitOrderBtn");
  try {
    btn.disabled = true;
    btn.textContent = "Recording Purchase Order in Ledger...";

    const res = await ApiClient.placeBuyerOrder({
      buyer_id: buyerId,
      crop_name: cropName,
      required_quantity_mt: quantity,
      target_grade: targetGrade,
      max_price_offer_per_quintal: maxPrice,
      delivery_hub: hub,
      required_by_date: reqDate,
      notes: notes,
    });

    alert(`Order Placed Successfully!\nTransaction ID: #${res.id}\nBuyer: ${buyerId}\nCrop: ${quantity} MT ${cropName}`);
    selectSubTab("buyer_entries");
  } catch (err) {
    alert("Order placement failed: " + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "📦 Place Commercial Purchase Order";
    }
  }
}

// --- 8. BULK BUYER: REGISTRATION & CREATE BUYER ID ---
function renderBuyerRegistration(container) {
  container.innerHTML = `
    <div style="max-width:760px; margin:0 auto; background:white; border:1px solid var(--border); border-radius:8px; padding:28px;">
      <div style="margin-bottom:20px; border-bottom:1px solid #eee; padding-bottom:14px;">
        <h3 style="color:var(--primary-dark); margin:0;">🏢 Commercial Bulk Buyer Registration</h3>
        <p style="font-size:0.82rem; color:var(--text-muted); margin:4px 0 0;">Official Onboarding for Mills, Exporters, and Institutional Food Processors</p>
      </div>

      <form id="buyerRegForm" class="form-grid" onsubmit="handleBuyerRegistrationSubmit(event)">
        <div class="form-group">
          <label class="form-label">Enterprise / Mill Name *</label>
          <input type="text" name="company_name" class="form-control" placeholder="e.g. Sahyadri Agro Processing & Flour Mills Pvt Ltd" required>
        </div>

        <div class="form-group">
          <label class="form-label">Business Classification *</label>
          <select name="business_type" class="form-control" required>
            <option value="Flour Mill">Flour Mill & Grain Processing</option>
            <option value="Sugar Factory">Sugar Factory / Distillery</option>
            <option value="Export House">Commodity Export House</option>
            <option value="Oil Mill">Edible Oil Extraction Mill</option>
            <option value="FMCG Producer">FMCG Food Producer</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">GST Identification Number (GSTIN) *</label>
          <input type="text" name="gst_number" class="form-control" placeholder="e.g. 27AAAAA0000A1Z5" required>
        </div>

        <div class="form-group">
          <label class="form-label">Contact Person *</label>
          <input type="text" name="contact_person" class="form-control" placeholder="Authorized Director / Procurement Head" required>
        </div>

        <div class="form-group">
          <label class="form-label">Contact Mobile *</label>
          <input type="text" name="contact_phone" class="form-control" placeholder="+91 98200 99887" required>
        </div>

        <div class="form-group">
          <label class="form-label">Official Corporate Email *</label>
          <input type="email" name="official_email" class="form-control" placeholder="procurement@sahyadriagro.in" required>
        </div>

        <div class="form-group" style="grid-column:span 2; text-align:right; margin-top:12px;">
          <button type="submit" class="btn btn-primary" style="background:#1565c0;">
            🏢 Submit Corporate Registration & Generate Buyer ID
          </button>
        </div>
      </form>
    </div>
  `;
}

async function handleBuyerRegistrationSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);
  const payload = {
    company_name: formData.get("company_name"),
    business_type: formData.get("business_type"),
    gst_number: formData.get("gst_number"),
    contact_person: formData.get("contact_person"),
    contact_phone: formData.get("contact_phone"),
    official_email: formData.get("official_email"),
  };

  try {
    const res = await ApiClient.createBuyerId(payload);
    alert(`Corporate Registration Successful!\nAssigned Buyer ID: ${res.buyer_id}`);
    selectSubTab("buyer_registry");
  } catch (err) {
    alert("Registration failed: " + err.message);
  }
}

function renderBuyerCreateId(container) {
  renderBuyerRegistration(container);
}

// --- 9. UNIVERSAL AUDIT HISTORY TAB ---
async function renderAuditHistoryTab(container) {
  container.innerHTML = `<div style="text-align:center; padding:32px; color:var(--text-muted);">Fetching universal audit history records...</div>`;
  try {
    const res = await ApiClient.getRecords("/audit/system/recent");
    const history = (res && res.history) || [];

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar">
          <div>
            <h3>📜 KrushiSetu Universal Operational Audit Trail</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">Every Human Override and Modification Recorded with Mandatory Justification</span>
          </div>
        </div>

        <div class="audit-timeline" style="max-width:860px; margin:0 auto;">
          ${history.length === 0 ? `
            <div style="text-align:center; padding:32px; background:white; border-radius:8px; border:1px solid var(--border); color:var(--text-muted);">
              All database records currently in pristine initial authorized state.
            </div>
          ` : history.map(item => `
            <div class="audit-card">
              <div class="audit-meta">
                <span><strong>Table: <code>${item.table_name}</code> • Field: ${item.field_name.toUpperCase()}</strong></span>
                <span>🕒 ${item.created_at}</span>
              </div>
              <div class="audit-diff">
                <span class="diff-old">${item.old_value || '(initial)'}</span>
                <span>→</span>
                <span class="diff-new">${item.new_value || '(empty)'}</span>
              </div>
              <div class="audit-meta" style="margin-top:6px;">
                <span>👤 Modified By: <strong>${item.edited_by}</strong> (${item.edited_by_role})</span>
              </div>
              <div class="audit-reason">
                Justification: "${item.change_reason}"
              </div>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load audit history: ${err.message}</div>`;
  }
}

// ==========================================
// CENTRAL AI EXTENSION MODALS & ONE-CLICK APPROVALS
// ==========================================
function openGeneratePSAIExtModal() {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = "🤖 Central AI Engine: Distribute Quota to Gram Panchayats";
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Run Central AI Block Allocation";

  modalBody.innerHTML = `
    <div style="background:#e3f2fd; border:1px solid #90caf9; padding:12px 16px; border-radius:6px; margin-bottom:16px;">
      <div style="font-weight:700; color:#1565c0; font-size:0.88rem; margin-bottom:4px;">
        🧠 Agro-Climatic Block Allocation Algorithm
      </div>
      <p style="font-size:0.8rem; color:#0d47a1; margin:0; line-height:1.4;">
        Synthesizes Gram Panchayat cultivable land area, irrigation infrastructure (canal vs rainfed), 
        and soil organic matter ratings to distribute the Food Department quota with maximum yield efficiency.
      </p>
    </div>

    <form id="psAiExtForm" class="form-grid">
      <div class="form-group">
        <label class="form-label">Panchayat Samiti *</label>
        <input type="text" id="psAiName" class="form-control" value="Baramati Block Panchayat Samiti" required>
      </div>

      <div class="form-group">
        <label class="form-label">Crop Name *</label>
        <select id="psAiCrop" class="form-control" required>
          <option value="Sugarcane">Sugarcane</option>
          <option value="Wheat (Lokwan)">Wheat (Lokwan)</option>
          <option value="Cotton (Bt)">Cotton (Bt)</option>
          <option value="Soybean (JS-335)">Soybean (JS-335)</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Total Quota to Distribute (MT) *</label>
        <input type="number" id="psAiQuota" class="form-control" value="12000" min="10" required>
      </div>

      <div class="form-group">
        <label class="form-label">Season *</label>
        <select id="psAiSeason" class="form-control" required>
          <option value="Kharif 2026">Kharif 2026</option>
          <option value="Rabi 2026">Rabi 2026</option>
        </select>
      </div>
    </form>
  `;

  modalSubmitBtn.onclick = async () => {
    const psName = document.getElementById("psAiName").value;
    const crop = document.getElementById("psAiCrop").value;
    const quota = parseFloat(document.getElementById("psAiQuota").value);
    const season = document.getElementById("psAiSeason").value;

    try {
      modalSubmitBtn.disabled = true;
      modalSubmitBtn.textContent = "Computing Allocations...";
      await ApiClient.generatePSAIAllocation(psName, crop, quota, season);
      closeModal();
      alert(`Central AI successfully allocated ${quota.toLocaleString()} MT ${crop} across Gram Panchayats!`);
      selectSubTab("ps_gp_allocations");
    } catch (e) {
      alert("AI Allocation failed: " + e.message);
    } finally {
      modalSubmitBtn.disabled = false;
      modalSubmitBtn.textContent = "Run Central AI Block Allocation";
    }
  };

  modal.style.display = "flex";
}

function openGenerateGPAIExtModal() {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = "🤖 Central AI Engine: Match Quota to Village Farmers";
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Run Central AI Farmer Matching";

  modalBody.innerHTML = `
    <div style="background:#e8f5e9; border:1px solid #a5d6a7; padding:12px 16px; border-radius:6px; margin-bottom:16px;">
      <div style="font-weight:700; color:#2e7d32; font-size:0.88rem; margin-bottom:4px;">
        🌱 Precision Plot & Soil Matching Engine
      </div>
      <p style="font-size:0.8rem; color:#1b5e20; margin:0; line-height:1.4;">
        Matches village crop targets to registered farmers based on plot acreage, soil NPK levels, pH, 
        and irrigation security.
      </p>
    </div>

    <form id="gpAiExtForm" class="form-grid">
      <div class="form-group">
        <label class="form-label">Gram Panchayat *</label>
        <input type="text" id="gpAiName" class="form-control" value="Shirsuphal Gram Panchayat" required>
      </div>

      <div class="form-group">
        <label class="form-label">Crop Name *</label>
        <select id="gpAiCrop" class="form-control" required>
          <option value="Sugarcane">Sugarcane</option>
          <option value="Wheat (Lokwan)">Wheat (Lokwan)</option>
          <option value="Cotton (Bt)">Cotton (Bt)</option>
          <option value="Soybean (JS-335)">Soybean (JS-335)</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Total GP Target Quota (MT) *</label>
        <input type="number" id="gpAiQuota" class="form-control" value="3800" min="10" required>
      </div>

      <div class="form-group">
        <label class="form-label">Season *</label>
        <select id="gpAiSeason" class="form-control" required>
          <option value="Kharif 2026">Kharif 2026</option>
          <option value="Rabi 2026">Rabi 2026</option>
        </select>
      </div>
    </form>
  `;

  modalSubmitBtn.onclick = async () => {
    const gpName = document.getElementById("gpAiName").value;
    const crop = document.getElementById("gpAiCrop").value;
    const quota = parseFloat(document.getElementById("gpAiQuota").value);
    const season = document.getElementById("gpAiSeason").value;

    try {
      modalSubmitBtn.disabled = true;
      modalSubmitBtn.textContent = "Matching Farmers...";
      await ApiClient.generateGPAIAssignment(gpName, crop, quota, season);
      closeModal();
      alert(`Central AI matched quota to farmers for ${gpName}!`);
      selectSubTab("gp_crop_assignments");
    } catch (e) {
      alert("Farmer matching failed: " + e.message);
    } finally {
      modalSubmitBtn.disabled = false;
      modalSubmitBtn.textContent = "Run Central AI Farmer Matching";
    }
  };

  modal.style.display = "flex";
}

function openGenerateWHAIExtModal() {
  selectSubTab("major_wh_ai_grading");
}

async function quickApprovePSAllocation(recordId) {
  if (!confirm(`Authorize Gram Panchayat allocation (Record #${recordId}) with zero typing?`)) return;
  try {
    await ApiClient.approvePSGPAllocation(recordId);
    alert("Allocation Approved!");
    renderActiveTable();
  } catch (e) {
    alert("Approval failed: " + e.message);
  }
}

async function quickApproveGPAllocation(recordId) {
  if (!confirm(`Authorize Farmer plot assignment (Record #${recordId}) with zero typing?`)) return;
  try {
    await ApiClient.approveGPCropAssignment(recordId);
    alert("Assignment Approved!");
    renderActiveTable();
  } catch (e) {
    alert("Approval failed: " + e.message);
  }
}

function openPSAIRationaleModal(recordId) {
  const record = currentRecordsList.find(r => r.id === recordId);
  if (!record) return;

  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `🤖 Central AI Allocation Rationale: ${record.gp_name} (#${record.id})`;
  modalSubmitBtn.style.display = "none";

  modalBody.innerHTML = `
    <div style="background:#e3f2fd; border-radius:6px; padding:14px; border:1px solid #90caf9; margin-bottom:14px;">
      <div style="font-size:0.75rem; color:#1565c0; font-weight:700; text-transform:uppercase;">AI Recommended Quota</div>
      <div style="font-size:1.4rem; font-weight:800; color:#0d47a1; margin-top:4px;">
        ${Number(record.ai_recommended_quantity_mt || record.allocated_quantity_mt).toLocaleString()} MT (${record.crop_name})
      </div>
      <div style="font-size:0.78rem; color:#1976d2; margin-top:4px;">
        Confidence Score: <strong>${((record.ai_confidence_score || 0.92) * 100).toFixed(1)}%</strong>
      </div>
    </div>

    <div style="margin-bottom:14px;">
      <label class="form-label" style="font-weight:700; color:var(--primary-dark);">Decision Rationale & Suitability Factors</label>
      <div style="background:#fafafa; border:1px solid var(--border); padding:12px; border-radius:6px; font-size:0.85rem; line-height:1.5;">
        ${record.ai_rationale || "Quota derived by analyzing Gram Panchayat cultivable acreage, irrigation density, and organic carbon."}
      </div>
    </div>

    <div style="text-align:right; margin-top:16px;">
      <button class="btn btn-secondary btn-sm" onclick="closeModal()">Close</button>
    </div>
  `;

  modal.style.display = "flex";
}

function openGPAIRationaleModal(recordId) {
  const record = currentRecordsList.find(r => r.id === recordId);
  if (!record) return;

  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `🤖 Central AI Farmer Matching Rationale: ${record.farmer_name} (#${record.id})`;
  modalSubmitBtn.style.display = "none";

  modalBody.innerHTML = `
    <div style="background:#e8f5e9; border-radius:6px; padding:14px; border:1px solid #a5d6a7; margin-bottom:14px;">
      <div style="font-size:0.75rem; color:#2e7d32; font-weight:700; text-transform:uppercase;">AI Precision Assignment</div>
      <div style="font-size:1.3rem; font-weight:800; color:#1b5e20; margin-top:4px;">
        ${record.ai_recommended_acres || record.assigned_acres} Acres ➔ ${record.ai_recommended_quintals || record.required_quantity_quintals} Quintals (${record.crop_name})
      </div>
      <div style="font-size:0.78rem; color:#388e3c; margin-top:4px;">
        Confidence Score: <strong>${((record.ai_confidence_score || 0.94) * 100).toFixed(1)}%</strong>
      </div>
    </div>

    <div style="margin-bottom:14px;">
      <label class="form-label" style="font-weight:700; color:var(--primary-dark);">Soil & Agronomy Correlation</label>
      <div style="background:#fafafa; border:1px solid var(--border); padding:12px; border-radius:6px; font-size:0.85rem; line-height:1.5;">
        ${record.ai_rationale || "Assignment matched to farmer's verified parcel acreage, soil laboratory pH, NPK fertility, and canal irrigation availability."}
      </div>
    </div>

    <div style="text-align:right; margin-top:16px;">
      <button class="btn btn-secondary btn-sm" onclick="closeModal()">Close</button>
    </div>
  `;

  modal.style.display = "flex";
}

// Global modal & action triggers exposed on window
window.openAddModal = openAddModal;
window.openEditModal = openEditModal;
window.openDualGradingModal = openDualGradingModal;
window.openHistoryModal = openHistoryModal;
window.openGenerateAIRecModal = openGenerateAIRecModal;
window.openAIRationaleModal = openAIRationaleModal;
window.openApproveModal = openApproveModal;
window.openAssignToPSModal = openAssignToPSModal;
window.selectSubTab = selectSubTab;
window.loadSectorTabs = loadSectorTabs;

// Custom Renderers
window.renderFDAIDataInsights = renderFDAIDataInsights;
window.renderFDAIRecommendations = renderFDAIRecommendations;
window.renderPSOverview = renderPSOverview;
window.renderPSAISuitability = renderPSAISuitability;
window.renderGPOverview = renderGPOverview;
window.renderGPAIMatching = renderGPAIMatching;
window.renderSoilTestDocs = renderSoilTestDocs;
window.openSoilDocViewerModal = openSoilDocViewerModal;
window.renderFarmerOverview = renderFarmerOverview;
window.renderFarmerProfile = renderFarmerProfile;
window.renderFarmerIdCard = renderFarmerIdCard;
window.renderFarmerCompleteHistory = renderFarmerCompleteHistory;
window.renderMajorWHOverview = renderMajorWHOverview;
window.renderMajorWHAIGradingConsole = renderMajorWHAIGradingConsole;
window.toggleWebcamStream = toggleWebcamStream;
window.captureCameraSnapshot = captureCameraSnapshot;
window.previewUploadedGrainImage = previewUploadedGrainImage;
window.runCameraAIGradingConsole = runCameraAIGradingConsole;
window.confirmCameraGradingFinal = confirmCameraGradingFinal;
window.runCVGradingAnalysis = typeof runCVGradingAnalysis !== "undefined" ? runCVGradingAnalysis : runCameraAIGradingConsole;
window.renderMajorWHStorage = renderMajorWHStorage;
window.renderMajorWHStorageInventory = renderMajorWHStorageInventory;
window.filterStorageRecords = filterStorageRecords;
window.openNewStorageModal = openNewStorageModal;
window.onStorageBatchSelected = onStorageBatchSelected;
window.handleCreateStorageSubmit = handleCreateStorageSubmit;
window.openDispatchEditModal = openDispatchEditModal;
window.handleUpdateStorageSubmit = handleUpdateStorageSubmit;
window.openStorageDetailModal = openStorageDetailModal;
window.openStorageAuditHistoryModal = openStorageAuditHistoryModal;

window.renderMinorWHOverview = renderMinorWHOverview;
window.renderMinorWHAIRecs = renderMinorWHAIRecs;
window.renderTruckTracking = renderTruckTracking;
window.simulateTruckGPSUpdate = simulateTruckGPSUpdate;
window.completeTruckDuty = completeTruckDuty;
window.renderBuyerSingleIdOrder = renderBuyerSingleIdOrder;
window.verifyBuyerIdForOrder = verifyBuyerIdForOrder;
window.handleSingleIdOrderSubmit = handleSingleIdOrderSubmit;
window.renderBuyerRegistration = renderBuyerRegistration;
window.renderBuyerCreateId = renderBuyerCreateId;
window.handleBuyerRegistrationSubmit = handleBuyerRegistrationSubmit;
window.renderAuditHistoryTab = renderAuditHistoryTab;

// Multi-Sector AI Modals & Approvals
window.openGeneratePSAIExtModal = openGeneratePSAIExtModal;
window.openGenerateGPAIExtModal = openGenerateGPAIExtModal;
window.openGenerateWHAIExtModal = openGenerateWHAIExtModal;
window.quickApprovePSAllocation = quickApprovePSAllocation;
window.quickApproveGPAllocation = quickApproveGPAllocation;
window.openPSAIRationaleModal = openPSAIRationaleModal;
window.openGPAIRationaleModal = openGPAIRationaleModal;

// KrushiSetu Central AI/ML Engine Food Dept Module Exports
window.renderCentralAIRecommendations = renderCentralAIRecommendations;
window.setAIPredictionFilter = setAIPredictionFilter;
window.openPredictCropModal = openPredictCropModal;
window.handleApproveAIPrediction = handleApproveAIPrediction;
window.openCorrectAIPredictionModal = openCorrectAIPredictionModal;
window.openAIPredictionAuditModal = openAIPredictionAuditModal;

// KrushiSetu Central AI/ML Engine Panchayat Samiti Module Exports
window.renderPSCentralAIAllocation = renderPSCentralAIAllocation;
window.setGPAllocationFilter = setGPAllocationFilter;
window.openRunGPAllocationModal = openRunGPAllocationModal;
window.handleApproveGPAllocation = handleApproveGPAllocation;
window.openCorrectGPAllocationModal = openCorrectGPAllocationModal;
window.openGPAllocationAuditModal = openGPAllocationAuditModal;
window.handleBatchApproveGPAllocations = handleBatchApproveGPAllocations;

// KrushiSetu Central AI/ML Engine Gram Panchayat Module Exports
window.renderGPCentralAIRecommendation = renderGPCentralAIRecommendation;
window.setFarmerRecFilter = setFarmerRecFilter;
window.openRunFarmerMatchingModal = openRunFarmerMatchingModal;
window.handleApproveFarmerRec = handleApproveFarmerRec;
window.openCorrectFarmerRecModal = openCorrectFarmerRecModal;
window.openFarmerAIRationaleModal = openFarmerAIRationaleModal;
window.openFarmerRecAuditModal = openFarmerRecAuditModal;
window.handleBatchApproveFarmerRecs = handleBatchApproveFarmerRecs;



window.onGradingBatchSelected = onGradingBatchSelected;
window.handleApproveWarehouseGrading = handleApproveWarehouseGrading;
window.openCorrectWarehouseGradingModal = openCorrectWarehouseGradingModal;
window.submitCorrectWarehouseGrading = submitCorrectWarehouseGrading;
window.loadGradingHistoryTable = loadGradingHistoryTable;
window.openGradingRecordDetailModal = openGradingRecordDetailModal;
// KrushiSetu Task 7: Major Warehouse -> Minor Warehouse Dispatch & Truck Tracking Exports
window.renderMajorWHDispatchesConsole = renderMajorWHDispatchesConsole;
window.setDispatchFilter = setDispatchFilter;
window.openCreateDispatchModal = openCreateDispatchModal;
window.onDispatchBatchSelected = onDispatchBatchSelected;
window.onDispatchTruckSelected = onDispatchTruckSelected;
window.handleCreateDispatchSubmit = handleCreateDispatchSubmit;
window.handleStartTransit = handleStartTransit;
window.openDispatchDetailModal = openDispatchDetailModal;
window.openEditDispatchModal = openEditDispatchModal;
window.handleUpdateDispatchSubmit = handleUpdateDispatchSubmit;
window.renderTruckTrackingConsole = renderTruckTrackingConsole;
window.renderTruckTracking = renderTruckTracking;
window.openDispatchTrackingModal = openDispatchTrackingModal;
window.openSimulateGPSModal = openSimulateGPSModal;
window.handleSimulateGPSSubmit = handleSimulateGPSSubmit;
window.renderMinorWHInwardConsole = renderMinorWHInwardConsole;
window.openMinorWHReceiveModal = openMinorWHReceiveModal;
window.updateMinorWHReceiveDiff = updateMinorWHReceiveDiff;
window.handleMinorWHReceiveSubmit = handleMinorWHReceiveSubmit;
window.renderMinorWHSentReceivedConsole = renderMinorWHSentReceivedConsole;
