from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from astrbot.api.provider import ProviderRequest

@register(
    "astrbot_plugin_chat_type",
    "xSapientia",
    "帮助区分私聊和群聊的插件",
    "0.0.4",
    "https://github.com/xSapientia/astrbot_plugin_chat_type",
)
class ChatTypeDetector(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config if config else AstrBotConfig()
        if not self.config:
            self.config = {
                "enable_plugin": True,
                "group_prompt": "[群聊环境] 切换为群聊模式",
                "private_prompt": "[私聊环境] 切换为私聊模式",
                "prompt_position": "prefix"
            }
        logger.info("Chat Type Detector v0.0.4 加载成功！")

    @filter.on_llm_request()
    async def modify_llm_prompt(self, event: AstrMessageEvent, req: ProviderRequest):
        """
        在LLM请求时修改prompt内容
        """
        if not self.config.get("enable_plugin", True):
            return

        try:
            # 使用 is_private_chat() 检测聊天类型
            is_private = event.is_private_chat()

            # 选择对应的提示词
            if is_private:
                chat_type = "private"
                chat_prompt = self.config.get("private_prompt")
                logger.debug(f"检测到私聊，将修改LLM prompt")
            else:
                chat_type = "group"
                chat_prompt = self.config.get("group_prompt")
                logger.debug(f"检测到群聊，将修改LLM prompt")

            # 获取原始prompt
            original_prompt = req.prompt if hasattr(req, 'prompt') else ""

            # 根据配置的位置插入提示词
            prompt_position = self.config.get("prompt_position", "prefix")

            if prompt_position == "prefix":
                # 在prompt前面添加提示词
                req.prompt = f"{chat_prompt}\n{original_prompt}"
            elif prompt_position == "suffix":
                # 在prompt后面添加提示词
                req.prompt = f"{original_prompt}\n{chat_prompt}"

            # 同时修改系统提示词（作为备选方案）
            if hasattr(req, 'system_prompt') and req.system_prompt:
                req.system_prompt = f"{chat_prompt}\n\n{req.system_prompt}"
            elif hasattr(req, 'system_prompt'):
                req.system_prompt = chat_prompt

            logger.info(f"已为{chat_type}聊天修改LLM请求: {chat_prompt}")
            logger.debug(f"修改后的prompt前50字符: {req.prompt[:50]}...")

        except Exception as e:
            logger.error(f"修改LLM请求时出错: {e}")

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

    @filter.command("chattype_debug")
    async def debug_info(self, event: AstrMessageEvent):
        """查看调试信息"""
        is_private = event.is_private_chat()
        group_id = event.get_group_id()

        debug_info = f"""调试信息：
聊天类型: {'私聊' if is_private else '群聊'}
is_private_chat(): {is_private}
get_group_id(): {group_id}
get_sender_id(): {event.get_sender_id()}
get_platform_name(): {event.get_platform_name()}
插件状态: {'启用' if self.config.get('enable_plugin', True) else '禁用'}
当前配置:
- group_prompt: {self.config.get('group_prompt')}
- private_prompt: {self.config.get('private_prompt')}
- prompt_position: {self.config.get('prompt_position')}"""

        yield event.plain_result(debug_info)

    async def terminate(self):
        """插件卸载时调用"""
        logger.info("astrbot_plugin_chat_type 插件已卸载")
