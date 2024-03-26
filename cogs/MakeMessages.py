#Make Messages is a helper for testing the purge function
#It should not be included in the final project.
#The file should be deleted and the cog removed from the main.py file.

import asyncio

import discord
from discord import app_commands
from discord.ext import commands


class MakeMessages(commands.Cog):

  def __init__(self, client: commands.Bot):
    self.client = client

  @app_commands.command(
      name="make_messages",
      description="Makes a numbered list of messages up to 50")
  async def make_messages(self,
                          interaction: discord.Interaction,
                          number_of_messages: int = 5):
    # Before entering the loop, defer the response
    await interaction.response.defer(ephemeral=True)
    # Ensure the number is within the limit of up to 50
    if number_of_messages < 1 or number_of_messages > 50:
      await interaction.response.send_message(
          "Please specify a number between 1 and 50.")
      return

    # Generate and send the specified number of messages with one second delay between each
    for i in range(1, number_of_messages + 1):
      if isinstance(interaction.channel, discord.TextChannel):
        await interaction.channel.send(
            f"{i}. This is a Purge bot-generated message.", silent=True)
        await asyncio.sleep(1)  # Introduce a one-second delay here
      else:
        await interaction.response.send_message(
            "This command can only be used in text channels.", ephemeral=True)
        break  # Exit the loop if the channel does not support sending messages to prevent further errors

    # Send a final message indicating completion
    await interaction.followup.send("Messages created successfully.",
                                    ephemeral=True)


async def setup(client: commands.Bot) -> None:
  await client.add_cog(MakeMessages(client))
