import { reactive } from 'vue';

// --- 类型定义 ---
interface RenderRequest {
  id: string;
  render: () => Promise<void>;
  onComplete: () => void;
}

interface OrchestratorState {
  isAnyoneRendering: boolean;
}

class ChatOrchestratorService {
  private renderQueue: RenderRequest[];
  private isRendering: boolean;
  public state: OrchestratorState;

  constructor() {
    this.renderQueue = [];
    this.isRendering = false;
    this.state = reactive({
      isAnyoneRendering: false,
    });
  }

  public requestRender(renderCallback: () => Promise<void>, messageId: string = 'unknown'): Promise<void> {
    return new Promise((resolve) => {
      const request: RenderRequest = {
        id: messageId,
        render: renderCallback,
        onComplete: resolve,
      };
      this.renderQueue.push(request);
      this.processQueue();
    });
  }

  private async processQueue(): Promise<void> {
    if (this.isRendering || this.renderQueue.length === 0) {
      return;
    }

    this.isRendering = true;
    this.state.isAnyoneRendering = true;
    const nextInQueue = this.renderQueue.shift();
    
    if (nextInQueue) {
        try {
            await nextInQueue.render();
        } catch (error) {
            console.error("ChatOrchestrator: 消息渲染期间出错。", error);
        } finally {
            nextInQueue.onComplete();
            this.isRendering = false;
            this.state.isAnyoneRendering = this.renderQueue.length > 0;
            
            // 处理队列中的下一个项目
            this.processQueue();
        }
    }
  }

  public isBusy(): boolean {
    return this.isRendering || this.renderQueue.length > 0;
  }

  public dispose(): void {
    this.renderQueue = [];
    this.isRendering = false;
    this.state.isAnyoneRendering = false;
  }
}

const chatOrchestratorService = new ChatOrchestratorService();
export default chatOrchestratorService;