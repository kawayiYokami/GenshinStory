"""
会话对象格式化模块，用于转换为各种输出格式，主要是 Markdown。
此格式化器实现了简单的嵌套列表结构，带有锚点链接，
用于表示分支对话流程，符合用户偏好。
"""

from typing import Dict, Any, List
from ..models.session import Session, Stage, Message, PlayerOptions, Option


class SessionFormatter:
    """
    会话对象格式化器，用于转换为各种输出格式。
    """

    @staticmethod
    def _format_message(message: Message) -> str:
        """
        将单个消息格式化为字符串行。

        参数:
            message: 要格式化的消息对象。

        返回:
            表示消息的格式化字符串行。
        """
        # 发言者名称已由 SessionInterpreter 解析
        speaker_display = f"**{message.speaker_name}**" if message.speaker_name else "**[未知发送者]**"
        # 消息文本已由 SessionInterpreter 解析
        message_text = message.text if message.text else "[无文本]"

        return f"{speaker_display}: {message_text}"

    @staticmethod
    def _format_option(option: Option, index: int) -> str:
        """
        将单个选项格式化为字符串行。

        参数:
            option: 要格式化的选项对象。
            index: 选项的从1开始的索引。

        返回:
            表示选项的格式化字符串行。
        """
        # 选项文本已由 SessionInterpreter 解析和组合
        option_text = option.text if option.text else "[无文本]"
        # 创建指向目标阶段的锚点链接
        target_anchor = f"#stage-{option.jump_to_sequence_id}"

        return f"{index}. {option_text} -> **跳转到 [阶段 {option.jump_to_sequence_id}]({target_anchor})**"

    @staticmethod
    def _format_player_options(player_options: PlayerOptions) -> List[str]:
        """
        将玩家选项对象格式化为字符串行列表。

        参数:
            player_options: 要格式化的玩家选项对象。

        返回:
            表示玩家选项的格式化字符串行列表。
        """
        lines = []

        # 添加选项标题
        lines.append("> **选项分支**:")

        # 格式化每个选项
        for i, option in enumerate(player_options.options, 1):
            lines.append(SessionFormatter._format_option(option, i))

        # 添加解锁条件（如果存在）
        if player_options.unlocks_condition:
            lines.append(f"  - `(解锁条件: {player_options.unlocks_condition})`")

        return lines

    @staticmethod
    def _format_stage(stage: Stage) -> List[str]:
        """
        将单个阶段格式化为字符串行列表。

        参数:
            stage: 要格式化的阶段对象。

        返回:
            表示阶段的格式化字符串行列表。
        """
        lines: List[str] = []

        # 分隔符和跳转目标的锚点
        lines.append("---")
        lines.append(f"<a id=\"stage-{stage.sequence_id}\"></a>")

        # 使用紧凑的内联标记代替大标题
        lines.append(f"[{stage.sequence_id}]")
        lines.append("")  # 标记后的空行

        # 格式化消息（如果存在）
        if stage.messages:
            for message in stage.messages:
                # 仅当消息有文本时才添加消息行
                if message.text:
                    lines.append(SessionFormatter._format_message(message))
                    # 添加消息的解锁条件（如果存在）
                    if message.unlocks_condition:
                        lines.append(f"  - `(解锁条件: {message.unlocks_condition})`")
            lines.append("")  # 消息后的空行

        # 格式化玩家选项（如果存在）
        if stage.player_options:
            option_lines = SessionFormatter._format_player_options(stage.player_options)
            lines.extend(option_lines)
            lines.append("")  # 选项后的空行

        # 处理结束信号
        if stage.is_end_signal:
            lines.append("*会话结束*")
            lines.append("")  # 结束信号后的空行

        return lines

    @staticmethod
    def to_markdown(session: Session) -> str:
        """
        使用带有锚点链接的嵌套列表结构将会话对象格式化为 Markdown 字符串，
        便于导航。

        参数:
            session: 要格式化的会话对象。

        返回:
            表示整个会话的 Markdown 格式字符串。
        """
        lines = []

        # 包含会话元数据的标题
        lines.append(f"# 会话: {session.session_id} - {session.main_npc_name}")
        lines.append("") # 标题后的空行

        # 按 sequence_id 排序阶段以确保正确顺序
        sorted_stages = sorted(session.stages.items())

        # 遍历并格式化所有阶段
        for sequence_id, stage in sorted_stages:
            stage_lines = SessionFormatter._format_stage(stage)
            lines.extend(stage_lines)

        # 如果存在末尾空行则移除
        if lines and lines[-1] == "":
            lines.pop()

        return "\n".join(lines)