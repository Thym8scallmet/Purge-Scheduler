import datetime

import discord
from discord import app_commands
from discord.ext import commands


class DisplayTime(commands.Cog):
  def __init__(self, client: commands.Bot):
      self.client = client


  async def display_current_time(self,interaction: discord.Interaction):
    # Get the current time and date
    now = datetime.datetime.now()
    # Format the time and date
    current_time_date = now.strftime("%Y-%m-%d %H:%M:%S")
    # Use interaction response to send the current time and date message to Discord
    await interaction.response.send_message(f"Current Time and Date: {current_time_date}")

  @app_commands.command(name="current_time", description="Displays the current time and date in the server")
  async def current_server_time(self, interaction: discord.Interaction):
      await self.display_current_time(interaction)  # Modified to call the new async version that includes date


async def setup(client:commands.Bot) -> None:
  await client.add_cog(DisplayTime(client))
