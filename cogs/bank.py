import discord
from discord.ext import commands
import pymysql
import asyncio
import config

class Bank(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.items = [1000, 5000, 25000, 100000, 150000, 250000, 20000]
		self.coin = "<:coins:585233801320333313>"

	@commands.group(invoke_without_command=True)
	async def bank(self, ctx):
		if ctx.invoked_subcommand is None:
			# await ctx.send("`bank <deposit/withdraw> amount`")
			await ctx.invoke(self.bot.get_command('help bank'))

	@bank.command()
	async def deposit(self, ctx, amnt:int):
		if not await self.bot.get_cog("Economy").subtractBet(ctx.author, amnt):
			await ctx.send("You either don't have enough or you haven't made an account with `.start`")
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


	@bank.command()
	async def withdraw(self, ctx, amnt):
		if amnt < 0:
			await ctx.send("You cannot withdraw a negative amount.")
			return
		if self.getBankBal(ctx.author.id) < amnt:
			await ctx.send("You do not have enough funds in your bank to withdraw that amount.")
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


	@bank.command(aliases=['status'])
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