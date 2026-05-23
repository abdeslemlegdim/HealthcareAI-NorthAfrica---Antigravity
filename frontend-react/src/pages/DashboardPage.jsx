import { useCallback, useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTranslate } from "../hooks/useTranslate";
import { Activity, MessageSquare, Image as ImageIcon, ArrowRight, Home } from "lucide-react";
import API from "../services/api";
import UsageDashboard from "../components/UsageDashboard";

const ACTIVITY_LABEL_KEYS = {
  chat: "dashboard_activity_chat_label",
  imaging: "dashboard_activity_imaging_label",
  vitals: "dashboard_activity_vitals_label"
};

const QUICK_LINK_KEYS = {
  "/dashboard": "dashboard",
  "/chat": "chat",
  "/imaging": "imaging",
  "/vitals": "vitals"
};

const RECOMMENDATION_KEYS = {
  "Try using the platform more regularly to get better health insights": "dashboard_rec_use_more",
  "You're doing well! Consider exploring more features": "dashboard_rec_explore_more",
  "Excellent engagement! Keep up the great work": "dashboard_rec_excellent",
  "Try the Chat Assistant to ask health-related questions": "dashboard_rec_try_chat",
  "Upload a medical image for AI-powered analysis": "dashboard_rec_try_imaging",
  "Record your vital signs to track your health over time": "dashboard_rec_try_vitals",
  "You haven't been active this week. Check in with your health!": "dashboard_rec_inactive_week",
  "Consider checking your health metrics more frequently": "dashboard_rec_more_frequent"
};

/**
 * Dashboard Page Component
 * 
 * Personalized user dashboard displaying profile information and usage statistics.
 * 
 * Features:
 * - User profile (email, account creation date, account age)
 * - Usage statistics with visual charts (chat queries, images analyzed, vitals recorded)
 * - Usage statistics for this week and this month
 * - Recent activities timeline (last 10 activities with timestamps)
 * - Usage trends charts (daily/weekly/monthly)
 * - Health insights (engagement score, recommendations)
 * - Quick access links to frequently used features
 * - Logout button
 * - Loading indicators while fetching data
 * - Error messages if data cannot be loaded
 * 
 * Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9, 13.10
 */
const DashboardPage = () => {
  const navigate = useNavigate();
  const { user, logout, isAuthenticated } = useAuth();
  const t = useTranslate();

  const translateQuickLink = (link, field) => {
    const routeKey = QUICK_LINK_KEYS[link?.url] || "dashboard";
    return t(`dashboard_quick_${routeKey}_${field}`) || link?.[field] || "";
  };

  const translateRecommendation = (rec) => {
    const key = RECOMMENDATION_KEYS[rec];
    return key ? t(key) : rec;
  };

  const translateActivityType = (type) => {
    const normalized = String(type || "").toLowerCase();
    const key = ACTIVITY_LABEL_KEYS[normalized];
    return key ? t(key) : type;
  };

  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const response = await API.get("/api/v1/auth/dashboard");
      setDashboardData(response.data);
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
      let errorMessage = "Failed to load dashboard data";
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          errorMessage = err.response.data.detail.map(d => d.msg || String(d)).join(", ");
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch dashboard data
  useEffect(() => {
    if (isAuthenticated) {
      fetchDashboardData();
    }

    const refreshTimer = isAuthenticated ? setInterval(fetchDashboardData, 15000) : null;

    const handleFocus = () => {
      if (isAuthenticated) {
        fetchDashboardData();
      }
    };

    window.addEventListener("focus", handleFocus);

    return () => {
      if (refreshTimer) {
        clearInterval(refreshTimer);
      }
      window.removeEventListener("focus", handleFocus);
    };
  }, [isAuthenticated, fetchDashboardData]);

  // Handle logout
  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login");
    } catch (err) {
      console.error("Logout error:", err);
    }
  };

  // Calculate account age
  const getAccountAge = (createdAt) => {
    if (!createdAt) return "N/A";
    
    const created = new Date(createdAt);
    const now = new Date();
    const diffTime = Math.abs(now - created);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return "1 day";
    if (diffDays < 30) return `${diffDays} days`;
    
    const diffMonths = Math.floor(diffDays / 30);
    if (diffMonths === 1) return "1 month";
    if (diffMonths < 12) return `${diffMonths} months`;
    
    const diffYears = Math.floor(diffMonths / 12);
    return diffYears === 1 ? "1 year" : `${diffYears} years`;
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString(undefined, {
      year: "numeric",
      month: "long",
      day: "numeric"
    });
  };

  // Format timestamp
  const formatTimestamp = (dateString) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const dashboardTools = [
    {
      to: "/imaging",
      icon: <ImageIcon size={24} />,
      titleKey: "dashboard_tool_imaging_title",
      descriptionKey: "dashboard_tool_imaging_description",
      actionKey: "dashboard_tool_imaging_action",
      gradientClass: "from-medical-400/20 to-teal-400/20 text-teal-200",
      gradientHoverClass: "from-medical-400/10 via-transparent to-transparent",
      actionTextClass: "text-teal-300 hover:text-teal-200"
    },
    {
      to: "/chat",
      icon: <MessageSquare size={24} />,
      titleKey: "dashboard_tool_chat_title",
      descriptionKey: "dashboard_tool_chat_description",
      actionKey: "dashboard_tool_chat_action",
      gradientClass: "from-teal-400/20 to-cyan-400/20 text-teal-200",
      gradientHoverClass: "from-teal-400/10 via-transparent to-transparent",
      actionTextClass: "text-teal-300 hover:text-teal-200"
    },
    {
      to: "/vitals",
      icon: <Activity size={24} />,
      titleKey: "dashboard_tool_vitals_title",
      descriptionKey: "dashboard_tool_vitals_description",
      actionKey: "dashboard_tool_vitals_action",
      gradientClass: "from-rose-400/20 to-orange-400/20 text-rose-200",
      gradientHoverClass: "from-rose-400/10 via-transparent to-transparent",
      actionTextClass: "text-rose-300 hover:text-rose-200"
    }
  ];

  if (loading) {
    return (
      <div className="app-page flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-teal-400 border-r-transparent shadow-[0_0_24px_rgba(45,212,191,0.25)]" />
          <p className="mt-4 text-sm text-slate-300">
            {t("dashboard_loading")}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-page min-h-screen py-8 animate-fade-in">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="app-shell-panel mb-6 flex flex-col gap-4 p-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="app-chip mb-3">{t("dashboard_chip")}</div>
            <h1 className="app-shell-title text-3xl font-bold text-white">
              {t("dashboard_title")}
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              {t("dashboard_welcome", { email: user?.email })}
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="group relative flex items-center justify-center overflow-hidden rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-slate-100 shadow-sm backdrop-blur-sm transition-all hover:scale-[1.02] hover:bg-white/10 hover:shadow-glow"
          >
            {t("dashboard_logout")}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 rounded-2xl border border-red-400/20 bg-red-500/10 p-4">
            <p className="text-sm text-red-100">{error}</p>
          </div>
        )}

        <div className="mb-8 grid gap-4 lg:grid-cols-[1.4fr_0.8fr]">
          <div className="app-shell-panel p-6">
            <div className="app-chip mb-4">{t("dashboard_mission_chip")}</div>
            <h2 className="app-shell-title text-2xl font-bold text-white">{t("dashboard_mission_title")}</h2>
            <p className="mt-2 max-w-2xl text-sm text-slate-300">
              {t("dashboard_mission_description")}
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
            <div className="app-metric">
              <p className="text-xs uppercase tracking-wide text-slate-400">{t("dashboard_metric_chat")}</p>
              <p className="mt-2 text-2xl font-bold text-white">{dashboardData?.statistics?.total_chat_queries || 0}</p>
            </div>
            <div className="app-metric">
              <p className="text-xs uppercase tracking-wide text-slate-400">{t("dashboard_metric_images")}</p>
              <p className="mt-2 text-2xl font-bold text-white">{dashboardData?.statistics?.total_images_analyzed || 0}</p>
            </div>
            <div className="app-metric">
              <p className="text-xs uppercase tracking-wide text-slate-400">{t("dashboard_metric_vitals")}</p>
              <p className="mt-2 text-2xl font-bold text-white">{dashboardData?.statistics?.total_vital_measurements || 0}</p>
            </div>
          </div>
        </div>

        {/* Core Medical Tools */}
        <div className="mb-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3 animate-slide-up" style={{ animationDelay: "50ms" }}>
          {dashboardTools.map((tool) => (
            <Link
              key={tool.to}
              to={tool.to}
              className="group relative flex flex-col justify-between overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/6 to-white/3 p-6 shadow-[0_24px_80px_rgba(0,0,0,0.34)] backdrop-blur-2xl transition-all hover:scale-[1.02] hover:border-teal-400/30 hover:shadow-glow"
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${tool.gradientHoverClass} opacity-0 transition-opacity group-hover:opacity-100`} />
              <div className="relative z-10">
                <div className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${tool.gradientClass} shadow-inner`}>
                  {tool.icon}
                </div>
                <h3 className="mb-2 text-lg font-bold text-white">{t(tool.titleKey)}</h3>
                <p className="text-sm text-slate-300">
                  {t(tool.descriptionKey)}
                </p>
              </div>
              <div className={`relative z-10 mt-6 flex items-center text-sm font-semibold transition-colors ${tool.actionTextClass}`}>
                {t(tool.actionKey)}
                <ArrowRight size={16} className="ml-1 transition-transform group-hover:translate-x-1" />
              </div>
            </Link>
          ))}
        </div>

        {/* Profile Section */}
        <div className="mb-6 glass-card rounded-2xl p-6 sm:p-8 animate-slide-up" style={{ animationDelay: "100ms" }}>
          <h2 className="mb-4 text-xl font-semibold text-slate-900 dark:text-slate-100">
            {t("dashboard_profile")}
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                {t("dashboard_profile_email")}
              </p>
              <p className="mt-1 font-medium text-slate-900 dark:text-slate-100">
                {user?.email}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                {t("dashboard_profile_created")}
              </p>
              <p className="mt-1 font-medium text-slate-900 dark:text-slate-100">
                {formatDate(user?.created_at)}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                {t("dashboard_profile_age")}
              </p>
              <p className="mt-1 font-medium text-slate-900 dark:text-slate-100">
                {getAccountAge(user?.created_at)}
              </p>
            </div>
          </div>
        </div>

        {/* Usage Statistics */}
        {dashboardData?.statistics && (
          <div className="mb-6 glass-card rounded-2xl p-6 sm:p-8 animate-slide-up" style={{ animationDelay: "200ms" }}>
            <h2 className="mb-4 text-xl font-semibold text-slate-900 dark:text-slate-100">
              {t("dashboard_usage_title")}
            </h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-xl border border-blue-200/50 bg-blue-50/50 p-5 backdrop-blur-sm transition-all hover:scale-[1.02] dark:border-blue-800/50 dark:bg-blue-900/20">
                  <p className="text-sm text-blue-600 dark:text-blue-400">
                    {t("dashboard_metric_total_chat")}
                  </p>
                <p className="mt-2 text-3xl font-bold text-blue-900 dark:text-blue-100">
                  {dashboardData.statistics.total_chat_queries || 0}
                </p>
              </div>
              <div className="rounded-xl border border-green-200/50 bg-green-50/50 p-5 backdrop-blur-sm transition-all hover:scale-[1.02] dark:border-green-800/50 dark:bg-green-900/20">
                  <p className="text-sm text-green-600 dark:text-green-400">
                    {t("dashboard_metric_total_images")}
                  </p>
                <p className="mt-2 text-3xl font-bold text-green-900 dark:text-green-100">
                  {dashboardData.statistics.total_images_analyzed || 0}
                </p>
              </div>
              <div className="rounded-xl border border-purple-200/50 bg-purple-50/50 p-5 backdrop-blur-sm transition-all hover:scale-[1.02] dark:border-purple-800/50 dark:bg-purple-900/20">
                  <p className="text-sm text-purple-600 dark:text-purple-400">
                    {t("dashboard_metric_total_vitals")}
                  </p>
                <p className="mt-2 text-3xl font-bold text-purple-900 dark:text-purple-100">
                  {dashboardData.statistics.total_vital_measurements || 0}
                </p>
              </div>
              <div className="rounded-xl border border-orange-200/50 bg-orange-50/50 p-5 backdrop-blur-sm transition-all hover:scale-[1.02] dark:border-orange-800/50 dark:bg-orange-900/20">
                  <p className="text-sm text-orange-600 dark:text-orange-400">
                    {t("dashboard_metric_this_week")}
                  </p>
                <p className="mt-2 text-3xl font-bold text-orange-900 dark:text-orange-100">
                  {dashboardData.statistics.this_week_queries || 0}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Credits / Usage Dashboard */}
        <div className="mb-6 glass-card rounded-2xl p-6 sm:p-8 animate-slide-up" style={{ animationDelay: "220ms" }}>
          <UsageDashboard accountId={dashboardData?.account_id || user?.account_id || user?.id} />
        </div>

        {/* Recent Activities */}
        {dashboardData?.recent_activities && dashboardData.recent_activities.length > 0 && (
          <div className="mb-6 glass-card rounded-2xl p-6 sm:p-8 animate-slide-up" style={{ animationDelay: "300ms" }}>
            <h2 className="mb-4 text-xl font-semibold text-slate-900 dark:text-slate-100">
              {t("dashboard_recent_activities")}
            </h2>
            <div className="space-y-3">
              {dashboardData.recent_activities.map((activity, index) => (
                <div
                  key={index}
                  className="flex items-start space-x-3 rounded-xl border border-slate-200/50 bg-white/50 p-4 backdrop-blur-sm transition-all hover:shadow-sm dark:border-slate-700/50 dark:bg-slate-800/50"
                >
                  <div className="flex-shrink-0">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-900/30">
                      <span className="text-xs font-medium text-indigo-600 dark:text-indigo-400">
                        {translateActivityType(activity.activity_type)?.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                      {translateActivityType(activity.activity_type)}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {formatTimestamp(activity.timestamp)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Health Insights */}
        {dashboardData?.health_insights && (
          <div className="mb-6 glass-card rounded-2xl p-6 sm:p-8 animate-slide-up" style={{ animationDelay: "400ms" }}>
            <h2 className="mb-4 text-xl font-semibold text-slate-900 dark:text-slate-100">
              {t("dashboard_health_insights")}
            </h2>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {t("dashboard_engagement_score")}
                </p>
                <div className="mt-2 flex items-center">
                  <div className="flex-1">
                    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                      <div
                        className="h-full bg-indigo-600 transition-all duration-300"
                        style={{ 
                          width: `${Math.min(100, (dashboardData.health_insights.engagement_score || 0) * 10)}%` 
                        }}
                      />
                    </div>
                  </div>
                  <span className="ml-3 text-sm font-medium text-slate-900 dark:text-slate-100">
                    {(dashboardData.health_insights.engagement_score || 0).toFixed(1)}/10
                  </span>
                </div>
              </div>
              {dashboardData.health_insights.recommendations && 
               dashboardData.health_insights.recommendations.length > 0 && (
                <div>
                  <p className="mb-2 text-sm text-slate-600 dark:text-slate-400">
                    {t("dashboard_recommendations")}
                  </p>
                  <ul className="space-y-2">
                    {dashboardData.health_insights.recommendations.map((rec, index) => (
                      <li
                        key={index}
                        className="flex items-start text-sm text-slate-700 dark:text-slate-300"
                      >
                        <span className="mr-2">•</span>
                        <span>{translateRecommendation(rec)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Quick Links */}
        {dashboardData?.quick_links && dashboardData.quick_links.length > 0 && (
          <div className="glass-card rounded-2xl p-6 sm:p-8 animate-slide-up" style={{ animationDelay: "500ms" }}>
            <h2 className="mb-4 text-xl font-semibold text-slate-900 dark:text-slate-100">
              {t("dashboard_quick_links")}
            </h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {dashboardData.quick_links.map((link, index) => (
                <Link
                  key={index}
                  to={link.url}
                  className="flex items-center space-x-3 rounded-xl border border-slate-200/50 bg-white/50 p-4 backdrop-blur-sm transition-all hover:scale-[1.02] hover:shadow-md dark:border-slate-700/50 dark:bg-slate-800/50 dark:hover:bg-slate-700/80"
                >
                  <div className="flex-shrink-0">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-100 dark:bg-indigo-900/30">
                          {(() => {
                            const key = String(link.icon || "").toLowerCase();
                            if (key === "chat") return <MessageSquare size={18} className="text-indigo-600" />;
                            if (key === "image") return <ImageIcon size={18} className="text-indigo-600" />;
                            if (key === "heart") return <Activity size={18} className="text-indigo-600" />;
                            if (key === "dashboard") return <Home size={18} className="text-indigo-600" />;
                            return <span className="text-sm font-medium text-indigo-600">{String(link.icon).slice(0,2)}</span>;
                          })()}
                        </div>
                      </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                      {translateQuickLink(link, "title")}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {translateQuickLink(link, "description")}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
