import nextcord
from nextcord.ext import commands
from nextcord import Interaction
from nextcord.ui import Select

from random import randint
import datetime
import cooldowns


class Fish(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.coin = "<:coins:585233801320333313>"

	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5400, bucket=cooldowns.SlashBucket.author)
	async def fish(self, interaction:Interaction):
		self.bot.get_cog("Inventory").addItemToInventory(interaction.user.id, 1, 'Fish')

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Bank")
		embed.set_footer(text="You found a fish! ")

		await interaction.send(embed=embed)
		

def setup(bot):
	bot.add_cog(Fish(bot))