import discord
from discord.ext import commands#, tasks
import asyncio

import random


class Utilities(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	@commands.cooldown(1, 20, commands.BucketType.user)
	async def rob(self, ctx, *, member: discord.Member):
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))
		if not await self.bot.get_cog("Economy").accCheck(member):
			await ctx.invoke(self.bot.get_command('start'), member)

		bal1 = await self.bot.get_cog("Economy").getBalance(ctx.author)
		if bal1 < 500:
			await ctx.send(f"{ctx.author}, you need at least 500<:coins:585233801320333313> to rob.")
			return
		
		bal2 = await self.bot.get_cog("Economy").getBalance(member)
		if bal2 < 500:
			await ctx.send(f"{member.mention} needs at least 500<:coins:585233801320333313> to be robbed.")
			return

		choice = random.randrange(0, 10)
		# amnt = random.range(500, 5000)

		if choice <= 7:
			coin = "<:coins:585233801320333313>"
			# amnt = -1

			if choice <= 4: # 0 - 4		(50%)
				robber = ctx.author
				robbee = member
				robbedBal = bal2
			else: # 5, 6, or 7			(30%)
				robber = member
				robbee = ctx.author
				robbedBal = bal1

			# bal is person getting robbed 
			if robbedBal <= 100000:
				thebal = int(robbedBal/4)
				if thebal < 500:
					thebal = 501
				amnt = random.randrange(500,thebal)
			else:
				amnt = random.randrange(500, 25001)

			if choice <= 4: # 0 - 4		(50%)
				message = f"While {member.mention} was sleeping, you took {amnt}{coin} out of their pockets."
			else: # 5, 6, or 7			(30%)
				message = f"As you walk past {member.mention}, you try to pick pocket them, but they notice. They beat you up and steal {amnt}{coin} from you instead."


			await self.bot.get_cog("Economy").addWinnings(robber.id, amnt)
			await self.bot.get_cog("Economy").addWinnings(robbee.id, -amnt)

			balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
			await ctx.reply(message + f"\nYour new balance is {balance}{coin}")
				

		else:							# (20%)
			await ctx.send(f"{member.mention} caught you red-handed! But they decided to forgive you... No money has been robbed!")




def setup(bot):
	bot.add_cog(Utilities(bot))