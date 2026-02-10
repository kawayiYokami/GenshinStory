from .base_parser import BaseParser
from bs4 import BeautifulSoup

class LightConeParser(BaseParser):
    """
    用于解析"光锥"类型页面的解析器。
    继承自 BaseParser 并实现其 parse 方法。
    """

    def parse(self, html: str) -> dict:
        """
        解析给定的光锥页面HTML，提取相关信息。
        """
        soup = self._create_soup(html)

        title = self._parse_title(soup)
        path = self._parse_path(soup)
        rarity = self._parse_rarity(soup)
        description = self._parse_description(soup)

        return {
            "title": title,
            "path": path,
            "rarity": rarity,
            "description": description
        }

    def _parse_title(self, soup: BeautifulSoup) -> str:
        """提取光锥标题"""
        title_tag = soup.select_one('h1.detail__title')
        return title_tag.get_text(strip=True) if title_tag else ""

    def _parse_path(self, soup: BeautifulSoup) -> str:
        """提取命途信息"""
        return self._extract_table_value(soup, "命途")

    def _parse_rarity(self, soup: BeautifulSoup) -> str:
        """提取稀有度信息"""
        return self._extract_table_value(soup, "稀有度")

    def _parse_description(self, soup: BeautifulSoup) -> str:
        """提取光锥描述"""
        return self._extract_table_value(soup, "光锥描述")

    def _extract_table_value(self, soup: BeautifulSoup, field_name: str) -> str:
        """从表格中提取指定字段的值"""
        # 优先使用mobile版本的表格
        table = soup.select_one('.obc-tml-light-table--mobile')
        if not table:
            # 如果没有mobile表格，使用PC版本
            table = soup.select_one('.obc-tml-light-table--pc')

        if not table:
            return ""

        # 查找包含指定字段名的行
        for row in table.select('tr'):
            cells = row.select('td')
            if len(cells) >= 2:
                field_cell = cells[0]
                value_cell = cells[1]

                if field_cell.get_text(strip=True) == field_name:
                    # 对于描述字段，保留换行符和格式
                    if field_name == "光锥描述":
                        return value_cell.get_text(separator='\n', strip=True)
                    else:
                        return value_cell.get_text(strip=True)

        return ""

    def get_template(self) -> dict:
        """
        返回光锥解析器的JSON模板

        Returns:
            dict: 光锥数据模板
        """
        return {
            "title": "请填写光锥名称",
            "path": "请填写命途",
            "rarity": "请填写稀有度",
            "description": "请填写光锥描述"
        }