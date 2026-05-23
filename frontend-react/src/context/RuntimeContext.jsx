import { createContext, useContext, useMemo, useState } from "react";

const RuntimeContext = createContext(null);

const initialTelemetry = {
  queryCount: 0,
  imageUploadCount: 0,
  vitalsMeasureCount: 0,
  avgResponseMs: 0,
  totalResponseMs: 0,
  requestCount: 0
};

export const RuntimeProvider = ({ children }) => {
  const [demoMode, setDemoMode] = useState(true);
  const [telemetry, setTelemetry] = useState(initialTelemetry);
  const [debugInfo, setDebugInfo] = useState({
    lastPayload: null,
    lastResponse: null,
    detectedLanguage: "N/A",
    confidence: "N/A"
  });

  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  const recordQuery = (responseMs) => {
    setTelemetry((prev) => {
      const requestCount = prev.requestCount + 1;
      const totalResponseMs = prev.totalResponseMs + (responseMs || 0);
      return {
        ...prev,
        queryCount: prev.queryCount + 1,
        requestCount,
        totalResponseMs,
        avgResponseMs: requestCount ? Math.round(totalResponseMs / requestCount) : 0
      };
    });
  };

  const recordImageUpload = (responseMs) => {
    setTelemetry((prev) => {
      const requestCount = prev.requestCount + 1;
      const totalResponseMs = prev.totalResponseMs + (responseMs || 0);
      return {
        ...prev,
        imageUploadCount: prev.imageUploadCount + 1,
        requestCount,
        totalResponseMs,
        avgResponseMs: requestCount ? Math.round(totalResponseMs / requestCount) : 0
      };
    });
  };

  const recordVitalsMeasure = (responseMs) => {
    setTelemetry((prev) => {
      const requestCount = prev.requestCount + 1;
      const totalResponseMs = prev.totalResponseMs + (responseMs || 0);
      return {
        ...prev,
        vitalsMeasureCount: prev.vitalsMeasureCount + 1,
        requestCount,
        totalResponseMs,
        avgResponseMs: requestCount ? Math.round(totalResponseMs / requestCount) : 0
      };
    });
  };

  const value = useMemo(
    () => ({
      demoMode,
      setDemoMode,
      telemetry,
      recordQuery,
      recordImageUpload,
      recordVitalsMeasure,
      debugInfo,
      setDebugInfo,
      isOffline,
      setIsOffline
    }),
    [demoMode, telemetry, debugInfo, isOffline]
  );

  return <RuntimeContext.Provider value={value}>{children}</RuntimeContext.Provider>;
};

export const useRuntime = () => {
  const context = useContext(RuntimeContext);
  if (!context) throw new Error("useRuntime must be used within RuntimeProvider");
  return context;
};
