import logger from './loggerService.js';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * @typedef {object} PacedStreamUpdate
 * @property {string} value - The text chunk.
 * @property {boolean} done - A flag indicating if the entire stream is complete.
 */

/**
 * Consumes an OpenAI SDK stream and yields paced, chunked text updates.
 * This service is responsible for controlling the "typing" rhythm.
 * @param {AsyncIterable<import('openai').API.Chat.Completions.ChatCompletionChunk>} openaiStream The raw stream from the openai library.
 * @returns {AsyncGenerator<PacedStreamUpdate>} An async generator yielding paced text chunks.
 */
export async function* createPacedStream(openaiStream) {
    
    for await (const chunk of openaiStream) {
        const delta = chunk.choices[0]?.delta?.content ?? '';
        const finishReason = chunk.choices[0]?.finish_reason;

        if (delta) {
            // If the delta is large, chunk it for a smoother "typing" effect.
            if (delta.length > 5) {
                let content = delta;
                while (content !== '') {
                    const chunkSize = Math.min(Math.floor(Math.random() * 3) + 1, content.length);
                    const chunkPart = content.slice(0, chunkSize);
                    
                    yield { value: chunkPart, done: false };
                    
                    if (typeof document !== 'undefined' && document.visibilityState !== 'hidden') {
                        await sleep(10);
                    }
                    content = content.slice(chunkSize);
                }
            } else {
                // For small deltas, yield them directly.
                yield { value: delta, done: false };
            }
        }
        
        // When the finish_reason is "stop", we know the stream is truly complete.
        if (finishReason === 'stop') {
            break; // Exit the loop.
        }
    }
    
    // Signal completion to the consumer.
    yield { value: '', done: true };
}