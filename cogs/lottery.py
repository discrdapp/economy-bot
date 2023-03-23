import nextcord
from nextcord.ext import commands 
from nextcord import Interaction
from nextcord import FFmpegPCMAudio 
from nextcord import Member 
from nextcord.ext.commands import has_permissions, MissingPermissions

import cooldowns
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
		self.CHANNEL_ID = 881421294866927686
		self.COMMANDS_ID = 790041597235822592
		self.SERVER_ID = 585226670361804827
		self.userTickets = list()
		self.coin = "<:coins:585233801320333313>"
		self.lotteryTask.start()
		self.sendToChannels = [self.CHANNEL_ID]

		

	@nextcord.slash_command()
	@cooldowns.cooldown(1, 3, bucket=cooldowns.SlashBucket.author)
	async def lottery(self, interaction:Interaction, amnt:str=""):
		if interaction.invoked_subcommand is not None:
			return
		# COMMANDS_ID = self.bot.get_channel(self.COMMANDS_ID)
		# if interaction.guild.id != self.SERVER_ID: # if not correct channel
		# 	await interaction.send(f"This command can only be played in the support server. Feel free to join the server in the /help menu")
		# 	return

		with open(r"lotteryChannels.json", 'r') as f:
			channels = json.load(f)

		if str(interaction.guild.id) not in channels:
			await interaction.send("An Administrator must set the channel for the lottery announcements. This can be ANY TEXT channel.\n" + 
				f"Please type `/lottery channel #channel`")
			return


		if not amnt:
			msg = ""
			try:
				timeRemaining = await self.getTime()
				msg += "Welcome to the lottery!\nEach lottery lasts for 4 hours." 
				msg += f"\nEach ticket is 1000{self.coin}."
				msg += "\n\nProper command use: .lottery <amnt>\nExample: .lottery 3"
				msg += f"\n\nCurrent lottery ends in **{timeRemaining}**"
				if len(self.userTickets):
					msg += f"\nThere are currently {len(self.userTickets)} tickets purchased."
				else:
					msg += "\nNo tickets have been purchased yet!"
			except:
				msg += "The lottery is currently closed. Please check back soon..."

			await interaction.send(msg)
			return

		if not await self.bot.get_cog("Economy").accCheck(interaction.user):
			await self.bot.get_cog("Economy").StartPlaying(interaction, interaction.user)

		# if user tries to enter "half" or "all", talking about their balance... we need to convert that 
		newAmnt = await self.bot.get_cog("Economy").GetBetAmount(interaction, str(amnt))

		# if amount retrieved vs. amount entered in... we need to convert to # of tickets
		if str(amnt) != str(newAmnt):
			newAmnt = int(newAmnt // 1000)

		if newAmnt + self.userTickets.count(interaction.user) > 500:
			await interaction.send("The maximum number of tickets you can buy is 500.")
			return

		cost = newAmnt * 1000

		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, cost):
			await self.bot.get_cog("Economy").notEnoughMoney(interaction)
			return

		for _ in range(newAmnt):
			self.userTickets.append(interaction.user)

		await interaction.send(f"Purchased {newAmnt} tickets successfully for {cost}{self.coin}! Good luck!!!")

		if channels[f"{interaction.guild.id}"] not in self.sendToChannels:
			self.sendToChannels.append(channels[f"{interaction.guild.id}"])


	@lottery.command()
	@has_permissions(administrator=True)
	async def channel(self, interaction:Interaction, chnl):
		with open(r"lotteryChannels.json", 'r') as f:
			channels = json.load(f)
		if "<#" != chnl[0:2]:
			if chnl == 'remove' or chnl == 'stop':
				del channels[f"{interaction.guild.id}"]
				await interaction.send("Removed your server from the list. This will go into effect after the current lottery ends.")
			else:
				await interaction.send(f"I don't know what {chnl} is. Please #mention a channel instead.")
				return
		else:
			channels[f"{interaction.guild.id}"] = int(chnl[2:-1])
			await interaction.send("Channel set successfully.\nYou can type `.lottery channel remove` to stop receiving the messages whenever you'd like.")

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
		self.sendToChannels.append(self.CHANNEL_ID)
		self.userTickets.clear()

		await self.bot.get_cog("Economy").addWinnings(winner.id, prizeAmount)

	@lotteryTask.before_loop
	async def before_lotteryTask(self):	
		await self.bot.wait_until_ready()

	async def getTime(self):
		timeLeft = self.lotteryTask.next_iteration - datetime.datetime.now(datetime.timezone.utc)
		strTimeLeft = str(timeLeft).split(".")[0]
		strTimeLeft = strTimeLeft.split(":")
		return f"{strTimeLeft[0]}h {strTimeLeft[1]}m {strTimeLeft[2]}s"


	@nextcord.slash_command()
	async def stopLottery(self, interaction:Interaction): 
		if not await self.bot.is_owner(interaction.user):
			return
		# await interaction.message.delete()
		if self.lotteryTask.is_running():
			await interaction.send("Lottery stopped")
			self.lotteryTask.cancel()
			await self.refundTickets(interaction)
		else:
			await interaction.send("Lottery is not running!", delete_after=3)

	@nextcord.slash_command()
	async def startLottery(self, interaction:Interaction):
		if interaction.user.id != self.bot.owner_id:
			return
		if not interaction:
			return
		if not self.lotteryTask.is_running():
			await interaction.send("Starting lottery!", delete_after=3)
			self.lotteryTask.start()
		else:
			await interaction.send("Lottery is already running", delete_after=3)

	@nextcord.slash_command()
	async def printTickets(self, interaction:Interaction):
		if interaction.user.id != self.bot.owner_id:
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
			await interaction.send("No one owns a ticket.")
		else:
			await interaction.send(msg)


	@nextcord.slash_command()
	async def refundTickets(self, interaction:Interaction):
		if interaction.user.id != self.bot.owner_id:
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
			await interaction.send("No one owns a ticket, so no refunds have been made.")
		else:
			await interaction.send(msg)

	@nextcord.slash_command()
	async def resetTickets(self, interaction:Interaction):
		if interaction.user.id != self.bot.owner_id:
			return
		self.userTickets.clear()
		await interaction.send("Tickets were cleared.")

	
	async def giveTickets(self, user, amnt):
		for _ in range(amnt):
			self.userTickets.append(user)

	@nextcord.slash_command()
	async def sendChannelList(self, interaction:Interaction):
		if self.sendToChannels:
			await interaction.send(self.sendToChannels)
		else:
			await interaction.send("List is empty.")


def setup(bot):
	bot.add_cog(Lottery(bot))