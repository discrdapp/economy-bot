import discord
from discord.ext import commands
import pymysql
import asyncio
import config

from math import floor

class Bank(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.items = [1000, 5000, 25000, 100000, 150000, 250000, 20000]
		self.coin = "<:coins:585233801320333313>"

	@commands.command(aliases=['dep', 'd'])
	async def deposit(self, ctx, amnt=None):
		if not amnt:
			await ctx.invoke(self.bot.get_command('help bank'))
			return
		await ctx.invoke(self.bot.get_command('bank deposit'), amnt)

	@commands.command(aliases=['w'])
	async def withdraw(self, ctx, amnt=None):
		if not amnt:
			await ctx.invoke(self.bot.get_command('help bank'))
			return
		await ctx.invoke(self.bot.get_command('bank withdraw'), amnt)

	@commands.group(invoke_without_command=True)
	async def bank(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.invoke(self.bot.get_command('help bank'))

	@bank.command(name='deposit', aliases=['dep', 'd'])
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _deposit(self, ctx, amnt):

		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))

		amnt = await self.bot.get_cog("Economy").GetBetAmount(ctx, amnt)

		if not await self.bot.get_cog("Economy").subtractBet(ctx.author, amnt):
			embed = discord.Embed(color=1768431, title=f"{self.bot.user.name} | Bank")
			embed.set_thumbnail(url=ctx.author.avatar_url)
			embed.add_field(name="ERROR", value="You do not have enough to do that.")

			embed.set_footer(text=ctx.author)

			await ctx.send(embed=embed)
			return

		conn = pymysql.connect(config.db)
		sql = f"""UPDATE Economy
				  SET Bank = Bank + {amnt}
				  WHERE DiscordID = '{ctx.author.id}';"""
		conn.execute(sql)
		conn.commit()
		conn.close()

		await ctx.send(f"Successfully deposited {amnt}{self.coin}!")


	@bank.command(name='withdraw', aliases=['w'])
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _withdraw(self, ctx, amnt):
		try:
			amnt = int(amnt)
			if self.getBankBal(ctx.author.id) < amnt:
				await ctx.send("You do not have enough funds in your bank to withdraw that amount.")
				return
		except:
			if amnt == "all":
				amnt = self.getBankBal(ctx.author.id)
			elif amnt == "half":
				amnt = floor(self.getBankBal(ctx.author.id) / 2)
			else:
				await ctx.send("Incorrect withdrawal amount.")
				return
		if amnt <= 0:
			await ctx.send("You must withdraw an amount greater than 0.")
			return

		conn = pymysql.connect(config.db)
		sql = f"""UPDATE Economy
				  SET Bank = Bank - {amnt}
				  WHERE DiscordID = '{ctx.author.id}';"""
		conn.execute(sql)
		conn.commit()
		conn.close()

		await self.bot.get_cog("Economy").addWinnings(ctx.author.id, amnt)

		await ctx.send(f"Successfully withdrew {amnt}{self.coin}!")


	@bank.command(aliases=['status', 'stat', 'stats', 'bal'])
	async def balance(self, ctx):
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))
		await ctx.send(f"You have {self.getBankBal(ctx.author.id)}{self.coin} in your bank.")

	def getBankBal(self, discordID):
		conn = pymysql.connect(config.db)
		sql = f"""SELECT Bank
				  FROM Economy
				  WHERE DiscordID = '{discordID}'
				  LIMIT 1;"""
		cursor = conn.execute(sql)
		getRow = cursor.fetchone()
		bal = getRow[0]
		conn.close()

		return bal


def setup(bot):
	bot.add_cog(Bank(bot))