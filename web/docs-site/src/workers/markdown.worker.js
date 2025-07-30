// web/docs-site/src/workers/markdown.worker.ts
import { marked } from 'marked';
// Listen for messages from the main thread
self.onmessage = async (event) => {
    const markdownText = event.data;
    if (typeof markdownText !== 'string') {
        self.postMessage({ error: 'Invalid input. Expected a string.' });
        return;
    }
    try {
        // Perform the CPU-intensive task in the worker thread
        const html = await marked(markdownText);
        // Send the result back to the main thread
        self.postMessage({ html });
    }
    catch (error) {
        self.postMessage({ error: error instanceof Error ? error.message : 'An unknown error occurred during Markdown parsing.' });
    }
};
//# sourceMappingURL=markdown.worker.js.map