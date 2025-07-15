from typing import List, Dict, Any

def package_list_as_self_describing(
    items: List[Dict[str, Any]], 
    item_type: str,
    name_key: str = "name",
    title_key: str = "title"
) -> List[Dict[str, Any]]:
    """
    一个可复用的包装器。
    接收一个简单的列表和类型字符串，返回统一的自描述结构。
    每个列表项都将包含一个 'data' 字段，其中含有类型和ID。

    :param items: 原始字典列表。
    :param item_type: 要分配给每个项目的数据类型 (例如, 'weapon')。
    :param name_key: 用于项目名称的字典键。
    :param title_key: 当 name_key 不存在时，备用的项目标题键。
    :return: 包装后的字典列表。
    """
    packaged_list = []
    for item in items:
        item_id = item.get("id")
        # 优先使用 name_key，然后是 title_key
        item_name = item.get(name_key) or item.get(title_key)
        
        if item_id is not None and item_name is not None:
            packaged_list.append({
                "id": item_id,
                "name": item_name,
                "data": {"type": item_type, "id": item_id}
            })
    return packaged_list

def convert_to_frontend_tree(
    service_tree: List[Dict[str, Any]], 
    leaf_type: str, 
    id_prefix: str
) -> List[Dict[str, Any]]:
    """
    通用函数，将任何 get_tree() 的输出转换为前端 Tree 控件所需的格式。
    """
    frontend_tree = []
    
    # 递归函数来处理每个节点
    def process_node(node: Dict[str, Any], current_prefix: str, parent_type: str) -> Dict[str, Any]:
        node_id = node.get("id")
        node_title = node.get("title")
        children = node.get("children", [])
        
        # 确定当前节点的类型
        # 如果有子节点，它是一个'category'。如果没有，它是一个'leaf'。
        current_type = parent_type if children else leaf_type

        # 构建前端节点
        frontend_node = {
            "key": f"{current_prefix}-{node_id}",
            "label": node_title,
            "data": {"type": current_type, "id": node_id},
            "children": [process_node(child, current_type, leaf_type) for child in children]
        }
        
        # 如果没有子节点，标记为 isLeaf
        if not frontend_node["children"]:
            frontend_node["isLeaf"] = True
            
        return frontend_node

    # 遍历顶层分类
    for category_node in service_tree:
        category_id = category_node.get("id")
        
        frontend_category_node = {
            "key": f"{id_prefix}-{category_id}",
            "label": category_node.get("title"),
            "data": {"type": id_prefix, "id": category_id},
            "children": [
                process_node(child, id_prefix, id_prefix) 
                for child in category_node.get("children", [])
            ]
        }
        frontend_tree.append(frontend_category_node)
        
    return frontend_tree