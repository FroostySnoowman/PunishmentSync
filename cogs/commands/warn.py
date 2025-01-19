import discord
import yaml
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from cogs.functions.utils import warn_member

with open('config.yml', 'r') as file:
    data = yaml.safe_load(file)

embed_color = data["General"]["EMBED_COLOR"]
staff_guild_id = data["Staff"]["STAFF_GUILD_ID"]
staff_role_id = data["Staff"]["STAFF_ROLE_ID"]
staff_logs_channel_id = data["Staff"]["STAFF_LOGS_CHANNEL_ID"]

class WarnCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="warn", description="Warns a member!")
    @app_commands.describe(member="Who do you want to warn?")
    @app_commands.describe(reason="What is the reason for warning them?")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str) -> None:
        staff_guild = interaction.client.get_guild(staff_guild_id)
        staff_logs_channel = staff_guild.get_channel(staff_logs_channel_id)
        staff_user = staff_guild.get_member(interaction.user.id)
        staff_role = staff_guild.get_role(staff_role_id)

        if staff_role in staff_user.roles:
            embed = discord.Embed(title="MBL Punishments", description="Loading...", color=discord.Color.from_str(embed_color))
            await interaction.response.send_message(embed=embed, ephemeral=True)

            timestamp = int(datetime.now().timestamp())

            await warn_member(interaction, member, reason)

            try:
                embed = discord.Embed(title="MBL Punishments", description=f"{member.mention}, you were warned for {reason} at <t:{timestamp}:f>.", color=discord.Color.from_str(embed_color))
                await member.send(embed=embed)

                embed = discord.Embed(title="MBL Punishments", description=f"Successfully warned {member.mention}!", color=discord.Color.from_str(embed_color))
                await interaction.edit_original_response(embed=embed)
            except:
                embed = discord.Embed(title="MBL Punishments", description=f"Successfully warned {member.mention}!", color=discord.Color.from_str(embed_color))
                embed.set_footer(text="They were not notified.")
                await interaction.edit_original_response(embed=embed)

            embed = discord.Embed(title="MBL Punishments", description=f"**{member.mention}** was warned by {interaction.user} for **{reason}**.", color=discord.Color.from_str(embed_color))
            embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
            embed.timestamp = datetime.now()

            await staff_logs_channel.send(embed=embed)
        else:
            embed = discord.Embed(title="MBL Punishments", description="You do not have permission to use this command.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(WarnCog(bot))