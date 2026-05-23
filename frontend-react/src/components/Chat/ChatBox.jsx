import { useEffect, useMemo, useRef, useState } from "react";
import { Activity, Copy, Languages, RefreshCw, SendHorizonal, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { describeApiError, getApiTargets, getHealth, queryRAG } from "../../services/api";
import { useRuntime } from "../../context/RuntimeContext";
import { useToast } from "../../context/ToastContext";
import { useLanguageStore } from "../../store/languageStore";
import { useTranslate } from "../../hooks/useTranslate";
import { requestWithRetry } from "../../utils/requestResilience";
import { safeNumber, safeRender } from "../../utils/safeRender";
import { streamParagraphs } from "../../utils/streamingText";
import Badge from "../UI/Badge";
import Button from "../UI/Button";
import ProgressBar from "../UI/ProgressBar";
import MessageBubble from "./MessageBubble";
import SourceCard from "./SourceCard";

const CHAT_TIMEOUT_MS = 90000;

const medicalTerms = [
  "pneumonia",
  "tuberculosis",
  "covid-19",
  "dyspnea",
  "diagnosis",
  "symptoms",
  "treatment",
  "infection",
  "respiratory",
  "pneumonie",
  "symptomes",
  "traitement",
  "الالتهاب الرئوي",
  "الاعراض",
  "التشخيص"
];

const escapeRegExp = (value) => String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const normalizeLanguage = (value) => {
  const code = String(value || "unknown").toLowerCase();
  const map = { en: "English", ar: "Arabic", fr: "French" };
  return map[code] || code;
};

const hasStructuredResponse = (result = {}) =>
  Boolean(
    result &&
      (
        result.title ||
        result.summary ||
        (Array.isArray(result.symptoms) && result.symptoms.length > 0) ||
        (Array.isArray(result.causes) && result.causes.length > 0) ||
        (Array.isArray(result.treatment) && result.treatment.length > 0) ||
        result.warning ||
        result.disclaimer
      )
  );

const formatAnswer = (text) => {
  if (!text) return ["No answer was returned."];
  return String(text)
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean);
};

const normalizeKey = (value) =>
  String(value || "")
    .toLowerCase()
    .replace(/[*_`#:\-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

const dedupeList = (items = []) => {
  const seen = new Set();
  return items.filter((item) => {
    const key = normalizeKey(item);
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
};

const cleanMarkdownText = (value) =>
  String(value || "")
    .replace(/^#{1,6}\s*/g, "")
    .replace(/^\*\*(.+)\*\*$/g, "$1")
    .replace(/^\*(.+)\*$/g, "$1")
    .trim();

const toMarkdownMessage = ({ title, sections }) => {
  const lines = [`## ${safeRender(title, "Clinical Summary")}`];

  sections.forEach((section) => {
    lines.push("", `### ${safeRender(section.title, "Clinical Summary")}`);
    section.paragraphs.forEach((paragraph) => {
      lines.push(safeRender(paragraph, ""));
    });
    section.bullets.forEach((item) => {
      lines.push(`- ${safeRender(item, "")}`);
    });
  });

  lines.push(
    "",
    "---",
    "",
    "### Disclaimer",
    "This information is provided for educational purposes only and does not replace professional medical advice. Please consult a healthcare professional if needed."
  );

  return lines.join("\n");
};

const markdownComponents = {
  h2: ({ children }) => <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">{children}</h3>,
  h3: ({ children }) => <h4 className="pt-1 text-sm font-semibold text-slate-900 dark:text-slate-100">{children}</h4>,
  p: ({ children }) => <p className="leading-7 text-slate-800 dark:text-slate-100">{children}</p>,
  ul: ({ children }) => <ul className="list-disc space-y-1 pl-5 text-slate-800 dark:text-slate-100">{children}</ul>,
  li: ({ children }) => <li className="leading-7">{children}</li>,
  hr: () => <hr className="my-2 border-slate-200 dark:border-slate-700" />,
};

const inferTitle = ({ answer = "", question = "", sources = [] }) => {
  const firstLine = String(answer)
    .split(/\n+/)
    .map((line) => cleanMarkdownText(line))
    .find((line) => line && !line.startsWith("- ") && !line.endsWith(":"));

  if (firstLine && firstLine.length <= 60) {
    return firstLine;
  }

  const sourceTitle = safeRender(sources?.[0]?.title, "").trim();
  if (sourceTitle) return sourceTitle;

  const q = safeRender(question, "").trim();
  if (!q) return "Clinical Summary";

  const match = q.match(/(?:of|about|for)\s+([a-z\-\s]{3,40})\??$/i);
  const phrase = (match?.[1] || q).replace(/\?+$/, "").trim();
  return phrase
    .split(/\s+/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
};

const isHeaderLine = (line) => {
  const cleaned = cleanMarkdownText(line).replace(/:$/, "").trim();
  if (!cleaned || cleaned.length > 48) return false;
  return /(symptom|sign|cause|risk|treatment|management|diagnos|complication|prevention|overview|summary)/i.test(cleaned);
};

const buildStructuredAnswer = ({ answer = "", question = "", sources = [] }) => {
  const lines = String(answer)
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean);

  const title = inferTitle({ answer, question, sources });
  const sections = [];
  let current = null;

  const ensureSection = (name) => {
    if (!current || current.title !== name) {
      current = { title: name, bullets: [], paragraphs: [] };
      sections.push(current);
    }
  };

  for (const rawLine of lines) {
    const line = cleanMarkdownText(rawLine);
    if (!line) continue;

    if (isHeaderLine(line)) {
      const normalizedHeader = line.replace(/:$/, "").trim();
      ensureSection(normalizedHeader);
      continue;
    }

    if (/^[-*•]\s+/.test(rawLine)) {
      ensureSection(current?.title || "Clinical Summary");
      current.bullets.push(line.replace(/^[-*•]\s+/, "").trim());
      continue;
    }

    if (line.toLowerCase() === normalizeKey(title)) {
      continue;
    }

    ensureSection(current?.title || "Clinical Summary");
    current.paragraphs.push(line);
  }

  const normalizedSections = sections.map((section, idx) => {
    const lowered = section.title.toLowerCase();
    const isSymptomSection = /symptom|sign/.test(lowered);
    let resolvedTitle = section.title;
    if (isSymptomSection && idx === 0) resolvedTitle = "Common Symptoms";
    if (isSymptomSection && idx > 0) resolvedTitle = "Additional Symptoms";
    if (/clinical summary/i.test(resolvedTitle) && section.bullets.length > 0) {
      resolvedTitle = "Key Findings";
    }

    return {
      title: resolvedTitle,
      bullets: dedupeList(section.bullets),
      paragraphs: dedupeList(section.paragraphs),
    };
  });

  const filteredSections = normalizedSections.filter((section) => section.bullets.length > 0 || section.paragraphs.length > 0);
  if (!filteredSections.length) {
    return {
      title,
      sections: [{ title: "Clinical Summary", bullets: [], paragraphs: [safeRender(answer, "No answer was returned.")] }],
    };
  }

  return { title, sections: filteredSections };
};

const buildStructuredResponse = ({ result = {}, question = "", lastPrompt = "" }) => {
  if (!hasStructuredResponse(result)) {
    return null;
  }

  const labels = result.labels || {};
  const fallbackQuestion = question || lastPrompt;
  const title = safeRender(result.title, inferTitle({ answer: result.summary || result.answer || "", question: fallbackQuestion, sources: result.sources || [] }));
  const summary = result.warning ? safeRender(result.summary, "") : safeRender(result.summary || result.answer, "No answer was returned.");
  const symptoms = Array.isArray(result.symptoms) ? result.symptoms.map((item) => safeRender(item, "")).filter(Boolean) : [];
  const causes = Array.isArray(result.causes) ? result.causes.map((item) => safeRender(item, "")).filter(Boolean) : [];
  const treatment = Array.isArray(result.treatment) ? result.treatment.map((item) => safeRender(item, "")).filter(Boolean) : [];

  const sections = [];
  if (summary) {
    sections.push({ title: labels.clinical_summary || "Clinical Summary", paragraphs: [summary], bullets: [] });
  }
  if (symptoms.length) {
    sections.push({ title: labels.symptoms || "Symptoms", paragraphs: [], bullets: symptoms });
  }
  if (causes.length) {
    sections.push({ title: labels.causes || "Causes", paragraphs: [], bullets: causes });
  }
  if (treatment.length) {
    sections.push({ title: labels.treatment || "Treatment", paragraphs: [], bullets: treatment });
  }

  return {
    title,
    sections,
    warning: safeRender(result.warning, ""),
    disclaimer: safeRender(result.disclaimer, ""),
    sources: result.sources || [],
  };
};

const serializeStructuredResponse = (response = {}) => {
  const title = safeRender(response?.title, "").trim();
  const summary = safeRender(response?.summary || response?.answer, "").trim();
  const labels = response?.labels || {};

  if (!hasStructuredResponse(response)) {
    return summary || "";
  }

  const lines = [];
  if (title) lines.push(title);
  if (summary) lines.push(summary);

  const sections = [
    { title: labels.symptoms || "Symptoms", items: response?.symptoms || [] },
    { title: labels.causes || "Causes", items: response?.causes || [] },
    { title: labels.treatment || "Treatment", items: response?.treatment || [] },
  ];

  sections.forEach((section) => {
    const items = Array.isArray(section.items) ? section.items.filter(Boolean) : [];
    if (!items.length) return;
    lines.push(`${section.title}:`);
    items.forEach((item) => lines.push(`- ${safeRender(item, "")}`));
  });

  if (response?.warning) {
    lines.push(`${labels.warning || "Warning"}: ${safeRender(response.warning, "")}`);
  }

  if (response?.disclaimer) {
    lines.push(`${labels.disclaimer_label || "Disclaimer"}: ${safeRender(response.disclaimer, "")}`);
  }

  return lines.join("\n\n").trim();
};

const highlightTerms = (text) => {
  try {
    const safeTerms = medicalTerms.map(escapeRegExp);
    const pattern = new RegExp(`(${safeTerms.join("|")})`, "gi");
    const parts = String(text).split(pattern);
    return parts.map((part, idx) => {
      const match = medicalTerms.some((term) => term.toLowerCase() === String(part).toLowerCase());
      if (!match) return <span key={`text-${idx}`}>{part}</span>;
      return (
        <mark
          key={`highlight-${idx}`}
          className="bg-medical-100 text-medical-800 dark:bg-medical-900/40 dark:text-medical-300 font-medium px-0.5 rounded cursor-help transition-all hover:bg-medical-200 dark:hover:bg-medical-900/60"
          title="Medical terminology identified"
        >
          {part}
        </mark>
      );
    });
  } catch (err) {
    console.error("Failed to highlight terms:", err);
    return <span>{text}</span>;
  }
};

const ChatBox = () => {
  const { demoMode, isOffline, recordQuery, setDebugInfo } = useRuntime();
  const { pushToast } = useToast();
  const { language } = useLanguageStore();
  const t = useTranslate();

  const chatContainerRef = useRef(null);
  const streamingCancelRef = useRef(null);

  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [apiFailure, setApiFailure] = useState(null);
  const [requestState, setRequestState] = useState("idle");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingAnswer, setStreamingAnswer] = useState("");
  const [lastPrompt, setLastPrompt] = useState("");

  const demoQueries = useMemo(() => [
    { label: "en", value: t("demo_query_en") || "Pneumonia symptoms" },
    { label: "ar", value: t("demo_query_ar") || "الالتهاب الرئوي" },
    { label: "fr", value: t("demo_query_fr") || "Symptômes de la pneumonie" }
  ], [t]);

  const isDirectMode = useMemo(() => hasStructuredResponse(result), [result]);

  const citationSearchTerms = useMemo(() => {
    if (!lastPrompt) return [];
    return lastPrompt
      .toLowerCase()
      .replace(/[^\w\s\u0600-\u06FF]/g, " ")
      .split(/\s+/)
      .filter((w) => w.length > 3);
  }, [lastPrompt]);

  const structuredAnswer = useMemo(() => {
    if (!result) return null;
    if (isDirectMode) {
      return buildStructuredResponse({ result, question: result.question, lastPrompt });
    }
    return buildStructuredAnswer({
      answer: isStreaming ? streamingAnswer : result.answer || result.summary,
      question: result.question || lastPrompt,
      sources: result.sources || []
    });
  }, [result, isDirectMode, isStreaming, streamingAnswer, lastPrompt]);

  const renderedMarkdown = useMemo(() => {
    if (isStreaming) return streamingAnswer;
    return result?.answer || result?.summary || "";
  }, [isStreaming, streamingAnswer, result]);

  // Clean up streaming on unmount
  useEffect(() => {
    return () => {
      if (streamingCancelRef.current) {
        streamingCancelRef.current();
      }
    };
  }, []);

  // Scroll to bottom
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, streamingAnswer, loading]);

  const runQuery = async (text) => {
    if (!text || !text.trim()) return;
    const cleanText = text.trim();

    // Cancel any active streaming
    if (streamingCancelRef.current) {
      streamingCancelRef.current();
      streamingCancelRef.current = null;
    }

    setLoading(true);
    setError(null);
    setApiFailure(null);
    setRequestState("pending");
    setResult(null);
    setIsStreaming(false);
    setStreamingAnswer("");
    setLastPrompt(cleanText);

    // Add user message if not already added
    setMessages((prev) => {
      const alreadyHasUserMsg = prev.length > 0 && prev[prev.length - 1].role === "user" && prev[prev.length - 1].content === cleanText;
      if (alreadyHasUserMsg) return prev;
      return [
        ...prev,
        {
          id: `user-${Date.now()}`,
          role: "user",
          content: cleanText,
          timestamp: new Date().toLocaleTimeString()
        }
      ];
    });

    try {
      const response = await requestWithRetry(
        () => queryRAG({ query: cleanText, language }),
        { timeoutMs: CHAT_TIMEOUT_MS, retries: 1 }
      );

      const responseData = response?.data;
      if (!responseData) {
        throw new Error("No data returned from service.");
      }

      setResult(responseData);
      setRequestState("success");

      recordQuery?.({
        query: cleanText,
        success: true,
        latency: response?.latency || 0,
        confidence: responseData.confidence || 0,
      });

      setDebugInfo?.((prev) => ({
        ...prev,
        lastRequest: { query: cleanText, language, timestamp: new Date().toISOString() },
        lastResponse: { data: responseData, timestamp: new Date().toISOString() },
      }));

      const fullAnswer = responseData.answer || responseData.summary || "";
      if (fullAnswer) {
        setIsStreaming(true);
        const paragraphs = fullAnswer.split(/\n+/);
        const cancel = streamParagraphs(
          paragraphs,
          15,
          200,
          (progress) => {
            setStreamingAnswer(progress.join("\n\n"));
          },
          () => {
            setIsStreaming(false);
            setStreamingAnswer(fullAnswer);
            setMessages((prev) => [
              ...prev,
              {
                id: `ai-${Date.now()}`,
                role: "assistant",
                content: fullAnswer,
                timestamp: new Date().toLocaleTimeString()
              }
            ]);
            pushToast(t("answer_generated") || "Answer generated successfully.", "success");
          }
        );
        streamingCancelRef.current = cancel;
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: `ai-${Date.now()}`,
            role: "assistant",
            content: "No clinical answer could be generated.",
            timestamp: new Date().toLocaleTimeString()
          }
        ]);
      }
    } catch (err) {
      console.error(err);
      const apiError = describeApiError(err);
      setError(apiError.userMessage || "Failed to generate an answer.");
      setApiFailure(apiError);
      setRequestState("error");

      recordQuery?.({
        query: cleanText,
        success: false,
        error: apiError.userMessage || "Failed to generate an answer.",
      });

      setDebugInfo?.((prev) => ({
        ...prev,
        lastRequest: { query: cleanText, language, timestamp: new Date().toISOString() },
        lastResponse: { error: apiError, timestamp: new Date().toISOString() },
      }));

      pushToast(apiError.toastMessage || "Request failed", "error");
    } finally {
      setLoading(false);
    }
  };

  const sendCurrentQuery = () => {
    if (!query.trim() || loading) return;
    const text = query.trim();
    setQuery("");
    
    // Add user message immediately
    setMessages((prev) => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        role: "user",
        content: text,
        timestamp: new Date().toLocaleTimeString()
      }
    ]);

    runQuery(text);
  };

  const retryLastQuery = () => {
    if (lastPrompt) {
      runQuery(lastPrompt);
    }
  };

  const copyAnswer = async () => {
    if (!result) return;
    try {
      let textToCopy = "";
      if (isDirectMode) {
        textToCopy = serializeStructuredResponse(result);
      } else {
        const structured = buildStructuredAnswer({
          answer: result.answer || result.summary,
          question: result.question || lastPrompt,
          sources: result.sources || []
        });
        textToCopy = toMarkdownMessage(structured);
      }

      await navigator.clipboard.writeText(textToCopy);
      pushToast(t("answer_copied") || "Answer copied to clipboard", "success");
    } catch (err) {
      console.error("Failed to copy:", err);
      pushToast(t("copy_failed") || "Failed to copy answer", "error");
    }
  };

  const runHealthCheck = async () => {
    try {
      const response = await requestWithRetry(() => getHealth(), { timeoutMs: 5000, retries: 0 });
      const apiTargets = getApiTargets();
      setDebugInfo((prev) => ({
        ...prev,
        apiTargets,
        lastResponse: {
          ...prev?.lastResponse,
          healthCheck: {
            ok: true,
            status: response?.status ?? 200,
            payload: response?.data ?? null,
            checkedAt: new Date().toISOString()
          }
        }
      }));
      pushToast(`API healthy (${response?.status ?? 200})`, "success");
    } catch (err) {
      const apiError = describeApiError(err);
      setDebugInfo((prev) => ({
        ...prev,
        apiTargets: getApiTargets(),
        lastResponse: {
          ...prev?.lastResponse,
          healthCheck: {
            ok: false,
            checkedAt: new Date().toISOString(),
            error: apiError.meta
          }
        }
      }));
      pushToast(apiError.toastMessage, "error");
    }
  };

  return (
    <main className="chatbot">
      <div className="chatbot__container">
        {messages.length === 0 && !result ? (
          <div className="chatbot__welcome">
            <div className="chatbot__icon-wrapper">
              <div className="chatbot__icon chatbot__icon--gradient">
                <Sparkles className="chatbot__icon-svg" strokeWidth={1.5} />
              </div>
            </div>
            <h1 className="chatbot__title">{t("chat_title") || "Ask the AI Medical Assistant"}</h1>
            <div className="chatbot__suggestions-box">
              {demoQueries.map((item) => (
                <button
                  key={item.label}
                  className="chatbot__suggestion"
                  onClick={() => {
                    setQuery(item.value);
                    runQuery(item.value);
                  }}
                  disabled={loading}
                >
                  {item.value}
                </button>
              ))}
              <div className="chatbot__input-wrapper mt-4">
                <label className="chatbot__label" htmlFor="chat-input">{t("chat_placeholder")}</label>
                <input
                  id="chat-input"
                  className="chatbot__input"
                  type="text"
                  placeholder={t("chat_placeholder")}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      sendCurrentQuery();
                    }
                  }}
                  disabled={loading}
                />
                <button
                  className="chatbot__submit"
                  onClick={sendCurrentQuery}
                  disabled={!query.trim() || loading}
                  aria-label={t("send_question")}
                >
                  <SendHorizonal className="chatbot__submit-icon" />
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="chatbot__conversation">
            <div className="chatbot__message-scroller" ref={chatContainerRef}>
              <div className="chatbot__messages">
                {messages.map((message, idx) => {
                  const isLatestAssistant = message.role === "assistant" && idx === messages.length - 1;
                  if (result && isLatestAssistant) return null;
                  
                  const isUser = message.role === "user";
                  const messageClass = `chatbot__message chatbot__message--${isUser ? "user" : "ai"}`;
                  
                  return (
                    <div key={message.id} className={messageClass}>
                      {!isUser && (
                        <div className="chatbot__message-icon">
                          <div className="chatbot__icon chatbot__icon--gradient chatbot__icon--small">
                            <Activity className="chatbot__icon-svg" />
                          </div>
                        </div>
                      )}
                      <div className="chatbot__message-content">
                        {isUser ? (
                          <p className="chatbot__message-text">{safeRender(message.content || message.text, "")}</p>
                        ) : (
                          <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                            {safeRender(message.content || message.text, "")}
                          </ReactMarkdown>
                        )}
                        {isUser && (
                          <>
                            <div className="chatbot__message-bubble" />
                            <div className="chatbot__message-bubble chatbot__message-bubble--end" />
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
                
                {loading && (
                  <div className="chatbot__message chatbot__message--ai chatbot__message--ai-loading">
                    <div className="chatbot__message-icon">
                      <div className="chatbot__icon chatbot__icon--gradient chatbot__icon--small">
                        <Activity className="chatbot__icon-svg" />
                      </div>
                    </div>
                    <div className="chatbot__message-content">
                      <div className="flex items-center gap-2">
                         <span className="h-2 w-2 rounded-full bg-medical-500 animate-bounce" />
                         <span className="h-2 w-2 rounded-full bg-medical-500 animate-bounce" style={{ animationDelay: "0.1s" }} />
                         <span className="h-2 w-2 rounded-full bg-medical-500 animate-bounce" style={{ animationDelay: "0.2s" }} />
                      </div>
                    </div>
                  </div>
                )}
                
                {result && (
                  <div className="chatbot__message chatbot__message--ai animate-fade-in mt-4">
                    <div className="chatbot__message-icon">
                      <div className="chatbot__icon chatbot__icon--gradient chatbot__icon--small">
                        <Activity className="chatbot__icon-svg" />
                      </div>
                    </div>
                    <div className="chatbot__message-content" style={{ width: "100%" }}>
                      <div className="space-y-4 w-full">
                        {structuredAnswer?.warning && (
                          <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                            <p className="font-semibold">{structuredAnswer.warning}</p>
                          </div>
                        )}
                        <header className="space-y-1 border-b border-slate-200 pb-3 dark:border-slate-700">
                          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">{safeRender(structuredAnswer?.title, "Clinical Summary")}</h3>
                        </header>
                        
                        {isStreaming ? (
                          <p className="leading-7 text-slate-800 dark:text-slate-100">
                            {highlightTerms(streamingAnswer || "")}
                            <span className="ml-1 inline-block h-4 w-0.5 animate-pulse bg-medical-600 dark:bg-medical-400" />
                          </p>
                        ) : structuredAnswer ? (
                          isDirectMode ? (
                            <div className="space-y-4">
                              <section className="space-y-2">
                                <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-700 dark:text-slate-300">{safeRender(result?.labels?.clinical_summary, "Summary")}</h4>
                                <p className="leading-7 dark:text-slate-100">{safeRender(result?.summary || result?.answer, "")}</p>
                              </section>
                              <section className="space-y-2">
                                <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-700 dark:text-slate-300">{safeRender(result?.labels?.symptoms, "Symptoms")}</h4>
                                <ul className="list-disc pl-5 dark:text-slate-100">
                                  {(Array.isArray(result?.symptoms) ? result.symptoms : []).map((item, idx) => (
                                    <li key={`symp-${idx}`}>{highlightTerms(safeRender(item, ""))}</li>
                                  ))}
                                </ul>
                              </section>
                            </div>
                          ) : (
                            <div className="space-y-4">
                              {structuredAnswer.sections.map((section) => (
                                <section key={section.title} className="space-y-2">
                                  <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-700 dark:text-slate-300">{section.title}</h4>
                                  {section.paragraphs.map((p, i) => <p key={i} className="dark:text-slate-100">{highlightTerms(p)}</p>)}
                                  {section.bullets.length > 0 && (
                                    <ul className="list-disc pl-5 dark:text-slate-100">
                                      {section.bullets.map((b, i) => <li key={i}>{highlightTerms(b)}</li>)}
                                    </ul>
                                  )}
                                </section>
                              ))}
                            </div>
                          )
                        ) : (
                          <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                            {renderedMarkdown}
                          </ReactMarkdown>
                        )}
                        
                        {!isDirectMode && result.sources && result.sources.length > 0 && (
                          <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
                            <h4 className="text-sm font-semibold mb-3 dark:text-slate-100">{result?.labels?.sources || "Sources"}</h4>
                            <div className="grid gap-3 sm:grid-cols-2">
                              {result.sources.map((src, idx) => (
                                <SourceCard key={idx} source={src} index={idx} searchTerms={citationSearchTerms} />
                              ))}
                            </div>
                          </div>
                        )}
                        
                        <div className="flex gap-2 pt-4">
                           <Button variant="secondary" onClick={copyAnswer} disabled={!result}><Copy size={14}/> {t("btn_copy")}</Button>
                           <Button variant="secondary" onClick={() => runQuery(lastPrompt || query)} disabled={loading}><RefreshCw size={14}/> {t("btn_regenerate")}</Button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                {error && (
                  <div className="chatbot__message chatbot__message--ai mt-4">
                    <div className="chatbot__message-icon">
                      <div className="chatbot__icon chatbot__icon--gradient chatbot__icon--small">
                        <Activity className="chatbot__icon-svg" />
                      </div>
                    </div>
                    <div className="chatbot__message-content bg-red-50 text-red-800 border border-red-200">
                      <p className="font-semibold">{t("could_not_generate_answer")}</p>
                      <p className="text-sm mt-1">{error}</p>
                      {apiFailure?.retryable !== false && (
                        <button onClick={retryLastQuery} className="mt-3 px-3 py-1 bg-red-600 text-white rounded-md text-sm font-medium">
                          {t("retry")}
                        </button>
                      )}
                    </div>
                  </div>
                )}
                
              </div>
            </div>
            
            <div className="chatbot__input-box">
              <div className="chatbot__textarea-wrapper">
                <label className="chatbot__label" htmlFor="chat-textarea">{t("chat_placeholder")}</label>
                <textarea
                  id="chat-textarea"
                  className="chatbot__textarea"
                  placeholder={t("chat_placeholder")}
                  value={query}
                  disabled={loading}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      sendCurrentQuery();
                    }
                  }}
                  rows={1}
                />
                <button
                  className="chatbot__submit chatbot__submit--textarea"
                  onClick={sendCurrentQuery}
                  disabled={!query.trim() || loading}
                  aria-label={t("send_question")}
                >
                  <SendHorizonal className="chatbot__submit-icon" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
      <div className="sr-only" aria-live="polite">{t("request_state")}: {requestState}</div>
    </main>
  );
};

export default ChatBox;
