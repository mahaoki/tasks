import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://api.tasks.localhost',
  withCredentials: true,
});

export default api;
