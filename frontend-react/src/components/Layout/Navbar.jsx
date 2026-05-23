import { Menu, Moon, Stethoscope, Sun, UserCircle2, ChevronDown } from "lucide-react";
import { useLanguageStore } from "../../store/languageStore";
import { useTranslate } from "../../hooks/useTranslate";
import { Link } from "react-router-dom";
import { useState, useRef, useEffect } from "react";

const Navbar = ({ onMenuClick, darkMode, onToggleDarkMode, demoMode, onToggleDemoMode }) => {
  const { language, setLanguage } = useLanguageStore();
  const t = useTranslate();

  return (
    <header className="sticky top-0 z-40 border-b border-white/8 bg-slate-950/70 shadow-[0_10px_40px_rgba(0,0,0,0.35)] backdrop-blur-2xl transition-all">
      <div className="flex h-16 items-center justify-between gap-3 px-4 md:px-6">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onMenuClick}
            className="rounded-xl border border-white/10 bg-white/5 p-2 text-slate-100 shadow-sm transition-all hover:scale-105 hover:bg-white/10 hover:shadow-glow md:hidden"
            aria-label="Toggle sidebar"
          >
            <Menu size={18} />
          </button>
          <div className="rounded-xl bg-gradient-to-br from-teal-400 via-cyan-400 to-medical-600 p-2.5 text-slate-950 shadow-glow transition-all hover:scale-110 hover:shadow-glow-strong">
            <Stethoscope size={20} />
          </div>
          <div>
            <h1 className="app-shell-title bg-gradient-to-r from-white via-slate-100 to-teal-200 bg-clip-text text-base font-extrabold text-transparent md:text-lg">{t("app_title")}</h1>
            <p className="text-xs font-medium text-slate-400">{t("navbar_subtitle")}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onToggleDemoMode}
            className={`app-chip transition-all hover:scale-105 hover:border-teal-400/40 hover:text-white ${demoMode ? "border-teal-400/30 bg-teal-400/10 text-teal-100" : "bg-white/5 text-slate-300"}`}
          >
            {t("demo_mode")}: {demoMode ? t("on") : t("off")}
          </button>
          <button
            type="button"
            onClick={onToggleDarkMode}
            className="rounded-xl border border-white/10 bg-white/5 p-2 text-slate-100 shadow-sm transition-all hover:scale-105 hover:bg-white/10 hover:shadow-glow"
            aria-label="Toggle dark mode"
          >
            {darkMode ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          <div className="relative hidden md:flex">
            <LanguageDropdown language={language} setLanguage={setLanguage} t={t} />
          </div>
          <Link to="/dashboard" className="rounded-xl border border-white/10 bg-white/5 p-1.5 text-slate-100 shadow-sm transition-all hover:scale-105 hover:shadow-glow">
            <UserCircle2 size={20} />
          </Link>
        </div>
      </div>
    </header>
  );
};

const LanguageDropdown = ({ language, setLanguage, t }) => {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const onClick = (e) => {
      if (!ref.current) return;
      if (!ref.current.contains(e.target)) setOpen(false);
    };
    window.addEventListener("click", onClick);
    return () => window.removeEventListener("click", onClick);
  }, []);

  const options = [
    { key: "en", label: "English" },
    { key: "fr", label: "Français" },
    { key: "ar", label: "العربية" }
  ];

  const current = options.find((o) => o.key === language) || options[0];

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-1 text-sm font-semibold text-slate-100 shadow-sm transition-all hover:scale-105 hover:border-teal-400/30"
        aria-label={t("language_selector")}
      >
        <span className="text-sm">{current.label}</span>
        <ChevronDown size={14} />
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-40 rounded-xl border border-white/10 bg-slate-900/90 shadow-lg">
          {options.map((opt) => (
            <button
              key={opt.key}
              onClick={() => { setLanguage(opt.key); setOpen(false); }}
              className={`w-full text-left px-3 py-2 text-sm transition-colors hover:bg-white/5 ${opt.key === language ? "bg-white/5 font-bold" : ""}`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default Navbar;
