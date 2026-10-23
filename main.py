from pathlib import Path

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger


@register("azurehelp")
class AzureHelp(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 图片路径：插件目录/file/help_page.jpg
        # 不依赖机器人启动时的工作目录
        self.help_image = Path(__file__).resolve().parent / "files" / "help_page.png"

    @filter.command("help")
    async def help(self, event: AstrMessageEvent):
        """发送帮助图片。"""
        try:
            if not self.help_image.is_file():
                logger.error(f"帮助图片不存在: {self.help_image}")
                yield event.plain_result("帮助图片不存在，请联系管理员。")
                return

            logger.info(f"触发 help 指令，发送图片: {self.help_image}")
            yield event.image_result(str(self.help_image))

        except Exception as e:
            logger.exception(f"发送帮助图片失败: {e}")
            yield event.plain_result("发送帮助图片失败，请稍后重试。")
