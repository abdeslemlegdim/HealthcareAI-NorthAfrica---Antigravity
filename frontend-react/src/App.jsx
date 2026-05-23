import { useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import Navbar from "./components/Layout/Navbar";
import Sidebar from "./components/Layout/Sidebar";
import ErrorBoundary from "./components/UI/ErrorBoundary";
import OfflineBanner from "./components/UI/OfflineBanner";
import ToastViewport from "./components/UI/ToastViewport";
import { RuntimeProvider, useRuntime } from "./context/RuntimeContext";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ToastProvider } from "./context/ToastContext";
import { useLanguageStore } from "./store/languageStore";
import { useTranslate } from "./hooks/useTranslate";
import ProtectedRoute from "./components/Auth/ProtectedRoute";
import ChatPage from "./pages/ChatPage";
import DashboardPage from "./pages/DashboardPage";
import AdminDashboardPage from "./pages/AdminDashboardPage";
import ImagingPage from "./pages/ImagingPage";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import StatusPage from "./pages/StatusPage";
import VitalsPage from "./pages/VitalsPage";
import { getApiTargets, getHealth, initializeAuthInterceptor } from "./services/api";

const AppShell = () => {
  const { demoMode, setDemoMode, setIsOffline } = useRuntime();
  const { logout } = useAuth();
  const { language } = useLanguageStore();
  const t = useTranslate();

  const [backendOnline, setBackendOnline] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const location = useLocation();
  const isLandingRoute = location.pathname === "/";

  useEffect(() => {
    let mounted = true;

    const normalizeTarget = (baseUrl) => {
      try {
        const withScheme = /^https?:\/\//i.test(baseUrl) ? baseUrl : `http://${baseUrl}`;
        const parsed = new URL(withScheme);
        return `${parsed.hostname}:${parsed.port || (parsed.protocol === "https:" ? "443" : "80")}`;
      } catch {
        return baseUrl;
      }
    };

    const pingDirect = async (baseUrl) => {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 3000);
      try {
        const response = await fetch(`${baseUrl}/health`, {
          method: "GET",
          signal: controller.signal,
          headers: { Accept: "application/json" }
        });
        return response.ok;
      } catch {
        return false;
      } finally {
        clearTimeout(timer);
      }
    };

    const ping = async () => {
      const targets = getApiTargets();
      const [primaryOnline, fallbackOnline] = await Promise.all([
        pingDirect(targets.primary),
        pingDirect(targets.fallback)
      ]);

      try {
        await getHealth();
        if (!mounted) return;

        setBackendOnline(true);
      } catch {
        if (!mounted) return;

        setBackendOnline(false);
      }
    };

    ping();
    const timer = setInterval(ping, 10000);

    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = language === "ar" ? "rtl" : "ltr";
  }, [language]);

  useEffect(() => {
    initializeAuthInterceptor(logout);
  }, [logout]);

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [setIsOffline]);

  return (
    <ToastProvider>
      <ErrorBoundary>
        <div className="app-page min-h-screen text-slate-100 transition-colors duration-500">
          <Routes>
            <Route path="/" element={<LandingPage backendOnline={backendOnline} />} />
            <Route path="*" element={(
              <>
                <Navbar
                  onMenuClick={() => setSidebarOpen((open) => !open)}
                  darkMode={darkMode}
                  onToggleDarkMode={() => setDarkMode((prev) => !prev)}
                  demoMode={demoMode}
                  onToggleDemoMode={() => setDemoMode((prev) => !prev)}
                />
                <OfflineBanner />
                <ToastViewport />
                <div className="relative z-10 md:flex">
                  <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
                  <main className="flex-1 p-4 md:p-6 lg:p-8">
                    <div className="mx-auto w-full max-w-7xl">
                      <Routes>
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/signup" element={<SignupPage />} />
                        <Route 
                          path="/dashboard" 
                          element={
                            <ProtectedRoute>
                              <DashboardPage />
                            </ProtectedRoute>
                          } 
                        />
                        <Route 
                          path="/admin" 
                          element={
                            <ProtectedRoute requireAdmin={true}>
                              <AdminDashboardPage />
                            </ProtectedRoute>
                          } 
                        />
                        <Route 
                          path="/chat" 
                          element={
                            <ProtectedRoute>
                              <ChatPage />
                            </ProtectedRoute>
                          } 
                        />
                        <Route 
                          path="/imaging" 
                          element={
                            <ProtectedRoute>
                              <ImagingPage />
                            </ProtectedRoute>
                          } 
                        />
                        <Route 
                          path="/vitals" 
                          element={
                            <ProtectedRoute>
                              <VitalsPage />
                            </ProtectedRoute>
                          } 
                        />
                        <Route path="/status" element={<StatusPage />} />
                        <Route path="*" element={<Navigate to="/" replace />} />
                      </Routes>
                    </div>
                    {!isLandingRoute ? (
                      <footer className="app-shell-panel mt-10 px-5 py-4 text-center text-xs font-semibold text-slate-300 transition-all hover:shadow-glow">
                        {t("footer_research_only")}
                      </footer>
                    ) : null}
                  </main>
                </div>
              </>
            )} />
          </Routes>
        </div>
      </ErrorBoundary>
    </ToastProvider>
  );
};

const App = () => (
  <RuntimeProvider>
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  </RuntimeProvider>
);

export default App;
