import nextcord
from nextcord.ext import commands
from nextcord import Interaction

from random import randint, choice
import cooldowns

import emojis
from db import DB


class Fish(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot

	@nextcord.slash_command()
	@cooldowns.cooldown(1, 1800, bucket=cooldowns.SlashBucket.author, cooldown_id='fish')
	async def fish(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Fish")
		if not self.bot.get_cog("Inventory").checkInventoryFor(interaction.user, "Fishing Pole"):
			embed.description = "You need a fishing pole to fish.\nYou can buy one from the /shop"
			await interaction.send(embed=embed)
			return
		
		num = randint(0,2)
		# 25% chance to not catch anything
		if num == 0:
			response = choice(["A fish swam away with your lure.",
		      "The fish was too heavy for you to reel in",
			  "You caught a fish and decided to let it go. How nice of you!",
			  "You caught a big one! But someone stole it from you \:\(",
			  "Fishing season is over *buddy*. try again later!"])
			embed.description = response
			await interaction.send(embed=embed)
			return

		elif num == 1: # 50% chance to get a fishing item (37.5% total)
			rarityChosen = self.bot.get_cog("Inventory").getRarity(3)
			# get all fishing items (IDs between 200 & 300)
			items = DB.fetchAll("SELECT * FROM Items WHERE ID >= 200 and ID < 300 AND Rarity = ? ORDER BY Price;", [rarityChosen])
			itemToGive, itemEmoji = self.bot.get_cog("Inventory").getItemFromListBasedOnPrice(items)

			self.bot.get_cog("Inventory").addItemToInventory(interaction.user.id, 1, itemToGive)

			aan = "an" if itemToGive in "aeiou" else "a"
			embed.description = f"You caught {aan} {itemToGive} {itemEmoji}"
			await interaction.send(embed=embed)

		elif num == 2: # 50% chance to get any random item (37.5% total)
			await self.bot.get_cog("Inventory").GiveRandomItem(interaction)

def setup(bot):
	bot.add_cog(Fish(bot))