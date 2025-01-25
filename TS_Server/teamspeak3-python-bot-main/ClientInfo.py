import logging
import re

logger = logging.getLogger("bot")


class ClientInfo:
    """
    ClientInfo contains various attributes of the client with the given client id.
    The attributes in this object have been filtered. If you want to know about all
    possible attributes, use `print(client_data.keys())`.
    """

    def __init__(self, client_id, ts3conn):
        """
        初始化 ClientInfo 对象。
        :param client_id: 客户端 ID
        :param ts3conn: TS3Connection 实例
        """
        if client_id == "-1":
            logger.error("Trying to get ClientInfo of clid=-1")
            logger.warning("Giving out mock object ...")
            client_data = {}
        else:
            try:
                # 修复：直接传递 client_id 作为参数
                client_data = ts3conn.clientinfo(client_id)
            except Exception as e:
                logger.error(f"获取客户端信息失败: {e}")
                client_data = {}

        # 客户端基本信息
        self._name = client_data.get('client_nickname', 'Unknown')
        self._unique_id = client_data.get('client_unique_identifier', '')
        self._database_id = client_data.get('client_database_id', '')
        self._description = client_data.get('client_description', '')
        self._country = client_data.get('client_country', '')
        self._created = client_data.get('client_created', '')
        self._total_connections = client_data.get('client_totalconnections', '')
        self._last_connection = client_data.get('client_lastconnected', '')
        self._connected_time = client_data.get('connection_connected_time', '')
        self._platform = client_data.get('client_platform', '')
        self._version = client_data.get('client_version', '')
        self._ip = client_data.get('connection_client_ip', '')
        self._away = client_data.get('client_away', '')
        self._input_muted = client_data.get('client_input_muted', '')
        self._output_muted = client_data.get('client_output_muted', '')
        self._outputonly_muted = client_data.get('client_outputonly_muted', '')
        self._input_hardware = client_data.get('client_input_hardware', '')
        self._output_hardware = client_data.get('client_output_hardware', '')
        self._channel_id = client_data.get('cid', '-1')

        # 获取服务器组信息
        sgs = {}
        try:
            for g in ts3conn.servergrouplist():
                sgs[g.get('sgid')] = g.get('name')
        except Exception as e:
            logger.error(f"获取服务器组列表失败: {e}")

        servergroups_list = client_data.get('client_servergroups', '').split(',')
        self._servergroups = []
        for g in servergroups_list:
            if g in sgs:
                self._servergroups.append(sgs[g])

        if not self._servergroups:
            logger.error(f"客户端没有服务器组: {self._name} (ID: {client_id})")
            logger.error(f"IP: {self._ip}, 频道 ID: {self._channel_id}")
            logger.error(f"客户端数据: {client_data}")

    @property
    def channel_id(self):
        """获取客户端所在的频道 ID。"""
        return self._channel_id

    @property
    def ip(self):
        """获取客户端的 IP 地址。"""
        return self._ip

    @property
    def name(self):
        """获取客户端的昵称。"""
        return self._name

    @property
    def servergroups(self):
        """获取客户端所属的服务器组列表。"""
        return self._servergroups

    def is_in_servergroups(self, pattern):
        """
        检查客户端是否属于匹配指定模式的服务器组。
        :param pattern: 正则表达式模式
        :return: 如果匹配则返回 True，否则返回 False
        """
        for group in self._servergroups:
            if re.search(pattern, group):
                return True
        return False

    def __getattr__(self, item):
        """
        动态获取属性。
        :param item: 属性名称
        :return: 属性值
        """
        if item.startswith("_"):
            return self.__getattribute__(item)
        return self.__getattribute__("_" + item)