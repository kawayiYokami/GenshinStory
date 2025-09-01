from typing import Dict, List
from ..models.partner import Partner
from ..dataloader import ZZZDataLoader

class PartnerInterpreter:
    """
    Interpreter for parsing partner (character) data from the game's text map.
    """

    def __init__(self):
        """
        Initializes the interpreter by loading the text map and partner config data.
        """
        self.data_loader = ZZZDataLoader(gender='M', player_name='哲')
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
            impression_f = self.text_map.get(config['impression_f_key'], '')
            impression_m = self.text_map.get(config['impression_m_key'], '')
            birthday = self.text_map.get(config['birthday_key'], '')
            camp_ids = config.get('camp_ids', [])
            camp_name = self.text_map.get(config.get('camp_key', ''), '')

            # Map gender ID to string
            gender_map = {1: "男", 2: "女"}
            gender = gender_map.get(config.get('gender'), "未知")

            partner = Partner(
                id=partner_id,
                name=name,
                outlook_desc=outlook_desc,
                profile_descs=profile_descs,
                impression_f=impression_f,
                impression_m=impression_m,
                true_name=config['true_name'],
                birthday=birthday,
                camp_ids=camp_ids,
                gender=gender,
                icon_path=config.get('icon_path', ''),
                gacha_splash_path=config.get('gacha_splash_path', ''),
                camp=camp_name
            )
            partners.append(partner)

        return partners