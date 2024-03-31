import json
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View

# Updated to include at least one selection for each of the 24 time regions
TIMEZONES_BY_REGION = {
    'North America': ['America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles'],
    'Europe': ['Europe/London', 'Europe/Berlin', 'Europe/Paris', 'Europe/Moscow'],
    'Asia': ['Asia/Tokyo', 'Asia/Hong_Kong', 'Asia/Singapore', 'Asia/Seoul'],
    'Australia': ['Australia/Sydney', 'Australia/Melbourne', 'Australia/Brisbane'],
    'Other': ['UTC'],
    'Africa': ['Africa/Lagos', 'Africa/Cairo'],
    'South America': ['America/Sao_Paulo', 'America/Buenos_Aires'],
    'New Zealand': ['Pacific/Auckland'],
    'India': ['Asia/Kolkata'],
    'Middle East': ['Asia/Dubai', 'Asia/Riyadh'],
    'Eastern Europe': ['Europe/Athens', 'Europe/Bucharest'],
    'Central America': ['America/Mexico_City'],
    'Canada': ['America/Toronto', 'America/Vancouver'],
    'South East Asia': ['Asia/Jakarta', 'Asia/Manila'],
    'East Asia': ['Asia/Shanghai', 'Asia/Seoul'],
    'Central Asia': ['Asia/Tashkent'],
    'West Africa': ['Africa/Accra'],
    'East Africa': ['Africa/Nairobi'],
    'Central Africa': ['Africa/Kinshasa'],
    'North Africa': ['Africa/Algiers'],
    'South Africa': ['Africa/Johannesburg'],
    'Pacific Islands': ['Pacific/Fiji'],
    'Northern Europe': ['Europe/Stockholm'],
    'Southern Europe': ['Europe/Rome']
}

class RegionSelect(Select):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, placeholder='Select your region...', **kwargs)
        for region in TIMEZONES_BY_REGION.keys():
            self.add_option(label=region, value=region)

    async def callback(self, interaction: discord.Interaction):
        # Update the select options to show timezones for the selected region
        region = self.values[0]
        self.view.clear_items()
        self.view.add_item(TimezoneSelect(region))
        await interaction.response.edit_message(view=self.view)

class TimezoneSelect(Select):
    def __init__(self, region, *args, **kwargs):
        super().__init__(*args, placeholder='Now select your timezone...', **kwargs)
        for tz in TIMEZONES_BY_REGION[region]:
            self.add_option(label=tz, value=tz)

    async def callback(self, interaction: discord.Interaction):
        # On timezone selection, update the usertimezones.json file
        user_id = str(interaction.user.id)
        timezone = self.values[0]

        try:
            with open('usertimezones.json', 'r') as file:
                user_timezones = json.load(file)
        except FileNotFoundError:
            user_timezones = {}

        user_timezones[user_id] = timezone

        with open('usertimezones.json', 'w') as file:
            json.dump(user_timezones, file, indent=4)

        await interaction.response.send_message(f"Your timezone has been set to {timezone}.", ephemeral=True)

class TimezoneView(View):
    def __init__(self):
        super().__init__()
        self.add_item(RegionSelect())

class SetTimezone(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="set_timezone", description="Select your timezone from a dropdown menu.")
    async def utimezone(self, interaction: discord.Interaction):
        # Send a message with the timezone selection dropdown
        await interaction.response.send_message("Please select your region:", view=TimezoneView(), ephemeral=True)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(SetTimezone(client))