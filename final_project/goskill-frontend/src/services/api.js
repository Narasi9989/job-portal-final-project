import axios from 'axios';

export const API_BASE_URL = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('goskillToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('goskillToken');
      localStorage.removeItem('goskillUser');
      localStorage.removeItem('goskillRole');
    }
    return Promise.reject(error);
  },
);

export function getApiError(error) {
  if (!error.response) {
    return 'Server is not reachable. Please confirm the service is running on http://127.0.0.1:8000.';
  }

  const { status, data } = error.response;

  if (status === 401) {
    return 'Login expired or credentials are invalid. Please sign in again.';
  }

  if (status === 422) {
    const detail = Array.isArray(data?.detail)
      ? data.detail.map((item) => `${item.loc?.join('.')}: ${item.msg}`).join(' ')
      : data?.detail;
    return detail || 'Validation failed. Please check the form values.';
  }

  if (status === 404) {
    return data?.detail || 'This service endpoint was not found.';
  }

  return data?.detail || `Request failed with status ${status}.`;
}

export async function loginUser(username, password) {
  const form = new URLSearchParams();
  form.append('username', username);
  form.append('password', password);

  const response = await api.post('/api/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });

  return response.data;
}

export async function registerUser({ username, email, password }) {
  const response = await api.post('/api/auth/register', {
    username,
    email,
    password,
  });

  return response.data;
}

export default api;
