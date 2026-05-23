import { ImagePlus } from "lucide-react";
import { useTranslate } from "../../hooks/useTranslate";

const UploadBox = ({ onChange, disabled, dragActive, onDragOver, onDragLeave, onDrop }) => {
  const t = useTranslate();

  return (
    <label
      htmlFor="xray-upload"
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      className={`flex min-h-56 cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed p-6 text-center transition-all ${
        dragActive
          ? "border-medical-500 bg-medical-100/80 shadow-glow"
          : "border-medical-300 bg-white hover:border-medical-400 hover:bg-medical-50"
      } dark:border-slate-700 dark:bg-slate-800 dark:hover:border-medical-500 dark:hover:bg-slate-700`}
    >
      <input
        id="xray-upload"
        type="file"
        accept="image/*"
        onChange={onChange}
        disabled={disabled}
        className="hidden"
      />
      <div className="mb-3 rounded-2xl bg-gradient-to-br from-medical-600 to-tealmed-600 p-3 text-white shadow-md">
        <ImagePlus size={28} />
      </div>
      <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{t("imaging_upload_prompt")}</p>
      <p className="mt-1 text-xs text-slate-500 dark:text-slate-300">{t("imaging_upload_hint")}</p>
    </label>
  );
};

export default UploadBox;
