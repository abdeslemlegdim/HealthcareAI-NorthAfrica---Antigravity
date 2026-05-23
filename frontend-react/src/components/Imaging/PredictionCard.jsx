import ProgressBar from "../UI/ProgressBar";
import { useTranslate } from "../../hooks/useTranslate";

const PredictionCard = ({ label, confidence, probabilities, findings = [], modelLoaded = false, modelSource = "" }) => {
  const t = useTranslate();
  const severity = confidence >= 0.8 ? "high" : confidence >= 0.55 ? "medium" : "low";
  const severityLabel =
    severity === "high"
      ? t("imaging_severity_high")
      : severity === "medium"
        ? t("imaging_severity_medium")
        : t("imaging_severity_low");
  const severityClass =
    severity === "high"
      ? "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300"
      : severity === "medium"
        ? "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300"
        : "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300";

  return (
    <section className="relative space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-card animate-slide-up transition duration-300 hover:scale-[1.02] dark:border-slate-700 dark:bg-slate-900/70">
      {/* Model badge */}
      <div className="absolute right-4 top-4">
        {modelLoaded ? (
          <span className="inline-flex items-center gap-2 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
            <svg className="h-3 w-3 text-emerald-600" fill="currentColor" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" /></svg>
            Model: {modelSource}
          </span>
        ) : (
          <span className="inline-flex items-center gap-2 rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
            <svg className="h-3 w-3 text-amber-600" fill="currentColor" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" /></svg>
            Mock model
          </span>
        )}
      </div>
      <div className="rounded-2xl bg-gradient-to-r from-medical-50 to-tealmed-50 p-4 dark:from-slate-800 dark:to-slate-800">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-300">{t("imaging_top_prediction")}</p>
        <div className="mt-1 flex flex-wrap items-center gap-2">
          <h3 className="text-3xl font-extrabold text-medical-700 dark:text-tealmed-300">{label}</h3>
          <span className={`rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wide ${severityClass}`}>
            {severityLabel} {t("imaging_severity")}
          </span>
        </div>
      </div>

      <ProgressBar value={confidence * 100} label={t("confidence")} color="medical" />

      <div className="space-y-3">
        <h4 className="text-sm font-bold uppercase tracking-wide text-slate-700 dark:text-slate-300">{t("imaging_class_probabilities")}</h4>
        <div className="space-y-2">
          {probabilities.map((item) => (
            <ProgressBar
              key={item.label}
              value={item.score * 100}
              label={item.label}
              color="success"
            />
          ))}
        </div>
      </div>

      {findings.length ? (
        <div className="space-y-3 border-t border-slate-200 pt-4 dark:border-slate-700">
          <h4 className="text-sm font-bold uppercase tracking-wide text-slate-700 dark:text-slate-300">Detected findings</h4>
          <div className="grid gap-2 sm:grid-cols-2">
            {findings.map((finding) => (
              <div
                key={finding.label}
                className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800"
              >
                <div className="font-semibold text-slate-900 dark:text-white">{finding.label}</div>
                <div className="text-xs text-slate-500 dark:text-slate-400">Confidence: {(finding.score * 100).toFixed(1)}%</div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
};

export default PredictionCard;
