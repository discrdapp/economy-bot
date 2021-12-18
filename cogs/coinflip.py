# economy-related stuff like betting and gambling, etc.

import discord
from discord.ext import commands
import asyncio
import random
import math

from db import DB

class Coinflip(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(aliases=['flipcoin', 'flip', 'coin', 'cf', 'coinflips', 'flipscoin', 'flipcoins', 'flipscoins'])
	@commands.bot_has_guild_permissions(send_messages=True, embed_links=True, attach_files=True, use_external_emojis=True)
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def coinflip(self, ctx, sideBet:str, amntBet, user: discord.Member=None):
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))

		amntBet = await self.bot.get_cog("Economy").GetBetAmount(ctx, amntBet)

		sideBet = sideBet.lower()
		if sideBet.find("head") != -1:
			sideBet = "heads"
		elif sideBet.find("tail") != -1:
			sideBet = "tails"
		else:
			raise commands.BadArgument("You need to specify `heads` or `tails` for your bet.\nExample: `.coinflip heads 100`")

		if user:
			def is_me(m):
				return m.channel.id == ctx.channel.id and m.author.id == user.id and m.content == "accept"

			msg = await ctx.send(f"{user.mention}, type: `accept`")
			try:
				await self.bot.wait_for('message', check=is_me, timeout=45)
			except:
				await msg.edit(message="Timeout error")
				raise Exception("timeoutError")
				return

			if not await self.bot.get_cog("Economy").subtractBet(ctx.author, amntBet):
				await self.bot.get_cog("Economy").notEnoughMoney(ctx)
				return

			if not await self.bot.get_cog("Economy").subtractBet(user, amntBet):
				await ctx.send(f"{user.mention} has either not typed .start yet or does not have enough money for this.")
				return

			side = random.choice(["Heads", "Tails"]).lower() # computer picks result

			file = None
			if side == "Heads":
				file = discord.File("./images/coinheads.png", filename="image.png")
			else:
				file = discord.File("./images/cointails.png", filename="image.png")
			if sideBet == side: # if author bets on correct side
				winner = ctx.author
			else: # else, user bet on correct side
				winner = user
			embed = discord.Embed(color=0x23f518)
			embed.set_thumbnail(url="attachment://image.png")
			embed.add_field(name=f"{self.bot.user.name} | Coinflip", value=f"The coin landed on {side}\n_ _{winner.mention} wins!", inline=False)

			await ctx.send(file=file, embed=embed)
			await self.bot.get_cog("Economy").addWinnings(winner.id, amntBet*2)

			return








		###################
		## SINGLE PLAYER ##
		###################

		if not await self.bot.get_cog("Economy").subtractBet(ctx.author, amntBet):
			await self.bot.get_cog("Economy").notEnoughMoney(ctx)
			return


		side = random.choice(["Heads", "Tails"]).lower()
		
		multiplier = self.bot.get_cog("Economy").getMultiplier(ctx.author)

		embed = discord.Embed(color=0x23f518)
		
		if sideBet == side:
			moneyToAdd = int(amntBet * 2)
			profitInt = moneyToAdd - amntBet
			profit = f"**{profitInt}** (**+{int(profitInt * (multiplier - 1))}**)"

			file = discord.File("./images/coinwon.png", filename="image.png")

		else:
			moneyToAdd = 0
			profitInt = moneyToAdd - amntBet
			profit = f"**{profitInt}**"

			file = discord.File("./images/coinlost.png", filename="image.png")
			embed.color = discord.Color(0xff2020)
			
		embed.set_thumbnail(url="attachment://image.png")
		embed.add_field(name=f"{self.bot.user.name}' Casino | Coinflip", value=f"The coin landed on {side}\n_ _",inline=False)
		giveZeroIfNeg = max(0, profitInt) # will give 0 if profitInt is negative. 
																		# we don't want it subtracting anything, only adding
		await self.bot.get_cog("Economy").addWinnings(ctx.author.id, moneyToAdd + (giveZeroIfNeg * (multiplier - 1)))
		
		coin = "<:coins:585233801320333313>"
		balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
		embed.add_field(name="Profit", value=f"{profit}{coin}", inline=True)
		embed.add_field(name="Credits", value=f"**{balance}**{coin}", inline=True)


		embed = await DB.calculateXP(self, ctx, balance - profitInt, amntBet, embed)

		await ctx.send(file=file, embed=embed)
		await self.bot.get_cog("Totals").addTotals(ctx, amntBet, moneyToAdd, 4)

		await self.bot.get_cog("Quests").AddQuestProgress(ctx, ctx.author, "CF", profitInt)

def setup(bot):
	bot.add_cog(Coinflip(bot))