from hsr_data_parser.models import MainMission

class MissionFormatter:
    """
    负责将 MainMission 对象格式化为 Markdown 文本。
    """
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
            # Group dialogue by sub-mission to present it logically
            last_ui_info = None
            for i, sub_mission_script in enumerate(mission.scripts):
                current_ui_info = sub_mission_script.ui_info
                
                # Print header for new sub-mission objective, only if it exists and is different
                if current_ui_info and current_ui_info.target_text and current_ui_info != last_ui_info:
                    lines.append(f"\n### {current_ui_info.target_text}")
                    if current_ui_info.description_text:
                        md_description = current_ui_info.description_text.replace('\\n', '  \n')
                        description_lines = md_description.split('\n')
                        lines.extend([f"> {line}" for line in description_lines])
                    last_ui_info = current_ui_info
                
                # If there is dialogue, ensure there's a blank line separating it from the header/description
                if current_ui_info and sub_mission_script.script and sub_mission_script.script.dialogue_blocks:
                    lines.append("")

                # Print dialogue
                if sub_mission_script.script and sub_mission_script.script.dialogue_blocks:
                    for block in sub_mission_script.script.dialogue_blocks:
                        if block.sentences:
                            for sentence in block.sentences:
                                speaker = sentence.speaker
                                text = sentence.text or ""
                                # If speaker is present, format as dialogue
                                if speaker:
                                    # Add two spaces at the end for a markdown line break
                                    lines.append(f"**{speaker}**: {text}  ")
                                # If no speaker, output the raw text and sentence ID for investigation
                                else:
                                    # Add two spaces at the end for a markdown line break
                                    lines.append(f"**未知来源文本 (SentenceID: {sentence.id})**: {text}  ")
        
        return "\n".join(lines)