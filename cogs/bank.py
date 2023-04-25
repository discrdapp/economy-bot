import nextcord
from nextcord.ext import commands, tasks
from nextcord import Interaction

from datetime import time
from math import floor

from db import DB

class Bank(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.coin = "<:coins:585233801320333313>"

	@commands.Cog.listener()
	async def on_ready(self):
		print("Interest has started up.")
		self.bankInterest.start()

	# 5 hours ahead
	# midnight is 5:00 AM
	# noon is 5:00 PM
	@tasks.loop(time=[time.fromisoformat('00:00:00'), time.fromisoformat('12:00:00')])
	async def bankInterest(self):
		print("TESTING! INTEREST ADDED!!!!")
		DB.update("UPDATE Economy SET Bank = round(Bank * 1.05) WHERE Bank > ? AND BANK < ?;", [10000, 2000000])
		DB.update("UPDATE Economy SET Bank = Bank + 100000 WHERE Bank > ?;", [2000000])


	@nextcord.slash_command()
	async def deposit(self, interaction:Interaction, amnt):
		await self._deposit(interaction, amnt)

	@nextcord.slash_command()
	async def withdraw(self, interaction:Interaction, amnt):
		await self._withdraw(interaction, amnt)

	@nextcord.slash_command()
	async def bank(self, interaction:Interaction):
		pass

	@bank.subcommand(name='deposit')
	async def _deposit(self, interaction:Interaction, amnt):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Bank")
		embed.set_thumbnail(url=interaction.user.avatar)

		amnt = await self.bot.get_cog("Economy").GetBetAmount(interaction, amnt)

		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, amnt):
			embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Bank")
			embed.set_thumbnail(url=interaction.user.avatar)
			embed.description = "You do not have enough to do that."
			await interaction.send(embed=embed)
			return

		DB.update("UPDATE Economy SET Bank = Bank + ? WHERE DiscordID = ?;", [amnt, interaction.user.id])

		embed.description = f"Successfully deposited {amnt:,}{self.coin}!"
		await interaction.send(embed=embed)


	@bank.subcommand(name='withdraw')
	async def _withdraw(self, interaction:Interaction, amnt):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Bank")
		embed.set_thumbnail(url=interaction.user.avatar)
		try:
			amnt = int(amnt)
			if self.getBankBal(interaction.user.id) < amnt:
				embed.description = "You do not have enough funds in your bank to withdraw that amount."
				await interaction.send(embed=embed)
				return
		except:
			if amnt == "all" or amnt == "100%":
				amnt = self.getBankBal(interaction.user.id)
			elif amnt == "half" or amnt == "50%":
				amnt = floor(self.getBankBal(interaction.user.id) / 2)
			else:
				embed.description = "Incorrect withdrawal amount."
				await interaction.send(embed=embed)
				return
		if amnt <= 0:
			embed.description = "You must withdraw an amount greater than 0."
			await interaction.send(embed=embed)
			return

		DB.update("UPDATE Economy SET Bank = Bank - ? WHERE DiscordID = ?;", [amnt, interaction.user.id])

		await self.bot.get_cog("Economy").addWinnings(interaction.user.id, amnt)


		embed.description = f"Successfully withdrew {amnt:,}{self.coin}!"
		await interaction.send(embed=embed)


	@bank.subcommand(name='balance')
	async def balance(self, interaction:Interaction, user:nextcord.Member=None):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Bank")
		if user:
			embed.set_thumbnail(url=user.avatar)
			embed.set_footer(text=user)
			if not await self.bot.get_cog("Economy").accCheck(user):
				embed.description=f"{user.name} has not registered yet."
			else:
				embed.description=f"{user.name} has {self.getBankBal(user.id):,}{self.coin} in their bank."
		else:
			embed.set_thumbnail(url=interaction.user.avatar)
			embed.set_footer(text=interaction.user)
			
			bankBal = self.getBankBal(interaction.user.id)
			embed.description=f"You have {bankBal:,}{self.coin} in your bank."

			if bankBal < 10000:
				embed.set_footer(text=f"You must deposit at least {(10000-bankBal):,} more credits in order to get interest")
			else:
				embed.set_footer(text=f"5% interest is earned every 12 hours!")

		await interaction.send(embed=embed)

	def getBankBal(self, discordID):
		bal = DB.fetchOne("SELECT Bank FROM Economy WHERE DiscordID = ? LIMIT 1;", [discordID])[0]
		return bal


def setup(bot):
	bot.add_cog(Bank(bot))