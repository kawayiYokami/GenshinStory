from ..models import Quest

class QuestFormatter:
    """
    负责将 **单个** Quest 对象的内部细节格式化为 Markdown。
    它处理任务的描述、步骤和对话。
    """
    def format_quest(self, quest: Quest, mode: str = 'story') -> str:
        """
        将单个 Quest 对象格式化为 Markdown 的一部分。
        此方法不再处理任务的顶级标题，因为这由 ChapterFormatter 控制。
        
        :param quest: 要格式化的 Quest 对象。
        :param mode: 格式化模式 ('story' 或 'debug')。
        """
        md = []

        # 任务标题由 ChapterFormatter 处理，这里只处理任务内部内容
        if mode == 'story':
            md.append(f'### {quest.quest_title}')
            md.append(f"<!-- Quest ID: {quest.quest_id} -->")
        else: # debug mode
            md.append(f"### {quest.quest_title} (ID: {quest.quest_id})")
        
        # 任务描述
        if quest.quest_description:
            md.append(f"> {quest.quest_description}")

        # 任务步骤
        if quest.steps:
            for step in quest.steps:
                md.append("") # 添加空行以分隔步骤
                if mode == 'story':
                    if step.step_description:
                         md.append(f"❖ **{step.step_description}**")
                    md.append(f"<!-- Step ID: {step.step_id} -->")
                else: # debug mode
                    md.append(f"**步骤 {step.step_id}**")
                    if step.step_description:
                        md.append(f"_{step.step_description}_")
                
                if step.dialogue_nodes:
                    md.append("") # 对话前添加空行
                    for line in step.dialogue_nodes:
                        md.append(f"- **{line.speaker}**: {line.content}")
        
        return "\n".join(md)