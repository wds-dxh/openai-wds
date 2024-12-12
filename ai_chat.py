'''
Author: wds-Ubuntu22-cqu wdsnpshy@163.com
Description: 集成版AI聊天助手
'''

import os
import json
import time
from typing import Dict, Any, List, Optional, Generator
from datetime import datetime
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class LLMBase(ABC):
    """LLM基类，定义统一接口"""
    
    @abstractmethod
    def initialize(self) -> None:
        """初始化LLM客户端"""
        pass
    
    @abstractmethod
    def chat(self, user_id: str, message: str, context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """聊天接口"""
        pass
    
    @abstractmethod
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """更新设置"""
        pass
    
    @abstractmethod
    def load_prompt(self, prompt_name: str) -> str:
        """加载提示词"""
        pass
    
    @abstractmethod
    def save_conversation(self, user_id: str, conversation: List[Dict]) -> None:
        """保存对话历史"""
        pass
    
    @abstractmethod
    def get_conversation_history(self, user_id: str) -> List[Dict]:
        """获取对话历史"""
        pass

class ConfigLoader:
    def __init__(self, config_path: str):
        """
        初始化配置加载器
        Args:
            config_path: 配置文件的完整路径
        """
        self.config_path = config_path
        load_dotenv()
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载并验证配置文件"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # 验证必要的配置项
        required_keys = ['openai', 'storage', 'conversation']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration key: {key}")
        
        # 替换环境变量
        config['openai']['api_key'] = os.getenv('OPENAI_API_KEY')
        
        # 确保存储路径是相对于配置文件的路径
        config_dir = os.path.dirname(self.config_path)
        for path_key in ['conversations_path', 'prompts_path']:
            if not os.path.isabs(config['storage'][path_key]):
                config['storage'][path_key] = os.path.normpath(
                    os.path.join(config_dir, config['storage'][path_key])
                )
                
        return config
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self.config
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """更新配置"""
        for key, value in updates.items():
            if key in self.config:
                self.config[key].update(value)

class OpenAIAssistant(LLMBase):
    def __init__(self, config_path: str):
        """
        初始化OpenAI Assistant实例
        Args:
            config_path: 配置文件的完整路径
        """
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.get_config()
        self.client = None
        self.current_role = "default"
        self.conversation_context = {}
        self.max_turns = self.config.get('conversation', {}).get('max_turns', 10)
        self.truncate_mode = self.config.get('conversation', {}).get('truncate_mode', 'sliding')
        self.initialize()
        
    def initialize(self) -> None:
        """初始化OpenAI客户端"""
        self.client = OpenAI(
            api_key=self.config['openai']['api_key'],
            base_url=self.config['openai'].get('base_url', "https://api.chatanywhere.tech"),
            timeout=self.config['openai'].get('timeout', 30),
        )
    
    @retry(
        stop=stop_after_attempt(3),  # 最多重试3次
        wait=wait_exponential(multiplier=1, min=4, max=10),  # 指数退避重试
        reraise=True
    )
    def _make_request(self, messages: List[Dict]) -> Dict:
        """发送请求到OpenAI API，带有重试机制"""
        try:
            response = self.client.chat.completions.create(
                model=self.config['openai']['model'],
                messages=messages,
                temperature=self.config['openai'].get('temperature', 0.7),
                max_tokens=self.config['openai'].get('max_tokens', 1000),
                top_p=self.config['openai'].get('top_p', 1.0)
            )
            return {"success": True, "data": response}
        except Exception as e:
            print(f"API request failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def chat(self, user_id: str, message: str, role_type: Optional[str] = None) -> Dict[str, Any]:
        """
        处理用户消息
        Args:
            user_id: 用户ID
            message: 用户消息
            role_type: 指定的角色类型，如果为None则使用当前角色
        """
        try:
            # 如果指定了新的角色类型，就更新当前角色
            if role_type and role_type != self.current_role:
                if not self.set_role(role_type):
                    return {
                        "error": f"无效的角色类型: {role_type}",
                        "timestamp": datetime.now().isoformat()
                    }

            # 获取当前角色的提示词
            system_prompt = self.load_prompt(self.current_role)
            
            # 获取或初始化用户的上下文
            if user_id not in self.conversation_context:
                self.conversation_context[user_id] = [{"role": "system", "content": system_prompt}]
            else:
                if self.conversation_context[user_id][0]["role"] == "system":
                    self.conversation_context[user_id][0]["content"] = system_prompt
                else:
                    self.conversation_context[user_id].insert(0, {"role": "system", "content": system_prompt})
            
            # 在添加新消息前检查并截断上下文
            if user_id in self.conversation_context:
                self.conversation_context[user_id] = self._truncate_context(
                    self.conversation_context[user_id]
                )
            
            # 添加用户消息
            self.conversation_context[user_id].append({"role": "user", "content": message})
            
            # 使用重试机制发送请求
            response = self._make_request(self.conversation_context[user_id])
            
            if not response["success"]:
                return {
                    "error": response["error"],
                    "timestamp": datetime.now().isoformat()
                }
            
            assistant_message = response["data"].choices[0].message.content
            self.conversation_context[user_id].append({"role": "assistant", "content": assistant_message})
            
            # 保存对话历史
            self.save_conversation(user_id, self.conversation_context[user_id])
            
            return {
                "response": assistant_message,
                "timestamp": datetime.now().isoformat(),
                "current_role": self.current_role
            }
            
        except Exception as e:
            print(f"Chat error: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "current_role": self.current_role
            }

    def _load_prompts(self) -> Dict[str, str]:
        """加载提示词模板"""
        prompts_path = self.config['storage']['prompts_path']
        try:
            with open(prompts_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"警告: 未找到提示词文件 {prompts_path}，创建默认文件")
            os.makedirs(os.path.dirname(prompts_path), exist_ok=True)
            default_prompts = {
                "default": "You are a helpful assistant.",
                "professional": "You are a professional assistant with expertise in various fields.",
                "creative": "You are a creative assistant that helps with brainstorming.",
                "code": "You are a coding assistant that helps with programming.",
                "儿童心理专家": "你是一个儿童心理专家，擅长儿童心理健康和发展指导。",
                "知心大姐姐": "你是一个知心大姐姐，擅长心理疗愈和心理疏导。"
            }
            with open(prompts_path, 'w', encoding='utf-8') as f:
                json.dump(default_prompts, f, indent=4, ensure_ascii=False)
            return default_prompts

    def load_prompt(self, prompt_name: str) -> str:
        """加载指定名称的提示词"""
        prompts = self._load_prompts()
        return prompts.get(prompt_name, prompts["default"])

    def set_role(self, role_type: str) -> bool:
        """
        设置当前角色
        Args:
            role_type: 角色类型
        Returns:
            bool: 是否成功设置角色
        """
        prompts = self._load_prompts()
        if role_type in prompts:
            self.current_role = role_type
            return True
        return False

    def get_current_role(self) -> str:
        """获取当前角色"""
        return self.current_role

    def list_available_roles(self) -> List[str]:
        """获取所有可用的角色类型"""
        try:
            prompts = self._load_prompts()
            return list(prompts.keys())
        except Exception:
            return ["default"]

    def save_conversation(self, user_id: str, conversation: List[Dict]) -> None:
        """保存对话历史到JSON文件"""
        conversations_path = self.config['storage']['conversations_path']
        try:
            os.makedirs(os.path.dirname(conversations_path), exist_ok=True)
            with open(conversations_path, 'r+', encoding='utf-8') as f:
                try:
                    conversations = json.load(f)
                except json.JSONDecodeError:
                    conversations = {}
                
                conversations[user_id] = conversations.get(user_id, []) + [{
                    "timestamp": datetime.now().isoformat(),
                    "messages": conversation
                }]
                
                f.seek(0)
                json.dump(conversations, f, ensure_ascii=False, indent=2)
                f.truncate()
                
        except FileNotFoundError:
            with open(conversations_path, 'w', encoding='utf-8') as f:
                json.dump({user_id: [{
                    "timestamp": datetime.now().isoformat(),
                    "messages": conversation
                }]}, f, ensure_ascii=False, indent=2)

    def get_conversation_history(self, user_id: str) -> List[Dict]:
        """获取用户对话历史"""
        conversations_path = self.config['storage']['conversations_path']
        try:
            with open(conversations_path, 'r', encoding='utf-8') as f:
                conversations = json.load(f)
                return conversations.get(user_id, [])
        except FileNotFoundError:
            return []

    def clear_context(self, user_id: str) -> None:
        """清除指定用户的对话上下文"""
        if user_id in self.conversation_context:
            del self.conversation_context[user_id]

    def get_current_context(self, user_id: str) -> Optional[List[Dict]]:
        """获取指定用户的当前对话上下文"""
        return self.conversation_context.get(user_id)

    def clear_all_contexts(self) -> None:
        """清除所有用户的对话上下文"""
        self.conversation_context.clear()

    def get_context_summary(self, user_id: str) -> Dict[str, Any]:
        """获取用户对话上下文的摘要信息"""
        context = self.conversation_context.get(user_id)
        if not context:
            return {
                "message_count": 0,
                "has_context": False,
                "max_turns": self.max_turns,
                "current_turns": 0
            }
        
        current_turns = (len(context) - 1) // 2  # 不计算system消息
        
        return {
            "message_count": len(context) - 1,
            "has_context": True,
            "current_role": self.current_role,
            "last_message_time": datetime.now().isoformat(),
            "max_turns": self.max_turns,
            "current_turns": current_turns
        }

    def update_settings(self, settings: Dict[str, Any]) -> None:
        """更新设置"""
        if "max_turns" in settings:
            self.max_turns = settings["max_turns"]
        if "truncate_mode" in settings:
            self.truncate_mode = settings["truncate_mode"]

    def _truncate_context(self, context: List[Dict]) -> List[Dict]:
        """
        截断对话上下文
        Args:
            context: 当前上下文
        Returns:
            截断后的上下文
        """
        if len(context) <= 1:  # 只有system消息
            return context
            
        # 计算实际对话轮数（不包括system消息）
        turns = (len(context) - 1) // 2  # 每轮包含一个user消息和一个assistant消息
        
        if turns <= self.max_turns:
            return context
            
        if self.truncate_mode == 'clear':
            # 保留system消息，清除其他所有消息
            return [context[0]]
        else:  # sliding mode
            # 保留system消息和最近的max_turns轮对话
            preserved_messages_count = self.max_turns * 2  # 每轮2条消息
            return [context[0]] + context[-preserved_messages_count:]

    def chat_stream(self, user_id: str, message: str, role_type: Optional[str] = None):
        """
        流式处理用户消息
        Args:
            user_id: 用户ID
            message: 用户消息
            role_type: 指定的角色类型，如果为None则使用当前角色
        Yields:
            生成的文本片段
        """
        try:
            # 如果指定了新的角色类型，就更新当前角色
            if role_type and role_type != self.current_role:
                if not self.set_role(role_type):
                    yield {
                        "error": f"无效的角色类型: {role_type}",
                        "timestamp": datetime.now().isoformat()
                    }
                    return

            # 获取当前角色的提示词
            system_prompt = self.load_prompt(self.current_role)
            
            # 获取或初始化用户的上下文
            if user_id not in self.conversation_context:
                self.conversation_context[user_id] = [{"role": "system", "content": system_prompt}]
            else:
                if self.conversation_context[user_id][0]["role"] == "system":
                    self.conversation_context[user_id][0]["content"] = system_prompt
                else:
                    self.conversation_context[user_id].insert(0, {"role": "system", "content": system_prompt})
            
            # 在添加新消息前检查并截断上下文
            if user_id in self.conversation_context:
                self.conversation_context[user_id] = self._truncate_context(
                    self.conversation_context[user_id]
                )
            
            # 添加用户消息
            self.conversation_context[user_id].append({"role": "user", "content": message})
            
            # 创建流式请求
            stream = self.client.chat.completions.create(
                model=self.config['openai']['model'],
                messages=self.conversation_context[user_id],
                temperature=self.config['openai'].get('temperature', 0.7),
                max_tokens=self.config['openai'].get('max_tokens', 1000),
                top_p=self.config['openai'].get('top_p', 1.0),
                stream=True  # 启用流式传输
            )

            # 用于累积完整的响应
            full_response = ""
            
            # 逐个产出流式响应
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield {
                        "content": content,
                        "type": "content",
                        "timestamp": datetime.now().isoformat(),
                        "current_role": self.current_role
                    }

            # 保存完整的对话到上下文
            self.conversation_context[user_id].append(
                {"role": "assistant", "content": full_response}
            )
            
            # 保存对话历史
            self.save_conversation(user_id, self.conversation_context[user_id])
            
            # 发送完成标记
            yield {
                "type": "done",
                "timestamp": datetime.now().isoformat(),
                "current_role": self.current_role
            }
            
        except Exception as e:
            print(f"Stream chat error: {str(e)}")
            yield {
                "error": str(e),
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "current_role": self.current_role
            }

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

def setup_environment(config_dir=None, data_dir=None):
    """
    设置环境
    Args:
        config_dir: 配置文件目录
        data_dir: 数据文件目录
    """
    if config_dir is None:
        config_dir = os.path.join(os.getcwd(), 'config')
    if data_dir is None:
        data_dir = os.path.join(os.getcwd(), 'data')
        
    config_path = os.path.join(config_dir, 'config.json')
    
    if not os.path.exists(config_path):
        print("未找到配置文件，创建默认配置...")
        config_path = create_default_config(config_dir, data_dir)
    
    return config_path

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

def main(config_dir=None, data_dir=None):
    """主函数"""
    # 设置环境并获取配置文件路径
    config_path = setup_environment(config_dir, data_dir)
    
    # 创建助手实例
    assistant = OpenAIAssistant(config_path)
    user_id = "test_user"
    
    print("欢迎使用AI助手！输入'help'查看命令列表，输入'exit'或'quit'退出。")
    print(f"当前角色: {assistant.get_current_role()}")
    print_help()
    
    # 设置默认角色
    assistant.set_role("儿童心理专家")
    print(f"已切换到角色: {assistant.get_current_role()}")
    
    while True:
        try:
            user_input = input("\n您: ").strip()
            
            # 处理特殊命令
            if user_input.lower() in ['exit', 'quit']:
                print("再见！")
                break
            elif user_input.lower() == 'help':
                print_help()
                continue
            # ... (其他命令处理保持不变)
            # 为了简洁，这里省略了其他命令处理代码
            
            time_now = time.time()
            
            # 使用流式接口
            print("\nAI: ", end="", flush=True)
            response_stream = assistant.chat_stream(user_id, user_input)
            process_stream_response(response_stream)
            
            # 输出回复的延迟
            print(f"回复延迟: {time.time() - time_now:.2f}秒")
                
        except KeyboardInterrupt:
            print("\n\n程序被中断。再见")
            break
        except Exception as e:
            print(f"\n发生错误: {str(e)}")
            print("请重试...")

if __name__ == "__main__":
    # 使用默认目录
    main()
    
    # 或者使用自定义目录
    # main(
    #     config_dir="/path/to/your/config",
    #     data_dir="/path/to/your/data"
    # ) 