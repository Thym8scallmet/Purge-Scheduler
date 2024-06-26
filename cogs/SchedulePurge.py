import json
from datetime import datetime, timedelta, timezone

import aiofiles
import discord
import pytz
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Select, View


class CancelView(View):

    def __init__(self, jobs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cancel_select = Select(
            placeholder="Select a job to cancel...",
            options=[
                discord.SelectOption(
                    label=f"Job {index + 1}: Channel {job['channel_id']} at {job['scheduled_time']}",
                    description=f"Limits: {job['amount']} messages",
                    value=str(index)) for index, job in enumerate(jobs)
            ])
        self.cancel_select.callback = self.cancel_job
        self.add_item(self.cancel_select)
        self.jobs = jobs

    async def cancel_job(self, interaction: discord.Interaction):
        job_index = int(self.cancel_select.values[0])
        self.jobs.pop(job_index)
        async with aiofiles.open("purgejobs.json", "w") as file:
            await file.write(json.dumps(self.jobs, indent=4))
        await interaction.response.send_message(
            content="Job cancelled successfully.", ephemeral=True)


class SchedulePurge(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client
        self.purge_check.start()

    async def cog_unload(self):
        self.purge_check.cancel()

    @app_commands.command(name="cancel_purge",
                          description="Cancel a scheduled purge job.")
    async def cancel_purge(self, interaction: discord.Interaction):
        try:
            async with aiofiles.open("purgejobs.json", "r") as file:
                content = await file.read()
                jobs = json.loads(content) if content else []

            if jobs:
                view = CancelView(jobs)
                await interaction.response.send_message(
                    "Select a purge job to cancel:", view=view, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "There are no scheduled purge jobs to cancel.", ephemeral=True)
        except Exception as e:
            print(f"Error in cancel_purge command: {e}")
            await interaction.response.send_message(
                "An error occurred while processing your request.", ephemeral=True)

    async def update_missed_purge_jobs(self):
        now = datetime.now(pytz.UTC)
        updated_jobs = []
        jobs_updated = False
        try:
            async with aiofiles.open("purgejobs.json", "r+") as file:
                jobs = json.loads(await file.read())
                for job in jobs:
                    job_time = datetime.fromisoformat(
                        job["scheduled_time"]).replace(tzinfo=pytz.UTC)
                    if now >= job_time and job["recurrence"] != "none":
                        intervals = {
                            "daily": timedelta(days=1),
                            "hourly": timedelta(hours=1),
                            "by minute": timedelta(minutes=1),
                            "weekly": timedelta(weeks=1),
                            "biweekly": timedelta(weeks=2),
                        }
                        while now >= job_time:
                            job_time += intervals[job["recurrence"]]
                            jobs_updated = True
                        job["scheduled_time"] = job_time.isoformat()
                    updated_jobs.append(job)
                if jobs_updated:
                    await file.seek(0)
                    await file.write(json.dumps(updated_jobs, indent=4))
                    await file.truncate()
        except Exception as e:
            print(f"Error updating missed purge jobs: {e}")

    @app_commands.command(name="view_purge_jobs",
                          description="View all scheduled purge jobs.")
    async def view_purge_jobs(self, interaction: discord.Interaction):
        try:
            async with aiofiles.open("purgejobs.json", "r") as file:
                content = await file.read()
                jobs = json.loads(content) if content else []

            if not jobs:
                await interaction.response.send_message(
                    "No scheduled purge jobs found.", ephemeral=True)
                return

            embed = discord.Embed(title="Scheduled Purge Jobs",
                                  color=discord.Color.blue())
            for i, job in enumerate(jobs, start=1):
                scheduled_time = datetime.fromisoformat(
                    job["scheduled_time"]).strftime("%Y-%m-%d %H:%M:%S UTC")
                job_info = (
                    f"Channel ID: {job['channel_id']}\n"
                    f"Scheduled Time: {scheduled_time}\n"
                    f"Messages to Purge: {job['amount']}\n"
                    f"Recurring: {'Yes' if job.get('recurrence') != 'none' else 'No'} - {job['recurrence'].capitalize() if job.get('recurrence') != 'none' else ''}"
                )
                embed.add_field(name=f"Job {i}", value=job_info, inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"Error in view_purge_jobs command: {e}")
            await interaction.response.send_message(
                "An error occurred while fetching the purge jobs.", ephemeral=True)

    @app_commands.command(
        name="schedule_purge",
        description="Schedule a purge, with optional recurrence, specifying date and time separately."
    )
    @app_commands.describe(
        channel="The channel where messages will be purged",
        date="The date for the purge (YYYY-MM-DD)",  # Will be replaced by automatic insertion
        time="The time for the purge (HH:MM)",
        message_limit="The maximum number of messages to purge",
        recurrence="How often the purge should recur")
    @app_commands.choices(date=[
    app_commands.Choice(name=datetime.now().strftime("%Y-%m-%d"),
                        value=datetime.now().strftime("%Y-%m-%d")),
    app_commands.Choice(
        name=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        value=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")),
    app_commands.Choice(
        name=(datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d"),
        value=(datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d")),
    app_commands.Choice(
        name=(datetime.now() + timedelta(weeks=2)).strftime("%Y-%m-%d"),
        value=(datetime.now() + timedelta(weeks=2)).strftime("%Y-%m-%d")),
], recurrence=[
    app_commands.Choice(name="none", value="none"),
    app_commands.Choice(name="daily", value="daily"),
    app_commands.Choice(name="hourly", value="hourly"),
    app_commands.Choice(name="by minute", value="by minute"),
    app_commands.Choice(name="weekly", value="weekly"),
    app_commands.Choice(name="biweekly", value="biweekly"),
])
    async def schedule_purge(self, interaction: discord.Interaction,
                             channel: discord.TextChannel, date: str, time: str,
                             message_limit: int, recurrence: str):
        try:
            scheduled_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

            new_job = {
                "channel_id": channel.id,
                "scheduled_time": scheduled_time.isoformat(),
                "amount": message_limit,
                "recurrence": recurrence,
            }

            async with aiofiles.open("purgejobs.json", "r+") as file:
                content = await file.read()
                jobs = json.loads(content) if content else []
                jobs.append(new_job)
                await file.seek(0)
                await file.write(json.dumps(jobs, indent=4))
                await file.truncate()

            await interaction.response.send_message("Purge scheduled successfully.",
                                                    ephemeral=True)
        except Exception as e:
            print(f"Error in schedule_purge command: {e}")
            await interaction.response.send_message(
                "An error occurred while scheduling the purge.", ephemeral=True)

    @tasks.loop(seconds=60)
    async def purge_check(self):
        """
        Adjusted function to only update the scheduled time for the next purge
        rather than executing the past due purges.
        """
        try:
            now = datetime.now(timezone.utc)
            async with aiofiles.open("purgejobs.json", "r+") as file:
                content = await file.read()
                jobs = json.loads(content) if content else []
                jobs_to_keep = []
                for job in jobs:
                    job_time = datetime.fromisoformat(
                        job["scheduled_time"]).replace(tzinfo=timezone.utc)
                    if now >= job_time and job["recurrence"] != "none":
                        # Update the job's scheduled time without purging
                        intervals = {
                            "daily": timedelta(days=1),
                            "hourly": timedelta(hours=1),
                            "by minute": timedelta(minutes=1),
                            "weekly": timedelta(weeks=1),
                            "biweekly": timedelta(weeks=2),
                        }
                        while now >= job_time:
                            job_time += intervals[job["recurrence"]]
                        job["scheduled_time"] = job_time.isoformat()

                    jobs_to_keep.append(job)  # Re-add the job with the updated time

                await file.seek(0)
                await file.write(json.dumps(jobs_to_keep, indent=4))
                await file.truncate()

        except Exception as e:
            print(f"Error in purge_check task: {e}")

    @purge_check.before_loop
    async def before_purge_check(self):
        await self.client.wait_until_ready()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(SchedulePurge(client))