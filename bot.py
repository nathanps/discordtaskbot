#!/usr/bin/env python3
import discord
from discord import app_commands

import config
import tasks
import git_ops
import server_config


intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    print("Syncing commands...")
    synced = await tree.sync()
    print(f"Synced {len(synced)} commands: {[c.name for c in synced]}")


async def send_update(interaction: discord.Interaction, message: str) -> None:
    """Send update to configured channel, or fallback to interaction channel."""
    guild_id = interaction.guild_id
    channel_id = server_config.get_updates_channel(guild_id) if guild_id else None

    if channel_id:
        channel = client.get_channel(channel_id)
        if channel:
            try:
                await channel.send(message)
                await interaction.followup.send("Done!", ephemeral=True)
                return
            except discord.Forbidden:
                pass  # Fall back to interaction channel

    await interaction.followup.send(message)


@tree.command(name="task", description="Create a new task")
@app_commands.describe(
    description="Task description",
    category="Optional category (e.g., bugs, features)"
)
async def cmd_task(interaction: discord.Interaction, description: str, category: str = ""):
    if not interaction.guild_id:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        git_ops.pull()
        task = tasks.add_task(interaction.guild_id, description, interaction.user.name, category)
        git_ops.commit_and_push(f"Added task #{task.id}: {description[:50]}")
        cat_text = f" [{task.category}]" if task.category else ""
        await interaction.followup.send(f"Created task **#{task.id}**{cat_text}: {task.task_name}")
    except git_ops.GitError as e:
        await interaction.followup.send(f"Git error: {e}")


@tree.command(name="tasklist", description="List tasks")
@app_commands.describe(
    filter="Filter: 'done', 'all', or a category name",
    limit="Max tasks to show (default 15)"
)
async def cmd_tasklist(interaction: discord.Interaction, filter: str = "", limit: int = config.DEFAULT_LIMIT):
    if not interaction.guild_id:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        git_ops.pull()
    except git_ops.GitError as e:
        await interaction.followup.send(f"Git error: {e}")
        return

    # Determine filter type
    state_filter = None
    category_filter = None

    if filter.lower() in ("done", "all"):
        state_filter = filter.lower()
    elif filter:
        category_filter = filter

    task_list = tasks.get_tasks(
        interaction.guild_id,
        state_filter=state_filter,
        category_filter=category_filter,
        limit=limit
    )

    if not task_list:
        await interaction.followup.send("No tasks found.")
        return

    lines = []
    for t in task_list:
        state_emoji = {"open": "⬜", "in-progress": "🔄", "done": "✅"}.get(t.state, "❓")
        cat = f"[{t.category}] " if t.category else ""
        assignee = f" → {t.assignee}" if t.assignee else ""
        lines.append(f"{state_emoji} **#{t.id}** {cat}{t.task_name}{assignee}")

    header = f"**Tasks** (showing {len(task_list)})"
    if filter:
        header += f" — filter: `{filter}`"

    await interaction.followup.send(f"{header}\n" + "\n".join(lines))


@tree.command(name="taskmine", description="List your assigned tasks")
@app_commands.describe(limit="Max tasks to show (default 15)")
async def cmd_taskmine(interaction: discord.Interaction, limit: int = config.DEFAULT_LIMIT):
    if not interaction.guild_id:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        git_ops.pull()
    except git_ops.GitError as e:
        await interaction.followup.send(f"Git error: {e}")
        return

    task_list = tasks.get_tasks(
        interaction.guild_id,
        assignee_filter=interaction.user.name,
        limit=limit
    )

    if not task_list:
        await interaction.followup.send("No tasks assigned to you.")
        return

    lines = []
    for t in task_list:
        state_emoji = {"open": "⬜", "in-progress": "🔄", "done": "✅"}.get(t.state, "❓")
        cat = f"[{t.category}] " if t.category else ""
        lines.append(f"{state_emoji} **#{t.id}** {cat}{t.task_name}")

    await interaction.followup.send(f"**Your Tasks** (showing {len(task_list)})\n" + "\n".join(lines))


@tree.command(name="taskconfig", description="Configure task bot settings")
@app_commands.describe(channel="Channel for task update notifications")
async def cmd_taskconfig(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.guild_id:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    server_config.set_updates_channel(interaction.guild_id, channel.id)
    await interaction.response.send_message(f"Task updates will now be posted to {channel.mention}")


@tree.command(name="taskdone", description="Mark a task as done")
@app_commands.describe(task_id="Task ID number")
async def cmd_taskdone(interaction: discord.Interaction, task_id: int):
    if not interaction.guild_id:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        git_ops.pull()
        task = tasks.update_task_state(interaction.guild_id, task_id, "done")
        if task:
            git_ops.commit_and_push(f"Marked task #{task_id} as done")
            await send_update(interaction, f"**{interaction.user.name}** marked task **#{task_id}** as done: {task.task_name}")
        else:
            await interaction.followup.send(f"Task #{task_id} not found.")
    except git_ops.GitError as e:
        await interaction.followup.send(f"Git error: {e}")


@tree.command(name="taskprogress", description="Mark a task as in-progress and assign to yourself")
@app_commands.describe(task_id="Task ID number")
async def cmd_taskprogress(interaction: discord.Interaction, task_id: int):
    if not interaction.guild_id:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        git_ops.pull()
        task = tasks.update_task_state(interaction.guild_id, task_id, "in-progress")
        if task:
            tasks.assign_task(interaction.guild_id, task_id, interaction.user.name)
            git_ops.commit_and_push(f"Marked task #{task_id} as in-progress ({interaction.user.name})")
            await send_update(interaction, f"**{interaction.user.name}** started task **#{task_id}**: {task.task_name}")
        else:
            await interaction.followup.send(f"Task #{task_id} not found.")
    except git_ops.GitError as e:
        await interaction.followup.send(f"Git error: {e}")


@tree.command(name="taskassign", description="Assign a task to someone")
@app_commands.describe(task_id="Task ID number", user="User to assign")
async def cmd_taskassign(interaction: discord.Interaction, task_id: int, user: discord.Member):
    if not interaction.guild_id:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        git_ops.pull()
        task = tasks.assign_task(interaction.guild_id, task_id, user.name)
        if task:
            git_ops.commit_and_push(f"Assigned task #{task_id} to {user.name}")
            await send_update(interaction, f"**{interaction.user.name}** assigned task **#{task_id}** to **{user.name}**: {task.task_name}")
        else:
            await interaction.followup.send(f"Task #{task_id} not found.")
    except git_ops.GitError as e:
        await interaction.followup.send(f"Git error: {e}")


@tree.command(name="tasknote", description="Add a note to a task")
@app_commands.describe(task_id="Task ID number", note="Note to add")
async def cmd_tasknote(interaction: discord.Interaction, task_id: int, note: str):
    if not interaction.guild_id:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        git_ops.pull()
        task = tasks.add_note(interaction.guild_id, task_id, note)
        if task:
            git_ops.commit_and_push(f"Added note to task #{task_id}")
            await send_update(interaction, f"**{interaction.user.name}** added note to task **#{task_id}**: {note}")
        else:
            await interaction.followup.send(f"Task #{task_id} not found.")
    except git_ops.GitError as e:
        await interaction.followup.send(f"Git error: {e}")


@tree.command(name="taskdelete", description="Delete a task")
@app_commands.describe(task_id="Task ID number")
async def cmd_taskdelete(interaction: discord.Interaction, task_id: int):
    if not interaction.guild_id:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        git_ops.pull()
        if tasks.delete_task(interaction.guild_id, task_id):
            git_ops.commit_and_push(f"Deleted task #{task_id}")
            await send_update(interaction, f"**{interaction.user.name}** deleted task **#{task_id}**")
        else:
            await interaction.followup.send(f"Task #{task_id} not found.")
    except git_ops.GitError as e:
        await interaction.followup.send(f"Git error: {e}")


if __name__ == "__main__":
    if not config.DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN not set. Copy .env.example to .env and add your token.")
        exit(1)
    client.run(config.DISCORD_TOKEN)
