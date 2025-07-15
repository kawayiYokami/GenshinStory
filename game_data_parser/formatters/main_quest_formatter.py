from ..models import MainQuest, SubQuest, MainQuestItem, MainQuestDialog, MainQuestText

class MainQuestMarkdownFormatter:
    """
    Formats a MainQuest object into a human-readable Markdown string.
    """
    
    def format(self, main_quest: MainQuest) -> str:
        """
        Converts a MainQuest object to a Markdown formatted string.

        Args:
            main_quest: The MainQuest object to format.

        Returns:
            A string containing the formatted quest in Markdown.
        """
        if not main_quest:
            return "## Error: Invalid MainQuest object provided."

        lines = []

        # --- Title and Metadata ---
        lines.append(f"# {main_quest.main_quest_title.text_content if main_quest.main_quest_title else 'Untitled Quest'}")
        if main_quest.chapter_num and main_quest.chapter_num.text_content:
            lines.append(f"_{main_quest.chapter_num.text_content}_")
        if main_quest.main_quest_desp and main_quest.main_quest_desp.text_content:
            lines.append(f"> {main_quest.main_quest_desp.text_content}")
        lines.append("\n---\n")

        # --- SubQuests and Items ---
        for i, sub_quest in enumerate(main_quest.sub_quests, 1):
            if sub_quest.sub_quest_title and sub_quest.sub_quest_title.text_content:
                lines.append(f"## {i}. {sub_quest.sub_quest_title.text_content}")
            else:
                lines.append(f"## Section {i}")

            for item in sub_quest.items:
                self._format_item(item, lines)
            
            lines.append("") # Add a blank line between sub-quests

        return "\n".join(lines)

    def _format_item(self, item: MainQuestItem, lines: list[str]):
        """Formats a single MainQuestItem."""
        
        # Format dialogue items
        if item.item_type in ["SingleDialog", "MultiDialog"]:
            speaker = item.speaker_text.text_content if item.speaker_text else "Unknown"
            
            if item.item_type == "MultiDialog":
                 lines.append(f"**{speaker} (Choose one):**")
                 for dialog in item.dialogs:
                     lines.append(f"- *{dialog.text.text_content if dialog.text else ''}*")
            else: # SingleDialog
                 for dialog in item.dialogs:
                    lines.append(f"**{speaker}:** {dialog.text.text_content if dialog.text else ''}")

        # Format narratage items
        elif item.item_type == "TextLeft":
            for text in item.texts:
                 lines.append(f"> *{text.text_content if text else ''}*")
        
        # Fallback for unknown item types
        else:
            lines.append(f"> `Unhandled ItemType: {item.item_type}`")
