import discord
import aiosqlite
import yaml
import re
from discord import app_commands
from discord.ext import commands, tasks
from async_mojang import API
from datetime import datetime, timedelta
from typing import Optional
from cogs.functions.utils import execute_command, mute_member

with open('config.yml', 'r') as file:
    data = yaml.safe_load(file)

embed_color = data["General"]["EMBED_COLOR"]
staff_guild_id = data["Staff"]["STAFF_GUILD_ID"]
staff_role_id = data["Staff"]["STAFF_ROLE_ID"]
staff_logs_channel_id = data["Staff"]["STAFF_LOGS_CHANNEL_ID"]
mute_command = data["Commands"]["MUTE_COMMAND"]

guilds = {guild['ID']: guild['MUTED_ROLE_ID'] for guild in data['Guilds']}

class MuteCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def cog_load(self):
        self.mute_loop.start()

    @tasks.loop(seconds=30)
    async def mute_loop(self):
        async with aiosqlite.connect('database.db') as db:
            cursor = await db.execute('SELECT * FROM mutes WHERE expiration != "expired"')
            mutes = await cursor.fetchall()

            for mute in mutes:
                member_id = mute[1]
                expiration_time = mute[5]

                if expiration_time and expiration_time <= int(datetime.now().timestamp()):
                    await db.execute('UPDATE mutes SET expiration = ? WHERE member_id = ?', ('expired', member_id))
                    await db.commit()

                    cursor_check = await db.execute('SELECT expiration FROM mutes WHERE member_id = ?', (member_id,))
                    expiration_status = await cursor_check.fetchone()

                    if expiration_status and expiration_status[0] == "expired":
                        for guild_id in guilds.keys():
                            guild = self.bot.get_guild(guild_id)
                            if guild is None:
                                continue

                            member = guild.get_member(member_id)
                            if member is None:
                                continue

                            muted_role_id = guilds[guild_id]
                            muted_role = guild.get_role(muted_role_id)
                            if muted_role is None:
                                continue

                            try:
                                await member.remove_roles(muted_role)
                            except:
                                continue

    @mute_loop.before_loop
    async def before_mute_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="mute", description="Mutes a member!")
    @app_commands.describe(member="Who do you want to mute?")
    @app_commands.describe(reason="What is the reason for muting them?")
    @app_commands.describe(time="How long should they be muted for?")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, reason: str, time: Optional[str]) -> None:
        staff_guild = interaction.client.get_guild(staff_guild_id)
        staff_logs_channel = staff_guild.get_channel(staff_logs_channel_id)
        staff_user = staff_guild.get_member(interaction.user.id)
        staff_role = staff_guild.get_role(staff_role_id)

        if staff_role in staff_user.roles:
            embed = discord.Embed(title="Mort", description="Loading...", color=discord.Color.from_str(embed_color))
            await interaction.response.send_message(embed=embed, ephemeral=True)

            timestamp = int(datetime.now().timestamp())

            if time:
                time_list = re.split('(\d+)', time)
                if time_list[2] == "s":
                    time_in_s = int(time_list[1])
                if time_list[2] == "m":
                    time_in_s = int(time_list[1]) * 60
                if time_list[2] == "h":
                    time_in_s = int(time_list[1]) * 60 * 60
                if time_list[2] == "d":
                    time_in_s = int(time_list[1]) * 60 * 60 * 24
                
                ts = datetime.now().timestamp()
                ts = datetime.now() + timedelta(seconds=time_in_s)
                mute_time = int(ts.timestamp())

            try:
                embed = discord.Embed(title="Mort", description=f"{member.mention}, you were muted for {reason} at <t:{timestamp}:f>.{f' This mute will expire at <t:{mute_time}:F>' if time else ''}", color=discord.Color.from_str(embed_color))
                embed.timestamp = datetime.now()
                await member.send(embed=embed)

                await mute_member(interaction, member, reason, mute_time if time else None)

                embed = discord.Embed(title="Mort", description=f"Successfully muted {member.mention}! They will be muted {f'for {time}' if time else 'forever'}.", color=discord.Color.from_str(embed_color))
                await interaction.edit_original_response(embed=embed)
            except:
                await mute_member(interaction, member, reason, mute_time if time else None)

                embed = discord.Embed(title="Mort", description=f"Successfully muted {member.mention}! They will be muted {f'for {time}' if time else 'forever'}.", color=discord.Color.from_str(embed_color))
                embed.set_footer(text="They were not notified.")
                await interaction.edit_original_response(embed=embed)

            embed = discord.Embed(title="Mort", description=f"**{member.mention}** was muted by {interaction.user} for **{reason}**.", color=discord.Color.from_str(embed_color))
            embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
            embed.timestamp = datetime.now()

            await staff_logs_channel.send(embed=embed)
        else:
            embed = discord.Embed(title="Mort", description="You do not have permission to use this command.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unmute", description="Unmutes a member!")
    @app_commands.describe(member="Who do you want to unmute?")
    async def unmute(self, interaction: discord.Interaction, member: discord.Member) -> None:
        staff_guild = interaction.client.get_guild(staff_guild_id)
        staff_logs_channel = staff_guild.get_channel(staff_logs_channel_id)
        staff_user = staff_guild.get_member(interaction.user.id)
        staff_role = staff_guild.get_role(staff_role_id)

        if staff_role in staff_user.roles:
            embed = discord.Embed(title="Mort", description="Loading...", color=discord.Color.from_str(embed_color))
            await interaction.response.send_message(embed=embed, ephemeral=True)

            async with aiosqlite.connect('database.db') as db:
                for guild_id in guilds.keys():
                    guild = interaction.client.get_guild(guild_id)

                    if guild is None:
                        continue

                    member_in_guild = guild.get_member(member.id)

                    if member_in_guild is None:
                        continue

                    muted_role_id = guilds[guild_id]
                    muted_role = guild.get_role(muted_role_id)

                    if muted_role is None:
                        continue

                    try:
                        await member_in_guild.remove_roles(muted_role)
                    except:
                        continue

                await db.execute('UPDATE mutes SET expiration = ? WHERE member_id = ?', ('expired', member.id))
                await db.commit()

            embed = discord.Embed(title="Mort", description=f"Successfully unmuted {member.mention} in all guilds.", color=discord.Color.from_str(embed_color))
            await interaction.edit_original_response(embed=embed)

            embed = discord.Embed(title="Mort", description=f"**{member.mention}** was unmuted by **{interaction.user}**.", color=discord.Color.from_str(embed_color))
            embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
            embed.timestamp = datetime.now()

            await staff_logs_channel.send(embed=embed)
        else:
            embed = discord.Embed(title="Mort", description="You do not have permission to use this command.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="imute", description="Mutes an in game player!")
    @app_commands.describe(name="Who do you want to mute?")
    @app_commands.describe(uuid="Who do you want to mute?")
    @app_commands.describe(reason="What is the reason for muting them?")
    @app_commands.describe(time="How long should they be muted for?")
    async def imute(self, interaction: discord.Interaction, name: Optional[str], uuid: Optional[str], reason: str, time: Optional[str]) -> None:
        staff_guild = interaction.client.get_guild(staff_guild_id)
        staff_logs_channel = staff_guild.get_channel(staff_logs_channel_id)
        staff_user = staff_guild.get_member(interaction.user.id)
        staff_role = staff_guild.get_role(staff_role_id)

        if staff_role in staff_user.roles:
            embed = discord.Embed(title="Mort", description="Loading...", color=discord.Color.from_str(embed_color))
            await interaction.response.send_message(embed=embed, ephemeral=True)

            async with API() as api:
                if not name:
                    if not uuid:
                        embed = discord.Embed(title="Mort", description="You must provide a name or UUID.", color=discord.Color.red())
                        await interaction.edit_original_response(embed=embed)
                        return
                    else:
                        try:
                            name = await api.get_username(uuid)
                        except:
                            embed = discord.Embed(title="Mort", description="Invalid UUID.", color=discord.Color.red())
                            await interaction.edit_original_response(embed=embed)
                            return
                else:
                    if not uuid:
                        try:
                            uuid = await api.get_uuid(name)
                        except:
                            embed = discord.Embed(title="Mort", description="Invalid name.", color=discord.Color.red())
                            await interaction.edit_original_response(embed=embed)
                            return
                    else:
                        embed = discord.Embed(title="Mort", description="You must provide a name or UUID, not both.", color=discord.Color.red())
                        await interaction.edit_original_response(embed=embed)
                        return
                
                if time is None:
                    command = mute_command.replace("{name}", name).replace("{uuid}", uuid).replace("{reason}", reason)
                    command = command.replace("{time}", "").strip()
                    command = " ".join(command.split())
                else:
                    command = mute_command.replace("{name}", name).replace("{uuid}", uuid).replace("{reason}", reason).replace("{time}", time)

                await execute_command(command)

                response = await execute_command(command)

                if response:
                    embed = discord.Embed(title="Mort", description=f"Successfully muted {name}! They will be muted {f'for {time}' if time else 'forever'}.", color=discord.Color.from_str(embed_color))
                    await interaction.edit_original_response(embed=embed)
                else:
                    embed = discord.Embed(title="Mort", description=f"Failed to connect to the server!", color=discord.Color.red())
                    await interaction.edit_original_response(embed=embed)

            embed = discord.Embed(title="Mort", description=f"**{name}** was muted by **{interaction.user}**.", color=discord.Color.from_str(embed_color))
            embed.set_footer(text="In game player")
            embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
            embed.timestamp = datetime.now()

            await staff_logs_channel.send(embed=embed)
        else:
            embed = discord.Embed(title="Mort", description="You do not have permission to use this command.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(MuteCog(bot))