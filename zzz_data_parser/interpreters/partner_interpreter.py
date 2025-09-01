from typing import Dict, List
from .models.partner import Partner
from ..dataloader import ZZZDataLoader

class PartnerInterpreter:
    """
    Interpreter for parsing partner (character) data from the game's text map.
    """

    def __init__(self):
        """
        Initializes the interpreter by loading the text map and partner config data.
        """
        self.data_loader = ZZZDataLoader()
        self.text_map = self.data_loader.get_text_map()

    def parse(self) -> List[Partner]:
        """
        Uses partner configuration data to accurately parse character information.

        Returns:
            A list of Partner objects.
        """
        partner_config = self.data_loader.get_partner_config()
        if not partner_config:
            return []

        partners = []
        for partner_id, config in partner_config.items():
            # 从配置中获取键，然后从text_map中获取值
            name = self.text_map.get(config['name_key'], '')
            outlook_desc = self.text_map.get(config['outlook_desc_key'], '')
            profile_descs = [self.text_map.get(config['profile_desc_key'], '')]
            # 注意：这里需要处理 _1, _2 等后缀，但配置中只给了基础键
            impression_f = self.text_map.get(config['impression_f_key'], '')
            impression_m = self.text_map.get(config['impression_m_key'], '')
            birthday = self.text_map.get(config['birthday_key'], '')

            partner = Partner(
                id=partner_id,
                name=name,
                outlook_desc=outlook_desc,
                profile_descs=profile_descs,
                impression_f=impression_f,
                impression_m=impression_m,
                true_name=config['true_name'], # 新增字段
                birthday=birthday # 新增字段
            )
            partners.append(partner)

        return partners