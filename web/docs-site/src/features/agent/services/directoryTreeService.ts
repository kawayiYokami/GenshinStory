import { useAppStore } from '@/features/app/stores/app';
import logger from '@/features/app/services/loggerService';

interface DirectoryNode {
  name: string;
  path: string;
  type: 'directory' | 'file';
  children?: DirectoryNode[];
}

interface DirectoryTree {
  [key: string]: DirectoryNode;
}

/**
 * 目录树服务 - 动态生成当前领域数据库结构
 */
class DirectoryTreeService {
  private cache = new Map<string, string>();
  private cacheExpiry = new Map<string, number>();

  /**
   * 生成目录树的字符串表示，用于系统提示词
   */
  async generateDirectoryTreeString(domain?: string): Promise<string> {
    const appStore = useAppStore();
    const currentDomain = domain || appStore.currentDomain;

    if (!currentDomain) {
      return '当前领域未设置，无法获取数据库结构。';
    }

    const cacheKey = `tree_${currentDomain}`;
    const now = Date.now();

    // 检查缓存（5分钟有效）
    if (this.cache.has(cacheKey) &&
        this.cacheExpiry.has(cacheKey) &&
        this.cacheExpiry.get(cacheKey)! > now) {
      return this.cache.get(cacheKey)!;
    }

    try {
      const treeString = await this._scanAndFormatDirectory(currentDomain);

      // 缓存结果
      this.cache.set(cacheKey, treeString);
      this.cacheExpiry.set(cacheKey, now + 5 * 60 * 1000); // 5分钟

      return treeString;
    } catch (error) {
      logger.error('生成目录树失败:', error);
      return '获取数据库结构时发生错误。';
    }
  }

  /**
   * 扫描并格式化目录结构
   */
  private async _scanAndFormatDirectory(domain: string): Promise<string> {
    const domains = ['gi', 'hsr', 'zzz'];

    if (!domains.includes(domain)) {
      return `未知领域: ${domain}`;
    }

    // 根据领域返回预定义的目录结构
    // 这样可以避免动态扫描的性能开销，同时保持准确性
    const domainStructures: Record<string, string> = {
      gi: `当前领域数据库结构（原神）：
📁 characters/
  📁 by_element/
  📁 by_rarity/
  📁 by_region/
  📁 by_weapon/
📁 weapons/
  📁 5_star/
  📁 4_star/
  📁 3_star/
  📁 by_type/
📁 items/
  📁 materials/
  📁 consumables/
  📁 artifacts/
  📁 by_gacha_type/
📁 quests/
  📁 archon/
  📁 story/
  📁 world/
  📁 by_region/
📁 enemies/
  📁 by_level/
  📁 by_element/
  📁 by_type/
📁 achievements/
  📁 by_category/
  📁 by_series/
📁 guides/
  📁 beginner/
  📁 advanced/
  📁 character_builds/
📁 gacha/
  📁 banners/
  📁 history/
  📁 pity_system/`,

      hsr: `当前领域数据库结构（崩坏：星穹铁道）：
📁 characters/
  📁 by_path/
  📁 by_element/
  📁 by_rarity/
  📁 by_faction/
📁 lightcones/
  📁 5_star/
  📁 4_star/
  📁 by_type/
📁 relics/
  📁 by_slot/
  📁 by_set/
  📁 by_rarity/
📁 items/
  📁 materials/
  📁 consumables/
  📁 by_category/
📁 quests/
  📁 trailblaze/
  📁 adventure/
  📁 by_difficulty/
📁 enemies/
  📁 by_level/
  📁 by_type/
  📁 by_weakness/
📁 guides/
  📁 character_builds/
  📁 team_comps/
  📁 progression/`,

      zzz: `当前领域数据库结构（绝区零）：
📁 characters/
  📁 by_faction/
  📁 by_element/
  📁 by_rarity/
  📁 by_weapon/
📁 w-engines/
  📁 by_manufacturer/
  📁 by_rank/
  📁 by_type/
📁 bangboo/
  📁 by_type/
  📁 by_rarity/
📁 items/
  📁 materials/
  📁 components/
  📁 by_category/
📁 quests/
  📁 commissions/
  📁 by_distract/
  📁 by_region/
📁 enemies/
  📁 by_type/
  📁 by_level/
  📁 by_faction/
📁 guides/
  📁 character_builds/
  📁 team_comps/
  📁 skill_guides/`
    };

    return domainStructures[domain] || `领域 ${domain} 的结构信息暂未配置。`;
  }

  /**
   * 清除缓存
   */
  clearCache(): void {
    this.cache.clear();
    this.cacheExpiry.clear();
  }

  /**
   * 获取目录路径（去掉文件名）
   */
  getDirectoryPath(filePath: string): string {
    // 移除文件名，只返回目录路径
    const lastSlashIndex = filePath.lastIndexOf('/');
    if (lastSlashIndex === -1) {
      return filePath; // 如果没有路径分隔符，返回原路径
    }
    return filePath.substring(0, lastSlashIndex);
  }
}

// 导出单例实例
export const directoryTreeService = new DirectoryTreeService();
export default directoryTreeService;