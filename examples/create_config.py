import os
import json
from pathlib import Path

def create_default_config(config_dir: str = None, data_dir: str = None) -> str:
    """
    创建默认配置文件
    Args:
        config_dir: 配置文件目录，默认为当前目录下的config
        data_dir: 数据文件目录，默认为当前目录下的data
    Returns:
        str: 配置文件的完整路径
    """
    if config_dir is None:
        config_dir = os.path.join(os.getcwd(), 'config')
    if data_dir is None:
        data_dir = os.path.join(os.getcwd(), 'data')
    
    # 确保目录存在
    os.makedirs(config_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    
    # 计算相对路径
    rel_data_dir = os.path.relpath(data_dir, config_dir)
    
    # 默认配置
    default_config = {
        "openai": {
            "api_key": "${OPENAI_API_KEY}",
            "base_url": "http://127.0.0.1:11434/v1",
            "model": "qwen2.5:0.5b",
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 1.0,
            "timeout": 60
        },
        "storage": {
            "conversations_path": os.path.join(rel_data_dir, 'conversations.json'),
            "prompts_path": os.path.join(rel_data_dir, 'prompts.json')
        },
        "conversation": {
            "max_turns": 10,
            "truncate_mode": "sliding"
        }
    }
    
    # 创建配置文件
    config_path = os.path.join(config_dir, 'config.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=4)
    
    return config_path

if __name__ == "__main__":
    # 在当前目录下创建配置
    create_default_config()