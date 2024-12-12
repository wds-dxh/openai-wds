'''
Author: wds-Ubuntu22-cqu wdsnpshy@163.com
Date: 2024-12-13 01:42:15
Description: 
邮箱：wdsnpshy@163.com 
Copyright (c) 2024 by ${wds-Ubuntu22-cqu}, All Rights Reserved. 
'''
import os
from openai_wds import create_assistant
from examples.create_config import create_default_config

def setup_environment():
    """设置环境"""
    # 检查配置文件是否存在，不存在则创建
    config_dir = os.path.join(os.getcwd(), 'config')
    config_path = os.path.join(config_dir, 'config.json')
    
    if not os.path.exists(config_path):
        print("未找到配置文件，创建默认配置...")
        create_default_config()
    
    return config_path

def chat_demo():
    """聊天演示"""
    # 设置环境
    config_path = setup_environment()
    
    # 创建助手实例
    assistant = create_assistant(config_path)
    
    # 设置用户ID
    user_id = "demo_user"
    
    # 设置角色
    assistant.set_role("儿童心理专家")
    print(f"当前角色: {assistant.get_current_role()}")
    
    # 开始对话
    while True:
        try:
            # 获取用户输入
            user_input = input("\n您: ").strip()
            
            # 检查退出命令
            if user_input.lower() in ['exit', 'quit']:
                print("再见！")
                break
                
            # 使用流式输出获取回复
            print("AI: ", end="", flush=True)
            for chunk in assistant.chat_stream(user_id, user_input):
                if "error" in chunk:
                    print(f"\n错误: {chunk['error']}")
                    break
                    
                if chunk["type"] == "content":
                    print(chunk["content"], end="", flush=True)
                elif chunk["type"] == "done":
                    print()  # 换行
                    
        except KeyboardInterrupt:
            print("\n\n程序被中断。")
            break
        except Exception as e:
            print(f"\n发生错误: {str(e)}")

if __name__ == "__main__":
    chat_demo() 