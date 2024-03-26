import json
from datetime import datetime, timedelta, timezone

import aiofiles
import discord
from discord import app_commands
from discord.ext import commands, tasks


class MinutesPurge(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.purge_check.start()

    async def cog_unload(self):
        self.purge_check.cancel()

    @app_commands.command(name="schedule_one_purge", description="Schedules messages to be purged.")
    async def schedule_one_purge(self, interaction: discord.Interaction, channel: discord.TextChannel, delay: int, amount: int):
        if delay < 1 or amount < 1:
            await interaction.response.send_message("Delay and amount must be positive integers.", ephemeral=True)
            return

        # Ensuring the scheduled_time is timezone-aware (UTC)
        scheduled_time = datetime.now(timezone.utc) + timedelta(minutes=delay)
        job = {"channel_id": channel.id, "scheduled_time": scheduled_time.isoformat(), "amount": amount, "recurring": False}

        try:
            async with aiofiles.open("minutepurge.json", "r+") as file:
                try:
                    data = json.loads(await file.read())
                except json.JSONDecodeError:
                    data = []
                data.append(job)
                await file.seek(0)
                await file.write(json.dumps(data, indent=4))
        except FileNotFoundError:
            data = [job]
            async with aiofiles.open("minutepurge.json", "w") as file:
                await file.write(json.dumps(data, indent=4))

        await interaction.response.send_message(f"Scheduled a purge of {amount} messages in {channel.mention} in {delay} minutes.", ephemeral=True)

    @app_commands.command(name="schedule_recurring_purge", description="Schedules recurring purges.")
    async def schedule_recurring_purge(self, interaction: discord.Interaction, channel: discord.TextChannel, start_time: str, recurrence_minutes: int, amount: int):
        if amount < 1 or amount > 100:
            await interaction.response.send_message("Amount must be between 1 and 100.", ephemeral=True)
            return
        if recurrence_minutes < 1:
            await interaction.response.send_message("Recurrence interval must be a positive integer.", ephemeral=True)
            return

        now = datetime.now(timezone.utc)
        start_hour, start_minute = map(int, start_time.split(':'))
        start_dt = datetime(now.year, now.month, now.day, start_hour, start_minute, tzinfo=timezone.utc)
        if start_dt < now:
            start_dt += timedelta(days=1)

        job = {"channel_id": channel.id, "scheduled_time": start_dt.isoformat(), "amount": amount, "recurring": True, "recurrence_minutes": recurrence_minutes}

        try:
            async with aiofiles.open("minutepurge.json", "r+") as file:
                try:
                    data = json.loads(await file.read())
                except json.JSONDecodeError:
                    data = []
                data.append(job)
                await file.seek(0)
                await file.write(json.dumps(data, indent=4))
        except FileNotFoundError:
            data = [job]
            async with aiofiles.open("minutepurge.json", "w") as file:
                await file.write(json.dumps(data, indent=4))

        scheduled_time_pretty = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        await interaction.response.send_message(f"Scheduled a recurring purge of {amount} messages in {channel.mention} starting at {scheduled_time_pretty} UTC and recurring every {recurrence_minutes} minutes.", ephemeral=True)

    @tasks.loop(seconds=60)
    async def purge_check(self):
        try:
            now = datetime.now(timezone.utc)  # Define 'now' at the start of the method
            async with aiofiles.open("minutepurge.json", "r+") as file:
                content = await file.read()
                jobs = json.loads(content) if content else []
                jobs_to_keep = []
                for job in jobs:
                    scheduled_time = datetime.fromisoformat(job["scheduled_time"]).replace(tzinfo=timezone.utc)
                    if scheduled_time <= now:
                        channel = self.client.get_channel(job["channel_id"])
                        if channel is not None and isinstance(channel, discord.TextChannel):
                            await channel.purge(limit=job["amount"])
                        if job.get("recurring"):
                            next_scheduled_time = scheduled_time + timedelta(minutes=job["recurrence_minutes"])
                            job["scheduled_time"] = next_scheduled_time.isoformat()
                            jobs_to_keep.append(job)
                    else:
                        jobs_to_keep.append(job)
                await file.seek(0)
                await file.truncate()
                await file.write(json.dumps(jobs_to_keep, indent=4))
        except Exception as e:
            print(f"Error during purge_check: {e}")

    @purge_check.before_loop
    async def before_purge_check(self):
        await self.client.wait_until_ready()

async def setup(client: commands.Bot) -> None:
    await client.add_cog(MinutesPurge(client))