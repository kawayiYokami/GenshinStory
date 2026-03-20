"""
Parser for Genshin Impact wiki pages under the 'Character' (角色) category.
ID: 25_character
"""
from typing import Dict, Any, List
from .base_parser import BaseParser


class Parser25Character(BaseParser):
    """
    Specific parser for 'Character' wiki pages.
    Extracts comprehensive character details including basic info, ascension materials, talents, constellations, stories, etc.
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of a character page.

        Args:
            html (str): The full HTML content of the page.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        soup = self._create_soup(html)

        # Initialize the result dictionary with default values
        result = {
            "名称": "",
            "星级": 0,
            "基础信息": {},
            "命之座": [],
            "角色故事": [],
            "特殊料理": "",
            "生日邮件": [],
            "配音": {
                "汉语": [],
                "日语": [],
                "韩语": [],
                "英语": []
            },
            "角色语音": [],
            "角色关联语音": []
        }

        # 1. Extract basic information
        self._extract_basic_info(soup, result)

        # 2. Extract constellations
        self._extract_constellations(soup, result)

        # 3. Extract character voice lines
        self._extract_character_voices(soup, result)

        # 4. Extract stories, voice lines, mails, media, and timeline
        self._extract_additional_info(soup, result)

        return result

    def _extract_basic_info(self, soup, result: Dict[str, Any]) -> None:
        """Extract basic character information with universal parsing."""
        # Extract name
        name_tag = soup.select_one('.obc-tmp-character__box--title')
        if name_tag:
            result["名称"] = name_tag.get_text(strip=True)

        # Extract rarity
        rarity_icons = soup.select('.obc-tmp-character__box--stars i')
        result["星级"] = len(rarity_icons)

        # Extract all basic information properties universally
        property_items = soup.select('.obc-tmp-character__property .obc-tmp-character__item')
        for item in property_items:
            key_tag = item.select_one('.obc-tmp-character__key')
            value_tag = item.select_one('.obc-tmp-character__value')
            if key_tag and value_tag:
                key = key_tag.get_text(strip=True)
                value = value_tag.get_text(strip=True)

                # Store all key-value pairs in basic info without filtering
                if key and value:
                    result["基础信息"][key] = value





    def _extract_constellations(self, soup, result: Dict[str, Any]) -> None:
        """Extract constellation information."""
        # Find the '命之座' header first
        constellation_header = soup.find('h2', class_='wiki-h2', string='命之座')
        if not constellation_header:
            return

        # Find the table within the same module
        constellation_table = constellation_header.find_next('table')
        if not constellation_table:
            return

        constellation_rows = constellation_table.select('tbody tr')
        constellations = []

        for row in constellation_rows:
            # Selector based on user-provided HTML snippet
            name_tag = row.select_one('td:first-child p:last-of-type')
            desc_tag = row.select_one('td:nth-child(2) p')

            if name_tag and desc_tag:
                name = name_tag.get_text(strip=True)
                description = desc_tag.get_text(strip=True)
                # Ensure we are not picking up empty paragraphs
                if name:
                    constellations.append({
                        "名称": name,
                        "描述": description
                    })

        # Only overwrite if we found actual constellations
        if constellations:
            result["命之座"] = constellations

    def _extract_additional_info(self, soup, result: Dict[str, Any]) -> None:
        """Extract and classify information based on panel titles."""
        # Extract all fold panels
        story_panels = soup.select('.obc-tmpl-fold')

        # Initialize lists for different categories
        character_stories = []
        birthday_mails = []
        voice_lines = []
        associated_voices = []

        for panel in story_panels:
            title_tag = panel.select_one('.obc-tmpl-fold__title span')
            content_tags = panel.select('.obc-tmpl__paragraph-box p')

            if title_tag and content_tags:
                title = title_tag.get_text(strip=True)
                content_parts = [tag.get_text(strip=True) for tag in content_tags]
                content = "\n".join(content_parts)

                # Classify based on title
                if title == "角色CV":
                    self._parse_voice_info(content, result)
                elif title == "特殊料理":
                    result["特殊料理"] = content
                elif title == "生日邮件":
                    self._parse_birthday_mails(panel, result)
                elif title == "角色关联语音":
                    self._parse_associated_voices(content, result)
                else:
                    # All other panels go to character stories
                    character_stories.append({
                        "标题": title,
                        "内容": content
                    })

        result["角色故事"] = character_stories

    def _parse_voice_info(self, content: str, result: Dict[str, Any]) -> None:
        """Parse voice actor information and filter valid entries."""
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Only keep lines containing Chinese, Japanese, English, or Korean indicators
            if any(lang in line for lang in ['中', '日', '英', '韩']):
                # Determine language and extract voice actor name
                if '中' in line:
                    # Extract everything after the language indicator
                    voice_actor = line.split('中', 1)[-1].strip('：: ')
                    if voice_actor:
                        result["配音"]["汉语"].append(voice_actor)
                elif '日' in line:
                    voice_actor = line.split('日', 1)[-1].strip('：: ')
                    if voice_actor:
                        result["配音"]["日语"].append(voice_actor)
                elif '英' in line:
                    voice_actor = line.split('英', 1)[-1].strip('：: ')
                    if voice_actor:
                        result["配音"]["英语"].append(voice_actor)
                elif '韩' in line:
                    voice_actor = line.split('韩', 1)[-1].strip('：: ')
                    if voice_actor:
                        result["配音"]["韩语"].append(voice_actor)

    def _parse_birthday_mails(self, panel, result: Dict[str, Any]) -> None:
        """Parse birthday mail information by splitting on <hr> tags."""
        # Get the raw HTML content from the panel
        content_div = panel.select_one('.obc-tmpl__paragraph-box')
        if not content_div:
            return

        # Split content by <hr> tags
        html_content = str(content_div)

        # Split by <hr> tag and process each section
        sections = html_content.split('<hr>')

        for section in sections:
            if not section.strip():
                continue

            # Create a temporary soup object for this section
            from bs4 import BeautifulSoup
            section_soup = BeautifulSoup(section, 'html.parser')

            # Extract text from all <p> tags in this section
            paragraphs = section_soup.find_all('p')
            if paragraphs:
                mail_content = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text:
                        mail_content.append(text)

                if mail_content:
                    # Join all paragraphs with newlines
                    full_mail = '\n'.join(mail_content)
                    result["生日邮件"].append(full_mail)

    def _parse_associated_voices(self, content: str, result: Dict[str, Any]) -> None:
        """Parse associated voice lines from other characters."""
        lines = content.split('\n')
        current_character = ""
        current_content = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Simple heuristic: if line is short and doesn't contain common punctuation, it might be a character name
            if len(line) < 20 and not any(punct in line for punct in ['。', '！', '？', '，', '…']):
                # Save previous entry if exists
                if current_character and current_content:
                    result["角色关联语音"].append({
                        "角色": current_character,
                        "内容": current_content.strip()
                    })

                # Start new character entry
                current_character = line
                current_content = ""
            else:
                # Accumulate content for current character
                if current_content:
                    current_content += "\n" + line
                else:
                    current_content = line

        # Don't forget the last entry
        if current_character and current_content:
            result["角色关联语音"].append({
                "角色": current_character,
                "内容": current_content.strip()
            })

    def _extract_character_voices(self, soup, result: Dict[str, Any]) -> None:
        """Extract character voice lines from the voice display section."""
        voice_section = soup.select_one('.obc-tmpl-roleVoice')
        if not voice_section:
            return

        # Get the first slide (汉语) since all text content is in Chinese anyway
        first_slide = voice_section.select_one('.swiper-slide')
        if not first_slide:
            return

        # Find the voice table in the first slide
        voice_table = first_slide.select_one('.obc-tmpl-character__voice-pc')
        if not voice_table:
            return

        voice_lines = []
        rows = voice_table.select('tbody tr')

        for row in rows:
            scene_tag = row.select_one('.wiki-h3')
            content_tag = row.select_one('.obc-tmpl-character__voice-content')

            if scene_tag and content_tag:
                scene = scene_tag.get_text(strip=True)
                content = content_tag.get_text(strip=True)

                if scene and content:
                    voice_lines.append({
                        "场景": scene,
                        "内容": content
                    })

        result["角色语音"] = voice_lines

    def get_template(self) -> Dict[str, Any]:
        """
        返回角色解析器的JSON模板

        Returns:
            Dict[str, Any]: 角色数据模板
        """
        return {
            "名称": "请填写角色名称",
            "星级": 5,
            "基础信息": {
                "生日": "请填写生日",
                "所属": "请填写所属",
                "神之眼": "请填写神之眼属性",
                "武器类型": "请填写武器类型",
                "命之座": "请填写命之座",
                "称号": "请填写称号"
            },
            "命之座": [
                {
                    "名称": "请填写命之座名称",
                    "描述": "请填写命之座描述"
                }
            ],
            "角色故事": [
                {
                    "标题": "请填写故事标题",
                    "内容": "请填写故事内容"
                }
            ],
            "特殊料理": "请填写特殊料理",
            "生日邮件": [
                "请填写生日邮件内容"
            ],
            "配音": {
                "汉语": [
                    "请填写汉语配音"
                ],
                "日语": [
                    "请填写日语配音"
                ],
                "韩语": [
                    "请填写韩语配音"
                ],
                "英语": [
                    "请填写英语配音"
                ]
            },
            "角色语音": [
                {
                    "场景": "请填写语音场景",
                    "内容": "请填写语音内容"
                }
            ],
            "角色关联语音": [
                {
                    "角色": "请填写角色名称",
                    "内容": "请填写关联语音内容"
                }
            ]
        }
