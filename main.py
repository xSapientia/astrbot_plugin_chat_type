from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig

@register(
    "astrbot_plugin_chat_type",
    "xSapientia",
    "帮助区分私聊和群聊的插件",
    "0.0.3",
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
                "group_prompt": "[群聊环境] 切换为群聊模式",
                "private_prompt": "[私聊环境] 切换为私聊模式",
                "prompt_position": "prefix"  # prefix 或 suffix
            }
        logger.info("Chat Type Detector v0.0.3 加载成功！")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message_received(self, event: AstrMessageEvent):
        """
        在接收到任何消息时检测聊天类型并修改消息内容
        """
        # 检查插件是否启用
        if not self.config.get("enable_plugin", True):
            return

        try:
            # 使用 is_private_chat() 检测聊天类型
            is_private = event.is_private_chat()

            # 选择对应的提示词
            if is_private:
                chat_type = "private"
                chat_prompt = self.config.get("private_prompt")
                logger.debug(f"检测到私聊消息，发送者: {event.get_sender_id()}")
            else:
                chat_type = "group"
                chat_prompt = self.config.get("group_prompt")
                group_id = event.get_group_id()
                logger.debug(f"检测到群聊消息，群组ID: {group_id}, 发送者: {event.get_sender_id()}")

            # 获取原始消息
            original_message = event.message_str

            # 根据配置的位置插入提示词
            prompt_position = self.config.get("prompt_position", "prefix")

            if prompt_position == "prefix":
                # 在消息前面添加提示词
                modified_message = f"{chat_prompt}\n{original_message}"
            elif prompt_position == "suffix":
                # 在消息后面添加提示词
                modified_message = f"{original_message}\n{chat_prompt}"
            else:
                # 默认前缀
                modified_message = f"{chat_prompt}\n{original_message}"

            # 修改事件中的消息内容
            event.message_obj.message_str = modified_message

            # 如果消息链中有纯文本消息，也需要修改
            if event.message_obj.message:
                from astrbot.api.message_components import Plain
                for i, component in enumerate(event.message_obj.message):
                    if isinstance(component, Plain):
                        if prompt_position == "prefix" and i == 0:
                            # 修改第一个文本组件
                            component.text = f"{chat_prompt}\n{component.text}"
                        elif prompt_position == "suffix" and i == len(event.message_obj.message) - 1:
                            # 修改最后一个文本组件
                            component.text = f"{component.text}\n{chat_prompt}"
                        break

            # 存储聊天类型信息到事件的额外信息中
            event.set_extra("chat_type", chat_type)
            event.set_extra("chat_prompt", chat_prompt)
            event.set_extra("is_private_chat", is_private)

            logger.info(f"已为{chat_type}聊天添加环境提示: {chat_prompt}")

        except Exception as e:
            logger.error(f"处理消息时出错: {e}")

    @filter.command("chattype")
    async def check_chat_type(self, event: AstrMessageEvent):
        """查看当前聊天类型"""
        is_private = event.is_private_chat()

        if is_private:
            yield event.plain_result(
                f"当前是私聊环境\n"
                f"用户ID: {event.get_sender_id()}\n"
                f"当前提示词: {self.config.get('private_prompt')}\n"
                f"提示词位置: {self.config.get('prompt_position', 'prefix')}"
            )
        else:
            group_id = event.get_group_id()
            yield event.plain_result(
                f"当前是群聊环境\n"
                f"群组ID: {group_id}\n"
                f"当前提示词: {self.config.get('group_prompt')}\n"
                f"提示词位置: {self.config.get('prompt_position', 'prefix')}"
            )

    @filter.command("chattype_test")
    async def test_modification(self, event: AstrMessageEvent, text: str = "测试消息"):
        """测试消息修改效果"""
        is_private = event.is_private_chat()
        chat_type = "私聊" if is_private else "群聊"
        prompt = self.config.get("private_prompt" if is_private else "group_prompt")
        position = self.config.get("prompt_position", "prefix")

        if position == "prefix":
            result = f"{prompt}\n{text}"
        else:
            result = f"{text}\n{prompt}"

        yield event.plain_result(
            f"原始消息: {text}\n"
            f"聊天类型: {chat_type}\n"
            f"修改后效果:\n---\n{result}\n---"
        )

    async def terminate(self):
        """插件卸载时调用"""
        logger.info("Chat Type Detector 插件已卸载")
