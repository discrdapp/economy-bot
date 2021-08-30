import discord
from discord.ext import commands
import pymysql
import asyncio
import config

class WeeklyMonthly(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.levelReward = [550, 1500, 3000, 7500, 13500, 18500, 24000, 29000, 35000, 42000, 50000]
		self.coin = "<:coins:585233801320333313>"

	@commands.command()
	@commands.cooldown(1, 604800, commands.BucketType.user)
	async def weekly(self, ctx):
		await ctx.send("Disabled for maintenance...")
		return
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.send("Hello! Please type .start to create your wallet. :smiley:")
			ctx.command.reset_cooldown(ctx)
			return
		weeklyReward = 12500
		multiplier = self.bot.get_cog("Economy").getMultiplier(ctx.author)
		extraMoney = int(weeklyReward * (multiplier - 1))
		await self.bot.get_cog("Economy").addWinnings(ctx.author.id, weeklyReward + extraMoney)
		balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
		embed = discord.Embed(color=1768431)
		embed.add_field(name = f"You got {weeklyReward} (+{extraMoney}) {self.coin}", 
						value = f"You have {balance} credits\nMultiplier: {multiplier}x\nExtra Money: {extraMoney}", inline=False)
		await ctx.send(embed=embed)

	@commands.command()
	@commands.cooldown(1, 2592000, commands.BucketType.user)
	async def monthly(self, ctx):
		await ctx.send("Disabled for maintenance...")
		return
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.send("Hello! Please type .start to create your wallet. :smiley:")
			ctx.command.reset_cooldown(ctx)
			return
		monthlyReward = 36000
		multiplier = self.bot.get_cog("Economy").getMultiplier(ctx.author)
		extraMoney = int(monthlyReward * (multiplier - 1))
		await self.bot.get_cog("Economy").addWinnings(ctx.author.id, monthlyReward + extraMoney)
		balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
		embed = discord.Embed(color=1768431)
		embed.add_field(name = f"You got {monthlyReward} (+{extraMoney}) {self.coin}", 
						value = f"You have {balance} credits\nMultiplier: {multiplier}x\nExtra Money: {extraMoney}", inline=False)
		await ctx.send(embed=embed)

def setup(bot):
	bot.add_cog(WeeklyMonthly(bot))