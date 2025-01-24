# utils.py
from ts3API.TS3Connection import TS3QueryException
import Bot
import Moduleloader
from Moduleloader import *

__version__ = "0.4"
bot: Bot.Ts3Bot
logger = logging.getLogger("bot")

@Moduleloader.setup
def setup(ts3bot):
    global bot
    bot = ts3bot

@command('hello')
@group('Server Admin')
def hello(self, sender, msg=None):
    Bot.send_msg_to_client(bot.ts3conn, sender, "Hello Admin!")

@command('hello')
@group('Moderator')
def hello(self, sender, msg=None):
    Bot.send_msg_to_client(bot.ts3conn, sender, "Hello Moderator!")

@command('hello')
@group('Normal')
def hello(self, sender, msg=None):
    Bot.send_msg_to_client(bot.ts3conn, sender, "Hello Casual!")

@command('kickme', 'fuckme')
@group('.*')
def kickme(self, sender, msg=None):
    bot.ts3conn.clientkick(sender, 5, "Whatever.")

@command('mtest')
def mtest(self, sender, msg=None):
    channels = msg[len("!mtest "):].split()
    print(channels)
    bot.ts3conn.channelfind(channels[0])

@command('multimove', 'mm')
@group('Server Admin', 'Moderator')
def multi_move(self, sender, msg=None):
    channels = msg.split()[1:]
    source_name = channels[0] if len(channels) > 0 else ""
    dest_name = channels[1] if len(channels) > 1 else ""
    if not source_name or not dest_name:
        Bot.send_msg_to_client(bot.ts3conn, sender, "Usage: !multimove source destination")
        return
    try:
        source = bot.ts3conn.channelfind(source_name)[0].get("cid", '-1')
        dest = bot.ts3conn.channelfind(dest_name)[0].get("cid", '-1')
        client_list = bot.ts3conn.clientlist()
        for client in client_list:
            if client.get("cid", '-1') == source:
                bot.ts3conn.clientmove(int(dest), int(client.get("clid", '-1')))
    except TS3QueryException as e:
        Bot.send_msg_to_client(bot.ts3conn, sender, f"Error: {e.message}")

@command('version')
@group('.*')
def send_version(self, sender, msg=None):
    Bot.send_msg_to_client(bot.ts3conn, sender, __version__)

@command('whoami')
@group('.*')
def whoami(self, sender, msg=None):
    Bot.send_msg_to_client(bot.ts3conn, sender, "None of your business!")

@command('stop')
@group('Server Admin')
def stop_bot(self, sender, msg=None):
    Moduleloader.exit_all()
    bot.ts3conn.quit()
    logger.warning("Bot was quit!")

@command('restart')
@group('Server Admin', 'Moderator')
def restart_bot(self, sender, msg=None):
    Moduleloader.exit_all()
    bot.ts3conn.quit()
    logger.warning("Bot was quit!")
    import main
    main.restart_program()

@command('commandlist')
@group('Server Admin', 'Moderator')
def get_command_list(self, sender, msg=None):
    Bot.send_msg_to_client(bot.ts3conn, sender, str(list(bot.command_handler.handlers.keys())))