const fs = require('fs');
const file = 'frontend-react/src/components/Chat/ChatBox.jsx';

const newJSX = `
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
                  const messageClass = \`chatbot__message chatbot__message--\${isUser ? "user" : "ai"}\`;
                  
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
                                    <li key={\`symp-\${idx}\`}>{highlightTerms(safeRender(item, ""))}</li>
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
`;

let content = fs.readFileSync(file, 'utf8');
const startIdx = content.indexOf('  return (');
if (startIdx !== -1) {
  content = content.substring(0, startIdx) + newJSX;
  fs.writeFileSync(file, content);
  console.log('Successfully patched ChatBox.jsx');
} else {
  console.log('Could not find return statement in ChatBox.jsx');
}
