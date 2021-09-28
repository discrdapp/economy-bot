import discord
from discord.ext import commands
import pymysql
import asyncio
import config

import json
import time
import math

class Daily(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.levelReward = [550, 1500, 3000, 7500, 13500, 18500, 24000, 29000, 35000, 42000, 50000]
		self.coin = "<:coins:585233801320333313>"

	@commands.command()
	async def daily(self, ctx):
		userId = ctx.author.id

		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))
		else:
			with open(r"rewards.json", 'r') as f:
				rewards = json.load(f)

			if (str(userId) in rewards) and ('daily' in rewards[f'{userId}']):
				if rewards[f'{userId}']['daily'] > time.time():
					waittime = rewards[f'{userId}']['daily'] - time.time()
					await ctx.send(f"Please wait **{math.floor(waittime/3600)}h {math.floor((waittime/60) % 60)}m** to use this again!")
					return

			elif not str(userId) in rewards:
				rewards[f'{userId}'] = dict()
			rewards[f'{userId}']['daily'] = time.time() + 86400

			with open(r"rewards.json", 'w') as f:
				json.dump(rewards, f, indent=4)


		dailyReward = await self.getDailyReward(ctx)
		multiplier = self.bot.get_cog("Economy").getMultiplier(ctx.author)
		extraMoney = int(dailyReward * (multiplier - 1))
		await self.bot.get_cog("Economy").addWinnings(userId, dailyReward + extraMoney)
		balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
		embed = discord.Embed(color=1768431)
		embed.add_field(name = f"You got {dailyReward} (+{extraMoney}) {self.coin}", 
						value = f"You have {balance} credits\nMultiplier: {multiplier}x\nExtra Money: {extraMoney}", inline=False)
		await ctx.send(embed=embed)



	async def getDailyReward(self, ctx):
		conn = pymysql.connect(config.db)
		sql = f"""SELECT DailyReward
				  FROM Economy
				  WHERE DiscordID = '{ctx.author.id}';"""
		cursor = conn.execute(sql)
		getRow = cursor.fetchone()
		conn.close()
		dailyReward = getRow[0]
		return dailyReward

def setup(bot):
	bot.add_cog(Daily(bot))