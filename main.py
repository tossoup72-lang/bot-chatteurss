"""Point d'entrée du bot : python main.py"""
import logging

import discord
from discord import app_commands
from discord.ext import commands

import config

log = logging.getLogger("bot")
COGS = ["cogs.recruitment", "cogs.tests", "cogs.admin", "cogs.progression", "cogs.onboarding", "cogs.push"]


class AgencyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True  # accueil des arrivants, gestion des rôles
        intents.message_content = True  # lecture des réponses pendant les tests
        super().__init__(command_prefix=commands.when_mentioned, intents=intents,
                         allowed_mentions=discord.AllowedMentions(everyone=False, roles=False))

    async def setup_hook(self):
        for cog in COGS:
            await self.load_extension(cog)
        self.tree.on_error = self.on_app_command_error
        guild = discord.Object(id=config.GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        log.info("%d commandes synchronisées sur le serveur %s", len(synced), config.GUILD_ID)

    async def on_ready(self):
        log.info("Connecté en tant que %s", self.user)

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            message = "Commande réservée aux responsables."
        else:
            log.exception("Erreur dans /%s", interaction.command.qualified_name if interaction.command else "?",
                          exc_info=error)
            message = "Oups, une erreur est survenue. Réessaie dans un instant ou préviens un responsable."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    missing = config.check()
    if missing:
        raise SystemExit("Variables manquantes : " + ", ".join(missing) + " (voir .env.example)")
    AgencyBot().run(config.DISCORD_TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
