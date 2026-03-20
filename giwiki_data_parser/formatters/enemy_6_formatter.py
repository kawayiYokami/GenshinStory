from giwiki_data_parser.models.enemy_6 import Enemy

class EnemyFormatter:
    """敌人格式化器"""
    
    def format(self, item: Enemy) -> str:
        """将敌人对象格式化为Markdown字符串"""
        if not isinstance(item, Enemy):
            return ""
        
        md = []
        
        # 标题
        md.append(f"# {item.name}")
        md.append("")
        
        # 基本信息
        if item.element:
            md.append(f"**元素属性**: {item.element}")
            md.append("")
        
        # 攻击方式
        if item.attack_methods:
            md.append("## 攻击方式")
            md.append("")
            for method in item.attack_methods:
                md.append(f"- {method}")
            md.append("")
        
        # 背景故事
        if item.background_story:
            md.append("## 背景故事")
            md.append("")
            # 处理长段落，按句号分段以提高可读性
            story = item.background_story.strip()
            if len(story) > 200:
                # 如果故事很长，尝试按句号分段
                sentences = story.split('。')
                formatted_story = []
                current_paragraph = ""
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    if len(current_paragraph + sentence) > 150:
                        if current_paragraph:
                            formatted_story.append(current_paragraph + "。")
                            current_paragraph = sentence
                        else:
                            formatted_story.append(sentence + "。")
                    else:
                        if current_paragraph:
                            current_paragraph += "。" + sentence
                        else:
                            current_paragraph = sentence
                
                if current_paragraph:
                    formatted_story.append(current_paragraph + ("。" if not current_paragraph.endswith("。") else ""))
                
                for paragraph in formatted_story:
                    md.append(paragraph)
                    md.append("")
            else:
                md.append(story)
                md.append("")
        
        return '\n'.join(md)