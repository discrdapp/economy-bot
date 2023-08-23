import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import cooldowns
from random import randint

import config
from db import DB


class ScratchTile(nextcord.ui.Button):
	def __init__(self, label, value, style, row, disabled=True):
		super().__init__(label=label, style=style, row=row, disabled=disabled)
		self.value = value
	async def callback(self, interaction: nextcord.Interaction):
		assert self.view is not None
		view: ScratchTicket = self.view

		if view.ownerId != interaction.user.id:
			await interaction.send("This is not your game!", ephemeral=True)
			return

		self.disabled = True
		
		if self.label == "W1":
			for child in view.children:
				if child.label != "W1":
					child.disabled = False
			self.label = self.value
			await interaction.edit(view=view)
			return
		
		self.label = self.value
			
		if self.value == view.winningNumber:
			self.style = nextcord.ButtonStyle.green
			view.matchingNums += 1
		else:
			self.style = nextcord.ButtonStyle.red
		
		view.ScratchTilesRemaining -= 1

		await interaction.edit(content=f"Current Profit: {(view.matchingNums*view.amntbet) - view.amntbet}", view=view)

		if view.ScratchTilesRemaining == 0:
			await view.EndGame(interaction, (view.matchingNums*view.amntbet) - view.amntbet)
			return


class ScratchTicket(nextcord.ui.View):
	def __init__(self, bot, amntbet, ownerId):
		super().__init__(timeout=60)
		self.bot:commands.bot.Bot = bot
		self.coin = "<:coins:585233801320333313>"

		self.amntbet = amntbet
		self.ownerId = ownerId

		self.matchingNums = 0
		self.ScratchTilesRemaining = 9

		self.GenerateTicket()
	

	async def Start(self, interaction):
		await interaction.send(content=f"Current Profit: -{self.amntbet}", view=self)
	
	async def EndGame(self, interaction, profit):
		self.stop()

		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)

		if profit >= 0:
			moneyToAdd = profit+self.amntbet
		else:
			moneyToAdd = 0

		gameID = await self.bot.get_cog("Economy").addWinnings(self.ownerId, moneyToAdd, giveMultiplier=True, 
							  activityName="Scratch", amntBet=self.amntbet)

		embed = nextcord.Embed(color=0xff2020)
		embed = await DB.addProfitAndBalFields(self, interaction, profit, embed)

		# Why don't we just calculate the XP in subtractBet
		embed = await DB.calculateXP(self, interaction, balance, self.amntbet, embed, gameID)
		await interaction.edit(content="", embed=embed, view=self)
	
	def GenerateTicket(self):
		self.winningNumber = randint(10, 99)

		hasOneSameNumber = hasTwoSameNumber = hasThreeSameNumber = hasFourSameNumber = False

		# 50% chance of getting your money back
		hasOneSameNumber = randint(0, 1)
		if hasOneSameNumber:
			placeForNumber = randint(1, 9)

			# 50% chance of making money (25% chance TOTAL)
			hasTwoSameNumber = randint(0, 1)
			if hasTwoSameNumber:
				placeForNumber2 = randint(1, 9)
				while placeForNumber == placeForNumber2:
					placeForNumber2 = randint(1, 9)

				# 50% chance of making money (12.5% chance TOTAL)
				hasThreeSameNumber = randint(0, 1)
				if hasThreeSameNumber:
					placeForNumber3 = randint(1, 9)
					while placeForNumber3 == placeForNumber or placeForNumber3 == placeForNumber2:
						placeForNumber3 = randint(1, 9)

					# 50% chance of making money (6.25% chance TOTAL)
					hasFourSameNumber = randint(0, 1)
					if hasFourSameNumber:
						placeForNumber4 = randint(1, 9)
						while placeForNumber4 == placeForNumber or placeForNumber4 == placeForNumber2 or placeForNumber4 == placeForNumber3:
							placeForNumber4 = randint(1, 9)
		
		count = 0
		row = 1

		self.add_item(ScratchTile(label="W1", value=self.winningNumber, style=nextcord.ButtonStyle.blurple, row=0, disabled=False))
		for x in "ABC":
			for y in range(1, 4):
				count += 1
				if  (hasOneSameNumber and count == placeForNumber) or \
					(hasTwoSameNumber and count == placeForNumber2) or \
					(hasThreeSameNumber and count == placeForNumber3 or \
					(hasFourSameNumber and count == placeForNumber4)):
					value = self.winningNumber
				else:
					value = randint(10, 99)
				self.add_item(ScratchTile(label=f"{x}{y}", value=value, style=nextcord.ButtonStyle.gray, row=row))
			row += 1
		
		

class Scratch(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.coin = "<:coins:585233801320333313>"


	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@commands.bot_has_guild_permissions(send_messages=True, manage_messages=True, embed_links=True, use_external_emojis=True, attach_files=True)
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='scratch')
	async def scratch(self, interaction:Interaction, amntbet:int=nextcord.SlashOption(description="Enter the amount you want to bet. Minimum is 100")):
		if amntbet < 100:
			raise Exception("minBet 100")

		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, amntbet):
			raise Exception("tooPoor")
		
		game = ScratchTicket(self.bot, amntbet, interaction.user.id)
		await game.Start(interaction)


def setup(bot):
	bot.add_cog(Scratch(bot))