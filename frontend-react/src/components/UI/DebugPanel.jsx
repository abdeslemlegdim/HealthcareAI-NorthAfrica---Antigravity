import { Bug, ChevronDown, ChevronUp, Copy } from "lucide-react";
import { useState } from "react";
import { useRuntime } from "../../context/RuntimeContext";
import { useToast } from "../../context/ToastContext";
import { useTranslate } from "../../hooks/useTranslate";

const DebugPanel = () => {
  const [open, setOpen] = useState(false);
  const { debugInfo } = useRuntime();
  const { pushToast } = useToast();
  const t = useTranslate();

  if (!import.meta.env.DEV) return null;

  const copyPayload = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(debugInfo, null, 2));
      pushToast(t("debug_copied"), "success");
    } catch {
      pushToast(t("debug_copy_failed"), "error");
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-[70] w-[min(92vw,360px)] rounded-2xl border border-slate-200 bg-white/95 shadow-card backdrop-blur dark:border-slate-700 dark:bg-slate-900/95">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between rounded-2xl px-3 py-2 text-left text-xs font-bold uppercase tracking-wide text-slate-700 transition hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800"
      >
        <span className="inline-flex items-center gap-2">
          <Bug size={14} /> {t("debug_panel")}
        </span>
        {open ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
      </button>

      {open ? (
        <div className="space-y-2 border-t border-slate-200 p-3 text-xs dark:border-slate-700">
          <div className="rounded-lg bg-slate-100 p-2 dark:bg-slate-800">
            <p className="mb-1 font-semibold text-slate-600 dark:text-slate-300">{t("debug_detected_language")}</p>
            <p className="break-all text-slate-800 dark:text-slate-200">{String(debugInfo.detectedLanguage)}</p>
          </div>
          <div className="rounded-lg bg-slate-100 p-2 dark:bg-slate-800">
            <p className="mb-1 font-semibold text-slate-600 dark:text-slate-300">{t("debug_confidence")}</p>
            <p className="break-all text-slate-800 dark:text-slate-200">{String(debugInfo.confidence)}</p>
          </div>
          <div className="rounded-lg bg-slate-100 p-2 dark:bg-slate-800">
            <p className="mb-1 font-semibold text-slate-600 dark:text-slate-300">{t("debug_last_payload")}</p>
            <pre className="max-h-24 overflow-auto whitespace-pre-wrap break-all text-slate-700 dark:text-slate-200">{JSON.stringify(debugInfo.lastPayload, null, 2)}</pre>
          </div>
          <div className="rounded-lg bg-slate-100 p-2 dark:bg-slate-800">
            <p className="mb-1 font-semibold text-slate-600 dark:text-slate-300">{t("debug_last_response")}</p>
            <pre className="max-h-28 overflow-auto whitespace-pre-wrap break-all text-slate-700 dark:text-slate-200">{JSON.stringify(debugInfo.lastResponse, null, 2)}</pre>
          </div>
          <button
            type="button"
            onClick={copyPayload}
            className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-slate-300 bg-white px-3 py-2 font-semibold text-slate-700 transition active:scale-95 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
          >
            <Copy size={14} /> {t("debug_copy_data")}
          </button>
        </div>
      ) : null}
    </div>
  );
};

export default DebugPanel;
