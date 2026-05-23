import { useMemo, useState } from "react";
import { ChevronDown, ChevronUp, Link2 } from "lucide-react";
import Badge from "../UI/Badge";
import { safeRender, safeNumber } from "../../utils/safeRender";

const escapeRegExp = (value) => String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const normalizeTerms = (terms = []) =>
  Array.from(
    new Set(
      terms
        .flatMap((term) => String(term || "").split(/\s+/))
        .map((term) => term.trim())
        .filter((term) => term.length > 2)
    )
  );

const extractSnippet = (source) => {
  const candidates = [source?.snippet, source?.excerpt, source?.summary, source?.text];
  for (const candidate of candidates) {
    const text = String(candidate || "").trim();
    if (text) return text;
  }

  const content = source?.content;
  if (typeof content === "string" && content.trim()) return content.trim();
  if (content && typeof content === "object") {
    if (Array.isArray(content.data)) {
      return content.data.slice(0, 3).map((item) => String(item)).join(" ");
    }
    if (content.data && typeof content.data === "object") {
      return Object.entries(content.data)
        .slice(0, 3)
        .map(([key, value]) => `${key}: ${safeRender(value, "")}`)
        .join(" ");
    }
    return safeRender(content.focus || content.description || content, "");
  }

  return "No source excerpt provided by backend.";
};

const extractMatchedTerms = (source, searchTerms = []) => {
  const haystack = `${safeRender(source?.title, "")} ${extractSnippet(source)} ${safeRender(source?.category, "")}`.toLowerCase();
  return normalizeTerms(searchTerms).filter((term) => haystack.includes(String(term).toLowerCase()));
};

const highlightText = (text, terms = []) => {
  const normalizedTerms = normalizeTerms(terms).filter(Boolean);
  if (!normalizedTerms.length) return text;

  const pattern = new RegExp(`(${normalizedTerms.map(escapeRegExp).join("|")})`, "gi");
  const parts = String(text).split(pattern);
  return parts.map((part, idx) => {
    if (!normalizedTerms.some((term) => term.toLowerCase() === String(part).toLowerCase())) {
      return <span key={`plain-${idx}`}>{part}</span>;
    }

    return (
      <mark
        key={`mark-${idx}`}
        className="rounded bg-amber-200 px-1 py-0.5 text-amber-950 dark:bg-amber-300/30 dark:text-amber-100"
      >
        {part}
      </mark>
    );
  });
};

const SourceCard = ({ source, index, delay = 0, searchTerms = [] }) => {
  const [expanded, setExpanded] = useState(false);
  const title = safeRender(source?.title, `Source ${index + 1}`);
  const snippet = extractSnippet(source);
  const score = safeNumber(source?.score ?? source?.relevance_score ?? 0, 0);
  const relevance = (score * 100).toFixed(1);
  const href = source?.url || source?.link || source?.source_url || "";
  const matchedTerms = useMemo(() => extractMatchedTerms(source, searchTerms), [source, searchTerms]);

  const openSource = () => {
    if (!href) return;
    window.open(href, "_blank", "noopener,noreferrer");
  };

  return (
    <article
      style={{ animationDelay: `${delay}ms` }}
      className={`block rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition duration-300 hover:scale-[1.01] hover:border-medical-300 hover:shadow-md dark:border-slate-700 dark:bg-slate-800 dark:hover:border-medical-500 animate-slide-up ${href ? "cursor-pointer" : ""}`}
      onClick={openSource}
      onKeyDown={(event) => {
        if (!href) return;
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openSource();
        }
      }}
      role={href ? "button" : undefined}
      tabIndex={href ? 0 : undefined}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="min-w-0 space-y-1">
          <div className="flex items-center gap-2">
            <h4 className="line-clamp-1 text-sm font-semibold text-slate-900 dark:text-slate-100">{title}</h4>
            {href ? (
              <a href={href} target="_blank" rel="noreferrer" className="shrink-0 text-medical-600 transition hover:text-medical-700 dark:text-medical-300 dark:hover:text-medical-200" aria-label={`Open source ${title} in a new tab`}>
                <Link2 size={14} />
              </a>
            ) : null}
          </div>
          {source?.category ? <p className="line-clamp-1 text-xs text-slate-500 dark:text-slate-400">{safeRender(source.category, "")}</p> : null}
        </div>
        <Badge tone="info">Relevance: {relevance}%</Badge>
      </div>

      <div className="mb-3 text-xs text-slate-600 dark:text-slate-300">
        {highlightText(expanded ? snippet : snippet.slice(0, 220), matchedTerms)}
        {!expanded && snippet.length > 220 ? <span className="text-slate-400">…</span> : null}
      </div>

      {href ? <p className="mb-3 text-[11px] font-semibold text-medical-700 dark:text-medical-300">Open source</p> : null}

      {matchedTerms.length ? (
        <div className="mb-3 flex flex-wrap gap-1.5">
          {matchedTerms.slice(0, 4).map((term) => (
            <span key={term} className="rounded-full bg-medical-50 px-2 py-1 text-[11px] font-semibold text-medical-700 dark:bg-medical-900/40 dark:text-medical-200">
              {term}
            </span>
          ))}
        </div>
      ) : null}

      {snippet.length > 220 || source?.content ? (
        <button
          type="button"
          onClick={(event) => {
            event.preventDefault();
            event.stopPropagation();
            setExpanded((prev) => !prev);
          }}
          className="inline-flex items-center gap-1 rounded-full border border-slate-200 px-3 py-1 text-[11px] font-semibold text-slate-600 transition hover:border-medical-300 hover:text-medical-700 dark:border-slate-700 dark:text-slate-300 dark:hover:border-medical-500 dark:hover:text-medical-200"
        >
          {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          {expanded ? "Collapse" : "Expand"}
        </button>
      ) : null}
    </article>
  );
};

export default SourceCard;
