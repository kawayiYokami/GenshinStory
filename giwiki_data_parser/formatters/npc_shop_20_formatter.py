"""
原神Wiki NPC数据格式化器

将NPC数据转换为Markdown格式，专注于展示对话和故事内容。
"""

from typing import List
from ..models.npc_shop_20 import NPCModel, NPCCollection, DialogueGroup, DialogueOption


class NPCFormatter:
    """NPC数据格式化器"""

    def format_single_npc(self, npc: NPCModel, include_metadata: bool = True) -> str:
        """格式化单个NPC"""
        lines = []

        # 标题
        lines.append(f"# {npc.name}")
        lines.append("")

        # 基本信息
        if include_metadata:
            lines.append("## 基本信息")
            lines.append("")

            if npc.location:
                lines.append(f"**位置**: {npc.location}")
            if npc.gender:
                lines.append(f"**性别**: {npc.gender}")

            lines.append("")

        # 对话内容
        if npc.dialogue_groups:
            lines.append("## 对话内容")
            lines.append("")
            lines.extend(self._format_dialogue_groups(npc.dialogue_groups))

        return '\n'.join(lines).strip()

    def _format_dialogue_groups(self, dialogue_groups: List[DialogueGroup]) -> List[str]:
        """格式化对话组"""
        lines = []

        for group in dialogue_groups:
            # 对话组标题（如果不是默认的"NPC对话"）
            if group.title and group.title != "NPC对话":
                lines.append(f"### {group.title}")
                lines.append("")

            # 处理对话选项
            for dialogue_option in group.dialogues:
                # 选项标题
                if dialogue_option.option:
                    lines.append(f"**{dialogue_option.option}**")
                    lines.append("")

                # 对话内容
                for content in dialogue_option.content:
                    content = content.strip()
                    if content:
                        lines.append(f"> {content}")
                        lines.append("")

                # 选项之间的分隔
                if dialogue_option != group.dialogues[-1]:  # 不是最后一个选项
                    lines.append("---")
                    lines.append("")

            # 对话组之间的分隔
            if group != dialogue_groups[-1]:  # 不是最后一个组
                lines.append("---")
                lines.append("")

        return lines

    def format_collection(self, collection: NPCCollection, story_only: bool = True) -> str:
        """格式化NPC集合"""
        lines = []

        # 标题
        lines.append("# 原神NPC资料")
        lines.append("")

        # 统计信息
        total_npcs = len(collection.npcs)
        story_npcs = collection.get_story_npcs()

        lines.append("## 数据概览")
        lines.append("")
        lines.append(f"- 总NPC数量: {total_npcs}")
        lines.append(f"- 包含故事内容: {len(story_npcs)}")
        lines.append("")

        # 选择要展示的NPC
        npcs_to_show = story_npcs if story_only else collection.npcs

        if story_only and story_npcs:
            lines.append("## 故事NPC")
            lines.append("")
            lines.append("以下NPC包含丰富的对话内容和故事背景：")
            lines.append("")

        # 按位置分组展示
        if npcs_to_show:
            location_groups = collection.group_by_location()

            for location, location_npcs in sorted(location_groups.items()):
                if not location_npcs:
                    continue

                # 只显示故事NPC
                if story_only:
                    location_npcs = [npc for npc in location_npcs if npc in story_npcs]
                    if not location_npcs:
                        continue

                lines.append(f"### {location}")
                lines.append("")

                for npc in location_npcs:
                    lines.append(f"#### {npc.name}")
                    lines.append("")

                    # 显示部分对话预览
                    all_content = npc.get_all_dialogue_content()
                    if all_content:
                        lines.append("**主要对话**:")
                        lines.append("")
                        # 只显示前3条对话作为预览
                        for content in all_content[:3]:
                            lines.append(f"> {content}")

                        if len(all_content) > 3:
                            lines.append(f"> ...")
                            lines.append(f"*（共{len(all_content)}条对话）*")
                        lines.append("")

                    lines.append("---")
                    lines.append("")

        return '\n'.join(lines).strip()

    def get_filename(self, npc: NPCModel) -> str:
        """生成文件名"""
        # 清理文件名中的特殊字符
        safe_name = npc.name.replace("/", "_").replace("\\", "_").replace(":", "_")
        return f"{safe_name}.md"

    def format(self, npc: NPCModel) -> str:
        """标准格式化方法，用于与主解析器兼容"""
        return self.format_single_npc(npc)