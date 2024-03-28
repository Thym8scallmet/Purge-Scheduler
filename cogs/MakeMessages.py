
#Make Messages is a helper for testing the purge function
#It should not be included in the final project.
#The file should be deleted and the cog removed from the main.py file.

import asyncio
import datetime

import discord
from discord import app_commands
from discord.ext import commands


class MakeMessages(commands.Cog):

  def __init__(self, client: commands.Bot):
    self.client = client

  @app_commands.command(
      name="make_messages",
      description="Makes a series of messages in batches of 50 until the requested number is reached")
  async def make_messages(self,
                          interaction: discord.Interaction,
                          number_of_messages: int = 5):
    # Before entering the loop, defer the response.
    await interaction.response.defer(ephemeral=True)

    # No upper limit for number_of_messages, but it must be positive.
    if number_of_messages < 1:
      await interaction.followup.send("Please specify a positive number of messages.")
      return

    # Calculate the number of full batches and the remainder for the last batch if not divisible by 50.
    full_batches = number_of_messages // 50
    remaining_messages = number_of_messages % 50

    for batch in range(full_batches + 1):
      # Determine the number of messages to send in this batch.
      batch_size = 50 if batch < full_batches else remaining_messages
      if batch_size == 0:
        continue  # If there are no remaining messages, skip the loop.

      for i in range(1, batch_size + 1):
        if isinstance(interaction.channel, discord.TextChannel):
          timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          await interaction.channel.send(
              f"{i + (batch * 50)}. This is a Purge bot-generated message. [{timestamp}]", silent=True)
        else:
          await interaction.followup.send("This command can only be used in text channels.", ephemeral=True)
          return  # Exit the function if the channel does not support sending messages.

      # If not on the last batch, pause for 5 seconds before sending the next batch.
      if batch < full_batches or (batch == full_batches and remaining_messages > 0):
        await asyncio.sleep(5)

    # Send a final message indicating completion
    await interaction.followup.send("Messages created successfully.", ephemeral=True)


async def setup(client: commands.Bot) -> None:
  await client.add_cog(MakeMessages(client))