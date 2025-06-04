import axios from 'axios';

const api = axios.create({
  baseURL: 'https://rfpbackend.gustavotadeu.com.br',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  maxRedirects: 0,
  proxy: false
});

// Interceptor para adicionar JWT automaticamente
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers = config.headers || {};
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

export default api;