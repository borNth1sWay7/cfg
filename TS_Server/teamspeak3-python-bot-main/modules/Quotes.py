# modules/Quotes.py
import logging
import random
from Moduleloader import command, setup

logger = logging.getLogger("bot")

class Quotes:
    def __init__(self, ts3bot, **kwargs):
        self.ts3bot = ts3bot
        self.ts3conn = ts3bot.ts3conn
        self.quotes = [
            "Stay hungry, stay foolish.",
            "The best way to predict the future is to invent it.",
            "Code is poetry.",
        ]

    @command("quote")
    def quote_command(self, sender, msg=None):
        quote = random.choice(self.quotes)
        self.ts3conn.sendtextmessage(targetmode=1, target=sender, msg=quote)

@setup
def setup_quotes(ts3bot, **kwargs):
    quotes = Quotes(ts3bot, **kwargs)
    ts3bot.plugins["Quotes"] = quotes
    return quotes