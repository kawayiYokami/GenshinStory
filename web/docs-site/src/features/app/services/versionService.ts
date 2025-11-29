/**
 * @fileoverview 版本检查服务模块
 * @description 负责检查服务器数据版本，管理本地缓存清理
 * @author yokami
 */
import localforage from 'localforage';
import { sessionsStore, lastUsedRolesStore } from '@/features/agent/stores/persistence';

// 重新创建一个指向相同数据库的实例
const catalogStore = localforage.createInstance({ name: "catalogTreeCache" });

const DATA_VERSION_KEY = 'dataVersion'; // 定义用于 localStorage 的键，避免魔法字符串

/**
 * 清除数据相关的本地缓存，但保留用户聊天记录
 * @description 只清除目录树缓存，保留会话和角色信息
 * @return {Promise<void[]>} 当所有清除操作完成时解析的 Promise
 */
async function clearDataCaches(): Promise<void[]> {
  console.log("检测到新数据版本，正在清除数据缓存（保留聊天记录）...");
  const clearPromises = [
    // 只清除数据相关缓存，保留用户数据
    catalogStore.clear()
    // sessionsStore 和 lastUsedRolesStore 不再清除
  ];
  return Promise.all(clearPromises);
}

/**
 * 检查服务器数据版本，并在必要时清除本地缓存
 * @description 比较服务器版本和本地版本，如果不匹配则清除数据缓存（保留聊天记录）
 * 该函数应在应用初始化时调用
 * @return {Promise<void>}
 * @throws {Error} 当版本检查失败时抛出异常
 */
export async function checkVersion(): Promise<void> {
  try {
    // 1. 使用时间戳绕过浏览器缓存，获取服务器版本
    const response = await fetch(`/version.json?t=${new Date().getTime()}`);
    if (!response.ok) {
      throw new Error('无法获取版本文件');
    }
    const serverConfig = await response.json();
    const serverVersion = serverConfig.version;

    // 2. 获取本地存储的版本
    const localVersion = localStorage.getItem(DATA_VERSION_KEY);

    // 3. 比较版本并执行操作
    if (serverVersion !== localVersion) {
      console.log(`版本不匹配。服务器版本: ${serverVersion}, 本地版本: ${localVersion}`);
      await clearDataCaches(); // 改为只清除数据缓存，保留聊天记录
      // 4. 更新本地版本号
      localStorage.setItem(DATA_VERSION_KEY, serverVersion);
      console.log("缓存清除完毕，本地版本已更新至", serverVersion);
    } else {
      console.log("本地数据已是最新版本，无需更新。");
    }
  } catch (error) {
    console.error("版本检查失败，将继续使用本地缓存:", error);
  }
}