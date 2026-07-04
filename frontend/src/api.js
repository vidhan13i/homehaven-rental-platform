import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Axios Instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Storage Helpers
export const getAccessToken = () => localStorage.getItem('access_token');
export const getRefreshToken = () => localStorage.getItem('refresh_token');

export const setTokens = (access, refresh) => {
  localStorage.setItem('access_token', access);
  if (refresh) {
    localStorage.setItem('refresh_token', refresh);
  }
};

export const clearTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

// Request Interceptor: Attach access token
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Auto refresh token on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Avoid infinite loop if refresh token call itself fails (401)
    if (error.response?.status === 401 && !originalRequest._retry && originalRequest.url !== '/api/auth/token/refresh/') {
      originalRequest._retry = true;
      const refreshToken = getRefreshToken();

      if (refreshToken) {
        try {
          const resp = await axios.post(`${API_BASE_URL}/api/auth/token/refresh/`, {
            refresh: refreshToken,
          });

          const newAccess = resp.data.access;
          setTokens(newAccess);

          // Retry the original request
          originalRequest.headers['Authorization'] = `Bearer ${newAccess}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed (expired refresh token)
          clearTokens();
          window.location.reload(); // Refresh the page to boot the user back to login
        }
      }
    }

    return Promise.reject(error);
  }
);

// ─── Chat API Helpers ────────────────────────────────────────────────────────

export const chatApi = {
  // Conversations
  getConversations: (page = 1) => api.get(`/api/chat/conversations/?page=${page}`),
  createConversation: (data) => api.post(`/api/chat/conversations/`, data),
  getConversation: (id) => api.get(`/api/chat/conversations/${id}/`),
  deleteConversation: (id) => api.delete(`/api/chat/conversations/${id}/`),
  archiveConversation: (id) => api.post(`/api/chat/conversations/${id}/archive/`),
  pinConversation: (id) => api.post(`/api/chat/conversations/${id}/pin/`),
  markRead: (id) => api.post(`/api/chat/conversations/${id}/mark_read/`),
  getUnreadCount: (id) => api.get(`/api/chat/conversations/${id}/unread_count/`),
  
  // Messages
  getMessages: (conversationId, page = 1) => api.get(`/api/chat/messages/?conversation=${conversationId}&page=${page}`),
  sendMessage: (data) => api.post(`/api/chat/messages/`, data),
  editMessage: (id, content) => api.patch(`/api/chat/messages/${id}/`, { content }),
  deleteMessage: (id) => api.delete(`/api/chat/messages/${id}/`),
  reactToMessage: (id, emoji) => api.post(`/api/chat/messages/${id}/react/`, { emoji }),
  
  // Presence
  getPresence: (userId) => api.get(`/api/chat/presence/${userId}/`),
};

// ─── Agent & Application API Helpers ─────────────────────────────────────────

export const profileApi = {
  getProfile: () => api.get('/api/profiles/profiles/'),
  getProfileByEmail: (email) => api.get(`/api/profiles/profiles/by-email/?email=${email}`),
  updateProfile: (data) => api.patch('/api/profiles/profiles/', data),
};

export const agentApi = {
  checkAgentStatus: (email) => api.get(`/api/listings/agents/?search=${email}`),
  getAgent: (id) => api.get(`/api/listings/agents/${id}/`),
  getAgentListings: (agentId) => api.get(`/api/listings/listings/?agent=${agentId}`),
  createFullListing: (fd) => api.post(`/api/listings/listings/create-full/`, fd, { headers: { 'Content-Type': undefined } }),
};

export const applicationApi = {
  getApplicationsByUnit: (unitId) => api.get(`/api/applications/applications/by-unit/?unit_id=${unitId}`),
  approveApplication: (id) => api.post(`/api/applications/applications/${id}/approve/`),
  rejectApplication: (id) => api.post(`/api/applications/applications/${id}/reject/`),
};
