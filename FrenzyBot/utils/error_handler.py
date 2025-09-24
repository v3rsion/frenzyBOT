import discord
from discord import app_commands


async def handle_admin_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "You do not have the necessary permissions to run this command.",
            ephemeral=True,
        )
