# -*- coding: utf-8 -*-
"""
日志设置模块
提供一个全局配置好的logger，可以同时输出到控制台和文件。
"""
import logging
from logging.handlers import RotatingFileHandler
import sys
from src.config import LOG_DIR

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
LOG_FILENAME = LOG_DIR / "scraper.log"

def setup_logging(log_level=logging.INFO):
    """
    配置并返回一个日志记录器。

    该函数会设置一个全局的日志系统，包含两种处理器：
    1. StreamHandler: 将日志信息输出到标准输出（控制台）。
    2. RotatingFileHandler: 将日志信息写入文件，并支持日志轮转，
       单个文件最大1MB，最多保留5个备份文件。

    Args:
        log_level (int): 日志记录的级别，默认为 logging.INFO。

    Returns:
        logging.Logger: 配置好的根日志记录器。
    """
    # 获取根logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # 如果已经有处理器了，就先移除，防止重复添加
    if logger.hasHandlers():
        logger.handlers.clear()

    # 1. 创建控制台处理器
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(stream_handler)

    # 2. 创建文件处理器（带轮转功能）
    # maxBytes: 单个文件最大大小
    # backupCount: 最多保留的备份文件数
    file_handler = RotatingFileHandler(
        LOG_FILENAME, maxBytes=1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)

    logging.info("日志系统初始化完成。")
    return logger
