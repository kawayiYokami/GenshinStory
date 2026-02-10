"""
HTML Preprocessor for Genshin Impact Wiki pages.

This module provides functions to clean and simplify the raw HTML content 
retrieved from the wiki before it's passed to the parsers.
"""

from bs4 import BeautifulSoup, Tag

def preprocess_html(html_content: str) -> Tag | None:
    """
    Cleans the raw HTML content to extract the main content body and remove clutter.

    Args:
        html_content (str): The raw HTML of the page.

    Returns:
        BeautifulSoup | None: A BeautifulSoup object representing the cleaned main 
                                content area, or None if the main content area 
                                cannot be found.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. Locate the core content area.
    # The order of classes is important, as some pages might have multiple.
    main_content = soup.find('div', class_='detail__body') or \
                   soup.find('div', class_='obc-tmpl-rich-text-content') or \
                   soup.find('div', class_='main-content') # Fallback

    if not main_content:
        print("Warning: Main content area not found in HTML.")
        return None

    # 2. Remove all <img> tags from the main content.
    for img_tag in main_content.find_all('img'):
        img_tag.decompose()

    # 3. Clear 'data-data' attributes from all tags within the main content.
    # These often contain redundant or complex data not needed for parsing.
    for data_tag in main_content.find_all(attrs={"data-data": True}):
        data_tag['data-data'] = ""
        
    # 4. Remove script and style tags
    for s in main_content.select('script, style'):
        s.decompose()

    return main_content