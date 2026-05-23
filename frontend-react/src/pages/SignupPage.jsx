import { useState } from "react";
import { Link, useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTranslate } from "../hooks/useTranslate";

/**
 * Signup Page Component
 * 
 * Provides user registration interface with email/password authentication.
 * 
 * Features:
 * - Email, password, and confirm password input fields
 * - Real-time password strength indicator
 * - Password match validation
 * - Error message display for failed registration
 * - Loading state during registration
 * - Link to login page for existing users
 * - Redirect to login page with success message after registration
 * 
 * Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9, 12.10
 */
const SignupPage = () => {
  const navigate = useNavigate();
  const { signup, isAuthenticated } = useAuth();
  const t = useTranslate();

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  // Form state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Password strength calculation
  const calculatePasswordStrength = (pwd) => {
    let strength = 0;
    
    if (pwd.length >= 8) strength += 1;
    if (pwd.length >= 12) strength += 1;
    if (/[a-z]/.test(pwd)) strength += 1;
    if (/[A-Z]/.test(pwd)) strength += 1;
    if (/[0-9]/.test(pwd)) strength += 1;
    if (/[^a-zA-Z0-9]/.test(pwd)) strength += 1;
    
    return strength;
  };

  const passwordStrength = calculatePasswordStrength(password);
  
  const getStrengthLabel = (strength) => {
    if (strength === 0) return { label: "", color: "" };
    if (strength <= 2) return { label: "Weak", color: "bg-red-500" };
    if (strength <= 4) return { label: "Fair", color: "bg-yellow-500" };
    return { label: "Strong", color: "bg-green-500" };
  };

  const strengthInfo = getStrengthLabel(passwordStrength);

  // Form validation
  const isValidEmail = (email) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const isValidPassword = (pwd) => {
    // Min 8 chars, 1 upper, 1 lower, 1 number, 1 special
    return (
      pwd.length >= 8 &&
      /[a-z]/.test(pwd) &&
      /[A-Z]/.test(pwd) &&
      /[0-9]/.test(pwd) &&
      /[^a-zA-Z0-9]/.test(pwd)
    );
  };

  const passwordsMatch = password && confirmPassword && password === confirmPassword;
  const canSubmit = 
    email && 
    password && 
    confirmPassword && 
    isValidEmail(email) && 
    isValidPassword(password) && 
    passwordsMatch && 
    !loading;

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Clear previous errors
    setError("");

    // Validate email format
    if (!isValidEmail(email)) {
      setError("Please enter a valid email address");
      return;
    }

    // Validate password strength
    if (!isValidPassword(password)) {
      setError(
        "Password must be at least 8 characters and include uppercase, lowercase, number, and special character"
      );
      return;
    }

    // Validate passwords match
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);

    try {
      await signup(email, password);
      
      // Redirect to dashboard with replace
      navigate("/dashboard", { replace: true });
    } catch (err) {
      console.error("Signup error:", err);
      
      // Extract error safely
      let errorMessage = "Registration failed. Please try again.";
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
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </div>
          <h2 className="app-shell-title mt-2 text-3xl font-bold tracking-tight text-white">
            Create your account
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Join the healthcare AI assistant
          </p>
        </div>

        {/* Signup Form */}
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
              <label htmlFor="email" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Email address
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
                  className="block w-full appearance-none rounded-xl border border-slate-300/50 bg-white/50 px-4 py-3 text-slate-900 placeholder-slate-400 shadow-inner backdrop-blur-sm transition-all focus:border-medical-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-medical-500/20 dark:border-slate-600/50 dark:bg-slate-800/50 dark:text-slate-100 dark:placeholder-slate-500 dark:focus:bg-slate-800 sm:text-sm"
                  placeholder="you@example.com"
                  disabled={loading}
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Password
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full appearance-none rounded-xl border border-slate-300/50 bg-white/50 px-4 py-3 text-slate-900 placeholder-slate-400 shadow-inner backdrop-blur-sm transition-all focus:border-medical-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-medical-500/20 dark:border-slate-600/50 dark:bg-slate-800/50 dark:text-slate-100 dark:placeholder-slate-500 dark:focus:bg-slate-800 sm:text-sm"
                  placeholder="••••••••"
                  disabled={loading}
                />
              </div>
              
              {/* Password Strength Indicator */}
              {password && (
                <div className="mt-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-600 dark:text-slate-400">
                      Password strength:
                    </span>
                    <span className={`font-medium ${
                      strengthInfo.label === "Weak" ? "text-red-600 dark:text-red-400" :
                      strengthInfo.label === "Fair" ? "text-yellow-600 dark:text-yellow-400" :
                      "text-green-600 dark:text-green-400"
                    }`}>
                      {strengthInfo.label}
                    </span>
                  </div>
                  <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                    <div
                      className={`h-full transition-all duration-300 ${strengthInfo.color}`}
                      style={{ width: `${(passwordStrength / 6) * 100}%` }}
                    />
                  </div>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    Must include: 8+ characters, uppercase, lowercase, number, special character
                  </p>
                </div>
              )}
            </div>

            {/* Confirm Password Field */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Confirm Password
              </label>
              <div className="mt-1">
                <input
                  id="confirm-password"
                  name="confirm-password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="block w-full appearance-none rounded-xl border border-slate-300/50 bg-white/50 px-4 py-3 text-slate-900 placeholder-slate-400 shadow-inner backdrop-blur-sm transition-all focus:border-medical-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-medical-500/20 dark:border-slate-600/50 dark:bg-slate-800/50 dark:text-slate-100 dark:placeholder-slate-500 dark:focus:bg-slate-800 sm:text-sm"
                  placeholder="••••••••"
                  disabled={loading}
                />
              </div>
              
              {/* Password Match Indicator */}
              {confirmPassword && (
                <p className={`mt-1 text-xs ${
                  passwordsMatch 
                    ? "text-green-600 dark:text-green-400" 
                    : "text-red-600 dark:text-red-400"
                }`}>
                  {passwordsMatch ? "✓ Passwords match" : "✗ Passwords do not match"}
                </p>
              )}
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
                    Creating account...
                  </span>
                ) : (
                  "Create account"
                )}
              </button>
            </div>
          </form>

            <div className="mt-6 text-center text-sm text-slate-400">
              Already have an account?{" "}
              <Link
                to="/login"
                className="font-semibold text-teal-300 transition-colors hover:text-teal-200"
              >
                Sign in
              </Link>
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

export default SignupPage;
