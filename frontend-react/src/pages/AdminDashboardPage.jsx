import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTranslate } from "../hooks/useTranslate";
import axios from "axios";

/**
 * Admin Dashboard Page Component
 * 
 * Comprehensive admin interface for user management and system monitoring.
 * 
 * Features:
 * - System-wide statistics (total users, active users, total activities)
 * - Usage charts and graphs (daily/weekly/monthly trends)
 * - Top users leaderboard
 * - Recent registrations list
 * - System health indicators
 * - Authentication failure statistics
 * 
 * Requirements: 23.1, 23.2, 23.8
 */
const AdminDashboardPage = () => {
  const { user } = useAuth();
  const t = useTranslate();

  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState(false);

  // Fetch admin dashboard data
  useEffect(() => {
    const fetchAdminDashboard = async () => {
      try {
        setLoading(true);
        setError("");

        const accessToken = localStorage.getItem("access_token");
        
        if (!accessToken) {
          throw new Error("No access token available");
        }

        const response = await axios.get("/api/v1/admin/dashboard", {
          headers: {
            Authorization: `Bearer ${accessToken}`
          }
        });

        setDashboardData(response.data);
      } catch (err) {
        console.error("Failed to fetch admin dashboard:", err);
        setError(
          err.response?.data?.detail || 
          err.message || 
          "Failed to load admin dashboard"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchAdminDashboard();
  }, []);

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
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

  // Export to CSV
  const exportToCSV = (data, filename) => {
    // Convert data to CSV format
    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(","),
      ...data.map(row => 
        headers.map(header => {
          const value = row[header];
          // Escape commas and quotes
          if (typeof value === "string" && (value.includes(",") || value.includes('"'))) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value;
        }).join(",")
      )
    ].join("\n");

    // Create blob and download
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Export user data
  const handleExportUsers = async () => {
    try {
      setExporting(true);
      setError("");

      const accessToken = localStorage.getItem("access_token");
      if (!accessToken) {
        throw new Error("No access token available");
      }

      // Fetch all users (with a high limit)
      const response = await axios.get("/api/v1/admin/users", {
        params: {
          skip: 0,
          limit: 10000
        },
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      });

      // Prepare data for export
      const exportData = response.data.map(user => ({
        id: user.id,
        email: user.email,
        is_active: user.is_active ? "Yes" : "No",
        is_admin: user.is_admin ? "Yes" : "No",
        created_at: formatDate(user.created_at),
        last_activity_at: formatTimestamp(user.last_activity_at)
      }));

      // Export to CSV
      const timestamp = new Date().toISOString().split("T")[0];
      exportToCSV(exportData, `users_export_${timestamp}.csv`);
    } catch (err) {
      console.error("Failed to export users:", err);
      setError(
        err.response?.data?.detail ||
        err.message ||
        "Failed to export users"
      );
    } finally {
      setExporting(false);
    }
  };

  // Export usage report
  const handleExportUsageReport = async () => {
    try {
      setExporting(true);
      setError("");

      if (!dashboardData) {
        throw new Error("No dashboard data available");
      }

      // Prepare usage report data
      const exportData = dashboardData.top_users.map(user => ({
        email: user.email,
        total_activities: user.total_activities,
        last_activity: formatTimestamp(user.last_activity)
      }));

      // Export to CSV
      const timestamp = new Date().toISOString().split("T")[0];
      exportToCSV(exportData, `usage_report_${timestamp}.csv`);
    } catch (err) {
      console.error("Failed to export usage report:", err);
      setError(
        err.response?.data?.detail ||
        err.message ||
        "Failed to export usage report"
      );
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent" />
          <p className="mt-4 text-sm text-slate-600 dark:text-slate-400">
            {t("loading_admin_dashboard") || "Loading admin dashboard..."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 py-8 dark:bg-slate-900">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
                {t("admin_dashboard_title") || "Admin Dashboard"}
              </h1>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                {t("admin_dashboard_subtitle") || "System overview and user management"}
              </p>
            </div>
            <div className="flex gap-3">
              {/* Export Dropdown */}
              <div className="relative">
                <button
                  onClick={() => document.getElementById("export-menu").classList.toggle("hidden")}
                  disabled={exporting}
                  className="flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  {exporting ? (t("exporting") || "Exporting...") : (t("export") || "Export")}
                </button>
                <div
                  id="export-menu"
                  className="absolute right-0 z-10 mt-2 hidden w-48 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 dark:bg-slate-700"
                >
                  <div className="py-1">
                    <button
                      onClick={() => {
                        handleExportUsers();
                        document.getElementById("export-menu").classList.add("hidden");
                      }}
                      className="block w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-600"
                    >
                      {t("export_users") || "Export Users"}
                    </button>
                    <button
                      onClick={() => {
                        handleExportUsageReport();
                        document.getElementById("export-menu").classList.add("hidden");
                      }}
                      className="block w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-600"
                    >
                      {t("export_usage_report") || "Export Usage Report"}
                    </button>
                  </div>
                </div>
              </div>
              <Link
                to="/dashboard"
                className="rounded-md bg-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-300 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
              >
                {t("back_to_dashboard") || "Back to Dashboard"}
              </Link>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 rounded-md bg-red-50 p-4 dark:bg-red-900/20">
            <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {/* System Statistics */}
        {dashboardData && (
          <>
            <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-lg bg-white p-6 shadow dark:bg-slate-800">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30">
                      <svg className="h-6 w-6 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                      {t("total_users") || "Total Users"}
                    </p>
                    <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                      {dashboardData.total_users || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-lg bg-white p-6 shadow dark:bg-slate-800">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/30">
                      <svg className="h-6 w-6 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                      {t("active_users") || "Active Users"}
                    </p>
                    <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                      {dashboardData.active_users || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-lg bg-white p-6 shadow dark:bg-slate-800">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900/30">
                      <svg className="h-6 w-6 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                      {t("total_chat_queries") || "Chat Queries"}
                    </p>
                    <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                      {dashboardData.total_chat_queries || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-lg bg-white p-6 shadow dark:bg-slate-800">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-orange-100 dark:bg-orange-900/30">
                      <svg className="h-6 w-6 text-orange-600 dark:text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                      {t("images_analyzed") || "Images Analyzed"}
                    </p>
                    <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                      {dashboardData.total_images_analyzed || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Top Users */}
            {dashboardData.top_users && dashboardData.top_users.length > 0 && (
              <div className="mb-6 rounded-lg bg-white p-6 shadow dark:bg-slate-800">
                <h2 className="mb-4 text-xl font-semibold text-slate-900 dark:text-slate-100">
                  {t("top_users") || "Top Users"}
                </h2>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                    <thead>
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                          {t("email") || "Email"}
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                          {t("total_activities") || "Total Activities"}
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                          {t("last_activity") || "Last Activity"}
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                      {dashboardData.top_users.map((topUser, index) => (
                        <tr key={index} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                          <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-900 dark:text-slate-100">
                            {topUser.email}
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-900 dark:text-slate-100">
                            {topUser.total_activities}
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-500 dark:text-slate-400">
                            {formatTimestamp(topUser.last_activity)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Recent Registrations */}
            {dashboardData.recent_registrations && dashboardData.recent_registrations.length > 0 && (
              <div className="mb-6 rounded-lg bg-white p-6 shadow dark:bg-slate-800">
                <h2 className="mb-4 text-xl font-semibold text-slate-900 dark:text-slate-100">
                  {t("recent_registrations") || "Recent Registrations"}
                </h2>
                <div className="space-y-3">
                  {dashboardData.recent_registrations.map((regUser, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between rounded-lg border border-slate-200 p-3 dark:border-slate-700"
                    >
                      <div>
                        <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                          {regUser.email}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400">
                          {formatDate(regUser.created_at)}
                        </p>
                      </div>
                      <span className={`rounded-full px-2 py-1 text-xs font-medium ${
                        regUser.is_active
                          ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                          : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
                      }`}>
                        {regUser.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* System Health */}
            {dashboardData.system_health && (
              <div className="mb-6 rounded-lg bg-white p-6 shadow dark:bg-slate-800">
                <h2 className="mb-4 text-xl font-semibold text-slate-900 dark:text-slate-100">
                  {t("system_health") || "System Health"}
                </h2>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {t("uptime") || "Uptime"}
                    </p>
                    <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-100">
                      {(dashboardData.system_health.uptime_percentage || 0).toFixed(1)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {t("avg_response_time") || "Avg Response Time"}
                    </p>
                    <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-100">
                      {(dashboardData.system_health.average_response_time || 0).toFixed(0)}ms
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {t("error_rate") || "Error Rate"}
                    </p>
                    <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-100">
                      {(dashboardData.system_health.error_rate || 0).toFixed(2)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {t("active_sessions") || "Active Sessions"}
                    </p>
                    <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-100">
                      {dashboardData.system_health.active_sessions || 0}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Authentication Failures */}
            {dashboardData.auth_failures && (
              <div className="rounded-lg bg-white p-6 shadow dark:bg-slate-800">
                <h2 className="mb-4 text-xl font-semibold text-slate-900 dark:text-slate-100">
                  {t("auth_failures") || "Authentication Failures"}
                </h2>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {t("total_failures") || "Total Failures"}
                    </p>
                    <p className="mt-1 text-2xl font-bold text-red-600 dark:text-red-400">
                      {dashboardData.auth_failures.total_failures || 0}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {t("failures_last_24h") || "Last 24 Hours"}
                    </p>
                    <p className="mt-1 text-2xl font-bold text-orange-600 dark:text-orange-400">
                      {dashboardData.auth_failures.failures_last_24h || 0}
                    </p>
                  </div>
                </div>
                {dashboardData.auth_failures.top_failure_reasons && 
                 dashboardData.auth_failures.top_failure_reasons.length > 0 && (
                  <div className="mt-4">
                    <p className="mb-2 text-sm font-medium text-slate-600 dark:text-slate-400">
                      {t("top_failure_reasons") || "Top Failure Reasons"}
                    </p>
                    <div className="space-y-2">
                      {dashboardData.auth_failures.top_failure_reasons.map((reason, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between rounded-lg bg-slate-50 p-2 dark:bg-slate-700/50"
                        >
                          <span className="text-sm text-slate-700 dark:text-slate-300">
                            {reason.reason}
                          </span>
                          <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                            {reason.count}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AdminDashboardPage;
