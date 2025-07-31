import { reactive } from 'vue';

class ChatOrchestratorService {
  constructor() {
    this.renderQueue = [];
    this.isRendering = false;
    this.state = reactive({
      isAnyoneRendering: false,
    });
  }

  requestRender(renderCallback, messageId = 'unknown') {
    return new Promise((resolve) => {
      const request = {
        id: messageId,
        render: renderCallback,
        onComplete: resolve,
      };
      this.renderQueue.push(request);
      this.processQueue();
    });
  }

  async processQueue() {
    if (this.isRendering || this.renderQueue.length === 0) {
      return;
    }

    this.isRendering = true;
    this.state.isAnyoneRendering = true;
    const nextInQueue = this.renderQueue.shift();
    
    try {
      await nextInQueue.render();
    } catch (error) {
      console.error("ChatOrchestrator: Error during message rendering.", error);
    } finally {
      nextInQueue.onComplete();
      this.isRendering = false;
      this.state.isAnyoneRendering = this.renderQueue.length > 0;
      
      // Process next item in the queue
      this.processQueue();
    }
  }

  isBusy() {
    return this.isRendering || this.renderQueue.length > 0;
  }
   dispose() {
    this.renderQueue = [];
    this.isRendering = false;
    this.state.isAnyoneRendering = false;
  }
}

const chatOrchestratorService = new ChatOrchestratorService();
export default chatOrchestratorService;