from typing import Dict, Any, List, Optional
import os
from game_data_parser.models import Quest, QuestStep, DialogueNode, Chapter
from game_data_parser.dataloader import DataLoader
from ..services.text_map_service import TextMapService
from ..utils.text_transformer import transform_text
import logging

class QuestInterpreter:
    """
    负责将原始任务数据解析成结构化的Quest对象。
    采用预处理机制，在第一次调用时扫描所有任务文件以构建系列和章节的完整映射。
    """
    def __init__(self, data_loader: DataLoader, text_map_service: TextMapService):
        self.loader = data_loader
        self.text_map_service = text_map_service
        self._dialog_excel: Dict[int, Dict] = {}
        self._npc_map: Dict[str, str] = {}
        
        # --- 结构化映射与缓存 ---
        self._raw_quests_cache: Dict[int, Dict] = {} # quest_id -> {'data': raw_quest_data, 'filename': str}
        self._chapter_map: Dict[int, Chapter] = {} # chapter_id -> Chapter object
        self._quest_map: Dict[int, Quest] = {} # quest_id -> Quest object
        
        self._is_prepared = False

    def _extract_type_from_luapath(self, lua_path: Optional[str]) -> Optional[str]:
        """从 luaPath 中提取任务类型，例如 'Actor/Quest/WQ71812' -> 'WQ'。"""
        if not lua_path or "Quest/" not in lua_path:
            return None
        try:
            start_index = lua_path.index("Quest/") + len("Quest/")
            if len(lua_path) >= start_index + 2:
                # 提取两个字母的类型代码
                type_code = lua_path[start_index:start_index+2]
                # 确保提取的是字母
                if type_code.isalpha():
                    return type_code.upper()
        except (ValueError, IndexError):
            return None
        return None

    def _get_text(self, text_map_hash: Any, default: str = "") -> str:
        """根据哈希值安全地获取原始文本。"""
        return self.text_map_service.get(text_map_hash, default)

    def _prepare_data_and_build_maps(self):
        """
        一次性加载所有需要的数据，并根据最终确定的多级优先级逻辑构建关系。
        采用分阶段处理，确保逻辑清晰和结果的确定性。
        """
        if self._is_prepared:
            return

        # --- Phase 0: 加载基础数据 ---
        logging.info("Phase 0: 加载基础数据 (DialogExcel, NpcExcel)...")
        dialog_list = self.loader.get_json("ExcelBinOutput/DialogExcelConfigData.json") or []
        self._dialog_excel = {item["GFLDJMJKIKE"]: item for item in dialog_list if "GFLDJMJKIKE" in item}
        npc_data_list = self.loader.get_json("ExcelBinOutput/NpcExcelConfigData.json") or []
        self._npc_map = {str(item["id"]): self._get_text(item.get("nameTextMapHash"), f"NPC {item['id']}") for item in npc_data_list}

        # --- Phase 1: 扫描并缓存所有任务和章节数据 ---
        logging.info("Phase 1: 扫描并缓存所有任务和章节数据...")
        all_quest_files = self.loader.get_all_json_files_in_dir("BinOutput/Quest", yield_filename=True)
        if not all_quest_files:
            logging.error("在 'BinOutput/Quest' 目录下没有找到任何任务文件。")
            self._is_prepared = True
            return
        
        for filename, quest_data in all_quest_files:
            quest_id = quest_data.get('id')
            if not quest_id or quest_data.get('showType') == 'QUEST_HIDDEN':
                continue
            # 优先使用主文件（文件名与ID相同）
            current_is_primary = (str(quest_id) == os.path.splitext(filename)[0])
            if quest_id in self._raw_quests_cache:
                existing_is_primary = (str(quest_id) == os.path.splitext(self._raw_quests_cache[quest_id].get('filename', ''))[0])
                if existing_is_primary and not current_is_primary:
                    continue
            self._raw_quests_cache[quest_id] = {'data': quest_data, 'filename': filename}

        chapter_data_list = self.loader.get_json("ExcelBinOutput/ChapterExcelConfigData.json") or []
        for chapter_data in chapter_data_list:
            chapter_id = chapter_data.get('id')
            if not chapter_id: continue
            self._chapter_map[chapter_id] = Chapter(
                id=chapter_id,
                title=self._get_text(chapter_data.get('chapterTitleTextMapHash')),
                chapter_num_text=self._get_text(chapter_data.get('chapterNumTextMapHash')),
                image_title=self._get_text(chapter_data.get('chapterImageTitleTextMapHash')),
                quest_type=chapter_data.get('questType'),
                entry_quest_ids=chapter_data.get("PJNNDMHDAPP", []),
                city_id=chapter_data.get("cityId"),
                group_id=chapter_data.get("groupId"),
            )

        # --- Phase 2: 实例化所有 Quest 对象 ---
        logging.info("Phase 2: 正在实例化所有 Quest 对象...")
        for quest_id in self._raw_quests_cache.keys():
            quest = self.interpret(quest_id, prepped=True)
            if quest:
                self._quest_map[quest_id] = quest

        # --- Phase 3: 建立 Chapter -> Quest 关系 ---
        logging.info("Phase 3: 正在建立 Chapter -> Quest 关联...")
        series_to_chapter_map: Dict[int, int] = {}

        # 来源 A (权威): 遍历 Chapter 的 entry_quest_ids (现在我们认为它存的是 series_id)
        for chapter in self._chapter_map.values():
            for series_id in chapter.entry_quest_ids:
                if series_id not in series_to_chapter_map:
                    series_to_chapter_map[series_id] = chapter.id
        
        # 来源 B (后备): 遍历 Quest 自身的 chapterId
        for quest in self._quest_map.values():
            if quest.series_id and quest.chapter_id:
                if quest.series_id not in series_to_chapter_map:
                    series_to_chapter_map[quest.series_id] = quest.chapter_id

        # 最终分配
        for quest in self._quest_map.values():
            final_chapter_id = quest.chapter_id
            
            if not final_chapter_id and quest.series_id in series_to_chapter_map:
                final_chapter_id = series_to_chapter_map[quest.series_id]
                quest.chapter_id = final_chapter_id
                chapter = self._chapter_map.get(final_chapter_id)
                if chapter:
                    quest.chapter_title = chapter.title

            if final_chapter_id and final_chapter_id in self._chapter_map:
                if not any(q.quest_id == quest.quest_id for q in self._chapter_map[final_chapter_id].quests):
                    self._chapter_map[final_chapter_id].quests.append(quest)

        # --- Phase 4: 处理孤立任务，为它们创建虚拟章节 ---
        logging.info("Phase 4: 正在处理孤立任务并创建虚拟章节...")
        # 使用内部方法安全地获取孤立任务，避免递归
        orphan_quests = self._find_orphan_quests_unsafe()
        
        orphan_by_series: Dict[int, List[Quest]] = {}
        orphans_no_series: List[Quest] = []

        for quest in orphan_quests:
            if quest.series_id:
                if quest.series_id not in orphan_by_series:
                    orphan_by_series[quest.series_id] = []
                orphan_by_series[quest.series_id].append(quest)
            else:
                orphans_no_series.append(quest)
        
        # 为有系列的孤立任务创建章节
        for series_id, quests in orphan_by_series.items():
            quests.sort(key=lambda q: q.quest_id)
            first_quest = quests[0]
            
            new_chapter_id = series_id + 100000
            new_chapter_title = f"系列 {series_id}: {first_quest.quest_title}"
            
            new_chapter = Chapter(
                id=new_chapter_id,
                title=new_chapter_title,
                quest_type="ORPHAN_SERIES", # 自定义类型
                quests=quests
            )
            self._chapter_map[new_chapter_id] = new_chapter
            
            # 更新任务的章节信息
            for q in quests:
                q.chapter_id = new_chapter_id
                q.chapter_title = new_chapter_title

        # 为无系列的孤立任务创建统一章节
        if orphans_no_series:
            orphans_no_series.sort(key=lambda q: q.quest_id)
            misc_chapter_id = 999999
            misc_chapter_title = "零散任务"
            
            misc_chapter = Chapter(
                id=misc_chapter_id,
                title=misc_chapter_title,
                quest_type="ORPHAN_MISC",
                quests=orphans_no_series
            )
            self._chapter_map[misc_chapter_id] = misc_chapter

            # 更新任务的章节信息
            for q in orphans_no_series:
                q.chapter_id = misc_chapter_id
                q.chapter_title = misc_chapter_title

        logging.info("结构化映射构建完成。")
        self._is_prepared = True

    def _parse_dialog_from_source(self, start_id: int, source_map: Dict[int, Dict], _processed_ids: Optional[set] = None) -> List[DialogueNode]:
        """
        从一个给定的对话源中追踪并解析对话链，正确处理分支和汇合。
        这是一个递归函数，每次调用处理一个节点及其直接后续。
        """
        if _processed_ids is None:
            _processed_ids = set()

        if not start_id or start_id in _processed_ids or start_id not in source_map:
            return []

        _processed_ids.add(start_id)
        
        dialog_data = source_map[start_id]
        raw_content = self._get_text(dialog_data.get("talkContentTextMapHash"))
        content, is_valid = transform_text(raw_content)

        if not is_valid:
            return []

        talk_role_info = dialog_data.get("talkRole", {})
        role_id = talk_role_info.get("_id")
        role_type = talk_role_info.get("type")
        
        final_role_name = "unknown"
        if role_id:
            role_id_str = str(role_id)
            final_role_name = self._npc_map.get(role_id_str, role_id_str)
        else:
            raw_role_name = self._get_text(dialog_data.get("talkRoleNameTextMapHash"))
            role_name, _ = transform_text(raw_role_name)
            if role_name:
                final_role_name = role_name
        
        if role_id == 1005 or str(role_id) == "1005":
            final_role_name = "派蒙"
        if role_type == 'TALK_ROLE_PLAYER':
            final_role_name = "旅行者"
        if role_type == 'TALK_ROLE_BLACK_SCREEN':
            final_role_name = "旁白"

        # 创建当前节点
        current_node = DialogueNode(
            id=start_id,
            speaker=final_role_name,
            content=content,
            node_type="option" if role_type == 'TALK_ROLE_PLAYER' else "dialogue"
        )

        next_ids = [nid for nid in dialog_data.get("nextDialogs", []) if nid != 0]

        # 检查是否为分支点
        is_branch_point = len(next_ids) > 1
        if is_branch_point:
            for option_id in next_ids:
                # 每个选项都是一个新的分支，递归解析
                # 注意：这里传递共享的 _processed_ids 以防止循环
                option_chain = self._parse_dialog_from_source(option_id, source_map, _processed_ids)
                if option_chain:
                    current_node.options.append(option_chain[0]) # 将分支的第一个节点作为选项
            return [current_node]

        # 如果不是分支点，处理线性流程
        elif next_ids:
            # 递归获取后续的对话链
            following_nodes = self._parse_dialog_from_source(next_ids[0], source_map, _processed_ids)
            return [current_node] + following_nodes
        
        # 如果是末端节点
        else:
            return [current_node]

    def _find_and_parse_dialog(self, base_talk_id: int, current_quest_talks: Dict[int, Dict], context_quest_id: Optional[int] = None) -> List[DialogueNode]:
        """
        根据 TalkID 解析对话。
        该函数采用优先级策略，以正确处理两种有效的对话模式：
        1. 优先查找在主任务文件中定义的“内嵌对话”。
        2. 如果找不到，则查找与TalkID同名的“独立对话文件”。
        """
        # 策略 1: 检查内嵌对话
        logging.debug(f"为 TalkID {base_talk_id} 查找对话... 策略1: 检查内嵌定义。")
        if base_talk_id in current_quest_talks:
            talk_definition = current_quest_talks[base_talk_id]
            dialog_list = talk_definition.get("dialogList")
            if dialog_list and isinstance(dialog_list, list) and dialog_list:
                logging.debug(f"  在内嵌定义中找到 'dialogList'，开始解析。")
                dialog_map = {d["id"]: d for d in dialog_list if "id" in d}
                if "id" in dialog_list[0]:
                    return self._parse_dialog_from_source(dialog_list[0]["id"], dialog_map)
                else:
                    logging.warning(f"    [Quest: {context_quest_id}] 内嵌 talk ({base_talk_id}) 的 dialogList[0] 格式不正确。")
                    return [] # 找到定义但格式错误，不再继续查找

        # 策略 2: 查找独立文件
        logging.debug(f"  策略1失败，转至策略2: 查找独立文件。")
        
        talk_id_map = self.loader.get_talk_id_map()
        talk_relative_path = talk_id_map.get(base_talk_id)

        if not talk_relative_path:
            # It's not an error if a talk is not found, it might just be an unused condition.
            # Logging as debug instead of warning.
            logging.debug(f"  [Quest: {context_quest_id}] 在 TalkID 映射中未找到 TalkID {base_talk_id} 对应的文件记录。")
            return []

        full_relative_path = os.path.join("BinOutput/Talk", talk_relative_path).replace('\\', '/')
        talk_file_data = self.loader.get_json(full_relative_path)
        
        if not talk_file_data:
            logging.warning(f"  [Quest: {context_quest_id}] TalkID {base_talk_id} 对应的文件 {full_relative_path} 加载失败或内容为空。")
            return []

        dialog_list = talk_file_data.get("dialogList", [])
        if not dialog_list:
            logging.warning(f"  [Quest: {context_quest_id}] TalkID {base_talk_id} 对应的文件 {full_relative_path} 中没有 'dialogList'。")
            return []
            
        dialog_map = {d["id"]: d for d in dialog_list if "id" in d}
        
        if "id" in dialog_list[0]:
            start_dialog_id = dialog_list[0]["id"]
            return self._parse_dialog_from_source(start_dialog_id, dialog_map)
        else:
            logging.warning(f"  [Quest: {context_quest_id}] 文件 {full_relative_path} 的 dialogList[0] 格式不正确，缺少 'id'。")
            return []

    def interpret(self, quest_id: int, prepped: bool = False) -> Optional[Quest]:
        """
        解析单个任务，并利用预先构建的映射来自动关联其所属的系列和章节。
        :param quest_id: The ID of the quest to interpret.
        :param prepped: Internal flag to avoid recursive preparation.
        """
        if not prepped:
            self._prepare_data_and_build_maps()

        # If the quest has already been interpreted, return it from the map.
        if quest_id in self._quest_map:
            return self._quest_map[quest_id]

        cached_item = self._raw_quests_cache.get(quest_id)
        if not cached_item:
            logging.warning(f"请求的任务ID {quest_id} 在缓存中不存在。")
            return None
        
        quest_data = cached_item['data']
        source_filename = cached_item['filename']

        # --- 推断 Quest Type (Category) ---
        quest_type = None
        chapter_id = quest_data.get('chapterId')
        chapter = self._chapter_map.get(chapter_id) if chapter_id else None
        
        if chapter and chapter.quest_type:
            quest_type = chapter.quest_type
        elif quest_data.get('luaPath'):
            quest_type = self._extract_type_from_luapath(quest_data.get('luaPath'))
        elif quest_data.get('damageRatio'):
            quest_type = quest_data.get('damageRatio')

        # 只加载当前任务自身的对话定义
        current_quest_talks = {}
        if "talks" in quest_data:
            for talk in quest_data.get("talks", []):
                current_quest_talks[talk["id"]] = talk
        
        quest_title_raw = self._get_text(quest_data.get("titleTextMapHash"))
        quest_title, is_title_valid = transform_text(quest_title_raw)
        
        if not is_title_valid:
            logging.debug(f"Quest {quest_id} has a non-displayable title: '{quest_title}'")

        quest_desc_raw = self._get_text(quest_data.get("descTextMapHash"))
        quest_desc, _ = transform_text(quest_desc_raw)

        quest = Quest(
            quest_id=quest_id,
            quest_title=quest_title,
            quest_description=quest_desc,
            quest_type=quest_type,
            chapter_id=chapter.id if chapter else None,
            chapter_title=chapter.title if chapter else None,
            series_id=quest_data.get('series'),
            source_json=source_filename,
            suggest_track_main_quest_list=quest_data.get("suggestTrackMainQuestList")
        )

        # 解析步骤和对话
        logging.debug(f"开始解析 Quest {quest_id} 的步骤...")
        
        # 1. 按 'order' 字段对子任务进行排序
        sorted_sub_quests = sorted(quest_data.get("subQuests", []), key=lambda sq: sq.get("order", 0))

        for sub_quest in sorted_sub_quests:
            # 2. 跳过 showType 为 "QUEST_HIDDEN" 的子任务
            if sub_quest.get("showType") == "QUEST_HIDDEN" or sub_quest.get("showGuide") == "QUEST_GUIDE_ITEM_DISABLE" :
                continue

            step_id = sub_quest.get('subId')
            logging.debug(f"  处理步骤 StepID: {step_id}")
            
            raw_step_desc = self._get_text(sub_quest.get("descTextMapHash"))
            step_description, is_valid = transform_text(raw_step_desc)

            quest_step = QuestStep(
                step_id=step_id,
                step_description=step_description if is_valid and step_description else None,
                # dialogue_nodes is now empty by default
            )

            logging.debug(f"    检查 finishCond: {sub_quest.get('finishCond')}")
            for cond in sub_quest.get("finishCond", []):
                condition_type = cond.get("type") or cond.get("damageRatio")

                if condition_type in ["QUEST_CONTENT_COMPLETE_TALK", "QUEST_CONTENT_COMPLETE_ANY_TALK"]:
                    talk_id = cond.get("param", [None])[0]
                    if talk_id:
                        # 惰性加载：只记录 TalkID，不立即解析
                        logging.debug(f"    在 StepID {step_id} 中找到对话条件, 记录 TalkID: {talk_id} 以待后续解析。")
                        quest_step.talk_ids.append(talk_id)

            # 只有当步骤包含有效描述或【潜在】对话时，才将其添加到任务中
            if quest_step.step_description or quest_step.talk_ids:
                quest.steps.append(quest_step)
            else:
                logging.debug(f"  跳过 StepID: {step_id} 因为其既无有效描述也无潜在对话。")

        return quest

    def get_all_chapters(self) -> List[Chapter]:
        """返回所有已解析的Chapter对象的列表，每个Chapter都链接了其对应的Quest。"""
        self._prepare_data_and_build_maps()
        return list(self._chapter_map.values())

    def get_quest_title(self, quest_id: int) -> Optional[str]:
        """快速获取任务标题，不进行完整解析。"""
        self._prepare_data_and_build_maps()
        cached_item = self._raw_quests_cache.get(quest_id)
        if not cached_item:
            return None
        
        title_hash = cached_item['data'].get('titleTextMapHash')
        if not title_hash:
            return f"Quest {quest_id}" # 返回一个默认值
            
        title, _ = transform_text(self._get_text(title_hash))
        return title
        
    def get_all_quest_ids(self) -> List[int]:
        """获取所有已发现的任务ID列表。"""
        self._prepare_data_and_build_maps()
        return sorted(list(self._raw_quests_cache.keys()))

    def get_raw_data(self, quest_id: int) -> Optional[Dict[str, Any]]:
        """从缓存中获取单个任务的原始JSON数据。"""
        self._prepare_data_and_build_maps()
        cached_item = self._raw_quests_cache.get(quest_id)
        return cached_item['data'] if cached_item else None

    def _find_orphan_quests_unsafe(self) -> List[Quest]:
        """
        [私有] 查找孤立任务的核心逻辑，不包含数据准备步骤以防止递归。
        """
        all_quest_ids = set(self._quest_map.keys())
        quests_in_chapters = set()
        for chapter in self._chapter_map.values():
            for quest in chapter.quests:
                quests_in_chapters.add(quest.quest_id)
        
        orphan_ids = all_quest_ids - quests_in_chapters
        return [self._quest_map[qid] for qid in sorted(list(orphan_ids))]

    def get_orphan_quest_ids(self) -> List[int]:
        """获取所有未被分配到任何章节的任务ID列表（孤立任务）。"""
        self._prepare_data_and_build_maps()
        # 在数据准备好后，调用安全的内部方法
        orphan_quests = self._find_orphan_quests_unsafe()
        return [q.quest_id for q in orphan_quests]