import discord
from discord import app_commands
from discord.ext import commands


class Hello(commands.Cog):

  def __init__(self, client: commands.Bot):
    self.client = client

  #Code for slash command hello.  It may be necessary to kick the bot and
  #re-add it to the server to make sure the slash commands are updated.
  @app_commands.command(name="hello", description="Says hello to the user")
  async def slashhello(self, interaction: discord.Interaction):
    await interaction.response.send_message(
        content="Hello this is a slash command")


async def setup(client: commands.Bot) -> None:
  await client.add_cog(Hello(client))
