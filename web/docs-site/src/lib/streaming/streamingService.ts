import logger from '@/features/app/services/loggerService';
import type { Stream } from 'openai/streaming';
import type { ChatCompletionChunk } from 'openai/resources/chat';

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
 * 消费 OpenAI SDK 流并产生有节奏的、分块的文本更新。
 * 此服务负责控制“打字”节奏。
 * @param openaiStream 来自 openai 库的原始流。
 * @returns 一个异步生成器，产生有节奏的文本块。
 */
export async function* createPacedStream(openaiStream: Stream<ChatCompletionChunk>): AsyncGenerator<PacedStreamUpdate> {
    
    for await (const chunk of openaiStream) {
        const delta = chunk.choices[0]?.delta?.content ?? '';
        const finishReason = chunk.choices[0]?.finish_reason;

        if (delta) {
            // 如果 delta 很大，则分块以获得更平滑的“打字”效果。
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
                // 对于小的 delta，直接产生它们。
                yield { value: delta, done: false };
            }
        }
        
        // 当 finish_reason 为 "stop" 时，我们知道流真正完成了。
        if (finishReason === 'stop') {
            break; // 退出循环。
        }
    }
    
    // 向消费者发出完成信号。
    yield { value: '', done: true };
}