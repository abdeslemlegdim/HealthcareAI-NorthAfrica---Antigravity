export const withTimeout = (promise, timeoutMs = 10000) => {
  let timer;
  const timeoutPromise = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error("Request timeout. Please try again.")), timeoutMs);
  });

  return Promise.race([promise, timeoutPromise]).finally(() => clearTimeout(timer));
};

export const requestWithRetry = async (requestFactory, options = {}) => {
  const { retries = 1, timeoutMs = 10000 } = options;

  let lastError;
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      const response = await withTimeout(requestFactory(), timeoutMs);
      return response;
    } catch (error) {
      lastError = error;
      if (attempt < retries) {
        // Small delay before a single retry for transient network glitches.
        // eslint-disable-next-line no-await-in-loop
        await new Promise((resolve) => setTimeout(resolve, 350));
      }
    }
  }

  throw lastError;
};
