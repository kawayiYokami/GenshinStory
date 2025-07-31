import { useAgentStore } from '@/stores/agent';

class CharacterAnimationService {
  constructor(renderWindow = 1000) {
    this.renderWindow = renderWindow;
    this.textQueue = [];
    this.isAnimating = false;
    this.currentMessageId = null;
    this.agentStore = null;
    this.animationFrameId = null;
    this.deadline = 0;
    this.onComplete = null; // 新增：用于在动画完成时调用的回调
    this.isStreamEnded = false; // 新增：标记网络流是否已结束
  }

  _getStore() {
    if (!this.agentStore) {
      this.agentStore = useAgentStore();
    }
    return this.agentStore;
  }

  enqueue(text) {
    if (text) {
      this.textQueue.push(...text.split(''));
      this.deadline = Date.now() + this.renderWindow;

      if (!this.isAnimating) {
        this.start();
      }
    }
  }

  // 新增：由外部调用，通知服务网络流已结束
  streamEnded() {
    this.isStreamEnded = true;
    // 如果此时没有在动画（意味着队列已空），则直接完成
    if (!this.isAnimating) {
      this._complete();
    }
  }

  start(messageId) {
    if (messageId) {
      this.currentMessageId = messageId;
    }
    if (this.isAnimating) {
      return;
    }
    this.isAnimating = true;
    this._animate();
  }

  _animate() {
    if (this.textQueue.length === 0) {
      // 只有当队列为空 **且** 网络流已结束时，才算真正完成
      if (this.isStreamEnded) {
        this._stop();
        this._complete();
      } else {
        // 队列暂时为空，但网络流可能还未结束，仅停止当前动画循环
        this._stop();
      }
      return;
    }

    const char = this.textQueue.shift();
    if (char) {
      this._getStore().appendMessageContent({
        messageId: this.currentMessageId,
        chunk: char,
      });
    }

    const timeRemaining = this.deadline - Date.now();
    const charsRemaining = this.textQueue.length;

    if (timeRemaining <= 0 || charsRemaining === 0) {
      if (charsRemaining > 0) {
        this._getStore().appendMessageContent({
          messageId: this.currentMessageId,
          chunk: this.textQueue.join(''),
        });
        this.textQueue = [];
      }
      // 同样，检查网络流是否结束
      if (this.isStreamEnded) {
        this._stop();
        this._complete();
      } else {
        this._stop();
      }
      return;
    }

    const nextDelay = timeRemaining / charsRemaining;
    this.animationFrameId = setTimeout(this._animate.bind(this), nextDelay);
  }

  _stop() {
    if (this.animationFrameId) {
      clearTimeout(this.animationFrameId);
      this.animationFrameId = null;
    }
    this.isAnimating = false;
  }

  // 新增：执行完成回调
  _complete() {
    if (this.onComplete) {
      this.onComplete();
      this.onComplete = null; // 防止重复调用
    }
  }

  reset() {
    this._stop();
    this.textQueue = [];
    this.currentMessageId = null;
    this.deadline = 0;
    this.onComplete = null;
    this.isStreamEnded = false;
  }
}

export default new CharacterAnimationService();