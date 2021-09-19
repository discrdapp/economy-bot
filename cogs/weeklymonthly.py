import discord
from discord.ext import commands
import pymysql
import asyncio
import config

import json
import time
import math

class WeeklyMonthly(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.levelReward = [550, 1500, 3000, 7500, 13500, 18500, 24000, 29000, 35000, 42000, 50000]
		self.coin = "<:coins:585233801320333313>"

	@commands.command()
	async def weekly(self, ctx):
		userId = ctx.author.id
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))
		else:
			with open(r"rewards.json", 'r') as f:
				rewards = json.load(f)

			if (str(userId) in rewards) and ('weekly' in rewards[f'{userId}']):
				if rewards[f'{userId}']['weekly'] > time.time():
					waittime = rewards[f'{userId}']['weekly'] - time.time()
					await ctx.send(f"Please wait **{math.floor(waittime/86400)}d {math.floor((waittime/3600) % 24)}h {math.floor((waittime/60) % 60)}m** to use this again!")
					return

			elif not str(userId) in rewards:
				rewards[f'{userId}'] = dict()
			rewards[f'{userId}']['weekly'] = time.time() + 604800

			with open(r"rewards.json", 'w') as f:
				json.dump(rewards, f, indent=4)



		weeklyReward = 12500
		multiplier = self.bot.get_cog("Economy").getMultiplier(ctx.author)
		extraMoney = int(weeklyReward * (multiplier - 1))
		await self.bot.get_cog("Economy").addWinnings(userId, weeklyReward + extraMoney)
		balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
		embed = discord.Embed(color=1768431)
		embed.add_field(name = f"You got {weeklyReward} (+{extraMoney}) {self.coin}", 
						value = f"You have {balance} credits\nMultiplier: {multiplier}x\nExtra Money: {extraMoney}", inline=False)
		await ctx.send(embed=embed)



	@commands.command()
	async def monthly(self, ctx):
		userId = ctx.author.id
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))
		else:
			with open(r"rewards.json", 'r') as f:
				rewards = json.load(f)

			if (str(userId) in rewards) and ('monthly' in rewards[f'{userId}']):
				if rewards[f'{userId}']['monthly'] > time.time():
					waittime = rewards[f'{userId}']['monthly'] - time.time()
					await ctx.send(f"Please wait **{math.floor(waittime/86400)}d {math.floor((waittime/3600) % 24)}h {math.floor((waittime/60) % 60)}m** to use this again!")
					return

			elif not str(userId) in rewards:
				rewards[f'{userId}'] = dict()
			rewards[f'{userId}']['monthly'] = time.time() + 2592000

			with open(r"rewards.json", 'w') as f:
				json.dump(rewards, f, indent=4)




		monthlyReward = 36000
		multiplier = self.bot.get_cog("Economy").getMultiplier(ctx.author)
		extraMoney = int(monthlyReward * (multiplier - 1))
		await self.bot.get_cog("Economy").addWinnings(userId, monthlyReward + extraMoney)
		balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
		embed = discord.Embed(color=1768431)
		embed.add_field(name = f"You got {monthlyReward} (+{extraMoney}) {self.coin}", 
						value = f"You have {balance} credits\nMultiplier: {multiplier}x\nExtra Money: {extraMoney}", inline=False)
		await ctx.send(embed=embed)

def setup(bot):
	bot.add_cog(WeeklyMonthly(bot))