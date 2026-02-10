/**
 * 路径处理工具函数
 */

/**
 * 从完整路径中提取文件名（最后一个 / 到 .md 之间的部分）
 * @param fullPath 完整路径，如 "任务/传说任务/金狼之章-第一幕-沉沙归寂-5286.md"
 * @returns 文件名，如 "金狼之章-第一幕-沉沙归寂-5286"
 */
export function extractFileName(fullPath: string): string {
  if (!fullPath || typeof fullPath !== 'string') {
    return fullPath;
  }

  // 查找最后一个 / 的位置
  const lastSlashIndex = fullPath.lastIndexOf('/');

  // 提取从最后一个 / 之后到 .md 之前的部分
  let fileName = lastSlashIndex >= 0 ? fullPath.substring(lastSlashIndex + 1) : fullPath;

  // 移除 .md 扩展名
  if (fileName.endsWith('.md')) {
    fileName = fileName.slice(0, -3);
  }

  return fileName;
}