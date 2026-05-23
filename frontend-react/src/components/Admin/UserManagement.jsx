import { useState, useEffect } from "react";
import PropTypes from "prop-types";
import axios from "axios";
import { useTranslate } from "../../hooks/useTranslate";

/**
 * User Management Component
 * 
 * Advanced user management interface for admins with search, filter,
 * pagination, and user actions (view, disable, enable, delete).
 * 
 * Features:
 * - Search users by email
 * - Filter by active/inactive status
 * - Pagination with configurable page size
 * - User actions: view details, disable, enable, delete
 * - Confirmation dialogs for destructive actions
 * - Real-time UI updates after actions
 * 
 * Requirements: 23.3, 23.4, 23.5, 23.6, 23.7
 */
const UserManagement = ({ onUserSelect }) => {
  const t = useTranslate();

  // State
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [filterActive, setFilterActive] = useState("all"); // "all", "active", "inactive"
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalUsers, setTotalUsers] = useState(0);
  const [actionLoading, setActionLoading] = useState(null); // user_id being acted upon
  const [confirmDialog, setConfirmDialog] = useState(null); // { action, user }

  // Fetch users
  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError("");

      const accessToken = localStorage.getItem("access_token");
      if (!accessToken) {
        throw new Error("No access token available");
      }

      // Build query parameters
      const params = {
        skip: (currentPage - 1) * pageSize,
        limit: pageSize
      };

      if (searchQuery) {
        params.search = searchQuery;
      }

      if (filterActive !== "all") {
        params.is_active = filterActive === "active";
      }

      const response = await axios.get("/api/v1/admin/users", {
        params,
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      });

      setUsers(response.data);
      // Note: Backend doesn't return total count, so we estimate
      setTotalUsers(response.data.length === pageSize ? (currentPage * pageSize) + 1 : (currentPage - 1) * pageSize + response.data.length);
    } catch (err) {
      console.error("Failed to fetch users:", err);
      setError(
        err.response?.data?.detail ||
        err.message ||
        "Failed to load users"
      );
    } finally {
      setLoading(false);
    }
  };

  // Fetch users on mount and when filters change
  useEffect(() => {
    fetchUsers();
  }, [currentPage, pageSize, searchQuery, filterActive]);

  // Handle search input change (debounced)
  useEffect(() => {
    const timer = setTimeout(() => {
      setCurrentPage(1); // Reset to first page on search
    }, 500);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Handle user action
  const handleUserAction = async (action, user) => {
    try {
      setActionLoading(user.id);
      setError("");

      const accessToken = localStorage.getItem("access_token");
      if (!accessToken) {
        throw new Error("No access token available");
      }

      let endpoint = "";
      let method = "PUT";

      switch (action) {
        case "disable":
          endpoint = `/api/v1/admin/users/${user.id}/disable`;
          break;
        case "enable":
          endpoint = `/api/v1/admin/users/${user.id}/enable`;
          break;
        case "delete":
          endpoint = `/api/v1/admin/users/${user.id}`;
          method = "DELETE";
          break;
        default:
          throw new Error(`Unknown action: ${action}`);
      }

      await axios({
        method,
        url: endpoint,
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      });

      // Refresh user list
      await fetchUsers();

      // Close confirmation dialog
      setConfirmDialog(null);
    } catch (err) {
      console.error(`Failed to ${action} user:`, err);
      setError(
        err.response?.data?.detail ||
        err.message ||
        `Failed to ${action} user`
      );
    } finally {
      setActionLoading(null);
    }
  };

  // Show confirmation dialog
  const showConfirmDialog = (action, user) => {
    setConfirmDialog({ action, user });
  };

  // Cancel confirmation dialog
  const cancelConfirmDialog = () => {
    setConfirmDialog(null);
  };

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

  // Calculate total pages
  const totalPages = Math.ceil(totalUsers / pageSize);

  return (
    <div className="rounded-lg bg-white p-6 shadow dark:bg-slate-800">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          {t("user_management") || "User Management"}
        </h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          {t("user_management_subtitle") || "Search, filter, and manage user accounts"}
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 rounded-md bg-red-50 p-4 dark:bg-red-900/20">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Search and Filter */}
      <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {/* Search */}
        <div className="flex-1">
          <label htmlFor="search" className="sr-only">
            {t("search_users") || "Search users"}
          </label>
          <div className="relative">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
              <svg className="h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              id="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t("search_by_email") || "Search by email..."}
              className="block w-full rounded-md border border-slate-300 bg-white py-2 pl-10 pr-3 text-sm placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500"
            />
          </div>
        </div>

        {/* Filter */}
        <div className="flex items-center gap-2">
          <label htmlFor="filter" className="text-sm font-medium text-slate-700 dark:text-slate-300">
            {t("status") || "Status"}:
          </label>
          <select
            id="filter"
            value={filterActive}
            onChange={(e) => {
              setFilterActive(e.target.value);
              setCurrentPage(1);
            }}
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
          >
            <option value="all">{t("all_users") || "All Users"}</option>
            <option value="active">{t("active_only") || "Active Only"}</option>
            <option value="inactive">{t("inactive_only") || "Inactive Only"}</option>
          </select>
        </div>

        {/* Page Size */}
        <div className="flex items-center gap-2">
          <label htmlFor="pageSize" className="text-sm font-medium text-slate-700 dark:text-slate-300">
            {t("per_page") || "Per page"}:
          </label>
          <select
            id="pageSize"
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setCurrentPage(1);
            }}
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
          >
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </div>
      </div>

      {/* User Table */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent" />
        </div>
      ) : users.length === 0 ? (
        <div className="py-12 text-center">
          <svg className="mx-auto h-12 w-12 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            {t("no_users_found") || "No users found"}
          </p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
              <thead className="bg-slate-50 dark:bg-slate-700/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    {t("email") || "Email"}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    {t("status") || "Status"}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    {t("role") || "Role"}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    {t("created") || "Created"}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    {t("last_activity") || "Last Activity"}
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    {t("actions") || "Actions"}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white dark:divide-slate-700 dark:bg-slate-800">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                    <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-slate-900 dark:text-slate-100">
                      {user.email}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm">
                      <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                        user.is_active
                          ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                          : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
                      }`}>
                        {user.is_active ? (t("active") || "Active") : (t("inactive") || "Inactive")}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm">
                      <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                        user.is_admin
                          ? "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400"
                          : "bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300"
                      }`}>
                        {user.is_admin ? (t("admin") || "Admin") : (t("user") || "User")}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-500 dark:text-slate-400">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-500 dark:text-slate-400">
                      {formatTimestamp(user.last_activity_at)}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                      <div className="flex items-center justify-end gap-2">
                        {/* View Details */}
                        {onUserSelect && (
                          <button
                            onClick={() => onUserSelect(user)}
                            className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300"
                            title={t("view_details") || "View details"}
                          >
                            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                          </button>
                        )}

                        {/* Enable/Disable */}
                        {user.is_active ? (
                          <button
                            onClick={() => showConfirmDialog("disable", user)}
                            disabled={actionLoading === user.id}
                            className="text-orange-600 hover:text-orange-900 disabled:opacity-50 dark:text-orange-400 dark:hover:text-orange-300"
                            title={t("disable_user") || "Disable user"}
                          >
                            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                            </svg>
                          </button>
                        ) : (
                          <button
                            onClick={() => handleUserAction("enable", user)}
                            disabled={actionLoading === user.id}
                            className="text-green-600 hover:text-green-900 disabled:opacity-50 dark:text-green-400 dark:hover:text-green-300"
                            title={t("enable_user") || "Enable user"}
                          >
                            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </button>
                        )}

                        {/* Delete */}
                        <button
                          onClick={() => showConfirmDialog("delete", user)}
                          disabled={actionLoading === user.id}
                          className="text-red-600 hover:text-red-900 disabled:opacity-50 dark:text-red-400 dark:hover:text-red-300"
                          title={t("delete_user") || "Delete user"}
                        >
                          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm text-slate-600 dark:text-slate-400">
                {t("showing") || "Showing"} {(currentPage - 1) * pageSize + 1} - {Math.min(currentPage * pageSize, totalUsers)} {t("of") || "of"} {totalUsers}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="rounded-md border border-slate-300 bg-white px-3 py-1 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
                >
                  {t("previous") || "Previous"}
                </button>
                <span className="flex items-center px-3 text-sm text-slate-600 dark:text-slate-400">
                  {t("page") || "Page"} {currentPage} {t("of") || "of"} {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="rounded-md border border-slate-300 bg-white px-3 py-1 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
                >
                  {t("next") || "Next"}
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Confirmation Dialog */}
      {confirmDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl dark:bg-slate-800">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {confirmDialog.action === "delete"
                ? (t("confirm_delete") || "Confirm Delete")
                : (t("confirm_disable") || "Confirm Disable")}
            </h3>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
              {confirmDialog.action === "delete"
                ? (t("confirm_delete_message") || `Are you sure you want to delete user ${confirmDialog.user.email}? This action cannot be undone.`)
                : (t("confirm_disable_message") || `Are you sure you want to disable user ${confirmDialog.user.email}? They will not be able to log in.`)}
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={cancelConfirmDialog}
                disabled={actionLoading === confirmDialog.user.id}
                className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
              >
                {t("cancel") || "Cancel"}
              </button>
              <button
                onClick={() => handleUserAction(confirmDialog.action, confirmDialog.user)}
                disabled={actionLoading === confirmDialog.user.id}
                className={`rounded-md px-4 py-2 text-sm font-medium text-white disabled:opacity-50 ${
                  confirmDialog.action === "delete"
                    ? "bg-red-600 hover:bg-red-700"
                    : "bg-orange-600 hover:bg-orange-700"
                }`}
              >
                {actionLoading === confirmDialog.user.id ? (
                  <span className="flex items-center gap-2">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-solid border-white border-r-transparent" />
                    {t("processing") || "Processing..."}
                  </span>
                ) : (
                  confirmDialog.action === "delete"
                    ? (t("delete") || "Delete")
                    : (t("disable") || "Disable")
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

UserManagement.propTypes = {
  onUserSelect: PropTypes.func
};

export default UserManagement;
