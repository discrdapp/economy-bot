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

class Roulette(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.previousNums = []
		self.coin = "<:coins:585233801320333313>"


	async def sendError(self, interaction:Interaction):
		await interaction.response.send_message("Unknown betting choices...\n" +
					   "Proper use: `.roulette <choice> <bet>`\n" +
					   "Advaced use: `.roulette <choice1> <bet1> <choice2> <bet2> <choice3> <bet3> <choice4> <bet4>`\n" + 
					   "Possible choices:\n`red`, `black`, `green`\n`odd`, `even`\n`high`, `low`\nNumber `1 - 36`\n\n" + 
					   "**Example:** .roulette red 500")



	@nextcord.slash_command(description="Play Roulette!")
	@commands.bot_has_guild_permissions(send_messages=True, embed_links=True, attach_files=True, add_reactions=True, use_external_emojis=True, manage_messages=True, read_message_history=True)
	@commands.cooldown(1, 1, commands.BucketType.user)
	async def roulette(self, interaction:Interaction, choice1=None, bet1=None, choice2=None, bet2=None, choice3=None, bet3=None, choice4=None, bet4=None):
		if not await self.bot.get_cog("Economy").accCheck(interaction.user):
			await self.bot.get_cog("Economy").start(interaction, interaction.user)

		msg = interaction.message
		channel = msg.channel
		author = msg.author
		mention = author.mention

		numberBet = ""
		rangeBet = ""
		colorBet = ""
		parityBet = ""
		amntNumberBet = 0
		amntRangeBet = 0
		amntColorBet = 0
		amntParityBet = 0
		refund = 0
		displayNumberBet = ""
		displayRangeBet = ""
		displayColorBet = ""
		displayParityBet = ""
		moneyToAdd = 0
		amntLost = 0
		end = 0
		result = ""


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


		if choice1:
			if not bet1:
				await self.sendError(interaction)
				return
			totalBet = 0
			for choice, bet in zip([choice1, choice2, choice3, choice4], [bet1, bet2, bet3, bet4]):
				if choice == None or bet == None:
					break
				if choice.isdigit() and not bet.isdigit():
					bffr = bet
					bet = choice
					choice = bffr
				choice = choice.lower()
				bet = await self.bot.get_cog("Economy").GetBetAmount(interaction, bet)

				if choice in ["red", "black", "green"]:
					if choice == "red":
						colorBet = "❤"
					elif choice == "black":
						colorBet = "🖤"
					else:
						colorBet = "💚"
					displayColorBet = f"{colorBet}  {bet}{self.coin}"
					amntColorBet = bet
				elif choice in ["odd", "even"]:
					if choice == "odd":
						parityBet = "1⃣"
					else:
						parityBet = "2⃣"
					displayParityBet = f"{parityBet}  {bet}{self.coin}"
					amntParityBet = bet
				elif choice in ["high", "low", "up", "down", "higher", "lower", "upper"]:
					if choice in ["high", "up", "higher", "upper"]:
						rangeBet = "⬆"
					else:
						rangeBet = "⬇"
					displayRangeBet = f"{rangeBet}  {bet}{self.coin}"
					amntRangeBet = bet
				elif choice.isdigit():
					if int(choice) < 0 or int(choice) > 36:
						await interaction.response.send_message("Proper automatic number betting format:\n`.roulette <number> <bet>`\nExample: .roulette 35 500")
						return
					emojiNum = await self.getNumEmoji(interaction, int(choice))
					numberBet = int(choice)
					displayNumberBet = f"{emojiNum}  {bet}{self.coin}"
					amntNumberBet = bet
				else:
					await self.sendError(interaction)
					return

				totalBet += bet

			if not await self.bot.get_cog("Economy").subtractBet(interaction.user, totalBet):
				await interaction.response.send_message("You do not have enough money for that... Cancelling roulette game...")
				return






		emojiNum = await self.getNumEmoji(interaction, numberBet)
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Roulette")
		embed.add_field(name = "Welcome to roulette, choose an option to bet on or choose start", value = "_ _", inline=True)
		# embed.add_field(name = "Current picks:", value = f"Number bet: \nHigh/low bet: \nColor bet: \nParity bet: ", inline=True)
		embed.add_field(name = "Current picks:", value = f"Number bet: {displayNumberBet}\nHigh/low bet: {displayRangeBet}\nColor bet: {displayColorBet}\nParity bet: {displayParityBet}", inline=True)
		embed.add_field(name = "Previous Numbers:", value = f"{nums}_ _", inline=True)
		#embed.add_field(name = "", value = "", inline=False)
		msg = await interaction.response.send_message(file=nextcord.File('images/roulette.png'), embed=embed)

		#await interaction.response.send_message(f"```Welcome to roulette, choose an option to bet on or choose start```\n\tCurrent picks:\n\t\t\tNumber bet: {str(numberBet)}\n\t\t\tHigh/low bet: {rangeBet}\n\t\t\tColor bet: {colorBet}\n\t\t\tParity bet: {parityBet}\n_ _")

		embedSelection = nextcord.Embed(color=1768431)

		while True:
			await self.addReactions(msg)

			def is_me(m):
				return m.author.id == author.id

			def is_me_reaction(reaction, user):
				return user == author

			reaction, user = await self.getReactionAndUser(interaction, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)

			await msg.clear_reactions()
			if str(reaction) == "🔢":
				embedSelection.clear_fields()
				embedSelection.add_field(name = f"{self.bot.user.name} | Roulette", value = f"Insert the number you'd like to bet on (0 - 36) and the amount of {self.coin} you're betting: \n*ex: typing 30 50\nwill bet on number 30 with 50{self.coin}*")
				await msg.edit(embed=embedSelection)
				try:
					numberBetMsg = await self.bot.wait_for('message', check=is_me, timeout=30)
				except asyncio.TimeoutError:
					embedError = await self.onTimeout(interaction, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
					await msg.edit(embed=embedError)
					await msg.clear_reactions()
					raise Exception("timeoutError")
				else:
					numberBets = numberBetMsg.content.split()
					try:
						numberBet = int(numberBets[0])
						amntNumberBet = int(numberBets[1])
					except:
						await interaction.response.send_message("ERROR: Did not provide number.")
						embedError = await self.onTimeout(interaction, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
						await msg.edit(embed=embedError)
						await msg.clear_reactions()
						return
					if await self.bot.get_cog("Economy").subtractBet(interaction.user, amntNumberBet):
						await numberBetMsg.delete()
						emojiNum = await self.getNumEmoji(interaction, numberBet)
						displayNumberBet = f"{emojiNum}  {amntNumberBet}{self.coin}"
						if not(isinstance(numberBet, int)) or not(numberBet >= 0) or not(numberBet <= 36):
							embedSelection.clear_fields()
							embedSelection.add_field(name = f"{self.bot.user.name} | Roulette", value ="Incorrect number.")
							await msg.edit(embed=embedSelection)
							numberBet = ""
							amntNumberBet = 0
					else:
						await interaction.response.send_message("You do not have enough credits to bet that amount")
						amntNumberBet = 0

			if str(reaction) == "🔃":
				embedSelection.clear_fields()
				embedSelection.add_field(name = f"{self.bot.user.name} | Roulette", value ="Which would you like to bet on: high or low?")
				await msg.edit(embed=embedSelection)
				await self.addRangeReactions(msg)
				reaction, user = await self.getReactionAndUser(interaction, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)

				if str(reaction) != "↩":
					await msg.clear_reactions()
					embedSelection.clear_fields()
					embedSelection.add_field(name = f"{self.bot.user.name} | Roulette", value = f"Insert how much you'd like to bet on {reaction}: ")
					await msg.edit(embed=embedSelection)
					try:
						amntRangeBetMsg = await self.bot.wait_for('message', check=is_me, timeout=30)
					except asyncio.TimeoutError:
						embedError = await self.onTimeout(interaction, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
						await msg.edit(embed=embedError)
						await msg.clear_reactions()
						raise Exception("timeoutError")
					else:
						try:
							amntRangeBet = int(amntRangeBetMsg.content)
						except:
							await interaction.response.send_message("ERROR: Did not provide number.")
							embedError = await self.onTimeout(interaction, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
							await msg.edit(embed=embedError)
							await msg.clear_reactions()
							return
						if await self.bot.get_cog("Economy").subtractBet(interaction.user, amntRangeBet):
							await amntRangeBetMsg.delete()
							rangeBet = reaction
							displayRangeBet = f"{reaction}  {amntRangeBet}{self.coin}"
						else:
							await interaction.response.send_message("You do not have enough credits to bet that amount")
							amntRangeBet = 0
				else:
					rangeBet = ""
					await msg.clear_reactions()
			

			elif str(reaction) == "🏳️‍🌈":
				embedSelection.clear_fields()
				embedSelection.add_field(name = f"{self.bot.user.name} | Roulette", value ="Which would you like to bet on: black, red, or green?")
				await msg.edit(embed=embedSelection)
				await self.addColorReactions(msg)

				reaction, user = await self.getReactionAndUser(interaction, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)

				if str(reaction) != "↩":
					await msg.clear_reactions()
					embedSelection.clear_fields()
					embedSelection.add_field(name = f"{self.bot.user.name} | Roulette", value = f"Insert how much you'd like to bet on {reaction}: ")
					await msg.edit(embed=embedSelection)
					try:
						amntColorBetMsg = await self.bot.wait_for('message', check=is_me, timeout=30)
					except asyncio.TimeoutError:
						embedError = await self.onTimeout(interaction, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
						await msg.edit(embed=embedError)
						await msg.clear_reactions()
						raise Exception("timeoutError")
					else:
						try:
							amntColorBet = int(amntColorBetMsg.content)
						except:
							await interaction.response.send_message("ERROR: Did not provide number.")
							embedError = await self.onTimeout(interaction, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
							await msg.edit(embed=embedError)
							await msg.clear_reactions()
							return
						if await self.bot.get_cog("Economy").subtractBet(interaction.user, amntColorBet):
							await amntColorBetMsg.delete()
							colorBet = reaction
							displayColorBet = f"{reaction}  {amntColorBet}{self.coin}"
						else:
							await interaction.response.send_message("You do not have enough credits to bet that amount")
							amntColorBet = 0
				else:
					colorBet = ""
					await msg.clear_reactions()
			

			elif str(reaction) == "➗":
				embedSelection.clear_fields()
				embedSelection.add_field(name = f"{self.bot.user.name} | Roulette", value ="Which would you like to bet on odd or even?")
				await msg.edit(embed=embedSelection)
				await self.addParityReactions(interaction, msg)
				
				reaction, user = await self.getReactionAndUser(interaction, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)

				if str(reaction) != "↩":
					await msg.clear_reactions()
					embedSelection.clear_fields()
					embedSelection.add_field(name = f"{self.bot.user.name} | Roulette", value = f"Insert how much you'd like to bet on {reaction}: ")
					await msg.edit(embed=embedSelection)
					try:
						amntParityBetMsg = await self.bot.wait_for('message', check=is_me, timeout=30)
					except asyncio.TimeoutError:
						embedError = await self.onTimeout(interaction, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
						await msg.edit(embed=embedError)
						await msg.clear_reactions()
						raise Exception("timeoutError")
					else:
						try:
							amntParityBet = int(amntParityBetMsg.content)
						except:
							await interaction.response.send_message("ERROR: Did not provide number.")
							embedError = await self.onTimeout(interaction, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
							await msg.edit(embed=embedError)
							await msg.clear_reactions()
							return
						if await self.bot.get_cog("Economy").subtractBet(interaction.user, amntParityBet):
							await amntParityBetMsg.delete()
							parityBet = reaction
							displayParityBet = f"{reaction}  {amntParityBet}{self.coin}"
						else:
							await interaction.response.send_message("You do not have enough credits to bet that amount")
							amntParityBet = 0
				else:
					parityBet = ""
					await msg.clear_reactions()
			

			elif str(reaction) == "🏁":
#					if ready == 1:
				n = random.randrange(0, 37)
				#n = 0

				if n >= 18: rangeResult = "⬆"
				else: rangeResult = "⬇"

				if n == 0: colorResult = "💚" #green
				elif n == 1 or n == 3 or n == 5 or n == 7 or n == 9 or n == 12 or n == 14 or n == 16 or n == 18 or n == 19 or n == 21 or n == 23 or n == 25 or n == 27 or n == 30 or n == 32 or n == 34 or n == 36:
					colorResult = "❤" # red
				else: colorResult = "🖤" #black

				if n % 2 == 0: parityResult = "2⃣"
				else: parityResult = "1⃣"

				emojiNum = await self.getNumEmoji(interaction, n)
				winnings = ""

				if numberBet == n:
					winnings += "\nYou guessed the number! You won 35x your bet!"
					await self.bot.get_cog("Economy").addWinnings(interaction.user.id, amntNumberBet*35)
					moneyToAdd += amntNumberBet*35

				if str(rangeBet) == rangeResult:
					winnings += "\nYou guessed the range! You won 2x your bet!"
					await self.bot.get_cog("Economy").addWinnings(interaction.user.id, amntRangeBet*2)
					moneyToAdd += amntRangeBet*2

				if str(colorBet) == colorResult and str(colorBet) != "💚":
					winnings += "\nYou guessed the color! You won 2x your bet!"
					await self.bot.get_cog("Economy").addWinnings(interaction.user.id, amntColorBet*2)
					moneyToAdd += amntColorBet*2
				elif str(colorBet) == colorResult:
					winnings += "\nYou guessed the color green! You won 35x your bet!"
					await self.bot.get_cog("Economy").addWinnings(interaction.user.id, amntColorBet*35)
					moneyToAdd += amntColorBet*35

				if str(parityBet) == parityResult:
					winnings += "\nYou guessed the parity! You won 2x your bet!"
					await self.bot.get_cog("Economy").addWinnings(interaction.user.id, amntParityBet*2)
					moneyToAdd += amntParityBet*2

				amntLost = amntNumberBet + amntRangeBet + amntColorBet + amntParityBet

				multiplier = self.bot.get_cog("Economy").getMultiplier(interaction.user)
				if moneyToAdd > amntLost:
					result = f"You won a grand total of {moneyToAdd} (+{moneyToAdd * (multiplier-1)}){self.coin} after betting {amntLost}{self.coin}\n**Profit:** {moneyToAdd-amntLost}{self.coin}"
				elif moneyToAdd < amntLost:
					if moneyToAdd > 0:
						result = f"You won {moneyToAdd}{self.coin} after betting {amntLost}{self.coin}"
					else:
						result = f"You lost {amntLost}{self.coin}"
				else:
					result = "You didn't lose or win anything!"

				balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
				if numberBet or rangeBet or colorBet or parityBet:
					priorBal = balance + amntLost - moneyToAdd
					minBet = priorBal * 0.05
					minBet = int(math.ceil(minBet / 10.0) * 10.0)
					if amntLost >= minBet:	
						xp = random.randint(50, 500)
						embed.set_footer(text=f"Earned {xp} XP!")
						await self.bot.get_cog("XP").addXP(interaction, xp)
					else:
						embed.set_footer(text=f"You have to bet your minimum to earn xp.")
				else:
					embed.set_footer(text="No bets were placed, no XP was earned.")
				embed.remove_field(0)
				embed.set_field_at(1, name="Outcome:", value=f"{msg.content}Number: {emojiNum}\nHigh/low: {rangeResult}\nColor: {colorResult}\nParity: {parityResult}")
				embed.add_field(name = "-----------------------------------------------------------------", 
								value = f"{winnings}\n{result}\n**Credits:** {balance}{self.coin}", inline=False)
				await msg.edit(embed=embed)
				await self.bot.get_cog("Totals").addTotals(interaction, amntLost, moneyToAdd + (moneyToAdd * (multiplier-1)), 3)
				await self.bot.get_cog("Quests").AddQuestProgress(interaction, interaction.user, "Rltte", moneyToAdd-amntLost)
				if len(self.previousNums) == 8: # display only 8 previous numbers
					self.previousNums.pop()
				self.previousNums.insert(0, f"{colorResult} {str(n)}") # insert the resulting color and number
					
#				else:
#					await msg.edit(content="Roulette game ended; no bets were placed]")
				break # end roulette while loop

			embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Roulette")
			embed.add_field(name = "Welcome to roulette, choose an option to bet on or choose start by clicking the flag", value = "_ _", inline=True)
			embed.add_field(name = "Current picks:", value = f"Number bet: {displayNumberBet}\nHigh/low bet: {displayRangeBet}\nColor bet: {displayColorBet}\nParity bet: {displayParityBet}", inline=True)
			embed.add_field(name = "Previous Numbers:", value = f"{nums}_ _", inline=True)
			await msg.edit(embed=embed)


	async def getReactionAndUser(self, interaction:Interaction, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet):
		def is_me_reaction(reaction, user):
			return user == interaction.user
		try:
			reaction, user = await self.bot.wait_for('reaction_add', check=is_me_reaction, timeout=30)
		except asyncio.TimeoutError:
			embedError = await self.onTimeout(interaction, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
			await msg.edit(embed=embedError)
			await msg.clear_reactions()
			raise Exception("timeoutError")
		return reaction, user


	async def onTimeout(self, interaction:Interaction, msg, nBet, rBet, cBet, pBet):
		embedError = nextcord.Embed(color=1768431)
		embedError.add_field(name = f"{self.bot.user.name} | Roulette", value = "Request timed out.", inline=False)
		refund = nBet + rBet + cBet + pBet
		if refund > 0:
			await self.bot.get_cog("Economy").addWinnings(interaction.user.id, refund)
			balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
			embedError.add_field(name = "-----------------------------------------------------------------",
								 value = f"A refund has been issued!\nYou received your {refund}{self.coin}\n**Credits:** {balance}{self.coin}", inline=False)
		else:
			balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
			embedError.add_field(name = "-----------------------------------------------------------------",
								 value = f"Your balance was not affected.\n**Credits:** {balance}{self.coin}", inline=False)

		return embedError

	async def addReactions(self, msg):
		await msg.add_reaction("🔢") # 2 tr
		await msg.add_reaction("🔃")
		await msg.add_reaction("🏳️‍🌈") # 3 l
		await msg.add_reaction("➗") # 4 mid
		await msg.add_reaction("🏁")

	async def addColorReactions(self, msg):
		await msg.add_reaction("🖤")
		await msg.add_reaction("❤")
		await msg.add_reaction("💚")
		await msg.add_reaction("↩")

	async def addRangeReactions(self, msg):
		await msg.add_reaction("⬆")
		await msg.add_reaction("⬇")
		await msg.add_reaction("↩")

	async def addParityReactions(self, interaction:Interaction, msg):
		await msg.add_reaction("1⃣") 
		await msg.add_reaction("2⃣")
		await msg.add_reaction("↩") 

	async def getNumEmoji(self, interaction:Interaction, num):
		if num == "":return ""
		elif num == 0:return ":zero:"
		elif num == 1:return ":one:"
		elif num == 2:return ":two:"
		elif num == 3:return ":three:"
		elif num == 4:return ":four:"
		elif num == 5:return ":five:"
		elif num == 6:return ":six:"
		elif num == 7:return ":seven"
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