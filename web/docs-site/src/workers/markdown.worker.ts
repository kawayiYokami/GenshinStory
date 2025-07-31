// web/docs-site/src/workers/markdown.worker.ts
import { marked } from 'marked';

// --- Worker Message Handling ---
self.onmessage = async (event: MessageEvent<{ markdownText: string; originalId: any }>) => {
  const { markdownText, originalId } = event.data;

  if (typeof markdownText !== 'string') {
    self.postMessage({ error: 'Invalid input. Expected a string.', originalId });
    return;
  }

  try {
    const html = await marked(markdownText);
    // Send back the HTML along with the original ID to map it correctly.
    self.postMessage({ html, originalId });
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred during Markdown parsing.';
    self.postMessage({ error: errorMessage, originalId });
  }
};