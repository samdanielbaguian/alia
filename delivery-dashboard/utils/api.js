import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Shipment endpoints
export const shipmentAPI = {
  getAll: () => apiClient.get('/api/shipments/'),
  getById: (id) => apiClient.get(`/api/shipments/${id}`),
  getByTracking: (trackingNumber) => apiClient.get(`/api/shipments/tracking/${trackingNumber}`),
  create: (data) => apiClient.post('/api/shipments/', data),
  update: (id, data) => apiClient.put(`/api/shipments/${id}`, data),
  delete: (id) => apiClient.delete(`/api/shipments/${id}`),
};

// Delivery endpoints
export const deliveryAPI = {
  getAll: () => apiClient.get('/api/deliveries/'),
  getById: (id) => apiClient.get(`/api/deliveries/${id}`),
  create: (data) => apiClient.post('/api/deliveries/', data),
  update: (id, data) => apiClient.put(`/api/deliveries/${id}`, data),
  delete: (id) => apiClient.delete(`/api/deliveries/${id}`),
};

// Driver endpoints
export const driverAPI = {
  getAll: () => apiClient.get('/api/drivers/'),
  getById: (id) => apiClient.get(`/api/drivers/${id}`),
  create: (data) => apiClient.post('/api/drivers/', data),
  update: (id, data) => apiClient.put(`/api/drivers/${id}`, data),
  delete: (id) => apiClient.delete(`/api/drivers/${id}`),
};

// Tracking endpoints
export const trackingAPI = {
  trackShipment: (trackingNumber) => apiClient.get(`/api/tracking/${trackingNumber}`),
  getDeliveryProgress: (deliveryId) => apiClient.get(`/api/tracking/delivery/${deliveryId}/progress`),
};

export default apiClient;
