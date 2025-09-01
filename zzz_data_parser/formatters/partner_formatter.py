from typing import Dict
from ..interpreters.models.partner import Partner

class PartnerFormatter:
    """
    Formatter for converting Partner objects into various output formats.
    """

    @staticmethod
    def to_markdown(partner: Partner) -> str:
        """
        Formats a Partner object into a Markdown string.

        Args:
            partner: The Partner object to format.

        Returns:
            A Markdown formatted string representing the partner.
        """
        lines = []
        lines.append(f"# 角色: {partner.name} (ID: {partner.id})")
        lines.append("")

        if partner.true_name:
            lines.append(f"**真名**: {partner.true_name}")
            lines.append("")

        if partner.birthday:
            lines.append(f"**生日**: {partner.birthday}")
            lines.append("")

        if partner.outlook_desc:
            lines.append("## 外观描述")
            lines.append(partner.outlook_desc)
            lines.append("")

        if partner.profile_descs:
            lines.append("## 角色简介")
            for i, desc in enumerate(partner.profile_descs):
                # If there's more than one profile desc, label them
                if len(partner.profile_descs) > 1:
                    lines.append(f"### 简介 {i+1}")
                lines.append(desc)
                lines.append("")

        if partner.impression_f or partner.impression_m:
            lines.append("## 印象")
            if partner.impression_f:
                lines.append(f"- **玲的印象**: {partner.impression_f}")
            if partner.impression_m:
                lines.append(f"- **哲的印象**: {partner.impression_m}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_dict(partner: Partner) -> Dict[str, any]:
        """
        Converts a Partner object into a dictionary.

        Args:
            partner: The Partner object to convert.

        Returns:
            A dictionary representation of the partner.
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