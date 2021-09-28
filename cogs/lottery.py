import discord
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions
import asyncio

import time
import random

import datetime
import numpy as np
import math

import json


class Lottery(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		# self.CHANNEL_ID = 881421294866927686
		self.CHANNEL_ID = 881421294866927686
		self.COMMANDS_ID = 790041597235822592
		self.SERVER_ID = 585226670361804827
		self.userTickets = list()
		self.coin = "<:coins:585233801320333313>"
		self.lotteryTask.start()
		self.sendToChannels = []

		

	@commands.group(aliases=['ticket'], invoke_without_command=True)
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def lottery(self, ctx, amnt:str=""):
		if ctx.invoked_subcommand is not None:
			return
		# COMMANDS_ID = self.bot.get_channel(self.COMMANDS_ID)
		# if ctx.guild.id != self.SERVER_ID: # if not correct channel
		# 	await ctx.send(f"This command can only be played in the support server. Feel free to join the server in the {ctx.prefix}help menu")
		# 	return

		with open(r"lotteryChannels.json", 'r') as f:
			channels = json.load(f)

		if str(ctx.guild.id) not in channels:
			await ctx.send("An Administrator must set the channel for the lottery announcements. This can be ANY TEXT channel.\n" + 
				f"Please type `{ctx.prefix}lottery channel #channel`")
			return


		if not amnt:
			try:
				timeRemaining = await self.getTime()
			except:
				timeRemaining = "N/A; no lottery is running..."
			await ctx.send("Welcome to the lottery!\nEach lottery lasts for 4 hours." +
				f"\nEach ticket is 1000{self.coin}." +
				"\n\nProper command use: .lottery <amnt>\nExample: .lottery 3" +
				f"\n\nCurrent lottery ends in **{timeRemaining}**")
			return

		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))

		# if user tries to enter "half" or "all", talking about their balance... we need to convert that 
		newAmnt = await self.bot.get_cog("Economy").GetBetAmount(ctx, str(amnt))

		# if amount retrieved vs. amount entered in... we need to convert to # of tickets
		if str(amnt) != str(newAmnt):
			newAmnt = int(newAmnt // 1000)

		if newAmnt + self.userTickets.count(ctx.author) > 500:
			await ctx.send("The maximum number of tickets you can buy is 500.")
			return

		cost = newAmnt * 1000

		if not await self.bot.get_cog("Economy").subtractBet(ctx.author, cost):
			await self.bot.get_cog("Economy").notEnoughMoney(ctx)
			return

		for _ in range(newAmnt):
			self.userTickets.append(ctx.author)

		await ctx.send(f"Purchased {newAmnt} tickets successfully for {cost}{self.coin}! Good luck!!!")

		if channels[f"{ctx.guild.id}"] not in self.sendToChannels:
			self.sendToChannels.append(channels[f"{ctx.guild.id}"])


	@lottery.command()
	@has_permissions(administrator=True)
	async def channel(self, ctx, chnl):
		with open(r"lotteryChannels.json", 'r') as f:
			channels = json.load(f)
		if "<#" != chnl[0:2]:
			if chnl == 'remove' or chnl == 'stop':
				del channels[f"{ctx.guild.id}"]
				await ctx.send("Removed your server from the list. This will go into effect after the current lottery ends.")
			else:
				await ctx.send(f"I don't know what {chnl} is. Please #mention a channel instead.")
				return
		else:
			channels[f"{ctx.guild.id}"] = int(chnl[2:-1])
			await ctx.send("Channel set successfully.\nYou can type `.lottery channel remove` to stop receiving the messages whenever you'd like.")

		with open(r"lotteryChannels.json", 'w') as f:
			json.dump(channels, f, indent=4)


	@tasks.loop(hours=4)
	async def lotteryTask(self):
		if not self.userTickets:
			return

		with open(r"lotteryChannels.json", 'r') as f:
			channels = json.load(f)

		prizeAmount = len(self.userTickets) * 1000

		uniqueList = np.array([x.id for x in self.userTickets])
		if len(np.unique(uniqueList)) == 1:
			prizeAmount = int(prizeAmount * 1.05)
			winner = self.userTickets[0]
			msg = f"{winner.mention} was the only one who entered the lottery.\nAs a reward, they got their money back + 5%!\nTotal received: {prizeAmount}{self.coin}"
		else:
			winner = random.choice(self.userTickets)
			msg = f"CONGRATULATIONS TO {winner.mention}.\nThey won {prizeAmount}{self.coin}"

		for chnlId in self.sendToChannels: # get each channel id to send lottery results to
			chnl = self.bot.get_channel(chnlId) # convert to channel
			try: await chnl.send(msg) # send winning message
			except: pass
		self.sendToChannels.clear()
		self.sendToChannels.append(585226670361804827)
		self.userTickets.clear()

		try:
			await self.bot.get_cog("Economy").addWinnings(winner.id, prizeAmount)
		except Exception as e:
			errorChannel = self.bot.get_channel(790282020009148446)
			await errorChannel.send(f"<@547475078082985990> {str(e)}\nNeed to give {winner.mention} ({winner.id}) {prizeAmount}{self.coin} ")

	@lotteryTask.before_loop
	async def before_lotteryTask(self):	
		await self.bot.wait_until_ready()

	async def getTime(self):
		timeLeft = self.lotteryTask.next_iteration - datetime.datetime.now(datetime.timezone.utc)
		strTimeLeft = str(timeLeft).split(".")[0]
		strTimeLeft = strTimeLeft.split(":")
		return f"{strTimeLeft[0]}h {strTimeLeft[1]}m {strTimeLeft[2]}s"


	@commands.command()
	async def stopLottery(self, ctx): 
		if not await self.bot.is_owner(ctx.author):
			return
		# await ctx.message.delete()
		if self.lotteryTask.is_running():
			await ctx.send("Lottery stopped")
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