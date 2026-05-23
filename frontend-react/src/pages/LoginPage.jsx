import { useState } from "react";
import { Link, useNavigate, useLocation, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTranslate } from "../hooks/useTranslate";

/**
 * Login Page Component
 * 
 * Provides user login interface with email/password authentication.
 * 
 * Features:
 * - Email and password input fields with validation
 * - "Remember Me" checkbox for extended sessions
 * - Error message display for failed login attempts
 * - Loading state during authentication
 * - Link to signup page for new users
 * - Redirect to original destination after successful login
 * 
 * Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10
 */
const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();
  const t = useTranslate();

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  // Get the redirect path from location state, default to dashboard
  const from = location.state?.from?.pathname || "/dashboard";

  // Form state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Form validation
  const isValidEmail = (email) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const canSubmit = email && password && isValidEmail(email) && !loading;

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Clear previous errors
    setError("");

    // Validate email format
    if (!isValidEmail(email)) {
      setError(t("login_error_invalid_email"));
      return;
    }

    // Validate password
    if (!password) {
      setError(t("login_error_no_password"));
      return;
    }

    setLoading(true);

    try {
      await login(email, password, rememberMe);
      
      // Redirect to original destination or dashboard
      navigate(from, { replace: true });
    } catch (err) {
      console.error("Login error:", err);
      
      // Extract error safely
      let errorMessage = t("login_error_failed");
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
  };

  return (
    <div className="app-page flex min-h-screen items-center justify-center px-4 py-12 sm:px-6 lg:px-8 animate-fade-in">
      <div className="w-full max-w-md space-y-8">
        {/* Header */}
          <div className="text-center animate-slide-up">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-teal-400 via-cyan-400 to-medical-600 shadow-glow">
            <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="app-shell-title mt-2 text-3xl font-bold tracking-tight text-white">
            {t("login_title")}
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            {t("login_subtitle")}
          </p>
        </div>

        {/* Login Form */}
        <div className="app-shell-panel rounded-2xl p-8 sm:p-10 animate-slide-up" style={{ animationDelay: "100ms" }}>
          <form className="space-y-6" onSubmit={handleSubmit}>
            {/* Error Message */}
            {error && (
              <div className="rounded-2xl border border-red-400/20 bg-red-500/10 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-5 w-5 text-red-400"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-red-100">
                      {error}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-200">
                {t("label_email")}
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full appearance-none rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 placeholder-slate-500 shadow-inner backdrop-blur-sm transition-all focus:border-teal-400/40 focus:bg-white/10 focus:outline-none focus:ring-2 focus:ring-teal-400/20 sm:text-sm"
                  placeholder="you@example.com"
                  disabled={loading}
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-200">
                {t("label_password")}
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full appearance-none rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 placeholder-slate-500 shadow-inner backdrop-blur-sm transition-all focus:border-teal-400/40 focus:bg-white/10 focus:outline-none focus:ring-2 focus:ring-teal-400/20 sm:text-sm"
                  placeholder="••••••••"
                  disabled={loading}
                />
              </div>
            </div>

            {/* Remember Me Checkbox */}
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="h-4 w-4 rounded border-white/15 text-teal-400 focus:ring-teal-400"
                  disabled={loading}
                />
                <label
                  htmlFor="remember-me"
                  className="ml-2 block text-sm text-slate-200"
                >
                  {t("remember_me")}
                </label>
              </div>

              <div className="text-sm">
                <a href="#" className="font-medium text-teal-300 hover:text-teal-200"
                  onClick={(e) => {
                    e.preventDefault();
                    // TODO: Implement forgot password flow
                    alert(t("login_forgot_password_alert") || "Password reset functionality coming soon!");
                  }}
                >
                  {t("forgot_password")}
                </a>
              </div>
            </div>

            {/* Submit Button */}
            <div>
              <button
                type="submit"
                disabled={!canSubmit}
                className="group relative flex w-full justify-center overflow-hidden rounded-xl bg-gradient-to-r from-teal-400 via-cyan-500 to-medical-600 px-4 py-3 text-sm font-semibold text-slate-950 shadow-glow transition-all duration-300 hover:scale-[1.02] hover:shadow-glow-strong focus:outline-none focus:ring-2 focus:ring-teal-400 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <div className="absolute inset-0 bg-white/20 opacity-0 transition-opacity group-hover:opacity-100" />
                {loading ? (
                  <span className="flex items-center">
                    <svg
                      className="mr-2 h-4 w-4 animate-spin"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    {t("login_signing_in")}
                  </span>
                ) : (
                  t("login_sign_in")
                )}
              </button>
            </div>
          </form>

          {/* Sign Up Link */}
          <div className="mt-6 text-center">
              <div className="mt-6 text-center text-sm text-slate-400">
              {t("login_no_account")}{" "}
              <Link
                to="/signup"
                className="font-semibold text-teal-300 transition-colors hover:text-teal-200"
              >
                {t("login_sign_up")}
              </Link>
            </div>
          </div>
        </div>

        {/* Back to Home Link */}
        <div className="text-center">
          <Link to="/" className="text-sm font-medium text-slate-400 hover:text-slate-100">
            ← {t("back_to_home") || "Back to home"}
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
