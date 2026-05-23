/**
 * Streaming/typewriter effect utilities for progressive text reveal
 * Creates a ChatGPT-like experience without changing backend behavior
 */

/**
 * Simulate streaming text reveal with configurable delay
 * @param {string} fullText - The complete text to stream
 * @param {number} delayMs - Delay between character reveals (default: 20ms)
 * @param {(text: string) => void} onProgress - Callback on each character reveal
 * @param {() => void} onComplete - Callback when streaming is complete
 * @returns {() => void} - Cancel function to stop streaming
 */
export const streamText = (fullText, delayMs = 20, onProgress, onComplete) => {
  if (!fullText || typeof fullText !== "string") {
    onComplete?.();
    return () => {};
  }

  let index = 0;
  let cancelled = false;
  const length = fullText.length;

  const nextCharacter = () => {
    if (cancelled || index >= length) {
      if (!cancelled && onComplete) onComplete();
      return;
    }

    index += 1;
    const revealed = fullText.slice(0, index);
    onProgress?.(revealed);

    setTimeout(nextCharacter, delayMs);
  };

  // Start immediately with first character
  if (length > 0) {
    index = 1;
    onProgress?.(fullText.slice(0, 1));
    setTimeout(nextCharacter, delayMs);
  } else {
    onComplete?.();
  }

  return () => {
    cancelled = true;
  };
};

/**
 * React hook for streaming text
 * @param {string} fullText - The complete text to stream
 * @param {boolean} shouldStream - Whether to enable streaming (default: true)
 * @param {number} delayMs - Delay between reveals (default: 20ms for 50 chars/sec)
 * @returns {string} - Currently revealed text
 */
export const useStreamingText = (fullText, shouldStream = true, delayMs = 20) => {
  const [displayText, setDisplayText] = React.useState("");

  React.useEffect(() => {
    if (!shouldStream || !fullText) {
      setDisplayText(fullText || "");
      return;
    }

    // Immediately show ~first 10% for perceived instant feedback
    const quickRevealLength = Math.ceil(fullText.length * 0.1);
    setDisplayText(fullText.slice(0, quickRevealLength));

    const cancel = streamText(
      fullText,
      delayMs,
      (revealed) => setDisplayText(revealed),
      () => setDisplayText(fullText)
    );

    return cancel;
  }, [fullText, shouldStream, delayMs]);

  return displayText;
};

/**
 * Multi-paragraph streaming with variable delays per paragraph
 * Useful for structured multi-line answers
 * @param {string[]} paragraphs - Array of paragraph texts
 * @param {number} paragraphDelayMs - Delay per character (default: 15ms)
 * @param {number} paragraphGapMs - Gap between paragraphs (default: 200ms)
 * @param {(texts: string[]) => void} onProgress - Called with array of revealed paragraphs
 * @param {() => void} onComplete - Called when all done
 * @returns {() => void} - Cancel function
 */
export const streamParagraphs = (
  paragraphs,
  paragraphDelayMs = 15,
  paragraphGapMs = 200,
  onProgress,
  onComplete
) => {
  if (!paragraphs || paragraphs.length === 0) {
    onComplete?.();
    return () => {};
  }

  const results = Array(paragraphs.length).fill("");
  let currentParagraph = 0;
  const cancels = [];
  let overallCancelled = false;

  const streamCurrentParagraph = () => {
    if (overallCancelled || currentParagraph >= paragraphs.length) {
      onComplete?.();
      return;
    }

    const text = paragraphs[currentParagraph];
    const cancel = streamText(
      text,
      paragraphDelayMs,
      (revealed) => {
        results[currentParagraph] = revealed;
        onProgress?.(results);
      },
      () => {
        results[currentParagraph] = text;
        currentParagraph += 1;
        setTimeout(streamCurrentParagraph, paragraphGapMs);
      }
    );

    cancels.push(cancel);
  };

  streamCurrentParagraph();

  return () => {
    overallCancelled = true;
    cancels.forEach((cancel) => cancel?.());
  };
};

/**
 * Estimate streaming duration
 * @param {string} text - Text to stream
 * @param {number} delayMs - Delay per character
 * @returns {number} - Duration in milliseconds
 */
export const estimateStreamDuration = (text, delayMs = 20) => {
  return (text || "").length * delayMs;
};

/**
 * Format streaming speed indicator (for UX feedback)
 * @param {number} charsPerSecond - Characters per second
 * @returns {string} - Human-readable speed
 */
export const formatStreamSpeed = (charsPerSecond = 50) => {
  return `${charsPerSecond} chars/sec (${Math.round(charsPerSecond * 0.06)} words/sec)`;
};
