import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

/**
 * ProtectedRoute Component
 * 
 * Wrapper component that enforces authentication for routes.
 * Redirects unauthenticated users to the login page and stores
 * the original destination for post-login redirect.
 * 
 * Features:
 * - Checks authentication status from AuthContext
 * - Redirects to login page if not authenticated
 * - Stores original destination URL for post-login redirect
 * - Supports backward compatibility flag (requireAuth prop)
 * - Shows loading state while checking authentication
 * - Supports admin-only routes with requireAdmin prop
 * 
 * Requirements: 14.1, 14.2, 14.3, 14.4, 14.9
 * 
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components to render if authenticated
 * @param {boolean} [props.requireAuth=true] - Whether authentication is required
 * @param {boolean} [props.requireAdmin=false] - Whether admin role is required
 * @returns {React.ReactNode} Protected content or redirect
 */
const ProtectedRoute = ({ 
  children, 
  requireAuth = true, 
  requireAdmin = false 
}) => {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" />
          <p className="mt-4 text-sm text-slate-600 dark:text-slate-400">
            Loading...
          </p>
        </div>
      </div>
    );
  }

  // If authentication is not required (backward compatibility mode), render children
  if (!requireAuth) {
    return children;
  }

  // If not authenticated, redirect to login with original destination
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If admin is required but user is not admin, redirect to dashboard with error
  if (requireAdmin && !user?.is_admin) {
    return (
      <Navigate 
        to="/dashboard" 
        state={{ 
          error: "You do not have permission to access this page. Admin access required." 
        }} 
        replace 
      />
    );
  }

  // User is authenticated (and admin if required), render children
  return children;
};

export default ProtectedRoute;
