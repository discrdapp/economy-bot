import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

# import cooldowns
from random import shuffle
import asyncio, cooldowns

from collections import Counter
from itertools import combinations

import emojis
from db import DB
from cogs.util import GetMaxBet


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

		elif self.label == "Check":
			if await view.FlipCards(interaction): return

		elif self.label == "Fold":
			await view.GameOver(interaction, "Folded.", folded=True)
			return
		await view.UpdateMsg(interaction)
		try:
			await interaction.response.defer()
		except:
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

		# self.foldCheckButton = Button(self.bot, "Check", nextcord.ButtonStyle.red)

	async def FlipCards(self, interaction:Interaction):
		# self.riverCards = ["♦ 9", "♦ Q", "♥ 8", "♠ 3", "♥ 2"]
		# await self.AfterFlop(interaction)
		# self.cardsDealt = 5
		# return True
		if self.cardsDealt == 0:
			for x in range(3):
				self.riverCards[x] = self.TakeCard()
			self.cardsDealt = 3
			self.foldCheckButton.label = "Check"
			self.foldCheckButton.style = nextcord.ButtonStyle.green
			self.clear_items()
			self.add_item(self.betButton)
			self.add_item(self.foldCheckButton)
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
		self.embed.set_footer(text=f"Cards in Deck: {len(self.cards)}")
		await self.msg.edit(view=self, embed=self.embed)

	def TakeCard(self):
		# if all 52 cards have been used, reset the deck
		if len(self.cards) == 0:
			self.cards = ["♣ A", "♣ 2", "♣ 3", "♣ 4", "♣ 5", "♣ 6", "♣ 7", "♣ 8", "♣ 9", "♣ T", "♣ J", "♣ Q", "♣ K",
						  "♦ A", "♦ 2", "♦ 3", "♦ 4", "♦ 5", "♦ 6", "♦ 7", "♦ 8", "♦ 9", "♦ T", "♦ J", "♦ Q", "♦ K",
						  "♥ A", "♥ 2", "♥ 3", "♥ 4", "♥ 5", "♥ 6", "♥ 7", "♥ 8", "♥ 9", "♥ T", "♥ J", "♥ Q", "♥ K",
						  "♠ A", "♠ 2", "♠ 3", "♠ 4", "♠ 5", "♠ 6", "♠ 7", "♠ 8", "♠ 9", "♠ T", "♠ J", "♠ Q", "♠ K"]
			shuffle(self.cards)

		drawnCard = self.cards.pop()

		return drawnCard

	
	def GetCardsString(self, cards):
		msg = ""
		for x in cards:
			msg += f"{x} | "
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
		self.embed.set_footer(text=f"Cards in Deck: {len(self.cards)}")
		
		# user is all in, so cannot place initial bet after anne. 
		if await self.bot.get_cog("Economy").getBalance(interaction.user) < self.amntbet:
			# start game, but flip all cards and end it right after
			await self.FlipCards(interaction)
			await asyncio.sleep(0.6)
			await self.FlipCards(interaction)
			await asyncio.sleep(0.6)
			await self.FlipCards(interaction)
		else:
			self.msg = await interaction.send(view=self, embed=self.embed)

	# pass in either dealer or player hand
	def GetBestHand(self, isPlayer:bool):
		def num_of_kind(cards):
			return Counter(c[-1] for c in cards)

		def count_pairs(cards):
			return sum(i > 1 for i in num_of_kind(cards).values())

		def largest_pair(cards):
			return max(num_of_kind(cards).values())

		def is_straight(cards):
			cards = straight_sort(cards)
			values = [c[-1] for c in cards]
			index = "A23456789TJQKA"["K" in values:].index
			indices = sorted(index(v) for v in values)
			return all(x == y for x, y in enumerate(indices, indices[0]))

		def is_flush(cards):
			suit_pop = Counter(c[0] for c in cards)
			return any(s > 4 for s in suit_pop.values())

		def straight_sort(cards):
			values = [c[-1] for c in cards]
			index = "A23456789TJQKA"["K" in values:].index
			return sorted(cards, key=lambda x:index(x[-1]), reverse=True)

		def flush_sort(cards):
			suit_pop = Counter(c[0] for c in cards)
			return sorted(cards, key=lambda x: suit_pop[x[0]], reverse=True)

		def pair_sort(cards):
			num = num_of_kind(cards)
			return sorted(cards, key=lambda x: num[x[-1]], reverse=True)
		
		def card_vals(cards):
			return [c[-1] for c in cards]

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

			# return cards, hand_score
			return hand_score, card_vals(cards), cards

		tempCards = self.riverCards.copy()
		if isPlayer:
			tempCards += self.pCards.copy()
		else:
			tempCards += self.dCards.copy()

		cards = max(list(combinations(tempCards, 5)), key=score_hand)
		score, _, cards = score_hand(cards)

		return cards, score


	async def AfterFlop(self, interaction:Interaction):
		self.OpponentDrawCards()

		pSorted, playerResult = self.GetBestHand(True)
		dSorted, dealerResult = self.GetBestHand(False)

		index = "23456789TJQKA"

		pMsgAddon = ""
		dMsgAddon = ""
		if self.scores[playerResult] == "High Card" or self.scores[playerResult] == "Pair":
			pMsgAddon = f" of {pSorted[0][-1]}"
		if self.scores[dealerResult] == "High Card" or self.scores[dealerResult] == "Pair":
			dMsgAddon = f" of {dSorted[0][-1]}"

		if playerResult > dealerResult:
			msg = f"**Player wins!**\nPlayer had {self.scores[playerResult]}{pMsgAddon}.\nOpponent had {self.scores[dealerResult]}{dMsgAddon}"
			await self.GameOver(interaction, msg, winner=True)
		elif playerResult < dealerResult:
			msg = f"**Player lost.**\nOpponent had {self.scores[dealerResult]}{dMsgAddon}.\nPlayer had {self.scores[playerResult]}{pMsgAddon}"
			await self.GameOver(interaction, msg, winner=False)
		else:
			index = "23456789TJQKA"
			pScore = index.find(pSorted[0][-1])
			dScore = index.find(dSorted[0][-1])

			if pScore == dScore:
				msg = f"**It is a tie.**\nBoth have {self.scores[playerResult]}{pMsgAddon}"
				await self.GameOver(interaction, msg, winner=False)
			elif pScore > dScore:
				msg = f"**Player wins!**\nBoth have {self.scores[playerResult]}, but player has {pSorted[0][-1]} high\nDealer only has {dSorted[0][-1]} high"
				await self.GameOver(interaction, msg, winner=True)
			else:
				msg = f"**Player lost.**\nBoth have {self.scores[playerResult]}, but dealer has {dSorted[0][-1]} high\nPlayer only has {pSorted[0][-1]} high"
				await self.GameOver(interaction, msg, winner=False)

	async def GameOver(self, interaction:Interaction, msg, winner:bool=False, folded:bool=False):
		if folded:
			moneyToAdd = 0
		else: 
			if winner:
				moneyToAdd = self.amntbet * 2
			else:
				moneyToAdd = 0
		
			self.embed.description = msg
		
		self.embed.set_field_at(1, name = f"_ _\nRiver Cards", value = f"{self.GetCardsString(self.riverCards)}", inline=False)
		self.embed.set_field_at(2, name = f"_ _\n{self.bot.user.name}'s cards", value = f"{self.GetCardsString(self.dCards)}", inline=False)

		profitInt = moneyToAdd - self.amntbet

		gameID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, moneyToAdd, giveMultiplier=False, activityName="Poker", amntBet=self.amntbet)

		self.embed = await DB.addProfitAndBalFields(self, interaction, profitInt, self.embed, giveMultiplier=False)

		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		self.embed = await DB.calculateXP(self, interaction, balance - profitInt, self.amntbet, self.embed, gameID)

		# if winner == 999:
		# await self.interaction.send(content=f"{user.mention}", file=file, embed=self.embed)

		# await interaction.send(content=f"{interaction.user.mention}", file=file, embed=self.embed)

		if self.msg:
			await self.msg.edit(view=None, embed=self.embed)
		else:
			await interaction.send(embed=self.embed)

	def PlayerDrawCards(self):
		# self.pCards = ["♥ J", "♠ T"]
		# return
		for _ in range(2):
			card = self.TakeCard()
			self.pCards.append(card)
	
	def OpponentDrawCards(self):
		# self.dCards = ["♠ J", "♥ Q"]
		# return
		for _ in range(2):
			card = self.TakeCard()
			self.dCards.append(card)


class Poker(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.cards = ["♣ A", "♣ 2", "♣ 3", "♣ 4", "♣ 5", "♣ 6", "♣ 7", "♣ 8", "♣ 9", "♣ T", "♣ J", "♣ Q", "♣ K",
					  "♦ A", "♦ 2", "♦ 3", "♦ 4", "♦ 5", "♦ 6", "♦ 7", "♦ 8", "♦ 9", "♦ T", "♦ J", "♦ Q", "♦ K",
					  "♥ A", "♥ 2", "♥ 3", "♥ 4", "♥ 5", "♥ 6", "♥ 7", "♥ 8", "♥ 9", "♥ T", "♥ J", "♥ Q", "♥ K",
					  "♠ A", "♠ 2", "♠ 3", "♠ 4", "♠ 5", "♠ 6", "♠ 7", "♠ 8", "♠ 9", "♠ T", "♠ J", "♠ Q", "♠ K"]
		shuffle(self.cards)

	@nextcord.slash_command(description="Play BlackJack!")
	@commands.bot_has_guild_permissions(send_messages=True, manage_messages=True, embed_links=True, use_external_emojis=True, attach_files=True)
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='blackjack')
	async def poker(self, interaction:Interaction, startingbet):
		startingbet = await self.bot.get_cog("Economy").GetBetAmount(interaction, startingbet)

		if startingbet < 100:
			raise Exception("minBet 100")
		
		if startingbet > GetMaxBet("Poker"):
			raise Exception(f"maxBet {GetMaxBet('Poker')}")
		
		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, startingbet):
			raise Exception("tooPoor")
		
		view = PokerView(self.bot, interaction.user.id, self.cards, startingbet)
		await view.Start(interaction)


def setup(bot):
	bot.add_cog(Poker(bot))