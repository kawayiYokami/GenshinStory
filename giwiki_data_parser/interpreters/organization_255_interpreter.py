import logging
from typing import List, Dict, Any, Optional

from giwiki_data_parser.models.organization_255 import Organization, OrganizationBranch
from giwiki_data_parser.services.dataloader import DataLoader

class OrganizationInterpreter:
    """组织解释器"""
    
    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.logger = logging.getLogger(__name__)
    
    def interpret(self, data: Dict[str, Any]) -> Optional[Organization]:
        """解析单个组织数据 - 公共接口"""
        return self._interpret_single(data)
    
    def interpret_all(self) -> List[Organization]:
        """解析所有组织数据"""
        organizations = []
        raw_data_iterator = self.loader.get_organizations()
        
        for data in raw_data_iterator:
            try:
                # 从数据中获取文件路径信息
                file_path = data.get("_file_path", "")
                organization = self._interpret_single(data, file_path)
                if organization:
                    organizations.append(organization)
            except Exception as e:
                self.logger.error(f"解析组织数据时出错: {e}")
        
        self.logger.info(f"成功解析 {len(organizations)} 个组织")
        return organizations
    
    def _interpret_single(self, data: Dict[str, Any], file_path: str = "") -> Optional[Organization]:
        """解析单个组织数据"""
        try:
            # 解析简介信息
            intro_data = data.get("简介", {})
            summary = intro_data.get("描述") if isinstance(intro_data, dict) else None
            
            # 解析分支信息
            branches = []
            if isinstance(intro_data, dict):
                branch_list = intro_data.get("分支", [])
                for branch_data in branch_list:
                    if isinstance(branch_data, dict):
                        branch = OrganizationBranch(
                            name=branch_data.get("名称", ""),
                            description=branch_data.get("描述", "")
                        )
                        branches.append(branch)
            
            # 解析其他信息
            subordinates_raw = data.get("下属机构", [])
            anecdotes = data.get("趣闻", [])
            major_events_raw = data.get("重大事迹", [])
            
            # 处理下属机构 - 可能是字典格式
            subordinates = []
            if subordinates_raw:
                for item in subordinates_raw:
                    if isinstance(item, dict):
                        # 如果是字典，提取名称和描述
                        name = item.get("名称", "")
                        desc = item.get("描述", "")
                        if name:
                            subordinates.append(f"{name}: {desc}" if desc else name)
                    elif isinstance(item, str) and item.strip():
                        subordinates.append(item.strip())
            
            # 处理重大事迹 - 可能是字典格式
            major_events = []
            if major_events_raw:
                for item in major_events_raw:
                    if isinstance(item, dict):
                        # 如果是字典，提取事件和描述
                        event = item.get("事件", "")
                        desc = item.get("描述", "")
                        if event:
                            major_events.append(f"{event}: {desc}" if desc else event)
                    elif isinstance(item, str) and item.strip():
                        major_events.append(item.strip())
            
            # 过滤空列表
            anecdotes = [item for item in anecdotes if item] if anecdotes else []
            
            # 创建组织对象
            organization = Organization(
                name=data.get("名称", ""),
                org_type=data.get("类型"),
                summary=summary,
                branches=branches,
                subordinates=subordinates,
                anecdotes=anecdotes,
                major_events=major_events
            )
            
            # 从文件路径设置ID
            if file_path:
                organization.set_id_from_filename(file_path)
            elif "_file_path" in data:
                organization.set_id_from_filename(data["_file_path"])
            elif "_file_id" in data:
                file_id = str(data["_file_id"])
                if file_id.isdigit():
                    organization.id = file_id
                else:
                    self.logger.warning(f"非数字文件ID，跳过: {file_id}")
                    return None
            
            return organization
            
        except Exception as e:
            self.logger.error(f"解析单个组织数据时出错: {e}")
            return None