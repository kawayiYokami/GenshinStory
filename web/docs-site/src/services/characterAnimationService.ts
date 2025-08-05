import { useAgentStore } from '@/stores/agentStore';

// 定义 AgentStore 类型作为 useAgentStore 的返回类型
type AgentStore = ReturnType<typeof useAgentStore>;

class CharacterAnimationService {
  private renderWindow: number;
  private textQueue: string[];
  private isAnimating: boolean;
  private currentMessageId: string | null;
  private agentStore: AgentStore | null;
  private animationFrameId: number | null;
  private deadline: number;
  private onComplete: (() => void) | null;
  private isStreamEnded: boolean;

  constructor(renderWindow = 1000) {
    this.renderWindow = renderWindow;
    this.textQueue = [];
    this.isAnimating = false;
    this.currentMessageId = null;
    this.agentStore = null;
    this.animationFrameId = null;
    this.deadline = 0;
    this.onComplete = null;
    this.isStreamEnded = false;
  }

  private _getStore(): AgentStore {
    if (!this.agentStore) {
      this.agentStore = useAgentStore();
    }
    return this.agentStore;
  }

  public enqueue(text: string): void {
    if (text) {
      this.textQueue.push(...text.split(''));
      this.deadline = Date.now() + this.renderWindow;

      if (!this.isAnimating) {
        this.start();
      }
    }
  }

  public streamEnded(): void {
    this.isStreamEnded = true;
    if (!this.isAnimating) {
      this._complete();
    }
  }

  public start(messageId?: string): void {
    if (messageId) {
      this.currentMessageId = messageId;
    }
    if (this.isAnimating) {
      return;
    }
    this.isAnimating = true;
    this._animate();
  }

  private _animate(): void {
    if (this.textQueue.length === 0) {
      if (this.isStreamEnded) {
        this._stop();
        this._complete();
      } else {
        this._stop();
      }
      return;
    }

    const char = this.textQueue.shift();
    if (char && this.currentMessageId) {
      this._getStore().appendMessageContent({
        messageId: this.currentMessageId,
        chunk: char,
      });
    }

    const timeRemaining = this.deadline - Date.now();
    const charsRemaining = this.textQueue.length;

    if (timeRemaining <= 0 || charsRemaining === 0) {
      if (charsRemaining > 0 && this.currentMessageId) {
        this._getStore().appendMessageContent({
          messageId: this.currentMessageId,
          chunk: this.textQueue.join(''),
        });
        this.textQueue = [];
      }
      if (this.isStreamEnded) {
        this._stop();
        this._complete();
      } else {
        this._stop();
      }
      return;
    }

    const nextDelay = timeRemaining / charsRemaining;
    this.animationFrameId = window.setTimeout(this._animate.bind(this), nextDelay);
  }

  private _stop(): void {
    if (this.animationFrameId) {
      clearTimeout(this.animationFrameId);
      this.animationFrameId = null;
    }
    this.isAnimating = false;
  }

  private _complete(): void {
    if (this.onComplete) {
      this.onComplete();
      this.onComplete = null;
    }
  }

  public reset(): void {
    this._stop();
    this.textQueue = [];
    this.currentMessageId = null;
    this.deadline = 0;
    this.onComplete = null;
    this.isStreamEnded = false;
  }
}

export default new CharacterAnimationService();