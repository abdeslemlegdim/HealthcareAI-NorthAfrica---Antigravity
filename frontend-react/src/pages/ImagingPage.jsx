import { useEffect, useMemo, useState } from "react";
import UploadBox from "../components/Imaging/UploadBox";
import PredictionCard from "../components/Imaging/PredictionCard";
import GradCAMView from "../components/Imaging/GradCAMView";
import Button from "../components/UI/Button";
import Loader from "../components/UI/Loader";
import { useRuntime } from "../context/RuntimeContext";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { classifyImage, describeApiError, explainImage, getApiTargets } from "../services/api";
import { requestWithRetry } from "../utils/requestResilience";
import { safeNumber, safeRender } from "../utils/safeRender";
import { useTranslate } from "../hooks/useTranslate";

const normalizeLabel = (value, fallback = "Unknown") =>
  String(value ?? fallback).replace(/_/g, " ").trim() || fallback;

const normalizeProbabilities = (raw) => {
  if (!raw) return [];

  if (Array.isArray(raw)) {
    return raw
      .map((item) => ({
        label: normalizeLabel(item?.label || item?.class || item?.name || item?.disease),
        score: Number(item?.score ?? item?.probability ?? item?.confidence ?? 0)
      }))
      .sort((a, b) => b.score - a.score);
  }

  return Object.entries(raw)
    .map(([label, score]) => ({
      label: normalizeLabel(label),
      score: Number(score ?? 0)
    }))
    .sort((a, b) => b.score - a.score);
};

const ImagingPage = () => {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [result, setResult] = useState(null);
  const [heatmapUrl, setHeatmapUrl] = useState("");
  const [rawHeatmapUrl, setRawHeatmapUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [requestState, setRequestState] = useState("idle");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [explainWarning, setExplainWarning] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [comparePosition, setComparePosition] = useState(50);
  const [analyzingProgress, setAnalyzingProgress] = useState(10);
  
  const { pushToast } = useToast();
  const { isOffline, recordImageUpload, setDebugInfo } = useRuntime();
  const { user } = useAuth();
  const t = useTranslate();

  const localizedRequestState =
    requestState === "loading"
      ? t("state_loading")
      : requestState === "success"
        ? t("state_success")
        : requestState === "error"
          ? t("state_error")
          : t("state_idle");

  const probabilities = useMemo(
    () => normalizeProbabilities(result?.probabilities || result?.scores || result?.class_probabilities),
    [result]
  );

  const findings = useMemo(
    () => normalizeProbabilities(result?.findings || result?.predicted_findings),
    [result]
  );

  const primaryPrediction = useMemo(
    () => normalizeLabel(
      result?.primary_prediction?.disease ||
        result?.primary_prediction?.label ||
        result?.predicted_disease ||
        result?.disease ||
        result?.primary_prediction,
      ""
    ),
    [result]
  );

  const needsReview = Boolean(result?.is_uncertain || result?.requires_review);
  const modelSource = normalizeLabel(result?.model_metadata?.model_source || result?.model_source || t("status_unknown"));
  const confidenceThreshold = safeNumber(result?.model_metadata?.confidence_threshold ?? result?.confidence_threshold, 0);

  const prediction = useMemo(() => {
    if (!result) return "";
    return normalizeLabel(
      safeRender(
        result.prediction ||
          result.predicted_class ||
          result.class_name ||
          result.label ||
          result.predicted_disease ||
          result.disease ||
          probabilities[0]?.label,
        t("status_unknown")
      )
    ).toUpperCase();
  }, [result, probabilities]);

  const confidence = useMemo(() => {
    const base = safeNumber(result?.confidence ?? result?.score ?? probabilities[0]?.score ?? 0, 0);
    return Math.max(0, Math.min(1, Number.isFinite(base) ? base : 0));
  }, [result, probabilities]);

  const onFileChange = (event) => {
    const selected = event.target.files?.[0];
    if (!selected) return;

    setError("");
    setSuccess("");
    setExplainWarning("");
    setResult(null);
    setHeatmapUrl("");
    setRawHeatmapUrl("");
    setComparePosition(50);
    setAnalyzingProgress(10);
    setFile(selected);

    const url = URL.createObjectURL(selected);
    setPreviewUrl(url);
  };

  const onDragOver = (event) => {
    event.preventDefault();
    setDragActive(true);
  };

  const onDragLeave = (event) => {
    event.preventDefault();
    setDragActive(false);
  };

  const onDrop = (event) => {
    event.preventDefault();
    setDragActive(false);
    const selected = event.dataTransfer?.files?.[0];
    if (!selected) return;

    const syntheticEvent = { target: { files: [selected] } };
    onFileChange(syntheticEvent);
  };

  const analyzeImage = async () => {
    if (!file) return;
    if (loading) return;

    if (isOffline) {
      setError(t("imaging_offline_error"));
      setRequestState("error");
      pushToast(t("imaging_offline_toast"), "error");
      return;
    }

    setLoading(true);
    setRequestState("loading");
    setAnalyzingProgress(12);
    setError("");
    setSuccess("");
    setExplainWarning("");
    const startedAt = performance.now();

    try {
      const formData = new FormData();
      formData.append("file", file);
      setDebugInfo((prev) => ({
        ...prev,
        lastPayload: { endpoint: "/api/v1/imaging/classify", fileName: file?.name },
        apiTargets: getApiTargets()
      }));

      const classifyRes = await requestWithRetry(() => classifyImage(formData), { timeoutMs: 10000, retries: 1 });
      if (!classifyRes?.data || typeof classifyRes.data !== "object") {
        throw new Error(t("imaging_invalid_classify_response"));
      }
      setResult(classifyRes.data);

      const explainFormData = new FormData();
      explainFormData.append("file", file);

      try {
        const explainRes = await requestWithRetry(
          () => explainImage(explainFormData, { mode: "overlay" }),
          { timeoutMs: 10000, retries: 1 }
        );

        const blob = explainRes?.data instanceof Blob
          ? explainRes.data
          : new Blob([explainRes.data], {
              type: explainRes.headers["content-type"] || "image/png"
            });

        const url = URL.createObjectURL(blob);
        setHeatmapUrl(url);

        const rawExplainFormData = new FormData();
        rawExplainFormData.append("file", file);
        const rawExplainRes = await requestWithRetry(
          () => explainImage(rawExplainFormData, { mode: "raw" }),
          { timeoutMs: 10000, retries: 1 }
        );

        const rawBlob = rawExplainRes?.data instanceof Blob
          ? rawExplainRes.data
          : new Blob([rawExplainRes.data], {
              type: rawExplainRes.headers["content-type"] || "image/png"
            });
        setRawHeatmapUrl(URL.createObjectURL(rawBlob));
      } catch (explainError) {
        setHeatmapUrl("");
        setRawHeatmapUrl("");
        setExplainWarning(t("imaging_explainability_unavailable"));
      }

      setSuccess(t("imaging_analyze_success"));
      setRequestState("success");
      pushToast(t("imaging_analyze_toast"), "success");
      const elapsed = Math.round(performance.now() - startedAt);
      recordImageUpload(elapsed);
      setDebugInfo((prev) => ({
        ...prev,
        lastResponse: classifyRes.data,
        detectedLanguage: "N/A",
        confidence: safeNumber(classifyRes?.data?.confidence ?? classifyRes?.data?.score, 0)
      }));
    } catch (err) {
      const apiError = describeApiError(err);
      const message = safeRender(apiError.userMessage, t("imaging_analyze_failed"));
      setError(`${message} (target: ${safeRender(apiError?.meta?.requestUrl, t("status_unknown"))})`);
      setRequestState("error");
      pushToast(apiError.toastMessage, "error");
      setDebugInfo((prev) => ({
        ...prev,
        apiTargets: getApiTargets(),
        lastResponse: { error: message, api: apiError.meta }
      }));
    } finally {
      setLoading(false);
      setAnalyzingProgress(100);
    }
  };

  useEffect(() => {
    if (!loading) return;
    const timer = setInterval(() => {
      setAnalyzingProgress((prev) => {
        if (prev >= 90) return prev;
        return prev + 5;
      });
    }, 220);

    return () => clearInterval(timer);
  }, [loading]);

  return (
    <div className="app-page mx-auto w-full max-w-7xl space-y-4">
      <div className="app-shell-panel p-5">
        <div className="app-chip mb-3">Diagnostic vision</div>
        <h2 className="app-shell-title text-2xl font-bold text-white">{t("imaging_title")}</h2>
        <p className="text-sm text-slate-400">
          {t("imaging_description")}
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4">
          <div className="app-shell-panel p-5">
            <UploadBox
              onChange={onFileChange}
              disabled={loading}
              dragActive={dragActive}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              onDrop={onDrop}
            />
            {previewUrl ? (
              <div className="mt-4 overflow-hidden rounded-2xl border border-white/10 bg-white/5">
                <img src={previewUrl} alt="Uploaded preview" className="w-full object-contain transition duration-500 hover:scale-[1.02]" />
              </div>
            ) : null}
            <div className="mt-4">
              <Button onClick={analyzeImage} loading={loading} disabled={!file || loading} className="w-full">
                {t("imaging_analyze_button")}
              </Button>
            </div>
            {/* Model management removed: page now only supports image analysis */}
          </div>

          {loading ? (
            <div className="app-shell-panel p-8">
              <Loader label={t("imaging_analyzing_label")} />
              <div className="mt-5">
                <div className="mb-2 flex items-center justify-between text-xs font-semibold text-slate-300">
                  <span>{t("imaging_pipeline_progress")}</span>
                  <span>{analyzingProgress}%</span>
                </div>
                <div className="h-2.5 overflow-hidden rounded-full bg-white/10">
                  <div className="h-full rounded-full bg-gradient-to-r from-medical-600 to-tealmed-500 transition-all duration-300" style={{ width: `${analyzingProgress}%` }} />
                </div>
              </div>
            </div>
          ) : null}

          {error ? (
            <div className="rounded-2xl border border-red-400/20 bg-red-500/10 p-4 text-sm font-medium text-red-100">
              {error}
            </div>
          ) : null}

          {success ? (
            <div className="rounded-2xl border border-emerald-400/20 bg-emerald-500/10 p-4 text-sm font-medium text-emerald-100">
              {safeRender(success, t("state_success"))}
            </div>
          ) : null}

          {explainWarning ? (
            <div className="rounded-2xl border border-amber-400/20 bg-amber-500/10 p-4 text-sm font-medium text-amber-100">
              {safeRender(explainWarning, t("imaging_explainability_unavailable"))}
            </div>
          ) : null}
        </div>

        <div className="space-y-4 xl:col-span-2">
          {result ? (
            <div className="space-y-3">
              <PredictionCard
                label={prediction}
                confidence={confidence}
                probabilities={probabilities.length ? probabilities : [{ label: prediction, score: confidence }]}
                findings={findings.length ? findings : probabilities.slice(0, 5)}
                modelLoaded={Boolean(result?.model_metadata?.model_loaded ?? result?.model_loaded)}
                modelSource={modelSource}
              />
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-200 shadow-card">
                <div className="grid gap-2 sm:grid-cols-2">
                  <p>
                    <span className="font-semibold">{t("imaging_backend")}:</span> {safeRender(result?.inference_backend, t("status_unknown"))}
                  </p>
                  <p>
                    <span className="font-semibold">{t("imaging_file")}:</span> {safeRender(result?.filename, file?.name || t("na"))}
                  </p>
                  <p>
                    <span className="font-semibold">Model source:</span> {safeRender(modelSource, t("status_unknown"))}
                  </p>
                  <p>
                    <span className="font-semibold">Confidence threshold:</span> {confidenceThreshold ? `${Math.round(confidenceThreshold * 100)}%` : t("status_unknown")}
                  </p>
                </div>
              </div>

              {needsReview ? (
                <div className="rounded-2xl border border-amber-400/20 bg-amber-500/10 p-4 text-sm text-amber-100">
                  <div className="font-semibold uppercase tracking-wide">Preliminary result</div>
                  <p className="mt-1">
                    The model confidence is below the review threshold. Treat this as a screening signal, not a final diagnosis.
                    {primaryPrediction ? ` Most likely finding: ${primaryPrediction}.` : null}
                  </p>
                </div>
              ) : null}
            </div>
          ) : null}

          {previewUrl || heatmapUrl || rawHeatmapUrl ? (
            <div className="grid gap-4 lg:grid-cols-3">
              {previewUrl ? (
                <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-card animate-fade-in dark:border-slate-700 dark:bg-slate-900/70">
                  <h3 className="mb-4 text-sm font-bold uppercase tracking-wide text-slate-700 dark:text-slate-300">{t("imaging_original_xray")}</h3>
                  <div className="overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800">
                    <img src={previewUrl} alt={t("imaging_original_xray")} className="h-full w-full object-contain transition duration-500 hover:scale-[1.03]" />
                  </div>
                </section>
              ) : null}
              <GradCAMView src={heatmapUrl} title={t("imaging_gradcam_overlay")} />
              <GradCAMView src={rawHeatmapUrl} title={t("imaging_raw_heatmap")} />
            </div>
          ) : null}

          {previewUrl && heatmapUrl ? (
            <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-card animate-slide-up dark:border-slate-700 dark:bg-slate-900/70">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-bold uppercase tracking-wide text-slate-700 dark:text-slate-300">{t("imaging_compare_title")}</h3>
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">{t("imaging_drag_slider")}</span>
              </div>
              <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800">
                <img src={previewUrl} alt={t("imaging_original_xray")} className="h-full w-full object-contain" />
                <div className="absolute inset-0 overflow-hidden" style={{ width: `${comparePosition}%` }}>
                  <img src={heatmapUrl} alt={t("imaging_gradcam_overlay")} className="h-full w-full object-contain" />
                </div>
                <div className="pointer-events-none absolute inset-y-0" style={{ left: `calc(${comparePosition}% - 1px)` }}>
                  <div className="h-full w-0.5 bg-white/80 shadow" />
                </div>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={comparePosition}
                onChange={(event) => setComparePosition(Number(event.target.value))}
                className="mt-3 h-2 w-full cursor-pointer accent-medical-600"
              />
            </section>
          ) : null}
        </div>
      </div>

      <div className="sr-only" aria-live="polite">{t("request_state")}: {localizedRequestState}</div>
    </div>
  );
};

export default ImagingPage;
