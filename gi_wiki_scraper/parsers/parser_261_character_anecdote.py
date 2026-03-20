"""
Parser for Genshin Impact wiki pages under the 'Character Anecdote' (角色逸闻) category.
ID: 261_character_anecdote
"""
from typing import Dict, Any, List, Optional
from bs4.element import Tag
from .base_parser import BaseParser


class Parser261CharacterAnecdote(BaseParser):
    """
    Specific parser for 'Character Anecdote' wiki pages.
    Rewritten for clarity, robustness, and maintainability.
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses the HTML content of a character anecdote page.
        """
        soup = self._create_soup(html)

        result = self._initialize_result()

        # Get the title from the main h1 tag
        title_tag = soup.select_one('h1.detail__title')
        if title_tag:
            result["标题"] = title_tag.get_text(strip=True)

        # Initialize a variable to hold the pure character name
        pure_character_name = ""

        main_content_body = soup.select_one('div.detail__body')
        if not main_content_body:
            return result

        # Iterate over each distinct content block, which can be 'obc-tmpl-part-wrap' or 'obc-tmpl-part'.
        # This handles both the old structure (wrapped in part-wrap) and the new structure (direct part).
        for module in main_content_body.select('.obc-tmpl-part-wrap, .obc-tmpl-part'):
            # Try multiple selectors for the header
            header = module.select_one('.obc-tmpl-fold__title, h1.wiki-h1, h2.wiki-h2, .title-box .title, .timeline-title')
            if not header:
                continue

            header_text = header.get_text(strip=True)

             # Dispatch based on the header text from within each block
            if "基本信息" in header_text:
                pure_character_name = self._parse_basic_info(module, result)
            elif "逸闻纪事" in header_text:
                result["逸闻纪事"].extend(self._parse_generic_modules(module, pure_character_name))
            elif "剧情彩蛋" in header_text:
                result["剧情彩蛋"].extend(self._parse_generic_modules(module, pure_character_name))
            elif "角色洞天" in header_text:
                self._parse_character_home_dialogue(module, result, pure_character_name)
            elif "角色赠礼" in header_text:
                self._parse_character_home_gifts(module, result, pure_character_name)
            elif "七圣召唤" in header_text:
                result["七圣召唤"].extend(self._parse_generic_modules(module, pure_character_name))
            elif "幻想真境剧诗" in header_text:
                result["幻想真境剧诗"].extend(self._parse_generic_modules(module, pure_character_name))
            elif "生日" in header_text: # Birthday mails have a simple "生日" title
                result["生日邮件"].extend(self._parse_birthday_mail(module, pure_character_name))

        # Clean up any empty dictionaries that might result from modules with titles but no content
        for key in ["逸闻纪事", "剧情彩蛋", "七圣召唤", "幻想真境剧诗"]:
            result[key] = [item for item in result[key] if item]

        return result

    def _initialize_result(self) -> Dict[str, Any]:
        """Initializes the result dictionary with a clean structure."""
        return {
            "标题": "", "类型": "角色逸闻", "基本信息": {"角色名称": ""},
            "逸闻纪事": [], "剧情彩蛋": [], "角色洞天": [], "角色赠礼": [],
            "七圣召唤": [], "幻想真境剧诗": [], "生日邮件": []
        }

    def _parse_basic_info(self, container: Tag, result: Dict[str, Any]) -> str:
        """Extracts basic character information from its specific container."""
        info_table = container.select_one('.obc-tmpl-character-table--pc')
        if not info_table: return ""

        # Find rows containing specific keys and extract their sibling values
        name_row = info_table.find(lambda tag: tag.name == 'td' and '角色名' in tag.get_text(strip=True))
        pure_character_name = ""
        if name_row and name_row.find_next_sibling('td'):
            pure_character_name = name_row.find_next_sibling('td').get_text(strip=True)
            result["基本信息"]["角色名称"] = pure_character_name

        birthday_row = info_table.find(lambda tag: tag.name == 'td' and '生日' in tag.get_text(strip=True))
        if birthday_row and birthday_row.find_next_sibling('td'):
            result["基本信息"]["生日"] = birthday_row.find_next_sibling('td').get_text(strip=True)

        affiliation_row = info_table.find(lambda tag: tag.name == 'td' and '所属' in tag.get_text(strip=True))
        if affiliation_row and affiliation_row.find_next_sibling('td'):
            result["基本信息"]["所属"] = affiliation_row.find_next_sibling('td').get_text(strip=True)

        intro_row = info_table.find(lambda tag: tag.name == 'td' and '角色介绍' in tag.get_text(strip=True))
        if intro_row and intro_row.find_next_sibling('td'):
            result["基本信息"]["角色介绍"] = intro_row.find_next_sibling('td').get_text(strip=True)

        return pure_character_name

    def _parse_generic_modules(self, container: Tag, character_name: str) -> List[Dict[str, Any]]:
        """Parses generic content modules that share a common structure within a container."""
        modules_data = []
        # Find all foldable sections within this part_wrap
        for module in container.select('.obc-tmpl-fold'):
            module_data = {"标题": "", "简介": "", "相关奖励": [], "对话": []}
            title_tag = module.select_one('.obc-tmpl-fold__title span')
            if title_tag:
                module_data["标题"] = title_tag.get_text(strip=True)
            else:
                continue

            info_table = module.select_one('.obc-tmpl-richBaseInfo table')
            if info_table:
                for row in info_table.select('tbody tr'):
                    cells = row.find_all('td')
                    if len(cells) < 2: continue
                    key, value_cell = cells[0].get_text(strip=True), cells[1]
                    if "简介" in key: module_data["简介"] = value_cell.get_text(strip=True)
                    elif "相关奖励" in key: module_data["相关奖励"] = self._parse_rewards(value_cell)

            dialogue_section = module.select_one('.obc-tmpl-interactiveDialogue .tree-node')
            if dialogue_section: module_data["对话"] = self._parse_dialogue_tree(dialogue_section, character_name)

            modules_data.append(module_data)
        return modules_data

    def _parse_character_home_dialogue(self, container: Tag, result: Dict[str, Any], character_name: str) -> None:
        """Parses the 'Character Home' dialogue from its specific container."""
        dialogue_section = container.select_one('.obc-tmpl-interactiveDialogue .tree-node')
        if dialogue_section:
            dialogue_data = self._parse_dialogue_tree(dialogue_section, character_name)
            if dialogue_data:
                result["角色洞天"].append({
                    "标题": "角色洞天对话", "简介": "", "相关奖励": [], "对话": dialogue_data
                })

    def _parse_character_home_gifts(self, container: Tag, result: Dict[str, Any], pure_character_name: str) -> None:
        """Parses the character gift sets table from its specific container."""
        gift_table = container.select_one('table')
        if not gift_table: return

        for row in gift_table.select('tbody tr'):
            cells = row.find_all('td')
            if len(cells) != 3: continue
            set_name_cell, rewards_cell, dialogue_cell = cells
            set_name_tag = set_name_cell.select_one('.custom-entry-wrapper .name')
            set_name = set_name_tag.get_text(strip=True) if set_name_tag else "未知套装"
            rewards = self._parse_rewards(rewards_cell)
            dialogue_text = '\n'.join(p.get_text(strip=True) for p in dialogue_cell.select('p'))
            # Use the pure character name for gift dialogues
            dialogue_entry = [{"角色": pure_character_name, "内容": dialogue_text}] if dialogue_text else []
            result["角色赠礼"].append({
                "标题": f"角色赠礼 - {set_name}", "简介": "", "相关奖励": rewards, "对话": dialogue_entry
            })

    def _parse_birthday_mail(self, container: Tag, character_name: str) -> List[Dict[str, Any]]:
        """Parses birthday mail modules from their specific container."""
        mails_data = []
        for module in container.select('.obc-tmpl-fold'):
            mail_data = {"标题": "", "发件人": "", "时间": "", "内容": ""}
            title_tag = module.select_one('.obc-tmpl-fold__title span')
            if title_tag:
                mail_data["标题"] = title_tag.get_text(strip=True)

            info_table = module.select_one('.obc-tmpl-richBaseInfo table')
            if info_table:
                info_dict = {cells[0].get_text(strip=True): cells[1].get_text(strip=True)
                             for row in info_table.select('tbody tr') if (cells := row.find_all('td')) and len(cells) >= 2}
                mail_data.update({
                    "发件人": info_dict.get("发件人", ""), "时间": info_dict.get("时间", ""), "内容": info_dict.get("内容", "")
                })

            if mail_data.get("标题"):
                mails_data.append(mail_data)
        return mails_data

    def _parse_rewards(self, container: Tag) -> List[Dict[str, int]]:
        """Helper function to parse material/reward items."""
        rewards = []
        for item in container.select('.obc-tmpl__material-item, .custom-entry-wrapper'):
            name_tag = item.select_one('.obc-tmpl__material-name, .name')
            num_tag = item.select_one('.obc-tmpl__material-num, .amount')
            name = name_tag.get_text(strip=True) if name_tag else ""
            num_str = num_tag.get_text(strip=True) if num_tag else "0"
            quantity = self._safe_int(num_str, 0)
            if name: rewards.append({"名称": name, "数量": quantity})
        return rewards

    def _parse_dialogue_tree(self, node: Tag, character_name: str) -> List[Dict[str, Any]]:
        """Recursively parses a dialogue tree structure robustly."""
        branches = []
        children = node.find_all(recursive=False)
        i = 0
        while i < len(children):
            child = children[i]
            if 'option-item' in child.get('class', []):
                branch = {"选项": "", "对话内容": [], "子分支": []}
                option_tag = child.select_one('.option-content span')
                branch["选项"] = option_tag.get_text(strip=True) if option_tag else ""
                i += 1
                if i < len(children) and 'content-box' in children[i].get('class', []):
                    branch["对话内容"] = self._parse_dialogue_content(children[i], character_name)
                    i += 1
                if i < len(children) and 'tree-node' in children[i].get('class', []):
                    branch["子分支"] = self._parse_dialogue_tree(children[i], character_name)
                else: i -=1
                branches.append(branch)
            elif 'content-box' in child.get('class', []):
                branches.extend(self._parse_dialogue_content(child, character_name))
            i += 1
        return branches

    def _parse_dialogue_content(self, content_box: Tag, character_name: str) -> List[Dict[str, Optional[str]]]:
        """Parses p-tags within a content-box into dialogues."""
        dialogues = []
        for p_tag in content_box.find_all('p'):
            text = p_tag.get_text(strip=True)
            if not text: continue
            if '：' in text:
                parts = text.split('：', 1)
                speaker = parts[0].strip()
                content = parts[1].strip()
                # Special handling for "奥兹" with parentheses, which indicates a status rather than speech
                if speaker == "奥兹" and content.startswith("("):
                    # "奥兹" is not speaking, it's a status description, treated as narration
                    speaker = "旁白"
                    content = text
                dialogues.append({"角色": speaker, "内容": content})
            else:
                # If no colon, assume the character_name is the speaker
                dialogues.append({"角色": character_name, "内容": text})
        return dialogues

    def get_template(self) -> Dict[str, Any]:
        """
        返回角色逸闻解析器的JSON模板

        Returns:
            Dict[str, Any]: 角色逸闻数据模板
        """
        return {
            "标题": "请填写标题",
            "类型": "角色逸闻",
            "基本信息": {
                "角色名称": "请填写角色名称",
                "生日": "请填写生日",
                "所属": "请填写所属",
                "角色介绍": "请填写角色介绍"
            },
            "逸闻纪事": [
                {
                    "标题": "请填写逸闻标题",
                    "简介": "请填写简介",
                    "相关奖励": [
                        {
                            "名称": "请填写奖励名称",
                            "数量": 1
                        }
                    ],
                    "对话": [
                        {
                            "角色": "请填写角色",
                            "内容": "请填写对话内容"
                        }
                    ]
                }
            ],
            "剧情彩蛋": [
                {
                    "标题": "请填写剧情彩蛋标题",
                    "简介": "请填写简介",
                    "相关奖励": [
                        {
                            "名称": "请填写奖励名称",
                            "数量": 1
                        }
                    ],
                    "对话": [
                        {
                            "角色": "请填写角色",
                            "内容": "请填写对话内容"
                        }
                    ]
                }
            ],
            "角色洞天": [
                {
                    "标题": "请填写角色洞天标题",
                    "简介": "请填写简介",
                    "相关奖励": [
                        {
                            "名称": "请填写奖励名称",
                            "数量": 1
                        }
                    ],
                    "对话": [
                        {
                            "角色": "请填写角色",
                            "内容": "请填写对话内容"
                        }
                    ]
                }
            ],
            "角色赠礼": [
                {
                    "标题": "请填写角色赠礼标题",
                    "简介": "请填写简介",
                    "相关奖励": [
                        {
                            "名称": "请填写奖励名称",
                            "数量": 1
                        }
                    ],
                    "对话": [
                        {
                            "角色": "请填写角色",
                            "内容": "请填写对话内容"
                        }
                    ]
                }
            ],
            "七圣召唤": [
                {
                    "标题": "请填写七圣召唤标题",
                    "简介": "请填写简介",
                    "相关奖励": [
                        {
                            "名称": "请填写奖励名称",
                            "数量": 1
                        }
                    ],
                    "对话": [
                        {
                            "角色": "请填写角色",
                            "内容": "请填写对话内容"
                        }
                    ]
                }
            ],
            "幻想真境剧诗": [
                {
                    "标题": "请填写幻想真境剧诗标题",
                    "简介": "请填写简介",
                    "相关奖励": [
                        {
                            "名称": "请填写奖励名称",
                            "数量": 1
                        }
                    ],
                    "对话": [
                        {
                            "角色": "请填写角色",
                            "内容": "请填写对话内容"
                        }
                    ]
                }
            ],
            "生日邮件": [
                {
                    "标题": "请填写生日邮件标题",
                    "发件人": "请填写发件人",
                    "时间": "请填写时间",
                    "内容": "请填写邮件内容"
                }
            ]
        }