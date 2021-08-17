# economy-related stuff like betting and gambling, etc.

import discord
from discord.ext import commands
import pymysql
import asyncio
import random

import math

class Roulette(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.previousNums = [""]
		self.coin = "<:coins:585233801320333313>"


	@commands.command(description="Play Roulette!", aliases=['russianroulette', 'r', 'rr', 'roulete', 'roullette', 'roullete'], pass_context=True)
	@commands.bot_has_guild_permissions(send_messages=True, embed_links=True, attach_files=True, add_reactions=True, use_external_emojis=True, manage_messages=True, read_message_history=True)
	@commands.cooldown(1, 1, commands.BucketType.user)
	async def roulette(self, ctx):
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))

		msg = ctx.message
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

		emojiNum = await self.getNumEmoji(ctx, numberBet)
		embed = discord.Embed(color=1768431, title=f"{self.bot.user.name}' Casino | Roulette")
		embed.add_field(name = "Welcome to roulette, choose an option to bet on or choose start", value = "_ _", inline=True)
		embed.add_field(name = "Current picks:", value = f"Number bet: \nHigh/low bet: \nColor bet: \nParity bet: ", inline=True)
		embed.add_field(name = "Previous Numbers:", value = f"{nums}_ _", inline=True)
		#embed.add_field(name = "", value = "", inline=False)
		msg = await ctx.send(file=discord.File('images/roulette.png'), embed=embed)

		#await ctx.send(f"```Welcome to roulette, choose an option to bet on or choose start```\n\tCurrent picks:\n\t\t\tNumber bet: {str(numberBet)}\n\t\t\tHigh/low bet: {rangeBet}\n\t\t\tColor bet: {colorBet}\n\t\t\tParity bet: {parityBet}\n_ _")

		embedSelection = discord.Embed(color=1768431)

		while True:
			await self.addReactions(msg)

			def is_me(m):
				return m.author.id == author.id

			def is_me_reaction(reaction, user):
				return user == author

			try:
				reaction, user = await self.bot.wait_for('reaction_add', check=is_me_reaction, timeout=30)
			except:
				embedError = await self.onTimeout(ctx, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
				await msg.edit(embed=embedError)
				await msg.clear_reactions()
				raise Exception("timeoutError")
			else:
				await msg.clear_reactions()
				if str(reaction) == "🔢":
					embedSelection.clear_fields()
					embedSelection.add_field(name = f"{self.bot.user.name}' Casino | Roulette", value = f"Insert the number you'd like to bet on (0 - 36) and the amount of {self.coin} you're betting: \n*ex: typing 30 50\nwill bet on number 30 with 50{self.coin}*")
					await msg.edit(embed=embedSelection)
					try:
						numberBetMsg = await self.bot.wait_for('message', check=is_me, timeout=30)
					except asyncio.TimeoutError:
						embedError = await self.onTimeout(ctx, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
						await msg.edit(embed=embedError)
						await msg.clear_reactions()
						raise Exception("timeoutError")
					else:
						numberBets = numberBetMsg.content.split()
						try:
							numberBet = int(numberBets[0])
							amntNumberBet = int(numberBets[1])
						except:
							await ctx.send("ERROR: Did not provide number.")
							embedError = await self.onTimeout(ctx, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
							await msg.edit(embed=embedError)
							await msg.clear_reactions()
							return
						if await self.bot.get_cog("Economy").subtractBet(ctx.author, amntNumberBet):
							await numberBetMsg.delete()
							emojiNum = await self.getNumEmoji(ctx, numberBet)
							displayNumberBet = f"{emojiNum}  {amntNumberBet}{self.coin}"
							if not(isinstance(numberBet, int)) or not(numberBet >= 0) or not(numberBet <= 36):
								embedSelection.clear_fields()
								embedSelection.add_field(name = f"{self.bot.user.name}' Casino | Roulette", value ="Incorrect number.")
								await msg.edit(embed=embedSelection)
								numberBet = ""
								amntNumberBet = 0
						else:
							await ctx.send("You do not have enough credits to bet that amount")
							amntNumberBet = 0

				if str(reaction) == "🔃":
					embedSelection.clear_fields()
					embedSelection.add_field(name = f"{self.bot.user.name}' Casino | Roulette", value ="Which would you like to bet on: high or low?")
					await msg.edit(embed=embedSelection)
					await self.addRangeReactions(msg)
					try:
						reaction, user = await self.bot.wait_for('reaction_add', check=is_me_reaction, timeout=30)
					except asyncio.TimeoutError:
						embedError = await self.onTimeout(ctx, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
						await msg.edit(embed=embedError)
						await msg.clear_reactions()
						raise Exception("timeoutError")
					else:
						if str(reaction) != "↩":
							await msg.clear_reactions()
							embedSelection.clear_fields()
							embedSelection.add_field(name = f"{self.bot.user.name}' Casino | Roulette", value = f"Insert how much you'd like to bet on {reaction}: ")
							await msg.edit(embed=embedSelection)
							try:
								amntRangeBetMsg = await self.bot.wait_for('message', check=is_me, timeout=30)
							except asyncio.TimeoutError:
								embedError = await self.onTimeout(ctx, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
								await msg.edit(embed=embedError)
								await msg.clear_reactions()
								raise Exception("timeoutError")
							else:
								try:
									amntRangeBet = int(amntRangeBetMsg.content)
								except:
									await ctx.send("ERROR: Did not provide number.")
									embedError = await self.onTimeout(ctx, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
									await msg.edit(embed=embedError)
									await msg.clear_reactions()
									return
								if await self.bot.get_cog("Economy").subtractBet(ctx.author, amntRangeBet):
									await amntRangeBetMsg.delete()
									rangeBet = reaction
									displayRangeBet = f"{reaction}  {amntRangeBet}{self.coin}"
								else:
									await ctx.send("You do not have enough credits to bet that amount")
									amntRangeBet = 0
						else:
							rangeBet = ""
							await msg.clear_reactions()
				

				elif str(reaction) == "🏳️‍🌈":
					embedSelection.clear_fields()
					embedSelection.add_field(name = f"{self.bot.user.name}' Casino | Roulette", value ="Which would you like to bet on: black, red, or green?")
					await msg.edit(embed=embedSelection)
					await self.addColorReactions(msg)

					try:
						reaction, user = await self.bot.wait_for('reaction_add', check=is_me_reaction, timeout=30)
					except asyncio.TimeoutError:
						embedError = await self.onTimeout(ctx, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
						await msg.edit(embed=embedError)
						await msg.clear_reactions()
						raise Exception("timeoutError")
					else:
						if str(reaction) != "↩":
							await msg.clear_reactions()
							embedSelection.clear_fields()
							embedSelection.add_field(name = f"{self.bot.user.name}' Casino | Roulette", value = f"Insert how much you'd like to bet on {reaction}: ")
							await msg.edit(embed=embedSelection)
							try:
								amntColorBetMsg = await self.bot.wait_for('message', check=is_me, timeout=30)
							except asyncio.TimeoutError:
								embedError = await self.onTimeout(ctx, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
								await msg.edit(embed=embedError)
								await msg.clear_reactions()
								raise Exception("timeoutError")
							else:
								try:
									amntColorBet = int(amntColorBetMsg.content)
								except:
									await ctx.send("ERROR: Did not provide number.")
									embedError = await self.onTimeout(ctx, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
									await msg.edit(embed=embedError)
									await msg.clear_reactions()
									return
								if await self.bot.get_cog("Economy").subtractBet(ctx.author, amntColorBet):
									await amntColorBetMsg.delete()
									colorBet = reaction
									displayColorBet = f"{reaction}  {amntColorBet}{self.coin}"
								else:
									await ctx.send("You do not have enough credits to bet that amount")
									amntColorBet = 0
						else:
							colorBet = ""
							await msg.clear_reactions()
				

				elif str(reaction) == "➗":
					embedSelection.clear_fields()
					embedSelection.add_field(name = f"{self.bot.user.name}' Casino | Roulette", value ="Which would you like to bet on odd or even?")
					await msg.edit(embed=embedSelection)
					await self.addParityReactions(ctx, msg)
					
					try:
						reaction, user = await self.bot.wait_for('reaction_add', check=is_me_reaction, timeout=30)
					except asyncio.TimeoutError:
						embedError = await self.onTimeout(ctx, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
						await msg.edit(embed=embedError)
						await msg.clear_reactions()
						raise Exception("timeoutError")
					else:
						if str(reaction) != "↩":
							await msg.clear_reactions()
							embedSelection.clear_fields()
							embedSelection.add_field(name = f"{self.bot.user.name}' Casino | Roulette", value = f"Insert how much you'd like to bet on {reaction}: ")
							await msg.edit(embed=embedSelection)
							try:
								amntParityBetMsg = await self.bot.wait_for('message', check=is_me, timeout=30)
							except asyncio.TimeoutError:
								embedError = await self.onTimeout(ctx, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
								await msg.edit(embed=embedError)
								await msg.clear_reactions()
								raise Exception("timeoutError")
							else:
								try:
									amntParityBet = int(amntParityBetMsg.content)
								except:
									await ctx.send("ERROR: Did not provide number.")
									embedError = await self.onTimeout(ctx, msg, amntNumberBet, amntRangeBet, amntColorBet, amntParityBet)
									await msg.edit(embed=embedError)
									await msg.clear_reactions()
									return
								if await self.bot.get_cog("Economy").subtractBet(ctx.author, amntParityBet):
									await amntParityBetMsg.delete()
									parityBet = reaction
									displayParityBet = f"{reaction}  {amntParityBet}{self.coin}"
								else:
									await ctx.send("You do not have enough credits to bet that amount")
									amntParityBet = 0
						else:
							parityBet = ""
							await msg.clear_reactions()
				

				elif str(reaction) == "🏁":
#					if ready == 1:
					n = random.randrange(0, 36)
					#n = 0

					if n >= 18: rangeResult = "⬆"
					else: rangeResult = "⬇"

					if n == 0: colorResult = "💚" #green
					elif n == 1 or n == 3 or n == 5 or n == 7 or n == 9 or n == 12 or n == 14 or n == 16 or n == 18 or n == 19 or n == 21 or n == 23 or n == 25 or n == 27 or n == 30 or n == 32 or n == 34 or n == 36:
						colorResult = "❤" # red
					else: colorResult = "🖤" #black

					if n % 2 == 0: parityResult = "2⃣"
					else: parityResult = "1⃣"

					emojiNum = await self.getNumEmoji(ctx, n)
					winnings = ""

					if numberBet == n:
						winnings += "\nYou guessed the number! You won 35x your bet!"
						await self.bot.get_cog("Economy").addWinnings(ctx.author.id, amntNumberBet*35)
						moneyToAdd += amntNumberBet*35

					if str(rangeBet) == rangeResult:
						winnings += "\nYou guessed the range! You won 2x your bet!"
						await self.bot.get_cog("Economy").addWinnings(ctx.author.id, amntRangeBet*2)
						moneyToAdd += amntRangeBet*2

					if str(colorBet) == colorResult and str(colorBet) != "💚":
						winnings += "\nYou guessed the color! You won 2x your bet!"
						await self.bot.get_cog("Economy").addWinnings(ctx.author.id, amntColorBet*2)
						moneyToAdd += amntColorBet*2
					elif str(colorBet) == colorResult and str(colorBet) == "💚":
						winnings += "\nYou guessed the color green! You won 35x your bet!"
						await self.bot.get_cog("Economy").addWinnings(ctx.author.id, amntColorBet*35)
						moneyToAdd += amntColorBet*35

					if str(parityBet) == parityResult:
						winnings += "\nYou guessed the parity! You won 2x your bet!"
						await self.bot.get_cog("Economy").addWinnings(ctx.author.id, amntParityBet*2)
						moneyToAdd += amntParityBet*2

					amntLost = amntNumberBet + amntRangeBet + amntColorBet + amntParityBet

					multiplier = self.bot.get_cog("Economy").getMultiplier(ctx.author)
					if moneyToAdd > amntLost:
						result = f"You won a grand total of {moneyToAdd} (+{moneyToAdd * (multiplier-1)}){self.coin} after betting {amntLost}{self.coin}\n**Profit:** {moneyToAdd-amntLost}{self.coin}"
					elif moneyToAdd < amntLost:
						if moneyToAdd > 0:
							result = f"You won {moneyToAdd}{self.coin} after betting {amntLost}{self.coin}"
						else:
							result = f"You lost {amntLost}{self.coin}"
					else:
						result = "You didn't lose or win anything!"

					balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
					if numberBet or rangeBet or colorBet or parityBet:
						priorBal = balance + amntLost - moneyToAdd
						minBet = priorBal * 0.05
						minBet = int(math.ceil(minBet / 10.0) * 10.0)
						if amntLost >= minBet:	
							xp = random.randint(50, 500)
							embed.set_footer(text=f"Earned {xp} XP!")
							await self.bot.get_cog("XP").addXP(ctx, xp)
						else:
							embed.set_footer(text=f"You have to bet your minimum to earn xp.")
					else:
						embed.set_footer(text="No bets were placed, no XP was earned.")
					embed.remove_field(0)
					embed.set_field_at(1, name="Outcome:", value=f"{msg.content}Number bet: {emojiNum}\nHigh/low bet: {rangeResult}\nColor bet: {colorResult}\nParity bet: {parityResult}")
					embed.add_field(name = "-----------------------------------------------------------------", 
									value = f"{winnings}\n{result}\n**Credits:** {balance}{self.coin}", inline=False)
					await msg.edit(embed=embed)
					await self.bot.get_cog("Totals").addTotals(ctx, amntLost, moneyToAdd + (moneyToAdd * (multiplier-1)), 3)
					if len(self.previousNums) == 8: # display only 8 previous numbers
						self.previousNums.pop()
					self.previousNums.insert(0, f"{colorResult} {str(n)}") # insert the resulting color and number
					if self.previousNums[1] == "":
						self.previousNums.pop(1) # if there was no previous numbers
						
#				else:
#					await msg.edit(content="Roulette game ended; no bets were placed]")
					break # end roulette while loop

				embed = discord.Embed(color=1768431, title=f"{self.bot.user.name}' Casino | Roulette")
				embed.add_field(name = "Welcome to roulette, choose an option to bet on or choose start by clicking the flag", value = "_ _", inline=True)
				embed.add_field(name = "Current picks:", value = f"Number bet: {displayNumberBet}\nHigh/low bet: {displayRangeBet}\nColor bet: {displayColorBet}\nParity bet: {displayParityBet}", inline=True)
				embed.add_field(name = "Previous Numbers:", value = f"{nums}_ _", inline=True)
				await msg.edit(embed=embed)

	async def onTimeout(self, ctx, msg, nBet, rBet, cBet, pBet):
		embedError = discord.Embed(color=1768431)
		embedError.add_field(name = f"{self.bot.user.name}' Casino | Roulette", value = "Request timed out.", inline=False)
		refund = nBet + rBet + cBet + pBet
		if refund > 0:
			await self.bot.get_cog("Economy").addWinnings(ctx.author.id, refund)
			balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
			embedError.add_field(name = "-----------------------------------------------------------------",
								 value = f"A refund has been issued!\nYou received your {refund}{self.coin}\n**Credits:** {balance}{self.coin}", inline=False)
		else:
			balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
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

	async def addParityReactions(self, ctx, msg):
		await msg.add_reaction("1⃣") 
		await msg.add_reaction("2⃣")
		await msg.add_reaction("↩") 

	async def getNumEmoji(self, ctx, num):
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


	# @roulette.error
	# async def roulette_handler(self, ctx, error):
	# 	embed = discord.Embed(color=1768431, title=f"{self.bot.user.name} Help Menu")
	# 	embed.add_field(name = "`Syntax: /roulette`", value = "_ _", inline=False)
	# 	embed.add_field(name = "__Play the Casino version of Roulette__", value = "_ _", inline=False)
	# 	await ctx.send(embed=embed)
	# 	print(error)


def setup(bot):
	bot.add_cog(Roulette(bot))