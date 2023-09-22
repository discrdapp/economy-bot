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

class Player():
	def __init__(self, user, interaction, id):
		self.gameView:GameView = None
		self.user:nextcord.User = user
		self.interaction = interaction
		self.message:nextcord.Message = None
		self.id = id
		self.hand = list()
		self.totalSpent = 0
		self.fundsWon = 0

		self.view = self.PlayerView()

		self.isPlayersTurn = False
	
	def Setup(self, player):
		self.view.player = player
	
	class BetCheckFoldButton(nextcord.ui.Button):
		def __init__(self, label, style):
			super().__init__(label=label, style=style)
		
		async def callback(self, interaction:Interaction):
			assert self.view is not None
			view:Player.PlayerView = self.view

			if not view.player.isPlayersTurn:
				await interaction.send("It is not your turn!", ephemeral=True)
				return

			if self.label == "Bet":
				await view.player.gameView.bot.get_cog("Economy").addWinnings(view.player.user.id, -view.player.gameView.startingbet, giveMultiplier=False)
				view.player.totalSpent += view.player.gameView.startingbet
				view.player.gameView.totalFundsToAdd += view.player.gameView.startingbet
				if await view.player.gameView.PlayerClickedBet(view.player):
					return
			elif self.label == "Check":
				if await view.player.gameView.PlayerClickedCheck(view.player):
					return
			elif self.label == "Fold":
				if await view.player.gameView.PlayerFoldCheckGameover(view.player):
					return
			print(f"view is {view}")
			view.player.gameView.NextTurn(view.player.id)

			view.player.isPlayersTurn = False
			await view.player.gameView.UpdateMessages()



	class PlayerView(nextcord.ui.View):
		def __init__(self, player=None):
			super().__init__(timeout=None)
			print("instantiated 123!")

			self.player:Player = player

			self.betButton = Player.BetCheckFoldButton("Bet", nextcord.ButtonStyle.blurple)
			self.checkButton = Player.BetCheckFoldButton("Check", nextcord.ButtonStyle.green)
			self.foldButton = Player.BetCheckFoldButton("Fold", nextcord.ButtonStyle.red)

			self.add_item(self.betButton)
			self.add_item(self.checkButton)
			self.add_item(self.foldButton)
		
		async def on_timeout(self):
			if self.player.isPlayersTurn:
				print("12323435235")
				self.player.isPlayersTurn = False
				await self.player.message.channel.send(f"{self.player.user.mention} took too long to respond. Automatic fold. Game will continue.", delete_after=3)
				if await self.player.gameView.PlayerFoldCheckGameover(self.player):
					return
				self.player.gameView.NextTurn(self.player.id)

				for aPlayer in self.player.gameView.players:
					aPlayer.view = aPlayer.PlayerView(aPlayer)
				await self.player.gameView.UpdateMessages(expired=True)

			


class JoinGameButton(nextcord.ui.Button):
	def __init__(self, label, style):
		super().__init__(label=label, style=style)
	
	async def callback(self, interaction:Interaction):
		assert self.view is not None
		view:JoinGameView = self.view

		if self.label == "Join":
			balance = await view.bot.get_cog("Economy").getBalance(interaction.user)

			if interaction.user.id in [player.user.id for player in view.players]:
				await interaction.send("You have already joined the game", ephemeral=True)
				return
			if view.startingbet * 3 > balance:
				await interaction.send(f"You need at least {(view.startingbet*3):,} (3x the starting bet of {view.startingbet:,}) to join this game", ephemeral=True)
				return
			
			newPlayer = Player(interaction.user, interaction, len(view.players)+1)
			view.players.append(newPlayer)

			await interaction.send("You joined the game!", ephemeral=True)
			await view.UpdateJoinMsg()
		elif self.label == "Start":
			if interaction.user.id != view.owner.id:
				await interaction.send(f"Only {view.owner.mention} can start the game", ephemeral=True)
				return
			if len(view.players) == 1:
				await interaction.send("Cannot start game with just you!", ephemeral=True)
				return
			view.stop()


class JoinGameView(nextcord.ui.View):
	def __init__(self, bot, ownerPlayer, startingbet):
		super().__init__(timeout=180)
		joinGameButton = JoinGameButton("Join", nextcord.ButtonStyle.blurple)
		startGameButton = JoinGameButton("Start", nextcord.ButtonStyle.green)
		self.add_item(joinGameButton)
		self.add_item(startGameButton)

		self.bot = bot
		self.owner = ownerPlayer.user
		self.startingbet = startingbet
		self.players = list()
		self.players.append(ownerPlayer)

		self.msg = None
	
	async def on_timeout(self):
		print("timeout")
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Poker Multiplayer")
		embed.description = f"{self.owner.mention} took too long to start game. Game cancelled."
		embed.set_footer(text="Your balance was not changed")
		self.clear_items()
		await self.msg.edit(embed=embed, view=self)
	
	async def UpdateJoinMsg(self):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Poker Multiplayer")

		usersInGame = ""
		for player in self.players:
			usersInGame += f"{player.user.mention}\n"
		embed.description = f"Waiting for players...\nPeople currently in game:\n{usersInGame}"

		await self.msg.edit(embed=embed)

class GameView(nextcord.ui.View):
	def __init__(self, bot, cards, channel, players, owner, startingbet):
		super().__init__(timeout=120)

		self.bot = bot
		self.cards = cards
		self.channel:nextcord.TextChannel = channel
		self.players:dict = players
		self.owner:Player = owner
		self.startingbet = startingbet


		self.currBet = self.startingbet
		
		self.totalFundsToAdd = len(players)*self.currBet

		self.idsLeft = [x for x in range(1, len(players)+1)]
		self.currTurnID = 1

		self.riverCards = [":black_joker:", ":black_joker:", ":black_joker:"]
		self.cardsDealt = 0
		self.lastCheckPersonTillFlip = self.players[-1]

		self.isBetting = False

		self.scores = ["High Card", "Pair", "Two Pair", "Three of a Kind", "Straight", "Flush", "Full House", "Four of a Kind", "Straight Flush"]
	
	def GetPlayerWithID(self, id):
		for player in self.players:
			if id == player.id:
				return player
	
	async def PlayerClickedCheck(self, checker):
		if self.lastCheckPersonTillFlip.id != checker.id:
			return False
		return await self.FlipCards()
	
	async def PlayerClickedBet(self, better):
		if self.isBetting:
			if self.lastCheckPersonTillFlip.id != better.id:
				return False

			self.isBetting = False
			if await self.FlipCards():
				return True

			for player in self.players:
				view:Player.PlayerView = player.view
				view.checkButton.disabled = False

				await self.UpdateMessages()
		else:
			self.isBetting = True
			for player in self.players:
				view:Player.PlayerView = player.view
				view.checkButton.disabled = True

			lastPersonID = better.id - 1
			if better.id == self.idsLeft[0]: # if better is first person
				# set to last person
				self.lastCheckPersonTillFlip = self.GetPlayerWithID(self.idsLeft[-1])
			elif lastPersonID in self.idsLeft: # if previous person is available
				# set to them
				self.lastCheckPersonTillFlip = self.GetPlayerWithID(lastPersonID)
			else:
				for id in self.idsLeft:
					if lastPersonID < id:
						self.lastCheckPersonTillFlip = self.GetPlayerWithID(lastPersonID)
			
		return False


	async def PlayerFoldCheckGameover(self, playerFolded):
		self.idsLeft.remove(playerFolded.id)

		if len(self.idsLeft) == 1:
			for player in self.players:
				if player.id == self.idsLeft[0]:
					player.fundsWon = self.totalFundsToAdd
					await self.GameOver([player])
					break
			return True
		return False

	def NextTurn(self, id):
		id += 1
		while id not in self.idsLeft:
			id += 1
			if id > self.idsLeft[-1]:
				id = 1
		
		self.currTurnID = id
		for player in self.players:
			if player.id == id:
				player.isPlayersTurn = True
				break

	async def FlipCards(self):
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
			self.NextTurn = -1
			await self.AfterFlop()
			return True

	def GetViewableHand(self, hand):
		msg = ""
		for card in hand:
			msg += f"{card} | "
		return msg

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

	def DrawCards(self):
		for player in self.players:
			for _ in range(2):
				player.hand.append(self.TakeCard())
	
	async def UpdateMessages(self, expired=False):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Poker")
		for player in self.players:
			embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Poker")

			msg = f"Player's Turn: {[player.user.mention for player in self.players if player.id == self.currTurnID][0]}\nCurrent Bet: {self.currBet}{emojis.coin}\n\
				Total Pot: {self.totalFundsToAdd}{emojis.coin}"
			if player.id in self.idsLeft:
				playerCards = self.GetViewableHand(player.hand)
			else:
				playerCards = "Folded"
			embed.add_field(name="Your Hand", value=playerCards, inline=False)
			embed.add_field(name="River Cards", value=self.GetViewableHand(self.riverCards), inline=False)
			for opponent in self.players:
				if opponent.id == player.id:
					continue
				if opponent.id in self.idsLeft:
					oppoCards = ":question: :question:"
				else:
					oppoCards = "Folded"
				embed.add_field(name=f" (Player {opponent.id}) {opponent.user.display_name}'s Hand", value = f"{oppoCards}", inline=False)

			embed.description = msg

			if not expired:
				await player.message.edit(embed=embed, view=player.view)
			else:
				await player.message.delete()
				player.message = await player.interaction.send(embed=embed, view=player.view, ephemeral=True)

	async def Start(self):
		for player in self.players:
			player.gameView = self
			player.Setup(player)
		self.DrawCards()

		for player in self.players:
			embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Poker Multiplayer")
			msg = f"Player's Turn: {[player.user.mention for player in self.players if player.id == self.currTurnID][0]}\nCurrent Bet: {self.currBet}{emojis.coin}\n\
				Total Pot: {self.totalFundsToAdd}{emojis.coin}"
			embed.add_field(name="Your Hand", value=self.GetViewableHand(player.hand), inline=False)
			embed.add_field(name="River Cards", value=self.GetViewableHand(self.riverCards), inline=False)
			for opponent in self.players:
				if opponent.id == player.id:
					continue
				embed.add_field(name=f" (Player {opponent.id}) {opponent.user.display_name}'s Hand", value = ":question: :question:", inline=False)

			embed.description = msg
			player.message = await player.interaction.send(view=player.view, embed=embed, ephemeral=True)


	# pass in either dealer or player hand
	def GetBestHand(self, playerHand):
		def num_of_kind(cards):
			count = Counter(c[-1] for c in cards)
			return count

		def count_pairs(cards):
			return sum(i > 1 for i in num_of_kind(cards).values())

		def largest_pair(cards):
			return max(num_of_kind(cards).values())

		def is_straight(cards):
			values = [c[-1] for c in cards]
			index = "A23456789TJQKA"["K" in values:].index
			indices = sorted(index(v) for v in values)
			return all(x == y for x, y in enumerate(indices, indices[-1]))

		def is_flush(cards):
			suit_pop = Counter(c[0] for c in cards)
			return any(s > 4 for s in suit_pop.values())

		def straight_sort(cards):
			values = [c[0] for c in cards]
			index = "A23456789TJQKA"["K" in values:].index
			return sorted(cards, key=lambda x:index(x[-1]), reverse=True)

		def flush_sort(cards):
			suit_pop = Counter(c[0] for c in cards)
			return sorted(cards, key=lambda x: suit_pop[x[0]], reverse=True)

		def pair_sort(cards):
			num = num_of_kind(cards)
			return sorted(cards, key=lambda x: num[x[-1]], reverse=True)

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

			return cards, hand_score

		tempCards = self.riverCards.copy()
		tempCards += playerHand.copy()
		print(f"tempcards are {tempCards}")

		cards = max(list(combinations(tempCards, 7)), key=score_hand)
		cards, score = score_hand(cards)

		return cards, score

	async def AfterFlop(self):
		scores = dict()

		print(f"ids left afterflop: {self.idsLeft}")
		for id in self.idsLeft:
			playerSorted, playerResult = self.GetBestHand(self.GetPlayerWithID(id).hand.copy())
			scores[id] = dict()
			scores[id]["cards"] = playerSorted
			scores[id]["score"] = playerResult

		maxScore = max([score['score'] for score in scores.values()])

		tiedUsers = [self.GetPlayerWithID(id) for id in scores.keys() if scores[id]["score"] == maxScore]

		# if only one user won
		if len(tiedUsers) == 1:
			tiedUsers[0].fundsWon = self.totalFundsToAdd
			await self.GameOver([tiedUsers[0]], self.scores[maxScore])
			return

		tiedScores = dict()
		index = "23456789TJQKA"
		for player in tiedUsers:
			tiedScores[player.id] = index.find(scores[player.id]["cards"][0][-1])

		tiedWinnerScore = max([score for score in tiedScores.values()])

		tiedWinnersPlayers = [self.GetPlayerWithID(id) for id in tiedScores.keys() if tiedScores[id] == tiedWinnerScore]

		if len(tiedWinnersPlayers) == 1:
			tiedWinnersPlayers[0].fundsWon = self.totalFundsToAdd
		else:
			for player in tiedWinnersPlayers:
				player.fundsWon = self.totalFundsToAdd / len(tiedWinnersPlayers)
		print(f"tied score is {maxScore}")
		await self.GameOver(tiedWinnersPlayers, self.scores[maxScore])



	async def GameOver(self, winner:list, winningHand=None):
		self.currTurnID = -1
		for player in self.players:
			player.isPlayersTurn = False
			player.view.clear_items()
			embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Multiplayer Poker")

			gameID = await self.bot.get_cog("Economy").addWinnings(player.user.id, player.fundsWon, giveMultiplier=False, activityName="Multiplayer Poker", amntBet=player.totalSpent)

			embed.description = f"Game ID: {gameID}"
			await player.message.edit(embed=embed, view=player.view)


		winningHandMsg = ""
		if winningHand != None:
			winningHandMsg = f"with a {winningHand}"

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Multiplayer Poker")
		if len(winner) == 1:
			winner = winner[0]
			embed.description = f"Game over. {winner.user.mention} wins {winner.fundsWon:,}{emojis.coin} {winningHandMsg}"
		else:
			msg = ""
			for player in winner:
				msg += f"{player.user.mention} "
			embed.description = f"Game over. Players {msg} tied {winningHandMsg}"

		embed.add_field(name="River Cards", value=self.GetViewableHand(self.riverCards), inline=False)
		for player in self.players:
			if player.id in self.idsLeft:
				playerCards = self.GetViewableHand(player.hand)
			else:
				playerCards = "Folded"
			embed.add_field(name=f" (ID {player.id}) {player.user.display_name}'s Hand", value = f"{playerCards}", inline=False)

		await self.channel.send(embed=embed)



class PokerMultiplayer(commands.Cog):
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
	async def multiplayerpoker(self, interaction:Interaction, startingbet:int):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Poker Multiplayer")

		owner = Player(interaction.user, interaction, 1)
		owner.isPlayersTurn = True
		joinGameView = JoinGameView(self.bot, owner, startingbet)

		embed.description = f"Waiting for players...\nPeople currently in game:\n{interaction.user.mention}"
		msg = await interaction.send(embed=embed, view=joinGameView)
		joinGameView.msg = msg

		if await joinGameView.wait():
			return
		await msg.delete()

		gameView = GameView(self.bot, self.cards, interaction.channel, joinGameView.players, interaction.user, startingbet)
		await gameView.Start()



def setup(bot):
	bot.add_cog(PokerMultiplayer(bot))