import discord
from discord.ext import commands


def create_bot():
    intents = discord.Intents.default()
    intents.messages = True  # Add the message intent
    intents.message_content = True  # Add the message content intent
    return commands.Bot(command_prefix=commands.when_mentioned, intents=intents)
