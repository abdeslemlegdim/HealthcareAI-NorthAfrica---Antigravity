import { CheckCircle2, AlertTriangle, Info, X } from "lucide-react";
import { useToast } from "../../context/ToastContext";

const iconByTone = {
  success: CheckCircle2,
  error: AlertTriangle,
  info: Info
};

const toneClasses = {
  success: "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300",
  error: "border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950/60 dark:text-red-300",
  info: "border-medical-200 bg-medical-50 text-medical-800 dark:border-medical-800 dark:bg-slate-900 dark:text-medical-300"
};

const ToastViewport = () => {
  const { toasts, dismissToast } = useToast();

  return (
    <div className="pointer-events-none fixed right-4 top-20 z-[60] flex w-[calc(100%-2rem)] max-w-sm flex-col gap-2">
      {toasts.map((toast) => {
        const Icon = iconByTone[toast.tone] || Info;
        return (
          <div
            key={toast.id}
            className={`pointer-events-auto animate-toast-in rounded-2xl border px-4 py-3 shadow-card backdrop-blur ${toneClasses[toast.tone] || toneClasses.info}`}
          >
            <div className="flex items-start gap-3">
              <Icon size={18} className="mt-0.5 shrink-0" />
              <p className="flex-1 text-sm font-medium">{toast.message}</p>
              <button
                type="button"
                className="rounded-md p-1 opacity-70 transition hover:bg-white/50 hover:opacity-100 dark:hover:bg-slate-700"
                onClick={() => dismissToast(toast.id)}
                aria-label="Dismiss notification"
              >
                <X size={14} />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default ToastViewport;
