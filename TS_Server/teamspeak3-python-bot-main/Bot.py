import configparser
import logging
import os
from distutils.util import strtobool

import ts3API.TS3Connection
from ts3API.TS3Connection import TS3QueryException
from ts3API.TS3QueryExceptionType import TS3QueryExceptionType

import CommandHandler
from EventHandler import EventHandler  # 修改导入方式
import Moduleloader


def stop_conn(ts3conn):
    ts3conn.stop_recv.set()


def send_msg_to_client(ts3conn, clid, msg):
    """
    Convenience method for sending a message to a client without having a bot object.
    :param ts3conn: TS3Connection to send message on.
    :type ts3conn: ts3API.TS3Connection
    :param clid: Client id of the client to send too.
    :type clid: int
    :param msg: Message to send
    :type msg: str
    :return:
    """
    try:
        ts3conn.sendtextmessage(targetmode=1, target=clid, msg=msg)
    except ts3API.TS3Connection.TS3QueryException:
        logger = logging.getLogger("bot")
        logger.exception("Error sending a message to clid " + str(clid))


class Ts3Bot:
    """
    Teamspeak 3 Bot with module support.
    """
    def get_channel_id(self, name):
        """
        Convenience method for getting a channel by name.
        :param name: Channel name to search for, can be a pattern
        :type name: str
        :return: Channel id of the first channel found
        :rtype: int
        """
        ret = self.ts3conn.channelfind(pattern=name)
        return int(ret[0]["cid"])

    @staticmethod
    def bot_from_config(config):
        """
        Create a bot from the values parsed from config.ini.
        :param config: a configuration for the bot
        :type config: dict
        :return: Created Bot
        :rtype: Ts3Bot
        """
        logger = logging.getLogger("bot")
        general_config = config.pop('General')  # 提取 General 配置
        plugins_config = config.pop('Plugins')  # 提取 Plugins 配置
        return Ts3Bot(logger=logger, plugins=plugins_config, **general_config)

    @staticmethod
    def parse_config(logger):
        """
        Parse the config file config.ini.
        :param logger: Logger to log errors to.
        :return: Dictionary containing options necessary to create a new bot
        :rtype: dict[str, dict[str, str]]
        """
        config = configparser.ConfigParser()
        try:
            # 显式指定使用 UTF-8 编码读取文件
            with open('config.ini', 'r', encoding='utf-8') as f:
                config.read_file(f)
        except FileNotFoundError:
            logger.error("Config file missing!")
            exit()
        except UnicodeDecodeError:
            logger.error("Config file encoding is not UTF-8!")
            exit()

        if not config.has_section('General'):
            logger.error("Config file is missing general section!")
            exit()
        if not config.has_section('Plugins'):
            logger.error("Config file is missing plugins section")
            exit()
        return config._sections

    def connect(self):
        """
        Connect to the server specified by self.host and self.port.
        :return:
        """
        try:
            self.ts3conn = ts3API.TS3Connection.TS3Connection(self.host, self.port,
                                                              use_ssh=self.is_ssh, username=self.user,
                                                              password=self.password, accept_all_keys=self.accept_all_keys,
                                                              host_key_file=self.host_key_file,
                                                              use_system_hosts=self.use_system_hosts, sshtimeout=self.sshtimeout, sshtimeoutlimit=self.sshtimeoutlimit)
        except ts3API.TS3Connection.TS3QueryException:
            self.logger.exception("Error while connecting, IP probably not whitelisted or Login data wrong!")
            # This is a very ungraceful exit!
            os._exit(-1)
            raise

    def setup_bot(self):
        """
        Setup routine for new bot. Does the following things:
            1. Select virtual server specified by self.sid
            2. Set bot nickname to the Name specified by self.bot_name
            3. Move the bot to the channel specified by self.default_channel
            4. Register command and event handlers
        :return:
        """
        try:
            self.ts3conn.use(sid=self.sid)
        except ts3API.TS3Connection.TS3QueryException:
            self.logger.exception("Error on use SID")
            exit()
        try:
            try:
                self.ts3conn.clientupdate(["client_nickname=" + self.bot_name])
            except TS3QueryException as e:
                if e.type == TS3QueryExceptionType.CLIENT_NICKNAME_INUSE:
                    self.logger.info("The chosen bot nickname is already in use, keeping the default nickname")
                else:
                    raise e
            try:
                self.channel = self.get_channel_id(self.default_channel)
                self.ts3conn.clientmove(self.channel, int(self.ts3conn.whoami()["client_id"]))
            except TS3QueryException as e:
                if e.type == TS3QueryExceptionType.CHANNEL_ALREADY_IN:
                    self.logger.info("The bot is already in the configured default channel")
                else:
                    raise e
        except TS3QueryException:
            self.logger.exception("Error on setting up client")
            self.ts3conn.quit()
            return
        self.command_handler = CommandHandler.CommandHandler(self.ts3conn)
        self.event_handler = EventHandler(ts3conn=self.ts3conn, command_handler=self.command_handler, ts3bot=self)  # 修改初始化
        try:
            self.ts3conn.register_for_server_events(self.event_handler.on_event)
            self.ts3conn.register_for_channel_events(0, self.event_handler.on_event)
            self.ts3conn.register_for_private_messages(self.event_handler.on_event)
        except ts3API.TS3Connection.TS3QueryException:
            self.logger.exception("Error on registering for events.")
            exit()

    def __del__(self):
        if self.ts3conn is not None:
            self.ts3conn.quit()

    def __init__(self, host, port, serverid, user, password, defaultchannel, botname, logger, plugins, ssh="False",
                 acceptallsshkeys="False", sshhostkeyfile=None, sshloadsystemhostkeys="False", sshtimeout=None, sshtimeoutlimit=3, *_, **__):
        """
        Create a new Ts3Bot.
        :param host: Host to connect to, can be a IP or a host name
        :param port: Port to connect to
        :param serverid: Virtual Server id to use
        :param user: Server Query Admin Login Name
        :param password: Server Query Admin Password
        :param defaultchannel: Channel to move the bot to
        :param botname: Nickname of the bot
        :param logger: Logger to use throughout the bot
        :param plugins: Plugins configuration
        :param ssh: Whether to use SSH (default: "False")
        :param acceptallsshkeys: Whether to accept all SSH keys (default: "False")
        :param sshhostkeyfile: Path to SSH host key file (default: None)
        :param sshloadsystemhostkeys: Whether to load system host keys (default: "False")
        :param sshtimeout: SSH timeout (default: None)
        :param sshtimeoutlimit: SSH timeout limit (default: 3)
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.sid = serverid
        self.default_channel = defaultchannel
        self.bot_name = botname
        self.event_handler = None
        self.command_handler = None
        self.channel = None
        self.logger = logger
        self.ts3conn = None
        self.is_ssh = bool(strtobool(ssh))
        self.accept_all_keys = bool(strtobool(acceptallsshkeys))
        self.host_key_file = sshhostkeyfile
        self.use_system_hosts = bool(strtobool(sshloadsystemhostkeys))
        self.sshtimeout = sshtimeout
        self.sshtimeoutlimit = sshtimeoutlimit
        self.plugins = {}  # 初始化 plugins 属性

        self.connect()
        self.setup_bot()
        # Load modules
        Moduleloader.load_modules(self, plugins)
        self.ts3conn.start_keepalive_loop()