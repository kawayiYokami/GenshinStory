import json
import logging
import os
import pickle
import lzma
from pathlib import Path
from typing import List, Dict, Any, Optional

class DataLoader:
    """
    负责加载、解析和缓存所有原始数据文件。
    采用单例模式，确保数据只被读取一次。
    """
    _instance = None
    _cache = {}
    
    # 默认数据根目录，相对于项目根目录
    _DEFAULT_ROOT = Path(__file__).parent.parent / "AnimeGameData"

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, root_path: Optional[str] = None, cache_path: Optional[str] = "game_data.cache"):
        """
        初始化 DataLoader。
        :param root_path: (可选) 数据源的根目录路径。
        :param cache_path: (可选) 二进制缓存文件的路径。
        """
        if hasattr(self, '_initialized'):
            # 如果实例已初始化，仅在提供了新的 root_path 时更新它
            if root_path:
                self.set_data_root(root_path)
            return

        # --- 关键修复：无论如何，总是先设置数据根目录 ---
        effective_path = Path(root_path) if root_path else self._DEFAULT_ROOT
        self.set_data_root(str(effective_path))
        
        self._talk_id_map: Optional[Dict[int, str]] = None
        self._text_map_cache: Optional[Dict[str, str]] = None
        self._directory_cache: Dict[str, List[Any]] = {}  # 新增：缓存目录遍历结果
        
        # 优先从缓存加载
        if cache_path and self.load_from_cache(cache_path):
            logging.info(f"已成功从缓存 '{cache_path}' 加载数据。")
        else:
            # 如果缓存加载失败或未提供，则进行常规初始化
            logging.info("未找到有效缓存或未提供缓存路径，将从原始文件加载。")
        
        self._initialized = True
    
    def set_data_root(self, root_path: str):
        """设置数据源的根目录。"""
        self._data_root = root_path

    def get_data_root(self) -> str:
        """获取数据源的根目录。"""
        return self._data_root

    def get_json(self, relative_path: str) -> dict:
        """
        根据相对于数据根目录的路径获取JSON数据，优先从缓存读取。
        """
        # 使用 os.path.normpath 确保路径在不同系统上的一致性
        normalized_path = os.path.normpath(relative_path)

        if normalized_path in self._cache:
            return self._cache[normalized_path]
        
        if not self._data_root:
            raise ValueError("Data root path is not set. Please call set_data_root() first.")

        full_path = os.path.join(self._data_root, normalized_path)

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._cache[normalized_path] = data
                return data
        except FileNotFoundError:
            print(f"Error: File not found at {full_path}")
            return None
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {full_path}")
            return None

    def get_all_json_files_in_dir(self, relative_dir: str, yield_filename: bool = False) -> List[Any]:
        """
        加载指定目录下的所有JSON文件。
        :param relative_dir: The directory to search in, relative to the data root.
        :param yield_filename: If True, returns a list of (filename, data) tuples. Otherwise, returns a list of data dicts.
        :return: A list of JSON data contents or (filename, data) tuples.
        """
        if not self._data_root:
            raise ValueError("Data root path is not set. Please call set_data_root() first.")

        # 构造缓存键
        cache_key = f"{relative_dir}::{yield_filename}"
        
        # 优先从缓存读取
        if cache_key in self._directory_cache:
            return self._directory_cache[cache_key]

        full_dir_path = Path(self._data_root) / relative_dir
        if not full_dir_path.is_dir():
            print(f"Error: Directory not found at {full_dir_path}")
            # 即使是空结果也要缓存，避免重复的文件系统访问
            self._directory_cache[cache_key] = []
            return []
        
        results = []
        # 修正：使用 rglob 进行递归搜索，以确保能找到所有子目录中的JSON文件。
        # 旧的 builder.py 使用的是 rglob，这是正确的行为。
        for file_path in full_dir_path.rglob('*.json'):
            # 计算相对于数据根目录的路径，以便使用 get_json 的缓存
            relative_file_path = file_path.relative_to(self._data_root).as_posix()
            data = self.get_json(relative_file_path)
            if data:
                if yield_filename:
                    results.append((file_path.name, data))
                else:
                    results.append(data)
        
        # 缓存结果
        self._directory_cache[cache_key] = results
        return results

    def get_all_file_paths_in_folder(self, relative_dir: str, name_contains: str = "") -> List[str]:
        """
        获取指定目录下的所有文件路径，并可选择根据文件名进行过滤。
        使用缓存机制，避免重复的文件系统访问。
        """
        if not self._data_root:
            raise ValueError("Data root path is not set. Please call set_data_root() first.")

        # 构造缓存键
        cache_key = f"file_paths::{relative_dir}::{name_contains}"
        
        # 优先从缓存读取
        if cache_key in self._directory_cache:
            return self._directory_cache[cache_key]

        full_dir_path = Path(self._data_root) / relative_dir
        if not full_dir_path.is_dir():
            print(f"Error: Directory not found at {full_dir_path}")
            # 即使是空结果也要缓存，避免重复的文件系统访问
            self._directory_cache[cache_key] = []
            return []
        
        all_paths = []
        for file_path in full_dir_path.rglob('*'): # rglob for recursive search
            if file_path.is_file() and (not name_contains or name_contains in file_path.name):
                # 存储相对于数据根目录的相对路径，而不是绝对路径
                relative_path = file_path.relative_to(self._data_root).as_posix()
                all_paths.append(relative_path)
        
        # 缓存结果
        self._directory_cache[cache_key] = all_paths
        return all_paths

    def get_file_name(self, full_path: str, with_extension: bool = True) -> str:
        """从完整路径中获取文件名。"""
        if with_extension:
            return os.path.basename(full_path)
        else:
            return Path(full_path).stem

    def get_text_file(self, relative_path: str) -> Optional[str]:
        """根据相对于数据根目录的路径，读取一个纯文本文件的内容。"""
        normalized_path = os.path.normpath(relative_path)
        
        # 复用 _cache 来缓存文本文件
        if normalized_path in self._cache:
            return self._cache[normalized_path]

        if not self._data_root:
            raise ValueError("Data root path is not set. Please call set_data_root() first.")

        full_path = os.path.join(self._data_root, normalized_path)

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
                self._cache[normalized_path] = content
                return content
        except FileNotFoundError:
            print(f"Error: Text file not found at {full_path}")
            return None

    def get_text_map(self, language: str = "CHS") -> Dict[str, str]:
        """
        加载并缓存指定语言的TextMap文件。
        TextMap文件本身就是一个 hash -> text 的映射。
        :param language: 语言代码 (例如 "CHS", "EN")。
        :return: 一个包含 {hash: text} 的字典。
        """
        if self._text_map_cache is None:
            # Corrected path based on project structure
            relative_path = f"TextMap/TextMap{language}.json"
            logging.info(f"正在从 {relative_path} 加载 TextMap...")
            data = self.get_json(relative_path)
            if data:
                # The keys in TextMap are string representations of hashes
                self._text_map_cache = data
            else:
                logging.error(f"TextMap 文件加载失败: {relative_path}")
                self._text_map_cache = {}  # Set to empty dict to avoid re-attempts
        
        return self._text_map_cache

    def get_talk_id_map(self) -> Dict[int, str]:
        """
        构建并缓存 TalkID 到文件相对路径的映射。
        这个过程只在第一次调用时执行一次。
        :return: 一个包含 {talk_id: relative_path} 的字典。
        """
        if self._talk_id_map is None:
            logging.info("TalkID -> Filename 映射不存在，正在构建...")
            talk_map = {}
            talks_dir = Path(self._data_root) / "BinOutput" / "Talk"
            
            if not talks_dir.is_dir():
                logging.error(f"Talks 目录不存在: {talks_dir}")
                self._talk_id_map = {}
                return self._talk_id_map

            for file_path in talks_dir.rglob('*.json'):
                try:
                    with open(file_path, 'rb') as f:
                        data = json.load(f)

                    if not isinstance(data, dict):
                        continue
                    
                    talk_id = data.get("talkId")
                    if talk_id:
                        # 关键修正：存储相对于 "BinOutput/Talk" 目录的相对路径
                        relative_path = file_path.relative_to(talks_dir).as_posix()
                        talk_map[talk_id] = relative_path
                except (json.JSONDecodeError, ValueError) as e:
                    logging.warning(f"处理文件 {file_path.name} 时出错: {e}")
            
            self._talk_id_map = talk_map
            logging.info(f"TalkID 映射构建完成，共找到 {len(talk_map)} 个条目。")

        return self._talk_id_map

    def save_cache(self, file_path: str):
        """
        将当前的内部缓存保存到二进制文件中。
        """
        cache_data = {
            'file_cache': self._cache,
            'talk_id_map': self.get_talk_id_map(), # Ensure it's generated
            'text_map_cache': self.get_text_map(), # Ensure it's generated
            'directory_cache': self._directory_cache # New: 目录遍历结果缓存
        }
        
        try:
            with lzma.open(file_path, 'wb') as f:
                pickle.dump(cache_data, f)
            logging.info(f"LZMA压缩缓存已成功保存到: {file_path}")
        except Exception as e:
            logging.error(f"保存LZMA压缩缓存到 {file_path} 时发生错误: {e}")

    def load_from_cache(self, file_path: str) -> bool:
        """
        从二进制文件中加载缓存。
        :return: 如果加载成功则返回 True，否则返回 False。
        """
        if not os.path.exists(file_path):
            return False
            
        try:
            with lzma.open(file_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            self._cache = cache_data.get('file_cache', {})
            self._talk_id_map = cache_data.get('talk_id_map', {})
            self._text_map_cache = cache_data.get('text_map_cache', {})
            self._directory_cache = cache_data.get('directory_cache', {})

            # Mark derivative caches as loaded
            if not self._talk_id_map: self._talk_id_map = {}
            if not self._text_map_cache: self._text_map_cache = {}

            # Important: Check if cache is valid. A simple check is enough.
            if not self._cache and not self._text_map_cache:
                 logging.warning("缓存文件为空或无效，将忽略。")
                 return False

            return True
        except Exception as e:
            logging.error(f"从 {file_path} 加载缓存时发生错误: {e}")
            return False