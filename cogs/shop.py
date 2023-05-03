import nextcord
from nextcord.ext import commands, menus
from nextcord import Interaction

from random import randint
import cooldowns
import datetime

from db import DB, buyableItems, buyableItemNamesList, usableItemNamesList


################
## ITEM TYPES ##
################
#	Collectible
#	Usable
#	Upgrade
#	Tool


class MySource(menus.ListPageSource):
	def __init__(self, data):
		super().__init__(data, per_page=4)

	async def format_page(self, menu, entries):
		# print(entries)
		offset = menu.current_page * self.per_page

		embed = nextcord.Embed(color=1768431, title=f"The Casino | Shop")

		# print(f"offset is {offset} and len is {len(entries)}")
		for x in range(0, len(entries)):
			# print(f"here with x being {x}")
			embed.add_field(name=f"{entries[x][1]} ─ {entries[x][4]:,}<:coins:585233801320333313>", value=f"{entries[x][2]}", inline=False)
		return embed

class Shop(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.coin = "<:coins:585233801320333313>"
		self.items = buyableItems

		self.itemsDict = dict()
		for item in self.items:
			self.itemsDict[item[0]] = {
				"Name": item[1],
				"Description": item[2],
				"Type": item[3],
				"InventoryRowName": item[1],
				"Price": item[4]
			}
		# self.itemsDict[1]["InventoryRowName"] = "Crates"
		# self.itemsDict[2]["InventoryRowName"] = "Keyss"

	@nextcord.slash_command()
	async def shop(self, interaction:Interaction):
		pass

	@shop.subcommand()
	async def list(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Shop")

		pages = menus.ButtonMenuPages(
			source=MySource(self.items),
			clear_buttons_after=True,
			style=nextcord.ButtonStyle.primary,
		)
		await pages.start(interaction=interaction)

	@shop.subcommand()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author)
	async def buy(self, interaction:Interaction, 
						itemSelected = nextcord.SlashOption(
										required=True,
										name="item", 
										choices=buyableItemNamesList), 
						amnt:int=1):
		for item in self.items:
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
		if theid == 7 and not self.bot.get_cog("Economy").isDonator(interaction.user.id):
			embed.description = f"That can only be used by Donators!"
			await interaction.send(embed=embed)
			return

		discordId = interaction.user.id
		cost = self.itemsDict[theid]['Price'] * amnt
		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)

		# troll-proof		
		if balance < cost:
			embed.description = f"That will cost you {cost}{self.coin}, but you only have {balance}{self.coin}"
			await interaction.send(embed=embed)
			return

		# maxed daily reward
		if theid == 3:
			dailyReward = await self.bot.get_cog("Daily").getDailyReward(interaction)
			if dailyReward >= 200000:
				embed.description = f"Sorry, but the max Daily Reward allowed is 200,000{self.coin}."
				await interaction.send(embed=embed)
				return




		await self.bot.get_cog("Economy").addWinnings(discordId, -(cost))
		
		if theid == 3:
			DB.update("UPDATE Economy SET DailyReward = DailyReward + ? WHERE DiscordID = ?;", [amnt*1000, discordId])
			embed.description = f"Successfully added {amnt * 1000}{self.coin} to daily reward"

		elif theid == 7:
			DB.update("UPDATE Economy SET DonatorReward = DonatorReward + ? WHERE DiscordID = ?;", [amnt*1500, discordId])
			embed.description = f"Successfully added {amnt * 1500}{self.coin} to donator reward"

		else:
			rowName = self.itemsDict[theid]["InventoryRowName"]
			
			self.bot.get_cog("Inventory").addItemToInventory(discordId, amnt, rowName)

			embed.description = f"Successfully bought {amnt} {self.itemsDict[theid]['Name']}"

		if self.itemsDict[theid]["Type"] == "Usable":
			embed.set_footer(text=f"Use this item with /use {itemSelected}")

		await interaction.send(embed=embed)

		if theid == 1 or theid == 2:
			await self.bot.get_cog("Economy").balance(interaction)


	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author)
	async def use(self, interaction:Interaction, 
						itemSelected = nextcord.SlashOption(
								required=True,
								name="item", 
								choices=usableItemNamesList),
						amnt:int=1):

		if itemSelected == "Crate":
			await self.useCrate(interaction, amnt)
		elif itemSelected == "Voter Chip":
			# '%Y-%d-%m %H:%M:%S'
			if not self.bot.get_cog("Inventory").checkInventoryFor(interaction.user, "Voter Chip", amnt):
				await interaction.send("You don't have enough Voter Chips to do that!")
				return

			msg = self.bot.get_cog("Multipliers").addMultiplier(interaction.user, 1.5, datetime.datetime.now() + datetime.timedelta(minutes=90))
			self.bot.get_cog("Inventory").removeFromInventory(interaction.user, "Voter Chip", amnt)
			await interaction.send(msg)
		else:
			print(itemSelected)




	# @nextcord.slash_command()
	# async def crate(self, interaction:Interaction):
	# 	pass


	# @crate.subcommand()
	async def useCrate(self, interaction:Interaction, amnt: int):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Crates")
		embed.set_thumbnail(url=interaction.user.avatar)

		if amnt > 50:
			embed.description = "Max crates you can open is 50."
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
		for x in range(1, amnt+1):
			# 30% chance to get crates
			# 30% chance to get keys
			# 20% chance to get 5000 - 12500 credits
			# 20% chance to get 0 - 500 credits
			choice = randint(1, 10)
			if choice <= 3:
				amntToAdd = randint(0, 3)
				embed.description = f"You found {amntToAdd} crates!"
				crates += amntToAdd

			elif choice <= 6:
				amntToAdd = randint(1, 3)
				embed.description = f"You found {amntToAdd} keys!"
				keys += amntToAdd

			elif choice <= 8:
				bal = randint(5000, 12500)
				embed.description = f"You found {bal}{self.coin}!"
				moneyToAdd += bal

			elif choice <= 10:
				bal = randint(0, 500)
				embed.description = f"You found {bal}{self.coin}!"
				moneyToAdd += bal

			if x >= 25 and x % 25 == 0: # send message every 25 crates opened
				await interaction.send(embed=embed)
				embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Shop")
				embed.set_thumbnail(url=interaction.user.avatar)

		if not x % 25 == 0: # send message for remaining crates that were opened, if not sent already
			await interaction.send(embed=embed)

		await self.bot.get_cog("Economy").addWinnings(interaction.user.id, moneyToAdd)
		if crates > 0:
			self.bot.get_cog("Inventory").addItemToInventory(interaction.user.id, crates, 'Crate')
		if keys > 0:
			self.bot.get_cog("Inventory").addItemToInventory(interaction.user.id, keys, 'Key')
		await self.bot.get_cog("Economy").balance(interaction)



def setup(bot):
	bot.add_cog(Shop(bot))