from typing import Dict, Any
from dataclasses import dataclass
from astrbot.api.star import Star, Context
from astrbot.api.provider import Provider
from astrbot.api.star.star_metadata import StarMetadata
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig

@register(
    "astrbot_plugin_chat_type",
    "xSapientia",
    "。",
    "0.0.1",
    "https://github.com/xSapientia/chattype",
)

class ChatTypeDetector(Star):
    def __init__(self, context: Context) -> None:
        super().__init__(context)
        self.context = context
        
        logger.info("chat type v0.0.1 加载成功！")

    @filter.command_group([""])  # Matches all messages
    async def on_message(self, event: AstrMessageEvent, context: Context):
        """
        Intercepts all messages to add chat type context
        """
        # Check if this is a group chat by checking if group_id exists
        is_private_result = event.is_private_chat()

        # Determine chat type
        if is_private_result:
            chat_type = "private"
            chat_prompt = "[当前对话识别为[私聊]场景]"
        else:
            chat_type = "group"
            chat_prompt = "[当前对话识别为[群聊]场景]"

        # 获取BOT的消息
        original_message = event.get_messages()

        # 在BOT消息前插入对应提示词
        modified_message = f"{chat_prompt}\n{original_message}"

        # 储存聊天类型文本，兼容其他插件调用
        context.set_property("chat_type", chat_type)
        context.set_property("chat_prompt", chat_prompt)

        # 输出识别日志 (optional)
        logger.info(f"{chat_type} ->消息 {original_message[:50]}...")

        # Continue processing
        return True

def export_star() -> Star:
    """
    Export function required by AstrBot plugin system
    """
    return ChatTypeDetector

# Alternative implementation using middleware pattern













    
    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
    
    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    
    @filter.llm_tool()
    async def detect_chat_type(context: Context, message: AstrBotMessage):
        """
        在LLM请求前检测聊天类型并插入相应提示
        """
        # 获取group_id来判断是否为群聊
        # 根据AstrBot文档，如果是私聊，group_id为None或空
        group_id = event.get_group_id()
        if not group_id:
            return

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
