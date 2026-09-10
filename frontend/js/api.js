/**
 * KrushiSetu - Central API Client Wrapper
 * Handles JWT Auth, Universal Record CRUD, Dual Grading, and Audit Logs
 */

const API_BASE_URL = (typeof window !== "undefined" && window.location && window.location.origin && window.location.origin.startsWith("http"))
  ? window.location.origin
  : "http://127.0.0.1:8000";

class ApiClient {
  static getToken() {
    return localStorage.getItem("krushisetu_token");
  }

  static setToken(token) {
    localStorage.setItem("krushisetu_token", token);
  }

  static removeToken() {
    localStorage.removeItem("krushisetu_token");
    localStorage.removeItem("krushisetu_user");
  }

  static getCurrentCachedUser() {
    const userJson = localStorage.getItem("krushisetu_user");
    return userJson ? JSON.parse(userJson) : null;
  }

  static setCachedUser(user) {
    localStorage.setItem("krushisetu_user", JSON.stringify(user));
  }

  static async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    const token = ApiClient.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);

      if (response.status === 401 && !endpoint.includes("/login")) {
        ApiClient.removeToken();
        window.location.href = "/pages/login.html?expired=1";
        return null;
      }

      let data;
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        data = await response.json();
      } else {
        const text = await response.text();
        data = { message: text || "Server responded with status " + response.status };
      }

      if (!response.ok) {
        const errorDetail = data.detail || (data.message || "An unexpected error occurred");
        throw new Error(errorDetail);
      }

      return data;
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      if (err.name === "TypeError" && err.message.toLowerCase().includes("fetch")) {
        throw new Error(`Unable to connect to KrushiSetu server at ${API_BASE_URL}. Please ensure the backend server is running.`);
      }
      throw err;
    }
  }

  // Auth & System Endpoints
  static async checkHealth() {
    return ApiClient.request("/api/health");
  }

  static async login(username, password) {
    const response = await ApiClient.request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    if (response && response.access_token) {
      ApiClient.setToken(response.access_token);
      ApiClient.setCachedUser(response.user);
    }
    return response;
  }

  static async getMe() {
    const user = await ApiClient.request("/api/auth/me");
    if (user) {
      ApiClient.setCachedUser(user);
    }
    return user;
  }

  static async register(userData) {
    return ApiClient.request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(userData),
    });
  }

  static async getRoles() {
    return ApiClient.request("/api/auth/roles");
  }

  static async getSupplyChainNodes() {
    return ApiClient.request("/api/chain/nodes");
  }

  // Universal CRUD & Audit Record Methods
  static async getRecords(endpoint) {
    return ApiClient.request(`/api/records${endpoint}`);
  }

  static async createRecord(endpoint, data) {
    return ApiClient.request(`/api/records${endpoint}`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  static async editRecord(endpoint, recordId, data, changeReason = "Operational update") {
    return ApiClient.request(`/api/records${endpoint}/${recordId}`, {
      method: "PUT",
      body: JSON.stringify({
        data,
        change_reason: changeReason,
      }),
    });
  }

  static async reviewMajorWhGrade(recordId, humanScore, humanGrade, gradingNotes, changeReason) {
    return ApiClient.request(`/api/records/major-wh/intakes/${recordId}/grade`, {
      method: "PUT",
      body: JSON.stringify({
        human_final_score: parseFloat(humanScore),
        human_final_grade: humanGrade,
        grading_notes: gradingNotes,
        change_reason: changeReason || "Human inspector quality review and confirmation",
      }),
    });
  }

  static async generateAIRecRequirement(cropName = "Sugarcane", season = "Kharif 2026") {
    return ApiClient.request("/api/records/fd/generate-ai-recommendation", {
      method: "POST",
      body: JSON.stringify({ crop_name: cropName, season: season }),
    });
  }

  static async approveFDRequirement(recordId, finalQty = null, finalPriority = null, notes = null, changeReason = null) {
    return ApiClient.request(`/api/records/fd/requirements/${recordId}/approve`, {
      method: "PUT",
      body: JSON.stringify({
        human_final_quantity_mt: finalQty !== null ? parseFloat(finalQty) : null,
        human_final_priority: finalPriority,
        human_review_notes: notes,
        change_reason: changeReason || "Food Department Directorate final approval",
      }),
    });
  }

  static async assignRequirementToPS(recordId, psName, targetQuotaMt, notes = null) {
    return ApiClient.request(`/api/records/fd/requirements/${recordId}/assign-ps`, {
      method: "POST",
      body: JSON.stringify({
        panchayat_samiti_name: psName,
        target_quota_mt: parseFloat(targetQuotaMt),
        notes: notes,
      }),
    });
  }

  static async getAuditHistory(tableName, recordId) {
    return ApiClient.request(`/api/records/audit/${tableName}/${recordId}`);
  }

  static async getRecentAuditHistory(limit = 50) {
    return ApiClient.request(`/api/records/audit/system/recent?limit=${limit}`);
  }

  // Multi-Sector AI-First Methods
  static async generatePSAIAllocation(psName, cropName, totalQuotaMt, season) {
    return ApiClient.request("/api/records/ps/generate-ai-allocation", {
      method: "POST",
      body: JSON.stringify({
        panchayat_samiti_name: psName,
        crop_name: cropName,
        total_quota_mt: parseFloat(totalQuotaMt),
        season: season,
      }),
    });
  }

  static async approvePSGPAllocation(recordId, finalQty = null, reason = null) {
    return ApiClient.request(`/api/records/ps/gp-allocations/${recordId}/approve`, {
      method: "PUT",
      body: JSON.stringify({
        human_final_quantity_mt: finalQty !== null ? parseFloat(finalQty) : null,
        change_reason: reason || "Panchayat Samiti official block authorization",
      }),
    });
  }

  static async generateGPAIAssignment(gpName, cropName, totalQuotaMt, season) {
    return ApiClient.request("/api/records/gp/generate-ai-assignment", {
      method: "POST",
      body: JSON.stringify({
        gp_name: gpName,
        crop_name: cropName,
        total_gp_quota_mt: parseFloat(totalQuotaMt),
        season: season,
      }),
    });
  }

  static async approveGPCropAssignment(recordId, finalAcres = null, finalQtl = null, reason = null) {
    return ApiClient.request(`/api/records/gp/crop-assignments/${recordId}/approve`, {
      method: "PUT",
      body: JSON.stringify({
        human_final_acres: finalAcres !== null ? parseFloat(finalAcres) : null,
        human_final_quintals: finalQtl !== null ? parseFloat(finalQtl) : null,
        change_reason: reason || "Gram Panchayat agriculture committee authorization",
      }),
    });
  }

  static async getFarmerProfileCard(farmerId = null) {
    const q = farmerId ? `?farmer_id=${farmerId}` : "";
    return ApiClient.request(`/api/records/farmer/profile-card${q}`);
  }

  static async getFarmerCropRecommendation(farmerId = null) {
    const q = farmerId ? `?farmer_id=${farmerId}` : "";
    return ApiClient.request(`/api/records/farmer/crop-recommendation${q}`);
  }

  static async getFarmerCompleteHistory(farmerId = null) {
    const q = farmerId ? `?farmer_id=${farmerId}` : "";
    return ApiClient.request(`/api/records/farmer/complete-history${q}`);
  }

  static async generateMajorWHAIGrade(batchId, cropName, metrics = {}) {
    return ApiClient.request("/api/records/major-wh/generate-ai-grade", {
      method: "POST",
      body: JSON.stringify({
        batch_id: batchId,
        crop_name: cropName,
        ...metrics,
      }),
    });
  }

  static async getMinorWHAIRecs(location = "Baramati APMC Godown No. 3", cropName = "Wheat (Lokwan)") {
    return ApiClient.request(`/api/records/minor-wh/ai-recommendations?location=${encodeURIComponent(location)}&crop_name=${encodeURIComponent(cropName)}`);
  }

  static async getTruckTracking() {
    return ApiClient.request("/api/records/tracking/trucks");
  }

  static async updateTruckGPS(dispatchId, location, lat = null, lng = null) {
    return ApiClient.request(`/api/records/tracking/trucks/${dispatchId}/update-gps`, {
      method: "PUT",
      body: JSON.stringify({ current_location: location, latitude: lat, longitude: lng }),
    });
  }

  static async completeTruckDelivery(dispatchId) {
    return ApiClient.request(`/api/records/tracking/trucks/${dispatchId}/complete`, {
      method: "PUT",
    });
  }

  static async createBuyerId(buyerData) {
    return ApiClient.request("/api/records/buyer/create-id", {
      method: "POST",
      body: JSON.stringify(buyerData),
    });
  }

  static async getAIFeedbackLoop() {
    return ApiClient.request("/api/records/ai/feedback-loop");
  }

  static async getFDAIDataInsights() {
    return ApiClient.request("/api/records/fd/ai-data-insights");
  }

  static async getPSGPs() {
    return ApiClient.request("/api/records/ps/gps");
  }

  static async registerPSGP(gpData) {
    return ApiClient.request("/api/records/ps/gps", {
      method: "POST",
      body: JSON.stringify(gpData),
    });
  }

  static async getGPFarmers() {
    return ApiClient.request("/api/records/gp/farmers");
  }

  static async registerGPFarmer(farmerData) {
    return ApiClient.request("/api/records/gp/farmers", {
      method: "POST",
      body: JSON.stringify(farmerData),
    });
  }

  static async uploadSoilReport(farmerId, docUrl = null) {
    return ApiClient.request("/api/records/gp/upload-soil-report", {
      method: "POST",
      body: JSON.stringify({ farmer_id: farmerId, doc_url: docUrl }),
    });
  }

  static async runCameraAIGrading(batchId, cropName, sampleMetrics = {}, imageBase64 = null) {
    return ApiClient.request("/api/records/major-wh/camera-ai-grading", {
      method: "POST",
      body: JSON.stringify({
        batch_id: batchId,
        crop_name: cropName,
        sample_metrics: sampleMetrics,
        image_base64: imageBase64,
      }),
    });
  }

  static async getMajorWHStorage() {
    return ApiClient.request("/api/records/major-wh/storage");
  }

  static async createMajorWHStorage(storageData) {
    return ApiClient.request("/api/records/major-wh/storage", {
      method: "POST",
      body: JSON.stringify(storageData),
    });
  }

  static async getMinorWHSentReceived() {
    return ApiClient.request("/api/records/minor-wh/sent-received");
  }

  static async verifyBulkBuyer(buyerId) {
    return ApiClient.request(`/api/records/buyer/verify/${encodeURIComponent(buyerId)}`);
  }

  static async placeBuyerOrder(orderData) {
    return ApiClient.request("/api/records/buyer/place-order", {
      method: "POST",
      body: JSON.stringify(orderData),
    });
  }

  // --- CENTRAL AI/ML ENGINE v1 ENDPOINTS ---
  static async getAIEngineStats() {
    return ApiClient.request("/api/v1/ai/stats");
  }

  static async predictCropRequirement(cropNameOrObj = "Sugarcane", season = "Kharif 2026", region = "Baramati Block Panchayat Samiti", targetYear = 2026) {
    let bodyPayload = {};
    if (typeof cropNameOrObj === "object" && cropNameOrObj !== null) {
      bodyPayload = cropNameOrObj;
    } else {
      bodyPayload = {
        crop_name: cropNameOrObj,
        season: season,
        region: region,
        target_year: targetYear,
      };
    }
    return ApiClient.request("/api/v1/ai/crop-requirement/predict", {
      method: "POST",
      body: JSON.stringify(bodyPayload),
    });
  }

  static async getAIPredictions(status = null) {
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    return ApiClient.request(`/api/v1/ai/predictions${query}`);
  }

  static async getAIPrediction(id) {
    return ApiClient.request(`/api/v1/ai/predictions/${encodeURIComponent(id)}`);
  }

  static async approveAIPrediction(id, notes = "Approved without changes by Food Directorate") {
    return ApiClient.request(`/api/v1/ai/predictions/${encodeURIComponent(id)}/approve`, {
      method: "POST",
      body: JSON.stringify({ notes }),
    });
  }

  static async correctAIPrediction(id, correctionData) {
    return ApiClient.request(`/api/v1/ai/predictions/${encodeURIComponent(id)}/correct`, {
      method: "POST",
      body: JSON.stringify(correctionData),
    });
  }

  // --- TASK 3: CENTRAL AI GP ALLOCATION ENDPOINTS ---
  static async predictGPAllocation(payload) {
    return ApiClient.request("/api/v1/ai/gp-allocation/predict", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  static async getGPAllocations(params = {}) {
    const query = new URLSearchParams();
    if (params.batch_code) query.append("batch_code", params.batch_code);
    if (params.status) query.append("status", params.status);
    if (params.crop_name) query.append("crop_name", params.crop_name);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return ApiClient.request(`/api/v1/ai/gp-allocation${qs}`);
  }

  static async getGPAllocation(id) {
    return ApiClient.request(`/api/v1/ai/gp-allocation/${encodeURIComponent(id)}`);
  }

  static async approveGPAllocation(id, notes = "Approved without modification by Panchayat Samiti") {
    return ApiClient.request(`/api/v1/ai/gp-allocation/${encodeURIComponent(id)}/approve`, {
      method: "POST",
      body: JSON.stringify({ notes }),
    });
  }

  static async correctGPAllocation(id, correctionData) {
    return ApiClient.request(`/api/v1/ai/gp-allocation/${encodeURIComponent(id)}/correct`, {
      method: "POST",
      body: JSON.stringify(correctionData),
    });
  }

  static async batchApproveGPAllocations(batchCode, notes = "Batch approved by Panchayat Samiti") {
    return ApiClient.request(`/api/v1/ai/gp-allocation/batch/${encodeURIComponent(batchCode)}/approve`, {
      method: "POST",
      body: JSON.stringify({ notes }),
    });
  }

  // --- TASK 4: CENTRAL AI FARMER RECOMMENDATION ENDPOINTS ---
  static async predictFarmerRecommendations(payload) {
    return ApiClient.request("/api/v1/ai/farmer-recommendation/predict", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  static async getFarmerRecommendations(params = {}) {
    const query = new URLSearchParams();
    if (params.batch_code) query.append("batch_code", params.batch_code);
    if (params.status) query.append("status", params.status);
    if (params.gp_name) query.append("gp_name", params.gp_name);
    if (params.crop_name) query.append("crop_name", params.crop_name);
    if (params.farmer_id) query.append("farmer_id", params.farmer_id);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return ApiClient.request(`/api/v1/ai/farmer-recommendation${qs}`);
  }

  static async getFarmerRecommendation(id) {
    return ApiClient.request(`/api/v1/ai/farmer-recommendation/${encodeURIComponent(id)}`);
  }

  static async approveFarmerRecommendation(id, notes = "Approved without modification by Gram Panchayat") {
    return ApiClient.request(`/api/v1/ai/farmer-recommendation/${encodeURIComponent(id)}/approve`, {
      method: "POST",
      body: JSON.stringify({ notes }),
    });
  }

  static async correctFarmerRecommendation(id, correctionData) {
    return ApiClient.request(`/api/v1/ai/farmer-recommendation/${encodeURIComponent(id)}/correct`, {
      method: "POST",
      body: JSON.stringify(correctionData),
    });
  }

  static async batchApproveFarmerRecommendations(batchCode, notes = "Batch approved by Gram Panchayat") {
    return ApiClient.request(`/api/v1/ai/farmer-recommendation/batch/${encodeURIComponent(batchCode)}/approve`, {
      method: "POST",
      body: JSON.stringify({ notes }),
    });
  }

  // --- TASK 5: CENTRAL AI MAJOR WAREHOUSE CROP QUALITY & GRADING ENDPOINTS ---
  static async analyzeCropQuality(payload) {
    return ApiClient.request("/api/v1/ai/warehouse/grading/analyze", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  static async getWarehouseGradings(params = {}) {
    const query = new URLSearchParams();
    if (params.batch_id) query.append("batch_id", params.batch_id);
    if (params.status) query.append("status", params.status);
    if (params.crop_name) query.append("crop_name", params.crop_name);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return ApiClient.request(`/api/v1/ai/warehouse/grading${qs}`);
  }

  static async getWarehouseGrading(id) {
    return ApiClient.request(`/api/v1/ai/warehouse/grading/${encodeURIComponent(id)}`);
  }

  static async approveWarehouseGrading(id, notes = "Approved without modification by Major Warehouse inspector") {
    return ApiClient.request(`/api/v1/ai/warehouse/grading/${encodeURIComponent(id)}/approve`, {
      method: "POST",
      body: JSON.stringify({ notes }),
    });
  }

  static async correctWarehouseGrading(id, correctionData) {
    return ApiClient.request(`/api/v1/ai/warehouse/grading/${encodeURIComponent(id)}/correct`, {
      method: "POST",
      body: JSON.stringify(correctionData),
    });
  }

  // --- TASK 6: MAJOR WAREHOUSE STORAGE, INVENTORY & AI STOCK INTELLIGENCE ---
  static async createWarehouseStorage(payload) {
    return ApiClient.request("/api/v1/warehouse/storage", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  static async getWarehouseStorageList(params = {}) {
    const query = new URLSearchParams();
    if (params.crop_name) query.append("crop_name", params.crop_name);
    if (params.crop_category) query.append("crop_category", params.crop_category);
    if (params.status) query.append("status", params.status);
    if (params.batch_id) query.append("batch_id", params.batch_id);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return ApiClient.request(`/api/v1/warehouse/storage${qs}`);
  }

  static async getWarehouseStorage(storageId) {
    return ApiClient.request(`/api/v1/warehouse/storage/${encodeURIComponent(storageId)}`);
  }

  static async updateWarehouseStorage(storageId, payload) {
    return ApiClient.request(`/api/v1/warehouse/storage/${encodeURIComponent(storageId)}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  }

  static async getWarehouseInventory(warehouseId = "MWH-PUN-01") {
    const qs = warehouseId ? `?warehouse_id=${encodeURIComponent(warehouseId)}` : "";
    return ApiClient.request(`/api/v1/warehouse/inventory${qs}`);
  }

  static async getWarehouseStockInsights(warehouseId = "MWH-PUN-01") {
    const qs = warehouseId ? `?warehouse_id=${encodeURIComponent(warehouseId)}` : "";
    return ApiClient.request(`/api/v1/ai/warehouse/stock-insights${qs}`);
  }

  static async getWarehouseStockRecommendations(warehouseId = "MWH-PUN-01") {
    const qs = warehouseId ? `?warehouse_id=${encodeURIComponent(warehouseId)}` : "";
    return ApiClient.request(`/api/v1/ai/warehouse/stock-recommendations${qs}`);
  }

  // --- TASK 7: MAJOR WAREHOUSE -> MINOR WAREHOUSE DISPATCH & TRUCK TRACKING ---
  static async getTrucksList(status = null) {
    const qs = status ? `?status=${encodeURIComponent(status)}` : "";
    return ApiClient.request(`/api/v1/warehouse/trucks${qs}`);
  }

  static async registerTruck(payload) {
    return ApiClient.request("/api/v1/warehouse/trucks", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  static async createWarehouseDispatch(payload) {
    return ApiClient.request("/api/v1/warehouse/dispatch", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  static async getWarehouseDispatches(params = {}) {
    const query = new URLSearchParams();
    if (params.batch_id) query.append("batch_id", params.batch_id);
    if (params.status) query.append("status", params.status);
    if (params.destination) query.append("destination", params.destination);
    if (params.origin) query.append("origin", params.origin);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return ApiClient.request(`/api/v1/warehouse/dispatches${qs}`);
  }

  static async getWarehouseDispatch(dispatchId) {
    return ApiClient.request(`/api/v1/warehouse/dispatch/${encodeURIComponent(dispatchId)}`);
  }

  static async updateWarehouseDispatch(dispatchId, payload) {
    return ApiClient.request(`/api/v1/warehouse/dispatch/${encodeURIComponent(dispatchId)}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  }

  static async startDispatchTransit(dispatchId, payload = {}) {
    return ApiClient.request(`/api/v1/warehouse/dispatch/${encodeURIComponent(dispatchId)}/start-transit`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  static async updateDispatchLocation(dispatchId, payload) {
    return ApiClient.request(`/api/v1/warehouse/dispatch/${encodeURIComponent(dispatchId)}/gps-location`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  static async getDispatchTracking(dispatchId) {
    return ApiClient.request(`/api/v1/warehouse/dispatch/${encodeURIComponent(dispatchId)}/tracking`);
  }

  static async receiveMinorWarehouseDispatch(dispatchId, payload) {
    return ApiClient.request(`/api/v1/warehouse/dispatch/${encodeURIComponent(dispatchId)}/receive`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }
}

window.ApiClient = ApiClient;

