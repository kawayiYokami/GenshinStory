from .base_parser import BaseParser
from bs4 import BeautifulSoup, Tag
import json


class CharacterParser(BaseParser):
    """
    用于解析"角色"类型页面的解析器，专注于提取剧情和语音信息。
    能够智能识别并解析两种不同HTML结构的"角色"页面模板。
    """

    def parse(self, html: str) -> dict:
        """
        解析给定的角色页面HTML，提取剧情和语音相关信息。
        """
        soup = self._create_soup(html)

        # 页面类型识别：通过是否存在"查看全部语音"按钮来判断
        # 由于 central_hub 已经处理了所有交互，我们可以直接检查页面结构
        voice_expand_buttons = soup.select("#module-20 .wiki-btn-all")
        page_type = 1 if voice_expand_buttons else 2

        # 根据页面类型调用不同的解析函数
        if page_type == 1:
            metadata = self._parse_metadata_type1(soup)
            summary = self._parse_summary_type1(soup)
            story = self._parse_story_type1(soup)
            voices = self._parse_voices_type1(soup)
        else:  # page_type == 2
            metadata = self._parse_metadata_type2(soup)
            summary = self._parse_summary_type2(soup)
            story = self._parse_story_type2(soup)
            voices = self._parse_voices_type2(soup)

        title = metadata.get('name', 'Unknown')

        return {
            "title": title,
            "metadata": metadata,
            "summary": summary,
            "story": story,
            "voices": voices
        }

    # --- 类型1页面解析方法 ---

    def _parse_summary_type1(self, soup: BeautifulSoup) -> str:
        """解析角色详情（summary）- 类型1"""
        summary_element = soup.select_one('#module-19 .summary .gt-rich-text')
        return summary_element.get_text(separator='', strip=True) if summary_element else ""

    def _parse_metadata_type1(self, soup: BeautifulSoup) -> dict:
        """解析角色基本信息 - 类型1"""
        metadata = {}
        name_tag = soup.select_one('.role-box__base__name_text')
        if name_tag:
            metadata['name'] = name_tag.get_text(strip=True)

        attrs_container = soup.select_one('.role-box-attrs')
        if attrs_container:
            camp_tag = attrs_container.select_one('.attr-item__left .text')
            if camp_tag:
                metadata['camp'] = camp_tag.get_text(strip=True)
            city_state_tag = attrs_container.select_one('.attr-item__right .text')
            if city_state_tag:
                metadata['city_state'] = city_state_tag.get_text(strip=True)
        return metadata

    def _parse_story_type1(self, soup: BeautifulSoup) -> list:
        """解析角色背景故事 - 类型1"""
        story = []
        story_module = soup.select_one('#module-19 .module-content__list')
        if story_module:
            for item in story_module.select('.list-item'):
                desc_element = item.select_one('.item-desc .gt-rich-text')
                if desc_element:
                    text = desc_element.get_text(separator='\n', strip=True)
                    if text:
                        story.append(text)
        return story

    def _parse_voices_type1(self, soup: BeautifulSoup) -> dict:
        """解析角色语音信息（仅中文）- 类型1"""
        voices = {"chinese_mandarin": []}

        # 解析互动语音
        interaction_container = soup.select_one('.voice-dialog .card-list')
        if interaction_container:
            for item in interaction_container.select('.list-item'):
                title_tag = item.select_one('.item-title')
                desc_tag = item.select_one('.item-desc')
                if title_tag and desc_tag:
                    voices["chinese_mandarin"].append({
                        "title": title_tag.get_text(strip=True),
                        "text": desc_tag.get_text(strip=True)
                    })

        # 解析战斗语音
        combat_container = soup.select_one('#module-20 .module-content > div[tab-key]:nth-of-type(2)')
        if combat_container:
            for item in combat_container.select('.module-content__list[data-index="0"] .list-item'):
                title_tag = item.select_one('.item-title')
                desc_tag = item.select_one('.item-desc')
                if title_tag and desc_tag:
                    voices["chinese_mandarin"].append({
                        "title": title_tag.get_text(strip=True),
                        "text": desc_tag.get_text(strip=True)
                    })
        return voices

    # --- 类型2页面解析方法 ---

    def _parse_metadata_type2(self, soup: BeautifulSoup) -> dict:
        """解析角色基本信息 - 类型2"""
        metadata = {}
        name_tag = soup.select_one('h1.detail__title')
        if name_tag:
            metadata['name'] = name_tag.get_text(strip=True)

        for item in soup.select('.obc-tmp-character__property .obc-tmp-character__item'):
            key_tag = item.select_one('.obc-tmp-character__key')
            value_tag = item.select_one('.obc-tmp-character__value')
            if key_tag and value_tag:
                key = key_tag.get_text(strip=True)
                value = value_tag.get_text(strip=True)
                metadata[key] = value
        return metadata

    def _parse_summary_type2(self, soup: BeautifulSoup) -> str:
        """解析角色详情（summary）- 类型2"""
        story_header = soup.find('h2', string='角色故事')
        if story_header:
            rich_text_div = story_header.find_next_sibling('div', class_='obc-tmpl__rich-text')
            if rich_text_div:
                first_p = rich_text_div.find('p')
                if first_p:
                    return first_p.get_text(strip=True)
        return ""

    def _parse_story_type2(self, soup: BeautifulSoup) -> list:
        """解析角色背景故事 - 类型2"""
        story = []
        story_header = soup.find('h2', string='角色故事')
        if story_header:
            rich_text_div = story_header.find_next_sibling('div', class_='obc-tmpl__rich-text')
            if rich_text_div:
                for details in rich_text_div.find_all('details'):
                    summary_tag = details.find('summary')
                    content_div = details.find('div', class_='expansion-content')
                    if summary_tag and content_div:
                        title = summary_tag.get_text(strip=True)
                        content = content_div.get_text('\n', strip=True)
                        story.append(f"{title}\n{content}")
        return story

    def _parse_voices_type2(self, soup: BeautifulSoup) -> dict:
        """解析角色语音信息（仅中文）- 类型2"""
        voices = {"chinese_mandarin": []}
        voice_headers = soup.find_all('h2', string=['互动语音', '战斗语音'])

        for header in voice_headers:
            table = header.find_next_sibling('table', class_='obc-tmpl-character__voice-pc')
            if table:
                for row in table.find_all('tr'):
                    title_cell = row.find('td', class_='h3')
                    if title_cell:
                        # 内容在标题单元格的下一个兄弟<td>中
                        content_cell = title_cell.find_next_sibling('td')
                        if content_cell:
                            content_div = content_cell.select_one('.obc-tmpl-character__voice-content')
                            if content_div:
                                voices["chinese_mandarin"].append({
                                    "title": title_cell.get_text(strip=True),
                                    "text": content_div.get_text(strip=True)
                                })
        return voices

    def get_template(self) -> dict:
        """
        返回角色解析器的JSON模板

        Returns:
            dict: 角色数据模板
        """
        return {
            "title": "请填写角色名称",
            "metadata": {
                "name": "请填写角色名称",
                "camp": "请填写阵营",
                "city_state": "请填写所属地区"
            },
            "summary": "请填写角色简介",
            "story": [
                "请填写角色故事1",
                "请填写角色故事2"
            ],
            "voices": {
                "chinese_mandarin": [
                    {
                        "title": "请填写语音标题",
                        "text": "请填写语音内容"
                    }
                ]
            }
        }