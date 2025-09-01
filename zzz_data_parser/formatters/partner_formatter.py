from typing import Dict
from ..models.partner import Partner

class PartnerFormatter:
    """
    伙伴对象格式化器，用于转换为各种输出格式。
    """

    @staticmethod
    def to_markdown(partner: Partner) -> str:
        """
        将伙伴对象格式化为 Markdown 字符串。

        参数:
            partner: 要格式化的伙伴对象。

        返回:
            表示伙伴的 Markdown 格式字符串。
        """
        lines = []
        lines.append(f"# {partner.name}")
        lines.append("")
        lines.append(f"**ID**: {partner.id}")
        lines.append("")

        if partner.true_name:
            lines.append(f"**英文名**: {partner.true_name}")
            lines.append("")

        if partner.birthday:
            lines.append(f"**生日**: {partner.birthday}")
            lines.append("")

        if partner.outlook_desc:
            lines.append("## 外貌描述")
            lines.append(partner.outlook_desc)
            lines.append("")

        if partner.profile_descs:
            lines.append("## 档案")
            for i, desc in enumerate(partner.profile_descs):
                if len(partner.profile_descs) > 1:
                    lines.append(f"### 档案 {i+1}")
                lines.append(desc)
                lines.append("")

        if partner.impression_f or partner.impression_m:
            lines.append("## 印象")
            if partner.impression_f:
                lines.append(f"**玲**: {partner.impression_f}")
            if partner.impression_m:
                lines.append(f"**哲**: {partner.impression_m}")
            lines.append("")

        return "\n".join(lines)
    @staticmethod
    def to_dict(partner: Partner) -> Dict[str, any]:
        """
        将伙伴对象转换为字典。

        参数:
            partner: 要转换的伙伴对象。

        返回:
            伙伴的字典表示。
        """
        return {
            "id": partner.id,
            "name": partner.name,
            "true_name": partner.true_name,
            "birthday": partner.birthday,
            "outlook_desc": partner.outlook_desc,
            "profile_descs": partner.profile_descs,
            "impression_f": partner.impression_f,
            "impression_m": partner.impression_m
        }