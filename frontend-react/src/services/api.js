import axios from "axios";
import { setupAuthInterceptor } from "./authInterceptor";

const browserHost = typeof window !== "undefined" ? window.location.hostname : "localhost";

const normalizeBaseUrl = (value, fallback) => {
  const raw = String(value || fallback || "").trim();
  if (!raw) {
    return fallback;
  }

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

const API_FALLBACK_BASE_URL = normalizeBaseUrl(
  import.meta.env.VITE_API_FALLBACK_URL,
  `http://${browserHost}:8002`
);

const LOCAL_BACKEND_PORTS = [8001, 8000, 8100, 8200, 8333, 8900];

const API_CANDIDATE_BASE_URLS = Array.from(
  new Set([
    API_BASE_URL,
    API_FALLBACK_BASE_URL,
    ...LOCAL_BACKEND_PORTS.map((port) => normalizeBaseUrl("", `http://${browserHost}:${port}`)),
  ])
);

const API = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000
});

// Setup authentication interceptor
// Note: onLogout callback should be set by the application after AuthContext is initialized
let authInterceptorCleanup = null;

export const initializeAuthInterceptor = (onLogout) => {
  // Clean up existing interceptor if any
  if (authInterceptorCleanup) {
    authInterceptorCleanup.cleanup();
  }
  
  // Setup new interceptor
  authInterceptorCleanup = setupAuthInterceptor(API, {
    onLogout,
    apiBaseUrl: API_BASE_URL
  });
};

export const getApiTargets = () => ({
  primary: API_BASE_URL,
  fallback: API_FALLBACK_BASE_URL,
  candidates: API_CANDIDATE_BASE_URLS
});

export const describeApiError = (error) => {
  const status = error?.response?.status;
  const detail = error?.response?.data?.detail;
  const method = String(error?.config?.method || "get").toUpperCase();
  const baseURL = error?.config?.baseURL || API_BASE_URL;
  const path = error?.config?.url || "";
  const requestUrl = `${baseURL}${path}`;
  const rawMessage = error?.message || "Request failed";
  const errorCode = String(error?.code || "").toUpperCase();

  const isTimeout = /timeout/i.test(rawMessage) || errorCode === "ECONNABORTED";
  const hasNetworkFailure = !error?.response && !isTimeout;

  let userMessage;
  if (status) {
    userMessage = detail ? String(detail) : `API request failed with status ${status}.`;
  } else if (isTimeout) {
    userMessage = "The request took too long to complete. Please try again.";
  } else if (hasNetworkFailure) {
    userMessage = "The backend could not be reached. Check that the server is running.";
  } else {
    userMessage = rawMessage;
  }

  const retryable = !status || status >= 500 || isTimeout || hasNetworkFailure;

  return {
    userMessage,
    toastMessage: isTimeout
      ? "Request timed out"
      : status
        ? `API error (${status})`
        : "API network error",
    retryable,
    meta: {
      status: status || null,
      method,
      requestUrl,
      primaryBaseUrl: API_BASE_URL,
      fallbackBaseUrl: API_FALLBACK_BASE_URL,
      code: error?.code || null,
      message: rawMessage,
      timeout: isTimeout
    }
  };
};

const requestWithFallback = async (config, options = {}) => {
  const retryOnStatuses = Array.isArray(options.retryOnStatuses)
    ? options.retryOnStatuses
    : [];

  const candidateBaseUrls = [
    config?.baseURL,
    API_BASE_URL,
    API_FALLBACK_BASE_URL,
    ...API_CANDIDATE_BASE_URLS,
  ].filter(Boolean);

  const uniqueCandidates = Array.from(new Set(candidateBaseUrls));

  let lastError = null;

  for (let index = 0; index < uniqueCandidates.length; index += 1) {
    const baseURL = uniqueCandidates[index];
    try {
      return await API.request({ ...config, baseURL });
    } catch (error) {
      lastError = error;
      const status = error?.response?.status;
      const isNetworkFailure = !error?.response;
      const canTryNext = isNetworkFailure || retryOnStatuses.includes(status);

      if (!canTryNext || index === uniqueCandidates.length - 1) {
        throw error;
      }
    }
  }

  throw lastError || new Error("API request failed");
};

export const queryRAG = async (data) => {
  try {
    return await requestWithFallback(
      { method: "post", url: "/api/v1/chat", data },
      { retryOnStatuses: [404] }
    );
  } catch (error) {
    if (error?.response?.status !== 404) {
      throw error;
    }

    return requestWithFallback(
      { method: "post", url: "/api/v1/rag/query", data },
      { retryOnStatuses: [404] }
    );
  }
};

export const classifyImage = (formData, options = {}) =>
  requestWithFallback({
    method: "post",
    url: "/api/v1/imaging/classify",
    data: formData,
    params: {
      explain: options.explain ?? true,
      top_k: options.topK ?? 5
    }
  });

export const explainImage = (formData, options = {}) =>
  requestWithFallback({
    method: "post",
    url: "/api/v1/imaging/explain",
    data: formData,
    params: {
      mode: options.mode || "overlay"
    },
    responseType: "blob"
  });

export const getHealth = () => requestWithFallback({ method: "get", url: "/health" });

export const deployLatestCheckpoint = () =>
  requestWithFallback({ method: "post", url: "/api/v1/imaging/deploy_latest_checkpoint" });

export const measureHeartRate = () =>
  requestWithFallback({ method: "get", url: "/api/v1/vitals/measure" });

export const measureVitalsDetailed = (data) =>
  requestWithFallback({ method: "post", url: "/api/v1/vitals/measure", data });

export default API;
