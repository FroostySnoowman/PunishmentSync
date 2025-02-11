import discord
import aiosqlite
import yaml
import math
from discord import app_commands
from discord.ext import commands

with open('config.yml', 'r') as file:
    data = yaml.safe_load(file)

embed_color = data["General"]["EMBED_COLOR"]
staff_guild_id = data["Staff"]["STAFF_GUILD_ID"]
staff_role_id = data["Staff"]["STAFF_ROLE_ID"]
staff_logs_channel_id = data["Staff"]["STAFF_LOGS_CHANNEL_ID"]

class HistoryPages(discord.ui.View):
    def __init__(self, records: list, page: int, total_pages: int, punishment_type: str):
        super().__init__(timeout=None)
        self.records = records
        self.page = page
        self.total_pages = total_pages
        self.punishment_type = punishment_type
        self.slices = [(i, min(i + 25, len(records))) for i in range(0, len(records), 25)]

    def generate_embed(self):
        start, end = self.slices[self.page - 1]
        embed = discord.Embed(title="Mort", description=f"History of {self.punishment_type}", color=discord.Color.from_str(embed_color))

        for idx, record in enumerate(self.records[start:end], start=start + 1):
            embed.add_field(
                name=f"{self.punishment_type[:-1]} #{idx}",
                value=(
                    f"Reason: {record[2]}\n"
                    f"Moderator: <@{record[3]}>\n"
                    f"Time: <t:{record[4]}:f>"
                ),
                inline=False
            )

        embed.set_footer(text=f"Page {self.page} of {self.total_pages}")
        return embed

    @discord.ui.button(emoji='⏪', style=discord.ButtonStyle.blurple, custom_id='history_pages:1')
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        view = HistoryPages(self.records, 1, self.total_pages, self.punishment_type)
        view.first.disabled = True
        view.back.disabled = True
        if self.total_pages == 1:
            view.forward.disabled = True
            view.last.disabled = True

        embed = view.generate_embed()
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(emoji='⬅️', style=discord.ButtonStyle.blurple, custom_id='history_pages:2')
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        view = HistoryPages(self.records, self.page - 1, self.total_pages, self.punishment_type)
        view.first.disabled = (self.page - 1) == 1
        view.back.disabled = (self.page - 1) == 1
        view.forward.disabled = False
        view.last.disabled = False

        embed = view.generate_embed()
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(emoji='➡️', style=discord.ButtonStyle.blurple, custom_id='history_pages:3')
    async def forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        view = HistoryPages(self.records, self.page + 1, self.total_pages, self.punishment_type)
        view.first.disabled = False
        view.back.disabled = False
        view.forward.disabled = (self.page + 1) == self.total_pages
        view.last.disabled = (self.page + 1) == self.total_pages

        embed = view.generate_embed()
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(emoji='⏩', style=discord.ButtonStyle.blurple, custom_id='history_pages:4')
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        view = HistoryPages(self.records, self.total_pages, self.total_pages, self.punishment_type)
        view.first.disabled = False
        view.back.disabled = False
        view.forward.disabled = True
        view.last.disabled = True

        embed = view.generate_embed()
        await interaction.edit_original_response(embed=embed, view=view)

class History(discord.ui.Select):
    def __init__(self, user: discord.User):
        self.user = user
        options = [
            discord.SelectOption(label='Bans'),
            discord.SelectOption(label='Kicks'),
            discord.SelectOption(label='Mutes'),
            discord.SelectOption(label='Warns'),
        ]
        super().__init__(placeholder='Select the punishment type', min_values=1, max_values=1, options=options, custom_id="history:1")

    async def callback(self, interaction: discord.Interaction):
        punishment_type = self.values[0]

        async with aiosqlite.connect('database.db') as db:
            cursor = await db.execute(f'SELECT * FROM {punishment_type.lower()} WHERE member_id = ?', (self.user.id,))
            records = await cursor.fetchall()

            if records == []:
                embed = discord.Embed(title="Mort", description=f"{self.user.name} has no {punishment_type.lower()}!", color=discord.Color.from_str(embed_color))
                await interaction.response.edit_message(embed=embed)
                return

        total_pages = math.ceil(len(records) / 25) or 1

        embed = discord.Embed(title="Mort", color=discord.Color.from_str(embed_color))
        embed.set_footer(text=f"Page 1 of {total_pages}")

        view = HistoryPages(records, 1, total_pages, punishment_type)
        view.add_item(History(self.user))
        view.first.disabled = True
        view.back.disabled = True
        if total_pages == 1:
            view.forward.disabled = True
            view.last.disabled = True

        embed = view.generate_embed()
        await interaction.response.edit_message(embed=embed, view=view)

class HistoryView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=None)
        self.add_item(History(user))

class HistoryCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="history", description="Views the history of a user!")
    @app_commands.describe(user="Who's history would you like to view?")
    async def history(self, interaction: discord.Interaction, user: discord.User) -> None:
        staff_guild = interaction.client.get_guild(staff_guild_id)
        staff_user = staff_guild.get_member(interaction.user.id)
        staff_role = staff_guild.get_role(staff_role_id)

        if staff_role in staff_user.roles:
            embed = discord.Embed(title="Mort", color=discord.Color.from_str(embed_color))
            await interaction.response.send_message(embed=embed, view=HistoryView(user), ephemeral=True)
        else:
            embed = discord.Embed(title="Mort", description="You do not have permission to use this command.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(HistoryCog(bot))