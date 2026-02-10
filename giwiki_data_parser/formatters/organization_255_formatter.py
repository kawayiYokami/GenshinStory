from giwiki_data_parser.models.organization_255 import Organization, OrganizationBranch

class OrganizationFormatter:
    """组织格式化器"""
    
    def format(self, item: Organization) -> str:
        """将组织对象格式化为Markdown字符串"""
        if not isinstance(item, Organization):
            return ""
        
        md = []
        
        # 标题
        md.append(f"# {item.name}")
        md.append("")
        
        # 组织简介（如果有引言，用引用格式）
        if item.summary:
            # 检查是否包含引言格式（带有——）
            if "——" in item.summary:
                # 分离引言和出处
                parts = item.summary.split("——")
                if len(parts) >= 2:
                    quote = parts[0].strip()
                    source = "——".join(parts[1:]).strip()
                    md.append(f"> {quote}")
                    md.append(f"> {source}")
                else:
                    md.append(f"> {item.summary}")
            else:
                md.append(item.summary)
            md.append("")
        
        # 基本信息表格
        md.append("## 基本信息")
        md.append("")
        md.append("| 项目 | 内容 |")
        md.append("|------|------|")
        md.append(f"| 组织名称 | {item.name} |")
        
        if item.org_type:
            md.append(f"| 组织类型 | {item.org_type} |")
        
        md.append("")
        
        # 组织特性/分支信息
        if item.branches:
            md.append("## 组织特性")
            md.append("")
            md.append("| 特性 | 描述 |")
            md.append("|------|------|")
            
            for branch in item.branches:
                md.append(f"| **{branch.name}** | {branch.description} |")
            
            md.append("")
        
        # 下属机构
        if item.subordinates:
            md.append("## 下属机构")
            md.append("")
            for subordinate in item.subordinates:
                md.append(f"- {subordinate}")
            md.append("")
        
        # 趣闻
        if item.anecdotes:
            md.append("## 趣闻")
            md.append("")
            for anecdote in item.anecdotes:
                md.append(f"- {anecdote}")
            md.append("")
        
        # 重大事迹
        if item.major_events:
            md.append("## 重大事迹")
            md.append("")
            for event in item.major_events:
                md.append(f"- {event}")
            md.append("")
        
        return '\n'.join(md)