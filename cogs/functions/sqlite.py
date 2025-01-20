import discord
import aiosqlite
import sqlite3
import yaml
from discord.ext import commands
from discord import app_commands
from typing import Literal

with open('config.yml', 'r') as file:
    data = yaml.safe_load(file)

embed_color = data["General"]["EMBED_COLOR"]

async def check_tables():
    await bans()
    await kicks()
    await mutes()
    await warns()

async def refresh_table(table: str):
    if table == "Bans":
        await bans(True)
    elif table == "Kicks":
        await kicks(True)
    elif table == "Mutes":
        await mutes(True)
    elif table == "Warns":
        await warns(True)

async def kicks(delete: bool = False):
    async with aiosqlite.connect('database.db') as db:
        if delete:
            try:
                await db.execute('DROP TABLE kicks')
                await db.commit()
            except sqlite3.OperationalError:
                pass

        try:
            await db.execute('SELECT * FROM kicks')
        except sqlite3.OperationalError:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS kicks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id INTEGER,
                    reason STRING,
                    moderator_id STRING,
                    timestamp INTEGER
                )
            """)
            await db.commit()

async def warns(delete: bool = False):
    async with aiosqlite.connect('database.db') as db:
        if delete:
            try:
                await db.execute('DROP TABLE warns')
                await db.commit()
            except sqlite3.OperationalError:
                pass

        try:
            await db.execute('SELECT * FROM warns')
        except sqlite3.OperationalError:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS warns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id INTEGER,
                    reason STRING,
                    moderator_id STRING,
                    timestamp INTEGER
                )
            """)
            await db.commit()

async def bans(delete: bool = False):
    async with aiosqlite.connect('database.db') as db:
        if delete:
            try:
                await db.execute('DROP TABLE bans')
                await db.commit()
            except sqlite3.OperationalError:
                pass

        try:
            await db.execute('SELECT * FROM bans')
        except sqlite3.OperationalError:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id INTEGER,
                    reason STRING,
                    moderator_id STRING,
                    timestamp INTEGER,
                    expiration INTEGER DEFAULT NULL
                )
            """)
            await db.commit()

async def mutes(delete: bool = False):
    async with aiosqlite.connect('database.db') as db:
        if delete:
            try:
                await db.execute('DROP TABLE mutes')
                await db.commit()
            except sqlite3.OperationalError:
                pass

        try:
            await db.execute('SELECT * FROM mutes')
        except sqlite3.OperationalError:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS mutes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id INTEGER,
                    reason STRING,
                    moderator_id STRING,
                    timestamp INTEGER,
                    expiration INTEGER DEFAULT NULL
                )
            """)
            await db.commit()

class SQLiteCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="refreshtable", description="Refreshes a SQLite table!")
    @app_commands.describe(table="What table should be refreshed?")
    @app_commands.default_permissions(administrator=True)
    async def refreshtable(self, interaction: discord.Interaction, table: Literal["Bans", "Kicks", "Mutes", "Warns"]) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        if await self.bot.is_owner(interaction.user):
            await refresh_table(table)
            embed = discord.Embed(title="Mort", description=f"Successfully refreshed the table **{table}**!", color=discord.Color.from_str(embed_color))
        else:
            embed = discord.Embed(title="Mort", description="You do not have permission to use this command!", color=discord.Color.red())
        
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(SQLiteCog(bot))