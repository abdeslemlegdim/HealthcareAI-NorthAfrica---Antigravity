import { describe, it, expect, vi, beforeEach } from "vitest";

const apiGet = vi.fn();

vi.mock("./api", () => ({
  default: {
    get: apiGet
  }
}));

const { getAccountSummary } = await import("./usageApi");

describe("getAccountSummary", () => {
  beforeEach(() => {
    apiGet.mockReset();
  });

  it("uses the authenticated me summary endpoint when no account id is provided", async () => {
    apiGet.mockResolvedValueOnce({ data: { available_credits: 42 } });

    const result = await getAccountSummary();

    expect(apiGet).toHaveBeenCalledWith("/api/v1/accounts/me/summary");
    expect(result).toEqual({ available_credits: 42 });
  });

  it("uses the explicit account summary endpoint when an account id is provided", async () => {
    apiGet.mockResolvedValueOnce({ data: { available_credits: 99 } });

    const result = await getAccountSummary("acct_123");

    expect(apiGet).toHaveBeenCalledWith("/api/v1/accounts/acct_123/summary");
    expect(result).toEqual({ available_credits: 99 });
  });
});