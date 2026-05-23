import { createContext, useContext, useEffect, useMemo, useState, useCallback } from "react";
import axios from "axios";

const AuthContext = createContext(null);

// API base URL configuration
const browserHost = typeof window !== "undefined" ? window.location.hostname : "localhost";
const normalizeBaseUrl = (value, fallback) => {
  const raw = String(value || fallback || "").trim();
  if (!raw) return fallback;
  const withScheme = /^https?:\/\//i.test(raw) ? raw : `http://${raw}`;
  try {
    const parsed = new URL(withScheme);
    return parsed.toString().replace(/\/$/, "");
  } catch {
    return String(fallback || withScheme).replace(/\/$/, "");
  }
};

const API_BASE_URL = normalizeBaseUrl(
  import.meta.env.VITE_API_BASE_URL,
  `http://${browserHost}:8001`
);

// Create axios instance for auth API calls
const authAPI = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json"
  }
});

// Token storage keys
const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
const TOKEN_EXPIRY_KEY = "token_expiry";
const AUTH_REFRESH_EXEMPT_PATHS = [
  "/api/v1/auth/login",
  "/api/v1/auth/register",
  "/api/v1/auth/refresh",
  "/api/v1/auth/logout",
];

const isAuthRefreshExemptRequest = (config) => {
  const requestUrl = String(config?.url || "");
  return AUTH_REFRESH_EXEMPT_PATHS.some((path) => requestUrl.includes(path));
};

/**
 * AuthProvider component that manages authentication state.
 * 
 * Provides:
 * - isAuthenticated: boolean indicating if user is logged in
 * - user: current user object or null
 * - loading: boolean indicating if auth state is being determined
 * - login: function to authenticate user
 * - signup: function to register new user
 * - logout: function to log out user
 * - refreshToken: function to refresh access token
 * - updateProfile: function to update user email
 * - changePassword: function to change user password
 * - getSessions: function to get active sessions
 * - revokeSession: function to revoke a specific session
 * - revokeAllOtherSessions: function to revoke all other sessions
 * 
 * Requirements: 15.1, 15.2, 15.6, 15.7, 15.8
 */
export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tokenRefreshTimer, setTokenRefreshTimer] = useState(null);

  /**
   * Store tokens in localStorage and set expiry time.
   */
  const storeTokens = useCallback((accessToken, refreshToken, expiresIn) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    
    // Calculate expiry timestamp (current time + expires_in seconds)
    const expiryTime = Date.now() + (expiresIn * 1000);
    localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
  }, []);

  /**
   * Clear tokens from localStorage.
   */
  const clearTokens = useCallback(() => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
  }, []);

  /**
   * Get stored access token.
   */
  const getAccessToken = useCallback(() => {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }, []);

  /**
   * Get stored refresh token.
   */
  const getRefreshToken = useCallback(() => {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }, []);

  /**
   * Check if token is expired or about to expire (within 5 minutes).
   */
  const isTokenExpired = useCallback(() => {
    const expiryTime = localStorage.getItem(TOKEN_EXPIRY_KEY);
    if (!expiryTime) return true;
    
    // Consider token expired if it expires within 5 minutes (300000ms)
    const bufferTime = 300000;
    return Date.now() >= (parseInt(expiryTime, 10) - bufferTime);
  }, []);

  /**
   * Fetch current user profile from API.
   */
  const fetchUserProfile = useCallback(async (accessToken = null) => {
    try {
      const token = accessToken || getAccessToken();
      if (!token) {
        throw new Error("No access token available");
      }

      const response = await authAPI.get("/api/v1/auth/me", {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      setUser(response.data);
      setIsAuthenticated(true);
      return response.data;
    } catch (error) {
      console.error("Failed to fetch user profile:", error);
      // If fetching profile fails, clear auth state
      clearTokens();
      setUser(null);
      setIsAuthenticated(false);
      throw error;
    }
  }, [getAccessToken, clearTokens]);

  /**
   * Refresh the access token using the refresh token.
   */
  const refreshToken = useCallback(async () => {
    try {
      const refreshTokenValue = getRefreshToken();
      if (!refreshTokenValue) {
        throw new Error("No refresh token available");
      }

      const response = await authAPI.post("/api/v1/auth/refresh", {
        refresh_token: refreshTokenValue
      });

      const { access_token, refresh_token, expires_in } = response.data;
      storeTokens(access_token, refresh_token, expires_in);

      return access_token;
    } catch (error) {
      console.error("Failed to refresh token:", error);
      // If refresh fails, clear auth state and log out
      clearTokens();
      setUser(null);
      setIsAuthenticated(false);
      throw error;
    }
  }, [getRefreshToken, storeTokens, clearTokens]);

  /**
   * Setup automatic token refresh before expiry.
   */
  const setupTokenRefresh = useCallback((expiresIn) => {
    // Clear existing timer
    if (tokenRefreshTimer) {
      clearTimeout(tokenRefreshTimer);
    }

    // Refresh token 5 minutes before expiry
    const refreshTime = (expiresIn - 300) * 1000;
    
    if (refreshTime > 0) {
      const timer = setTimeout(async () => {
        try {
          await refreshToken();
        } catch (error) {
          console.error("Automatic token refresh failed:", error);
        }
      }, refreshTime);

      setTokenRefreshTimer(timer);
    }
  }, [tokenRefreshTimer, refreshToken]);

  /**
   * Register a new user.
   * 
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise<Object>} User data
   */
  const signup = useCallback(async (email, password) => {
    try {
      setLoading(true);
      
      const response = await authAPI.post("/api/v1/auth/register", {
        email,
        password
      });

      const { access_token, refresh_token, expires_in } = response.data;
      storeTokens(access_token, refresh_token, expires_in);
      setupTokenRefresh(expires_in);

      // Fetch user profile after registration, passing the token directly
      const userData = await fetchUserProfile(access_token);
      
      return userData;
    } catch (error) {
      console.error("Signup failed:", error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [storeTokens, setupTokenRefresh, fetchUserProfile]);

  /**
   * Log in a user.
   * 
   * @param {string} email - User email
   * @param {string} password - User password
   * @param {boolean} rememberMe - Whether to remember the user
   * @returns {Promise<Object>} User data
   */
  const login = useCallback(async (email, password, rememberMe = false) => {
    try {
      setLoading(true);
      
      const response = await authAPI.post("/api/v1/auth/login", {
        email,
        password,
        remember_me: rememberMe
      });

      const { access_token, refresh_token, expires_in } = response.data;
      storeTokens(access_token, refresh_token, expires_in);
      setupTokenRefresh(expires_in);

      // Fetch user profile after login, passing the token directly
      const userData = await fetchUserProfile(access_token);
      
      return userData;
    } catch (error) {
      console.error("Login failed:", error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [storeTokens, setupTokenRefresh, fetchUserProfile]);

  /**
   * Log out the current user.
   */
  const logout = useCallback(async () => {
    try {
      const refreshTokenValue = getRefreshToken();
      
      // Attempt to logout on server
      if (refreshTokenValue) {
        try {
          await authAPI.post("/api/v1/auth/logout", {
            refresh_token: refreshTokenValue
          });
        } catch (error) {
          console.error("Server logout failed:", error);
          // Continue with local logout even if server logout fails
        }
      }
    } finally {
      // Clear local state regardless of server response
      clearTokens();
      setUser(null);
      setIsAuthenticated(false);
      
      // Clear token refresh timer
      if (tokenRefreshTimer) {
        clearTimeout(tokenRefreshTimer);
        setTokenRefreshTimer(null);
      }
    }
  }, [getRefreshToken, clearTokens, tokenRefreshTimer]);

  /**
   * Update user profile (email).
   * 
   * @param {string} newEmail - New email address
   * @returns {Promise<Object>} Updated user data
   */
  const updateProfile = useCallback(async (newEmail) => {
    try {
      const accessToken = getAccessToken();
      if (!accessToken) {
        throw new Error("Not authenticated");
      }

      const response = await authAPI.put(
        "/api/v1/auth/me",
        { new_email: newEmail },
        {
          headers: {
            Authorization: `Bearer ${accessToken}`
          }
        }
      );

      // Update local user state
      setUser(response.data);
      
      return response.data;
    } catch (error) {
      console.error("Profile update failed:", error);
      throw error;
    }
  }, [getAccessToken]);

  /**
   * Change user password.
   * 
   * @param {string} currentPassword - Current password
   * @param {string} newPassword - New password
   * @returns {Promise<Object>} Success message
   */
  const changePassword = useCallback(async (currentPassword, newPassword) => {
    try {
      const accessToken = getAccessToken();
      if (!accessToken) {
        throw new Error("Not authenticated");
      }

      const response = await authAPI.put(
        "/api/v1/auth/me/password",
        {
          current_password: currentPassword,
          new_password: newPassword
        },
        {
          headers: {
            Authorization: `Bearer ${accessToken}`
          }
        }
      );

      return response.data;
    } catch (error) {
      console.error("Password change failed:", error);
      throw error;
    }
  }, [getAccessToken]);

  /**
   * Get list of active sessions.
   * 
   * @returns {Promise<Array>} List of sessions
   */
  const getSessions = useCallback(async () => {
    try {
      const accessToken = getAccessToken();
      if (!accessToken) {
        throw new Error("Not authenticated");
      }

      const response = await authAPI.get("/api/v1/auth/sessions", {
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      });

      return response.data;
    } catch (error) {
      console.error("Failed to fetch sessions:", error);
      throw error;
    }
  }, [getAccessToken]);

  /**
   * Revoke a specific session.
   * 
   * @param {string} sessionId - Session ID to revoke
   * @returns {Promise<Object>} Success message
   */
  const revokeSession = useCallback(async (sessionId) => {
    try {
      const accessToken = getAccessToken();
      if (!accessToken) {
        throw new Error("Not authenticated");
      }

      const response = await authAPI.delete(`/api/v1/auth/sessions/${sessionId}`, {
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      });

      return response.data;
    } catch (error) {
      console.error("Failed to revoke session:", error);
      throw error;
    }
  }, [getAccessToken]);

  /**
   * Revoke all other sessions except the current one.
   * 
   * @returns {Promise<Object>} Success message
   */
  const revokeAllOtherSessions = useCallback(async () => {
    try {
      const accessToken = getAccessToken();
      const refreshTokenValue = getRefreshToken();
      
      if (!accessToken || !refreshTokenValue) {
        throw new Error("Not authenticated");
      }

      const response = await authAPI.delete(
        "/api/v1/auth/sessions",
        {
          headers: {
            Authorization: `Bearer ${accessToken}`
          },
          data: {
            refresh_token: refreshTokenValue
          }
        }
      );

      return response.data;
    } catch (error) {
      console.error("Failed to revoke all other sessions:", error);
      throw error;
    }
  }, [getAccessToken, getRefreshToken]);

  /**
   * Initialize authentication state on mount.
   * Checks for stored tokens and validates them.
   */
  useEffect(() => {
    const initAuth = async () => {
      try {
        const accessToken = getAccessToken();
        const refreshTokenValue = getRefreshToken();

        if (!accessToken || !refreshTokenValue) {
          // No tokens stored, user is not authenticated
          setLoading(false);
          return;
        }

        // Check if token is expired
        if (isTokenExpired()) {
          // Try to refresh the token
          try {
            await refreshToken();
            // After refresh, fetch user profile
            await fetchUserProfile();
          } catch (error) {
            console.error("Token refresh failed during init:", error);
            // Clear invalid tokens
            clearTokens();
          }
        } else {
          // Token is still valid, fetch user profile
          try {
            await fetchUserProfile();
            
            // Setup automatic refresh
            const expiryTime = localStorage.getItem(TOKEN_EXPIRY_KEY);
            if (expiryTime) {
              const expiresIn = Math.floor((parseInt(expiryTime, 10) - Date.now()) / 1000);
              setupTokenRefresh(expiresIn);
            }
          } catch (error) {
            console.error("Failed to fetch user profile during init:", error);
            clearTokens();
          }
        }
      } catch (error) {
        console.error("Auth initialization failed:", error);
      } finally {
        setLoading(false);
      }
    };

    initAuth();

    // Cleanup timer on unmount
    return () => {
      if (tokenRefreshTimer) {
        clearTimeout(tokenRefreshTimer);
      }
    };
  }, []); // Empty dependency array - only run on mount

  /**
   * Setup axios interceptor to add auth token to requests.
   */
  useEffect(() => {
    const requestInterceptor = authAPI.interceptors.request.use(
      (config) => {
        const accessToken = getAccessToken();
        if (accessToken && !config.headers.Authorization) {
          config.headers.Authorization = `Bearer ${accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    const responseInterceptor = authAPI.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (!originalRequest || isAuthRefreshExemptRequest(originalRequest)) {
          return Promise.reject(error);
        }

        // If error is 401 and we haven't retried yet, try to refresh token
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const newAccessToken = await refreshToken();
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            return authAPI(originalRequest);
          } catch (refreshError) {
            // Refresh failed, log out user
            await logout();
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );

    // Cleanup interceptors
    return () => {
      authAPI.interceptors.request.eject(requestInterceptor);
      authAPI.interceptors.response.eject(responseInterceptor);
    };
  }, [getAccessToken, refreshToken, logout]);

  const value = useMemo(
    () => ({
      isAuthenticated,
      user,
      loading,
      login,
      signup,
      logout,
      refreshToken,
      updateProfile,
      changePassword,
      getSessions,
      revokeSession,
      revokeAllOtherSessions
    }),
    [
      isAuthenticated,
      user,
      loading,
      login,
      signup,
      logout,
      refreshToken,
      updateProfile,
      changePassword,
      getSessions,
      revokeSession,
      revokeAllOtherSessions
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * Hook to access authentication context.
 * Must be used within AuthProvider.
 * 
 * @returns {Object} Authentication context
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};
