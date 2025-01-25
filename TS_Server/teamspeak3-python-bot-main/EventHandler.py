# EventHandler.py
import logging
import threading

import ts3API.Events as Events


class EventHandler:
    """
    EventHandler 类负责将事件分发给注册的监听器。
    """
    logger = logging.getLogger("eventhandler")
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler("eventhandler.log", mode='a+')
    formatter = logging.Formatter('Eventhandler Logger %(asctime)s %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.info("Configured Eventhandler logger")
    logger.propagate = 0

    def __init__(self, ts3conn, command_handler, ts3bot):
        """
        初始化 EventHandler。
        :param ts3conn: TS3Connection 实例
        :param command_handler: CommandHandler 实例
        :param ts3bot: Ts3Bot 实例
        """
        self.ts3conn = ts3conn
        self.command_handler = command_handler
        self.ts3bot = ts3bot
        self.observers = {}
        self.add_observer(self.command_handler.inform, Events.TextMessageEvent)

    def on_event(self, _sender, **kw):
        """
        当新事件发生时调用。记录事件并通知所有监听器。
        :param _sender: 事件发送者
        :param kw: 事件参数
        """
        parsed_event = kw["event"]
        if isinstance(parsed_event, Events.TextMessageEvent):
            logging.debug(type(parsed_event))
        self.inform_all(parsed_event)

    def get_obs_for_event(self, evt):
        """
        获取事件的所有监听器。
        :param evt: 事件
        :return: 监听器列表
        """
        obs = set()
        for t in type(evt).mro():
            obs.update(self.observers.get(t, set()))
        return obs

    def add_observer(self, obs, evt_type):
        """
        添加事件类型的监听器。
        :param obs: 监听函数
        :param evt_type: 事件类型
        """
        obs_set = self.observers.get(evt_type, set())
        obs_set.add(obs)
        self.observers[evt_type] = obs_set

    def remove_observer(self, obs, evt_type):
        """
        移除事件类型的监听器。
        :param obs: 监听器
        :param evt_type: 事件类型
        """
        self.observers.get(evt_type, set()).discard(obs)

    def remove_observer_from_all(self, obs):
        """
        从所有事件类型中移除监听器。
        :param obs: 监听器
        """
        for evt_type in self.observers.keys():
            self.remove_observer(obs, evt_type)

    def inform_all(self, evt):
        """
        通知所有注册到事件类型的监听器。
        :param evt: 事件
        """
        for o in self.get_obs_for_event(evt):
            try:
                EventHandler.logger.debug(f"Informing observer {o.__name__} of event {type(evt)}")
                threading.Thread(target=o, args=(evt, self.ts3bot)).start()
            except BaseException:
                EventHandler.logger.exception("Exception while informing %s of Event of type %s", str(o), str(type(evt)))