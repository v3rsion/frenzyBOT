import discord
from discord import app_commands
from discord.ext import commands
import random
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.game import Game, GameConfig
from core import config


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="set_log_channel_message_game",
        description="Set the log channel for message game commands",
    )
    @app_commands.describe(channel="The channel to log message game commands")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_log_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        config.log_channel_id = channel.id
        await interaction.response.send_message(
            f"Log channel set to {channel.mention}", ephemeral=True
        )

    @app_commands.command(
        name="start_message_game",
        description="Starts a game with a random message drop",
    )
    @app_commands.describe(
        chance="Chance of message drop (0.00001-100%)",
        cooldown="Cooldown in seconds",
        role="Role allowed to play",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def start_game(
        self,
        interaction: discord.Interaction,
        chance: float,
        cooldown: int,
        role: discord.Role = None,
    ):
        if config.log_channel_id is None:
            await interaction.response.send_message(
                "Log channel is not set. Please set the log channel first using the /set_log_channel_message_game command.",
                ephemeral=True,
            )
            return

        if not (0.00001 <= chance <= 100):
            await interaction.response.send_message(
                "Chance must be between 0.00001 and 100 percent.", ephemeral=True
            )
            return

        game_id = random.randint(1000, 9999)
        while game_id in config.games:
            game_id = random.randint(1000, 9999)

        game_config = GameConfig(
            channel=interaction.channel,
            chance=chance,
            cooldown=cooldown,
            role=role,
            game_id=game_id
        )
        game = Game(game_config)
        config.games[game_id] = game
        log_channel = self.bot.get_channel(config.log_channel_id)
        if log_channel:
            embed = discord.Embed(
                title="New Message Game Started",
                description=f"A new message game with the ID ({game_id}) has started in {interaction.channel.mention}.\nResponsible user for starting this game: {interaction.user.mention}",
                color=0x02FA02,
            )
            await log_channel.send(embed=embed)
        await interaction.response.send_message(
            f"Game has started and the ID of the game has been sent to {log_channel.mention}",
            ephemeral=True,
        )

    @app_commands.command(name="end_message_game", description="Ends the message game")
    @app_commands.describe(game_id="ID of the game to end")
    @app_commands.checks.has_permissions(administrator=True)
    async def end_game(self, interaction: discord.Interaction, game_id: int):
        if game_id in config.games:
            config.games[game_id].active = False
            if config.games[game_id].frenzy_end_time:
                config.games[game_id].frenzy_end_time = None
                config.games[game_id].frenzy_multiplier = 1
            del config.games[game_id]
            log_channel = self.bot.get_channel(
                config.log_channel_id
            )  # the log_channel_id which is set by admis it call back here
            if log_channel:
                embed = discord.Embed(
                    title="Message Game Ended",
                    description=f"The message game with the ID ({game_id}) has been ended.\nResponsible user for ending the game: {interaction.user.mention}",  # mention the user who ended the game
                    color=0xFA0202,
                )
                await log_channel.send(embed=embed)
            await interaction.response.send_message(
                "Game ended and logged.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"Game {game_id} not found!", ephemeral=True
            )

    @app_commands.command(name="active_games", description="Lists all active games")
    @app_commands.checks.has_permissions(administrator=True)
    async def list_active_games(self, interaction: discord.Interaction):
        active_game_ids = [
            game_id for game_id in config.games if config.games[game_id].active
        ]
        if active_game_ids:
            await interaction.response.send_message(
                f"Active games: {', '.join(map(str, active_game_ids))}", ephemeral=True
            )  # list all the active games
        else:
            await interaction.response.send_message(
                "No active games currently.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
