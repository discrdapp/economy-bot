import discord
from discord.ext import commands, tasks
import asyncio

import time
import random


class Lottery(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.CHANNEL_ID = 881421294866927686
		self.COMMANDS_ID = 790041597235822592
		self.SERVER_ID = 585226670361804827
		self.userTickets = list()
		self.coin = "<:coins:585233801320333313>"
		self.lotteryTask.start()

	@commands.command(aliases=['ticket'])
	@commands.cooldown(1, 30, commands.BucketType.user)
	async def lottery(self, ctx, amnt=-1):
		COMMANDS_ID = self.bot.get_channel(self.COMMANDS_ID)
		if ctx.guild.id != self.SERVER_ID: # if not correct channel
			await ctx.send(f"This command can only be played in the support server. Feel free to join the server in the {ctx.prefix}help menu")
			return

		if amnt == -1:
			await ctx.send(f"Welcome to the lottery!\nEach lottery lasts for 4 hours.\nEach ticket is 1000{self.coin}.\nProper command use: .lottery <amnt>\nExample: .lottery 3")
			return

		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))

		if not await self.bot.get_cog("Economy").subtractBet(ctx.author, amnt * 1000):
			await self.bot.get_cog("Economy").notEnoughMoney(ctx)
			return

		for _ in range(amnt):
			self.userTickets.append(ctx.author)

		await ctx.send(f"Purchased {amnt} tickets successfully! Good luck!!!")

	@tasks.loop(hours=4)
	async def lotteryTask(self):
		CHANNEL = self.bot.get_channel(self.CHANNEL_ID)

		if len(self.userTickets) == 0:
			await CHANNEL.send(f"There was no winner for this lottery because no one joined...")
			return

		prizeAmount = len(self.userTickets) * 1000
		if len(self.userTickets) == 1:
			prizeAmount = int(prizeAmount * 1.05)
			await CHANNEL.send(f"{self.userTickets[0].mention}, you were the only one who entered the lottery... here's your money back + 5%!" + 
				f"\nTotal received: {prizeAmount}{self.coin}")
			winner = self.userTickets[0]
		else:
			winner = random.choice(self.userTickets)
			await CHANNEL.send(f"CONGRATULATIONS TO {winner.mention}.\nThey won {prizeAmount}{self.coin}")
		
		self.userTickets.clear()

		await self.bot.get_cog("Economy").addWinnings(winner.id, prizeAmount)

	@lotteryTask.before_loop
	async def before_lotteryTask(self):	
		await self.bot.wait_until_ready()

	@commands.command()
	async def stopLottery(self, ctx): 

		if not await self.bot.is_owner(ctx.author):
			return
		# await ctx.message.delete()
		if self.lotteryTask.is_running():
			await ctx.send("Lottery stopped", delete_after=3)
			self.lotteryTask.cancel()
			await self.refundTickets(ctx)
		else:
			await ctx.send("Lottery is not running!", delete_after=3)

	@commands.command()
	async def startLottery(self, ctx):
		if ctx.author.id != self.bot.owner_id:
			return
		if not ctx:
			return
		if not self.lotteryTask.is_running():
			await ctx.send("Starting lottery!", delete_after=3)
			self.lotteryTask.start()
		else:
			await ctx.send("Lottery is already running", delete_after=3)

	@commands.command(aliases=['listtickets', 'ticketlist', 'printickets'])
	async def printTickets(self, ctx):
		if ctx.author.id != self.bot.owner_id:
			return
		users = dict()
		for user in self.userTickets:
			if user.id not in users.keys():
				users[user.id] = 1
			else:
				users[user.id] += 1

		msg = ""
		for userID, tickets in users.items():
			user = await self.bot.fetch_user(userID)
			await self.bot.get_cog("Economy").addWinnings(user.id, tickets * 1000)
			msg += f"User {user.mention} owns {tickets} tickets.\n"

		if not msg:
			await ctx.send("No one owns a ticket.")
		else:
			await ctx.send(msg)


	@commands.command()
	async def refundTickets(self, ctx):
		if ctx.author.id != self.bot.owner_id:
			return
		users = dict()
		for user in self.userTickets:
			if user.id not in users.keys():
				users[user.id] = 1
			else:
				users[user.id] += 1

		msg = ""
		for userID, tickets in users.items():
			user = await self.bot.fetch_user(userID)
			await self.bot.get_cog("Economy").addWinnings(user.id, tickets * 1000)
			msg += f"User {user.mention} refunded {tickets} tickets.\n"

		if not msg:
			await ctx.send("No one owns a ticket, so no refunds have been made.")
		else:
			await ctx.send(msg)

	@commands.command(aliases=['clearTickets'])
	async def resetTickets(self, ctx):
		if ctx.author.id != self.bot.owner_id:
			return
		self.userTickets.clear()
		await ctx.send("Tickets were cleared.")

	
	async def giveTickets(self, user, amnt):
		for _ in range(amnt):
			self.userTickets.append(user)



def setup(bot):
	bot.add_cog(Lottery(bot))