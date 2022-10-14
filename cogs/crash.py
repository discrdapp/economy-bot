# Stock market crash game

import nextcord
from nextcord.ext import commands 
from nextcord import Interaction
from nextcord import FFmpegPCMAudio 
from nextcord import Member 
from nextcord.ext.commands import has_permissions, MissingPermissions

import sqlite3
import asyncio
import random

import math

class Crash(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.userId = ""
		self.task = None
		self.multiplier = 1.0
		self.crashNum = 1.2
		self.coin = "<:coins:585233801320333313>"
		self.crash = False
		self.amntbet = 0


	async def do_loop(self, interaction:Interaction, botMsg, embed): # keeps the number going and edits the message, until it "crashes"
		await asyncio.sleep(2)
		while True: # will keep going until crash
			self.multiplier += 0.2
			self.multiplier = round(self.multiplier, 1)
			#await self.bot.wait_for('message', check=is_stop, timeout=2)
			embed.set_field_at(0, name = f"Multiplier", value = f"{str(self.multiplier)}x", inline=True)
			embed.set_field_at(1, name = "Profit", value = f"{str(round(self.multiplier * self.amntbet - self.amntbet))}{self.coin}", inline=True)
			await botMsg.edit(embed=embed)
			if self.multiplier == self.crashNum: # if the current multiplier number is the number to crash on 
				self.crash = True
				break
			await asyncio.sleep(2)	
		self.task.cancel() # ends the task


	@nextcord.slash_command()
	@commands.bot_has_guild_permissions(send_messages=True, embed_links=True, use_external_emojis=True)
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def crash(self, interaction:Interaction, bet): # actual command
		if not await self.bot.get_cog("Economy").accCheck(interaction.user):
			await self.bot.get_cog("Economy").start(interaction, interaction.user)

		bet = await self.bot.get_cog("Economy").GetBetAmount(interaction, bet)

		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, bet):
			await self.bot.get_cog("Economy").notEnoughMoney(interaction)
			return


		self.amntbet = round(bet)
		self.userId = interaction.user.id
		# self.crashNum = round(random.uniform(1.2, 2.4), 1)

		pC = random.randint(1, 10)

		if 1 <= pC <= 3:	self.crashNum = 1.2 								# 30%
		elif 4 <= pC <= 5:	self.crashNum = 1.4									# 20% 
		elif 6 <= pC <= 8:	self.crashNum = random.choice([1.6, 1.8])			# 30%
		elif pC == 9:		self.crashNum = random.choice([1.8, 2.0, 2.2, 2.4])	# 10%
		elif pC == 10:	 	
			self.crashNum = round(random.uniform(2.6, 12.0), 1)					# 10%
			if int(self.crashNum * 10) % 2 == 1: self.crashNum = round(self.crashNum + 0.1, 1)

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name}' Casino | Crash")
		embed.set_footer(text="Use .done to stop")
		embed.add_field(name = "Multiplier:", value = f"{str(self.multiplier)}x", inline=True)
		embed.add_field(name = "Profit", value = f"{str(round(self.multiplier * self.amntbet - self.amntbet))}{self.coin}", inline=True)
		botMsg = await interaction.response.send_message(embed=embed)

		try:
			if self.crashNum == 1.2:
				self.crash = True
				raise Exception
			self.task = self.bot.loop.create_task(self.do_loop(interaction, botMsg, embed)) # creates loop for the crash game
			await self.task # performs the loop
		except:
			# all of this will occur once the game is over

			embed = nextcord.Embed(color=0x23f518, title=f"{self.bot.user.name}' Casino | Crash")
			multi = self.bot.get_cog("Economy").getMultiplier(interaction.user)
			profitInt = 0
			
			if not self.crash: # if they .stop it before it crashes 
				profitInt = int(self.amntbet * self.multiplier - self.amntbet) 
				moneyToAdd = int(self.amntbet + profitInt)
				profit = f"**{profitInt}** (+**{int(profitInt * (multi - 1))}**)"

				await self.bot.get_cog("Economy").addWinnings(interaction.user.id, (moneyToAdd + (profitInt * (multi - 1))))

			else: # if game crashes without them $stop'ing it in time
				profitInt = -self.amntbet
				moneyToAdd = 0
				profit = f"**{profitInt}**"
				embed.color = nextcord.Color(0xff2020)

			balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
			

			embed.add_field(name = f"Crashed at", value = f"{str(self.multiplier)}x", inline=True)

			embed.add_field(name = "Profit", value = f"{profit}", inline=True)

			if not self.crash:
				embed.add_field(name = f"Would've crashed at {self.crashNum}", value="_ _", inline=False)
			embed.add_field(name = "Credits",
								value = f"You have {balance} credits", inline=False)

			priorBal = balance - profitInt
			minBet = priorBal * 0.05
			minBet = int(math.ceil(minBet / 10.0) * 10.0)
			if self.amntbet >= minBet:
				xp = random.randint(50, 500)
				embed.set_footer(text=f"Earned {xp} XP!")
				await self.bot.get_cog("XP").addXP(interaction, xp)
			else:
				embed.set_footer(text=f"You have to bet your minimum to earn xp.")

			await botMsg.edit(embed=embed)

			await self.bot.get_cog("Totals").addTotals(interaction, self.amntbet, moneyToAdd, 2)

			await self.bot.get_cog("Quests").AddQuestProgress(interaction, interaction.user, "Crsh", profitInt)

		finally:
			# resets all the variables 
			self.task = None
			self.multiplier = 1.0
			self.crashNum = 1.6
			self.crash = False
			self.amntbet = 0


	@nextcord.slash_command()
	async def done(self, interaction:Interaction): # the command to stop the game before it "crashes"
		if self.task is not None and self.multiplier != self.crashNum and interaction.user.id == self.userId:
			self.task.cancel() # cancel task if there is a current task, and current multiplier number isn't the crashing number
							   # and user issuing command is user who started the game

def setup(bot):
	bot.add_cog(Crash(bot))