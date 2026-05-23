import { render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

const apiGet = vi.fn();
const navigateMock = vi.fn();

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: {
      id: "user-123",
      account_id: "acct-user-456",
      email: "test@example.com",
      created_at: "2024-01-01T00:00:00Z"
    },
    logout: vi.fn(),
    isAuthenticated: true
  })
}));

vi.mock("../hooks/useTranslate", () => ({
  useTranslate: () => (key) => key
}));

vi.mock("../services/api", () => ({
  default: {
    get: apiGet
  }
}));

vi.mock("../components/UsageDashboard", () => ({
  default: ({ accountId }) => <div data-testid="usage-dashboard" data-account-id={accountId ?? ""} />
}));

vi.mock("react-router-dom", () => ({
  Link: ({ to, children }) => <a href={to}>{children}</a>,
  useNavigate: () => navigateMock
}));

const { default: DashboardPage } = await import("./DashboardPage");

describe("DashboardPage", () => {
  beforeEach(() => {
    apiGet.mockReset();
    navigateMock.mockReset();
  });

  it("passes the authenticated user account id to UsageDashboard when the dashboard payload has no account_id", async () => {
    apiGet.mockResolvedValueOnce({
      data: {
        statistics: {
          total_chat_queries: 1,
          total_images_analyzed: 2,
          total_vital_measurements: 3,
          this_week_queries: 4
        }
      }
    });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(apiGet).toHaveBeenCalledWith("/api/v1/auth/dashboard");
    });

    await waitFor(() => {
      expect(screen.getByTestId("usage-dashboard")).toHaveAttribute("data-account-id", "acct-user-456");
    });
  });
});