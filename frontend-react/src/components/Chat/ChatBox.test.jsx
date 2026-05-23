import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import ChatBox from "./ChatBox";

const mocks = vi.hoisted(() => ({
  pushToast: vi.fn(),
  recordQuery: vi.fn(),
  setDebugInfo: vi.fn(),
  queryRAG: vi.fn(),
  getHealth: vi.fn(),
}));

vi.mock("../../context/RuntimeContext", () => ({
  useRuntime: () => ({
    demoMode: false,
    isOffline: false,
    recordQuery: mocks.recordQuery,
    setDebugInfo: mocks.setDebugInfo,
  }),
}));

vi.mock("../../context/ToastContext", () => ({
  useToast: () => ({ pushToast: mocks.pushToast }),
}));

vi.mock("../../services/api", async () => {
  const actual = await vi.importActual("../../services/api");
  return {
    ...actual,
    queryRAG: mocks.queryRAG,
    getHealth: mocks.getHealth,
    getApiTargets: vi.fn(() => ({ primary: "http://localhost:8001", fallback: "http://localhost:8001" })),
  };
});

vi.mock("../../utils/requestResilience", () => ({
  requestWithRetry: vi.fn((requestFactory) => requestFactory()),
}));

vi.mock("../../utils/streamingText", () => ({
  streamParagraphs: vi.fn((paragraphs, _paragraphDelay, _gap, onProgress, onComplete) => {
    onProgress?.(paragraphs);
    onComplete?.();
    return vi.fn();
  }),
  estimateStreamDuration: vi.fn(() => 0),
}));

const renderChat = () => render(<ChatBox />);

const containsText = (container, snippet) =>
  Array.from(container.querySelectorAll("p.leading-7")).some((node) =>
    String(node.textContent || "").includes(snippet)
  );

beforeEach(() => {
  vi.clearAllMocks();
  mocks.queryRAG.mockReset();
  mocks.getHealth.mockReset();
  mocks.recordQuery.mockReset();
  mocks.setDebugInfo.mockReset();
  mocks.pushToast.mockReset();
});

test("submits a chat question and renders the response with sources", async () => {
  mocks.queryRAG.mockResolvedValueOnce({
    data: {
      answer: "Pneumonia symptoms include cough, fever, and shortness of breath.",
      sources: [
        {
          title: "Pneumonia Guide",
          category: "Respiratory Infection",
          score: 0.92,
          relevance_score: 0.92,
          snippet: "Pneumonia commonly causes cough, fever, and shortness of breath in adults.",
          content: {
            focus: "Symptoms",
            data: ["Cough", "Fever", "Shortness of breath"],
          },
        },
      ],
      confidence: 0.92,
      language: "en",
      question: "What are symptoms of pneumonia?",
    },
  });

  const user = userEvent.setup();
  const { container } = renderChat();

  await user.type(screen.getByPlaceholderText(/Type your question/i), "What are symptoms of pneumonia?");
  await user.click(screen.getByRole("button", { name: /send question/i }));

  await waitFor(() => {
    expect(containsText(container, "Pneumonia symptoms include cough, fever, and shortness of breath.")).toBe(true);
  });
  expect(screen.getByText("What are symptoms of pneumonia?")).toBeVisible();
  expect(screen.getAllByText(/Pneumonia Guide/i).length).toBeGreaterThan(0);
  expect(screen.getByText(/Relevance:\s*92.0%/i)).toBeVisible();
  expect(screen.getByRole("button", { name: /expand/i })).toBeVisible();
});

test("shows a friendly timeout error and allows retry", async () => {
  mocks.queryRAG
    .mockRejectedValueOnce({ message: "timeout of 10000ms exceeded", code: "ECONNABORTED" })
    .mockResolvedValueOnce({
      data: {
        answer: "Pneumonia symptoms include cough and fever.",
        sources: [
          {
            title: "Pneumonia Guide",
            category: "Respiratory Infection",
            score: 0.88,
            relevance_score: 0.88,
            snippet: "Pneumonia commonly causes cough and fever.",
            content: {
              focus: "Symptoms",
              data: ["Cough", "Fever"],
            },
          },
        ],
        confidence: 0.88,
        language: "en",
        question: "What are symptoms of pneumonia?",
      },
    });

  const user = userEvent.setup();
    const { container } = renderChat();

  await user.type(screen.getByPlaceholderText(/Type your question/i), "What are symptoms of pneumonia?");
  await user.click(screen.getByRole("button", { name: /send question/i }));

  await expect(screen.findByText(/The request took too long to complete/i)).resolves.toBeVisible();
  expect(screen.getByRole("button", { name: /^retry$/i })).toBeVisible();

  await user.click(screen.getByRole("button", { name: /^retry$/i }));

  await waitFor(() => {
    expect(containsText(container, "Pneumonia symptoms include cough and fever.")).toBe(true);
  });
  expect(mocks.queryRAG).toHaveBeenCalledTimes(2);
});

test("renders message bubbles and lets the user expand source snippets", async () => {
  mocks.queryRAG.mockResolvedValueOnce({
    data: {
      answer: "Pneumonia symptoms include cough, fever, and fatigue.",
      sources: [
        {
          title: "Clinical Pneumonia Notes",
          category: "Respiratory Infection",
          score: 0.9,
          relevance_score: 0.9,
          snippet:
            "Pneumonia commonly causes cough, fever, fatigue, chest pain, breathing difficulty, and other longer details that should be hidden until the card is expanded by the user.",
          content: {
            focus: "Symptoms",
            data: ["Cough", "Fever", "Fatigue", "Chest pain"],
          },
        },
      ],
      confidence: 0.9,
      language: "en",
      question: "What are symptoms of pneumonia?",
    },
  });

  const user = userEvent.setup();
  const { container } = renderChat();

  await user.type(screen.getByPlaceholderText(/Type your question/i), "What are symptoms of pneumonia?");
  await user.click(screen.getByRole("button", { name: /send question/i }));

  await waitFor(() => {
    expect(containsText(container, "Pneumonia symptoms include cough, fever, and fatigue.")).toBe(true);
  });
  expect(screen.getByText("What are symptoms of pneumonia?")).toBeVisible();

  const expandButton = screen.getByRole("button", { name: /expand/i });
  await user.click(expandButton);

  await waitFor(() => {
    expect(screen.getByText(/hidden until the card is expanded/i)).toBeVisible();
  });
});
