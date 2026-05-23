import { useState } from "react";
import { Activity, HeartPulse, Timer, Waves } from "lucide-react";
import Button from "../components/UI/Button";
import { useRuntime } from "../context/RuntimeContext";
import { useToast } from "../context/ToastContext";
import { useTranslate } from "../hooks/useTranslate";
import { describeApiError, getApiTargets, measureHeartRate, measureVitalsDetailed } from "../services/api";
import { requestWithRetry } from "../utils/requestResilience";
import { safeRender } from "../utils/safeRender";

const clampDuration = (value) => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return 15;
  return Math.max(5, Math.min(120, Math.round(parsed)));
};

const VitalsPage = () => {
  const t = useTranslate();
  const [heartRate, setHeartRate] = useState(null);
  const [details, setDetails] = useState(null);
  const [duration, setDuration] = useState(15);
  const [loadingQuick, setLoadingQuick] = useState(false);
  const [loadingDetailed, setLoadingDetailed] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const { isOffline, setDebugInfo, recordVitalsMeasure } = useRuntime();
  const { pushToast } = useToast();

  const runQuickMeasure = async () => {
    if (loadingQuick || loadingDetailed) return;

    if (isOffline) {
      setError(t("vitals_offline_error"));
      pushToast(t("vitals_offline_toast"), "error");
      return;
    }

    setLoadingQuick(true);
    setError("");
    setSuccess("");

    const startedAt = performance.now();

    try {
      setDebugInfo((prev) => ({
        ...prev,
        lastPayload: { request: "heart-rate measurement", method: "GET" },
        apiTargets: getApiTargets()
      }));

      const response = await requestWithRetry(() => measureHeartRate(), {
        timeoutMs: 42000,
        retries: 0
      });

      const bpm = Number(response?.data?.heart_rate);
      if (!Number.isFinite(bpm) || bpm <= 0) {
        throw new Error(t("vitals_invalid_hr_response"));
      }

      setHeartRate(Math.round(bpm));
      recordVitalsMeasure(Math.round(performance.now() - startedAt));
      setSuccess(t("vitals_quick_success"));
      pushToast(t("vitals_quick_toast"), "success");
      setDebugInfo((prev) => ({
        ...prev,
        lastResponse: response?.data || null,
        confidence: "N/A",
        detectedLanguage: "N/A"
      }));
    } catch (err) {
      const apiError = describeApiError(err);
      const message = safeRender(apiError.userMessage, t("vitals_quick_failed"));
      setError(`${message} (target: ${safeRender(apiError?.meta?.requestUrl, "unknown")})`);
      pushToast(apiError.toastMessage, "error");
      setDebugInfo((prev) => ({
        ...prev,
        lastResponse: { error: message, api: apiError.meta }
      }));
    } finally {
      setLoadingQuick(false);
    }
  };

  const runDetailedMeasure = async () => {
    if (loadingQuick || loadingDetailed) return;

    if (isOffline) {
      setError(t("vitals_offline_error"));
      pushToast(t("vitals_offline_toast"), "error");
      return;
    }

    const sanitizedDuration = clampDuration(duration);
    setDuration(sanitizedDuration);
    setLoadingDetailed(true);
    setError("");
    setSuccess("");

    const startedAt = performance.now();

    try {
      const payload = { duration: sanitizedDuration, display: false };
      setDebugInfo((prev) => ({
        ...prev,
        lastPayload: payload,
        apiTargets: getApiTargets()
      }));

      const response = await requestWithRetry(() => measureVitalsDetailed(payload), {
        timeoutMs: Math.max(12000, (sanitizedDuration + 8) * 1000),
        retries: 0
      });

      const data = response?.data || null;
      if (!data || !Number.isFinite(Number(data.heart_rate))) {
        throw new Error(t("vitals_invalid_detailed_response"));
      }

      setDetails(data);
      setHeartRate(Math.round(Number(data.heart_rate)));
      recordVitalsMeasure(Math.round(performance.now() - startedAt));
      setSuccess(t("vitals_detailed_success"));
      pushToast(t("vitals_detailed_toast"), "success");
      setDebugInfo((prev) => ({
        ...prev,
        lastResponse: data,
        confidence: Number.isFinite(Number(data?.confidence)) ? Number(data.confidence).toFixed(2) : "N/A",
        detectedLanguage: "N/A"
      }));
    } catch (err) {
      const apiError = describeApiError(err);
      const message = safeRender(apiError.userMessage, t("vitals_detailed_failed"));
      setError(`${message} (target: ${safeRender(apiError?.meta?.requestUrl, "unknown")})`);
      pushToast(apiError.toastMessage, "error");
      setDebugInfo((prev) => ({
        ...prev,
        lastResponse: { error: message, api: apiError.meta }
      }));
    } finally {
      setLoadingDetailed(false);
    }
  };

  return (
    <div className="app-page mx-auto w-full max-w-6xl space-y-4">
      <div className="app-shell-panel overflow-hidden p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-3">
            <div className="app-chip">{t("vitals_chip")}</div>
            <h2 className="app-shell-title text-2xl font-bold text-white">{t("vitals_title")}</h2>
            <p className="max-w-3xl text-sm leading-6 text-slate-300">
              {t("vitals_description")}
            </p>
          </div>
          <div className="grid gap-3 rounded-2xl border border-white/10 bg-white/5 p-4 text-xs text-slate-300 sm:grid-cols-3 lg:min-w-[420px]">
            <div>
              <p className="font-semibold text-white">{t("vitals_secure_capture")}</p>
              <p className="mt-1">{t("vitals_secure_capture_desc")}</p>
            </div>
            <div>
              <p className="font-semibold text-white">{t("vitals_quick_path")}</p>
              <p className="mt-1">{t("vitals_quick_path_desc")}</p>
            </div>
            <div>
              <p className="font-semibold text-white">{t("vitals_detailed_path")}</p>
              <p className="mt-1">{t("vitals_detailed_path_desc")}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <section className="space-y-4 lg:col-span-2">
          <div className="app-shell-panel p-5">
            <h3 className="app-chip">{t("vitals_quick_title")}</h3>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              {t("vitals_quick_desc")}
            </p>
            <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
              <p className="font-semibold text-white">{t("vitals_expect_title")}</p>
              <p className="mt-1">{t("vitals_expect_desc")}</p>
            </div>
            <div className="mt-4">
              <Button onClick={runQuickMeasure} loading={loadingQuick} disabled={loadingDetailed}>
                <HeartPulse size={16} />
                {t("vitals_start_quick")}
              </Button>
            </div>
          </div>

          <div className="app-shell-panel p-5">
            <h3 className="app-chip">{t("vitals_detailed_title")}</h3>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              {t("vitals_detailed_desc")}
            </p>
            <div className="mt-4 rounded-2xl border border-teal-400/20 bg-teal-500/10 p-4 text-sm text-teal-50">
              <p className="font-semibold text-white">{t("vitals_duration_reason_title")}</p>
              <p className="mt-1 text-teal-50/90">{t("vitals_duration_reason_desc")}</p>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-[160px_1fr] md:items-center">
              <label htmlFor="duration" className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                {t("vitals_duration")}
              </label>
              <input
                id="duration"
                type="number"
                min="5"
                max="120"
                step="1"
                value={duration}
                disabled={loadingQuick || loadingDetailed}
                onChange={(event) => setDuration(clampDuration(event.target.value))}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 outline-none ring-teal-300 focus:border-teal-400 focus:ring-2"
              />
            </div>
            <div className="mt-4">
              <Button variant="secondary" onClick={runDetailedMeasure} loading={loadingDetailed} disabled={loadingQuick}>
                <Waves size={16} />
                {t("vitals_start_detailed")}
              </Button>
            </div>
          </div>

          {error ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
              {error}
            </div>
          ) : null}

          {success ? (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm font-medium text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300">
              {success}
            </div>
          ) : null}
        </section>

        <aside className="space-y-4">
          <div className="app-shell-panel p-5">
            <div className="mb-3 flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-slate-300">
              <Activity size={16} />
              {t("vitals_latest_result")}
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{t("vitals_heart_rate")}</p>
              <p className="mt-2 text-3xl font-bold text-white">
                {heartRate ? `${heartRate} BPM` : "--"}
              </p>
              <p className="mt-2 text-xs leading-5 text-slate-400">{heartRate ? t("vitals_recent_estimate") : t("vitals_summary_empty")}</p>
            </div>

            {details ? (
              <div className="mt-3 space-y-2 text-sm text-slate-700 dark:text-slate-200">
                <div className="rounded-xl border border-slate-200 px-3 py-2 dark:border-slate-700">
                  {t("vitals_respiratory")}: {Number.isFinite(Number(details.respiratory_rate)) ? `${Math.round(Number(details.respiratory_rate))} /min` : t("na")}
                </div>
                <div className="rounded-xl border border-slate-200 px-3 py-2 dark:border-slate-700">
                  {t("vitals_spo2")}: {Number.isFinite(Number(details.oxygen_saturation)) ? `${Number(details.oxygen_saturation).toFixed(1)}%` : t("na")}
                </div>
                <div className="rounded-xl border border-slate-200 px-3 py-2 dark:border-slate-700">
                  {t("vitals_bp")}: {details?.blood_pressure?.systolic && details?.blood_pressure?.diastolic
                    ? `${Math.round(Number(details.blood_pressure.systolic))}/${Math.round(Number(details.blood_pressure.diastolic))}`
                    : t("na")}
                </div>
                <div className="rounded-xl border border-slate-200 px-3 py-2 dark:border-slate-700">
                  {t("confidence")}: {Number.isFinite(Number(details.confidence)) ? Number(details.confidence).toFixed(2) : t("na")}
                </div>
              </div>
            ) : null}
          </div>

          <div className="rounded-3xl border border-amber-400/20 bg-amber-500/10 p-4 text-sm text-amber-100">
            <div className="mb-2 flex items-center gap-2 font-semibold">
              <Timer size={15} />
              {t("vitals_tips")}
            </div>
            <ul className="space-y-1">
              <li>{t("vitals_tip_1")}</li>
              <li>{t("vitals_tip_2")}</li>
              <li>{t("vitals_tip_3")}</li>
            </ul>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default VitalsPage;
