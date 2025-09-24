import discord
from discord import app_commands
from discord.ext import commands
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import config


class UserManagementCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ban_user_from_message_game",
        description="Bans a user from playing the message game",
    )
    @app_commands.describe(game_id="ID of the game", user="User to ban")
    @app_commands.checks.has_permissions(administrator=True)
    async def ban_user(
        self, interaction: discord.Interaction, game_id: int, user: discord.User
    ):
        if game_id in config.games:
            if user.id in config.games[game_id].banned_users:
                await interaction.response.send_message(
                    "User is already banned from this game.", ephemeral=True
                )
                return

            config.games[game_id].banned_users.add(user.id)
            log_channel = self.bot.get_channel(
                config.log_channel_id
            )  # the log_channel_id which is set by admis it call back here
            # Send a log message to the log channel log_channel = bot.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="Manually banned user from message game",
                    description=f"{user.mention} has been banned from the message game with the ID ({game_id}).\nResponsible user for banning: {interaction.user.mention}",
                    color=0xFDFE06,  # color hex
                )
                await log_channel.send(embed=embed)
            await interaction.response.send_message(
                "User banned and logged.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"Game {game_id} not found!", ephemeral=True
            )

    @app_commands.command(
        name="unban_user_from_message_game",
        description="Unbans a user from playing the message game",
    )  # unban the user from the game
    @app_commands.describe(game_id="ID of the game", user="User to unban")
    @app_commands.checks.has_permissions(administrator=True)
    async def unban_user(
        self, interaction: discord.Interaction, game_id: int, user: discord.User
    ):
        if game_id in config.games:
            if user.id not in config.games[game_id].banned_users:
                await interaction.response.send_message(
                    "User is not banned from this game.", ephemeral=True
                )
                return

            config.games[game_id].banned_users.remove(
                user.id
            )  # Remove the user from the banned list
            log_channel = self.bot.get_channel(config.log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="Manually unbanned user from message game",
                    description=f"{user.mention} has been unbanned from the message game with the ID ({game_id}).\nResponsible user for unbanning: {interaction.user.mention}",
                    color=0x02FA02,
                )
                await log_channel.send(embed=embed)
            await interaction.response.send_message(
                "User unbanned and logged.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"Game {game_id} not found!", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(UserManagementCommands(bot))
