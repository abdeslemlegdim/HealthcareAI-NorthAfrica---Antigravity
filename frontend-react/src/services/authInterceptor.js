/**
 * Authentication Interceptor for Axios
 * 
 * This module provides axios interceptors for automatic token management:
 * - Attaches access tokens to all API requests
 * - Intercepts 401 responses and automatically refreshes tokens
 * - Retries failed requests after token refresh
 * - Handles concurrent requests during token refresh
 * 
 * Requirements: 15.3, 15.4, 15.5, 15.9
 */

import axios from "axios";

// Token storage keys
const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
const TOKEN_EXPIRY_KEY = "token_expiry";

// Flag to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
let failedQueue = [];

/**
 * Process queued requests after token refresh
 */
const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

/**
 * Get stored access token from localStorage
 */
const getAccessToken = () => {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
};

/**
 * Get stored refresh token from localStorage
 */
const getRefreshToken = () => {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
};

/**
 * Store tokens in localStorage
 */
const storeTokens = (accessToken, refreshToken, expiresIn) => {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  
  // Calculate expiry timestamp
  const expiryTime = Date.now() + (expiresIn * 1000);
  localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
};

/**
 * Clear tokens from localStorage
 */
const clearTokens = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(TOKEN_EXPIRY_KEY);
};

/**
 * Refresh access token using refresh token
 */
const refreshAccessToken = async (apiBaseUrl) => {
  const refreshToken = getRefreshToken();
  
  if (!refreshToken) {
    throw new Error("No refresh token available");
  }

  try {
    const response = await axios.post(
      `${apiBaseUrl}/api/v1/auth/refresh`,
      { refresh_token: refreshToken },
      {
        headers: {
          "Content-Type": "application/json"
        }
      }
    );

    const { access_token, refresh_token, expires_in } = response.data;
    storeTokens(access_token, refresh_token, expires_in);

    return access_token;
  } catch (error) {
    // Clear tokens if refresh fails
    clearTokens();
    throw error;
  }
};

/**
 * Setup authentication interceptors for an axios instance
 * 
 * @param {Object} axiosInstance - The axios instance to configure
 * @param {Object} options - Configuration options
 * @param {Function} options.onLogout - Callback to execute on authentication failure
 * @param {string} options.apiBaseUrl - Base URL for API requests
 * @returns {Object} Object with cleanup function
 */
export const setupAuthInterceptor = (axiosInstance, options = {}) => {
  const { onLogout, apiBaseUrl } = options;

  // Request interceptor - attach access token to all requests
  const requestInterceptor = axiosInstance.interceptors.request.use(
    (config) => {
      const accessToken = getAccessToken();
      
      // Only attach token if not already present and token exists
      if (accessToken && !config.headers.Authorization) {
        config.headers.Authorization = `Bearer ${accessToken}`;
      }
      
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor - handle 401 errors and token refresh
  const responseInterceptor = axiosInstance.interceptors.response.use(
    (response) => {
      // Pass through successful responses
      return response;
    },
    async (error) => {
      const originalRequest = error.config;

      // Check if error is 401 and we haven't already retried
      if (error.response?.status === 401 && !originalRequest._retry) {
        // Check if this is a token expiration error
        const errorDetail = error.response?.data?.detail;
        const isTokenExpired = 
          errorDetail && 
          (errorDetail.includes("expired") || 
           errorDetail.includes("token_expired") ||
           errorDetail.includes("invalid"));

        if (isTokenExpired) {
          // Mark request as retried to prevent infinite loops
          originalRequest._retry = true;

          if (isRefreshing) {
            // If already refreshing, queue this request
            return new Promise((resolve, reject) => {
              failedQueue.push({ resolve, reject });
            })
              .then((token) => {
                originalRequest.headers.Authorization = `Bearer ${token}`;
                return axiosInstance(originalRequest);
              })
              .catch((err) => {
                return Promise.reject(err);
              });
          }

          // Start refresh process
          isRefreshing = true;

          try {
            const newAccessToken = await refreshAccessToken(apiBaseUrl);
            
            // Process queued requests
            processQueue(null, newAccessToken);
            
            // Retry original request with new token
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            return axiosInstance(originalRequest);
          } catch (refreshError) {
            // Refresh failed - process queue with error and logout
            processQueue(refreshError, null);
            
            // Call logout callback if provided
            if (onLogout && typeof onLogout === "function") {
              onLogout();
            }
            
            return Promise.reject(refreshError);
          } finally {
            isRefreshing = false;
          }
        }
      }

      // For non-401 errors or non-token errors, pass through
      return Promise.reject(error);
    }
  );

  // Return cleanup function
  return {
    cleanup: () => {
      axiosInstance.interceptors.request.eject(requestInterceptor);
      axiosInstance.interceptors.response.eject(responseInterceptor);
    }
  };
};

/**
 * Create a configured axios instance with auth interceptors
 * 
 * @param {Object} options - Configuration options
 * @param {string} options.baseURL - Base URL for API requests
 * @param {Function} options.onLogout - Callback to execute on authentication failure
 * @param {number} options.timeout - Request timeout in milliseconds
 * @returns {Object} Configured axios instance
 */
export const createAuthenticatedAxios = (options = {}) => {
  const {
    baseURL,
    onLogout,
    timeout = 60000
  } = options;

  // Create axios instance
  const instance = axios.create({
    baseURL,
    timeout,
    headers: {
      "Content-Type": "application/json"
    }
  });

  // Setup interceptors
  setupAuthInterceptor(instance, {
    onLogout,
    apiBaseUrl: baseURL
  });

  return instance;
};

export default {
  setupAuthInterceptor,
  createAuthenticatedAxios
};
