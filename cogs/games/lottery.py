import nextcord
from nextcord.ext import commands, tasks, application_checks
from nextcord import Interaction
from nextcord.ext.commands import has_permissions

import cooldowns, random, datetime, json
import numpy as np

import config

class Lottery(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.CHANNEL_ID = 881421294866927686
		self.userTickets = list()
		self.coin = "<:coins:585233801320333313>"
		self.lotteryTask.start()
		self.sendToChannels = [self.CHANNEL_ID]


	@nextcord.slash_command()
	@cooldowns.cooldown(1, 3, bucket=cooldowns.SlashBucket.author)
	async def lottery(self, interaction:Interaction):
		pass

	@lottery.subcommand()
	@has_permissions(administrator=True)
	async def info(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Lottery")
		msg = ""
		try:
			timeRemaining = await self.getTime()
			msg += "Each lottery lasts for 4 hours." 
			msg += f"\nEach ticket is 1,000{self.coin}."
			msg += f"\n\nCurrent lottery ends in **{timeRemaining}**"
			if len(self.userTickets):
				msg += f"\nThere are currently {len(self.userTickets)} tickets purchased."
			else:
				msg += "\nNo tickets have been purchased yet!"
			if interaction.user in self.userTickets:
				msg += f"\n\nYou have {self.userTickets.count(interaction.user)} tickets"
		except:
			msg += "The lottery is currently closed. Please check back soon..."

		embed.description = msg

		await interaction.send(embed=embed)
	
	@lottery.subcommand()
	@has_permissions(administrator=True)
	async def buy(self, interaction:Interaction, amnt:int=1):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Lottery")
		if not self.lotteryTask.is_running():
			embed.description = "The lottery is currently closed. Please check back soon..."
			await interaction.send(embed=embed)
			return

		with open(r"lotteryChannels.json", 'r') as f:
			channels = json.load(f)

		if str(interaction.guild.id) not in channels:
			embed.description = "An Administrator must set the channel for the lottery announcements. This can be ANY TEXT channel.\n \
								 Please type `/lottery channel #channel`"
			await interaction.send(embed=embed)
			return

		if amnt + self.userTickets.count(interaction.user) > 500:
			embed.description = "The maximum number of tickets you can buy is 500."
			await interaction.send(embed=embed)
			return

		cost = amnt * 1000

		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, cost):
			raise Exception("tooPoor")

		for _ in range(amnt):
			self.userTickets.append(interaction.user)

		embed.description = f"Purchased {amnt} tickets successfully for {cost:,}{self.coin}! Good luck!!!"
		await interaction.send(embed=embed)

		if channels[f"{interaction.guild.id}"] not in self.sendToChannels:
			self.sendToChannels.append(channels[f"{interaction.guild.id}"])


	@lottery.subcommand()
	@has_permissions(administrator=True)
	async def channel(self, interaction:Interaction, channel: nextcord.TextChannel):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Lottery")
		with open(r"lotteryChannels.json", 'r') as f:
			channels = json.load(f)

		channels[f"{interaction.guild.id}"] = channel.id
		embed.description = "Channel set successfully.\nYou can type `/lottery remove` to stop participating in the lottery."
		await interaction.send(embed=embed)

		with open(r"lotteryChannels.json", 'w') as f:
			json.dump(channels, f, indent=4)

	@lottery.subcommand()
	@has_permissions(administrator=True)
	async def remove(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Lottery")
		with open(r"lotteryChannels.json", 'r') as f:
			channels = json.load(f)

		if f"{interaction.guild.id}" in channels:
			del channels[f"{interaction.guild.id}"]
			embed.description = "Removed your server from the list. This will go into effect after the current lottery ends."
		else:
			embed.description = "Your server has already been removed or was never set up for our lottery. \
								\nIf you believe this is an error, please open a ticket in our support server in the help menu."
		await interaction.send(embed=embed)

		with open(r"lotteryChannels.json", 'w') as f:
			json.dump(channels, f, indent=4)

	# @tasks.loop(seconds=10)
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
			msg = f"{winner.mention} was the only one who entered the lottery.\nAs a reward, they got their money back + 5%!\nTotal received: {prizeAmount:,}{self.coin}"
		else:
			winner = random.choice(self.userTickets)
			msg = f"CONGRATULATIONS TO {winner.mention}.\nThey won {prizeAmount:,}{self.coin}"

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


	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def stoplottery(self, interaction:Interaction): 
		# await interaction.message.delete()
		if self.lotteryTask.is_running():
			await interaction.send("Lottery stopped")
			self.lotteryTask.cancel()
			await self.refundtickets(interaction)
			self.userTickets.clear()
			self.sendToChannels = [self.CHANNEL_ID]
		else:
			await interaction.send("Lottery is not running!", delete_after=3)

	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def startlottery(self, interaction:Interaction):
		if not interaction:
			return
		if not self.lotteryTask.is_running():
			await interaction.send("Starting lottery!", delete_after=3)
			self.lotteryTask.start()
		else:
			await interaction.send("Lottery is already running", delete_after=3)

	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def printtickets(self, interaction:Interaction):
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


	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def refundtickets(self, interaction:Interaction):
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

	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def resettickets(self, interaction:Interaction):
		if interaction.user.id != self.bot.owner_id:
			return
		self.userTickets.clear()
		await interaction.send("Tickets were cleared.")

	
	async def giveTickets(self, user, amnt):
		for _ in range(amnt):
			self.userTickets.append(user)

	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def sendchannellist(self, interaction:Interaction):
		if self.sendToChannels:
			await interaction.send(self.sendToChannels)
		else:
			await interaction.send("List is empty.")


def setup(bot):
	bot.add_cog(Lottery(bot))