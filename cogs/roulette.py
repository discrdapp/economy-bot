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

from PIL import Image

class GetAmountToBet(nextcord.ui.TextInput):
	def __init__(self):
		super().__init__(label="Amount of credits to bet (FOR EACH ONE)", min_length=1, max_length=10, required=False, placeholder="1000")
class GetNumberBet(nextcord.ui.TextInput):
	def __init__(self):
		super().__init__(label = "Number to bet on", min_length = 1, max_length = 2, required=False, placeholder = "0 - 36")
class GetColorBet(nextcord.ui.TextInput):
	def __init__(self):
		super().__init__(label = "Color to bet on", min_length = 3, max_length = 5, required=False, placeholder = "Red, Black, or Green")
class GetParityBet(nextcord.ui.TextInput):
	def __init__(self):
		super().__init__(label = "Bet on the Parity", min_length = 3, max_length = 4, required=False, placeholder = "ODD or EVEN")
class GetHighLowBet(nextcord.ui.TextInput):
	def __init__(self):
		super().__init__(label = "Bet on high or low", min_length = 3, max_length = 4, required=False, placeholder = "HIGH or LOW")


class GetBets(nextcord.ui.Modal):
	def __init__(self):
		super().__init__("Your pet", timeout=60)
		self.number = GetNumberBet()
		self.add_item(self.number)

		self.color = GetColorBet()
		self.add_item(self.color)

		self.parity = GetParityBet()
		self.add_item(self.parity)

		self.highlow = GetHighLowBet()
		self.add_item(self.highlow)

		self.betamnt = GetAmountToBet()
		self.add_item(self.betamnt)

	async def callback(self, interaction: nextcord.Interaction):
		self.stop()
		# await interaction.send(f"{self.number.value} {self.color.value} {self.parity.value} {self.highlow.value} {self.betamnt.value} ")

class Roulette(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.previousNums = []
		self.coin = "<:coins:585233801320333313>"
		self.totalBet = 0

	async def ProcessBets(self, interaction, amntBet, numberBet, parityBet, colorBet, highLowBet):
		if not amntBet or not amntBet.isdigit() or int(amntBet) <= 0 or (numberBet == "" and parityBet == "" and colorBet == "" and highLowBet == ""):
			return None, None, None, None
		amntBet = int(amntBet)

		displayNumberBet = None
		displayParityBet = None
		displayColorBet = None
		displayHighLowBet = None

		if numberBet:
			self.totalBet += amntBet
			if not numberBet.isdigit() or int(numberBet) < 0 or int(numberBet) > 36:
				raise Exception("valueError")
			displayNumberBet = self.getNumEmoji(numberBet)
		if parityBet:
			self.totalBet += amntBet
			if parityBet.lower() != "odd" and parityBet.lower() != "even":
				raise Exception("valueError")
			displayParityBet = "1⃣" if parityBet == "odd" else "2⃣"
		if colorBet:
			self.totalBet += amntBet
			if colorBet.lower() != "red" and colorBet.lower() != "black" and colorBet.lower() != "green":
				raise Exception("valueError")
			if colorBet == "red": displayColorBet = ":heart:"
			elif colorBet == "black": displayColorBet = ":black_heart:"
			else: displayColorBet = ":green_heart:"
		if highLowBet:
			self.totalBet += amntBet
			if highLowBet.lower() != "high" and highLowBet.lower() != "low":
				raise Exception("valueError")
			displayHighLowBet = "⬆" if highLowBet == "high" else "⬇"

		return displayNumberBet, displayHighLowBet, displayColorBet, displayParityBet



	@nextcord.slash_command(description="Play Roulette!")
	@commands.bot_has_guild_permissions(send_messages=True, embed_links=True, attach_files=True, add_reactions=True, use_external_emojis=True, manage_messages=True, read_message_history=True)
	async def roulette(self, interaction:Interaction):
		self.totalBet = 0
		
		modal = GetBets()
		await interaction.response.send_modal(modal)

		if not await self.bot.get_cog("Economy").accCheck(interaction.user):
			await self.bot.get_cog("Economy").StartPlaying(interaction, interaction.user)

		nums = ""
		numCount = 0
		for x in self.previousNums:
			if numCount == 0:
				nums += f"{x}"
			elif numCount % 2 == 1:
				nums += f" , {x}\n"
			elif numCount % 2 == 0:
				nums += f"{x}"

			numCount += 1

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Roulette")
		embed.add_field(name="Picks",
						value=f"Number bet: \nHigh/low bet: \nColor bet: \nParity bet: ",
						inline=True)
		embed.add_field(name="Previous Numbers", value=f"{nums}_ _", inline=True)
		msg = await interaction.send(file=nextcord.File('images/roulette/roulette.png'), embed=embed)

		await modal.wait()

		amntBet = modal.betamnt.value
		numberBet = modal.number.value
		parityBet = modal.parity.value
		colorBet = modal.color.value
		highLowBet = modal.highlow.value

		displayNumberBet, displayHighLowBet, displayColorBet, displayParityBet = await self.ProcessBets(interaction, amntBet, numberBet, parityBet, colorBet, highLowBet)

		if not amntBet or not amntBet.isdigit():
			amntBet = 0
		else:
			amntBet = int(amntBet)
		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, self.totalBet):
			await self.bot.get_cog("Economy").notEnoughMoney(interaction)
			return

		if amntBet: amntBet = int(amntBet)
		if parityBet: parityBet = parityBet.lower()
		if colorBet: colorBet = colorBet.lower()
		if highLowBet: highLowBet = highLowBet.lower()

		n = random.randrange(0, 37)

		roulette = Image.open('images/roulette/roulette.png')
		whiteChip = Image.open('images/roulette/whitechip.png')
		whiteChip = whiteChip.resize((50, 50))
		roulette.paste(whiteChip, self.getPos(n), whiteChip)
		# n = 0

		if n >= 18: 
			highLowResult = "⬆"
			roulette.paste(whiteChip, self.getHighLowPos("high"), whiteChip)
		else: 
			highLowResult = "⬇"
			roulette.paste(whiteChip, self.getHighLowPos("low"), whiteChip)

		if n == 0: colorResult = ":green_heart:"  # green
		elif n == 1 or n == 3 or n == 5 or n == 7 or n == 9 or n == 12 or n == 14 or n == 16 or n == 18 or n == 19 or n == 21 or n == 23 or n == 25 or n == 27 or n == 30 or n == 32 or n == 34 or n == 36:
			colorResult = ":heart:"  # red
			roulette.paste(whiteChip, self.getColorPos("red"), whiteChip)
		else: 
			colorResult = ":black_heart:"  # black
			roulette.paste(whiteChip, self.getColorPos("black"), whiteChip)

		if n % 2 == 0: 
			parityResult = "2⃣"
			roulette.paste(whiteChip, self.getParityPos("even"), whiteChip)
		else:
			parityResult = "1⃣"
			roulette.paste(whiteChip, self.getParityPos("odd"), whiteChip)

		roulette.save("images/roulette/temproulette.png")

		emojiNum = self.getNumEmoji(n)
		winnings = ""

		moneyToAdd = 0
		if numberBet == n:
			winnings += "\nYou guessed the number! You won 35x your bet!"
			await self.bot.get_cog("Economy").addWinnings(interaction.user.id, amntBet * 35)
			moneyToAdd += amntBet * 35

		if displayHighLowBet == highLowResult:
			winnings += "\nYou guessed the high/low! You won 2x your bet!"
			await self.bot.get_cog("Economy").addWinnings(interaction.user.id, amntBet * 2)
			moneyToAdd += amntBet * 2

		if displayColorBet == colorResult and displayColorBet != ":green:":
			winnings += "\nYou guessed the color! You won 2x your bet!"
			await self.bot.get_cog("Economy").addWinnings(interaction.user.id, amntBet * 2)
			moneyToAdd += amntBet * 2
		elif displayColorBet == colorResult:
			winnings += "\nYou guessed the color green! You won 35x your bet!"
			await self.bot.get_cog("Economy").addWinnings(interaction.user.id, amntBet * 35)
			moneyToAdd += amntBet * 35

		if displayParityBet == parityResult:
			winnings += "\nYou guessed the parity! You won 2x your bet!"
			await self.bot.get_cog("Economy").addWinnings(interaction.user.id, amntBet * 2)
			moneyToAdd += amntBet * 2


		amntSpent = self.totalBet
		multiplier = self.bot.get_cog("Economy").getMultiplier(interaction.user)
		if moneyToAdd > amntSpent:
			result = f"You won a grand total of {moneyToAdd} (+{moneyToAdd * (multiplier - 1)}){self.coin} after betting {amntSpent}{self.coin}\n**Profit:** {moneyToAdd - amntSpent}{self.coin}"
		elif moneyToAdd < amntSpent:
			if moneyToAdd > 0:
				result = f"You got back {moneyToAdd}{self.coin} after betting {amntSpent}{self.coin}"
			else:
				result = f"You lost {amntSpent}{self.coin}"
		else:
			result = "You didn't lose or win anything!"

		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		if numberBet or highLowBet or colorBet or parityBet:
			priorBal = balance + amntSpent - moneyToAdd
			minBet = priorBal * 0.05
			minBet = int(math.ceil(minBet / 10.0) * 10.0)
			if amntSpent >= minBet:
				xp = random.randint(50, 500)
				embed.set_footer(text=f"Earned {xp} XP!")
				await self.bot.get_cog("XP").addXP(interaction, xp)
			else:
				embed.set_footer(text=f"You have to bet your minimum to earn xp.")
		else:
			embed.set_footer(text="No bets were placed, no XP was earned.")
		embed.set_field_at(0, name="Picks", 
			value=f"Number bet: {displayNumberBet}\nHigh/low bet: {displayHighLowBet}\nColor bet: {displayColorBet}\nParity bet: {displayParityBet}")
		embed.set_field_at(1, name="Outcome:",
							value=f"{msg.content}Number: {emojiNum}\nHigh/low: {highLowResult}\nColor: {colorResult}\nParity: {parityResult}")
		embed.add_field(name="-----------------------------------------------------------------",
						value=f"{winnings}\n{result}\n**Credits:** {balance}{self.coin}", inline=False)
		await msg.edit(embed=embed, file=nextcord.File('images/roulette/temproulette.png'))
		await self.bot.get_cog("Totals").addTotals(interaction, amntSpent, moneyToAdd + (moneyToAdd * (multiplier - 1)), 3)
		await self.bot.get_cog("Quests").AddQuestProgress(interaction, interaction.user, "Rltte", moneyToAdd - amntSpent)
		if len(self.previousNums) == 8:  # display only 8 previous numbers
			self.previousNums.pop()
		self.previousNums.insert(0, f"{colorResult} {str(n)}")  # insert the resulting color and number

	def getColorPos(self, color):
		if color == "red":
			return (505, 440)
		else:
			return (680, 440)

	def getHighLowPos(self, highLow):
		if highLow == "high":
			return (1030, 440)
		else:
			return (155, 440)

	def getParityPos(self, parity):
		if parity == "even":
			return (330, 440)
		else:
			return (855, 440)


	def getPos(self, num:int):
		if num == 0: 
			return (30,75)

		x = 0
		y = 0

		if num % 3 == 0:
			y = 75
		elif num % 3 == 2:
			y = 170
		elif num % 3 == 1:
			y = 265

		if num in [1, 2, 3]:			x = 110
		elif num in [4, 5, 6]:			x = 200
		elif num in [7, 8, 9]:			x = 285
		elif num in [10, 11, 12]:		x = 375
		elif num in [13, 14, 15]:		x = 460
		elif num in [16, 17, 18]:		x = 550
		elif num in [19, 20, 21]:		x = 635
		elif num in [22, 23, 24]:		x = 725
		elif num in [25, 26, 27]:		x = 810
		elif num in [28, 29, 30]:		x = 900
		elif num in [31, 32, 33]:		x = 985
		elif num in [34, 35, 36]:		x = 1075

		print(f"num is {num}")
		return (x,y)

	def getNumEmoji(self, num):
		num = int(num)
		if num == "":return ""
		elif num == 0:return ":zero:"
		elif num == 1:return ":one:"
		elif num == 2:return ":two:"
		elif num == 3:return ":three:"
		elif num == 4:return ":four:"
		elif num == 5:return ":five:"
		elif num == 6:return ":six:"
		elif num == 7:return ":seven:"
		elif num == 8:return ":eight:"
		elif num == 9:return ":nine:"
		elif num == 10:return ":keycap_ten:"
		elif num == 11:return ":one::one:"
		elif num == 12:return ":one::two:"
		elif num == 13:return ":one::three:"
		elif num == 14:return ":one::four:"
		elif num == 15:return ":one::five:"
		elif num == 16:return ":one::six:"
		elif num == 17:return ":one::seven:"
		elif num == 18:return ":one::eight:"
		elif num == 19:return ":one::nine:"
		elif num == 20:return ":two::zero:"
		elif num == 21:return ":two::one:"
		elif num == 22:return ":two::two:"
		elif num == 23:return ":two::three:"
		elif num == 24:return ":two::four:"
		elif num == 25:return ":two::five:"
		elif num == 26:return ":two::six:"
		elif num == 27:return ":two::seven:"
		elif num == 28:return ":two::eight:"
		elif num == 29:return ":two::nine:"
		elif num == 30:return ":three::zero:"
		elif num == 31:return ":three::one:"
		elif num == 32:return ":three::two:"
		elif num == 33:return ":three::three:"
		elif num == 34:return ":three::four:"
		elif num == 35:return ":three::five:"
		elif num == 36:return ":three::six:"
		else: "error"



def setup(bot):
	bot.add_cog(Roulette(bot))