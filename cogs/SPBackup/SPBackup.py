import json
from datetime import datetime, timedelta, timezone

import aiofiles
import discord
import pytz
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Select, View


class CancelView(View):
  # Initializes a view for job cancellation with a dropdown of scheduled jobs.
  def __init__(self, jobs, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.cancel_select = Select(
        placeholder="Select a job to cancel...",
        options=[
            discord.SelectOption(
                label=
                f"Job {index + 1}: Channel {job['channel_id']} at {job['scheduled_time']}",
                description=f"Limits: {job['amount']} messages",
                value=str(index)) for index, job in enumerate(jobs)
        ])
    self.cancel_select.callback = self.cancel_job
    self.add_item(self.cancel_select)
    self.jobs = jobs

  # Callback function to cancel a job based on user selection from the dropdown.
  async def cancel_job(self, interaction: discord.Interaction):
    job_index = int(self.cancel_select.values[0])
    self.jobs.pop(job_index)
    async with aiofiles.open("purgejobs.json", "w") as file:
      await file.write(json.dumps(self.jobs, indent=4))
    await interaction.response.send_message(
        content="Job cancelled successfully.", ephemeral=True)


class SchedulePurge(commands.Cog):
  # Cog initialization where we also start the looping task.
  def __init__(self, client: commands.Bot):
    self.client = client
    self.purge_check.start()

  # Cleanup action to cancel the looping task on cog unload.
  async def cog_unload(self):
    self.purge_check.cancel()

  # Command to allow users to cancel scheduled purge jobs via a dropdown selection.
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

  # Checks for any missed purge jobs and updates their schedule if necessary.
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

  # Command to display all scheduled purge jobs to the user.
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

  # Command to schedule a new purge job.
  @app_commands.command(
      name="schedule_purge",
      description=
      "Schedule a purge up to 2 weeks in advance, recurring at specified intervals."
  )
  @app_commands.describe(
      channel="The channel where messages will be purged",
      date_time="The date and time for the purge (YYYY-MM-DD HH:MM)",
      message_limit="The maximum number of messages to purge",
      recurrence="How often the purge should recur")
  @app_commands.choices(recurrence=[
      app_commands.Choice(name="none", value="none"),
      app_commands.Choice(name="daily", value="daily"),
      app_commands.Choice(name="hourly", value="hourly"),
      app_commands.Choice(name="by minute", value="by minute"),
      app_commands.Choice(name="weekly", value="weekly"),
      app_commands.Choice(name="biweekly", value="biweekly"),
  ])
  async def schedule_purge(self, interaction: discord.Interaction,
                           channel: discord.TextChannel, date_time: str,
                           message_limit: int, recurrence: str):
    try:
      scheduled_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M")

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

  # Looping task checks every minute to automatically purge messages based on scheduled jobs.
  @tasks.loop(seconds=60)
  async def purge_check(self):
    try:
      now = datetime.now(timezone.utc)
      async with aiofiles.open("purgejobs.json", "r+") as file:
        content = await file.read()
        jobs = json.loads(content) if content else []
        jobs_to_keep = []
        for job in jobs:
          job_time = datetime.fromisoformat(
              job["scheduled_time"]).replace(tzinfo=timezone.utc)
          if now >= job_time:
            channel = self.client.get_channel(job["channel_id"])
            if channel:
              await channel.purge(limit=job['amount'])
              print(
                  f"Purged {job['amount']} messages from {channel} at {job['scheduled_time']}"
              )
              if job["recurrence"] == "none":
                continue  # Skip re-scheduling for non-recurring jobs
            intervals = {
                "none": timedelta(
                    0),  # should not actually happen due to the continue above
                "daily": timedelta(days=1),
                "hourly": timedelta(hours=1),
                "by minute": timedelta(minutes=1),
                "weekly": timedelta(weeks=1),
                "biweekly": timedelta(weeks=2),
            }
            next_job_time = job_time + intervals[job["recurrence"]]
            job["scheduled_time"] = next_job_time.isoformat()
          jobs_to_keep.append(
              job)  # Re-add the job, potentially with an updated time

        await file.seek(0)
        await file.write(json.dumps(jobs_to_keep, indent=4))
        await file.truncate()

    except Exception as e:
      print(f"Error in purge_check task: {e}")

  # Ensure that the bot is fully ready and connected before starting the purge check loop.
  @purge_check.before_loop
  async def before_purge_check(self):
    await self.client.wait_until_ready()


# Function to setup the cog when the bot starts.
async def setup(client: commands.Bot) -> None:
  await client.add_cog(SchedulePurge(client))
