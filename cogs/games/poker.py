import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

# import cooldowns
from random import randint, shuffle
import asyncio, cooldowns

from collections import Counter
from itertools import combinations

import emojis
from db import DB


class Button(nextcord.ui.Button['PokerView']):
	def __init__(self, bot, label, style):
		self.bot:commands.bot.Bot = bot
		super().__init__(label=label, style=style)

	async def callback(self, interaction: Interaction):
		assert self.view is not None
		view: PokerView = self.view

		if view.ownerId != interaction.user.id:
			await interaction.send("This is not your game!", ephemeral=True)
			return

		if self.label == "Bet":
			if not await self.bot.get_cog("Economy").subtractBet(interaction.user, view.initialBet):
				await interaction.send("You don't have enough credits for that bet", ephemeral=True)
				return
			view.amntbet += view.initialBet
			if await view.FlipCards(interaction): return
			await view.UpdateMsg(interaction)


		elif self.label == "Fold":
			await view.GameOver(interaction, folded=True)
		elif self.label == "Check":
			pass

class PokerView(nextcord.ui.View):
	def __init__(self, bot, id, cards, amntbet):
		super().__init__(timeout=120)
		self.bot:commands.bot.Bot = bot
		self.cards = cards

		self.initialBet = amntbet
		self.amntbet = self.initialBet

		self.ownerId = id

		self.pCards = list()
		self.dCards = list()

		self.embed = None
		self.msg = None

		self.cardsDealt = 0
		# for river, edit with self.riverCards[0] = card. For flop/turn, .append()
		self.riverCards = [":black_joker:", ":black_joker:", ":black_joker:"]

		self.scores = ["High Card", "Pair", "Two Pair", "Three of a Kind", "Straight", "Flush", "Full House", "Four of a Kind", "Straight Flush"]

		self.betButton = Button(self.bot, "Bet", nextcord.ButtonStyle.blurple)
		self.add_item(self.betButton)

		self.foldCheckButton = Button(self.bot, "Fold", nextcord.ButtonStyle.red)
		self.add_item(self.foldCheckButton)
	
	# async def on_timeout(self):
	# 	self.clear_items()
	# 	await self.interaction.edit_original_message(embed=None, view=self, 
	# 				       content=f"{self.interaction.user.mention}\nYou took too long to respond, staying with your current hand")
	# 	await self.stand()

	async def FlipCards(self, interaction:Interaction):
		if self.cardsDealt == 0:
			for x in range(3):
				self.riverCards[x] = self.TakeCard()
			self.cardsDealt = 3
		elif self.cardsDealt == 3:
			self.riverCards.append(self.TakeCard())
			self.cardsDealt = 4
		elif self.cardsDealt == 4:
			self.riverCards.append(self.TakeCard())
			self.cardsDealt = 5
			await self.AfterFlop(interaction)
			return True
	
	async def UpdateMsg(self, interaction: Interaction):
		self.embed.description = f"Your bet: {self.amntbet}{emojis.coin}"
		self.embed.set_field_at(0, name = f"{interaction.user.display_name}'s cards", value = f"{self.GetCardsString(self.pCards)}", inline=False)
		self.embed.set_field_at(1, name = f"_ _\nRiver Cards", value = f"{self.GetCardsString(self.riverCards)}", inline=False)
		self.embed.set_field_at(2, name = f"_ _\n{self.bot.user.name}'s cards", value = f":question: :question:", inline=False)

		await self.msg.edit(view=self, embed=self.embed)

	def TakeCard(self):
		# if all 52 cards have been used, reset the deck
		if len(self.cards) == 0:
			self.cards = ["♣ A", "♣ 2", "♣ 3", "♣ 4", "♣ 5", "♣ 6", "♣ 7", "♣ 8", "♣ 9", "♣ 10", "♣ Jack", "♣ Queen", "♣ King",
						  "♦ A", "♦ 2", "♦ 3", "♦ 4", "♦ 5", "♦ 6", "♦ 7", "♦ 8", "♦ 9", "♦ 10", "♦ Jack", "♦ Queen", "♦ King",
						  "♥ A", "♥ 2", "♥ 3", "♥ 4", "♥ 5", "♥ 6", "♥ 7", "♥ 8", "♥ 9", "♥ 10", "♥ Jack", "♥ Queen", "♥ King",
						  "♠ A", "♠ 2", "♠ 3", "♠ 4", "♠ 5", "♠ 6", "♠ 7", "♠ 8", "♠ 9", "♠ 10", "♠ Jack", "♠ Queen", "♠ King"]
			shuffle(self.cards)

		drawnCard = self.cards.pop()

		return drawnCard

	
	def GetCardsString(self, cards):
		msg = ""
		for x in cards:
			msg += f"{x} "
		return msg


	async def Start(self, interaction: Interaction):
		# self.add_item(Button(self.bot, "Bet", nextcord.ButtonStyle.green))

		self.embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Poker")
		file = nextcord.File("./images/bj.png", filename="image.png")
		self.embed.set_thumbnail(url="attachment://image.png")

		self.PlayerDrawCards()

		self.embed.description = f"Your bet: {self.amntbet}{emojis.coin}"
		self.embed.add_field(name = f"{interaction.user.display_name}'s cards", value = f"{self.GetCardsString(self.pCards)}", inline=False)
		self.embed.add_field(name = f"_ _\nRiver Cards", value = f"{self.GetCardsString(self.riverCards)}", inline=False)
		self.embed.add_field(name = f"_ _\n{self.bot.user.name}'s cards", value = f":question: :question:", inline=False)

		self.msg = await interaction.send(view=self, embed=self.embed)

	# pass in either dealer or player hand
	def GetBestHand(self, isPlayer:bool):
		def ConvertToReadableFormat(cards):
			readable = list()
			for card in cards:
				currCard = ""
				card = card.split()

				if card[1] == "10":
					currCard += "T"
				elif card[1] == "Jack":
					currCard += "J"
				elif card[1] == "Queen":
					currCard += "Q"
				elif card[1] == "King":
					currCard += "K"
				else:
					currCard += card[1]
				currCard += card[0]
				readable.append(currCard)
			return readable

		def num_of_kind(cards):
			return Counter(c[0] for c in cards)

		def count_pairs(cards):
			return sum(i > 1 for i in num_of_kind(cards).values())

		def largest_pair(cards):
			return max(num_of_kind(cards).values())

		def is_straight(cards):
			values = [c[0] for c in cards]
			index = "A23456789TJQKA"["K" in values:].index
			indices = sorted(index(v) for v in values)
			return all(x == y for x, y in enumerate(indices, indices[0]))

		def is_flush(cards):
			suit_pop = Counter(c[1] for c in cards)
			return any(s > 4 for s in suit_pop.values())

		def straight_sort(cards):
			values = [c[0] for c in cards]
			index = "A23456789TJQKA"["K" in values:].index
			return sorted(cards, key=lambda x:index(x[0]), reverse=True)

		def flush_sort(cards):
			suit_pop = Counter(c[1] for c in cards)
			return sorted(cards, key=lambda x: suit_pop[x[1]], reverse=True)

		def pair_sort(cards):
			num = num_of_kind(cards)
			return sorted(cards, key=lambda x: num[x[0]], reverse=True)

		def score_hand(cards):
			pairs = count_pairs(cards)
			largest = largest_pair(cards)
			straight = is_straight(cards)
			flush = is_flush(cards)

			cards = straight_sort(cards)
			hand_score = 0
			if flush and straight:
				hand_score, cards = 8, flush_sort(cards)
			elif largest == 4:
				hand_score, cards = 7, pair_sort(cards)
			elif pairs == 2 and largest == 3:
				hand_score, cards = 6, pair_sort(cards)
			elif flush:
				hand_score, cards = 5, flush_sort(cards)
			elif straight:
				hand_score = 4
			elif largest == 3:
				hand_score, cards = 3, pair_sort(cards)
			else:
				hand_score, cards = pairs, pair_sort(cards)
			return hand_score

		if isPlayer:
			tempCards = self.pCards + self.riverCards
		else:
			tempCards = self.dCards + self.riverCards

		cards = ConvertToReadableFormat(tempCards)
		print(cards)
		cards = max(list(combinations(cards, 5)), key=score_hand)
		score = score_hand(cards)

		return score


	async def AfterFlop(self, interaction:Interaction):
		self.OpponentDrawCards()

		playerResult = self.GetBestHand(True)
		dealerResult = self.GetBestHand(False)

		if playerResult > dealerResult:
			await self.GameOver(interaction, playerResult, dealerResult, winner=True)
		elif playerResult < dealerResult:
			await self.GameOver(interaction, playerResult, dealerResult, winner=False)
		else:
			print(f"same scores? player has {playerResult} dealer is {dealerResult}")


	async def GameOver(self, interaction:Interaction, pResult, dResult, winner:bool=False, folded:bool=False):
		if folded:
			moneyToAdd = 0
		else: 
			if winner:
				moneyToAdd = self.amntbet * 2
				msg = f"Player wins with {self.scores[pResult]}. Opponent had {self.scores[dResult]}"
			else:
				moneyToAdd = 0
				msg = f"Player lost. Opponent has {self.scores[dResult]} while player has {self.scores[pResult]}"
		
			self.embed.description = msg	
		
		profitInt = moneyToAdd - self.amntbet

		gameID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, moneyToAdd, giveMultiplier=True, activityName="Poker", amntBet=self.amntbet)

		self.embed = await DB.addProfitAndBalFields(self, interaction, profitInt, self.embed)

		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		self.embed = await DB.calculateXP(self, interaction, balance - profitInt, self.amntbet, self.embed, gameID)

		# if winner == 999:
		# await self.interaction.send(content=f"{user.mention}", file=file, embed=self.embed)

		# await interaction.send(content=f"{interaction.user.mention}", file=file, embed=self.embed)

		await self.msg.edit(view=None, embed=self.embed)

	def PlayerDrawCards(self):
		for _ in range(2):
			card = self.TakeCard()
			self.pCards.append(card)
	
	def OpponentDrawCards(self):
		for _ in range(2):
			print("adding card??")
			card = self.TakeCard()
			self.dCards.append(card)
		print(f"11{self.dCards}")


class Poker(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.cards = ["♣ A", "♣ 2", "♣ 3", "♣ 4", "♣ 5", "♣ 6", "♣ 7", "♣ 8", "♣ 9", "♣ 10", "♣ Jack", "♣ Queen", "♣ King",
					  "♦ A", "♦ 2", "♦ 3", "♦ 4", "♦ 5", "♦ 6", "♦ 7", "♦ 8", "♦ 9", "♦ 10", "♦ Jack", "♦ Queen", "♦ King",
					  "♥ A", "♥ 2", "♥ 3", "♥ 4", "♥ 5", "♥ 6", "♥ 7", "♥ 8", "♥ 9", "♥ 10", "♥ Jack", "♥ Queen", "♥ King",
					  "♠ A", "♠ 2", "♠ 3", "♠ 4", "♠ 5", "♠ 6", "♠ 7", "♠ 8", "♠ 9", "♠ 10", "♠ Jack", "♠ Queen", "♠ King"]
		shuffle(self.cards)

	@nextcord.slash_command(description="Play BlackJack!")
	@commands.bot_has_guild_permissions(send_messages=True, manage_messages=True, embed_links=True, use_external_emojis=True, attach_files=True)
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='blackjack')
	async def poker(self, interaction:Interaction, startingbet):
		startingbet = await self.bot.get_cog("Economy").GetBetAmount(interaction, startingbet)

		if startingbet < 100:
			raise Exception("minBet 100")
		
		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, startingbet):
			raise Exception("tooPoor")
		
		view = PokerView(self.bot, interaction.user.id, self.cards, startingbet)
		await view.Start(interaction)


def setup(bot):
	bot.add_cog(Poker(bot))