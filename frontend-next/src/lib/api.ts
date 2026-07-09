import axios from 'axios';

let currentToken = '';
let currentRole = '';

/**
 * Fetches a JWT token for the given role and stores it for subsequent API requests.
 */
export const fetchToken = async (role: string) => {
  if (role === currentRole && currentToken) return currentToken;
  
  // Use mock credentials matching the backend auth logic
  const username = role.toLowerCase() === 'engineer' || role.toLowerCase() === 'admin' ? 'admin' : 'operator';
  const password = username === 'admin' ? 'adminpassword' : 'operatorpassword';
  
  try {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    
    const response = await axios.post('http://localhost:8000/auth/token', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    
    currentToken = response.data.access_token;
    currentRole = role;
    return currentToken;
  } catch (err) {
    console.error('Failed to authenticate:', err);
    return null;
  }
};

const api = axios.create({
  baseURL: 'http://localhost:8000'
});

// Intercept all requests and attach the Bearer token
api.interceptors.request.use(async (config) => {
  if (currentToken) {
    config.headers.Authorization = `Bearer ${currentToken}`;
  }
  return config;
});

export default api;
