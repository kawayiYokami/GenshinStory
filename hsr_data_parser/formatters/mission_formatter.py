from hsr_data_parser.models import MainMission, DialogueElement, DialogueSentence, DialogueOptionGroup

class MissionFormatter:
    """
    负责将 MainMission 对象格式化为 Markdown 文本。
    """
    
    def _format_elements(self, elements: list[DialogueElement]) -> list[str]:
        """
        将一个扁平化的 DialogueSentence 元素列表格式化为 Markdown 行。
        """
        lines = []
        for element in elements:
            if isinstance(element, DialogueSentence):
                speaker = element.speaker
                text = element.text or ""
                
                # 玩家选项通常由开拓者说出，可以进行强调。
                if speaker == "开拓者":
                    lines.append(f"* **{speaker}**: {text}")
                elif speaker:
                    lines.append(f"**{speaker}**: {text}")
                else:
                    lines.append(f"**未知来源文本 (ID: {element.id})**: {text}")
        return lines

    def format(self, mission: MainMission) -> str:
        """
        将 MainMission 对象转换为格式化的 Markdown 字符串。
        """
        if not mission:
            return ""

        lines = [f"# {mission.name} (ID: {mission.id})"]
        if hasattr(mission, 'description') and mission.description:
            lines.append(f"_{mission.description}_")
        
        lines.append("\n---")
        
        if mission.scripts:
            last_ui_info = None
            for sub_mission_script in mission.scripts:
                
                # 在子任务之间添加标准水平分割线
               # 仅在不是第一个脚本时添加，以避免开头的分割线。
               if lines and lines[-1] != "\n---":
                   lines.append("\n---\n")

               current_ui_info = sub_mission_script.ui_info
               
               # 仅在任务目标为新时打印
               if current_ui_info and current_ui_info.target_text and current_ui_info != last_ui_info:
                   lines.append(f"### {current_ui_info.target_text}")
                   if current_ui_info.description_text:
                       md_description = current_ui_info.description_text.replace('\\n', '  \n')
                       description_lines = md_description.split('\n')
                       lines.extend([f"> {line}" for line in description_lines])
                       lines.append("") # 确保引用块后有空行
                   last_ui_info = current_ui_info

               # 如果存在，则打印摘要
               if sub_mission_script.summary:
                   lines.append(f"> **概要**: {sub_mission_script.summary}")
                   lines.append("") # 确保引用块后有空行

               # 使用新的简化格式化程序打印对话
               if sub_mission_script.script and sub_mission_script.script.dialogue_blocks:
                    for block in sub_mission_script.script.dialogue_blocks:
                        if block.sentences:
                            formatted_block_lines = self._format_elements(block.sentences)
                            lines.extend(formatted_block_lines)
        
        # 清理并连接所有行
        final_text = "\n".join(lines).strip()
        # 确保不会出现超过两个连续的换行符
        import re
        final_text = re.sub(r'\n{3,}', '\n\n', final_text)
        return final_text