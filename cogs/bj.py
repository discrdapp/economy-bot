####################################################################
# BLACKJACK! YAY!
# 
# Comment definitions:
# short-version: actual-version
# p: player
# d: dealer


import discord
from discord.ext import commands
import asyncio
from random import randrange
from random import randint
import math

from db import DB

class bj(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.cards = ["♣ A", "♣ 2", "♣ 3", "♣ 4", "♣ 5", "♣ 6", "♣ 7", "♣ 8", "♣ 9", "♣ 10", "♣ Jack", "♣ Queen", "♣ King",
					  "♦ A", "♦ 2", "♦ 3", "♦ 4", "♦ 5", "♦ 6", "♦ 7", "♦ 8", "♦ 9", "♦ 10", "♦ Jack", "♦ Queen", "♦ King",
					  "♥ A", "♥ 2", "♥ 3", "♥ 4", "♥ 5", "♥ 6", "♥ 7", "♥ 8", "♥ 9", "♥ 10", "♥ Jack", "♥ Queen", "♥ King",
					  "♠ A", "♠ 2", "♠ 3", "♠ 4", "♠ 5", "♠ 6", "♠ 7", "♠ 8", "♠ 9", "♠ 10", "♠ Jack", "♠ Queen", "♠ King"]
		self.coin = "<:coins:585233801320333313>"

	@commands.command(description="Play BlackJack!", aliases=['blackjack'])
	@commands.bot_has_guild_permissions(send_messages=True, manage_messages=True, embed_links=True, use_external_emojis=True, attach_files=True)
	@commands.cooldown(1, 5, commands.BucketType.user)	
	async def bj(self, ctx, amntBet):
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))

		amntBet = await self.bot.get_cog("Economy").GetBetAmount(ctx, amntBet)
		
		if not await self.bot.get_cog("Economy").subtractBet(ctx.author, amntBet):
			await self.bot.get_cog("Economy").notEnoughMoney(ctx)
			return
		# generate the starting cards
		dFirstHand, dFirstNum = await self.dealer_first_turn(ctx)
		
		# collect player input for player's hand
		player_hand, player_num, embed = await self.player_turn(dFirstHand, dFirstNum, ctx)
		# generate dealer's hand
		dealer_hand, dealer_num = await self.dealer_turn(dFirstHand, dFirstNum, ctx)
		
		winner = await self.compare_between(player_num, dealer_num, ctx)
		
		await self.displayWinner(ctx, winner, player_hand, player_num, dealer_hand, dealer_num, amntBet, embed.copy()) 



	async def player_turn(self, dCard, dCardNum, ctx):
		author = ctx.author
		pCARD = []
		pCardSuit = []
		pCardNum = []

		pDrawnCard = await self.take_card()

		pCARD.append(pDrawnCard)

		pDrawnCard = pDrawnCard.split()

		# assigns number value
		if pDrawnCard[1] == "Jack" or pDrawnCard[1] == "Queen" or pDrawnCard[1] == "King":
			pDrawnCard[1] = "10"
		elif pDrawnCard[1] == "A":
			pDrawnCard[1] = "11"
		pCardNum.append(int(pDrawnCard[1]))

		embed = discord.Embed(color=1768431, title=f"{self.bot.user.name} | Blackjack")
		file = discord.File("./images/bj.png", filename="image.png")
		embed.set_thumbnail(url="attachment://image.png")
		botMsg = await ctx.send(f"{author.mention}", file=file, embed=embed)
		ans = "hit"
		while (ans.lower() == "h") or (ans.lower() == "hit"):
			
			# player draws a card 
			pDrawnCard = await self.take_card()
			pCARD.append((pDrawnCard))

			# splits the number and the suit 
			pDrawnCard = pDrawnCard.split()

			# converts to number
			if pDrawnCard[1] == "Jack" or pDrawnCard[1] == "Queen" or pDrawnCard[1] == "King":
				pDrawnCard[1] = "10"
			elif pDrawnCard[1] == "A":
				pDrawnCard[1] = "11"

			# adds the card to the player's hand
			pCardNum.append(int(pDrawnCard[1]))

			pCardNum = await self.eval_ace(pCardNum)

			# used to make display for all p cards
			pTotal = ""
			for x in pCARD:
				pTotal += f"{x} "

			# used to make display for all d cards
			dTotal = ""
			for x in dCard:
				dTotal += f"{x} "

			# if game just started, it will add all the fields; if player "hit", it will update the embed for player's cards
			try:
				embed.set_field_at(0, name = f"{author.name}'s CARD:", value = f"{pTotal}\n**Score**: {sum(pCardNum)}", inline=True)
			except:
				embed.add_field(name = f"{author.name}'s CARD:", value = f"{pTotal}\n**Score**: {sum(pCardNum)}", inline=True)
				embed.add_field(name = f"{self.bot.user.name}' CARD", value = f"{dCard[0]}\n**Score**: {dCardNum[0]}\n", inline=True)
				embed.add_field(name = "_ _", value = "**Options:** hit or stay", inline=False)

			embed.set_footer(text=f"Cards in Deck: {len(self.cards)}")

			# ends game if player busted or has 21
			if (await self.is_bust(pCardNum) or await self.is_blackjack(pCardNum)):
				break
			await botMsg.edit(content=f"{author.mention}", embed=embed)

			userSettings = self.bot.get_cog("Settings").getUserSettings(author)
			emojis = userSettings[str(author.id)]["blackjack"]["emojis"]

			if emojis == "\u2705":
				def is_me_reaction(reaction, user):
					return user == author

				await botMsg.add_reaction("1⃣") 
				await botMsg.add_reaction("2⃣")
				try:
					reaction, user = await self.bot.wait_for('reaction_add', check=is_me_reaction, timeout=45)
					#return reaction, user
				except asyncio.TimeoutError:
					await botMsg.delete()
					raise Exception("timeoutError")

				if str(reaction) == "1⃣": 
					ans = "hit"
				elif str(reaction) == "2⃣": 
					ans = "stay"
				else:
					raise Exception

				await botMsg.clear_reactions()

			else:
				def is_me(m):
					return (m.author.id == author.id) and (m.content.lower() in ["hit", "stay", "h", "s", "stand"])
				try:
					# waits for user action; while loop repeated
					ans = await self.bot.wait_for('message', check=is_me, timeout=45)
					ans = ans.content
				except asyncio.TimeoutError:
					await botMsg.delete()
					raise Exception("timeoutError")

		return pCARD, pCardNum, embed


	async def take_card(self):
		# get arbitrary card from 2 to 11.
		drawnCard = self.cards.pop(randint(0, len(self.cards) - 1))

		# if all 52 cards have been used, reset the deck
		if len(self.cards) == 0:
			self.cards = ["♣ A", "♣ 2", "♣ 3", "♣ 4", "♣ 5", "♣ 6", "♣ 7", "♣ 8", "♣ 9", "♣ 10", "♣ Jack", "♣ Queen", "♣ King",
						  "♦ A", "♦ 2", "♦ 3", "♦ 4", "♦ 5", "♦ 6", "♦ 7", "♦ 8", "♦ 9", "♦ 10", "♦ Jack", "♦ Queen", "♦ King",
						  "♥ A", "♥ 2", "♥ 3", "♥ 4", "♥ 5", "♥ 6", "♥ 7", "♥ 8", "♥ 9", "♥ 10", "♥ Jack", "♥ Queen", "♥ King",
						  "♠ A", "♠ 2", "♠ 3", "♠ 4", "♠ 5", "♠ 6", "♠ 7", "♠ 8", "♠ 9", "♠ 10", "♠ Jack", "♠ Queen", "♠ King"]
		return drawnCard


	async def eval_ace(self, cardNum):
		# Determine Ace = 1 or 11, relying on total cardNum. 
		total = sum(cardNum)
		for ace in cardNum:
			if ace == 11 and total > 21:
				# at position, where Ace == 11, replace by Ace == 1.
				position_ace = cardNum.index(11)
				cardNum[position_ace] = 1
		return cardNum


	async def is_bust(self, cardNum):
		# Condition True: if the cardNum of player (or dealer) > 21.
		total = sum(cardNum)
		if total > 21:
			return True
		return None


	async def is_blackjack(self, cardNum):
		# Condition True: if the cardNum of player (or dealer) == 21.
		total = sum(cardNum)
		if total == 21:
			return True
		return None

	async def dealer_first_turn(self, ctx):
		dCARD = []
		dCardNum = []

		dDrawnCard = await self.take_card()
		dCARD.append(dDrawnCard)

		dDrawnCard = dDrawnCard.split()

		if dDrawnCard[1] == "Jack" or dDrawnCard[1] == "Queen" or dDrawnCard[1] == "King":
			dDrawnCard[1] = "10"
		elif dDrawnCard[1] == "A":
			dDrawnCard[1] = "11"

		dCardNum.append(int(dDrawnCard[1]))

		dCardNum = await self.eval_ace(dCardNum)
		
		return dCARD, dCardNum

	async def dealer_turn(self, dCARD, dCardNum, ctx):
		# d will keep drawing until card values sum > 16
		while sum(dCardNum) <= 16:
			# grabs a card
			dDrawnCard = await self.take_card()
			# adds it to his hand
			dCARD.append(dDrawnCard)

			# splits suit and number
			dDrawnCard = dDrawnCard.split()

			if dDrawnCard[1] == "Jack" or dDrawnCard[1] == "Queen" or dDrawnCard[1] == "King":
				dDrawnCard[1] = "10"
			elif dDrawnCard[1] == "A":
				dDrawnCard[1] = "11"

			dCardNum.append(int(dDrawnCard[1]))

			dCardNum = await self.eval_ace(dCardNum)
		return dCARD, dCardNum


	async def compare_between(self, player_hand, dealer_hand, ctx):
		total_player = sum(player_hand)
		total_dealer = sum(dealer_hand)
		player_bust = await self.is_bust(player_hand)
		dealer_bust = await self.is_bust(dealer_hand)
		player_blackjack = await self.is_blackjack(player_hand)
		dearler_blackjack = await self.is_blackjack(dealer_hand)

		# when p bust.
		if player_bust:
			return -1
		# when d bust
		elif dealer_bust:
			return 1
		# when both 21
		elif player_blackjack and dearler_blackjack:
			return 0
		# when p 21
		elif player_blackjack:
			return 1
		# when d 21
		elif dearler_blackjack:
			return -1
		# when total CARD of player (dealer) < 21.
		elif total_player < 21 and total_dealer < 21:
			if total_player > total_dealer:
				return 1
			elif total_dealer > total_player:
				return -1
			else:
				return 0

	async def displayWinner(self, ctx, winner, player_hand, player_num, dealer_hand, dealer_num, amntBet, embed):
		pTotal = ""
		for x in player_hand:
			pTotal += f"{x} "

		dTotal = ""
		for x in dealer_hand:
			dTotal += f"{x} "


		#self.embed.add_field(name = f"{author.name}'s' CARD:", value = f"{pTotal}\n**Score**: {sum(player_num)}", inline=True)

		coin = "<:coins:585233801320333313>"

		embed.set_field_at(1, name = f"{self.bot.user.name}' CARD", value = f"{dTotal}\n**Score**: {sum(dealer_num)}", inline=True)
		embed.color = discord.Color(0xff2020)
		result = ""


		# MONEY WINNINGS EXPLAINED:
		# If you win, you get 2x your money
		# (amntBet * 2)
		# 
		# But profit is only how much you won subtracted with how much you bet
		# Meaning profit = amntBet
		# 
		# 
		#########################

		multiplier = self.bot.get_cog("Economy").getMultiplier(ctx.author)

		file = None
		if winner == 1:
			moneyToAdd = amntBet * 2 
			profitInt = moneyToAdd - amntBet
			result = "YOU WON"
			profit = f"**{profitInt}** (+**{int(profitInt * (multiplier - 1))}**)"
			
			embed.color = discord.Color(0x23f518)
			if player_num != 21:
				file = discord.File("./images/bjwon.png", filename="image.png")
			else:
				file = discord.File("./images/21.png", filename="image.png")

		elif winner == -1:
			moneyToAdd = 0 # nothing to add since loss
			profitInt = -amntBet # profit = amntWon - amntBet; amntWon = 0 in this case
			result = "YOU LOST"
			profit = f"**{profitInt}**"
			file = discord.File("./images/bjlost.png", filename="image.png")

		
		elif winner == 0:
			moneyToAdd = amntBet # add back their bet they placed since it was pushed (tied)
			profitInt = 0 # they get refunded their money (so they don't make or lose money)
			result = "PUSHED"
			profit = f"**{profitInt}**"
			file = discord.File("./images/bjpushed.png", filename="image.png")
		
		if file:
			embed.set_thumbnail(url="attachment://image.png")

		giveZeroIfNeg = max(0, profitInt) # will give 0 if profit is negative. 
																				# we don't want it subtracting anything, only adding
		await self.bot.get_cog("Economy").addWinnings(ctx.author.id, moneyToAdd + (giveZeroIfNeg * (multiplier - 1)))
		balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
		embed.set_field_at(2, name = f"**--- {result} ---**", value = "_ _", inline=False)
		embed.add_field(name="Profit", value=f"{profit}{coin}", inline=True)
		embed.add_field(name="Credits", value=f"**{balance}**{coin}", inline=True)

		priorBal = balance - profitInt + (giveZeroIfNeg * (multiplier - 1))
		embed = await DB.calculateXP(self, ctx, priorBal, amntBet, embed)

		await ctx.send(content=f"{ctx.author.mention}", file=file, embed=embed)

		await self.bot.get_cog("Totals").addTotals(ctx, amntBet, moneyToAdd, 1)	

		await self.bot.get_cog("Quests").AddQuestProgress(ctx, ctx.author, "BJ", profitInt)

def setup(bot):
	bot.add_cog(bj(bot))