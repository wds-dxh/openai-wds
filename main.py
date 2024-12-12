'''
Author: wds-Ubuntu22-cqu wdsnpshy@163.com
Date: 2024-12-12 16:38:09
Description: 
邮箱：wdsnpshy@163.com 
Copyright (c) 2024 by ${wds-Ubuntu22-cqu}, All Rights Reserved. 
'''
import time
from openai_wds import create_assistant  # 使用新的导入路径
import sys

def print_help():
    """打印帮助信息"""
    print("\n=== 命令列表 ===")
    print("exit/quit: 退出程序")
    print("help: 显示帮助信息")
    print("clear: 清除当前对话历史")
    print("history: 显示历史对话")
    print("role: 显示当前角色")
    print("roles: 显示所有可用角色")
    print("role <type>: 切换角色 (例如: role professional)")
    print("context: 显示当前对话上下文信息")
    print("set_turns <number>: 设置最大对话轮数")
    print("set_truncate <mode>: 设置截断模式 (sliding/clear)")
    print("================\n")

def process_stream_response(response_stream):
    """处理流式响应"""
    full_response = ""
    for response in response_stream:
        if "error" in response:
            print(f"\n错误: {response['error']}")
            return
        
        if response["type"] == "content":
            print(response["content"], end="", flush=True)
            full_response += response["content"]
        elif response["type"] == "done":
            print()  # 换行
            return full_response

def main():
    assistant = create_assistant()
    user_id = "test_user"
    
    print("欢迎使用AI助手！输入'help'查看命令列表，输入'exit'或'quit'退出。")
    print(f"当前角色: {assistant.get_current_role()}")
    print_help()
    
    # 设置角色
    assistant.set_role("儿童心理专家")
    print(f"当前角色: {assistant.get_current_role()}")
    
    while True:
        try:
            user_input = input("\n您: ").strip()
            
            # 处理特殊命令
            if user_input.lower() in ['exit', 'quit']:  # 退出程序
                print("再见！")
                sys.exit(0)
            elif user_input.lower() == 'help':  # 打印帮助信息
                print_help()
                continue
            elif user_input.lower() == 'clear':  # 清除对话历史
                assistant.clear_context(user_id)
                print("对话历史已清除！")
                continue
            elif user_input.lower() == 'context':  # 显示当前对话信息
                summary = assistant.get_context_summary(user_id)
                print("\n=== 当前对话信息 ===")
                print(f"消息数量: {summary['message_count']}")
                print(f"是否有上下文: {'是' if summary['has_context'] else '否'}")
                print(f"当前角色: {summary.get('current_role', 'default')}")
                print(f"当前��话轮数: {summary['current_turns']}/{summary['max_turns']}")
                if summary['has_context']:
                    print(f"最后更新时间: {summary['last_message_time']}")
                print("==================")
                continue
            elif user_input.lower() == 'role':  # 显示当前角色
                print(f"当前角色: {assistant.get_current_role()}")
                continue
            elif user_input.lower() == 'roles':  # 显示所有可用角色
                roles = assistant.list_available_roles()
                print("\n可用角色:")
                for role in roles:
                    print(f"- {role}")
                continue
            elif user_input.lower().startswith('role '):  # 切换角色
                new_role = user_input.split(' ')[1].strip()
                if assistant.set_role(new_role):
                    print(f"已切换到角色: {new_role}")
                else:
                    print(f"切换角色失败: {new_role} 不是有效的角色类型")
                continue
            elif user_input.lower() == 'history':  # 显示历史对话
                history = assistant.get_conversation_history(user_id)
                print("\n=== 历史对话 ===")
                for conv in history:
                    print(f"\n时间: {conv['timestamp']}")
                    for msg in conv['messages']:
                        if msg['role'] != 'system':
                            prefix = "AI: " if msg['role'] == 'assistant' else "您: "
                            print(f"{prefix}{msg['content']}")
                print("\n==============")
                continue
            elif user_input.lower().startswith('set_turns '):  # 设置最大对话轮数
                try:
                    turns = int(user_input.split(' ')[1])
                    if turns < 1:
                        print("对话轮数必须大于0")
                    else:
                        assistant.update_settings({"max_turns": turns})
                        print(f"已设置最大对话轮数为: {turns}")
                except ValueError:
                    print("请输入有效的数字")
                continue
            elif user_input.lower().startswith('set_truncate '):  # 设置截断模式，sliding:滑动截断，clear:清除截断
                mode = user_input.split(' ')[1].strip()
                if mode not in ['sliding', 'clear']:
                    print("无效的截断模式，请使用 'sliding' 或 'clear'")
                else:
                    assistant.update_settings({"truncate_mode": mode})
                    print(f"已设置截断模式为: {mode}")
                continue
            elif not user_input:  # 如果用户输入为空，则跳过 
                continue
            
            time_now = time.time()
            
            # 使用流式接口
            print("\nAI: ", end="", flush=True)
            response_stream = assistant.chat_stream(user_id, user_input)
            process_stream_response(response_stream)
            
            # 输出回复的延迟
            print(f"回复延迟: {time.time() - time_now:.2f}秒")
                
        except KeyboardInterrupt:
            print("\n\n程序被中断。再见！")
            sys.exit(0)
        except Exception as e:
            print(f"\n发生错误: {str(e)}")
            print("请重试...")

if __name__ == "__main__":
    main() 