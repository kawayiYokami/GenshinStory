from hsrwiki_data_parser.models.rogue_event import RogueEvent, DialogueNode, Dialogue, Narrator

class RogueEventFormatter:

    def _format_dialogue_content(self, part: Dialogue | Narrator, indent_level: int = 0) -> str:
        """格式化单个对话内容（Dialogue 或 Narrator）"""
        indent = "    " * indent_level
        if isinstance(part, Dialogue):
            return f"{indent}**{part.speaker}:** {part.line}"
        elif isinstance(part, Narrator):
            return f"{indent}*({part.line})*"
        return ""

    def _format_dialogue_tree(self, node: DialogueNode, indent_level: int = 0) -> str:
        """递归格式化整个对话树，跳过空选项节点"""
        if not node:
            return ""

        indent = "    " * indent_level
        lines = []

        # 添加当前节点的对话内容
        for part in node.dialogue:
            lines.append(self._format_dialogue_content(part, indent_level))

        # 处理选项
        def _collect_options(options):
            """递归收集非空选项，跳过空选项节点"""
            collected = []
            for opt in options:
                if opt.option_text:
                    # 如果选项文本不为空，则是有效选项，直接添加
                    collected.append(opt)
                else:
                    # 如果是空选项节点，则递归处理其子选项
                    collected.extend(_collect_options(opt.options))
            return collected

        if node.options:
            effective_options = _collect_options(node.options)
            if effective_options:
                lines.append(f"{indent}- (玩家选项)")
                for option in effective_options:
                    lines.append(f"{indent}    - **{option.option_text}**")
                    # 递归处理子树，缩进级别增加
                    sub_tree = self._format_dialogue_tree(option, indent_level + 1)
                    if sub_tree:
                        # 移除子树开头可能存在的 "- (玩家选项)\n"，因为我们已经在当前层级渲染了它
                        sub_lines = sub_tree.split('\n')
                        if sub_lines and sub_lines[0].strip() == "- (玩家选项)":
                            sub_tree = '\n'.join(sub_lines[1:])
                        lines.append(sub_tree)

        return '\n'.join(lines)

    def format(self, item: RogueEvent) -> str:
        if not isinstance(item, RogueEvent):
            return ""

        md = []
        md.append(f"# {item.title}")
        if item.location:
            md.append(f"*地点: {item.location}*")
        md.append("\n---\n")

        if item.dialogue_tree:
            md.append("\n## 事件对话")
            md.append(self._format_dialogue_tree(item.dialogue_tree))

        # 可选：添加 possible_outcomes 部分
        if item.possible_outcomes:
            md.append("\n## 可能的结果")
            for outcome in item.possible_outcomes:
                # 过滤掉包含"[注释]"的条目
                if "[注释]" not in outcome:
                    md.append(f"- {outcome}")

        return '\n'.join(md)