import discord
import aiosqlite
import asyncio
import yaml
import re
from datetime import datetime
from aiomcrcon import Client

with open('config.yml', 'r') as file:
    data = yaml.safe_load(file)

rcon_host = data["RCON"]["HOST"]
rcon_port = data["RCON"]["PORT"]
rcon_password = data["RCON"]["PASSWORD"]

guilds = {guild['ID']: guild['MUTED_ROLE_ID'] for guild in data['Guilds']}

async def execute_command(command: str, timeout=5):
    try:
        async with Client(rcon_host, rcon_port, rcon_password) as client:
            await asyncio.wait_for(client.send_cmd(command), timeout=timeout)
            return True
    except:
        return False

async def kick_member(interaction: discord.Interaction, member: discord.Member, reason: str) -> None:
    async with aiosqlite.connect('database.db') as db:
        timestamp = int(datetime.now().timestamp())

        await db.execute('INSERT INTO kicks (member_id, reason, moderator_id, timestamp) VALUES (?,?,?,?)', (member.id, reason, interaction.user.id, timestamp))
        await db.commit()

        for guild_id in guilds.keys():
            guild = interaction.client.get_guild(guild_id)
            if guild is None:
                continue

            try:
                await guild.kick(member, reason=reason)
            except:
                continue

async def warn_member(interaction: discord.Interaction, member: discord.Member, reason: str) -> None:
    async with aiosqlite.connect('database.db') as db:
        timestamp = int(datetime.now().timestamp())

        await db.execute('INSERT INTO warns (member_id, reason, moderator_id, timestamp) VALUES (?,?,?,?)', (member.id, reason, interaction.user.id, timestamp))
        await db.commit()

async def ban_member(interaction: discord.Interaction, member: discord.User, reason: str, expiration: int = None) -> None:
    async with aiosqlite.connect('database.db') as db:
        timestamp = int(datetime.now().timestamp())

        await db.execute('INSERT INTO bans (member_id, reason, moderator_id, timestamp, expiration) VALUES (?,?,?,?,?)', (member.id, reason, interaction.user.id, timestamp, expiration))
        await db.commit()

        for guild_id in guilds.keys():
            guild = interaction.client.get_guild(guild_id)

            if guild is None:
                continue

            try:
                await guild.ban(discord.Object(id=member.id), reason=reason)
            except:
                continue

async def mute_member(interaction: discord.Interaction, member: discord.Member, reason: str, expiration: int = None) -> None:
    async with aiosqlite.connect('database.db') as db:
        timestamp = int(datetime.now().timestamp())

        await db.execute('INSERT INTO mutes (member_id, reason, moderator_id, timestamp, expiration) VALUES (?,?,?,?,?)', (member.id, reason, interaction.user.id, timestamp, expiration))
        await db.commit()

        for guild_id in guilds.keys():
            guild = interaction.client.get_guild(guild_id)

            member_in_guild = guild.get_member(member.id)

            if member_in_guild is None:
                continue

            if guild is None:
                continue

            muted_role_id = guilds[guild_id]
            muted_role = guild.get_role(muted_role_id)

            if muted_role is None:
                continue

            try:
                await member_in_guild.add_roles(muted_role, reason=reason)
            except:
                continue