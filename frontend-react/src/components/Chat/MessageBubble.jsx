const MessageBubble = ({ role = "assistant", timestamp, style, children }) => {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        style={style}
        className={`max-w-3xl rounded-2xl px-4 py-3 text-sm shadow-sm transition-all duration-500 ${
          isUser
            ? "bg-gradient-to-r from-medical-600 to-tealmed-600 text-white"
            : "border border-slate-200 bg-white text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
        } animate-slide-up`}
      >
        {timestamp ? <p className={`mb-2 text-[11px] ${isUser ? "text-cyan-100" : "text-slate-500 dark:text-slate-400"}`}>{timestamp}</p> : null}
        {children}
      </div>
    </div>
  );
};

export default MessageBubble;
