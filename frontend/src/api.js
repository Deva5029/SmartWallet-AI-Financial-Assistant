import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000', 
});

// --- User API Calls ---
export const getUserById = async (userId) => {
  const response = await apiClient.get(`/users/${userId}`);
  return response.data;
};

export const getUserByFirebaseId = async (firebaseUid) => {
  const response = await apiClient.get(`/users/by_firebase/${firebaseUid}`);
  return response.data;
};

export const createUser = async (userData) => {
  const response = await apiClient.post('/users', userData);
  return response.data;
};

// --- Card & Offer API Calls ---
export const addCard = async (cardData) => {
  const response = await apiClient.post('/cards', cardData);
  return response.data;
};

export const addOffer = async (offerData) => {
  const response = await apiClient.post('/offers', offerData);
  return response.data;
};

export const updateOfferStatus = async (offerId, status, amountSaved = null) => {
    const response = await apiClient.patch(`/offers/${offerId}/status`, { 
        status: status, 
        amount_saved: amountSaved 
    });
    return response.data;
};

// --- Preferences API Calls ---
export const updatePreferences = async (userId, preferencesData) => {
  const response = await apiClient.put(`/preferences/${userId}`, preferencesData);
  return response.data;
};

// --- AI & Other Feature API Calls ---
export const getAlerts = async (userId) => {
  const response = await apiClient.get(`/alerts/${userId}`);
  return response.data;
};

// --- MODIFIED: Now accepts an array of files ---
export const scanOffers = async (files) => {
  const formData = new FormData();
  // Loop through the files array and append each one.
  // The backend's 'List[UploadFile]' will correctly interpret this.
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  const response = await apiClient.post('/ocr/scan-offers', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const analyzeSpend = async (queryData) => {
  const response = await apiClient.post('/smart_spend/analyze', queryData);
  return response.data;
};

export const generateDigest = async (userId) => {
  const response = await apiClient.get(`/digest/${userId}`);
  return response.data;
};

