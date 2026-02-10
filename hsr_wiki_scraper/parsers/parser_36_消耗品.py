from .base_parser import BaseParser
from bs4 import BeautifulSoup

class ConsumableParser(BaseParser):
    """
    用于解析“消耗品”类型页面的解析器。
    """

    def parse(self, html: str) -> dict:
        """
        解析给定的消耗品页面HTML，提取相关信息。
        """

        soup = self._create_soup(html)

        title = self._parse_title(soup)
        metadata = self._parse_metadata(soup)
        description = self._parse_description(soup)

        return {
            "title": title,
            "metadata": metadata,
            "description": description
        }

    def _parse_title(self, soup: BeautifulSoup) -> str:
        title_tag = soup.select_one('h1.detail__title')
        return title_tag.get_text(strip=True) if title_tag else ""

    def _parse_metadata(self, soup: BeautifulSoup) -> dict:
        metadata = {}
        table = soup.select_one('table.material-table--pc')
        if not table:
            return metadata

        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                header_cell = cells[0]
                if 'h3' in header_cell.get('class', []):
                    key = header_cell.get_text(strip=True)
                    value_cell = cells[1]
                    if key == '稀有度':
                        metadata['rarity'] = value_cell.get_text(strip=True)
                    elif key == '类型':
                        metadata['type'] = value_cell.get_text(strip=True)
        return metadata

    def _parse_description(self, soup: BeautifulSoup) -> str:
        table = soup.select_one('table.material-table--pc')
        if not table:
            return ""
        
        header = table.find('td', class_='h3', string='介绍')
        if header:
            value_cell = header.find_next_sibling('td')
            if value_cell:
                return value_cell.get_text(separator='\n', strip=True)
        return ""
