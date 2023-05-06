####################################################################
# BLACKJACK! YAY!
# 
# Comment definitions:
# short-version: actual-version
# p: player
# d: dealer


import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import cooldowns
from random import randint

from db import DB

import asyncio

class Button(nextcord.ui.Button['Blackjack']):
	def __init__(self, label, style):
		super().__init__(label=label, style=style)
	
	async def callback(self, interaction: nextcord.Interaction):
		assert self.view is not None
		view: Blackjack = self.view

		if view.ownerId != interaction.user.id:
			await interaction.send("This is not your game!", ephemeral=True)
			return

		if self.label == "Hit":
			await view.hit(interaction)
		elif self.label == "Stand":
			await view.stand(interaction)
		
		await view.msg.edit(f"{interaction.user.mention}", embed=view.embed, view=view)
		await interaction.response.defer()

class Blackjack(nextcord.ui.View):
	def __init__(self, bot, id, cards, amntbet):
		super().__init__()
		self.bot = bot
		self.coin = "<:coins:585233801320333313>"

		self.cards = cards
		self.pCARD = list()
		self.pCardSuit = list()
		self.pCardNum = list()

		self.ownerId = id

		self.dealerNum = list()
		self.dealerHand = list()

		self.embed = None
		self.msg = None

		self.amntbet = amntbet

	async def Start(self, interaction):
		# generate the starting cards
		await self.dealer_first_turn(interaction)
		
		self.add_item(Button(label="Hit", style=nextcord.ButtonStyle.green))
		self.add_item(Button(label="Stand", style=nextcord.ButtonStyle.red))

		self.embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Blackjack")
		file = nextcord.File("./images/bj.png", filename="image.png")
		self.embed.set_thumbnail(url="attachment://image.png")
		
		await self.player_first_turn(interaction)

	async def player_first_turn(self, interaction):
		pDrawnCard = await self.take_card()
		self.pCARD.append(pDrawnCard)

		pDrawnCard = pDrawnCard.split()

		# assigns number value
		if pDrawnCard[1] == "Jack" or pDrawnCard[1] == "Queen" or pDrawnCard[1] == "King":
			pDrawnCard[1] = "10"
		elif pDrawnCard[1] == "A":
			pDrawnCard[1] = "11"
		self.pCardNum.append(int(pDrawnCard[1]))

		# player draws a card 
		pDrawnCard = await self.take_card()
		self.pCARD.append(pDrawnCard)

		# splits the number and the suit 
		pDrawnCard = pDrawnCard.split()

		# converts to number
		if pDrawnCard[1] == "Jack" or pDrawnCard[1] == "Queen" or pDrawnCard[1] == "King":
			pDrawnCard[1] = "10"
		elif pDrawnCard[1] == "A":
			pDrawnCard[1] = "11"

		# adds the card to the player's hand
		self.pCardNum.append(int(pDrawnCard[1]))

		# checks if player has an ace
		self.pCardNum = await self.eval_ace(self.pCardNum)

		# used to make display for all p cards
		pTotal = ""
		for x in self.pCARD:
			pTotal += f"{x} "

		# used to make display for all d cards
		dTotal = ""
		for x in self.dealerHand:
			dTotal += f"{x} "


		self.embed.add_field(name = f"{interaction.user.name}'s CARD:", value = f"{pTotal}\n**Score**: {sum(self.pCardNum)}", inline=True)
		self.embed.add_field(name = f"{self.bot.user.name}' CARD", value = f"{self.dealerHand[0]}\n**Score**: {self.dealerNum[0]}\n", inline=True)
		self.embed.add_field(name = "_ _", value = "**Options:** hit or stay", inline=False)
		self.embed.set_footer(text=f"Cards in Deck: {len(self.cards)}")

		botMsg = await interaction.send(f"{interaction.user.mention}", embed=self.embed, view=self)
		self.msg = await botMsg.fetch()


	async def hit(self, interaction):
		# player draws a card 
		pDrawnCard = await self.take_card()
		self.pCARD.append(pDrawnCard)

		# splits the number and the suit 
		pDrawnCard = pDrawnCard.split()

		# converts to number
		if pDrawnCard[1] == "Jack" or pDrawnCard[1] == "Queen" or pDrawnCard[1] == "King":
			pDrawnCard[1] = "10"
		elif pDrawnCard[1] == "A":
			pDrawnCard[1] = "11"

		# adds the card to the player's hand
		self.pCardNum.append(int(pDrawnCard[1]))
		
		# checks if player has an ace
		self.pCardNum = await self.eval_ace(self.pCardNum)

		# used to make display for all p cards
		pTotal = ""
		for x in self.pCARD:
			pTotal += f"{x} "

		# used to make display for all d cards
		dTotal = ""
		for x in self.dealerHand:
			dTotal += f"{x} "

		self.embed.set_field_at(0, 
			name = f"{interaction.user.name}'s CARD:", 
			value = f"{pTotal}\n**Score**: {sum(self.pCardNum)}", 
			inline=True)

		self.embed.set_footer(text=f"Cards in Deck: {len(self.cards)}")

		# ends game if player busted or has 21
		if (await self.is_bust(self.pCardNum) or await self.is_blackjack(self.pCardNum)):
			await self.EndGame(interaction)
			return 

	async def stand(self, interaction):
		# generate dealer's hand
		await self.dealer_turn(interaction)
		await self.EndGame(interaction)


	async def EndGame(self, interaction):
		for child in self.children:
			child.disabled = True
		self.stop()
		winner = await self.compare_between(interaction)
		await self.displayWinner(interaction, winner) 


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

	async def dealer_first_turn(self, interaction:Interaction):
		dDrawnCard = await self.take_card()
		self.dealerHand.append(dDrawnCard)

		dDrawnCard = dDrawnCard.split()

		if dDrawnCard[1] == "Jack" or dDrawnCard[1] == "Queen" or dDrawnCard[1] == "King":
			dDrawnCard[1] = "10"
		elif dDrawnCard[1] == "A":
			dDrawnCard[1] = "11"

		self.dealerNum.append(int(dDrawnCard[1]))

		self.dealerNum = await self.eval_ace(self.dealerNum)
		
		

	async def dealer_turn(self, interaction):
		# d will keep drawing until card values sum > 16
		while sum(self.dealerNum) <= 16:
			# grabs a card
			dDrawnCard = await self.take_card()
			# adds it to his hand
			self.dealerHand.append(dDrawnCard)

			# splits suit and number
			dDrawnCard = dDrawnCard.split()

			if dDrawnCard[1] == "Jack" or dDrawnCard[1] == "Queen" or dDrawnCard[1] == "King":
				dDrawnCard[1] = "10"
			elif dDrawnCard[1] == "A":
				dDrawnCard[1] = "11"

			self.dealerNum.append(int(dDrawnCard[1]))

			self.dealerNum = await self.eval_ace(self.dealerNum)


	async def compare_between(self, interaction):
		total_player = sum(self.pCardNum)
		total_dealer = sum(self.dealerNum)
		player_bust = await self.is_bust(self.pCardNum)
		dealer_bust = await self.is_bust(self.dealerNum)
		player_blackjack = await self.is_blackjack(self.pCardNum)
		dearler_blackjack = await self.is_blackjack(self.dealerNum)

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

	async def displayWinner(self, interaction:Interaction, winner):
		pTotal = ""
		for x in self.pCARD:
			pTotal += f"{x} "

		dTotal = ""
		for x in self.dealerHand:
			dTotal += f"{x} "


		#self.embed.add_field(name = f"{author.name}'s' CARD:", value = f"{pTotal}\n**Score**: {sum(player_num)}", inline=True)

		self.embed.set_field_at(1, name = f"{self.bot.user.name}' CARD", value = f"{dTotal}\n**Score**: {sum(self.dealerNum)}", inline=True)
		self.embed.color = nextcord.Color(0xff2020)
		result = ""


		# MONEY WINNINGS EXPLAINED:
		# If you win, you get 2x your money
		# (amntbet * 2)
		# 
		# But profit is only how much you won subtracted with how much you bet
		# Meaning profit = amntbet
		# 
		# 
		#########################

		multiplier = self.bot.get_cog("Multipliers").getMultiplier(interaction.user)

		file = None
		if winner == 1:
			moneyToAdd = self.amntbet * 2 
			profitInt = moneyToAdd - self.amntbet
			result = "YOU WON"
			profit = f"**{profitInt:,}** (+**{int(profitInt * (multiplier - 1))}**)"
			
			self.embed.color = nextcord.Color(0x23f518)
			if sum(self.pCardNum) == 21:
				file = nextcord.File("./images/21.png", filename="image.png")
			else:
				file = nextcord.File("./images/bjwon.png", filename="image.png")

		elif winner == -1:
			moneyToAdd = 0 # nothing to add since loss
			profitInt = -self.amntbet # profit = amntWon - amntbet; amntWon = 0 in this case
			result = "YOU LOST"
			profit = f"**{profitInt:,}**"
			file = nextcord.File("./images/bjlost.png", filename="image.png")

		
		elif winner == 0:
			moneyToAdd = self.amntbet # add back their bet they placed since it was pushed (tied)
			profitInt = 0 # they get refunded their money (so they don't make or lose money)
			result = "PUSHED"
			profit = f"**{profitInt:,}**"
			file = nextcord.File("./images/bjpushed.png", filename="image.png")
		
		if file:
			self.embed.set_thumbnail(url="attachment://image.png")

		if moneyToAdd > 0:
			await self.bot.get_cog("Economy").addWinnings(interaction.user.id, moneyToAdd + (moneyToAdd * (multiplier - 1)))
		self.embed.set_field_at(2, name = f"**--- {result} ---**", value = "_ _", inline=False)

		self.embed = await DB.addProfitAndBalFields(self, interaction, profit, self.embed)

		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		self.embed = await DB.calculateXP(self, interaction, balance - profitInt, self.amntbet, self.embed)

		# await interaction.send(content=f"{interaction.user.mention}", file=file, embed=self.embed)

		await self.bot.get_cog("Totals").addTotals(interaction, self.amntbet, moneyToAdd, 1)	
		await self.bot.get_cog("Quests").AddQuestProgress(interaction, interaction.user, "BJ", profitInt)


class bj(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.cards = ["♣ A", "♣ 2", "♣ 3", "♣ 4", "♣ 5", "♣ 6", "♣ 7", "♣ 8", "♣ 9", "♣ 10", "♣ Jack", "♣ Queen", "♣ King",
					  "♦ A", "♦ 2", "♦ 3", "♦ 4", "♦ 5", "♦ 6", "♦ 7", "♦ 8", "♦ 9", "♦ 10", "♦ Jack", "♦ Queen", "♦ King",
					  "♥ A", "♥ 2", "♥ 3", "♥ 4", "♥ 5", "♥ 6", "♥ 7", "♥ 8", "♥ 9", "♥ 10", "♥ Jack", "♥ Queen", "♥ King",
					  "♠ A", "♠ 2", "♠ 3", "♠ 4", "♠ 5", "♠ 6", "♠ 7", "♠ 8", "♠ 9", "♠ 10", "♠ Jack", "♠ Queen", "♠ King"]

	@nextcord.slash_command(description="Play BlackJack!")
	@commands.bot_has_guild_permissions(send_messages=True, manage_messages=True, embed_links=True, use_external_emojis=True, attach_files=True)
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author)	
	async def blackjack(self, interaction:Interaction, amntbet):
		print(len(self.cards))
		amntbet = await self.bot.get_cog("Economy").GetBetAmount(interaction, amntbet)
		
		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, amntbet):
			raise Exception("tooPoor")
		
		view = Blackjack(self.bot, interaction.user.id, self.cards, amntbet)
		await view.Start(interaction)


def setup(bot):
	bot.add_cog(bj(bot))