from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig

@register(
    "astrbot_plugin_chat_type",
    "xSapientia",
    "帮助区分私聊和群聊的插件",
    "0.0.2",
    "https://github.com/xSapientia/astrbot_plugin_chat_type",
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
                "group_prompt": "[群聊环境] 请注意这是群聊，回复应当考虑公开性和适当性",
                "private_prompt": "[私聊环境] 这是私聊对话，可以进行更个性化的交流",
                "add_to_system_prompt": True
            }
        logger.info("Chat Type Detector v0.0.2 加载成功！")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message_received(self, event: AstrMessageEvent):
        """
        在接收到任何消息时检测聊天类型
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
                logger.debug(f"检测到群聊消息，群组ID: {group_id}, 发送者: {event.get_sender_id()}")
            else:
                chat_type = "private"
                chat_prompt = self.config.get("private_prompt")
                logger.debug(f"检测到私聊消息，发送者: {event.get_sender_id()}")

            # 将聊天类型信息存储到事件的额外信息中
            event.set_extra("chat_type", chat_type)
            event.set_extra("chat_prompt", chat_prompt)
            event.set_extra("is_group_chat", is_group_chat)
            event.set_extra("group_id", group_id if group_id else "")

            # 如果配置中启用了系统提示词修改
            if self.config.get("add_to_system_prompt", True):
                # 为后续的LLM请求准备提示词
                event.set_extra("system_prompt_addon", chat_prompt)

            logger.info(f"已识别{chat_type}聊天环境，消息: {event.message_str[:30]}...")

        except Exception as e:
            logger.error(f"检测聊天类型时出错: {e}")

    @filter.on_llm_request()
    async def modify_system_prompt(self, event: AstrMessageEvent, req):
        """
        在LLM请求时，如果之前已经检测到聊天类型，则添加到系统提示词
        """
        # 检查是否有之前存储的系统提示词附加内容
        system_prompt_addon = event.get_extra("system_prompt_addon")
        if system_prompt_addon and self.config.get("add_to_system_prompt", True):
            if req.system_prompt:
                req.system_prompt = f"{system_prompt_addon}\n\n{req.system_prompt}"
            else:
                req.system_prompt = system_prompt_addon
            logger.debug("已将聊天类型提示添加到系统提示词")

    @filter.command("chattype")
    async def check_chat_type(self, event: AstrMessageEvent):
        """查看当前聊天类型"""
        # 尝试从事件的额外信息中获取已存储的聊天类型
        stored_chat_type = event.get_extra("chat_type")

        if stored_chat_type:
            # 使用已存储的信息
            if stored_chat_type == "group":
                group_id = event.get_extra("group_id")
                yield event.plain_result(
                    f"当前是群聊环境\n"
                    f"群组ID: {group_id}\n"
                    f"当前提示词: {event.get_extra('chat_prompt')}"
                )
            else:
                yield event.plain_result(
                    f"当前是私聊环境\n"
                    f"用户ID: {event.get_sender_id()}\n"
                    f"当前提示词: {event.get_extra('chat_prompt')}"
                )
        else:
            # 实时检测
            group_id = event.get_group_id()
            if group_id:
                yield event.plain_result(f"当前是群聊环境\n群组ID: {group_id}")
            else:
                yield event.plain_result(f"当前是私聊环境\n用户ID: {event.get_sender_id()}")

    @filter.command("chattype_reload")
    async def reload_config(self, event: AstrMessageEvent):
        """重新加载配置"""
        try:
            # 尝试重新加载配置
            if hasattr(self, 'config') and hasattr(self.config, 'load_config'):
                self.config.load_config()
                yield event.plain_result("配置已重新加载")
            else:
                yield event.plain_result("配置重载功能暂不可用")
        except Exception as e:
            yield event.plain_result(f"重载配置失败: {str(e)}")

    async def terminate(self):
        """插件卸载时调用"""
        logger.info("Chat Type Detector 插件已卸载")
