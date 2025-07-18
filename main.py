from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
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
    def __init__(self, context: Context):
        super().__init__(context)
        
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

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
