from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from astrbot.api.provider import ProviderRequest

@register(
    "astrbot_plugin_chat_type",
    "xSapientia",
    "帮助区分私聊和群聊的插件",
    "0.0.1",
    "https://github.com/xSapientia/chattype",
)
class ChatTypeDetector(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        # 正确的配置加载方式
        self.config = config if config else AstrBotConfig()
        # 设置默认配置
        if not self.config:
            self.config = {
                "enable_plugin": True,
                "group_prompt": "[群聊环境] 切换为群聊模式",
                "private_prompt": "[私聊环境] 切换为私聊模式"
            }
        logger.info("Chat Type Detector v0.0.1 加载成功！")

    @filter.on_llm_request()
    async def add_chat_type_prompt(self, event: AstrMessageEvent, req: ProviderRequest):
        """
        在LLM请求前添加聊天类型提示到系统提示词中
        """
        # 检查插件是否启用
        if not self.config.get("enable_plugin", True):
            return

        try:
            # 检测聊天类型
            group_id = event.get_group_id()
            is_group_chat = group_id is not None

            # 选择对应的提示词
            if is_group_chat:
                chat_type = "group"
                chat_prompt = self.config.get("group_prompt")
                logger.debug(f"检测到群聊，群组ID: {group_id}")
            else:
                chat_type = "private"
                chat_prompt = self.config.get("private_prompt")
                logger.debug(f"检测到私聊，用户ID: {event.get_sender_id()}")

            # 在系统提示词中添加聊天类型提示
            if req.system_prompt:
                req.system_prompt = f"{chat_prompt}\n\n{req.system_prompt}"
            else:
                req.system_prompt = chat_prompt

            # 存储聊天类型信息到事件的额外信息中
            event.set_extra("chat_type", chat_type)
            event.set_extra("chat_prompt", chat_prompt)

            logger.info(f"已为{chat_type}聊天添加环境提示")

        except Exception as e:
            logger.error(f"添加聊天类型提示时出错: {e}")

    @filter.command("chattype")
    async def check_chat_type(self, event: AstrMessageEvent):
        """查看当前聊天类型"""
        group_id = event.get_group_id()
        if group_id:
            yield event.plain_result(f"当前是群聊环境\n群组ID: {group_id}")
        else:
            yield event.plain_result(f"当前是私聊环境\n用户ID: {event.get_sender_id()}")

    async def terminate(self):
        """插件卸载时调用"""
        logger.info("Chat Type Detector 插件已卸载")
