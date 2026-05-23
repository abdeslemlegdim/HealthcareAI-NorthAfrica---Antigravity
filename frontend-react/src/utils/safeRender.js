export const safeRender = (value, fallback = "") => {
  if (value === null || value === undefined) return fallback;
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);

  if (Array.isArray(value)) {
    const normalized = value
      .map((item) => safeRender(item, ""))
      .filter((item) => String(item).trim().length > 0);
    return normalized.length ? normalized.join(", ") : fallback;
  }

  if (typeof value === "object") {
    const preferred = ["text", "answer", "content", "data", "focus", "message", "label", "title"];
    for (const key of preferred) {
      if (value[key] !== undefined && value[key] !== null) {
        return safeRender(value[key], fallback);
      }
    }

    try {
      return JSON.stringify(value);
    } catch {
      return fallback;
    }
  }

  return fallback;
};

export const safeNumber = (value, fallback = 0) => {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
};
