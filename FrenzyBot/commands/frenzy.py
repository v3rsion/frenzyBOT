import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime
import sys
import os
from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import config
from core.game import FrenzyRequest

if TYPE_CHECKING:
    from core.game import Game


@dataclass(frozen=True)
class StartFrenzyRequest:
    game_id: int
    length: int
    multiplier: float
    frenzy_chance: float


@dataclass
class FrenzySession:
    game: "Game"
    check: Callable[[discord.Message], bool]
    frenzy_chance: float
    length: int
    multiplier: float
    interaction: discord.Interaction


class FrenzyCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="start_frenzy", description="Starts a frenzy with a chance multiplier"
    )
    @app_commands.describe(
        game_id="ID of the game",
        length="Length of the frenzy in seconds",
        multiplier="Chance multiplier",
        frenzy_chance="Chance this frenzy starts",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def start_frenzy( 
        self,
        interaction: discord.Interaction,
        game_id: int,
        length: int,
        multiplier: float,
        frenzy_chance: float,
    ):
        request = StartFrenzyRequest(
            game_id=game_id,
            length=length,
            multiplier=multiplier,
            frenzy_chance=frenzy_chance,
        )
        await self._handle_start_frenzy(interaction, request)

    async def _handle_start_frenzy(
        self, interaction: discord.Interaction, request: StartFrenzyRequest
    ) -> None:
        game = await self._get_active_game(interaction, request.game_id)
        if not game:
            return

        if not await self._ensure_frenzy_available(interaction, game):
            return

        await interaction.response.send_message(
            "Frenzy mode initiated. Messages will be checked to start frenzy.",
            ephemeral=True,
        )

        session = FrenzySession(
            game=game,
            check=self._build_frenzy_check(game),
            frenzy_chance=request.frenzy_chance,
            length=request.length,
            multiplier=request.multiplier,
            interaction=interaction,
        )
        await self._wait_for_initial_message(session.check)
        await self._wait_for_frenzy_trigger(session)

    async def _get_active_game(
        self, interaction: discord.Interaction, game_id: int
    ) -> "Game | None":
        if game_id not in config.games:
            await interaction.response.send_message("Game not found!", ephemeral=True)
            return None

        game = config.games[game_id]
        if not game.active:
            await interaction.response.send_message(
                "Game is not active!", ephemeral=True
            )
            return None

        return game

    async def _ensure_frenzy_available(
        self, interaction: discord.Interaction, game: "Game"
    ) -> bool:
        if (
            game.frenzy_end_time and datetime.now() < game.frenzy_end_time
        ):  # Check if a frenzy is already active
            await interaction.response.send_message(
                "A frenzy is already active for this game.", ephemeral=True
            )
            return False
        return True

    def _build_frenzy_check(self, game: "Game") -> Callable[[discord.Message], bool]:
        def frenzy_check(m: discord.Message) -> bool:
            return m.channel == game.channel and m.author != self.bot.user

        return frenzy_check

    async def _wait_for_initial_message(
        self, frenzy_check: Callable[[discord.Message], bool]
    ) -> None:
        message_count = 0
        while message_count < 1:
            await self.bot.wait_for("message", check=frenzy_check)
            message_count += 1

    async def _wait_for_frenzy_trigger(self, session: FrenzySession) -> None:
        while True:
            await self.bot.wait_for(
                "message", check=session.check
            )  # Wait for a message await funtion aka frenzy check
            if random.uniform(0, 100) <= session.frenzy_chance:
                frenzy_request = FrenzyRequest(
                    length=session.length,
                    multiplier=session.multiplier,
                    interaction=session.interaction,
                    bot=self.bot,
                    log_channel_id=config.log_channel_id,
                )
                await session.game.start_frenzy(frenzy_request)
                break


async def setup(bot):
    await bot.add_cog(FrenzyCommands(bot))
