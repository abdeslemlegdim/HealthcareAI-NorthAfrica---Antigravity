import React, { StrictMode, useEffect, useLayoutEffect, useRef, useState } from "https://esm.sh/react";
import { createRoot } from "https://esm.sh/react-dom/client";
import { Sparkles, ArrowRight, Headset, Globe } from "https://esm.sh/lucide-react";
import Markdown from "https://esm.sh/react-markdown";

createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<AIChat />
	</StrictMode>
);

interface Message {
	id: string;
	type: MessageType;
	content: string;
}
type MessageType = "user" | "ai";

const AIChatText = {
	p({ node, ...rest }) {
		return <p className="chatbot__message-text" {...rest} />
	},
	ul({ node, ...rest }) {
		return <ul className="chatbot__message-text" {...rest} />
	}
};

function AIChat() {
	const chatScrollerRef = useRef<HTMLDivElement>(null);
	const chatMessagesRef = useRef<HTMLDivElement>(null);
	const [messages, setMessages] = useState<Message[]>([]);
	const [input, setInput] = useState<string>("");
	const [isLoading, setIsLoading] = useState<boolean>(false);
	const [scrollbarWidth, setScrollbarWidth] = useState<number>(0);
	const messagesStyle: React.CSSProperties = {
		"paddingInlineEnd": `calc(1.5em - ${scrollbarWidth}px)`
	};
	const placeholder = "Ask anything…";
	const suggestions: string[] = [
		"Write an email to the marketing team",
		"Summarize key points",
		"Create a follow-up checklist"
	];
	const suggestionsFollowUp: string[] = [
		"Create in-depth analysis",
		"Identify actionable tasks"
	];
	/*
	mock responses to messages containing a specific word, typically the suggestions;
	normally you need an API key for the LLM you want to use to generate real results
	*/
	const mockResponses: Record<string, string> = {
		"default": "This is a simulated AI response to your message.",
		"marketing": `Subject: Request Marketing Support for [Project Name]

Hi Team,

I’m reaching out to get your eyes on [Project Name], which we are aiming to launch on [Date].
To ensure this is successful, we’d love the marketing team’s help with:

- [Asset 1] (e.g. Social media graphics)
- [Asset 2] (e.g. An email blast to our current subscriber list)
- [Asset 3] (e.g. A landing page update)

I’ve attached the project brief and target audience details. Could we schedule a 15-minute sync later this week to discuss the timeline and bandwidth?

Best regards,

[Your Name]`,
		"summarize": "I’d love to help with that! However, you haven’t provided the text, article, or topic you’d like me to summarize yet. Please paste the content or describe the topic below, and I will break it down into a clear, organized summary for you.",
		"checklist": `To give you the most effective checklist, it helps to know what you are following up on (a job interview, a sales lead, or a project task). However, here is a Universal Professional Follow-Up Checklist that works for most situations. It ensures you stay organized, polite, and effective.

- [ ] Review previous notes
- [ ] Identify the “Value Add”
- [ ] Check the timing
- [ ] Verify contact details
- [ ] Subject Line
- [ ] The Hook
- [ ] The “Why”
- [ ] The Call to Action (CTA)
- [ ] Proofread
- [ ] Log the contact
- [ ] Set a “Silence Reminder”
- [ ] The “Three-Strike” Rule`,
		"analysis": "To provide you with a high-quality, in-depth analysis, I need to know the subject you are focusing on. Whether it is a business case, a scientific phenomenon, a literary work, or a market trend, I can apply a structured analytical framework to help you uncover deep insights.",
		"tasks": `To help you identify actionable tasks, I need a little more context about what you are looking at. Are you reviewing meeting notes, a project plan, a long email thread, or perhaps just organizing your own thoughts?`
	};
	const findMockResponse = (input: string) => {
		const mockKeys = Object.keys(mockResponses);
		const inputNoCaps = input.toLowerCase();
		const responseKey = mockKeys.find(key => inputNoCaps.includes(key)) || "default";

		return mockResponses[responseKey];
	};
	// normal stuff continued
	const randomID = () => {
		const random = crypto.getRandomValues(new Uint32Array(1))[0] / 2 ** 32;
		// use an 8-digit hex value
		return (Math.floor(random * 2 ** 32)).toString(16).padStart(8, "0");
	};
	const handleSuggestionClick = (suggestion: string) => {
		handleSubmit(suggestion)
	};
	const handleSubmit = (text?: string) => {
		const messageText = text || input;
		const userMessage: Message = {
			id: randomID(),
			type: "user",
			content: messageText
		};

		setIsLoading(true);
		setMessages((prev) => [...prev, userMessage]);
		setInput("");

		setTimeout(() => {
			const aiMessage: Message = {
				id: randomID(),
				type: "ai",
				content: findMockResponse(messageText),
			};
			setIsLoading(false);
			setMessages((prev) => [...prev, aiMessage]);
		}, 1500);
	};
	const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			handleSubmit();
		}
	};

	useEffect(() => {
		if (chatScrollerRef.current) {
			chatScrollerRef.current.scrollTo({
				top: chatScrollerRef.current.scrollHeight,
				left: 0,
				behavior: "smooth"
			});
		}
	}, [messages]);

	useLayoutEffect(() => {
		const calculateWidth = () => {
			const scrollerWidth = chatScrollerRef.current?.offsetWidth || 0;
			const messagesWidth = chatMessagesRef.current?.offsetWidth || 0;
			const width = scrollerWidth - messagesWidth;

			setScrollbarWidth(width);
		};

		const frameId = requestAnimationFrame(calculateWidth);

		return () => cancelAnimationFrame(frameId);
	}, [messages]);

	return (
		<main className="chatbot">
			<div className="chatbot__container">
				{messages.length === 0 ? (
					<div className="chatbot__welcome">
						<div className="chatbot__icon-wrapper">
							<div className="chatbot__icon chatbot__icon--gradient">
								<Sparkles className="chatbot__icon-svg" strokeWidth={1.5} />
							</div>
						</div>
						<h1 className="chatbot__title">Asking with AI suggestions</h1>
						<div className="chatbot__suggestions-box">
							{suggestions.map((suggestion, i) => {
								const suggestionKey = `suggestion${i + 1}`;

								return (
									<button
										key={suggestionKey}
										className="chatbot__suggestion"
										onClick={() => handleSuggestionClick(suggestion)}
									>
										{suggestion}
									</button>
								);
							})}
							<div className="chatbot__input-wrapper">
								<label
									className="chatbot__label"
									htmlFor="chat-input"
								>
									Ask
								</label>
								<input
									id="chat-input"
									className="chatbot__input"
									type="text"
									placeholder={placeholder}
									value={input}
									onChange={(e) => setInput(e.target.value)}
									onKeyDown={handleKeyDown}
								/>
								<button
									className="chatbot__submit"
									onClick={() => handleSubmit()}
									disabled={!input.trim()}
									aria-label="Submit"
								>
									<ArrowRight className="chatbot__submit-icon" />
								</button>
							</div>
						</div>
					</div>
				) : (
					<div className="chatbot__conversation">
						<div className="chatbot__message-scroller" ref={chatScrollerRef}>
							<div
								className="chatbot__messages"
								ref={chatMessagesRef}
								style={messagesStyle}
							>
								{messages.map((message, i) => {
									const messageClass = `chatbot__message chatbot__message--${message.type}`;
									const messageId = `message${message.id}`;

									return (
										<div
											key={messageId}
											className={messageClass}
										>
											{message.type === "ai" && (
												<div className="chatbot__message-icon">
													<div className="chatbot__icon chatbot__icon--gradient  chatbot__icon--small">
														<Headset className="chatbot__icon-svg" />
													</div>
												</div>
											)}
											<div className="chatbot__message-content">
												<Markdown components={AIChatText}>
													{message.content}
												</Markdown>
												{message.type === "user" && <>
													<div className="chatbot__message-bubble" />
													<div className="chatbot__message-bubble chatbot__message-bubble--end" />
												</>}
											</div>
										</div>
									);
								})}
								{isLoading && (
									<div className="chatbot__message chatbot__message--ai chatbot__message--ai-loading">
										<div className="chatbot__message-icon">
											<div className="chatbot__icon chatbot__icon--gradient  chatbot__icon--small">
												<Headset className="chatbot__icon-svg" />
											</div>
										</div>
										<Loader />
									</div>
								)}
							</div>
						</div>
						<div className="chatbot__input-box">
							<div className="chatbot__suggestion-tags">
								{suggestionsFollowUp.map((suggestion, i) => {
									const suggestionTagKey = `suggestion-tag${i + 1}`;

									return (
										<button
											key={suggestionTagKey}
											className="chatbot__suggestion-tag"
											type="button"
											disabled={isLoading}
											onClick={() => handleSuggestionClick(suggestion)}
										>
											{suggestion}
										</button>
									);
								})}
							</div>
							<div className="chatbot__textarea-wrapper">
								<label
									className="chatbot__label"
									htmlFor="chat-textarea"
								>
									Ask
								</label>
								<textarea
									id="chat-textarea"
									className="chatbot__textarea"
									placeholder={placeholder}
									value={input}
									disabled={isLoading}
									onChange={(e) => setInput(e.target.value)}
									onKeyDown={handleKeyDown}
									rows={1}
								/>
								<button className="chatbot__globe-button" aria-label="Globe">
									<Globe className="chatbot__globe-icon" />
								</button>
								<button
									className="chatbot__submit chatbot__submit--textarea"
									onClick={() => handleSubmit()}
									disabled={!input.trim() || isLoading}
									aria-label="Submit"
								>
									<ArrowRight className="chatbot__submit-icon" />
								</button>
							</div>
						</div>
					</div>
				)}
			</div>
		</main>
	)
}

function Loader() {
	return (
		<svg
			className="chatbot__loader lucide lucide-loader-icon lucide-loader"
			width="24"
			height="24"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="2"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<path className="chatbot__loader-line" d="m4.9 4.9 2.9 2.9" />
			<path className="chatbot__loader-line" d="M2 12h4" />
			<path className="chatbot__loader-line" d="m4.9 19.1 2.9-2.9" />
			<path className="chatbot__loader-line" d="M12 18v4" />
			<path className="chatbot__loader-line" d="m16.2 16.2 2.9 2.9" />
			<path className="chatbot__loader-line" d="M18 12h4" />
			<path className="chatbot__loader-line" d="m16.2 7.8 2.9-2.9" />
			<path className="chatbot__loader-line" d="M12 2v4" />
		</svg>
	);
}