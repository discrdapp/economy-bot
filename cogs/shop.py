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
		self.items = [1000, 5000, 75000, 100000, 150000, 250000, 40000]
		self.coin = "<:coins:585233801320333313>"


	@nextcord.slash_command()
	async def shop(self, interaction:Interaction):
		if not await self.bot.get_cog("Economy").accCheck(interaction.user):
			await self.bot.get_cog("Economy").start(interaction, interaction.user)
			
		if interaction.invoked_subcommand is None:
			await interaction.response.send_message("```ML\nID            ITEMS                COST\n"
								+ "----------------------------------------\n"
								+ "1            1 crate               1,000\n"
								+ "2             1 key                5,000\n"
								+ "3      +1,000 to daily reward     75,000\n\n"
								+ "7     +1,500 to donator reward    40,000\n"
								+ "----------------------------------------\n"
								+ "Use .shop buy <id> <amount>\n\n\tSHOP IS A WORK IN PROGRESS!```")

	@nextcord.slash_command(name='buy')
	async def _buy(self, interaction:Interaction, theid, amnt: int=1):
		await interaction.invoke(self.bot.get_command('shop buy'), theid, amnt)

	@shop.subcommand()
	async def buy(self, interaction:Interaction, theid, amnt: int=1):
		if not await self.bot.get_cog("Economy").accCheck(interaction.user):
			await self.bot.get_cog("Economy").start(interaction, interaction.user) 
		try:
			theid = int(theid)
		except:
			if theid == "crate" or theid == "crates":
				theid = 1
			elif theid == "key" or theid == "keys":
				theid = 2
			else:
				theid = 100

		if theid != 1 and theid != 2 and theid != 3 and theid != 7:
			await interaction.response.send_message("Invalid item ID.")
			await interaction.invoke(self.bot.get_command('shop'))
			return
		if theid == 7 and not self.bot.get_cog("Economy").isDonator(interaction.user.id):
			embed = nextcord.Embed(color=1768431)
			embed.set_thumbnail(url=interaction.user.avatar)
			embed.add_field(name = f"Shop", 
							value = f"That can only be used by Donators!", inline=False)
			embed.set_footer(text=f"{interaction.user}")
			await interaction.response.send_message(embed=embed)
			return

		discordId = interaction.user.id
		cost = self.items[theid - 1] * amnt
		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		
		if balance < cost:
			embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Shop")
			embed.set_thumbnail(url=interaction.user.avatar)
			embed.add_field(name="Error", value=f"That will cost you {cost}{self.coin}, but you only have {balance}{self.coin}")
			embed.set_footer(text=f"{interaction.user}")
			await interaction.response.send_message(embed=embed)
			return

		if theid == 3:
			dailyReward = await self.bot.get_cog("Daily").getDailyReward(interaction)
			if dailyReward >= 250000:
				await interaction.response.send_message(f"Sorry, but the max Daily Reward allowed is 250,000{self.coin}.")
				return
		await self.bot.get_cog("Economy").addWinnings(discordId, -(cost))
		
		if theid == 1:
			DB.update("UPDATE Inventory SET Crates = Crates + ? WHERE DiscordID = ?;", [amnt, discordId])
			await interaction.invoke(self.bot.get_command('balance'))

		elif theid == 2:
			DB.update("UPDATE Inventory SET Keyss = Keyss + ? WHERE DiscordID = ?;", [amnt, discordId])
			await interaction.invoke(self.bot.get_command('balance'))

		elif theid == 3:

			DB.update("UPDATE Economy SET DailyReward = DailyReward + ? WHERE DiscordID = ?;", [amnt*1000, discordId])

			embed = nextcord.Embed(color=1768431)
			embed.set_thumbnail(url=interaction.user.avatar)
			embed.set_footer(text=f"{interaction.user}")
			embed.add_field(name = f"Shop", 
							value = f"Successfully added {amnt * 1000}{self.coin} to daily reward")
			await interaction.response.send_message(embed=embed)

		elif theid == 7:
			DB.update("UPDATE Economy SET DonatorReward = DonatorReward + ? WHERE DiscordID = ?;", [amnt*1500, discordId])

			embed = nextcord.Embed(color=1768431)
			embed.add_field(name = f"Shop", 
							value = f"Successfully added {amnt * 1000}{self.coin} to donator reward")
			embed.set_thumbnail(url=interaction.user.avatar)
			embed.set_footer(text=f"{interaction.user}")
			await interaction.response.send_message(embed=embed)


	@shop.subcommand()
	async def sell(self, interaction:Interaction, theid: int, amnt: int=1):
		await interaction.response.send_message("WORK IN PROGRESS!")

	@nextcord.slash_command()
	async def crate(self, interaction:Interaction):
		# await interaction.response.send_message(".crate open 1*")
		if interaction.invoked_subcommand is None:
			embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Open a crate to receive a prize!")
			embed.add_field(name="Possible prizes and their chances:", value=f"**(30%)** 0-3 Crates\n**(30%)** 1-3 Keys\n**(20%)** 5000-12500{self.coin}\n**(20%)** 0 - 500{self.coin}\nMore coming soon...")
			embed.set_footer(text=".crate open")
			embed.set_thumbnail(url=interaction.user.avatar)

			await interaction.response.send_message(embed=embed)


	@crate.subcommand()
	async def open(self, interaction:Interaction, amnt=1):
		if amnt > 125:
			await interaction.response.send_message("Max crates you can open is 125.")
			return
		if not await self.bot.get_cog("Economy").accCheck(interaction.user):
			await self.bot.get_cog("Economy").start(interaction, interaction.user)

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Shop")
		embed.set_thumbnail(url=interaction.user.avatar)

		crates, keys = await self.bot.get_cog("Economy").getInventory(interaction.user)
		if crates < amnt:
			embed.add_field(name="Invalid Amount", value=f"{interaction.user.mention}, you only have {crates} crates. You cannot open {amnt} crate(s).")
			embed.set_footer(text="Buy more crates from the shop!")
			await interaction.response.send_message(embed=embed)
			return
		elif keys < amnt:
			embed.add_field(name="Invalid Amount", value=f"{interaction.user.mention}, you only have {keys} keys. You cannot use {amnt} key(s).")
			embed.set_footer(text="Buy more keys from the shop!")
			await interaction.response.send_message(embed=embed)
			return
		elif amnt <= 0:
			embed.add_field(name="Invalid Amount", value=f"{interaction.user.mention}, you cannot open a negative amount of crates.")
			await interaction.response.send_message(embed=embed)
			return

		await self.bot.get_cog("Economy").subtractInv(interaction.user.id, amnt)
		
		crates = crates - amnt
		keys = keys - amnt
		moneyToAdd = 0
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

			if x >= 25 and x % 25 == 0:
				await interaction.response.send_message(embed=embed)
				embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Shop")
				embed.set_thumbnail(url=interaction.user.avatar)

		if not x % 25 == 0:
			await interaction.response.send_message(embed=embed)

		await self.bot.get_cog("Economy").addWinnings(interaction.user.id, moneyToAdd)

		DB.update("UPDATE Inventory SET Crates = ?, Keyss = ? WHERE DiscordID = ?;", [crates, keys, interaction.user.id])
		await interaction.invoke(self.bot.get_command('balance'))



def setup(bot):
	bot.add_cog(Shop(bot))