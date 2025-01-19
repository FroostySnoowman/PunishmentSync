import discord
import yaml
from discord import app_commands
from discord.ext import commands
from async_mojang import API
from datetime import datetime
from typing import Optional
from cogs.functions.utils import execute_command, kick_member

with open('config.yml', 'r') as file:
    data = yaml.safe_load(file)

embed_color = data["General"]["EMBED_COLOR"]
staff_guild_id = data["Staff"]["STAFF_GUILD_ID"]
staff_role_id = data["Staff"]["STAFF_ROLE_ID"]
staff_logs_channel_id = data["Staff"]["STAFF_LOGS_CHANNEL_ID"]
kick_command = data["Commands"]["KICK_COMMAND"]

class KickCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="kick", description="Kicks a member!")
    @app_commands.describe(member="Who do you want to kick?")
    @app_commands.describe(reason="What is the reason for kicking them?")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str) -> None:
        staff_guild = interaction.client.get_guild(staff_guild_id)
        staff_logs_channel = staff_guild.get_channel(staff_logs_channel_id)
        staff_user = staff_guild.get_member(interaction.user.id)
        staff_role = staff_guild.get_role(staff_role_id)

        if staff_role in staff_user.roles:
            embed = discord.Embed(title="MBL Punishments", description="Loading...", color=discord.Color.from_str(embed_color))
            await interaction.response.send_message(embed=embed, ephemeral=True)

            timestamp = int(datetime.now().timestamp())

            try:
                embed = discord.Embed(title="MBL Punishments", description=f"{member.mention}, you were kicked from {interaction.guild.name} for {reason} at <t:{timestamp}:f>.", color=discord.Color.from_str(embed_color))
                await member.send(embed=embed)

                await kick_member(interaction, member, reason)

                embed = discord.Embed(title="MBL Punishments", description=f"Successfully kicked {member.mention}!", color=discord.Color.from_str(embed_color))
                await interaction.edit_original_response(embed=embed)
            except:
                await kick_member(interaction, member, reason)

                embed = discord.Embed(title="MBL Punishments", description=f"Successfully kicked {member.mention}!", color=discord.Color.from_str(embed_color))
                embed.set_footer(text="They were not notified.")
                await interaction.edit_original_response(embed=embed)
            
            embed = discord.Embed(title="MBL Punishments", description=f"**{member.mention}** was kicked by {interaction.user} for **{reason}**.", color=discord.Color.from_str(embed_color))
            embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
            embed.timestamp = datetime.now()

            await staff_logs_channel.send(embed=embed)
        else:
            embed = discord.Embed(title="MBL Punishments", description="You do not have permission to use this command.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ikick", description="Kicks an in game player!")
    @app_commands.describe(name="Who do you want to kick?")
    @app_commands.describe(uuid="Who do you want to kick?")
    @app_commands.describe(reason="What is the reason for kicking them?")
    async def ikick(self, interaction: discord.Interaction, name: Optional[str], uuid: Optional[str], reason: str) -> None:
        staff_guild = interaction.client.get_guild(staff_guild_id)
        staff_logs_channel = staff_guild.get_channel(staff_logs_channel_id)
        staff_user = staff_guild.get_member(interaction.user.id)
        staff_role = staff_guild.get_role(staff_role_id)

        if staff_role in staff_user.roles:
            embed = discord.Embed(title="MBL Punishments", description="Loading...", color=discord.Color.from_str(embed_color))
            await interaction.response.send_message(embed=embed, ephemeral=True)

            async with API() as api:
                if not name:
                    if not uuid:
                        embed = discord.Embed(title="MBL Punishments", description="You must provide a name or UUID.", color=discord.Color.red())
                        await interaction.edit_original_response(embed=embed, ephemeral=True)
                        return
                    else:
                        try:
                            name = await api.get_username(uuid)
                        except:
                            embed = discord.Embed(title="MBL Punishments", description="Invalid UUID.", color=discord.Color.red())
                            await interaction.edit_original_response(embed=embed, ephemeral=True)
                            return
                else:
                    if not uuid:
                        try:
                            uuid = await api.get_uuid(name)
                        except:
                            embed = discord.Embed(title="MBL Punishments", description="Invalid name.", color=discord.Color.red())
                            await interaction.edit_original_response(embed=embed, ephemeral=True)
                            return
                    else:
                        embed = discord.Embed(title="MBL Punishments", description="You must provide a name or UUID, not both.", color=discord.Color.red())
                        await interaction.edit_original_response(embed=embed, ephemeral=True)
                        return
                
                command = kick_command.replace("{name}", name).replace("{uuid}", uuid).replace("{reason}", reason)

                await execute_command(command)

                response = await execute_command(command)

                if response:
                    embed = discord.Embed(title="MBL Punishments", description=f"Successfully kicked {name}!", color=discord.Color.from_str(embed_color))
                    await interaction.edit_original_response(embed=embed)
                else:
                    embed = discord.Embed(title="MBL Punishments", description=f"Failed to connect to the server!", color=discord.Color.red())
                    await interaction.edit_original_response(embed=embed)

            embed = discord.Embed(title="MBL Punishments", description=f"**{name}** was kicked by **{interaction.user}**.", color=discord.Color.from_str(embed_color))
            embed.set_footer(text="In game player.")
            embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
            embed.timestamp = datetime.now()

            await staff_logs_channel.send(embed=embed)
        else:
            embed = discord.Embed(title="MBL Punishments", description="You do not have permission to use this command.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(KickCog(bot))