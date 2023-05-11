import nextcord
from nextcord.ext import commands, menus, application_checks
from nextcord import Interaction
from nextcord.ui import Select

from random import randint
import datetime
from cooldowns import cooldown, SlashBucket

import config
from db import DB, allItemNamesList, usableItemNamesList

class MySource(menus.ListPageSource):
	def __init__(self, data):
		super().__init__(data, per_page=4)

	async def format_page(self, menu, entries):
		offset = menu.current_page * self.per_page

		embed = nextcord.Embed(color=1768431, title=f"The Casino | Inventory")

		for x in range(0, len(entries)):
									# Item, Quantity, Type, Description
			embed.add_field(name=f"{entries[x][0]}  (Amount: {entries[x][1]})", value=entries[x][3], inline=False)

		return embed

class Inventory(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.coin = "<:coins:585233801320333313>"
	
	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def giveitem(self, interaction:Interaction, 
		    user: nextcord.Member,
			itemSelected = nextcord.SlashOption(
								required=True,
								name="item", 
								choices=allItemNamesList),
			amnt: int=1):
		
		self.addItemToInventory(interaction.user.id, amnt, itemSelected)
		
	
	@nextcord.slash_command()
	@cooldown(1, 5, bucket=SlashBucket.author)
	async def inventory(self, interaction:Interaction):
		inventory = self.getAllInventory(interaction.user)
		
		if not inventory:
			embed = nextcord.Embed(color=1768431, title=f"The Casino | Inventory")
			embed.description = "Your inventory is empty."
			await interaction.send(embed=embed)
			return

		pages = menus.ButtonMenuPages(
			source=MySource(inventory),
			clear_buttons_after=True,
			style=nextcord.ButtonStyle.primary,
		)

		async def callback(interaction):
			values = interaction.data['values']

			newSource = []
			if "Usable" in values:
				newSource.extend(self.getAllInventory(interaction.user, 'Usable'))
			if "Collectible" in values:
				newSource.extend(self.getAllInventory(interaction.user, 'Collectible'))
			if "Tool" in values:
				newSource.extend(self.getAllInventory(interaction.user, 'Tool'))
			if "Usable" not in values and "Collectible" not in values and "Tool" not in values:
				newSource.extend(self.getAllInventory(interaction.user))

			await pages.change_source(MySource(newSource))

		options = [
			nextcord.SelectOption(label="All"), 
			nextcord.SelectOption(label="Usable"), 
			nextcord.SelectOption(label="Collectible"),
			nextcord.SelectOption(label="Tool")
		]

		a = Select(options=options, min_values=1, max_values=2)
		a.callback = callback
		pages.add_item(a)

		test = await pages.start(interaction=interaction, ephemeral=True)
	
	@nextcord.slash_command()
	@cooldown(1, 5, bucket=SlashBucket.author)
	async def use(self, interaction:Interaction, 
						itemSelected = nextcord.SlashOption(
								required=True,
								name="item", 
								choices=usableItemNamesList),
						amnt:int=1):

		if amnt < 1:
			raise Exception("valueError")

		if itemSelected == "Crate":
			await self.bot.get_cog("Shop").useCrate(interaction, amnt)
			return

		if not self.bot.get_cog("Inventory").checkInventoryFor(interaction.user, itemSelected, amnt):
			raise Exception("itemNotFoundInInventory")


		if itemSelected == "Voter Chip":
			msg = self.bot.get_cog("Multipliers").addMultiplier(interaction.user, 1.5, datetime.datetime.now() + datetime.timedelta(minutes=150))
			self.bot.get_cog("Inventory").removeItemFromInventory(interaction.user, "Voter Chip", amnt)
			await interaction.send(msg)
		elif itemSelected == "Magic 8 Ball":
			amnt = randint(5000, 50000)
			await self.bot.get_cog("Economy").addWinnings(interaction.user.id, amnt)

	# returns a list of items in the inventory
	def getAllInventory(self, user: nextcord.user, itemType:str=None):
		if itemType:
			return DB.fetchAll("SELECT Item, Quantity, Type, Description \
		     				FROM Inventory LEFT JOIN Items ON Inventory.Item = Items.Name \
		     				WHERE DiscordID = ? and Type = ?;", [user.id, itemType])
		else:
			return DB.fetchAll("SELECT Item, Quantity, Type, Description \
		     				FROM Inventory LEFT JOIN Items ON Inventory.Item = Items.Name \
		     				WHERE DiscordID = ?;", [user.id])

	# returns the amount of crates and keys a user has
	def getInventory(self, user: nextcord.user): # grabs all the crates and keys from database
		crates = DB.fetchOne("SELECT Quantity FROM Inventory WHERE DiscordID = ? AND Item = 'Crate';", [user.id])
		keys = DB.fetchOne("SELECT Quantity FROM Inventory WHERE DiscordID = ? AND Item = 'Key';", [user.id])

		if crates: crates = crates[0]
		else: crates = 0
		if keys: keys = keys[0]
		else: keys = 0

		return crates, keys

	# checks if user has an item in their inventory
	def checkInventoryFor(self, user: nextcord.user, itemName: str, amnt: int=1):
		if amnt < 1:
			raise ValueError("valueError")
		isInInventory = DB.fetchOne("SELECT 1 FROM Inventory WHERE DiscordID = ? AND Item = ? AND Quantity >= ?;", [user.id, itemName, amnt])
		
		if isInInventory: return True
		else: return False

	def removeItemFromInventory(self, user: nextcord.user, itemName: str, amnt: int=1):
		if amnt < 1:
			raise ValueError("valueError")
		DB.update("UPDATE Inventory SET Quantity = Quantity - ? WHERE DiscordID = ? AND Item = ?;", [amnt, user.id, itemName])

	# called when people open crates (subtracts them from inv.)
	def subtractInv(self, discordid: int, amnt: int): # called when people open crates (subtracts them from inv.)
		DB.update("UPDATE Inventory SET Quantity = Quantity - ? WHERE DiscordID = ? AND Item = 'Crate';", [amnt, discordid])
		DB.update("UPDATE Inventory SET Quantity = Quantity - ? WHERE DiscordID = ? and Item = 'Key';", [amnt, discordid])
	

	def addItemToInventory(self, discordId: int, amnt: int, itemName: str):
		# if user doesnt have item being added, add it to their inventory
		DB.insert('INSERT OR IGNORE INTO Inventory(DiscordID, Item, Quantity) VALUES (?, ?, 0);', [discordId, itemName])
		# update quantity of item in inventory
		DB.update('UPDATE Inventory SET Quantity = Quantity + ? WHERE DiscordID = ? AND Item = ?;', [amnt, discordId, itemName])




def setup(bot):
	bot.add_cog(Inventory(bot))