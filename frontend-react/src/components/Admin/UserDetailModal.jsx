import { useEffect, useState } from "react";
import PropTypes from "prop-types";
import axios from "axios";
import { useTranslate } from "../../hooks/useTranslate";

/**
 * User Detail Modal Component
 * 
 * Displays comprehensive user information in a modal dialog.
 * 
 * Features:
 * - User profile information (email, status, role, dates)
 * - Usage statistics (chat queries, images analyzed, vitals recorded)
 * - Recent activity history with timestamps
 * - Active sessions with device info and IP addresses
 * - Audit logs for security tracking
 * 
 * Requirements: 23.4
 */
const UserDetailModal = ({ userId, onClose }) => {
  const t = useTranslate();

  const [userDetails, setUserDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("overview"); // "overview", "activities", "sessions", "audit"

  // Fetch user details
  useEffect(() => {
    const fetchUserDetails = async () => {
      try {
        setLoading(true);
        setError("");

        const accessToken = localStorage.getItem("access_token");
        if (!accessToken) {
          throw new Error("No access token available");
        }

        const response = await axios.get(`/api/v1/admin/users/${userId}`, {
          headers: {
            Authorization: `Bearer ${accessToken}`
          }
        });

        setUserDetails(response.data);
      } catch (err) {
        console.error("Failed to fetch user details:", err);
        setError(
          err.response?.data?.detail ||
          err.message ||
          "Failed to load user details"
        );
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      fetchUserDetails();
    }
  }, [userId]);

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
    if (!dateString) return "Never";
    return new Date(dateString).toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  // Handle backdrop click
  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
      onClick={handleBackdropClick}
    >
      <div className="w-full max-w-4xl rounded-lg bg-white shadow-xl dark:bg-slate-800">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 p-6 dark:border-slate-700">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {t("user_details") || "User Details"}
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="max-h-[calc(100vh-200px)] overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent" />
            </div>
          ) : error ? (
            <div className="rounded-md bg-red-50 p-4 dark:bg-red-900/20">
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </div>
          ) : userDetails ? (
            <>
              {/* Tabs */}
              <div className="mb-6 border-b border-slate-200 dark:border-slate-700">
                <nav className="-mb-px flex space-x-8">
                  <button
                    onClick={() => setActiveTab("overview")}
                    className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                      activeTab === "overview"
                        ? "border-indigo-500 text-indigo-600 dark:text-indigo-400"
                        : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300"
                    }`}
                  >
                    {t("overview") || "Overview"}
                  </button>
                  <button
                    onClick={() => setActiveTab("activities")}
                    className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                      activeTab === "activities"
                        ? "border-indigo-500 text-indigo-600 dark:text-indigo-400"
                        : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300"
                    }`}
                  >
                    {t("activities") || "Activities"} ({userDetails.activities?.length || 0})
                  </button>
                  <button
                    onClick={() => setActiveTab("sessions")}
                    className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                      activeTab === "sessions"
                        ? "border-indigo-500 text-indigo-600 dark:text-indigo-400"
                        : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300"
                    }`}
                  >
                    {t("sessions") || "Sessions"} ({userDetails.sessions?.length || 0})
                  </button>
                  <button
                    onClick={() => setActiveTab("audit")}
                    className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                      activeTab === "audit"
                        ? "border-indigo-500 text-indigo-600 dark:text-indigo-400"
                        : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300"
                    }`}
                  >
                    {t("audit_logs") || "Audit Logs"} ({userDetails.audit_logs?.length || 0})
                  </button>
                </nav>
              </div>

              {/* Tab Content */}
              {activeTab === "overview" && (
                <div className="space-y-6">
                  {/* Profile Information */}
                  <div>
                    <h3 className="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">
                      {t("profile_information") || "Profile Information"}
                    </h3>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div>
                        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                          {t("email") || "Email"}
                        </p>
                        <p className="mt-1 text-sm text-slate-900 dark:text-slate-100">
                          {userDetails.user.email}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                          {t("status") || "Status"}
                        </p>
                        <p className="mt-1">
                          <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                            userDetails.user.is_active
                              ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                              : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
                          }`}>
                            {userDetails.user.is_active ? (t("active") || "Active") : (t("inactive") || "Inactive")}
                          </span>
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                          {t("role") || "Role"}
                        </p>
                        <p className="mt-1">
                          <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                            userDetails.user.is_admin
                              ? "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400"
                              : "bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300"
                          }`}>
                            {userDetails.user.is_admin ? (t("admin") || "Admin") : (t("user") || "User")}
                          </span>
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                          {t("user_id") || "User ID"}
                        </p>
                        <p className="mt-1 text-sm text-slate-900 dark:text-slate-100">
                          {userDetails.user.id}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                          {t("created_at") || "Created At"}
                        </p>
                        <p className="mt-1 text-sm text-slate-900 dark:text-slate-100">
                          {formatTimestamp(userDetails.user.created_at)}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                          {t("last_activity") || "Last Activity"}
                        </p>
                        <p className="mt-1 text-sm text-slate-900 dark:text-slate-100">
                          {formatTimestamp(userDetails.user.last_activity_at)}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Usage Statistics */}
                  <div>
                    <h3 className="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">
                      {t("usage_statistics") || "Usage Statistics"}
                    </h3>
                    <div className="grid gap-4 sm:grid-cols-3">
                      <div className="rounded-lg bg-blue-50 p-4 dark:bg-blue-900/20">
                        <p className="text-sm font-medium text-blue-600 dark:text-blue-400">
                          {t("chat_queries") || "Chat Queries"}
                        </p>
                        <p className="mt-2 text-2xl font-bold text-blue-900 dark:text-blue-100">
                          {userDetails.statistics?.total_chat_queries || 0}
                        </p>
                      </div>
                      <div className="rounded-lg bg-purple-50 p-4 dark:bg-purple-900/20">
                        <p className="text-sm font-medium text-purple-600 dark:text-purple-400">
                          {t("images_analyzed") || "Images Analyzed"}
                        </p>
                        <p className="mt-2 text-2xl font-bold text-purple-900 dark:text-purple-100">
                          {userDetails.statistics?.total_images_analyzed || 0}
                        </p>
                      </div>
                      <div className="rounded-lg bg-green-50 p-4 dark:bg-green-900/20">
                        <p className="text-sm font-medium text-green-600 dark:text-green-400">
                          {t("vitals_recorded") || "Vitals Recorded"}
                        </p>
                        <p className="mt-2 text-2xl font-bold text-green-900 dark:text-green-100">
                          {userDetails.statistics?.total_vital_measurements || 0}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "activities" && (
                <div>
                  <h3 className="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">
                    {t("recent_activities") || "Recent Activities"}
                  </h3>
                  {userDetails.activities && userDetails.activities.length > 0 ? (
                    <div className="space-y-3">
                      {userDetails.activities.map((activity, index) => (
                        <div
                          key={index}
                          className="rounded-lg border border-slate-200 p-4 dark:border-slate-700"
                        >
                          <div className="flex items-start justify-between">
                            <div>
                              <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                                {activity.description}
                              </p>
                              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                                {formatTimestamp(activity.timestamp)}
                              </p>
                            </div>
                            <span className={`rounded-full px-2 py-1 text-xs font-medium ${
                              activity.activity_type === "chat"
                                ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
                                : activity.activity_type === "imaging"
                                ? "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400"
                                : "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                            }`}>
                              {activity.activity_type}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      {t("no_activities") || "No activities found"}
                    </p>
                  )}
                </div>
              )}

              {activeTab === "sessions" && (
                <div>
                  <h3 className="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">
                    {t("active_sessions") || "Active Sessions"}
                  </h3>
                  {userDetails.sessions && userDetails.sessions.length > 0 ? (
                    <div className="space-y-3">
                      {userDetails.sessions.map((session) => (
                        <div
                          key={session.id}
                          className="rounded-lg border border-slate-200 p-4 dark:border-slate-700"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                                {session.device_info || t("unknown_device") || "Unknown Device"}
                              </p>
                              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                                IP: {session.ip_address || "N/A"}
                              </p>
                              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                                {t("created") || "Created"}: {formatTimestamp(session.created_at)}
                              </p>
                            </div>
                            <span className={`rounded-full px-2 py-1 text-xs font-medium ${
                              session.is_active
                                ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                                : "bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300"
                            }`}>
                              {session.is_active ? (t("active") || "Active") : (t("expired") || "Expired")}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      {t("no_sessions") || "No active sessions"}
                    </p>
                  )}
                </div>
              )}

              {activeTab === "audit" && (
                <div>
                  <h3 className="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">
                    {t("audit_logs") || "Audit Logs"}
                  </h3>
                  {userDetails.audit_logs && userDetails.audit_logs.length > 0 ? (
                    <div className="space-y-3">
                      {userDetails.audit_logs.map((log, index) => (
                        <div
                          key={index}
                          className="rounded-lg border border-slate-200 p-4 dark:border-slate-700"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                                {log.event_type.replace(/_/g, " ").toUpperCase()}
                              </p>
                              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                                {formatTimestamp(log.timestamp)}
                              </p>
                              {log.ip_address && (
                                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                                  IP: {log.ip_address}
                                </p>
                              )}
                              {log.user_agent && (
                                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                                  {log.user_agent}
                                </p>
                              )}
                            </div>
                            <span className={`rounded-full px-2 py-1 text-xs font-medium ${
                              log.event_type.includes("failed")
                                ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
                                : log.event_type.includes("success")
                                ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                                : "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
                            }`}>
                              {log.event_type.split("_")[0]}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      {t("no_audit_logs") || "No audit logs found"}
                    </p>
                  )}
                </div>
              )}
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="flex justify-end border-t border-slate-200 p-6 dark:border-slate-700">
          <button
            onClick={onClose}
            className="rounded-md bg-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-300 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
          >
            {t("close") || "Close"}
          </button>
        </div>
      </div>
    </div>
  );
};

UserDetailModal.propTypes = {
  userId: PropTypes.number.isRequired,
  onClose: PropTypes.func.isRequired
};

export default UserDetailModal;
