import { Link, useLocation } from "react-router-dom";
import { Home, MessageSquareText, ActivitySquare, ShieldCheck, HeartPulse } from "lucide-react";
import { useTranslate } from "../../hooks/useTranslate";

const items = [
  { to: "/", labelKey: "sidebar_overview", icon: Home },
  { to: "/chat", labelKey: "sidebar_chat", icon: MessageSquareText },
  { to: "/imaging", labelKey: "sidebar_imaging", icon: ActivitySquare },
  { to: "/vitals", labelKey: "sidebar_vitals", icon: HeartPulse },
  { to: "/status", labelKey: "sidebar_status", icon: ShieldCheck }
];

const Sidebar = ({ open, onClose }) => {
  const location = useLocation();
  const t = useTranslate();

  return (
    <>
      <div
        className={`fixed inset-0 z-20 bg-slate-950/70 backdrop-blur-md transition-opacity duration-300 md:hidden ${open ? "opacity-100" : "pointer-events-none opacity-0"}`}
        onClick={onClose}
      />
      <aside
        className={`fixed inset-y-16 left-0 z-30 w-72 transform border-r border-white/8 bg-slate-950/72 p-5 shadow-[0_24px_80px_rgba(0,0,0,0.42)] backdrop-blur-2xl transition-transform duration-300 md:sticky md:top-16 md:h-[calc(100vh-4rem)] md:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}
      >
        <nav className="space-y-2">
          {items.map(({ to, labelKey, icon: Icon }) => {
            const active = location.pathname === to;

            return (
              <Link
                key={to}
                to={to}
                onClick={onClose}
                className={`group flex items-center gap-3 rounded-2xl px-4 py-3.5 text-sm font-bold transition-all ${
                  active
                    ? "bg-gradient-to-r from-teal-400 via-cyan-500 to-medical-600 text-slate-950 shadow-glow"
                    : "text-slate-300 hover:-translate-x-0.5 hover:bg-white/5 hover:text-white hover:shadow-sm"
                }`}
              >
                <span className={`rounded-xl p-2 transition-all ${active ? "bg-white/25 shadow-sm" : "bg-white/5 group-hover:scale-110 group-hover:bg-white/10"}`}>
                  <Icon size={18} strokeWidth={2.5} />
                </span>
                <span>{t(labelKey)}</span>
              </Link>
            );
          })}
        </nav>
      </aside>
    </>
  );
};

export default Sidebar;
