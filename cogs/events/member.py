import discord
import aiosqlite
import yaml
from discord.ext import commands
from datetime import datetime

with open('config.yml', 'r') as file:
    data = yaml.safe_load(file)

embed_color = data["General"]["EMBED_COLOR"]
guilds = {guild['ID']: guild['MUTED_ROLE_ID'] for guild in data['Guilds']}

class MemberEventsCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        async with aiosqlite.connect('database.db') as db:
            cursor = await db.execute('SELECT * FROM mutes WHERE member_id = ? AND (expiration IS NULL OR expiration > ?)', (member.id, datetime.now().timestamp()))
            mute_record = await cursor.fetchone()

            if mute_record:
                for guild_id, muted_role_id in guilds.items():
                    guild = self.bot.get_guild(guild_id)
                    if not guild:
                        continue

                    muted_role = guild.get_role(muted_role_id)
                    if not muted_role:
                        continue

                    member_in_guild = guild.get_member(member.id)
                    if not member_in_guild:
                        continue

                    try:
                        await member_in_guild.add_roles(muted_role, reason="Re-applied muted role after rejoining.")
                    except:
                        continue

async def setup(bot: commands.Bot):
    await bot.add_cog(MemberEventsCog(bot))