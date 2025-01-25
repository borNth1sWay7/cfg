# modules/nickname.py
import logging
import time
from Moduleloader import event, setup
from ts3API.Events import ClientEnteredEvent
from ClientInfo import ClientInfo

# 配置 nickname 的日志记录器
nickname_logger = logging.getLogger("nickname")
nickname_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("nickname.log", mode='a+')
formatter = logging.Formatter('Nickname Logger %(asctime)s %(message)s')
file_handler.setFormatter(formatter)
nickname_logger.addHandler(file_handler)
nickname_logger.propagate = 0

class NicknameChecker:
    def __init__(self, ts3bot, **kwargs):
        """
        初始化 NicknameChecker 插件。
        :param ts3bot: Ts3Bot 实例
        :param kwargs: 插件配置
        """
        self.ts3bot = ts3bot
        self.ts3conn = ts3bot.ts3conn
        self.kick_timeout = int(kwargs.get("kick_timeout", 10))  # 踢出用户的等待时间
        self.default_nickname_prefix = kwargs.get("default_nickname_prefix", "TeamSpeakUser")  # 默认昵称前缀

    def check_nickname(self, client_id):
        """
        检查用户昵称是否为默认昵称。
        :param client_id: 用户 ID
        """
        client_info = ClientInfo(client_id, self.ts3conn)
        nickname = client_info.name

        # 如果用户使用默认昵称
        if nickname.startswith(self.default_nickname_prefix) or "TeamSpeakUser" in nickname:
            nickname_logger.info(f"发现用户使用默认昵称: {nickname} (ID: {client_id})")

            # 发送 Poke 弹窗消息
            try:
                self.ts3conn.clientpoke(clid=client_id, msg="请更改您的昵称后再连接！以供别人识别！")
            except Exception as e:
                nickname_logger.error(f"发送 Poke 消息失败: {e}")

            # 发送文本消息（可选）
            try:
                self.ts3conn.sendtextmessage(targetmode=1, target=client_id, msg="请更改您的昵称后再连接！")
            except Exception as e:
                nickname_logger.error(f"发送文本消息失败: {e}")

            # 等待指定时间
            time.sleep(self.kick_timeout)

            # 再次检查用户是否已改名
            updated_client_info = ClientInfo(client_id, self.ts3conn)
            updated_nickname = updated_client_info.name

            if updated_nickname.startswith(self.default_nickname_prefix) or "TeamSpeakUser" in updated_nickname:
                # 如果用户仍未改名，踢出用户
                try:
                    self.ts3conn.clientkick(client_id=client_id, reason_id=5, reason_msg="请更改昵称后重新连接，以便识别。")
                    nickname_logger.info(f"已踢出用户: {nickname} (ID: {client_id})")
                except Exception as e:
                    nickname_logger.error(f"踢出用户失败: {e}")

@event(ClientEnteredEvent)
def on_client_entered(event_data, ts3bot):
    """
    处理客户端加入事件。
    :param event_data: 事件数据
    :param ts3bot: Ts3Bot 实例
    """
    client_id = event_data.client_id
    nickname_checker = ts3bot.plugins.get("NicknameChecker")
    if nickname_checker:
        nickname_checker.check_nickname(client_id)

@setup
def setup_nickname_checker(ts3bot, **kwargs):
    """
    Setup function for NicknameChecker plugin.
    """
    nickname_checker = NicknameChecker(ts3bot, **kwargs)
    ts3bot.plugins["NicknameChecker"] = nickname_checker
    nickname_logger.info("NicknameChecker plugin loaded.")
    nickname_logger.debug(f"Plugin config: {kwargs}")
    return nickname_checker