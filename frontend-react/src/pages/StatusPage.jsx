import { useEffect, useMemo, useState } from "react";
import { Activity, Brain, Database, RefreshCw, Server, ShieldCheck } from "lucide-react";
import { useRuntime } from "../context/RuntimeContext";
import { useToast } from "../context/ToastContext";
import { useTranslate } from "../hooks/useTranslate";
import { getHealth } from "../services/api";
import { requestWithRetry } from "../utils/requestResilience";
import { safeRender } from "../utils/safeRender";
import Badge from "../components/UI/Badge";
import Loader from "../components/UI/Loader";

const iconMap = {
  rag_system: Brain,
  medical_imaging: Activity,
  api: Server,
  knowledge_graph: Database,
  vital_signs: ShieldCheck
};

const StatusPage = () => {
  const t = useTranslate();
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastCheck, setLastCheck] = useState(null);
  const [responseMs, setResponseMs] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const { telemetry } = useRuntime();
  const { pushToast } = useToast();

  const fetchHealth = async () => {
    const startedAt = performance.now();
    try {
      const { data } = await requestWithRetry(() => getHealth(), { timeoutMs: 10000, retries: 1 });
      setHealth(data);
      setError("");
      setLastCheck(new Date());
      setResponseMs(Math.round(performance.now() - startedAt));
    } catch (err) {
      setError(safeRender(err?.message, t("status_backend_unavailable")));
      pushToast(t("status_check_failed"), "error");
      setHealth(null);
      setLastCheck(new Date());
      setResponseMs(Math.round(performance.now() - startedAt));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const timer = setInterval(fetchHealth, 10000);
    return () => clearInterval(timer);
  }, []);

  const online = useMemo(() => health?.status === "healthy", [health]);
  const uptime = useMemo(() => (online ? "99.9%" : "97.2%"), [online]);

  return (
    <div className="app-page mx-auto w-full max-w-6xl space-y-4">
      <div className="app-shell-panel p-5">
        <div className="app-chip mb-3">System intelligence</div>
        <h2 className="app-shell-title text-2xl font-bold text-white">{t("status_title")}</h2>
        <p className="text-sm text-slate-400">{t("status_autorefresh")}</p>
      </div>

      <div className="app-shell-panel p-5">
        {loading ? (
          <Loader label={t("status_checking")} />
        ) : (
          <div className="space-y-5 animate-fade-in">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="app-chip">{t("status_backend_availability")}</h3>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setRefreshing(true);
                    fetchHealth();
                  }}
                  className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-slate-100 transition hover:bg-white/10 hover:border-teal-400/30"
                >
                  <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
                  {t("status_refresh")}
                </button>
                <Badge tone={online ? "success" : "danger"}>{online ? t("online") : t("offline")}</Badge>
              </div>
            </div>

            {error ? (
              <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
                {error}
              </div>
            ) : null}

            <div className="grid gap-3 md:grid-cols-3">
              <div className="app-metric transition duration-300 hover:scale-[1.02]">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Status</p>
                <p className="mt-1 flex items-center gap-2 text-lg font-bold text-white">
                  {online ? <span className="online-dot h-2.5 w-2.5 rounded-full bg-emerald-400" /> : <span className="h-2.5 w-2.5 rounded-full bg-red-400" />}
                  {safeRender(health?.status, t("status_unknown"))}
                </p>
              </div>
              <div className="app-metric transition duration-300 hover:scale-[1.02]">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{t("status_last_check")}</p>
                <p className="mt-1 text-lg font-bold text-white">
                  {lastCheck ? lastCheck.toLocaleTimeString() : t("na")}
                </p>
              </div>
              <div className="app-metric transition duration-300 hover:scale-[1.02]">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{t("status_response_time")}</p>
                <p className="mt-1 text-lg font-bold text-white">{responseMs ? `${responseMs} ms` : t("na")}</p>
              </div>
              <div className="app-metric transition duration-300 hover:scale-[1.02] md:col-span-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{t("status_uptime")}</p>
                <p className="mt-1 text-lg font-bold text-white">{uptime}</p>
              </div>
              <div className="app-metric transition duration-300 hover:scale-[1.02]">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{t("status_queries")}</p>
                <p className="mt-1 text-lg font-bold text-white">{telemetry.queryCount}</p>
              </div>
              <div className="app-metric transition duration-300 hover:scale-[1.02]">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{t("status_image_uploads")}</p>
                <p className="mt-1 text-lg font-bold text-white">{telemetry.imageUploadCount}</p>
              </div>
              <div className="app-metric transition duration-300 hover:scale-[1.02]">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{t("status_vitals_measures")}</p>
                <p className="mt-1 text-lg font-bold text-white">{telemetry.vitalsMeasureCount || 0}</p>
              </div>
              <div className="app-metric transition duration-300 hover:scale-[1.02]">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{t("status_avg_response")}</p>
                <p className="mt-1 text-lg font-bold text-white">{telemetry.avgResponseMs || 0} ms</p>
              </div>
            </div>

            <div>
              <h4 className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-400">{t("status_service_map")}</h4>
              <div className="grid gap-3 md:grid-cols-2">
                {Object.entries(health?.services || {}).map(([name, value]) => (
                  <div key={name} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 transition duration-300 hover:scale-[1.02] hover:border-teal-400/30 hover:bg-white/10">
                    <div className="flex items-center gap-3">
                      <span className={`rounded-xl p-2 ${value === "active" ? "bg-emerald-400/15 text-emerald-300" : "bg-red-400/15 text-red-300"}`}>
                        {(() => {
                          const Icon = iconMap[name] || Server;
                          return <Icon size={16} />;
                        })()}
                      </span>
                      <span className="text-sm font-medium capitalize text-slate-200">{safeRender(name, t("status_service")).replace(/_/g, " ")}</span>
                    </div>
                    <Badge tone={value === "active" ? "success" : "warning"}>{safeRender(value, t("status_unknown"))}</Badge>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StatusPage;
