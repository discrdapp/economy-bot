import nextcord
from nextcord.ext import commands 
from nextcord import Interaction
from nextcord import FFmpegPCMAudio 
from nextcord import Member 
from nextcord.ext.commands import has_permissions, MissingPermissions

from random import randint

from db import DB

class Shop(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.coin = "<:coins:585233801320333313>"
		self.items = {
			1: {"Price": 1000, "Name": "1 Crate"},
			2: {"Price": 1000, "Name": "1 Key"},
			3: {"Price": 75000, "Name": f"+1,000{self.coin} to daily reward"},
			7: {"Price": 75000, "Name": f"+1,500{self.coin} to donator reward"}
		}


	@nextcord.slash_command()
	async def shop(self, interaction:Interaction):
		pass

	@shop.subcommand()
	async def list(self, interaction:Interaction):
		if not await self.bot.get_cog("Economy").accCheck(interaction.user):
			await self.bot.get_cog("Economy").StartPlaying(interaction, interaction.user)

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Shop")

		for item in self.items:
			embed.add_field(name=f"{self.items[item]['Name']}", value=f"ID {item} ─ {self.items[item]['Price']} {self.coin}", inline=False)

		
		# await interaction.send("```ML\nID            ITEMS                COST\n"
		# 					+ "----------------------------------------\n"
		# 					+ "1            1 crate               1,000\n"
		# 					+ "2             1 key                5,000\n"
		# 					+ "3      +1,000 to daily reward     75,000\n\n"
		# 					+ "7     +1,500 to donator reward    40,000\n"
		# 					+ "----------------------------------------\n"
		# 					+ "Use /shop buy <id> <amount>\n\n\tSHOP IS A WORK IN PROGRESS!```")

		await interaction.send(embed=embed)
		

	# @nextcord.slash_command(name='buy')
	# async def _buy(self, interaction:Interaction, theid: int, amnt: int=1):
	# 	print("in buy..")
	# 	print(f"got: {theid} {amnt}")
	# 	await self.buy(interaction, theid, amnt)

	@shop.subcommand()
	async def buy(self, interaction:Interaction, theid: int, amnt: int=1):
		if not await self.bot.get_cog("Economy").accCheck(interaction.user):
			await self.bot.get_cog("Economy").StartPlaying(interaction, interaction.user) 

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Shop")
		embed.set_thumbnail(url=interaction.user.avatar)
		embed.set_footer(text=interaction.user)

		if amnt <= 0:
			embed.description = "Amount must be greater than 0"
			await interaction.send(embed=embed)
			return


		if theid not in self.items.keys():
			embed.description = "Invalid item ID."
			await interaction.send(embed=embed)
			return
		if theid == 7 and not self.bot.get_cog("Economy").isDonator(interaction.user.id):
			embed.description = f"That can only be used by Donators!"
			await interaction.send(embed=embed)
			return

		discordId = interaction.user.id
		cost = self.items[theid]["Price"] * amnt
		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		
		if balance < cost:
			embed.description = f"That will cost you {cost}{self.coin}, but you only have {balance}{self.coin}"
			await interaction.send(embed=embed)
			return

		if theid == 3:
			dailyReward = await self.bot.get_cog("Daily").getDailyReward(interaction)
			if dailyReward >= 250000:
				embed.description = f"Sorry, but the max Daily Reward allowed is 250,000{self.coin}."
				await interaction.send(embed=embed)
				return
		await self.bot.get_cog("Economy").addWinnings(discordId, -(cost))
		
		if theid == 1:
			DB.update("UPDATE Inventory SET Crates = Crates + ? WHERE DiscordID = ?;", [amnt, discordId])
			# economy.balance(interaction)
			embed.description = f"Successfully bought {amnt} Crates"
			await interaction.send(embed=embed)
			await self.bot.get_cog("Economy").balance(interaction)


		elif theid == 2:
			DB.update("UPDATE Inventory SET Keyss = Keyss + ? WHERE DiscordID = ?;", [amnt, discordId])
			embed.description = f"Successfully bought {amnt} Keys"
			await interaction.send(embed=embed)
			await self.bot.get_cog("Economy").balance(interaction)

		elif theid == 3:
			DB.update("UPDATE Economy SET DailyReward = DailyReward + ? WHERE DiscordID = ?;", [amnt*1000, discordId])
			embed.description = f"Successfully added {amnt * 1000}{self.coin} to daily reward"
			await interaction.send(embed=embed)

		elif theid == 7:
			DB.update("UPDATE Economy SET DonatorReward = DonatorReward + ? WHERE DiscordID = ?;", [amnt*1500, discordId])
			embed.description = f"Successfully added {amnt * 1000}{self.coin} to donator reward"
			await interaction.send(embed=embed)


	# @shop.subcommand()
	# async def sell(self, interaction:Interaction, theid: int, amnt: int=1):
	# 	await interaction.send("WORK IN PROGRESS!")

	@nextcord.slash_command()
	async def crate(self, interaction:Interaction):
		pass


	@crate.subcommand()
	async def open(self, interaction:Interaction, amnt):
		if amnt.isdigit():
			amnt = int(amnt)
		else:
			raise commands.BadArgument(f'You entered {amnt} for the amount you want to open. Please enter a number instead.')
			return
		if amnt > 125:
			await interaction.send("Max crates you can open is 125.")
			return
		if not await self.bot.get_cog("Economy").accCheck(interaction.user):
			await self.bot.get_cog("Economy").StartPlaying(interaction, interaction.user)

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Shop")
		embed.set_thumbnail(url=interaction.user.avatar)

		crates, keys = await self.bot.get_cog("Economy").getInventory(interaction.user)
		if crates < amnt:
			embed.add_field(name="Invalid Amount", value=f"{interaction.user.mention}, you only have {crates} crates. You cannot open {amnt} crate(s).")
			embed.set_footer(text="Buy more crates from the shop!")
			await interaction.send(embed=embed)
			return
		elif keys < amnt:
			embed.add_field(name="Invalid Amount", value=f"{interaction.user.mention}, you only have {keys} keys. You cannot use {amnt} key(s).")
			embed.set_footer(text="Buy more keys from the shop!")
			await interaction.send(embed=embed)
			return
		elif amnt <= 0:
			embed.add_field(name="Invalid Amount", value=f"{interaction.user.mention}, you cannot open a negative amount of crates.")
			await interaction.send(embed=embed)
			return

		await self.bot.get_cog("Economy").subtractInv(interaction.user.id, amnt)
		
		crates = crates - amnt
		keys = keys - amnt
		moneyToAdd = 0

		# 30% chance to get crates
		# 30% chance to get keys
		# 20% chance to get 5000 - 12500 credits
		# 20% chance to get 0 - 500 credits
		for x in range(1, amnt+1):
			choice = randint(1, 10)
			if choice <= 3:
				amntToAdd = randint(0, 3)
				embed.add_field(name="Crate opened...", value=f"You found {amntToAdd} crates!")
				crates += amntToAdd

			elif choice <= 6:
				amntToAdd = randint(1, 3)
				embed.add_field(name="Crate opened...", value=f"You found {amntToAdd} keys!")
				keys += amntToAdd

			elif choice <= 8:
				bal = randint(5000, 12500)
				embed.add_field(name="Crate opened...", value=f"You found {bal}{self.coin}!")
				moneyToAdd += bal
				
			elif choice <= 10:
				bal = randint(0, 500)
				embed.add_field(name="Crate opened...", value=f"You found {bal}{self.coin}!")
				moneyToAdd += bal

			if x >= 25 and x % 25 == 0: # send message every 25 crates opened
				await interaction.send(embed=embed)
				embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Shop")
				embed.set_thumbnail(url=interaction.user.avatar)

		if not x % 25 == 0: # send message for remaining crates that were opened, if not sent already
			await interaction.send(embed=embed)

		await self.bot.get_cog("Economy").addWinnings(interaction.user.id, moneyToAdd)

		DB.update("UPDATE Inventory SET Crates = ?, Keyss = ? WHERE DiscordID = ?;", [crates, keys, interaction.user.id])
		await self.bot.get_cog("Economy").balance(interaction)



def setup(bot):
	bot.add_cog(Shop(bot))