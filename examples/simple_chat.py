from openai_wds import create_assistant

def main():
    # 使用默认配置创建助手
    assistant = create_assistant()
    
    # 或者使用自定义配置
    # assistant = create_assistant('path/to/your/config.json')
    
    response = assistant.chat("user123", "你好")
    print(response["response"])

if __name__ == "__main__":
    main() 