import Loader from "./Loader";

const Button = ({
  children,
  onClick,
  type = "button",
  disabled = false,
  loading = false,
  variant = "primary",
  className = ""
}) => {
  const base =
    "inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-semibold tracking-wide transition-all duration-200 active:scale-95 disabled:cursor-not-allowed disabled:opacity-60";

  const variants = {
    primary: "border border-teal-300/20 bg-gradient-to-r from-teal-400 via-cyan-500 to-medical-600 text-slate-950 shadow-glow hover:scale-[1.02] hover:shadow-glow-strong",
    secondary: "border border-white/10 bg-white/5 text-slate-100 hover:bg-white/10 hover:border-teal-400/30 hover:shadow-glow",
    ghost: "border border-transparent text-slate-300 hover:bg-white/6 hover:text-white"
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`${base} ${variants[variant]} ${className}`}
    >
      {loading ? <Loader size="sm" label="" /> : null}
      {children}
    </button>
  );
};

export default Button;
