# some random libraries
import asyncio
from core.bot import create_bot
from core import config
from utils.error_handler import handle_admin_error

bot = create_bot()


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"We have logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author == bot.user:  # Ignore messages from the bot itself
        return

    for game in config.games.values():
        if game.channel == message.channel:  # Check all active games
            await game.check_message(message, bot, config.log_channel_id)

    await bot.process_commands(message)


async def main():
    async with bot:
        await bot.load_extension("commands.admin")
        await bot.load_extension("commands.user_management")
        await bot.load_extension("commands.frenzy")

        # Sync command checks with the bot
        for cog_name in [
            "commands.admin",
            "commands.user_management",
            "commands.frenzy",
        ]:
            cog = bot.get_cog(
                cog_name.split(".")[-1].replace("_", "").title() + "Commands"
            )
            if cog:
                for command in cog.get_app_commands():
                    command.on_error = handle_admin_error

        await bot.start("YOUR_BOT_TOKEN")  # Replace with your bot token


if __name__ == "__main__":
    asyncio.run(main())
