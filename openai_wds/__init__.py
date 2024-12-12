"""
OpenAI Assistant
~~~~~~~~~~~~~~~

A flexible OpenAI API wrapper with multi-role support and context management.
"""

import os
from .assistants.openai_assistant import OpenAIAssistant

__version__ = '0.1.0'

# 获取包的默认配置目录
DEFAULT_CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'config')
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# 提供便捷的工厂函数
def create_assistant(config_path=None):
    """
    创建OpenAI助手实例的便捷方法
    
    Args:
        config_path: 可选的配置文件路径，如果不提供则使用默认配置
    
    Returns:
        OpenAIAssistant实例
    """
    if config_path is None:
        config_path = os.path.join(DEFAULT_CONFIG_DIR, 'config.json')
    return OpenAIAssistant(config_path)

# 导出主要的类和函数
__all__ = ['OpenAIAssistant', 'create_assistant'] 