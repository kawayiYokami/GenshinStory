/**
 * @fileoverview 表情服务
 * @description 管理表情包资源，提供随机获取表情图片的功能
 *
 * 表情目录结构：/public/meme/memes/{emoteName}/表情*.png
 * 配置文件：/public/meme/memes_data.json
 */

import logger from '@/features/app/services/loggerService';

// 有效的表情名称列表
const VALID_EMOTES = [
  'angry', 'happy', 'sad', 'surprised', 'confused',
  'color', 'cpu', 'fool', 'givemoney', 'like',
  'see', 'shy', 'work', 'reply', 'meow',
  'baka', 'morning', 'sleep', 'sigh'
] as const;

export type EmoteName = typeof VALID_EMOTES[number];

interface EmoteCache {
  [emoteName: string]: string[];
}

class EmoteService {
  private cache: EmoteCache = {};
  private initialized = false;
  private initPromise: Promise<void> | null = null;

  /**
   * 初始化表情服务
   * 预加载所有表情列表
   */
  public async initialize(): Promise<void> {
    if (this.initialized) return;
    if (this.initPromise) return this.initPromise;

    this.initPromise = this.loadAllEmotes();
    await this.initPromise;
    this.initialized = true;
  }

  /**
   * 加载所有表情列表
   */
  private async loadAllEmotes(): Promise<void> {
    try {
      // 并行加载所有表情目录
      const loadPromises = VALID_EMOTES.map(async (emoteName) => {
        try {
          const files = await this.scanEmoteDirectory(emoteName);
          if (files.length > 0) {
            this.cache[emoteName] = files;
          }
        } catch (e) {
          logger.warn(`[EmoteService] 加载表情 ${emoteName} 失败:`, e);
        }
      });

      await Promise.all(loadPromises);
      logger.log(`[EmoteService] 已加载 ${Object.keys(this.cache).length} 种表情`);
    } catch (e) {
      logger.error('[EmoteService] 初始化失败:', e);
    }
  }

  /**
   * 扫描表情目录获取图片列表
   * 注意：浏览器环境无法直接扫描目录，使用预定义的文件列表
   */
  private async scanEmoteDirectory(emoteName: string): Promise<string[]> {
    // 浏览器环境：尝试加载目录索引
    // 由于无法直接扫描目录，我们使用一个简单的策略：
    // 尝试加载已知的文件名模式

    const files: string[] = [];
    const basePath = `/meme/memes/${emoteName}/`;

    // 尝试加载常见的文件名模式
    // 根据实际的文件命名规则（表情1_xxx.png, 表情2_xxx.png 等）
    for (let i = 1; i <= 200; i++) {
      for (let j = 1; j <= 5; j++) {
        const fileName = `表情${j}_${i}.png`;
        const filePath = basePath + fileName;

        // 检查文件是否存在（通过 HEAD 请求）
        try {
          const response = await fetch(filePath, { method: 'HEAD' });
          if (response.ok) {
            files.push(filePath);
          }
        } catch {
          // 文件不存在，继续
        }
      }
    }

    // 如果扫描太慢，使用硬编码的文件列表作为 fallback
    if (files.length === 0) {
      return this.getHardcodedFiles(emoteName);
    }

    return files;
  }

  /**
   * 获取硬编码的表情文件列表（作为 fallback）
   * 基于实际存在的文件
   */
  private getHardcodedFiles(emoteName: string): string[] {
    const basePath = `/meme/memes/${emoteName}/`;

    // 基于观察到的实际文件模式生成列表
    const filePatterns: Record<string, number[]> = {
      'happy': [5, 6, 13, 18, 25, 30, 44, 45, 80, 85, 98, 99, 114, 131, 136, 139, 141, 143, 174, 175],
      'sad': [23, 34],
      'angry': [46, 89],
      'surprised': [27, 33, 42, 72, 133],
      'confused': [17, 69, 70, 90, 117],
      'shy': [29, 41, 43, 57, 62, 93],
      'meow': [14, 24, 28, 66, 67, 92, 100, 130, 142, 170, 171, 172],
      'baka': [19, 35, 47, 116, 121, 137, 144, 145],
      'sigh': [20, 26, 31, 32, 58, 65, 71, 135, 162],
      'cpu': [3, 79, 115, 118, 134],
      'givemoney': [4, 7, 8, 15, 16, 36],
      'like': [94, 97],
      'work': [22, 96, 138, 163],
      'sleep': [60, 68, 78, 91, 95],
      'see': [21, 48, 77, 140],
      'reply': [113, 122, 173],
      'fool': [59],
      'color': [],
      'morning': [],
    };

    const indices = filePatterns[emoteName] || [];
    return indices.map(i => {
      // 根据索引范围确定表情组
      let group = 1;
      if (i >= 41 && i < 81) group = 2;
      else if (i >= 81 && i < 121) group = 3;
      else if (i >= 121 && i < 161) group = 4;
      else if (i >= 161) group = 5;

      return `${basePath}表情${group}_${i}.png`;
    });
  }

  /**
   * 检查是否是有效的表情名称
   */
  public isValidEmote(name: string): boolean {
    return VALID_EMOTES.includes(name as EmoteName);
  }

  /**
   * 获取随机表情图片路径（异步）
   */
  public async getRandomEmote(name: string): Promise<string | null> {
    if (!this.isValidEmote(name)) {
      return null;
    }

    // 确保已初始化
    if (!this.initialized) {
      await this.initialize();
    }

    const files = this.cache[name];
    if (!files || files.length === 0) {
      // 尝试使用硬编码的文件列表
      const hardcoded = this.getHardcodedFiles(name);
      if (hardcoded.length > 0) {
        this.cache[name] = hardcoded;
        return hardcoded[Math.floor(Math.random() * hardcoded.length)];
      }
      return null;
    }

    return files[Math.floor(Math.random() * files.length)];
  }

  /**
   * 简单的种子随机数生成器
   * 使用 mulberry32 算法，确保相同种子产生相同的随机序列
   */
  private seededRandom(seed: number): number {
    let t = seed + 0x6D2B79F5;
    t = Math.imul(t ^ t >>> 15, t | 1);
    t ^= t + Math.imul(t ^ t >>> 7, t | 61);
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  }

  /**
   * 获取随机表情图片路径（同步）
   * 用于流式解析场景
   * @param name 表情名称
   * @param seed 可选的随机种子，用于确定性选择（流式传输时保持一致）
   */
  public getRandomEmoteSync(name: string, seed?: number): string | null {
    if (!this.isValidEmote(name)) {
      return null;
    }

    // 如果没有缓存，使用硬编码的文件列表
    let files = this.cache[name];
    if (!files || files.length === 0) {
      files = this.getHardcodedFiles(name);
      if (files.length > 0) {
        this.cache[name] = files;
      }
    }

    if (!files || files.length === 0) {
      return null;
    }

    // 如果提供了种子，使用确定性随机；否则使用普通随机
    if (seed !== undefined) {
      // 将表情名称的哈希值与种子组合，确保同一消息中不同表情也有不同但确定的结果
      const nameHash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
      const combinedSeed = seed + nameHash;
      const randomValue = this.seededRandom(combinedSeed);
      return files[Math.floor(randomValue * files.length)];
    }

    return files[Math.floor(Math.random() * files.length)];
  }

  /**
   * 获取表情描述（用于提示词）
   */
  public async getEmoteDescriptions(): Promise<Record<string, string>> {
    try {
      const response = await fetch('/meme/memes_data.json');
      if (!response.ok) {
        throw new Error('Failed to load memes_data.json');
      }
      return await response.json();
    } catch (e) {
      logger.error('[EmoteService] 加载表情描述失败:', e);
      return {};
    }
  }

  /**
   * 获取所有有效表情名称
   */
  public getValidEmotes(): readonly string[] {
    return VALID_EMOTES;
  }
}

export const emoteService = new EmoteService();
export default emoteService;
