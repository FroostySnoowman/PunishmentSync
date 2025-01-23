import discord
import aiosqlite
import yaml
from discord import app_commands
from discord.ext import commands, tasks
from async_mojang import API
from datetime import datetime
from typing import Optional
from cogs.functions.utils import convert_time_to_int, execute_command, ban_member

with open('config.yml', 'r') as file:
    data = yaml.safe_load(file)

embed_color = data["General"]["EMBED_COLOR"]
staff_guild_id = data["Staff"]["STAFF_GUILD_ID"]
staff_role_id = data["Staff"]["STAFF_ROLE_ID"]
staff_logs_channel_id = data["Staff"]["STAFF_LOGS_CHANNEL_ID"]
ban_command = data["Commands"]["BAN_COMMAND"]

guilds = {guild['ID']: guild['MUTED_ROLE_ID'] for guild in data['Guilds']}

class BanCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def cog_load(self):
        self.ban_loop.start()

    @tasks.loop(seconds=30)
    async def ban_loop(self):
        async with aiosqlite.connect('database.db') as db:
            cursor = await db.execute('SELECT * FROM bans WHERE expiration != "expired"')
            bans = await cursor.fetchall()

            for row in bans:
                if row[4] and row[4] <= datetime.now().timestamp():
                    await db.execute('UPDATE bans SET expiration = ? WHERE member_id = ?', ('expired', row[1]))

                for guild_id in guilds.keys():
                    guild = self.bot.get_guild(guild_id)
                    if guild is None:
                        continue

                    try:
                        member = discord.Object(id=row[1])
                        await guild.unban(member)
                    except:
                        continue

            await db.commit()

    @ban_loop.before_loop
    async def before_ban_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="ban", description="Bans a member!")
    @app_commands.describe(member="Who do you want to ban?")
    @app_commands.describe(reason="What is the reason for banning them?")
    @app_commands.describe(time="How long should they be banned for?")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str, time: Optional[str]) -> None:
        staff_guild = interaction.client.get_guild(staff_guild_id)
        staff_logs_channel = staff_guild.get_channel(staff_logs_channel_id)
        staff_user = staff_guild.get_member(interaction.user.id)
        staff_role = staff_guild.get_role(staff_role_id)

        if staff_role in staff_user.roles:
            embed = discord.Embed(title="Mort", description="Loading...", color=discord.Color.from_str(embed_color))
            await interaction.response.send_message(embed=embed, ephemeral=True)

            timestamp = int(datetime.now().timestamp())

            if time:
                ban_time, beautified = await convert_time_to_int(time)

            try:
                embed = discord.Embed(title="Mort", description=f"{member.mention}, you were banned from {interaction.guild.name} for {reason} at <t:{timestamp}:f>.", color=discord.Color.from_str(embed_color))
                await member.send(embed=embed)

                await ban_member(interaction, member, reason, ban_time + timestamp if time else None)

                embed = discord.Embed(title="Mort", description=f"Successfully banned {member.mention}! They will be banned {f'for {beautified}' if time else 'forever'}.", color=discord.Color.from_str(embed_color))
                await interaction.edit_original_response(embed=embed)
            except:
                await ban_member(interaction, member, reason, ban_time + timestamp if time else None)

                embed = discord.Embed(title="Mort", description=f"Successfully banned {member.mention}! They will be banned {f'for {beautified}' if time else 'forever'}.", color=discord.Color.from_str(embed_color))
                embed.set_footer(text="They were not notified.")
                await interaction.edit_original_response(embed=embed)
            
            embed = discord.Embed(title="Mort", description=f"**{member}** was banned by {interaction.user.mention} for **{reason}**.", color=discord.Color.from_str(embed_color))
            embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
            embed.timestamp = datetime.now()

            await staff_logs_channel.send(embed=embed)
        else:
            embed = discord.Embed(title="Mort", description="You do not have permission to use this command.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unban", description="Unbans a member!")
    @app_commands.describe(member_id="The ID of the member to unban.")
    async def unban(self, interaction: discord.Interaction, member_id: str) -> None:
        staff_guild = interaction.client.get_guild(staff_guild_id)
        staff_logs_channel = staff_guild.get_channel(staff_logs_channel_id)
        staff_user = staff_guild.get_member(interaction.user.id)
        staff_role = staff_guild.get_role(staff_role_id)

        if staff_role in staff_user.roles:
            embed = discord.Embed(title="Mort", description="Loading...", color=discord.Color.from_str(embed_color),)
            await interaction.response.send_message(embed=embed, ephemeral=True)

            async with aiosqlite.connect('database.db') as db:
                for guild_id in guilds.keys():
                    guild = self.bot.get_guild(guild_id)
                    if guild is None:
                        continue

                    try:
                        async for entry in guild.bans():
                            if str(entry.user.id) == member_id:
                                await guild.unban(entry.user)
                                break

                    except:
                        continue

                await db.execute('UPDATE bans SET expiration = ? WHERE member_id = ?', ('expired', member_id),)
                await db.commit()

            embed = discord.Embed(title="Mort", description=f"Successfully unbanned user with ID `{member_id}` from all guilds.", color=discord.Color.from_str(embed_color),)
            await interaction.edit_original_response(embed=embed)

            embed = discord.Embed(title="Mort", description=f"**{member_id}** was unbanned by {interaction.user.mention}.", color=discord.Color.from_str(embed_color))
            embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
            embed.timestamp = datetime.now()

            await staff_logs_channel.send(embed=embed)
        else:
            embed = discord.Embed(title="Mort", description="You do not have permission to use this command.", color=discord.Color.red(),)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="iban", description="Bans an in game player!")
    @app_commands.describe(name="Who do you want to ban?")
    @app_commands.describe(uuid="Who do you want to ban?")
    @app_commands.describe(reason="What is the reason for banning them?")
    @app_commands.describe(time="How long should they be banned for?")
    async def iban(self, interaction: discord.Interaction, name: Optional[str], uuid: Optional[str], reason: str, time: Optional[str]) -> None:
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
                    command = ban_command.replace("{name}", name).replace("{uuid}", uuid).replace("{reason}", reason)
                    command = command.replace("{time}", "").strip()
                    command = " ".join(command.split())
                else:
                    command = ban_command.replace("{name}", name).replace("{uuid}", uuid).replace("{reason}", reason).replace("{time}", time)

                await execute_command(command)

                response = await execute_command(command)

                if response:
                    embed = discord.Embed(title="Mort", description=f"Successfully banned {name}! They will be banned {f'for {time}' if time else 'forever'}.", color=discord.Color.from_str(embed_color))
                    await interaction.edit_original_response(embed=embed)
                else:
                    embed = discord.Embed(title="Mort", description=f"Failed to connect to the server!", color=discord.Color.red())
                    await interaction.edit_original_response(embed=embed)

            embed = discord.Embed(title="Mort", description=f"**{name}** was banned by **{interaction.user}**.", color=discord.Color.from_str(embed_color))
            embed.set_footer(text="In game player.")
            embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
            embed.timestamp = datetime.now()

            await staff_logs_channel.send(embed=embed)
        else:
            embed = discord.Embed(title="Mort", description="You do not have permission to use this command.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(BanCog(bot))