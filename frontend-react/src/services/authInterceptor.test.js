import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import axios from "axios";
import { setupAuthInterceptor, getApiClient } from "./authInterceptor";

// Mock axios
vi.mock("axios");

describe("authInterceptor", () => {
  let mockAxiosInstance;
  let mockAuthContext;
  let requestInterceptor;
  let responseInterceptor;

  beforeEach(() => {
    // Setup mock axios instance
    mockAxiosInstance = {
      interceptors: {
        request: {
          use: vi.fn((onFulfilled, onRejected) => {
            requestInterceptor = { onFulfilled, onRejected };
            return 1;
          }),
          eject: vi.fn()
        },
        response: {
          use: vi.fn((onFulfilled, onRejected) => {
            responseInterceptor = { onFulfilled, onRejected };
            return 1;
          }),
          eject: vi.fn()
        }
      },
      request: vi.fn(),
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn()
    };

    // Mock axios.create to return our mock instance
    axios.create.mockReturnValue(mockAxiosInstance);

    // Setup mock auth context
    mockAuthContext = {
      getAccessToken: vi.fn(),
      refreshToken: vi.fn(),
      logout: vi.fn()
    };

    // Clear all mocks
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("setupAuthInterceptor", () => {
    it("should setup request and response interceptors", () => {
      setupAuthInterceptor(mockAuthContext);

      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalledTimes(1);
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalledTimes(1);
    });
  });

  describe("Request Interceptor", () => {
    beforeEach(() => {
      setupAuthInterceptor(mockAuthContext);
    });

    it("should attach access token to request headers", async () => {
      mockAuthContext.getAccessToken.mockReturnValue("test_access_token");

      const config = {
        headers: {}
      };

      const result = await requestInterceptor.onFulfilled(config);

      expect(result.headers.Authorization).toBe("Bearer test_access_token");
    });

    it("should not attach Authorization header if no token exists", async () => {
      mockAuthContext.getAccessToken.mockReturnValue(null);

      const config = {
        headers: {}
      };

      const result = await requestInterceptor.onFulfilled(config);

      expect(result.headers.Authorization).toBeUndefined();
    });

    it("should handle request interceptor errors", async () => {
      const error = new Error("Request error");

      await expect(requestInterceptor.onRejected(error)).rejects.toThrow("Request error");
    });
  });

  describe("Response Interceptor", () => {
    beforeEach(() => {
      setupAuthInterceptor(mockAuthContext);
    });

    it("should pass through successful responses", async () => {
      const response = {
        status: 200,
        data: { message: "Success" }
      };

      const result = await responseInterceptor.onFulfilled(response);

      expect(result).toEqual(response);
    });

    it("should pass through non-401 errors", async () => {
      const error = {
        response: {
          status: 500,
          data: { error: "Server error" }
        },
        config: {}
      };

      await expect(responseInterceptor.onRejected(error)).rejects.toEqual(error);
    });

    it("should pass through 401 errors without token_expired code", async () => {
      const error = {
        response: {
          status: 401,
          data: { error_code: "unauthorized" }
        },
        config: {}
      };

      await expect(responseInterceptor.onRejected(error)).rejects.toEqual(error);
    });

    it("should refresh token and retry request on token_expired error", async () => {
      const originalRequest = {
        headers: {},
        url: "/api/v1/test"
      };

      const error = {
        response: {
          status: 401,
          data: { error_code: "token_expired" }
        },
        config: originalRequest
      };

      const newAccessToken = "new_access_token";
      mockAuthContext.refreshToken.mockResolvedValue(newAccessToken);

      const retryResponse = {
        status: 200,
        data: { message: "Success after retry" }
      };
      mockAxiosInstance.request.mockResolvedValue(retryResponse);

      const result = await responseInterceptor.onRejected(error);

      expect(mockAuthContext.refreshToken).toHaveBeenCalledTimes(1);
      expect(originalRequest.headers.Authorization).toBe(`Bearer ${newAccessToken}`);
      expect(originalRequest._retry).toBe(true);
      expect(mockAxiosInstance.request).toHaveBeenCalledWith(originalRequest);
      expect(result).toEqual(retryResponse);
    });

    it("should handle token_expired with 'code' field instead of 'error_code'", async () => {
      const originalRequest = {
        headers: {},
        url: "/api/v1/test"
      };

      const error = {
        response: {
          status: 401,
          data: { code: "token_expired" }
        },
        config: originalRequest
      };

      const newAccessToken = "new_access_token";
      mockAuthContext.refreshToken.mockResolvedValue(newAccessToken);

      const retryResponse = {
        status: 200,
        data: { message: "Success after retry" }
      };
      mockAxiosInstance.request.mockResolvedValue(retryResponse);

      const result = await responseInterceptor.onRejected(error);

      expect(mockAuthContext.refreshToken).toHaveBeenCalledTimes(1);
      expect(result).toEqual(retryResponse);
    });

    it("should logout user if token refresh fails", async () => {
      const originalRequest = {
        headers: {},
        url: "/api/v1/test"
      };

      const error = {
        response: {
          status: 401,
          data: { error_code: "token_expired" }
        },
        config: originalRequest
      };

      const refreshError = new Error("Refresh token invalid");
      mockAuthContext.refreshToken.mockRejectedValue(refreshError);
      mockAuthContext.logout.mockResolvedValue();

      // Mock window.location
      delete global.window;
      global.window = { location: { href: "" } };

      await expect(responseInterceptor.onRejected(error)).rejects.toThrow("Refresh token invalid");

      expect(mockAuthContext.refreshToken).toHaveBeenCalledTimes(1);
      expect(mockAuthContext.logout).toHaveBeenCalledTimes(1);
      expect(global.window.location.href).toBe("/login");
    });

    it("should not retry request if already retried", async () => {
      const originalRequest = {
        headers: {},
        url: "/api/v1/test",
        _retry: true // Already retried
      };

      const error = {
        response: {
          status: 401,
          data: { error_code: "token_expired" }
        },
        config: originalRequest
      };

      await expect(responseInterceptor.onRejected(error)).rejects.toEqual(error);

      expect(mockAuthContext.refreshToken).not.toHaveBeenCalled();
    });

    it("should handle concurrent requests during token refresh", async () => {
      // First request triggers token refresh
      const request1 = {
        headers: {},
        url: "/api/v1/test1"
      };

      const error1 = {
        response: {
          status: 401,
          data: { error_code: "token_expired" }
        },
        config: request1
      };

      // Second request comes in while refresh is in progress
      const request2 = {
        headers: {},
        url: "/api/v1/test2"
      };

      const error2 = {
        response: {
          status: 401,
          data: { error_code: "token_expired" }
        },
        config: request2
      };

      const newAccessToken = "new_access_token";
      
      // Mock refresh to take some time
      let resolveRefresh;
      const refreshPromise = new Promise((resolve) => {
        resolveRefresh = resolve;
      });
      mockAuthContext.refreshToken.mockReturnValue(refreshPromise);

      const response1 = {
        status: 200,
        data: { message: "Success 1" }
      };

      const response2 = {
        status: 200,
        data: { message: "Success 2" }
      };

      mockAxiosInstance.request
        .mockResolvedValueOnce(response1)
        .mockResolvedValueOnce(response2);

      // Start both requests
      const promise1 = responseInterceptor.onRejected(error1);
      const promise2 = responseInterceptor.onRejected(error2);

      // Resolve the refresh
      resolveRefresh(newAccessToken);

      // Wait for both to complete
      const [result1, result2] = await Promise.all([promise1, promise2]);

      // Refresh should only be called once
      expect(mockAuthContext.refreshToken).toHaveBeenCalledTimes(1);

      // Both requests should be retried with new token
      expect(request1.headers.Authorization).toBe(`Bearer ${newAccessToken}`);
      expect(request2.headers.Authorization).toBe(`Bearer ${newAccessToken}`);

      expect(result1).toEqual(response1);
      expect(result2).toEqual(response2);
    });

    it("should reject queued requests if token refresh fails", async () => {
      // First request triggers token refresh
      const request1 = {
        headers: {},
        url: "/api/v1/test1"
      };

      const error1 = {
        response: {
          status: 401,
          data: { error_code: "token_expired" }
        },
        config: request1
      };

      // Second request comes in while refresh is in progress
      const request2 = {
        headers: {},
        url: "/api/v1/test2"
      };

      const error2 = {
        response: {
          status: 401,
          data: { error_code: "token_expired" }
        },
        config: request2
      };

      const refreshError = new Error("Refresh token invalid");
      
      // Mock refresh to take some time then fail
      let rejectRefresh;
      const refreshPromise = new Promise((resolve, reject) => {
        rejectRefresh = reject;
      });
      mockAuthContext.refreshToken.mockReturnValue(refreshPromise);
      mockAuthContext.logout.mockResolvedValue();

      // Mock window.location
      delete global.window;
      global.window = { location: { href: "" } };

      // Start both requests
      const promise1 = responseInterceptor.onRejected(error1);
      const promise2 = responseInterceptor.onRejected(error2);

      // Reject the refresh
      rejectRefresh(refreshError);

      // Both should reject
      await expect(promise1).rejects.toThrow("Refresh token invalid");
      await expect(promise2).rejects.toThrow("Refresh token invalid");

      // Refresh should only be called once
      expect(mockAuthContext.refreshToken).toHaveBeenCalledTimes(1);
      expect(mockAuthContext.logout).toHaveBeenCalledTimes(1);
    });
  });

  describe("getApiClient", () => {
    it("should return the configured axios instance", () => {
      const client = getApiClient();
      expect(client).toBeDefined();
    });
  });
});
