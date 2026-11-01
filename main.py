"""Azure Help —— /help 以「合并转发」的形式发送帮助图 + 网站教程。"""

from pathlib import Path

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Image, Node, Nodes, Plain
from astrbot.api.star import Context, Star, register

# 插件目录：不依赖机器人启动时的工作目录
PLUGIN_DIR = Path(__file__).resolve().parent
FILE_DIR = PLUGIN_DIR / "file"
HELP_IMAGE = FILE_DIR / "help_page.png"
TUTORIAL_FILE = FILE_DIR / "tutorial.txt"
TUTORIAL_URL = "https://azure712.space/bothelp"

# 合并转发里显示的发送者
NODE_NAME = "Azure 帮助"
# 单个转发节点的文本上限，超出会被拆成多条（QQ 对单条消息有长度限制）
MAX_NODE_CHARS = 1500

FALLBACK_TUTORIAL = (
    "📖 Bot 指令手册\n"
    "· !接歌词 / !接歌词 search <歌名> / !接歌词 from <歌名> <歌词>\n"
    "· 退出接歌 / 结束接歌 / quit\n"
    "· !点歌 <歌名> / !副歌 <歌名>\n"
    "· 赞我（无前缀）/ !查询好感度 / !help\n"
    "🔗 服务群 1067790453\n"
    f"🌐 完整教程：{TUTORIAL_URL}"
)


def split_text(text: str, limit: int = MAX_NODE_CHARS) -> list[str]:
    """按行把长文本切成多段，避免单条转发节点超长。"""
    chunks: list[str] = []
    buf = ""
    for line in text.splitlines(keepends=True):
        while len(line) > limit:  # 单行本身就超长，硬切
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.append(line[:limit])
            line = line[limit:]
        if buf and len(buf) + len(line) > limit:
            chunks.append(buf)
            buf = ""
        buf += line
    if buf.strip():
        chunks.append(buf)
    return chunks


@register("azurehelp")
class AzureHelp(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("help")
    async def help(self, event: AstrMessageEvent):
        """以合并转发的形式发送帮助图与网站教程。"""
        try:
            nodes = self._build_nodes(event)
            if not nodes.nodes:
                logger.error("帮助内容为空：既没有帮助图，也没有教程文本")
                yield event.plain_result("帮助内容缺失，请联系管理员。")
                return

            # 合并转发目前只有 OneBot v11（aiocqhttp）支持
            if event.get_platform_name() == "aiocqhttp":
                logger.info(f"触发 help 指令，发送合并转发（{len(nodes.nodes)} 条）")
                yield event.chain_result([nodes])
                return

            logger.info("当前平台不支持合并转发，改为逐条发送帮助内容")
            for node in nodes.nodes:
                yield event.chain_result(node.content)

        except Exception as e:
            logger.exception(f"发送帮助失败: {e}")
            yield event.plain_result("发送帮助失败，请稍后重试。")

    def _build_nodes(self, event: AstrMessageEvent) -> Nodes:
        """帮助图 + 网站教程 → 合并转发的节点列表。"""
        self_id = event.get_self_id() or "0"
        nodes: list[Node] = []

        if HELP_IMAGE.is_file():
            nodes.append(
                Node(
                    content=[Image.fromFileSystem(str(HELP_IMAGE))],
                    name=NODE_NAME,
                    uin=self_id,
                )
            )
        else:
            logger.warning(f"帮助图片不存在，已跳过: {HELP_IMAGE}")

        for chunk in split_text(self._load_tutorial()):
            nodes.append(Node(content=[Plain(chunk)], name=NODE_NAME, uin=self_id))

        return Nodes(nodes)

    def _load_tutorial(self) -> str:
        """读取内置的网站教程快照（file/tutorial.txt）。"""
        try:
            text = TUTORIAL_FILE.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"读取教程文本失败，使用内置简版: {e}")
            return FALLBACK_TUTORIAL

        if not text:
            logger.warning(f"教程文本为空，使用内置简版: {TUTORIAL_FILE}")
            return FALLBACK_TUTORIAL
        return text
