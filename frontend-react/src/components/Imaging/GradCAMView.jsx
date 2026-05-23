import { useTranslate } from "../../hooks/useTranslate";

const GradCAMView = ({ src, title }) => {
  const t = useTranslate();
  const resolvedTitle = title || t("imaging_gradcam_explainability");

  if (!src) return null;

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-card animate-slide-up transition duration-300 hover:scale-[1.02] dark:border-slate-700 dark:bg-slate-900/70">
      <h3 className="mb-4 text-sm font-bold uppercase tracking-wide text-slate-700 dark:text-slate-300">{resolvedTitle}</h3>
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800">
        <img src={src} alt={t("imaging_gradcam_heatmap")} className="h-full w-full object-contain transition duration-500 hover:scale-[1.03]" />
      </div>
    </section>
  );
};

export default GradCAMView;
