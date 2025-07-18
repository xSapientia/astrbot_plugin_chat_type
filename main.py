from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig

@register(
    "astrbot_plugin_chat_type",
    "xSapientia",
    "帮助区分私聊和群聊的插件",
    "0.0.1",
    "https://github.com/xSapientia/chattype",
)

class ChatTypeDetector(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.config = self._load_config(context)
        logger.info("Chat Type Detector v0.1.0 加载成功！")

    def _load_config(self, context: Context) -> dict:
        """加载配置文件"""
        try:
            config = context.get_config()
            return {
                "enable_plugin": config.get("enable_plugin", True),
                "group_prompt": config.get("group_prompt", "[群聊环境] 切换为群聊模式"),
                "private_prompt": config.get("private_prompt", "[私聊环境] 切换为私聊模式")
            }
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return {
                "enable_plugin": True,
                "group_prompt": "[群聊环境] 切换为群聊模式",
                "private_prompt": "[私聊环境] 切换为私聊模式"
            }

    @filter.on_llm_request()
    async def add_chat_type_prompt(self, event: AstrMessageEvent, context: Context) -> MessageEventResult:
        """
        在Bot回复前拦截并添加聊天类型提示
        """
        # 检查插件是否启用
        if not self.config.get("enable_plugin", True):
            return MessageEventResult().continue_()

        try:
            # 检测聊天类型
            is_private = event.is_private_chat()

            # 选择对应的提示词
            if is_private:
                chat_type = "private"
                chat_prompt = self.config.get("private_prompt")
            else:
                chat_type = "group"
                chat_prompt = self.config.get("group_prompt")

            # 存储聊天类型信息供其他插件使用
            context.set_property("chat_type", chat_type)
            context.set_property("chat_prompt", chat_prompt)

            # 记录日志
            logger.debug(f"检测到{chat_type}聊天，用户: {event.get_sender_id()}")

            # 获取并修改Bot的回复内容
            bot_reply = event.get_result_str()
            if bot_reply:
                # 在Bot回复前添加提示词
                modified_reply = f"{chat_prompt}\n{bot_reply}"
                event.set_result(modified_reply)
                logger.debug(f"已添加聊天类型提示: {chat_prompt}")

        except Exception as e:
            logger.error(f"处理消息时出错: {e}")

        return MessageEventResult().continue_()

    @filter.on_activated()
    async def on_activated(self):
        """插件激活时调用"""
        logger.info("Chat Type Detector 插件已激活")

    @filter.on_deactivated()
    async def on_deactivated(self):
        """插件停用时调用"""
        logger.info("Chat Type Detector 插件已停用")

def export_star() -> type[Star]:
    """
    导出Star类供AstrBot加载
    """
    return ChatTypeDetector
