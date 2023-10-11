import nextcord
from nextcord.ext import commands, menus
from nextcord import Interaction

from random import randint
import cooldowns

import emojis
from db import DB, allItems, buyableItems, buyableItemNamesList, sellableItems, sellableItemNamesList
from cogs.totals import log



################
## ITEM TYPES ##
################
#	Collectible
#	Usable
#	Upgrade
#	Tool


class ShopPages(menus.ListPageSource):
	def __init__(self, data):
		super().__init__(data, per_page=5)

	async def format_page(self, menu, entries):
		embed = nextcord.Embed(color=1768431, title=f"The Casino | Shop")

		for x in range(0, len(entries)):
			embed.add_field(name=f"{entries[x][1]} {entries[x][8]} ─ {entries[x][4]:,}{emojis.coin}", value=f"{entries[x][2]}", inline=False)
		
		embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
		return embed

class ItemList(menus.ListPageSource):
	def __init__(self, data):
		super().__init__(data, per_page=5)
		

	async def format_page(self, menu, entries):
		embed = nextcord.Embed(color=1768431, title=f"The Casino | Item List")

		for x in range(0, len(entries)):
			if entries[x][7] == 0: rarity = "Uncommon"
			elif entries[x][7] == 1: rarity = "Common"
			elif entries[x][7] == 2: rarity = "Unique"
			elif entries[x][7] == 3: rarity = "Rare"
			elif entries[x][7] == 4: rarity = "Mythic"
			elif entries[x][7] == 5: rarity = "Exotic"
			elif entries[x][7] == 6: rarity = "Legendary"
			elif entries[x][7] == 7: rarity = "Artifact"
			else: rarity = "Error. Please report this to PyCord for a reward."
			if entries[x][6] > 0:
				name = f"{entries[x][1]} {entries[x][8]} ─ B {entries[x][4]:,}{emojis.coin} | S {entries[x][6]:,}{emojis.coin}"
			else:
				name = f"{entries[x][1]} {entries[x][8]} ─ {entries[x][4]:,}{emojis.coin}"
			embed.add_field(name=name, value=f"{rarity}\n{entries[x][2]}", inline=False)
		
		embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
		return embed

class Shop(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot

		self.itemsDict = dict()
		for item in buyableItems:
			self.itemsDict[item[0]] = {
				"Name": item[1],
				"Description": item[2],
				"Type": item[3],
				"Price": item[4]
			}
	
	def GetItem(self, itemList, itemName):
		for x in itemList:
			if itemName == x[1]:
				return x
		
		return None

	@nextcord.slash_command()
	async def shop(self, interaction:Interaction):
		pass

	@shop.subcommand()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='list')
	async def list(self, interaction:Interaction):
		pages = menus.ButtonMenuPages(
			source=ShopPages(buyableItems),
			clear_buttons_after=True,
			style=nextcord.ButtonStyle.primary,
		)
		await pages.start(interaction=interaction, ephemeral=True)
	
	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='items')
	async def items(self, interaction:Interaction):
		pages = menus.ButtonMenuPages(
			source=ItemList(allItems),
			clear_buttons_after=True,
			style=nextcord.ButtonStyle.primary,
		)
		await pages.start(interaction=interaction, ephemeral=True)

	@shop.subcommand()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='buy')
	async def buy(self, interaction:Interaction, 
						itemSelected = nextcord.SlashOption(
										required=True,
										name="item", 
										choices=buyableItemNamesList), 
						amnt:int=1):
		await interaction.response.defer(with_message=True, ephemeral=True)
		deferMsg = await interaction.original_message()
		
		for item in buyableItems:
			if item[1] == itemSelected:
				theid = item[0]
				break

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Shop")

		# troll-proof
		if amnt <= 0:
			embed.description = "Amount must be greater than 0"
			await deferMsg.edit(embed=embed)
			return
		if amnt > 25:
			embed.description = "Can only buy MAX 25 items at a time"
			await deferMsg.edit(embed=embed)
			return
		# not valid item
		if theid not in self.itemsDict.keys():
			embed.description = "Invalid item ID."
			await deferMsg.edit(embed=embed)
			return

		discordId = interaction.user.id
		cost = self.itemsDict[theid]['Price'] * amnt
		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)

		# troll-proof		
		if balance < cost:
			embed.description = f"That will cost you {cost:,}{emojis.coin}, but you only have {balance:,}{emojis.coin}"
			await deferMsg.edit(embed=embed)
			return
		
		if theid == 60:
			tableCount = self.bot.get_cog("Inventory").getCountForItem(interaction.user, 'Table')
			if amnt + tableCount > 10:
				embed.description = f"You can only own 10 tables.\nYou are trying to buy {amnt}, but you already own {tableCount}"
				await deferMsg.edit(embed=embed)
				return


		logID = await self.bot.get_cog("Economy").addWinnings(discordId, -cost, giveMultiplier=False, activityName=f"Bought {amnt} {itemSelected}")		
		
		rowName = self.itemsDict[theid]["Name"]
		
		self.bot.get_cog("Inventory").addItemToInventory(discordId, amnt, rowName)

		embed.description = f"Successfully bought {amnt} {self.itemsDict[theid]['Name']}"

		if self.itemsDict[theid]["Type"] == "Usable":
			embed.set_footer(text=f"Use this item with /use {itemSelected}\nLog ID: {logID}")
		else:
			embed.set_footer(text=f"Log ID: {logID}")

		await deferMsg.edit(embed=embed)

	@shop.subcommand()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='sell')
	async def sell(self, interaction:Interaction, 
						itemSelected = nextcord.SlashOption(
										required=True,
										name="item", 
										choices=sellableItemNamesList), 
						amnt:int=1):
		
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Shop")
		
		# troll-proof
		if amnt <= 0:
			embed.description = "Amount must be greater than 0"
			await interaction.send(embed=embed, ephemeral=True)
			return
		if not self.bot.get_cog("Inventory").checkInventoryFor(interaction.user, itemSelected, amnt):
			embed.description = f"You do not have that {amnt} {itemSelected} in your inventory!"
			await interaction.send(embed=embed, ephemeral=True)
			return
		
		item = self.GetItem(sellableItems, itemSelected)
		
		self.bot.get_cog("Inventory").removeItemFromInventory(interaction.user, itemSelected, amnt)
		logID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, item[6]*amnt, giveMultiplier=False, activityName=f"Sold {amnt} {itemSelected}", amntBet=0)

		embed.description = f"Successfully sold {amnt} {itemSelected} for {item[6]*amnt}{emojis.coin}"
		embed.set_footer(text=f"Log ID: {logID}")

		await interaction.send(embed=embed)
		
		


	# @crate.subcommand()
	async def useCrate(self, interaction:Interaction, amnt: int):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Crates")
		embed.set_thumbnail(url=interaction.user.avatar)

		if amnt > 25:
			embed.description = "Max crates you can open is 25."
			await interaction.send(embed=embed, ephemeral=True)
			return

		if amnt <= 0:
			embed.description = f"Invalid Amount. {interaction.user.mention}, you cannot open a negative amount of crates."
			await interaction.send(embed=embed, ephemeral=True)
			return

		crates, keys = self.bot.get_cog("Inventory").getInventory(interaction.user)
		if crates < amnt:
			embed.description = f"Invalid Amount. {interaction.user.mention}, you only have {crates} crates. You cannot open {amnt} crate(s)."
			embed.set_footer(text="Buy more crates from the shop!")
			await interaction.send(embed=embed, ephemeral=True)
			return
		elif keys < amnt:
			embed.description = f"Invalid Amount. {interaction.user.mention}, you only have {keys} keys. You cannot use {amnt} key(s)."
			embed.set_footer(text="Buy more keys from the shop!")
			await interaction.send(embed=embed, ephemeral=True)
			return

		self.bot.get_cog("Inventory").subtractInv(interaction.user.id, amnt)

		crates = 0
		keys = 0
		moneyToAdd = 0

		# open amnt number of crates
		embed.description = ""
		for x in range(1, amnt+1):
			# 30% chance to get crates
			# 30% chance to get keys
			# 20% chance to get 5000 - 12500 credits
			# 20% chance to get 0 - 500 credits
			choice = randint(0, 100)
			if choice <= 40: # 50% chance to find random item.
				itemName, itemRarity, itemEmoji = self.bot.get_cog("Inventory").getRandomItem(3)
				self.bot.get_cog("Inventory").addItemToInventory(interaction.user.id, 1, itemName)
				aan = "an" if itemRarity[0].lower() in "aeiou" else "a"
				embed.description += f"You found {aan} ({itemRarity}) {itemName} {itemEmoji}\n"
			elif choice <= 50:
				amntToAdd = randint(0, 3)
				embed.description += f"You found {amntToAdd} crates!\n"
				crates += amntToAdd

			elif choice <= 60:
				amntToAdd = randint(1, 3)
				embed.description += f"You found {amntToAdd} keys!\n"
				keys += amntToAdd

			elif choice <= 70:
				bal = randint(2500, 12000)
				embed.description += f"You found {bal}{emojis.coin}!\n"
				moneyToAdd += bal

			elif choice <= 80:
				bal = randint(50, 250)
				embed.description += f"You found {bal}{emojis.coin}!\n"
				moneyToAdd += bal
			else:
				embed.description += "The crate was empty... Better luck next time!\n"

			if x >= 25 and x % 25 == 0: # send message every 25 crates opened
				await interaction.send(embed=embed)
				embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Shop")
				embed.set_thumbnail(url=interaction.user.avatar)

		logID = None
		if moneyToAdd > 0:
			logID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, moneyToAdd, giveMultiplier=False, activityName="Crate", amntBet=0)
		if not x % 25 == 0: # send message for remaining crates that were opened, if not sent already
			if logID:
				embed.set_footer(text=f"Log ID: {logID}")
			await interaction.send(embed=embed)

		if crates > 0:
			self.bot.get_cog("Inventory").addItemToInventory(interaction.user.id, crates, 'Crate')
		if keys > 0:
			self.bot.get_cog("Inventory").addItemToInventory(interaction.user.id, keys, 'Key')
		
		await self.bot.get_cog("Economy").balance(interaction)



def setup(bot):
	bot.add_cog(Shop(bot))