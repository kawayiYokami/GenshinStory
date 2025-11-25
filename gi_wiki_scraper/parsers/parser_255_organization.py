"""
Parser for Genshin Impact wiki pages under the 'Organization' (组织) category.
ID: 255_organization
"""
from typing import Dict, Any, List, Optional
from bs4.element import Tag
from .base_parser import BaseParser


class Parser255Organization(BaseParser):
    """
    Specific parser for 'Organization' wiki pages.
    Rewritten for clarity and robustness.
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of an organization page.
        """
        soup = self._create_soup(html)
        result = self._initialize_result()

        name_tag = soup.select_one('h1.detail__title')
        if name_tag:
            result["名称"] = name_tag.get_text(strip=True)

        main_content_body = soup.select_one('div.detail__body')
        if not main_content_body:
            return result

        for part_wrap in main_content_body.select('.obc-tmpl-part-wrap'):
            header = part_wrap.select_one('h2.wiki-h2, .obc-tmpl-fold__title, .timeline-title')
            if not header:
                continue

            header_text = header.get_text(strip=True)

            if "简介" in header_text:
                result["简介"] = self._parse_introduction(part_wrap)
            elif "基础信息" in header_text:
                result["基础信息"] = self._parse_basic_info(part_wrap)
            elif "社奉行" in header_text or "天领奉行" in header_text or "勘定奉行" in header_text:
                result["下属机构"].append(self._parse_main_branch(part_wrap))
            elif "趣闻" in header_text:
                result["趣闻"] = self._parse_trivia(part_wrap)
            elif "重大事迹" in header_text:
                result["重大事迹"] = self._parse_timeline(part_wrap)

        return result

    def _initialize_result(self) -> Dict[str, Any]:
        """Initializes the result dictionary."""
        return {
            "名称": "",
            "类型": "组织",
            "简介": {},
            "基础信息": [],
            "下属机构": [],
            "趣闻": [],
            "重大事迹": []
        }

    def _parse_introduction(self, container: Tag) -> Dict[str, Any]:
        """Parses the introduction table."""
        intro_data = {"描述": "", "分支": []}
        table = container.select_one('table')
        if not table:
            return intro_data

        rows = table.select('tr')
        if not rows:
            return intro_data

        # First row is the main description
        desc_cell = rows[0].select_one('td')
        if desc_cell:
            intro_data["描述"] = '\n'.join(p.get_text(strip=True) for p in desc_cell.find_all('p'))

        # Subsequent rows are the branches
        for row in rows[1:]:
            branch_cell = row.select_one('td')
            if branch_cell:
                paragraphs = branch_cell.find_all('p')
                if len(paragraphs) >= 2:
                    intro_data["分支"].append({
                        "名称": paragraphs[0].get_text(strip=True),
                        "描述": paragraphs[1].get_text(strip=True)
                    })
        return intro_data

    def _parse_basic_info(self, container: Tag) -> List[Dict[str, str]]:
        """Parses the basic info image slider."""
        info_list = []
        slider = container.select_one('.mhy-swiper')
        if not slider:
            return info_list

        tabs = slider.select('.swiper-pagination li')
        images = slider.select('.swiper-wrapper .swiper-slide picture source')

        for i, tab in enumerate(tabs):
            entry = {"标题": tab.get_text(strip=True), "图片URL": ""}
            if i < len(images) and images[i].has_attr('srcset'):
                entry["图片URL"] = images[i]['srcset'].split('?')[0]
            info_list.append(entry)

        return info_list

    def _parse_main_branch(self, container: Tag) -> Dict[str, Any]:
        """Parses a main branch like '社奉行', '天领奉行', or '勘定奉行'."""
        title_tag = container.select_one('.obc-tmpl-fold__title span')
        branch_data = {
            "名称": title_tag.get_text(strip=True) if title_tag else "未知分支",
            "描述": "",
            "章节": []
        }

        content_box = container.select_one('.obc-tmpl__paragraph-box')
        if not content_box:
            return branch_data

        # First paragraph is the general description
        first_p = content_box.find('p', recursive=False)
        if first_p:
            branch_data["描述"] = first_p.get_text(strip=True)

        # Subsequent sections are chapters
        current_chapter = None
        for element in content_box.find_all(['h1', 'blockquote', 'p', 'ul'], recursive=False):
            if element.name == 'h1' and 'custom-heading-cls' in element.get('class', []):
                if current_chapter:
                    branch_data["章节"].append(current_chapter)
                current_chapter = {"标题": element.get_text(strip=True), "内容": []}
            elif current_chapter:
                text = element.get_text(strip=True)
                if text:
                    current_chapter["内容"].append(text)

        if current_chapter:
            branch_data["章节"].append(current_chapter)

        return branch_data

    def _parse_trivia(self, container: Tag) -> List[str]:
        """Parses the trivia list."""
        return [li.get_text(strip=True) for li in container.select('.obc-tmpl__paragraph-box ul li')]

    def _parse_timeline(self, container: Tag) -> List[Dict[str, str]]:
        """Parses the timeline of major events."""
        timeline = []
        for event in container.select('.timeline-content__inner'):
            title_tag = event.select_one('h4')
            desc_tag = event.select_one('.timeline-content__inner--desc')
            if title_tag and desc_tag:
                timeline.append({
                    "事件": title_tag.get_text(strip=True),
                    "描述": desc_tag.get_text(strip=True)
                })
        return timeline

    def get_template(self) -> Dict[str, Any]:
        """
        返回组织解析器的JSON模板

        Returns:
            Dict[str, Any]: 组织数据模板
        """
        return {
            "名称": "请填写组织名称",
            "类型": "组织",
            "简介": {
                "描述": "请填写组织描述",
                "分支": [
                    {
                        "名称": "请填写分支名称",
                        "描述": "请填写分支描述"
                    }
                ]
            },
            "基础信息": [
                {
                    "标题": "请填写信息标题",
                    "图片URL": "请填写图片URL"
                }
            ],
            "下属机构": [
                {
                    "名称": "请填写下属机构名称",
                    "描述": "请填写描述",
                    "章节": [
                        {
                            "标题": "请填写章节标题",
                            "内容": [
                                "请填写章节内容1",
                                "请填写章节内容2"
                            ]
                        }
                    ]
                }
            ],
            "趣闻": [
                "请填写趣闻1",
                "请填写趣闻2"
            ],
            "重大事迹": [
                {
                    "事件": "请填写事件名称",
                    "描述": "请填写事件描述"
                }
            ]
        }