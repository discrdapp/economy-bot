import discord
from discord.ext import commands
import pymysql
import asyncio
import random

import math

class rps(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	@commands.bot_has_guild_permissions(send_messages=True, embed_links=True, attach_files=True, add_reactions=True, use_external_emojis=True, manage_messages=True, read_message_history=True)
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def rps(self, ctx, userChoice: str, amntBet: int):
		coin = "<:coins:585233801320333313>"
		userChoice = userChoice.lower()

		if userChoice != "rock" and userChoice != "paper" and userChoice != "scissors":
			await ctx.send("Incorrect choice. Possible choices are rock, paper, and scissors.")
			return

		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))

		if not await self.bot.get_cog("Economy").subtractBet(ctx.author, amntBet):
			embed = discord.Embed(color=1768431, title=f"{self.bot.user.name} | RPS")
			embed.set_thumbnail(url=ctx.author.avatar_url)
			embed.add_field(name="ERROR", value="You do not have enough to do that.")

			embed.set_footer(text=ctx.author)

			await ctx.send(embed=embed)
			return
			
		botChoice = random.choice(['rock', 'paper', 'scissors'])

		if userChoice == botChoice:
			winner = 0
			file = discord.File("./images/rps/tie.png", filename="image.png")

		elif userChoice == "rock" and botChoice == "scissors":
			winner = 1
			file = discord.File("./images/rps/rockwon.png", filename="image.png")

		elif userChoice == "paper" and botChoice == "rock":
			winner = 1
			file = discord.File("./images/rps/paperwon.png", filename="image.png")

		elif userChoice == "scissors" and botChoice == "paper":
			winner = 1
			file = discord.File("./images/rps/scissorswon.png", filename="image.png")

		elif userChoice == "rock" and botChoice == "paper":	
			winner = -1
			file = discord.File("./images/rps/rocklost.png", filename="image.png")

		elif userChoice == "paper" and botChoice == "scissors":
			winner = -1
			file = discord.File("./images/rps/paperlost.png", filename="image.png")

		elif userChoice == "scissors" and botChoice == "rock":
			winner = -1
			file = discord.File("./images/rps/scissorslost.png", filename="image.png")

		multiplier = self.bot.get_cog("Economy").getMultiplier(ctx.author)
		embed = discord.Embed(color=0xff2020)
		embed.set_thumbnail(url="attachment://image.png")
		if winner == 1:
			moneyToAdd = amntBet * 2 
			profitInt = moneyToAdd - amntBet
			result = "YOU WON"
			profit = f"**{profitInt}** (**+{int(profitInt * (multiplier - 1))}**)"
			
			embed.color = discord.Color(0x23f518)

		elif winner == -1:
			moneyToAdd = 0 # nothing to add since loss
			profitInt = -amntBet # profit = amntWon - amntBet; amntWon = 0 in this case
			result = "YOU LOST"
			profit = f"**{profitInt}**"

		
		elif winner == 0:
			moneyToAdd = amntBet # add back their bet they placed since it was pushed (tied)
			profitInt = 0 # they get refunded their money (so they don't make or lose money)
			result = "PUSHED"
			profit = f"**{profitInt}**"

		embed.add_field(name=f"{self.bot.user.name}' Casino | RPS", value=f"**{ctx.author.name}** picked **{userChoice}** \n**Pit Boss** picked **{botChoice}**",inline=False)
		giveZeroIfNeg = max(0, profitInt) # will give 0 if profit is negative. 
																				# we don't want it subtracting anything, only adding
		await self.bot.get_cog("Economy").addWinnings(ctx.author.id, moneyToAdd + (giveZeroIfNeg * (multiplier - 1)))
		balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
		embed.add_field(name="Profit", value=f"{profit}{coin}", inline=True)
		embed.add_field(name="Credits", value=f"**{balance}**{coin}", inline=True)

		priorBal = balance - profitInt
		minBet = priorBal * 0.05
		minBet = int(math.ceil(minBet / 10.0) * 10.0)
		if amntBet >= minBet:	
			xp = random.randint(50, 500)
			embed.set_footer(text=f"Earned {xp} XP! {amntBet} {minBet}")
			await self.bot.get_cog("XP").addXP(ctx, xp)
		else:
			embed.set_footer(text=f"You have to bet your minimum to earn xp. {amntBet} {minBet}")

		await ctx.send(content=f"{ctx.message.author.mention}", file=file, embed=embed)
		await self.bot.get_cog("Totals").addTotals(ctx, amntBet, moneyToAdd, 5)


	# @rps.error
	# async def rps_handler(self, ctx, error):
	# 	embed = discord.Embed(color=0xff2020, title=f"{self.bot.user.name} Help Menu")
	# 	embed.add_field(name = "`Syntax: .rps <choice> <bet>`", value = "_ _", inline=False)
	# 	embed.add_field(name = "__Verse the bot against some rock, paper, scissors__", value="_ _", inline=False)
	# 	await ctx.send(embed=embed)
	# 	print(error)


def setup(bot):
	bot.add_cog(rps(bot))