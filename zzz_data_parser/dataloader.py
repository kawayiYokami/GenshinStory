import json
import logging
import os
import gzip
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
import collections
from typing import NamedTuple

class SearchResult(NamedTuple):
    id: Any
    name: str
    type: str
    match_source: str

# Import the new interpreter
# Import the new text transformer
from .utils.text_transformer import transform_text
from .interpreters.session_interpreter import SessionInterpreter, Session

class ZZZDataLoader:
    """
    负责加载、解析和缓存所有绝区零的原始数据文件。
    """
    _instance = None
    _cache: Dict[str, Any] = {}
    _search_index: Dict[str, List[Any]] = collections.defaultdict(list)


    # 数据根目录
    _DEFAULT_ROOT = Path(__file__).parent.parent / "ZenlessData"

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, root_path: Optional[str] = None, gender: str = 'M', player_name: str = '哲'):
        if hasattr(self, '_initialized'):
            if root_path:
                self.set_data_root(root_path)
            return

        effective_path = Path(root_path) if root_path else self._DEFAULT_ROOT
        self.set_data_root(str(effective_path))

        self.gender = gender
        self.player_name = player_name
        self._text_map_cache: Optional[Dict[str, str]] = None
        self._initialized = True

    def set_data_root(self, root_path: str):
        """设置数据源的根目录。"""
        self._data_root = root_path

    def get_data_root(self) -> str:
        """获取数据源的根目录。"""
        return self._data_root

    def get_json(self, relative_path: str) -> Optional[Dict[str, Any]]:
        """
        根据相对于数据根目录的路径获取JSON数据，优先从缓存读取。
        """
        normalized_path = relative_path.replace('\\', '/')

        if normalized_path in self._cache:
            return self._cache[normalized_path]

        if not self._data_root:
            raise ValueError("Data root path is not set.")

        full_path = os.path.join(self._data_root, normalized_path)

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._cache[normalized_path] = data
                return data
        except FileNotFoundError:
            logging.warning(f"JSON file not found at: {full_path}")
            return None
        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON from: {full_path}")
            return None

    def clear_cache(self):
        """Clear the text map cache."""
        self._text_map_cache = None
        if 'text_map' in self._cache:
            del self._cache['text_map']

    def clear_search_index(self) -> None:
        """Clear the search index."""
        self._search_index.clear()

    def get_text_map(self) -> Dict[str, str]:
        """
        加载并合并绝区零的两个TextMap文件。
        - TextMapTemplateTb.json (基础)
        - TextMapOverwriteTemplateTb.json (覆盖)
        """
        # First, check if it's in the general cache
        if 'text_map' in self._cache:
            return self._cache['text_map']

        if self._text_map_cache is None:
            logging.info("Loading and cleaning ZZZ TextMaps...")

            # get_json 直接返回我们需要的字典
            base_text_map = self.get_json("TextMap/TextMapTemplateTb.json") or {}
            overwrite_text_map = self.get_json("TextMap/TextMapOverwriteTemplateTb.json") or {}

            # 合并两个字典，overwrite_text_map 中的键会覆盖 base_text_map 中的同名键
            merged_map = {**base_text_map, **overwrite_text_map}

            # --- 新增的清洗逻辑 ---
            cleaned_map = {}
            count = 0
            for key, value in merged_map.items():
                # 对每个文本值应用 transform_text
                cleaned_text, _ = transform_text(value, self.gender, self.player_name)
                cleaned_map[key] = cleaned_text
                count += 1
                # Print a message every 50000 entries to show progress
                if count % 50000 == 0:
                    logging.info(f"Cleaned {count} entries...")
            logging.info(f"Finished cleaning {count} entries.")
            # --- 清洗逻辑结束 ---

            self._text_map_cache = cleaned_map # 缓存清洗后的 map
            self._cache['text_map'] = cleaned_map # Also cache in the general cache
            logging.info(f"ZZZ TextMaps loaded and cleaned. Total entries: {len(cleaned_map)}")

        return self._text_map_cache

    def get_partner_config(self) -> Optional[Dict[str, Any]]:
        """
        加载并返回伙伴配置数据，以ID为键进行索引。
        """
        if 'partner_config' not in self._cache:
            logging.info("Loading Partner Config...")
            raw_config = self.get_json("FileCfg/PartnerConfigTemplateTb.json")
            if not raw_config or 'PDHBFPILAJD' not in raw_config:
                logging.error("Failed to load or parse PartnerConfigTemplateTb.json")
                return None

            # 预处理：构建以ID为键的配置字典
            processed_config = {}
            for partner_data in raw_config['PDHBFPILAJD']:
                partner_id = str(partner_data['DDFGCLKJPJC'])
                processed_config[partner_id] = {
                    'id': partner_id,
                    'name_key': partner_data['CNFOJMDENMK'],
                    'outlook_desc_key': partner_data['GNJCDLGHDDF'],
                    'profile_desc_key': partner_data['HEIAFGBBAAE'],
                    'impression_f_key': partner_data['MBFJNKPEACB'],
                    'impression_m_key': partner_data['DIDBDGDIJFP'],
                    'birthday_key': partner_data['FELBLONCIDJ'],
                    'true_name': partner_data['NMDLENGDAKD'],
                    'camp_ids': partner_data['CLKJKCGPCAN'],
                    'camp_key': partner_data.get('NPMBJEBPMIK', ''),
                    'gender': partner_data.get('EEMFLLFIIKL', 0),
                    'icon_path': partner_data.get('PCOENAKPIMP', ''),
                    'gacha_splash_path': partner_data.get('MNHJEPLGCKC', '')
                }
            self._cache['partner_config'] = processed_config
            logging.info(f"Partner Config loaded for {len(processed_config)} partners.")

        return self._cache['partner_config']

    def get_item_config(self) -> Optional[Dict[int, Any]]:
        """
        加载并返回道具配置数据，以ID为键进行索引。
        """
        if 'item_config' not in self._cache:
            logging.info("Loading Item Config...")
            raw_config = self.get_json("FileCfg/ItemTemplateTb.json")
            if not raw_config or 'PDHBFPILAJD' not in raw_config:
                logging.error("Failed to load or parse ItemTemplateTb.json")
                return None
            # 预处理：构建以ID为键的配置字典
            processed_config = {}
            for item_data in raw_config['PDHBFPILAJD']:
                item_id = int(item_data['CJHNGFMGKGE'])

                # 基本配置：ID和名称键是必须的
                config_entry = {
                    'id': item_id,
                    'name_key': item_data['LNCODBGHFKM']
                }

                # 可选配置：描述和故事键
                # 只有当键存在且非空时才添加
                description_key = item_data.get('HKLJIIIPINE', '')
                if description_key:
                    config_entry['description_key'] = description_key

                story_key = item_data.get('NCDPCNGNNDB', '')
                if story_key:
                    config_entry['story_key'] = story_key

                processed_config[item_id] = config_entry

            self._cache['item_config'] = processed_config
            logging.info(f"Item Config loaded for {len(processed_config)} items.")

        return self._cache['item_config']


    def get_hollow_item_config(self) -> Optional[Dict[int, Any]]:
        """
        加载并返回空洞道具配置数据，以ID为键进行索引。
        """
        if 'hollow_item_config' not in self._cache:
            logging.info("Loading Hollow Item Config...")
            raw_config = self.get_json("FileCfg/HollowItemTemplateTb.json")
            if not raw_config or 'PDHBFPILAJD' not in raw_config:
                logging.error("Failed to load or parse HollowItemTemplateTb.json")
                return None

            # 预处理：构建以ID为键的配置字典
            processed_config = {}
            for item_data in raw_config['PDHBFPILAJD']:
                item_id = int(item_data['CJHNGFMGKGE'])

                # 基本配置：ID、名称键和描述键是必须的
                config_entry = {
                    'id': item_id,
                    'name_key': item_data['LNCODBGHFKM'],
                    'description_key': item_data['PPILGGFGMDP']
                }

                processed_config[item_id] = config_entry

            self._cache['hollow_item_config'] = processed_config
            logging.info(f"Hollow Item Config loaded for {len(processed_config)} items.")

        return self._cache['hollow_item_config']

    def get_weapon_config(self) -> Optional[Dict[int, Any]]:
        """
        加载并返回武器配置数据，以ID为键进行索引。
        """
        if 'weapon_config' not in self._cache:
            logging.info("Loading Weapon Config...")
            raw_config = self.get_json("FileCfg/WeaponTemplateTb.json")
            if not raw_config or 'PDHBFPILAJD' not in raw_config:
                logging.error("Failed to load or parse WeaponTemplateTb.json")
                return None

            # 预处理：构建以ID为键的配置字典
            processed_config = {}
            for weapon_data in raw_config['PDHBFPILAJD']:
                weapon_id = int(weapon_data['EGDBEJFIMCP'])

                # 基本配置：ID和模型ID是必须的
                config_entry = {
                    'id': weapon_id,
                    'model_id': weapon_data['MCGNCAPBMDN'] # e.g., "Weapon_B_Common_01"
                }

                # 可选配置：描述和故事键
                # 只有当键存在且非空时才添加
                description_key = weapon_data.get('LJDMINMOCKG', '')
                if description_key:
                    config_entry['description_key'] = description_key

                story_key = weapon_data.get('JDBHFACHBOF', '') or weapon_data.get('PHINCIBGEFF', '')
                if story_key:
                    config_entry['story_key'] = story_key

                # 推导名称键 (Name Key)
                # 例如: model_id = "Weapon_B_Common_01" -> name_key = "Item_Weapon_B_Common_01_Name"
                if config_entry.get('model_id'):
                    config_entry['name_key'] = f"Item_{config_entry['model_id']}_Name"

                processed_config[weapon_id] = config_entry

            self._cache['weapon_config'] = processed_config
            logging.info(f"Weapon Config loaded for {len(processed_config)} weapons.")

        return self._cache['weapon_config']

    def get_vhs_collection_config(self) -> Optional[Dict[int, Any]]:
        """
        加载并返回录像带集合配置数据，以ID为键进行索引。
        """
        if 'vhs_collection_config' not in self._cache:
            logging.info("Loading VHS Collection Config...")
            raw_config = self.get_json("FileCfg/VHSCollectionConfigTemplateTb.json")
            if not raw_config or 'PDHBFPILAJD' not in raw_config:
                logging.error("Failed to load or parse VHSCollectionConfigTemplateTb.json")
                return None

            # 预处理：构建以ID为键的配置字典
            processed_config = {}
            for vhs_data in raw_config['PDHBFPILAJD']:
                vhs_id = int(vhs_data['DDLCOLOFOOJ'])

                # 基本配置：ID是必须的
                config_entry = {
                    'id': vhs_id
                }

                # 可选配置：名称和描述键
                # 只有当键存在且非空时才添加
                name_key = vhs_data.get('DIEPHCMFCIL', '')
                if name_key:
                    config_entry['name_key'] = name_key

                description_key = vhs_data.get('DMPNAMLKGBP', '')
                if description_key:
                    config_entry['description_key'] = description_key

                processed_config[vhs_id] = config_entry

            self._cache['vhs_collection_config'] = processed_config
            logging.info(f"VHS Collection Config loaded for {len(processed_config)} items.")

        return self._cache['vhs_collection_config']

    def get_message_config(self) -> Optional[Dict[int, Any]]:
        """
        加载并返回手机短信配置数据，以消息ID为键进行索引。
        """
        if 'message_config' not in self._cache:
            logging.info("Loading Message Config...")
            raw_config = self.get_json("FileCfg/MessageConfigTemplateTb.json")
            if not raw_config or 'PDHBFPILAJD' not in raw_config:
                logging.error("Failed to load or parse MessageConfigTemplateTb.json")
                return None

            # 预处理：构建以消息ID为键的配置字典
            processed_config = {}
            for message_data in raw_config['PDHBFPILAJD']:
                message_id = int(message_data['CJHNGFMGKGE'])

                # 基本配置
                config_entry = {
                    'id': message_id,
                    'group_id': int(message_data.get('IIBGABOLBDI', 0)),
                    'text_key': message_data.get('DECDHOMFHKM', ''),
                    'sequence': int(message_data.get('BKOAPELPEGL', 0)),
                    'session_npc_id': int(message_data.get('POAKMNJMIAJ', 0)), # 使用 POAKMNJMIAJ 作为会话NPC ID
                    'POAKMNJMIAJ': int(message_data.get('POAKMNJMIAJ', 0)), # 保留原始字段，用于判断是否是玩家消息
                    'LMBEMIPCECK': int(message_data.get('LMBEMIPCECK', 0))  # 保留原始字段
                }

                # 解析对话选项
                options = []
                # Option 1
                if message_data.get('PJILMILDDBN') or message_data.get('ODCPPAKEEPM') or message_data.get('AAJNLGHFKID'):
                    option1 = {
                        'text_key': message_data.get('PJILMILDDBN'),
                        'long_text_key': message_data.get('ODCPPAKEEPM'),
                        'next_message_id': int(message_data.get('AAJNLGHFKID', 0)) if message_data.get('AAJNLGHFKID') else None
                    }
                    options.append(option1)

                # Option 2
                if message_data.get('LEACGIIJHHO') or message_data.get('NGADKHLFKDI') or message_data.get('AFNINBBDCOF'):
                    option2 = {
                        'text_key': message_data.get('LEACGIIJHHO'),
                        'long_text_key': message_data.get('NGADKHLFKDI'),
                        'next_message_id': int(message_data.get('AFNINBBDCOF', 0)) if message_data.get('AFNINBBDCOF') else None
                    }
                    options.append(option2)

                # Option 3
                if message_data.get('PFEFHIBHJDL') or message_data.get('KBIFFIEJJMO'):
                    option3 = {
                        'text_key': None, # 假设没有单独的文本键
                        'long_text_key': None,
                        'next_message_id': int(message_data.get('PFEFHIBHJDL', 0)) if message_data.get('PFEFHIBHJDL') else None
                    }
                    options.append(option3)

                # Option 4
                if message_data.get('KBIFFIEJJMO'):
                    option4 = {
                        'text_key': None, # 假设没有单独的文本键
                        'long_text_key': None,
                        'next_message_id': int(message_data.get('KBIFFIEJJMO', 0)) if message_data.get('KBIFFIEJJMO') else None
                    }
                    options.append(option4)

                config_entry['options'] = options
                processed_config[message_id] = config_entry

            self._cache['message_config'] = processed_config
            logging.info(f"Message Config loaded for {len(processed_config)} messages.")

        return self._cache['message_config']

    def get_message_npc_config(self) -> Optional[Dict[int, Any]]:
        """
        加载并返回手机短信NPC配置数据，以NPC ID为键进行索引。
        """
        if 'message_npc_config' not in self._cache:
            logging.info("Loading Message NPC Config...")
            raw_config = self.get_json("FileCfg/MessageNPCTemplateTb.json")
            if not raw_config or 'PDHBFPILAJD' not in raw_config:
                logging.error("Failed to load or parse MessageNPCTemplateTb.json")
                return None

            # 预处理：构建以NPC ID为键的配置字典
            processed_config = {}
            for npc_data in raw_config['PDHBFPILAJD']:
                npc_id = int(npc_data['CJHNGFMGKGE'])

                # 基本配置
                config_entry = {
                    'id': npc_id,
                    'LNCODBGHFKM': npc_data.get('LNCODBGHFKM', ''),
                    'avatar_id': npc_data.get('MDHDICACNJE', '') # 存储头像ID/路径
                }

                processed_config[npc_id] = config_entry

            self._cache['message_npc_config'] = processed_config
            logging.info(f"Message NPC Config loaded for {len(processed_config)} NPCs.")

        return self._cache['message_npc_config']

    def get_message_session_markdown(self, session_id: int) -> Optional[str]:
        """
        获取指定会话ID的格式化Markdown字符串。

        Args:
            session_id: 要获取的会话ID。

        Returns:
            格式化后的Markdown字符串，如果会话不存在则返回None。
        """
        from .formatters.session_formatter import SessionFormatter # Import here to avoid circular imports

        sessions = self.get_message_sessions()
        if not sessions:
            return None

        for session in sessions:
            if session.session_id == session_id:
                return SessionFormatter.to_markdown(session)

        return None # Session not found

    def get_message_sessions(self) -> Optional[List[Session]]:
        """
        加载并返回结构化的手机短信会话数据。
        使用 SessionInterpreter 将原始消息数据解释为 Session 对象列表。
        """
        cache_key = 'message_sessions'
        if cache_key not in self._cache:
            logging.info("Loading and parsing Message Sessions...")

            # 1. 获取原始数据
            raw_messages = self.get_json("FileCfg/MessageConfigTemplateTb.json")
            if not raw_messages or 'PDHBFPILAJD' not in raw_messages:
                logging.error("Failed to load or parse MessageConfigTemplateTb.json for sessions")
                return None

            # 2. 获取文本映射
            text_map = self.get_text_map()

            # 3. 获取NPC配置 (用于更准确的NPC名称解析)
            npc_config = self.get_json("FileCfg/MessageNPCTemplateTb.json")

            # 4. 初始化解释器并解释
            interpreter = SessionInterpreter(text_map, npc_config, player_name=self.player_name)
            try:
                sessions = interpreter.interpret(raw_messages['PDHBFPILAJD'])
                self._cache[cache_key] = sessions
                logging.info(f"Message Sessions parsed successfully. Total sessions: {len(sessions)}")
            except Exception as e:
                logging.error(f"Error parsing message sessions: {e}")
                return None

        return self._cache[cache_key]

    def save_cache(self, file_path: str) -> None:
        """
        Save the cache and search index to a file using pickle and gzip.
        """
        data_to_save = {
            'cache': self._cache,
            'search_index': self._search_index
        }
        with gzip.open(file_path, 'wb') as f:
            pickle.dump(data_to_save, f)
        logging.info(f"Cache and search index saved to {file_path}")

    def load_cache(self, file_path: str) -> bool:
        """
        Load the cache and search index from a file using pickle and gzip.
        """
        try:
            with gzip.open(file_path, 'rb') as f:
                data_loaded = pickle.load(f)
            self._cache = data_loaded.get('cache', {})
            self._search_index = data_loaded.get('search_index', {})
            logging.info(f"Cache and search index loaded from {file_path}")
            return True
        except FileNotFoundError:
            logging.warning(f"Cache file not found at: {file_path}")
            return False
        except (pickle.UnpicklingError, gzip.BadGzipFile) as e:
            logging.error(f"Failed to load cache from {file_path}: {e}")
            return False

    def _clean_text(self, text: str) -> str:
        """
        清洗文本，移除标点符号、特殊字符，并转换为小写。
        """
        text = re.sub(r'[^\u4e00-\u9fa5\u3040-\u30ff\uac00-\ud7a3a-zA-Z0-9\s]', '', text)
        text = re.sub(r'\s+', '', text)
        return text.lower()

    def _generate_ngrams(self, text: str, n: int = 2):
        """为给定的文本生成二元词条集合。"""
        if len(text) < n:
            return set()
        return {text[i:i+n] for i in range(len(text)-n+1)}

    def _add_to_index(self, keyword: str, item_id: Any, item_name: str, item_type: str, source_field: str):
        """向索引中添加一条记录，处理重复。"""
        key = keyword.lower()
        if not any(res.id == item_id and res.type == item_type for res in self._search_index[key]):
            self._search_index[key].append(
                SearchResult(id=item_id, name=item_name, type=item_type, match_source=source_field)
            )

    def _index_item(self, data: dict, context: Any):
        """
        为从JSON加载的数据(`data`)，根据其归属信息(`context`)，建立搜索索引。
        """
        item_id = context.get('id')
        item_type = context.get('type')
        item_name = context.get('name')

        if not all([item_id, item_type, item_name]):
            logging.warning(f"Indexing skipped: missing id, type, or name in context. context={context}")
            return

        # 对 content 字段进行索引
        if 'content' in data and isinstance(data['content'], str):
            cleaned_text = self._clean_text(data['content'])
            if cleaned_text:
                # 对短字段进行完整索引
                if len(cleaned_text) <= 5:
                     self._add_to_index(cleaned_text, item_id, item_name, item_type, 'content')

                # 对所有字段都进行二元索引
                for token in self._generate_ngrams(cleaned_text):
                     self._add_to_index(token, item_id, item_name, item_type, 'content')
