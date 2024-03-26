
import discord
from discord import app_commands
from discord.ext import commands


class PurgeBot(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="purge_bot_help", description="Purge bot help and Information")
    async def purgehelp(self, interaction: discord.Interaction):
        embed = discord.Embed(  # Here we assign the discord.Embed object to embed
            title="Purge Bot Instructions",
            description=(
                "Purge bot is a helpful tool that can be used to delete messages from a channel.\n\n "
                "To use the purge bot, you need to have the Admin role:\n\n"
                "For Purge bot to work, it must have the following Permissions.\n"
                "1. Manage Messages\n2. View channel\n3. Read Message History\n4. Send Messages\n\n"
                "Use:\n"
                "- The /purge command to delete up to 100 messages in a channel.\n"
                "- The /purge_old command to delete messages older than 14 days\n"
                #"-- Use this command only if /purge does not remove messages in the channel.--\n"
                #"- The /schedule_purge command to schedule a purge the channel you are currently in.\n"
                #"- The /view_jobs command to view all scheduled purge jobs.\n"
                #"- The /cancel_job command to cancel a scheduled purge job.\n"
            ),
        )
        await interaction.response.send_message(embed=embed , ephemeral=True)

    @app_commands.command(name="purge", description="Purge messages. Choose 'recent' or 'old' for older than 14 days.")
    async def purge(self, interaction: discord.Interaction, amount: int, type: str = "recent"):
         # Ensure the interaction is in a guild
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used within a server.", ephemeral=True)
            return

        member = interaction.guild.get_member(interaction.user.id)

        if member is None:
            await interaction.response.send_message("Could not retrieve member information.", ephemeral=True)
            return

        roles = [role.name for role in member.roles]
        if "Admin" not in roles and not member.guild_permissions.manage_messages:
            await interaction.response.send_message("You do not have the required permissions to use this command.", ephemeral=True)
            return

        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("This command can only be used in text channels.")
            return

        permissions = channel.permissions_for(channel.guild.me)
        if not permissions.manage_messages or not permissions.read_message_history:
            await interaction.response.send_message("I do not have the necessary permissions in this channel.")
            return

        if type == "recent":
            await interaction.response.send_message("Purging recent messages...")
            await channel.purge(limit=amount)
        elif type == "old":
            await interaction.response.send_message("Processing... This might take some time.")
            deleted = 0
            async for message in channel.history(limit=amount, oldest_first=True):
                if (discord.utils.utcnow() - message.created_at).days > 14:
                    await message.delete()
                    deleted += 1
            await interaction.followup.send(f"Deleted {deleted} messages older than 14 days.")
        else:
            await interaction.response.send_message("Invalid type specified. Please use 'recent' or 'old'.")

    @purge.error
    async def purge_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(content=str(error), ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(PurgeBot(client))