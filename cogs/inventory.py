import nextcord
from nextcord.ext import commands, menus
from nextcord import Interaction
from nextcord.ui import View, Select

from cooldowns import cooldown, SlashBucket

from db import DB

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

			if "Usable" in values:
				newSource = self.getAllInventory(interaction.user, 'Usable')
			elif "Collectible" in values:
				newSource = self.getAllInventory(interaction.user, 'Usable')	
			else:
				newSource = self.getAllInventory(interaction.user)

			await pages.change_source(MySource(newSource))

		a = Select(options=[nextcord.SelectOption(label="Usable"), nextcord.SelectOption(label="Collectible")])
		a.callback = callback
		pages.add_item(a)




		test = await pages.start(interaction=interaction, ephemeral=True)
	
	def getAllInventory(self, user: nextcord.user, itemType:str=None):
		if itemType:
			return DB.fetchAll("SELECT Item, Quantity, Type, Description \
		     				FROM Inventory LEFT JOIN Items ON Inventory.Item = Items.Name \
		     				WHERE DiscordID = ? and Type = ?;", [user.id, itemType])
		else:
			return DB.fetchAll("SELECT Item, Quantity, Type, Description \
		     				FROM Inventory LEFT JOIN Items ON Inventory.Item = Items.Name \
		     				WHERE DiscordID = ?;", [user.id])

	def getInventory(self, user: nextcord.user): # grabs all the crates and keys from database
		crates = DB.fetchOne("SELECT Quantity FROM Inventory WHERE DiscordID = ? AND Item = 'Crate';", [user.id])
		keys = DB.fetchOne("SELECT Quantity FROM Inventory WHERE DiscordID = ? AND Item = 'Key';", [user.id])

		if crates: crates = crates[0]
		else: crates = 0
		if keys: keys = keys[0]
		else: keys = 0

		return crates, keys


	def subtractInv(self, discordid: int, amnt: int): # called when people open crates (subtracts them from inv.)
		DB.update("UPDATE Inventory SET Quantity = Quantity - ? WHERE DiscordID = ? AND Item = 'Crate';", [amnt, discordid])
		DB.update("UPDATE Inventory SET Quantity = Quantity - ? WHERE DiscordID = ? and Item = 'Key';", [amnt, discordid])
	

	def addItemToInventory(self, discordId: int, amnt: int, itemName: str):
		DB.insert('INSERT OR IGNORE INTO Inventory(DiscordID, Item, Quantity) VALUES (?, ?, 0);', [discordId, itemName])
		DB.update('UPDATE Inventory SET Quantity = Quantity + ? WHERE DiscordID = ? AND Item = ?;', [amnt, discordId, itemName])




def setup(bot):
	bot.add_cog(Inventory(bot))