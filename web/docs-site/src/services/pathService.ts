import logger from './loggerService';
import { useAppStore } from '@/stores/app';
import localforage from 'localforage';

interface CatalogTree {
    [key: string]: CatalogTree | null;
}

const catalogStore = localforage.createInstance({
  name: "catalogTreeCache"
});

class PathService {
  private _catalogLoadingPromise: { [domain: string]: Promise<void> } = {};
  private _catalogTreeCache: { [domain: string]: CatalogTree } = {};

  public async resolveLogicalPath(logicalPath: string): Promise<string | null> {
    try {
        await this.ensureCatalogReady();
    } catch (error) {
        logger.error(`[resolveLogicalPath] 无法加载目录树，路径解析中止:`, error);
        return null;
    }

    const appStore = useAppStore();
    const currentDomain = appStore.currentDomain;
    if (!currentDomain) return null;

    const catalogTree = this._catalogTreeCache[currentDomain];
    if (!catalogTree) return null;

    const cleanPath = logicalPath.split('#')[0];
    const normalizedPath = cleanPath.trim().replace(/\\/g, '/');
    const pathParts = normalizedPath.split('/').filter(p => p);

    let currentNode: any = catalogTree;
    let isValid = true;
    for (const part of pathParts) {
        if (currentNode && typeof currentNode === 'object' && part in currentNode) {
            currentNode = currentNode[part];
        } else {
            isValid = false;
            break;
        }
    }
    if (isValid && currentNode === null) {
        return normalizedPath;
    }

    const justTheFileName = pathParts.length > 0 ? pathParts[pathParts.length - 1].toLowerCase() : null;
    if (!justTheFileName) return null;

    const traverse = (node: CatalogTree, currentPath: string): string | null => {
        for (const key in node) {
            const newPath = currentPath ? `${currentPath}/${key}` : key;
            if (node[key] === null) {
                if (key.toLowerCase() === justTheFileName || key.toLowerCase() === `${justTheFileName}.md`) {
                    return newPath;
                }
            } else if (typeof node[key] === 'object') {
                const found = traverse(node[key] as CatalogTree, newPath);
                if (found) return found;
            }
        }
        return null;
    };

    const foundPath = traverse(catalogTree, '');
    return foundPath;
  }

  public async ensureCatalogReady(): Promise<void> {
    const appStore = useAppStore();
    const currentDomain = appStore.currentDomain;
    if (!currentDomain) {
        throw new Error("当前域未设置，无法确保目录已就绪。");
    }

    if (this._catalogTreeCache[currentDomain]) {
      return;
    }

    if (this._catalogLoadingPromise[currentDomain] !== undefined) {
      await this._catalogLoadingPromise[currentDomain];
      return;
    }

    const loadPromise = (async () => {
      try {
        // 强制从网络获取以解决顽固的缓存问题。
        // localforage 缓存现在仅用作网络失败时的备用。
        const mapPath = `/domains/${currentDomain}/metadata/catalog.json?t=${new Date().getTime()}`;
        logger.log(`正在为域 '${currentDomain}' 加载目录树: ${mapPath}`);
        const response = await fetch(mapPath);
        if (!response.ok) {
          // 网络请求失败时，尝试从缓存加载作为备用
          const cachedTree = await catalogStore.getItem<CatalogTree>(currentDomain);
          if (cachedTree) {
            logger.warn(`网络请求失败，从 LocalForage 缓存加载了备用数据 for '${currentDomain}'.`);
            this._catalogTreeCache[currentDomain] = cachedTree;
            return; // 从缓存加载后返回
          }
          throw new Error(`HTTP 错误! status: ${response.status}`);
        }
        const tree = await response.json();

        this._catalogTreeCache[currentDomain] = tree;
        await catalogStore.setItem(currentDomain, tree); // 更新缓存

        logger.log(`目录树 for '${currentDomain}' 加载并缓存成功。`);
      } catch (error) {
        logger.error(`加载目录树失败 for '${currentDomain}':`, error);
        
        // 在捕获到错误后，也尝试从缓存加载作为最终备用
        const cachedTree = await catalogStore.getItem<CatalogTree>(currentDomain);
        if (cachedTree) {
            logger.warn(`网络请求和解析失败，从 LocalForage 缓存加载了最终备用数据 for '${currentDomain}'.`);
            this._catalogTreeCache[currentDomain] = cachedTree;
            return;
        }

        throw error;
      } finally {
        delete this._catalogLoadingPromise[currentDomain];
      }
    })();

    this._catalogLoadingPromise[currentDomain] = loadPromise;
    await loadPromise;
  }

  public async listDocs(path: string = '/'): Promise<string> {
    logger.log(`执行目录列表...`, { path });
    const appStore = useAppStore();
    const currentDomain = appStore.currentDomain;
    
    if (!currentDomain) {
        return "错误：当前域未设置。";
    }

    try {
      await this.ensureCatalogReady();
      const catalogTree = this._catalogTreeCache[currentDomain];
      const pathParts = path.trim().replace(/^\/|\/$/g, '').split('/').filter(p => p);
      
      let currentLevel: any = catalogTree;
      for (const part of pathParts) {
        if (currentLevel && typeof currentLevel === 'object' && part in currentLevel) {
          currentLevel = currentLevel[part];
        } else {
          return `错误：路径 '${path}' 不存在。`;
        }
      }

      if (typeof currentLevel !== 'object' || currentLevel === null) {
        return `错误：路径 '${path}' 不是一个目录。`;
      }
      
      const normalizedBasePath = path.trim().replace(/\/$/, '');
      const finalPath = normalizedBasePath === '/' ? '' : normalizedBasePath;

      const results = Object.keys(currentLevel).map(key => {
        const fullPath = [finalPath, key].filter(Boolean).join('/');
        const type = currentLevel[key] === null ? 'file' : 'directory';
        return { path: fullPath, type: type };
      });

      logger.log(`目录列表成功: ${path}`, { count: results.length });
      return JSON.stringify(results, null, 2);

    } catch (error: any) {
      logger.error(`列出目录时失败: ${path}`, error);
      return `错误：无法列出目录 '${path}': ${error.message}`;
    }
  }
}

const pathService = new PathService();
export default pathService;