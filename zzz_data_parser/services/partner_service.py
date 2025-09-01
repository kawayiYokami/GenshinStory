from typing import List, Dict, Optional, Any
from ..interpreters.partner_interpreter import PartnerInterpreter
from ..models.partner import Partner
from ..formatters.partner_formatter import PartnerFormatter

class PartnerService:
    """
    Service layer for accessing partner (character) data.
    This service handles parsing and caching of partner data.
    """

    _instance: Optional['PartnerService'] = None
    _partners: Optional[List[Partner]] = None
    _partner_map: Optional[Dict[str, Partner]] = None

    def __new__(cls) -> 'PartnerService':
        """
        Singleton pattern implementation. Ensures only one instance of the service exists.
        """
        if cls._instance is None:
            cls._instance = super(PartnerService, cls).__new__(cls)
        return cls._instance

    def _load_data(self) -> None:
        """
        Loads and parses partner data using the PartnerInterpreter.
        This method initializes the internal cache.
        """
        if self._partners is None:
            interpreter = PartnerInterpreter()
            self._partners = interpreter.parse()
            # Create a map for quick ID-based lookups
            self._partner_map = {partner.id: partner for partner in self._partners}

    def get_partner_by_id(self, partner_id: str) -> Optional[Partner]:
        """
        Retrieves a partner by its unique ID.

        Args:
            partner_id: The ID of the partner to retrieve.

        Returns:
            The Partner object if found, otherwise None.
        """
        self._load_data()
        return self._partner_map.get(partner_id)

    def list_partner_ids(self) -> List[str]:
        """
        Retrieves a list of all available partner IDs.

        Returns:
            A list of partner IDs.
        """
        self._load_data()
        return list(self._partner_map.keys()) if self._partner_map else []

    def get_partner_as_markdown(self, partner_id: str) -> str:
        """
        生成伙伴的 Markdown 表示。

        参数:
            partner_id: 伙伴的 ID。

        返回:
            表示伙伴的 Markdown 字符串。
        """
        partner = self.get_partner_by_id(partner_id)
        if not partner:
            return f"# 伙伴 {partner_id} 未找到"

        # 使用 PartnerFormatter 生成 Markdown
        return PartnerFormatter.to_markdown(partner)

    def get_tree(self) -> List[Dict[str, Any]]:
        """
        Generate a tree structure for partners, categorized by camp.

        Returns:
            A list of dictionaries representing the tree structure.
        """
        self._load_data()
        if not self._partners:
            return []

        # Create a dictionary to hold camps
        camps: Dict[str, List[Dict[str, Any]]] = {}

        # Categorize partners by their camp name
        for partner in self._partners:
            camp_name = partner.camp or "未知阵营"

            if camp_name not in camps:
                camps[camp_name] = []

            # Add partner to the appropriate camp
            camps[camp_name].append({
                "id": partner.id,
                "name": partner.name,
                "type": "partner"
            })

        # Convert to the required format
        tree = []
        for camp_name, partners in camps.items():
            if partners:  # Only add camps that have partners
                tree.append({
                    "name": camp_name,
                    "children": partners
                })

        return tree