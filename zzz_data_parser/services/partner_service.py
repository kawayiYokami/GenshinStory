from typing import List, Dict, Optional
from ..interpreters.partner_interpreter import PartnerInterpreter
from ..interpreters.models.partner import Partner

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