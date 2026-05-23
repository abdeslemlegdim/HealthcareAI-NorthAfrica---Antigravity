const ProgressBar = ({ value = 0, label, color = "medical" }) => {
  const safe = Math.max(0, Math.min(100, value));

  const colorMap = {
    medical: "bg-gradient-to-r from-medical-600 to-tealmed-600",
    success: "bg-gradient-to-r from-emerald-500 to-teal-500",
    warning: "bg-amber-500",
    danger: "bg-red-500"
  };

  return (
    <div className="space-y-2">
      {label ? (
        <div className="flex items-center justify-between text-sm font-medium text-slate-700 dark:text-slate-300">
          <span>{label}</span>
          <span>{safe.toFixed(1)}%</span>
        </div>
      ) : null}
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
        <div
          className={`h-full rounded-full transition-all duration-500 ${colorMap[color]}`}
          style={{ width: `${safe}%` }}
        />
      </div>
    </div>
  );
};

export default ProgressBar;
