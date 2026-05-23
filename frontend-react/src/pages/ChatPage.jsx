import ChatBox from "../components/Chat/ChatBox";
import { useTranslate } from "../hooks/useTranslate";
import "../styles/chat.css";

const ChatPage = () => {
  const t = useTranslate();

  return (
    <div className="app-page mx-auto w-full max-w-6xl space-y-5">
      <div className="app-shell-panel animate-slide-up p-6 sm:p-8">
        <div className="app-chip mb-4">Knowledge Assistant</div>
        <h2 className="app-shell-title bg-gradient-to-r from-white via-slate-100 to-teal-200 bg-clip-text text-3xl font-extrabold text-transparent">{t("chat_title")}</h2>
        <p className="mt-2 max-w-3xl text-base text-slate-300">{t("chat_description")}</p>
      </div>
      <ChatBox />
    </div>
  );
};

export default ChatPage;
