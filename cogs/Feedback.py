import discord
from discord import app_commands
from discord.ext import commands


class Feedback(commands.Cog):

  def __init__(self, client: commands.Bot):
    self.client = client
    self.owner_id = int(
        '1217892784116338744'
    )  # Convert string to integer  # Replace 'YOUR_USER_ID' with your actual Discord user ID

  @app_commands.command(
      name="feedback",
      description="Provide feedback or report an issue about the bot.")
  @app_commands.describe(details="Your feedback or issue report.")
  async def feedback_simple(self, interaction: discord.Interaction,
                             details: str):
    # Attempt to send feedback to the bot owner
    owner = await self.client.fetch_user(self.owner_id)
    if owner:
      try:
        await owner.send(f"Feedback received: {details}")
        await interaction.response.send_message(
            "Your feedback has been forwarded to the bot owner. Thank you!",
            ephemeral=True)
      except discord.HTTPException as e:
        print(f"Error sending feedback to bot owner: {e}")
        await interaction.response.send_message(
            "An error occurred while forwarding your feedback.",
            ephemeral=True)
    else:
      await interaction.response.send_message(
          "Bot owner could not be found. Feedback not sent.", ephemeral=True)


async def setup(client: commands.Bot) -> None:
  await client.add_cog(Feedback(client))
