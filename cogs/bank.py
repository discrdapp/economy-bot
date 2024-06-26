import nextcord
from nextcord.ext import commands, tasks
from nextcord import Interaction

from datetime import time
from math import floor

import cooldowns

import emojis
from cogs.totals import log
from db import DB

class Bank(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot

	@commands.Cog.listener()
	async def on_ready(self):
		if not self.bankInterest.is_running():
			self.bankInterest.start()

	def cog_unload(self):
		if self.bankInterest.is_running():
			self.bankInterest.cancel()

	# 5 hours ahead
	# midnight is 5:00 AM
	# noon is 5:00 PM
	@tasks.loop(time=[time.fromisoformat('00:00:00'), time.fromisoformat('12:00:00')])
	async def bankInterest(self):
		print("TESTING! INTEREST ADDED!!!!")
		DB.update("UPDATE Economy SET Bank = round(Bank * 1.05) WHERE Bank > ? AND BANK < ?;", [10000, 2000000])
		DB.update("UPDATE Economy SET Bank = Bank + 100000 WHERE Bank > ?;", [2000000])

	cooldowns.define_shared_cooldown(1, 7, cooldowns.SlashBucket.author, cooldown_id="bank")


	@nextcord.slash_command()
	async def deposit(self, interaction:Interaction, amnt):
		await self._deposit(interaction, amnt)

	@nextcord.slash_command()
	async def withdraw(self, interaction:Interaction, amnt):
		await self._withdraw(interaction, amnt)

	@nextcord.slash_command(description="Deposit/withdraw your funds to limit yourself")
	# @cooldowns.shared_cooldown("bank")
	async def bank(self, interaction:Interaction):
		pass

	@bank.subcommand(name='deposit')
	@cooldowns.shared_cooldown("bank")
	async def _deposit(self, interaction:Interaction, amnt):
		await interaction.response.defer(with_message=True)
		deferMsg = await interaction.original_message()

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Bank")
		embed.set_thumbnail(url=interaction.user.avatar)

		amnt = await self.bot.get_cog("Economy").GetBetAmount(interaction, amnt)

		# remove credits from Credits
		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, amnt):
			raise Exception("tooPoor")

		# add credits to Bank
		DB.update("UPDATE Economy SET Bank = Bank + ? WHERE DiscordID = ?;", [amnt, interaction.user.id])
		balance = DB.fetchOne("SELECT Credits FROM Economy WHERE DiscordID = ?;", [interaction.user.id])[0]
		logID = log(interaction.user.id, amnt, 0, "Deposit", balance)

		embed.description = f"Successfully deposited {amnt:,}{emojis.coin}!"
		embed.set_footer(text=f"Log ID: {logID}")
		await deferMsg.edit(embed=embed)

	@bank.subcommand(name='withdraw')
	@cooldowns.shared_cooldown("bank")
	async def _withdraw(self, interaction:Interaction, amnt):
		await interaction.response.defer(with_message=True)
		deferMsg = await interaction.original_message()

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Bank")
		embed.set_thumbnail(url=interaction.user.avatar)
		try:
			amnt = int(amnt)
			if self.getBankBal(interaction.user.id) < amnt:
				embed.description = "You do not have enough funds in your bank to withdraw that amount."
				await deferMsg.edit(embed=embed)
				return
		except:
			if amnt == "all" or amnt == "100%":
				amnt = self.getBankBal(interaction.user.id)
			elif amnt == "half" or amnt == "50%":
				amnt = floor(self.getBankBal(interaction.user.id) / 2)
			else:
				embed.description = "Incorrect withdrawal amount."
				await deferMsg.edit(embed=embed)
				return
		if amnt <= 0:
			embed.description = "You must withdraw an amount greater than 0."
			await deferMsg.edit(embed=embed)
			return

		DB.update("UPDATE Economy SET Bank = Bank - ? WHERE DiscordID = ?;", [amnt, interaction.user.id])

		logID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, amnt, giveMultiplier=False, activityName="Withdraw", amntBet=0)

		embed.description = f"Successfully withdrew {amnt:,}{emojis.coin}!"
		embed.set_footer(text=f"Log ID: {logID}")
		await deferMsg.edit(embed=embed)


	@bank.subcommand(name='balance')
	@cooldowns.shared_cooldown("bank")
	async def balance(self, interaction:Interaction, user:nextcord.Member=None):
		await interaction.response.defer(with_message=True)
		deferMsg = await interaction.original_message()

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Bank")
		if user:
			embed.set_thumbnail(url=user.avatar)
			embed.set_footer(text=user)
			if not await self.bot.get_cog("Economy").accCheck(user):
				embed.description=f"{user.name} has not registered yet."
			else:
				embed.description=f"{user.name} has {self.getBankBal(user.id):,}{emojis.coin} in their bank."
		else:
			embed.set_thumbnail(url=interaction.user.avatar)
			embed.set_footer(text=interaction.user)
			
			bankBal = self.getBankBal(interaction.user.id)
			embed.description=f"You have {bankBal:,}{emojis.coin} in your bank."

			if bankBal < 10000:
				embed.set_footer(text=f"You must deposit at least {(10000-bankBal):,} more credits in order to get interest")
			else:
				embed.set_footer(text=f"5% interest is earned every 12 hours!")

		await deferMsg.edit(embed=embed)

	def getBankBal(self, discordID):
		bal = DB.fetchOne("SELECT Bank FROM Economy WHERE DiscordID = ? LIMIT 1;", [discordID])[0]
		return bal


def setup(bot):
	bot.add_cog(Bank(bot))