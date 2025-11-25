/**
 * @fileoverview 对话截图服务
 * @description 使用Canvas API生成美观的对话截图
 * @author yokami
 */

import type { Message } from '../types';

export interface ScreenshotConfig {
  width?: number;
  title?: string;
  quality?: number;
  backgroundColor?: string;
  padding?: number;
}

export class ScreenshotService {
  private config: ScreenshotConfig;
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;

  constructor(config: ScreenshotConfig) {
    this.config = {
      width: 800,
      quality: 0.9,
      backgroundColor: '#ffffff',
      padding: 20,
      ...config
    };

    // 创建Canvas
    this.canvas = document.createElement('canvas');
    const ctx = this.canvas.getContext('2d');
    if (!ctx) {
      throw new Error('无法创建Canvas渲染上下文');
    }
    this.ctx = ctx;
  }

  /**
   * 生成对话截图
   * @param messages 对话消息数组
   * @returns JPEG格式的Data URL
   */
  async captureConversation(messages: Message[]): Promise<string> {
    const { width, padding } = this.config;
    const safeWidth = width ?? 800; // 提供默认值以防止 undefined
    const safePadding = padding ?? 20; // 提供默认值以防止 undefined

    // 计算所需的高度
    const headerHeight = 80;
    const footerHeight = 60;
    const messagesHeight = this.calculateMessagesHeight(messages, safeWidth - safePadding * 2);
    const totalHeight = headerHeight + messagesHeight + footerHeight + safePadding * 2;

    // 设置Canvas尺寸
    this.canvas.width = safeWidth;
    this.canvas.height = totalHeight;

    // 绘制背景
    this.drawBackground();

    // 绘制头部
    this.drawHeader();

    // 绘制消息
    let currentY = headerHeight + safePadding;
    const visibleMessages = messages.filter(msg =>
      msg.role === 'user' || msg.role === 'assistant'
    );

    for (const message of visibleMessages) {
      await this.drawMessage(message, currentY, safeWidth - safePadding * 2);
      currentY += this.getMessageHeight(message, safeWidth - safePadding * 2) + 16;
    }

    // 绘制底部
    this.drawFooter(totalHeight - footerHeight);

    // 转换为JPEG
    return new Promise((resolve, reject) => {
      this.canvas.toBlob((blob) => {
        if (blob) {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result as string);
          reader.onerror = reject;
          reader.readAsDataURL(blob);
        } else {
          reject(new Error('无法生成图片'));
        }
      }, 'image/jpeg', this.config.quality);
    });
  }

  /**
   * 绘制背景
   */
  private drawBackground(): void {
    this.ctx.fillStyle = this.config.backgroundColor ?? '#ffffff';
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
  }

  /**
   * 绘制头部
   */
  private drawHeader(): void {
    const { width } = this.config;
    const safeWidth = width ?? 800; // 提供默认值以防止 undefined

    // 绘制渐变背景
    const gradient = this.ctx.createLinearGradient(0, 0, safeWidth, 80);
    gradient.addColorStop(0, '#667eea');
    gradient.addColorStop(1, '#764ba2');
    this.ctx.fillStyle = gradient;
    this.ctx.fillRect(0, 0, safeWidth, 80);

    // 绘制标题
    this.ctx.fillStyle = '#ffffff';
    this.ctx.font = 'bold 18px system-ui';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText(
      this.config.title || 'AI 对话记录',
      safeWidth / 2,
      40
    );
  }

  /**
   * 绘制单个消息
   */
  private async drawMessage(message: Message, y: number, maxWidth: number): Promise<void> {
    const isUser = message.role === 'user';
    const padding = 12;
    const avatarSize = 32;
    const avatarX = isUser ? maxWidth - avatarSize - 20 : 20;
    const bubbleX = isUser ? maxWidth - 280 : 60;
    const bubbleWidth = 200;
    const content = this.extractTextContent(message);
    const lines = this.wrapText(content, bubbleWidth - padding * 2);
    const bubbleHeight = lines.length * 20 + padding * 2;

    // 绘制头像背景
    this.ctx.fillStyle = isUser ? '#3b82f6' : '#10b981';
    this.ctx.beginPath();
    this.ctx.arc(avatarX + avatarSize/2, y + avatarSize/2, avatarSize/2, 0, 2 * Math.PI);
    this.ctx.fill();

    // 绘制头像文字
    this.ctx.fillStyle = '#ffffff';
    this.ctx.font = '16px system-ui';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText(
      isUser ? '👤' : '🤖',
      avatarX + avatarSize/2,
      y + avatarSize/2
    );

    // 绘制消息气泡
    this.drawMessageBubble(bubbleX, y, bubbleWidth, bubbleHeight, isUser);

    // 绘制消息文字
    this.ctx.fillStyle = '#111827';
    this.ctx.font = '14px system-ui';
    this.ctx.textAlign = 'left';
    this.ctx.textBaseline = 'top';
    lines.forEach((line, index) => {
      this.ctx.fillText(line, bubbleX + padding, y + padding + index * 20);
    });
  }

  /**
   * 绘制消息气泡
   */
  private drawMessageBubble(x: number, y: number, width: number, height: number, isUser: boolean): void {
    this.ctx.fillStyle = isUser ? '#f3f4f6' : '#ffffff';
    this.ctx.strokeStyle = '#e5e7eb';
    this.ctx.lineWidth = 1;

    // 绘制圆角矩形
    this.roundRect(x, y, width, height, 12);
    this.ctx.fill();

    if (!isUser) {
      this.ctx.stroke();
    }
  }

  /**
   * 绘制圆角矩形
   */
  private roundRect(x: number, y: number, width: number, height: number, radius: number): void {
    this.ctx.beginPath();
    this.ctx.moveTo(x + radius, y);
    this.ctx.lineTo(x + width - radius, y);
    this.ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    this.ctx.lineTo(x + width, y + height - radius);
    this.ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    this.ctx.lineTo(x + radius, y + height);
    this.ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    this.ctx.lineTo(x, y + radius);
    this.ctx.quadraticCurveTo(x, y, x + radius, y);
    this.ctx.closePath();
  }

  /**
   * 绘制底部
   */
  private drawFooter(y: number): void {
    const { width } = this.config;
    const safeWidth = width ?? 800; // 提供默认值以防止 undefined

    // 绘制底部背景
    this.ctx.fillStyle = '#f9fafb';
    this.ctx.fillRect(0, y, safeWidth, 60);

    // 绘制分隔线
    this.ctx.strokeStyle = '#e5e7eb';
    this.ctx.lineWidth = 1;
    this.ctx.beginPath();
    this.ctx.moveTo(0, y);
    this.ctx.lineTo(safeWidth, y);
    this.ctx.stroke();

    // 绘制底部文字
    const date = new Date().toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });

    this.ctx.fillStyle = '#6b7280';
    this.ctx.font = '12px system-ui';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText(`生成于 ${date} | AI 对话助手`, safeWidth / 2, y + 30);
  }

  /**
   * 提取消息文本内容
   */
  private extractTextContent(message: Message): string {
    if (typeof message.content === 'string') {
      return message.content;
    }

    if (Array.isArray(message.content)) {
      return message.content
        .filter(part => part.type === 'text')
        .map(part => part.text)
        .join('\n');
    }

    return String(message.content || '');
  }

  /**
   * 文本换行处理
   */
  private wrapText(text: string, maxWidth: number): string[] {
    const lines: string[] = [];
    const paragraphs = text.split('\n');

    for (const paragraph of paragraphs) {
      if (!paragraph.trim()) {
        lines.push('');
        continue;
      }

      const words = paragraph.split('');
      let currentLine = '';

      for (const char of words) {
        const testLine = currentLine + char;
        const metrics = this.ctx.measureText(testLine);

        if (metrics.width > maxWidth && currentLine.length > 0) {
          lines.push(currentLine);
          currentLine = char;
        } else {
          currentLine = testLine;
        }
      }

      if (currentLine) {
        lines.push(currentLine);
      }
    }

    return lines;
  }

  /**
   * 计算单个消息的高度
   */
  private getMessageHeight(message: Message, maxWidth: number): number {
    const content = this.extractTextContent(message);
    const lines = this.wrapText(content, maxWidth - 24);
    const messagePadding = 12 * 2; // 重命名以避免与配置中的 padding 混淆
    return lines.length * 20 + messagePadding;
  }

  /**
   * 计算所有消息的总高度
   */
  private calculateMessagesHeight(messages: Message[], maxWidth: number): number {
    const visibleMessages = messages.filter(msg =>
      msg.role === 'user' || msg.role === 'assistant'
    );

    if (visibleMessages.length === 0) return 100;

    const totalHeight = visibleMessages.reduce((sum, message) => {
      return sum + this.getMessageHeight(message, maxWidth) + 16; // 16px 间距
    }, 0);

    return totalHeight - 16; // 去掉最后一个间距
  }
}

/**
 * 下载图片的辅助函数
 */
export function downloadImage(dataUrl: string, filename?: string): void {
  const link = document.createElement('a');
  link.href = dataUrl;
  link.download = filename || `对话截图-${Date.now()}.jpg`;
  link.click();
}