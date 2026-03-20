/**
 * @fileoverview 表情服务
 * @description 管理表情包资源，提供随机获取表情图片的功能
 *
 * 角色索引文件：/public/meme/meme_index.json
 * 描述文件：/public/meme/memes_data.json
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
  [cacheKey: string]: string[];
}

interface MemeIndexData {
  version: number;
  generatedAt: string;
  emoteNames?: string[];
  default?: Record<string, string[]>;
  agents?: Record<string, Record<string, string[]>>;
}

class EmoteService {
  private cache: EmoteCache = {};
  private initialized = false;
  private initPromise: Promise<void> | null = null;
  private indexData: MemeIndexData | null = null;

  /**
   * 初始化表情服务
   * 预加载索引文件并缓存默认表情列表
   */
  public async initialize(): Promise<void> {
    if (this.initialized) return;
    if (this.initPromise) return this.initPromise;

    this.initPromise = this.loadMemeIndex();
    await this.initPromise;
    this.initialized = true;
  }

  private buildCacheKey(emoteName: string, memePackPath?: string): string {
    const normalizedPack = memePackPath?.replace(/\/+$/, '') || '__default__';
    return `${normalizedPack}|${emoteName}`;
  }

  private resolveRoleIdFromMemePack(memePackPath?: string): string | null {
    if (!memePackPath) return null;
    const trimmed = memePackPath.replace(/\/+$/, '');
    const parts = trimmed.split('/').filter(Boolean);
    return parts.length > 0 ? parts[parts.length - 1] : null;
  }

  /**
   * 加载 meme 索引文件
   */
  private async loadMemeIndex(): Promise<void> {
    try {
      const response = await fetch('/meme/meme_index.json');
      if (!response.ok) {
        throw new Error(`Failed to load meme_index.json: ${response.status}`);
      }

      const indexData = await response.json() as MemeIndexData;
      this.indexData = indexData;

      // 预填充默认缓存，确保同步渲染可用
      const defaultMap = indexData.default || {};
      for (const emoteName of Object.keys(defaultMap)) {
        const files = defaultMap[emoteName];
        if (Array.isArray(files) && files.length > 0) {
          const cacheKey = this.buildCacheKey(emoteName);
          this.cache[cacheKey] = files;
        }
      }

      logger.log(`[EmoteService] 已加载表情索引，默认表情种类: ${Object.keys(defaultMap).length}`);
    } catch (e) {
      logger.error('[EmoteService] 加载表情索引失败:', e);
      this.indexData = null;
    }
  }

  private getFilesFromIndex(emoteName: string, memePackPath?: string): string[] {
    const indexData = this.indexData;
    if (!indexData) return [];

    if (memePackPath) {
      const roleId = this.resolveRoleIdFromMemePack(memePackPath);
      if (roleId) {
        const roleFiles = indexData.agents?.[roleId]?.[emoteName];
        if (Array.isArray(roleFiles) && roleFiles.length > 0) {
          return roleFiles;
        }
      }
      // 指定了角色专属表情包时，不回退到默认公共表情包
      return [];
    }

    const defaultFiles = indexData.default?.[emoteName];
    if (Array.isArray(defaultFiles) && defaultFiles.length > 0) {
      return defaultFiles;
    }

    return [];
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
  public async getRandomEmote(name: string, memePackPath?: string): Promise<string | null> {
    if (!this.isValidEmote(name)) {
      return null;
    }

    if (!this.initialized) {
      await this.initialize();
    }

    const cacheKey = this.buildCacheKey(name, memePackPath);
    let files = this.cache[cacheKey];

    if (!files || files.length === 0) {
      files = this.getFilesFromIndex(name, memePackPath);
      if (files.length > 0) {
        this.cache[cacheKey] = files;
      }
    }

    if (!files || files.length === 0) {
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
  public getRandomEmoteSync(name: string, seed?: number, memePackPath?: string): string | null {
    if (!this.isValidEmote(name)) {
      return null;
    }

    const cacheKey = this.buildCacheKey(name, memePackPath);
    let files = this.cache[cacheKey];

    // 若角色缓存不存在，尝试从索引读取并缓存
    if ((!files || files.length === 0) && this.indexData) {
      files = this.getFilesFromIndex(name, memePackPath);
      if (files.length > 0) {
        this.cache[cacheKey] = files;
      }
    }

    // 兜底读取默认缓存（初始化阶段已预填充）
    if (!files || files.length === 0) {
      const defaultFiles = this.cache[this.buildCacheKey(name)];
      if (defaultFiles && defaultFiles.length > 0) {
        files = defaultFiles;
      }
    }

    if (!files || files.length === 0) {
      return null;
    }

    if (seed !== undefined) {
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
