import logging
from ClientInfo import ClientInfo
import Bot
import ts3API.Events as Events

logger = logging.getLogger("bot")


class CommandHandler:
    def __init__(self, ts3conn):
        self.ts3conn = ts3conn
        self.logger = logging.getLogger("textMsg")
        self.logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler("msg.log", mode='a+')
        formatter = logging.Formatter('MSG Logger %(asctime)s %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.propagate = 0
        self.handlers = {}
        self.plugins = {}  # 存储插件实例
        self.accept_from_groups = ['Server Admin', 'Moderator']

    def add_handler(self, handler, command):
        if self.handlers.get(command) is None:
            self.handlers[command] = [handler]
        else:
            self.handlers[command].append(handler)

    def check_permission(self, handler, clientinfo):
        if hasattr(handler, "allowed_groups"):
            for group in handler.allowed_groups:
                if clientinfo.is_in_servergroups(group):
                    return True
        else:
            for group in self.accept_from_groups:
                if clientinfo.is_in_servergroups(group):
                    return True
        return False

    def handle_command(self, msg, sender=0):
        logger.debug("Handling message " + msg)
        command = msg.split(None, 1)[0]
        if len(command) > 1:
            command = command[1:]
            handlers = self.handlers.get(command)
            ci = ClientInfo(sender, self.ts3conn)
            handled = False
            if handlers is not None:
                for handler in handlers:
                    if self.check_permission(handler, ci):
                        handled = True
                        # 检查命令是否属于某个插件
                        for plugin_name, plugin_instance in self.plugins.items():
                            if hasattr(plugin_instance, handler.__name__):
                                handler(plugin_instance, sender, msg)  # 传递插件实例作为 self
                                return
                        # 如果没有找到插件，直接调用处理函数
                        handler(self, sender, msg)
                if not handled:
                    Bot.send_msg_to_client(self.ts3conn, sender, "You are not allowed to use this command!")
            else:
                Bot.send_msg_to_client(self.ts3conn, sender, "I cannot interpret your command. I am very sorry. :(")
                logger.info("Unknown command " + msg + " received!")

    def inform(self, event, *args, **kwargs):
        if isinstance(event, Events.TextMessageEvent):
            self.handle_command(event.message, sender=event.invoker_id)