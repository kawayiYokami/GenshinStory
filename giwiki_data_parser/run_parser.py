#!/usr/bin/env python3
"""
GI Wiki数据解析器主执行脚本
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from giwiki_data_parser.main import GIWikiDataParser

def setup_logging(log_level: str = "INFO"):
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('giwiki_parser.log', encoding='utf-8')
        ]
    )

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='GI Wiki数据解析器')
    
    parser.add_argument(
        '--data-path', 
        default='gi_wiki_scraper/output/structured_data',
        help='Wiki数据路径 (默认: gi_wiki_scraper/output/structured_data)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='output',
        help='输出目录 (默认: output)'
    )
    
    parser.add_argument(
        '--cache-dir',
        default='giwiki_data_parser/cache',
        help='缓存目录 (默认: giwiki_data_parser/cache)'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='不使用缓存'
    )
    
    parser.add_argument(
        '--no-markdown',
        action='store_true',
        help='不生成Markdown文件'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别 (默认: INFO)'
    )
    
    parser.add_argument(
        '--categories',
        nargs='+',
        help='指定要处理的数据类别 (例如: 261_角色逸闻 68_书籍)'
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # 检查数据路径是否存在
        if not os.path.exists(args.data_path):
            logger.error(f"数据路径不存在: {args.data_path}")
            sys.exit(1)
        
        logger.info("启动GI Wiki数据解析器...")
        logger.info(f"数据路径: {args.data_path}")
        logger.info(f"输出目录: {args.output_dir}")
        logger.info(f"缓存目录: {args.cache_dir}")
        logger.info(f"使用缓存: {not args.no_cache}")
        logger.info(f"生成Markdown: {not args.no_markdown}")
        
        if args.categories:
            logger.info(f"指定处理类别: {', '.join(args.categories)}")
        
        # 创建解析器实例
        wiki_parser = GIWikiDataParser(
            data_path=args.data_path,
            cache_dir=args.cache_dir
        )
        
        # 运行解析
        parsed_data = wiki_parser.run(
            use_cache=not args.no_cache,
            generate_md=not args.no_markdown,
            output_dir=args.output_dir,
            categories=args.categories
        )
        
        # 输出统计信息
        logger.info("解析完成！统计信息：")
        for category, items in parsed_data.items():
            logger.info(f"  {category}: {len(items)} 项")
        
        logger.info("GI Wiki数据解析器执行完成！")
        
    except KeyboardInterrupt:
        logger.info("用户中断执行")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()