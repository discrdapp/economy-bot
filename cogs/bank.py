import nextcord
from nextcord.ext import commands 
from nextcord import Interaction
from nextcord import FFmpegPCMAudio 
from nextcord import Member 
from nextcord.ext.commands import has_permissions, MissingPermissions

import asyncio

from math import floor

from db import DB

class Bank(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.items = [1000, 5000, 25000, 100000, 150000, 250000, 20000]
		self.coin = "<:coins:585233801320333313>"

	@nextcord.slash_command()
	async def deposit(self, interaction:Interaction, amnt=None):
		if not amnt:
			await interaction.invoke(self.bot.get_command('help bank'))
			return
		await interaction.invoke(self.bot.get_command('bank deposit'), amnt)

	@nextcord.slash_command()
	async def withdraw(self, interaction:Interaction, amnt=None):
		if not amnt:
			await interaction.invoke(self.bot.get_command('help bank'))
			return
		await interaction.invoke(self.bot.get_command('bank withdraw'), amnt)

	@nextcord.slash_command()
	async def bank(self, interaction:Interaction):
		if interaction.invoked_subcommand is None:
			await interaction.invoke(self.bot.get_command('help bank'))

	@bank.subcommand(name='deposit')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _deposit(self, interaction:Interaction, amnt):

		if not await self.bot.get_cog("Economy").accCheck(interaction.user):
			await self.bot.get_cog("Economy").start(interaction, interaction.user)

		amnt = await self.bot.get_cog("Economy").GetBetAmount(interaction, amnt)

		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, amnt):
			embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Bank")
			embed.set_thumbnail(url=interaction.user.avatar)
			embed.add_field(name="ERROR", value="You do not have enough to do that.")

			embed.set_footer(text=interaction.user)

			await interaction.response.send_message(embed=embed)
			return

		DB.update("UPDATE Economy SET Bank = Bank + ? WHERE DiscordID = ?;", [amnt, interaction.user.id])

		await interaction.response.send_message(f"Successfully deposited {amnt}{self.coin}!")


	@bank.subcommand(name='withdraw')
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _withdraw(self, interaction:Interaction, amnt):
		try:
			amnt = int(amnt)
			if self.getBankBal(interaction.user.id) < amnt:
				await interaction.response.send_message("You do not have enough funds in your bank to withdraw that amount.")
				return
		except:
			if amnt == "all":
				amnt = self.getBankBal(interaction.user.id)
			elif amnt == "half":
				amnt = floor(self.getBankBal(interaction.user.id) / 2)
			else:
				await interaction.response.send_message("Incorrect withdrawal amount.")
				return
		if amnt <= 0:
			await interaction.response.send_message("You must withdraw an amount greater than 0.")
			return

		DB.update("UPDATE Economy SET Bank = Bank - ? WHERE DiscordID = ?;", [amnt, interaction.user.id])

		await self.bot.get_cog("Economy").addWinnings(interaction.user.id, amnt)

		await interaction.response.send_message(f"Successfully withdrew {amnt}{self.coin}!")


	@bank.subcommand(name='balance')
	async def balance(self, interaction:Interaction, user:nextcord.Member=None):
		if user:
			if not await self.bot.get_cog("Economy").accCheck(user):
				await interaction.response.send_message(f"{user.name} has not registered yet.")
			await interaction.response.send_message(f"{user.name} has {self.getBankBal(user.id)}{self.coin} in their bank.")
		else:
			if not await self.bot.get_cog("Economy").accCheck(interaction.user):
				await self.bot.get_cog("Economy").start(interaction, interaction.user)
			await interaction.response.send_message(f"You have {self.getBankBal(interaction.user.id)}{self.coin} in your bank.")

	def getBankBal(self, discordID):
		bal = DB.fetchOne("SELECT Bank FROM Economy WHERE DiscordID = ? LIMIT 1;", [discordID])[0]
		return bal


def setup(bot):
	bot.add_cog(Bank(bot))