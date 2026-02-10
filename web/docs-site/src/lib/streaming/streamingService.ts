import logger from '@/features/app/services/loggerService';

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * @typedef {object} PacedStreamUpdate
 * @property {string} value - 文本块。
 * @property {boolean} done - 标记整个流是否完成的标志。
 */
export interface PacedStreamUpdate {
    value: string;
    done: boolean;
}

/**
 * 消费文本流并产生有节奏的、分块的文本更新。
 * 此服务负责控制“打字”节奏。
 * @param textStream 来自 Vercel AI SDK 的文本流 (AsyncIterable<string>)。
 * @returns 一个异步生成器，产生有节奏的文本块。
 */
export async function* createPacedStream(textStream: AsyncIterable<string>): AsyncGenerator<PacedStreamUpdate> {

    for await (const chunk of textStream) {
        // chunk 已经是纯文本 delta
        if (chunk) {
            // 如果 delta 很大，则分块以获得更平滑的“打字”效果。
            if (chunk.length > 5) {
                let content = chunk;
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
                // 对于小的 delta，直接产生它们。
                yield { value: chunk, done: false };
            }
        }
    }

    // 向消费者发出完成信号。
    yield { value: '', done: true };
}