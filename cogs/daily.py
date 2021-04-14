import discord
from discord.ext import commands
import pymysql
import asyncio
import config

class Daily(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.levelReward = [550, 1500, 3000, 7500, 13500, 18500, 24000, 29000, 35000, 42000, 50000]
		self.coin = "<:coins:585233801320333313>"

	@commands.command()
	@commands.cooldown(1, 86400, commands.BucketType.user)
	async def daily(self, ctx):
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.send("Hello! Please type .start to create your wallet. :smiley:")
			return			
		dailyReward = await self.getDailyReward(ctx)
		multiplier = self.bot.get_cog("Economy").getMultiplier(ctx.author)
		extraMoney = int(dailyReward * (multiplier - 1))
		await self.bot.get_cog("Economy").addWinnings(ctx.author.id, dailyReward + extraMoney)
		balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
		embed = discord.Embed(color=1768431)
		embed.add_field(name = f"You got {dailyReward} (+{extraMoney}) {self.coin}", 
						value = f"You have {balance} credits\nMultiplier: {multiplier}x\nExtra Money: {extraMoney}", inline=False)
		await ctx.send(embed=embed)

	async def getDailyReward(self, ctx):
		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()
		sql = f"""SELECT DailyReward
				  FROM Economy
				  WHERE DiscordID = '{ctx.author.id}';"""
		cursor.execute(sql)
		db.commit()
		getRow = cursor.fetchone()
		db.close()
		dailyReward = getRow[0]
		return dailyReward

def setup(bot):
	bot.add_cog(Daily(bot))