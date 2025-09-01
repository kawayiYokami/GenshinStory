from typing import List, Dict, Optional
from ..interpreters.vhs_collection_interpreter import VHSCollectionInterpreter
from ..models.vhs_collection import VHSCollection


class VHSCollectionService:
    """
    Service layer for accessing VHS Collection data.
    This service handles parsing and caching of VHS Collection data.
    """

    _instance: Optional['VHSCollectionService'] = None
    _vhs_collections: Optional[List[VHSCollection]] = None
    _vhs_collection_map: Optional[Dict[int, VHSCollection]] = None

    def __new__(cls) -> 'VHSCollectionService':
        """
        Singleton pattern implementation. Ensures only one instance of the service exists.
        """
        if cls._instance is None:
            cls._instance = super(VHSCollectionService, cls).__new__(cls)
        return cls._instance

    def _load_data(self) -> None:
        """
        Loads and parses VHS Collection data using the VHSCollectionInterpreter.
        This method initializes the internal cache.
        """
        if self._vhs_collections is None:
            interpreter = VHSCollectionInterpreter()
            self._vhs_collections = interpreter.parse()
            # Create a map for quick ID-based lookups
            self._vhs_collection_map = {vhs.id: vhs for vhs in self._vhs_collections}

    def get_vhs_collection_by_id(self, vhs_id: int) -> Optional[VHSCollection]:
        """
        Retrieves a VHS Collection item by its unique ID.

        Args:
            vhs_id: The ID of the VHS Collection item to retrieve.

        Returns:
            The VHSCollection object if found, otherwise None.
        """
        self._load_data()
        return self._vhs_collection_map.get(vhs_id)

    def list_vhs_collection_ids(self) -> List[int]:
        """
        Retrieves a list of all available VHS Collection item IDs.

        Returns:
            A list of VHS Collection item IDs.
        """
        self._load_data()
        return list(self._vhs_collection_map.keys()) if self._vhs_collection_map else []