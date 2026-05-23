import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import axios from "axios";

// Mock axios before importing AuthContext
const mockAxiosInstance = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
  interceptors: {
    request: {
      use: vi.fn(() => 1),
      eject: vi.fn()
    },
    response: {
      use: vi.fn(() => 1),
      eject: vi.fn()
    }
  }
};

vi.mock("axios", () => ({
  default: {
    create: vi.fn(() => mockAxiosInstance)
  }
}));

// Import after mocking
const { AuthProvider, useAuth } = await import("./AuthContext");

describe("AuthContext", () => {
  let localStorageMock;

  beforeEach(() => {
    // Setup localStorage mock with a simple in-memory store
    const store = {};
    localStorageMock = {
      getItem: vi.fn((key) => store[key] || null),
      setItem: vi.fn((key, value) => { store[key] = value; }),
      removeItem: vi.fn((key) => { delete store[key]; }),
      clear: vi.fn(() => { Object.keys(store).forEach(key => delete store[key]); })
    };
    global.localStorage = localStorageMock;

    // Clear all mocks
    vi.clearAllMocks();

    // Clear all timers
    vi.clearAllTimers();
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  describe("useAuth hook", () => {
    it("should throw error when used outside AuthProvider", () => {
      expect(() => {
        renderHook(() => useAuth());
      }).toThrow("useAuth must be used within AuthProvider");
    });

    it("should return auth context when used within AuthProvider", () => {
      const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current).toHaveProperty("isAuthenticated");
      expect(result.current).toHaveProperty("user");
      expect(result.current).toHaveProperty("loading");
      expect(result.current).toHaveProperty("login");
      expect(result.current).toHaveProperty("signup");
      expect(result.current).toHaveProperty("logout");
      expect(result.current).toHaveProperty("refreshToken");
      expect(result.current).toHaveProperty("updateProfile");
      expect(result.current).toHaveProperty("changePassword");
      expect(result.current).toHaveProperty("getSessions");
      expect(result.current).toHaveProperty("revokeSession");
      expect(result.current).toHaveProperty("revokeAllOtherSessions");
    });
  });

  describe("Initial state", () => {
    it("should initialize with unauthenticated state when no tokens exist", async () => {
      localStorageMock.getItem.mockReturnValue(null);

      const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBe(null);
    });

    it("should restore authentication state from valid tokens", async () => {
      const mockUser = {
        id: 1,
        email: "test@example.com",
        created_at: "2024-01-01T00:00:00",
        updated_at: "2024-01-01T00:00:00",
        is_active: true
      };

      // Mock stored tokens
      const futureExpiry = Date.now() + 3600000; // 1 hour from now
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === "access_token") return "valid_access_token";
        if (key === "refresh_token") return "valid_refresh_token";
        if (key === "token_expiry") return futureExpiry.toString();
        return null;
      });

      mockAxiosInstance.get.mockResolvedValue({ data: mockUser });

      const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
    });
  });

  describe("signup", () => {
    it("should register a new user and store tokens", async () => {
      const mockTokenResponse = {
        access_token: "new_access_token",
        refresh_token: "new_refresh_token",
        token_type: "bearer",
        expires_in: 1800
      };

      const mockUser = {
        id: 1,
        email: "newuser@example.com",
        created_at: "2024-01-01T00:00:00",
        updated_at: "2024-01-01T00:00:00",
        is_active: true
      };

      localStorageMock.getItem.mockReturnValue(null);
      mockAxiosInstance.post.mockResolvedValue({ data: mockTokenResponse });
      mockAxiosInstance.get.mockResolvedValue({ data: mockUser });

      const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      let userData;
      await act(async () => {
        userData = await result.current.signup("newuser@example.com", "password123");
      });

      expect(mockAxiosInstance.post).toHaveBeenCalledWith("/api/v1/auth/register", {
        email: "newuser@example.com",
        password: "password123"
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith("access_token", "new_access_token");
      expect(localStorageMock.setItem).toHaveBeenCalledWith("refresh_token", "new_refresh_token");
      expect(localStorageMock.setItem).toHaveBeenCalledWith("token_expiry", expect.any(String));

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
      expect(userData).toEqual(mockUser);
    });

    it("should handle signup failure", async () => {
      localStorageMock.getItem.mockReturnValue(null);
      mockAxiosInstance.post.mockRejectedValue(new Error("Email already exists"));

      const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await expect(
        act(async () => {
          await result.current.signup("existing@example.com", "password123");
        })
      ).rejects.toThrow("Email already exists");

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBe(null);
    });
  });

  describe("login", () => {
    it("should authenticate user and store tokens", async () => {
      const mockTokenResponse = {
        access_token: "access_token_123",
        refresh_token: "refresh_token_123",
        token_type: "bearer",
        expires_in: 1800
      };

      const mockUser = {
        id: 1,
        email: "user@example.com",
        created_at: "2024-01-01T00:00:00",
        updated_at: "2024-01-01T00:00:00",
        is_active: true
      };

      localStorageMock.getItem.mockReturnValue(null);
      mockAxiosInstance.post.mockResolvedValue({ data: mockTokenResponse });
      mockAxiosInstance.get.mockResolvedValue({ data: mockUser });

      const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      let userData;
      await act(async () => {
        userData = await result.current.login("user@example.com", "password123", true);
      });

      expect(mockAxiosInstance.post).toHaveBeenCalledWith("/api/v1/auth/login", {
        email: "user@example.com",
        password: "password123",
        remember_me: true
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith("access_token", "access_token_123");
      expect(localStorageMock.setItem).toHaveBeenCalledWith("refresh_token", "refresh_token_123");

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
      expect(userData).toEqual(mockUser);
    });

    it("should handle login failure", async () => {
      localStorageMock.getItem.mockReturnValue(null);
      mockAxiosInstance.post.mockRejectedValue(new Error("Invalid credentials"));

      const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await expect(
        act(async () => {
          await result.current.login("user@example.com", "wrongpassword");
        })
      ).rejects.toThrow("Invalid credentials");

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBe(null);
    });

    it("should not attempt refresh handling for login 401 responses", async () => {
      localStorageMock.getItem.mockReturnValue(null);

      const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
      renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
      });

      localStorageMock.getItem.mockClear();

      const responseInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls.at(-1)[1];
      const authError = {
        config: { url: "/api/v1/auth/login" },
        response: { status: 401 },
      };

      await expect(responseInterceptor(authError)).rejects.toBe(authError);
      expect(localStorageMock.getItem).not.toHaveBeenCalledWith("refresh_token");
    });
  });

  describe("logout", () => {
    it("should clear tokens and reset state", async () => {
      localStorageMock.getItem.mockReturnValue("some_token");
      mockAxiosInstance.post.mockResolvedValue({ data: { message: "Logged out" } });

      const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.logout();
      });

      expect(mockAxiosInstance.post).toHaveBeenCalledWith("/api/v1/auth/logout", {
        refresh_token: "some_token"
      });

      expect(localStorageMock.removeItem).toHaveBeenCalledWith("access_token");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("refresh_token");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("token_expiry");

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBe(null);
    });

    it("should clear local state even if server logout fails", async () => {
      localStorageMock.getItem.mockReturnValue("some_token");
      mockAxiosInstance.post.mockRejectedValue(new Error("Server error"));

      const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.logout();
      });

      expect(localStorageMock.removeItem).toHaveBeenCalledWith("access_token");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("refresh_token");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("token_expiry");

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBe(null);
    });
  });

  describe("refreshToken", () => {
    it("should refresh access token", async () => {
      const mockRefreshResponse = {
        access_token: "new_access_token",
        refresh_token: "new_refresh_token",
        token_type: "bearer",
        expires_in: 1800
      };

      localStorageMock.getItem.mockImplementation((key) => {
        if (key === "refresh_token") return "old_refresh_token";
        return null;
      });

      mockAxiosInstance.post.mockResolvedValue({ data: mockRefreshResponse });

      const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
      const { result } = renderHook(() => useAuth(), { wrapper });

      let newToken;
      await act(async () => {
        newToken = await result.current.refreshToken();
      });

      expect(mockAxiosInstance.post).toHaveBeenCalledWith("/api/v1/auth/refresh", {
        refresh_token: "old_refresh_token"
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith("access_token", "new_access_token");
      expect(localStorageMock.setItem).toHaveBeenCalledWith("refresh_token", "new_refresh_token");
      expect(newToken).toBe("new_access_token");
    });

    it("should clear auth state if refresh fails", async () => {
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === "refresh_token") return "invalid_refresh_token";
        return null;
      });

      mockAxiosInstance.post.mockRejectedValue(new Error("Invalid refresh token"));

      const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
      const { result } = renderHook(() => useAuth(), { wrapper });

      await expect(
        act(async () => {
          await result.current.refreshToken();
        })
      ).rejects.toThrow("Invalid refresh token");

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBe(null);
    });
  });

  describe("updateProfile", () => {
    it("should update user email", async () => {
      const updatedUser = {
        id: 1,
        email: "newemail@example.com",
        created_at: "2024-01-01T00:00:00",
        updated_at: "2024-01-02T00:00:00",
        is_active: true
      };

      localStorageMock.getItem.mockImplementation((key) => {
        if (key === "access_token") return "valid_token";
        return null;
      });

      mockAxiosInstance.put.mockResolvedValue({ data: updatedUser });

      const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
      const { result } = renderHook(() => useAuth(), { wrapper });

      let userData;
      await act(async () => {
        userData = await result.current.updateProfile("newemail@example.com");
      });

      expect(mockAxiosInstance.put).toHaveBeenCalledWith(
        "/api/v1/auth/me",
        { new_email: "newemail@example.com" },
        {
          headers: {
            Authorization: "Bearer valid_token"
          }
        }
      );

      expect(userData).toEqual(updatedUser);
    });
  });

  describe("changePassword", () => {
    it("should change user password", async () => {
      const mockResponse = { message: "Password changed successfully" };

      localStorageMock.getItem.mockImplementation((key) => {
        if (key === "access_token") return "valid_token";
        return null;
      });

      mockAxiosInstance.put.mockResolvedValue({ data: mockResponse });

      const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
      const { result } = renderHook(() => useAuth(), { wrapper });

      let response;
      await act(async () => {
        response = await result.current.changePassword("oldpass123", "newpass456");
      });

      expect(mockAxiosInstance.put).toHaveBeenCalledWith(
        "/api/v1/auth/me/password",
        {
          current_password: "oldpass123",
          new_password: "newpass456"
        },
        {
          headers: {
            Authorization: "Bearer valid_token"
          }
        }
      );

      expect(response).toEqual(mockResponse);
    });
  });

  describe("getSessions", () => {
    it("should fetch active sessions", async () => {
      const mockSessions = [
        { id: "session1", created_at: "2024-01-01T00:00:00" },
        { id: "session2", created_at: "2024-01-02T00:00:00" }
      ];

      localStorageMock.getItem.mockImplementation((key) => {
        if (key === "access_token") return "valid_token";
        return null;
      });

      mockAxiosInstance.get.mockResolvedValue({ data: mockSessions });

      const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
      const { result } = renderHook(() => useAuth(), { wrapper });

      let sessions;
      await act(async () => {
        sessions = await result.current.getSessions();
      });

      expect(mockAxiosInstance.get).toHaveBeenCalledWith("/api/v1/auth/sessions", {
        headers: {
          Authorization: "Bearer valid_token"
        }
      });

      expect(sessions).toEqual(mockSessions);
    });
  });

  describe("revokeSession", () => {
    it("should revoke a specific session", async () => {
      const mockResponse = { message: "Session revoked" };

      localStorageMock.getItem.mockImplementation((key) => {
        if (key === "access_token") return "valid_token";
        return null;
      });

      mockAxiosInstance.delete.mockResolvedValue({ data: mockResponse });

      const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
      const { result } = renderHook(() => useAuth(), { wrapper });

      let response;
      await act(async () => {
        response = await result.current.revokeSession("session123");
      });

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith("/api/v1/auth/sessions/session123", {
        headers: {
          Authorization: "Bearer valid_token"
        }
      });

      expect(response).toEqual(mockResponse);
    });
  });

  describe("revokeAllOtherSessions", () => {
    it("should revoke all other sessions", async () => {
      const mockResponse = { message: "All other sessions revoked" };

      localStorageMock.getItem.mockImplementation((key) => {
        if (key === "access_token") return "valid_access_token";
        if (key === "refresh_token") return "valid_refresh_token";
        return null;
      });

      mockAxiosInstance.delete.mockResolvedValue({ data: mockResponse });

      const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
      const { result } = renderHook(() => useAuth(), { wrapper });

      let response;
      await act(async () => {
        response = await result.current.revokeAllOtherSessions();
      });

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        "/api/v1/auth/sessions",
        {
          headers: {
            Authorization: "Bearer valid_access_token"
          },
          data: {
            refresh_token: "valid_refresh_token"
          }
        }
      );

      expect(response).toEqual(mockResponse);
    });
  });
});
