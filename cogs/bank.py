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
	async def deposit(self, ctx):
		await ctx.invoke(self.bot.get_command('help bank'))

	@commands.command(aliases=['w'])
	async def withdraw(self, ctx):
		await ctx.invoke(self.bot.get_command('help bank'))

	@commands.group(invoke_without_command=True)
	async def bank(self, ctx):
		if ctx.invoked_subcommand is None:
			# await ctx.send("`bank <deposit/withdraw> amount`")
			await ctx.invoke(self.bot.get_command('help bank'))

	@bank.command(name='deposit', aliases=['dep', 'd'])
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def _deposit(self, ctx, amnt):
		try:
			amnt = int(amnt)
		except:
			if amnt == "all" or amnt == "max":
				amnt = await self.bot.get_cog("Economy").getBalance(ctx.author)
			elif amnt == "half":
				amnt = floor(await self.bot.get_cog("Economy").getBalance(ctx.author)/2)
			else:
				await ctx.send("Incorrect withdrawal amount.")
				return

		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))

		if not await self.bot.get_cog("Economy").subtractBet(ctx.author, amnt):
			embed = discord.Embed(color=1768431, title=f"{self.bot.user.name} | Bank")
			embed.set_thumbnail(url=ctx.author.avatar_url)
			embed.add_field(name="ERROR", value="You do not have enough to do that.")

			embed.set_footer(text=ctx.author)

			await ctx.send(embed=embed)
			return

		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()
		sql = f"""UPDATE Economy
				  SET Bank = Bank + {amnt}
				  WHERE DiscordID = '{ctx.author.id}';"""
		cursor.execute(sql)
		db.commit()
		db.close()

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

		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()
		sql = f"""UPDATE Economy
				  SET Bank = Bank - {amnt}
				  WHERE DiscordID = '{ctx.author.id}';"""
		cursor.execute(sql)
		db.commit()
		db.close()

		await self.bot.get_cog("Economy").addWinnings(ctx.author.id, amnt)

		await ctx.send(f"Successfully withdrew {amnt}{self.coin}!")


	@bank.command(aliases=['status', 'stat', 'stats'])
	async def balance(self, ctx):
		await ctx.send(f"You have {self.getBankBal(ctx.author.id)}{self.coin} in your bank.")

	def getBankBal(self, discordID):
		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()
		sql = f"""SELECT Bank
				  FROM Economy
				  WHERE DiscordID = '{discordID}'
				  LIMIT 1;"""
		cursor.execute(sql)
		getRow = cursor.fetchone()
		bal = getRow[0]
		db.close()

		return bal


def setup(bot):
	bot.add_cog(Bank(bot))