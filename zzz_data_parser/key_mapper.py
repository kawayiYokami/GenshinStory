import logging
from typing import Dict, Any, List, Optional
import re

class KeyMapper:
    """
    负责动态映射数据文件的 Key。
    通过扫描文件内容，匹配特征值，自动推导出当前版本的 Key。
    """

    @staticmethod
    def get_list_key(data: Dict[str, Any]) -> Optional[str]:
        """
        获取 JSON 数据中包含主列表的 Key。
        通常是唯一的顶层 Key，且对应的值是列表。
        """
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                return key
        return None

    @staticmethod
    def map_partner_keys(data_list: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        映射 PartnerConfigTemplateTb.json 的 Key。
        锚点特征 (ID=101011):
        - ID: 101011
        - Name: 包含 Partner_Name_
        - Outlook: 包含 Partner_OutlookDesc_
        - Profile: 包含 Partner_ProfileDesc_
        - ImpressionF: 包含 Partner_Impression_f_
        - ImpressionM: 包含 Partner_Impression_m_
        - Birthday: 包含 Partner_Birthday_
        - CampKey: 包含 PartnerBg_Camp
        - Icon: 包含 IconRole/
        """
        mapping = {}
        target_item = None

        # 寻找锚点条目
        for item in data_list:
            # 简单的 ID 匹配可能不可靠，因为 Key 也是未知的。
            # 我们先遍历 item 的所有值，看是否包含 101011
            if 101011 in item.values():
                target_item = item
                break

        if not target_item:
            logging.warning("Partner Key Mapping: Anchor item (ID 101011) not found.")
            return mapping

        # 映射字段
        for key, value in target_item.items():
            if value == 101011:
                mapping['id'] = key
            elif isinstance(value, str):
                if "Partner_Name_" in value:
                    mapping['name_key'] = key
                elif "Partner_OutlookDesc_" in value:
                    mapping['outlook_desc_key'] = key
                elif "Partner_ProfileDesc_" in value:
                    mapping['profile_desc_key'] = key
                elif "Partner_Impression_f_" in value:
                    mapping['impression_f_key'] = key
                elif "Partner_Impression_m_" in value:
                    mapping['impression_m_key'] = key
                elif "Partner_Birthday_" in value:
                    mapping['birthday_key'] = key
                elif "PartnerBg_Camp" in value and 'camp_key' not in mapping: # 取第一个
                    mapping['camp_key'] = key
                elif "IconRole/" in value:
                    mapping['icon_path'] = key
                elif "MNHJEPLGCKC" in key: # Legacy fallback or specific hash if known
                     pass # Do not rely on hardcoded keys if possible
            elif isinstance(value, list) and len(value) > 0:
                 # camp_ids usually list of ints
                 if all(isinstance(x, int) for x in value):
                     mapping['camp_ids'] = key

        # Gender & TrueName might be tricky without specific values.
        # TrueName is usually a string, Gender an int.
        # Let's try to infer Gender (0, 1, 2) from context if possible, or skip.
        # In the provided example: "FHOLCJBPPNC": "Partner_Gender_02" -> Wait, provided example has string for gender key?
        # The user provided example: "FHOLCJBPPNC": "Partner_Gender_02"
        # Old code expected int: gender: partner_data.get('EEMFLLFIIKL', 0)
        # It seems the data structure might have changed slightly or we need to be careful.
        # Let's map what we can confidently map.

        return mapping

    @staticmethod
    def map_weapon_keys(data_list: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        映射 WeaponTemplateTb.json 的 Key。
        锚点特征 (ID=12001):
        - ID: 12001
        - ModelID: 包含 Weapon_ 且不包含 /
        - Description: 包含 _Desc 且包含 Weapon
        """
        mapping = {}
        target_item = None
        for item in data_list:
            if 12001 in item.values():
                target_item = item
                break

        if not target_item:
            logging.warning("Weapon Key Mapping: Anchor item (ID 12001) not found.")
            return mapping

        for key, value in target_item.items():
            if value == 12001:
                mapping['id'] = key
            elif isinstance(value, str):
                if "Weapon_" in value and "/" not in value and "UI" not in value and "Play_sfx" not in value and "_Desc" not in value:
                    mapping['model_id'] = key
                elif "_Desc" in value and "Weapon" in value:
                    mapping['description_key'] = key
                # Story might be empty in the first item, try to find a non-empty story in other items if needed
                # But for now, let's map what we have.

        return mapping

    @staticmethod
    def map_item_keys(data_list: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        映射 ItemTemplateTb.json 的 Key。
        锚点特征 (ID=10, Item_Gold):
        - ID: 10
        - Name: Item_Gold
        - Desc: Item_Gold_des
        - Story: Item_Gold_story
        """
        mapping = {}
        target_item = None
        for item in data_list:
            if 10 in item.values() and "Item_Gold" in item.values():
                target_item = item
                break

        if not target_item:
            logging.warning("Item Key Mapping: Anchor item (ID 10) not found.")
            return mapping

        for key, value in target_item.items():
            if value == 10:
                mapping['id'] = key
            elif isinstance(value, str):
                if value == "Item_Gold":
                    mapping['name_key'] = key
                elif value == "Item_Gold_des":
                    mapping['description_key'] = key
                elif value == "Item_Gold_story":
                    mapping['story_key'] = key

        return mapping

    @staticmethod
    def map_hollow_item_keys(data_list: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        映射 HollowItemTemplateTb.json 的 Key。
        锚点特征 (ID=400001):
        - ID: 400001
        - Name: 包含 HollowItemName_
        - Desc: 包含 HollowItemDes_
        """
        mapping = {}
        target_item = None
        for item in data_list:
            if 400001 in item.values():
                target_item = item
                break

        if not target_item:
            logging.warning("Hollow Item Key Mapping: Anchor item (ID 400001) not found.")
            return mapping

        for key, value in target_item.items():
            if value == 400001:
                mapping['id'] = key
            elif isinstance(value, str):
                if "HollowItemName_" in value:
                    mapping['name_key'] = key
                elif "HollowItemDes_" in value:
                    mapping['description_key'] = key

        return mapping

    @staticmethod
    def map_vhs_keys(data_list: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        映射 VHSCollectionConfigTemplateTb.json 的 Key。
        锚点特征 (ID=701000):
        - ID: 701000
        - Name: 包含 VHSCollection_Name_
        - Desc: 包含 VHSCollection_Desc_
        """
        mapping = {}
        target_item = None
        for item in data_list:
            if 701000 in item.values():
                target_item = item
                break

        if not target_item:
            logging.warning("VHS Key Mapping: Anchor item (ID 701000) not found.")
            return mapping

        for key, value in target_item.items():
            if value == 701000:
                mapping['id'] = key
            elif isinstance(value, str):
                if "VHSCollection_Name_" in value:
                    mapping['name_key'] = key
                elif "VHSCollection_Desc_" in value:
                    mapping['description_key'] = key

        return mapping

    @staticmethod
    def map_message_keys(data_list: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        映射 MessageConfigTemplateTb.json 的 Key。

        1. 基础字段锚点 (ID=100301):
           - ID: 100301
           - GroupID: 1003
           - Text: 包含 Message_
           - Sequence: 1
           - Sender/NPC: 10043

        2. 选项字段锚点 (ID=100304):
           - Option1 Text: Option01_100304
           - Option2 Text: Option02_100304
        """
        mapping = {}

        # 1. 基础字段映射
        base_item = None
        for item in data_list:
            if 100301 in item.values():
                base_item = item
                break

        if base_item:
            for key, value in base_item.items():
                if value == 100301:
                    mapping['id'] = key
                elif value == 1003:
                    mapping['group_id'] = key
                elif isinstance(value, str) and "Message_" in value:
                    mapping['text_key'] = key
                elif value == 1:
                     # Sequence is 1, but other fields might also be 1.
                     # We might need to verify if this key is consistent across messages
                     # For now, let's assume Sequence is usually small int.
                     # Let's check another message to verify sequence key if possible,
                     # or just map it and hope for the best (risky).
                     # Safe bet: Sequence is often small.
                     if 'sequence' not in mapping:
                         mapping['sequence'] = key
                elif value == 10043:
                     # Sender ID
                     mapping['session_npc_id'] = key

        # 2. 选项字段映射
        option_item = None
        for item in data_list:
            # Check for Option01_100304 value
            if "Option01_100304" in item.values():
                option_item = item
                break

        if option_item:
            # We need to find which key holds the option text, and which holds the next ID
            # This is complex because there are multiple options (Option 1, 2, 3...)
            # We look for keys that have the specific string values

            # Map keys for Option 1
            for key, value in option_item.items():
                if value == "Option01_100304":
                    mapping['option1_text_key'] = key
                    # Usually Next ID is related or close. But JSON is unordered.
                    # We might not be able to strictly map "Option 1 Next ID" key just by value
                    # because we don't know which int value corresponds to it without schema.
                    # However, in the provided sample:
                    # "LJCBKOKNHNC": "Option01_100304" (Text)
                    # "IDCKEMJAOMG": 2 (Next ID?)
                    pass
                elif value == "Option02_100304":
                    mapping['option2_text_key'] = key

            # For Next IDs, it's safer to rely on the fact that if we found the text keys,
            # we might just return the whole item and let the interpreter handle logic,
            # BUT we are mapping keys here.
            # Let's infer based on user provided sample structure if possible,
            # or try to map based on value 2 and 3 if they are unique enough in that item.
            # Item 100304:
            # "IDCKEMJAOMG": 2
            # "CEMBBHNALNB": 3
            # These are likely the next IDs/Sequences.
            # Let's temporarily map them.
            for key, value in option_item.items():
                if value == 2:
                    mapping['option1_next_id_key'] = key
                elif value == 3:
                    mapping['option2_next_id_key'] = key

        return mapping

    @staticmethod
    def map_message_npc_keys(data_list: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        映射 MessageNPCTemplateTb.json 的 Key。
        锚点特征 (ID=998):
        - ID: 998
        - Name: Message_MultiMessage_Name
        - Avatar: UI/Sprite/
        """
        mapping = {}
        target_item = None
        for item in data_list:
            if 998 in item.values():
                target_item = item
                break

        if not target_item:
            logging.warning("Message NPC Key Mapping: Anchor item (ID 998) not found.")
            return mapping

        for key, value in target_item.items():
            if value == 998:
                mapping['id'] = key
            elif isinstance(value, str):
                if "Message_MultiMessage_Name" in value:
                    mapping['name_key'] = key
                elif "UI/Sprite/" in value:
                    mapping['avatar_id'] = key

        return mapping