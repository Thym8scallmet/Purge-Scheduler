import discord
from discord import app_commands
from discord.ext import commands


class BotTest(commands.Cog):

  def __init__(self, client: commands.Bot):
    self.client = client

  #Basic command to make sure the bot is working.
  #It may be neccassary to kick the bot and re-add it to the server to make sure the slash commands are updated.
  @app_commands.command(name="bot_test",
                        description="Makes sure the bot is working")
  async def bottest(self, interaction: discord.Interaction):
    try:
      await interaction.response.send_message(
          content="Hello, the bot is working")
    except Exception as e:
      print(f"Error in bottest command: {e}")


async def setup(client: commands.Bot) -> None:
  await client.add_cog(BotTest(client))
