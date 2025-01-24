import importlib
import logging
import sys

from CommandHandler import CommandHandler
from EventHandler import EventHandler

setups = []
exits = []
plugin_modules = {}
event_handler: 'EventHandler'
command_handler: 'CommandHandler'
logger = logging.getLogger("moduleloader")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("moduleloader.log", mode='a+')
formatter = logging.Formatter('Moduleloader Logger %(asctime)s %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.info("Configured Moduleloader logger")
logger.propagate = 0


def load_modules(bot, config):
    global event_handler, command_handler
    plugins = config
    event_handler = bot.event_handler
    command_handler = bot.command_handler

    for plugin_name, plugin_module in plugins.items():
        try:
            plugin_modules[plugin_name] = importlib.import_module("modules." + plugin_module, package="modules")
            plugin_modules[plugin_name].pluginname = plugin_name
            logger.info("Loaded module " + plugin_name)
        except BaseException:
            logger.exception("While loading plugin " + str(plugin_name) + " from modules." + str(plugin_module))

    # 调用所有注册的 setup 函数
    for setup_func in setups:
        try:
            name = sys.modules.get(setup_func.__module__).pluginname
            if name in config:
                plugin_config = config[name]
                if isinstance(plugin_config, str):
                    plugin_config = {}
                plugin_instance = setup_func(ts3bot=bot, **plugin_config)
                command_handler.plugins[name] = plugin_instance  # 注册插件实例
            else:
                setup_func(bot)
        except BaseException:
            logger.exception("While setting up a module.")


def setup(function):
    setups.append(function)
    return function


def event(*event_types):
    def register_observer(function):
        for event_type in event_types:
            event_handler.add_observer(function, event_type)
        return function
    return register_observer


def command(*command_list):
    def register_command(function):
        for text_command in command_list:
            command_handler.add_handler(function, text_command)
        return function
    return register_command


def group(*groups):
    def save_allowed_groups(func):
        func.allowed_groups = groups
        return func
    return save_allowed_groups


def exit(function):
    exits.append(function)


def exit_all():
    for exit_func in exits:
        try:
            exit_func()
        except BaseException:
            logger.exception("While exiting a module.")