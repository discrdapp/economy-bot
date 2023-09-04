import nextcord
from nextcord.ext import commands, menus
from nextcord import Interaction

from random import randint
import cooldowns, difflib

import emojis
from db import DB, buyableItems, buyableItemNamesList, sellableItems, sellableItemNamesList, usableItemNamesList
from cogs.totals import log



################
## ITEM TYPES ##
################
#	Collectible
#	Usable
#	Upgrade
#	Tool


class MySource(menus.ListPageSource):
	def __init__(self, data):
		super().__init__(data, per_page=5)

	async def format_page(self, menu, entries):
		offset = menu.current_page * self.per_page

		embed = nextcord.Embed(color=1768431, title=f"The Casino | Shop")

		for x in range(0, len(entries)):
			embed.add_field(name=f"{entries[x][1]} {entries[x][8]} ─ {entries[x][4]:,}<:coins:585233801320333313>", value=f"{entries[x][2]}", inline=False)
		
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
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Shop")

		pages = menus.ButtonMenuPages(
			source=MySource(buyableItems),
			clear_buttons_after=True,
			style=nextcord.ButtonStyle.primary,
		)
		await pages.start(interaction=interaction)

	@shop.subcommand()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='buy')
	async def buy(self, interaction:Interaction, 
						itemSelected = nextcord.SlashOption(
										required=True,
										name="item", 
										choices=buyableItemNamesList), 
						amnt:int=1):
		for item in buyableItems:
			if item[1] == itemSelected:
				theid = item[0]
				break

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Shop")

		# troll-proof
		if amnt <= 0:
			embed.description = "Amount must be greater than 0"
			await interaction.send(embed=embed)
			return
		# not valid item
		if theid not in self.itemsDict.keys():
			embed.description = "Invalid item ID."
			await interaction.send(embed=embed)
			return
		# not donator but trying to buy donator item
		if theid == 999 and not self.bot.get_cog("Economy").isDonator(interaction.user.id):
			embed.description = f"That can only be used by Donators!"
			await interaction.send(embed=embed)
			return

		discordId = interaction.user.id
		cost = self.itemsDict[theid]['Price'] * amnt
		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)

		# troll-proof		
		if balance < cost:
			embed.description = f"That will cost you {cost}{emojis.coin}, but you only have {balance}{emojis.coin}"
			await interaction.send(embed=embed)
			return

		# maxed daily reward
		if theid == 3:
			dailyReward = await self.bot.get_cog("Daily").getDailyReward(interaction)
			if dailyReward >= 200000:
				embed.description = f"Sorry, but the max Daily Reward allowed is 200,000{emojis.coin}."
				await interaction.send(embed=embed)
				return


		logID = await self.bot.get_cog("Economy").addWinnings(discordId, -cost, giveMultiplier=False, activityName=f"Bought {amnt} {itemSelected}")		
		
		if theid == 3:
			DB.update("UPDATE Economy SET DailyReward = DailyReward + ? WHERE DiscordID = ?;", [amnt*1000, discordId])
			embed.description = f"Successfully added {amnt * 1000}{emojis.coin} to daily reward"

		elif theid == 999:
			DB.update("UPDATE Economy SET DonatorReward = DonatorReward + ? WHERE DiscordID = ?;", [amnt*1500, discordId])
			embed.description = f"Successfully added {amnt * 1500}{emojis.coin} to donator reward"

		else:
			rowName = self.itemsDict[theid]["Name"]
			
			self.bot.get_cog("Inventory").addItemToInventory(discordId, amnt, rowName)

			embed.description = f"Successfully bought {amnt} {self.itemsDict[theid]['Name']}"

		if self.itemsDict[theid]["Type"] == "Usable":
			embed.set_footer(text=f"Use this item with /use {itemSelected}\nLog ID: {logID}")
		else:
			embed.set_footer(text=f"Log ID: {logID}")

		await interaction.send(embed=embed)

		if theid == 1 or theid == 2:
			await self.bot.get_cog("Economy").balance(interaction)

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
			await interaction.send(embed=embed)
			return
		if not self.bot.get_cog("Inventory").checkInventoryFor(interaction.user, itemSelected, amnt):
			embed.description = "You do not have that item in your inventory!"
			await interaction.send(embed=embed)
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
			await interaction.send(embed=embed)
			return

		if amnt <= 0:
			embed.description = f"Invalid Amount. {interaction.user.mention}, you cannot open a negative amount of crates."
			await interaction.send(embed=embed)
			return

		crates, keys = self.bot.get_cog("Inventory").getInventory(interaction.user)
		if crates < amnt:
			embed.description = f"Invalid Amount. {interaction.user.mention}, you only have {crates} crates. You cannot open {amnt} crate(s)."
			embed.set_footer(text="Buy more crates from the shop!")
			await interaction.send(embed=embed)
			return
		elif keys < amnt:
			embed.description = f"Invalid Amount. {interaction.user.mention}, you only have {keys} keys. You cannot use {amnt} key(s)."
			embed.set_footer(text="Buy more keys from the shop!")
			await interaction.send(embed=embed)
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
				itemName, emoji = self.bot.get_cog("Inventory").getRandomItem(3)
				self.bot.get_cog("Inventory").addItemToInventory(interaction.user.id, 1, itemName)
				aan = "an" if itemName in "aeiou" else "a"
				embed.description += f"You found {aan} {itemName} {emoji}\n"
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
				embed.description = "The crate was empty... Better luck next time!\n"

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