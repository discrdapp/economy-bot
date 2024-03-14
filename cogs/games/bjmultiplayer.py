import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

# import cooldowns
from random import shuffle
import asyncio, cooldowns, emojis


class Player():
	def __init__(self, user, id):
		self.user = user
		self.id = id
		self.isPlayersTurn:bool = False
		self.totalMoneyBet:int = 0

		self.pCards = list()
		self.pCardSuits = list()
		self.pCardNums = list()

		self.insuranceBet = 0

		self.busted = False
		self.stand = False
		self.winner = -1


class JoinGameButton(nextcord.ui.Button):
	def __init__(self, label, style, bot):
		super().__init__(label=label, style=style)
		self.bot = bot
	
	async def callback(self, interaction:Interaction):
		assert self.view is not None
		view:JoinGameView = self.view

		if self.label == "Join":
			if interaction.user.id in [player.user.id for player in view.players]:
				await interaction.send("You have already joined the game", ephemeral=True)
				return
			balance = await view.bot.get_cog("Economy").getBalance(interaction.user)
			if balance < view.amntbet:
				await interaction.send(f"You do not have enough {emojis.coin} to do that (or you are trying to use an amount less than 1)", ephemeral=True)
				return

			view.players.append(Player(interaction.user, len(view.players)+1))

			await interaction.send("You joined the game!", ephemeral=True)
			await view.UpdateJoinMsg()
		elif self.label == "Start":
			if interaction.user.id != view.owner.user.id:
				await interaction.send(f"Only {view.owner.user.mention} can start the game", ephemeral=True)
				return
			if len(view.players) == 1:
				await interaction.send("Cannot start game with just you!", ephemeral=True)
				return
			view.stop()


class JoinGameView(nextcord.ui.View):
	def __init__(self, bot, owner:Player, amntbet):
		super().__init__(timeout=180)
		joinGameButton = JoinGameButton("Join", nextcord.ButtonStyle.blurple, bot)
		startGameButton = JoinGameButton("Start", nextcord.ButtonStyle.green, bot)
		self.add_item(joinGameButton)
		self.add_item(startGameButton)

		self.bot = bot
		self.owner = owner
		self.amntbet = amntbet
		self.players = list()
		owner.isPlayersTurn = True
		self.players.append(owner)

		self.msg = None

	async def on_timeout(self):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Blackjack Multiplayer")
		embed.description = f"{self.owner.user.mention} took too long to start game. Game cancelled."
		embed.set_footer(text="Your balance was not changed")
		await self.msg.edit(embed=embed, view=None)
	

	async def UpdateJoinMsg(self):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Blackjack Multiplayer")

		usersInGame = ""
		for player in self.players:
			usersInGame += f"{player.user.mention}\n"
		embed.description = f"Waiting for players...\nPeople currently in game:\n{usersInGame}"

		await self.msg.edit(embed=embed)


class CreditsToBet(nextcord.ui.TextInput):
	def __init__(self):
		super().__init__(label="Amount of credits", placeholder="Max amount is your bet", min_length=1)

class Insurance(nextcord.ui.Modal):
	def __init__(self, view, bot):
		super().__init__(title="Insurance", timeout=None)
		self.add_item(CreditsToBet())
		self.view = view
		self.bot:commands.bot.Bot = bot

	async def callback(self, interaction: Interaction):
		assert self.view is not None
		view: Blackjack = self.view

		if interaction.user.id not in [player.user.id for player in view.players]:
			await interaction.send("This is not your game!", ephemeral=True)
			return
		currPlayer:Player = view.GetPlayerWithUserID(interaction.user.id)

		if not currPlayer.isPlayersTurn:
			await interaction.send("It is not your turn!", ephemeral=True)
			return
		if not self.children[0].value.isdigit():
			await interaction.send("Please enter a valid number!", ephemeral=True)
			return
		insuranceBet = int(self.children[0].value)
		if insuranceBet > view.amntbet:
			await interaction.send(f"You can't bet more than the original bet of {view.amntbet}!", ephemeral=True)
			return
		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, insuranceBet):
			await interaction.send("You don't have enough credits for that bet", ephemeral=True)
			return

		currPlayer.insuranceBet = int(self.children[0].value)

		await interaction.response.defer()
		self.stop() 

class Button(nextcord.ui.Button['Blackjack']):
	def __init__(self, bot, label, style, row=0, disabled=False):
		self.bot:commands.bot.Bot = bot
		super().__init__(label=label, style=style, row=row, disabled=disabled)
		self.modal = None

	async def callback(self, interaction: Interaction):
		assert self.view is not None
		view: Blackjack = self.view

		if interaction.user.id not in [player.user.id for player in view.players]:
			await interaction.send("This is not your game!", ephemeral=True)
			return
		currPlayer:Player = [player for player in view.players if player.user.id == interaction.user.id][0]

		if not currPlayer.isPlayersTurn:
			await interaction.send("It is not your turn!")
			return

		if self.label == "Yes" or self.label == "No":
			if self.label == "Yes":
				self.modal = Insurance(view, view.bot)
				await interaction.response.send_modal(self.modal)
				await self.modal.wait()
			await view.NextTurn(currPlayer.id)
		if self.label == "Double Down":
			if len(currPlayer.pCardNums) > 2:
				await interaction.send("You can only Double Down on your first turn", ephemeral=True)
				return
			if not await self.bot.get_cog("Economy").subtractBet(currPlayer.user, currPlayer.totalMoneyBet*2):
				await interaction.send("You don't have enough credits for that bet", ephemeral=True)
				return
			currPlayer.totalMoneyBet *= 2
			await view.hit(currPlayer, True)
		if self.label == "Hit":
			await view.hit(currPlayer)
		elif self.label == "Stand":
			await view.stand()

		if view.gameOver:
			return
		
		view.UpdateEmbed()
		await view.msg.edit(embed=view.embed, view=view)
		try:
			await interaction.response.defer()
		except:
			pass


class Blackjack(nextcord.ui.View):
	def __init__(self, bot, channel, players, owner, cards, amntbet):
		super().__init__(timeout=None)
		self.bot:commands.bot.Bot = bot
		self.channel = channel

		self.players = players
		self.owner:Player = owner
		
		self.currTurnID = 1

		self.cards = cards

		self.interaction = None
		self.ownerId = owner.user.id

		self.gameOver = False


		self.dealerNum = list()
		self.dealerHand = list()
		self.embed = None
		self.msg = None

		self.amntbet = amntbet

		self.idsLeft = [x for x in range(1, len(players)+1)]

		self.doubleDown = Button(bot, label="Double Down", style=nextcord.ButtonStyle.blurple, row=1)
		self.add_item(self.doubleDown)
		self.insuranceYes = Button(bot, label="Yes", style=nextcord.ButtonStyle.blurple, row=1)
		self.insuranceNo = Button(bot, label="No", style=nextcord.ButtonStyle.blurple, row=1)
		self.insuranceIDsLeft = None

		self.hitButton = Button(self.bot, label="Hit", style=nextcord.ButtonStyle.green)
		self.standButton = Button(self.bot, label="Stand", style=nextcord.ButtonStyle.red)

		self.add_item(self.hitButton)
		self.add_item(self.standButton)



	async def CheckForInsurance(self):
			await self.msg.edit(content=f"Checking for blackjack")
			await asyncio.sleep(0.6)
			await self.msg.edit(content=f"Checking for blackjack.")
			await asyncio.sleep(0.6)
			await self.msg.edit(content=f"Checking for blackjack..")
			await asyncio.sleep(0.6)
			await self.msg.edit(content=f"Checking for blackjack...")
			await asyncio.sleep(0.6)
			if self.dealerNum[1] == 10: # checks if dealer's second card is a 10
				self.gameOver = True
				await self.msg.edit(content=f"Checking for blackjack... Protected by insurance!")
				return True
			else:
				await self.msg.edit(content=f"Dealer does not have blackjack... game will continue")
				return False

	async def PlayerStandOrBustCheckGameOver(self, playedStayed:Player):
		self.idsLeft.remove(playedStayed.id)
		if len(self.idsLeft) == 0:
			await self.dealer_turn()
			await self.msg.edit(view=None)
			self.gameOver = True
			await self.EndGame()
			return
		await self.NextTurn(playedStayed.id)


	async def CheckForBlackjack(self):
		await self.msg.edit(content=f"Checking for blackjack")
		await asyncio.sleep(0.6)
		await self.msg.edit(content=f"Checking for blackjack.")
		await asyncio.sleep(0.6)
		await self.msg.edit(content=f"Checking for blackjack..")
		await asyncio.sleep(0.6)
		await self.msg.edit(content=f"Checking for blackjack...")
		await asyncio.sleep(0.6)
		if self.dealerNum[1] == 10: # checks if dealer's second card is a 10
			await self.msg.edit(content=f"DEALER HAS BLACKJACK!")
			for player in self.players:
				if player.insuranceBet > 0:
					player.winner = 999
			await self.displayWinners()
			self.gameOver = True
			return True
		else:
			await self.msg.edit(content=f"Dealer does not have blackjack... game will continue")
	
	async def NextTurn(self, id):
		self.GetPlayerWithPlayerID(id).isPlayersTurn = False

		if self.insuranceIDsLeft:
			self.insuranceIDsLeft.remove(id)

			if len(self.insuranceIDsLeft) == 0:
				if await self.CheckForBlackjack():
					return
				self.insuranceIDsLeft = self.idsLeft.copy()
				self.doubleDown.disabled = False
				self.hitButton.disabled = False
				self.standButton.disabled = False
				self.remove_item(self.insuranceYes)
				self.remove_item(self.insuranceNo)
				
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

	def GetPlayerWithUserID(self, userID):
		for player in self.players:
			if player.user.id == userID:
				return player
	
	def GetPlayerWithPlayerID(self, playerID):
		for player in self.players:
			if player.id == playerID:
				return player

	def GetCardsString(self, cards):
		pTotal = ""
		for x in cards:
			pTotal += f"{x} "
		return pTotal

	def UpdateEmbed(self):
		self.embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Blackjack")

		self.embed.description = f"Player's Turn: {self.GetPlayerWithPlayerID(self.currTurnID).user.mention}"

		if not self.gameOver:
			self.embed.add_field(name = f"{self.bot.user.name}'s cards", value = f"{self.dealerHand[0]}", inline=False)
		else:
			self.embed.add_field(name = f"{self.bot.user.name}'s cards", value = f"{self.GetCardsString(self.dealerHand)}\n**Score**: {sum(self.dealerNum)}\n", inline=False)

		for player in self.players:
			msg = ""
			if player.busted:
				msg = "(BUSTED)"
			elif player.stand:
				msg = "(STAYED)"
			self.embed.add_field(name = f"{player.user.display_name}'s cards:", value = f"{self.GetCardsString(player.pCards)}\n**Score**: {sum(player.pCardNums)} {msg}", inline=False)
		if self.insuranceIDsLeft == None or len(self.insuranceIDsLeft) == 0:
			self.embed.add_field(name = "_ _", value = "**Options:** hit or stay", inline=False)
		else:
			self.embed.add_field(name = "_ _", value = "**Do you want to buy Insurance?**", inline=False)


	async def Start(self):
		# generate the starting cards
		for player in self.players:
			player.totalMoneyBet = self.amntbet
			await self.bot.get_cog("Economy").addWinnings(player.user.id, -self.amntbet)

		self.embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Blackjack")
		self.embed.set_thumbnail(url="attachment://image.png")


		self.dealer_first_turn()

		await self.players_first_turn()

	async def players_first_turn(self):
		for player in self.players:
			for x in range(0,2):
				# player draws a card
				# 
				# pDrawnCard = "♦ 10"
				
				pDrawnCard = self.take_card()
				player.pCards.append(pDrawnCard)

				# splits the number and the suit 
				pDrawnCard = pDrawnCard.split()

				# converts to number
				if pDrawnCard[1] == "Jack" or pDrawnCard[1] == "Queen" or pDrawnCard[1] == "King":
					pDrawnCard[1] = "10"
				elif pDrawnCard[1] == "A":
					pDrawnCard[1] = "11"

				# adds the card to the player's hand
				player.pCardNums.append(int(pDrawnCard[1]))

				# checks if player has an ace
				player.pCardNums = self.eval_ace(player.pCardNums)

			
			if (self.is_blackjack(player.pCardNums)):
				await self.stand()
				return
		
		self.embed.set_footer(text=f"Cards in Deck: {len(self.cards)}")

		self.UpdateEmbed()
		self.msg = await self.channel.send(embed=self.embed, view=self)


	async def hit(self, player:Player, isDoubleDown=False):
		pDrawnCard = self.take_card()

		# splits the number and the suit 
		splitpDrawnCard = pDrawnCard.split()

		# converts to number
		if splitpDrawnCard[1] == "Jack" or splitpDrawnCard[1] == "Queen" or splitpDrawnCard[1] == "King":
			splitpDrawnCard[1] = "10"
		elif splitpDrawnCard[1] == "A":
			splitpDrawnCard[1] = "11"


		# adds card to player hand
		player.pCards.append(pDrawnCard)
		# adds the card num to the player's hand
		player.pCardNums.append(int(splitpDrawnCard[1]))
	
		# checks if player has an ace
		player.pCardNums = self.eval_ace(player.pCardNums)

		self.embed.set_footer(text=f"Cards in Deck: {len(self.cards)}")

		# ends game if player busted or has 21
		if (self.is_bust(player.pCardNums) or self.is_blackjack(player.pCardNums)):
			if self.is_blackjack(player.pCardNums): # gets 21
				await self.stand()
			else: # busts
				player.busted = True
				await self.PlayerStandOrBustCheckGameOver(player)
			return
		if isDoubleDown:
			await self.stand()


	async def stand(self):
		player = self.GetPlayerWithPlayerID(self.currTurnID)
		player.stand = True

		await self.PlayerStandOrBustCheckGameOver(player)

	async def EndGame(self):
		for player in self.players:
			player.winner = self.compare_between(player.pCardNums)
		await self.displayWinners() 

	def take_card(self):
		# if all 52 cards have been used, reset the deck
		if len(self.cards) == 0:
			self.cards = ["♣ A", "♣ 2", "♣ 3", "♣ 4", "♣ 5", "♣ 6", "♣ 7", "♣ 8", "♣ 9", "♣ 10", "♣ Jack", "♣ Queen", "♣ King",
						  "♦ A", "♦ 2", "♦ 3", "♦ 4", "♦ 5", "♦ 6", "♦ 7", "♦ 8", "♦ 9", "♦ 10", "♦ Jack", "♦ Queen", "♦ King",
						  "♥ A", "♥ 2", "♥ 3", "♥ 4", "♥ 5", "♥ 6", "♥ 7", "♥ 8", "♥ 9", "♥ 10", "♥ Jack", "♥ Queen", "♥ King",
						  "♠ A", "♠ 2", "♠ 3", "♠ 4", "♠ 5", "♠ 6", "♠ 7", "♠ 8", "♠ 9", "♠ 10", "♠ Jack", "♠ Queen", "♠ King"]
			shuffle(self.cards)

		drawnCard = self.cards.pop()

		return drawnCard


	def eval_ace(self, cardNum):
		# Determine Ace = 1 or 11, relying on total cardNum. 
		total = sum(cardNum)
		for ace in cardNum:
			if ace == 11 and total > 21:
				# at position, where Ace == 11, replace by Ace == 1.
				position_ace = cardNum.index(11)
				cardNum[position_ace] = 1
		return cardNum


	def is_bust(self, cardNum):
		# Condition True: if the cardNum of player (or dealer) > 21.
		total = sum(cardNum)
		if total > 21:
			return True
		return None


	def is_blackjack(self, cardNum):
		# Condition True: if the cardNum of player (or dealer) == 21.
		total = sum(cardNum)
		if total == 21:
			return True
		return None

	def dealer_first_turn(self):
		dDrawnCard = self.take_card()
		for x in range(2):
			dDrawnCard = self.take_card()
			# dDrawnCard = "♦ A"
			# if x == 0:
			# 	dDrawnCard = "♦ A"
			# else:
			# 	dDrawnCard = "♦ 10"
			self.dealerHand.append(dDrawnCard)

			dDrawnCard = dDrawnCard.split()

			if dDrawnCard[1] == "Jack" or dDrawnCard[1] == "Queen" or dDrawnCard[1] == "King":
				dDrawnCard[1] = "10"
			elif dDrawnCard[1] == "A":
				dDrawnCard[1] = "11"

			self.dealerNum.append(int(dDrawnCard[1]))
			self.dealerNum = self.eval_ace(self.dealerNum)

		if self.dealerHand[0][-1] == "A":
			self.insuranceIDsLeft = self.idsLeft.copy()
			self.doubleDown.disabled = True
			self.hitButton.disabled = True
			self.standButton.disabled = True
			self.add_item(self.insuranceYes)
			self.add_item(self.insuranceNo)

	async def refresh_dealer_hand(self):
		self.UpdateEmbed()
		await self.msg.edit(view=None, embed=self.embed)
		await asyncio.sleep(0.6)


	async def dealer_turn(self):
		# d will keep drawing until card values sum > 16
		while sum(self.dealerNum) <= 16:
			# grabs a card
			dDrawnCard = self.take_card()
			# adds it to his hand
			self.dealerHand.append(dDrawnCard)

			# splits suit and number
			dDrawnCard = dDrawnCard.split()

			if dDrawnCard[1] == "Jack" or dDrawnCard[1] == "Queen" or dDrawnCard[1] == "King":
				dDrawnCard[1] = "10"
			elif dDrawnCard[1] == "A":
				dDrawnCard[1] = "11"

			self.dealerNum.append(int(dDrawnCard[1]))

			self.dealerNum = self.eval_ace(self.dealerNum)

			await self.refresh_dealer_hand()
		

	def compare_between(self, cardNum):
		total_player = sum(cardNum)
		total_dealer = sum(self.dealerNum)
		player_bust = self.is_bust(cardNum)
		dealer_bust = self.is_bust(self.dealerNum)
		player_blackjack = self.is_blackjack(cardNum)
		dealer_blackjack = self.is_blackjack(self.dealerNum)

		# when p bust.
		if player_bust:
			return -1
		# when d bust
		elif dealer_bust:
			return 1
		# when both 21
		elif player_blackjack and dealer_blackjack:
			return 0
		# when p 21
		elif player_blackjack:
			return 1
		# when d 21
		elif dealer_blackjack:
			return -1
		# when total CARD of player (dealer) < 21.
		elif total_player < 21 and total_dealer < 21:
			if total_player > total_dealer:
				return 1
			elif total_dealer > total_player:
				return -1
			else:
				return 0

	async def displayWinners(self):
		self.UpdateEmbed()

		self.embed.color = nextcord.Color(0xff2020)
		await self.msg.edit(embed=self.embed)	


		gameIDsMsg = ""
		wonMsg = ""
		for player in self.players:
			moneyToAdd = 0
			if player.winner == 999: # won by insurance
				wonMsg += f"{player.user.mention} won by insurance\n"
				moneyToAdd = player.insuranceBet * 3
			elif player.winner == 1:
				wonMsg += f"{player.user.mention} beat dealer\n"
				moneyToAdd = player.totalMoneyBet * 2 
			elif player.winner == -1:
				wonMsg += f"{player.user.mention} lost to dealer\n"
				moneyToAdd = 0 # nothing to add since loss
			elif player.winner == 0:
				wonMsg += f"{player.user.mention} pushed!\n"
				moneyToAdd = player.totalMoneyBet # add back their bet they placed since it was pushed (tied)
			gameID = await self.bot.get_cog("Economy").addWinnings(player.user.id, moneyToAdd, giveMultiplier=False, activityName="Multiplayer BJ", amntBet=player.totalMoneyBet)
			gameIDsMsg += f"{player.user.mention}'s GameID: {gameID}\n"

		if not wonMsg: wonMsg = "Dealer wins!\n"
		self.embed.description = wonMsg + "\n" + gameIDsMsg


		# if winner == 999:
		# await self.interaction.send(content=f"{user.mention}", file=file, embed=self.embed)

		# await interaction.send(content=f"{interaction.user.mention}", file=file, embed=self.embed)

		await self.msg.edit(embed=self.embed, view=None)


class BJMultiplayer(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.cards = ["♣ A", "♣ 2", "♣ 3", "♣ 4", "♣ 5", "♣ 6", "♣ 7", "♣ 8", "♣ 9", "♣ 10", "♣ Jack", "♣ Queen", "♣ King",
					  "♦ A", "♦ 2", "♦ 3", "♦ 4", "♦ 5", "♦ 6", "♦ 7", "♦ 8", "♦ 9", "♦ 10", "♦ Jack", "♦ Queen", "♦ King",
					  "♥ A", "♥ 2", "♥ 3", "♥ 4", "♥ 5", "♥ 6", "♥ 7", "♥ 8", "♥ 9", "♥ 10", "♥ Jack", "♥ Queen", "♥ King",
					  "♠ A", "♠ 2", "♠ 3", "♠ 4", "♠ 5", "♠ 6", "♠ 7", "♠ 8", "♠ 9", "♠ 10", "♠ Jack", "♠ Queen", "♠ King"]
		shuffle(self.cards)

	@nextcord.slash_command(description="Play Multiplayer Blackjack!!")
	@commands.bot_has_guild_permissions(send_messages=True, manage_messages=True, embed_links=True, use_external_emojis=True, attach_files=True)
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='mblackjack')
	async def multiplayerbj(self, interaction:Interaction, amntbet:int):
		if amntbet < 100:
			raise Exception("minBet 100")

		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		if balance < amntbet:
			raise Exception("tooPoor")
		
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Blackjack Multiplayer")

		owner = Player(interaction.user, 1)
		joinGameView = JoinGameView(self.bot, owner, amntbet)

		embed.description = f"Waiting for players...\nPeople currently in game:\n{interaction.user.mention}"
		msg = await interaction.send(embed=embed, view=joinGameView)
		joinGameView.msg = msg

		if await joinGameView.wait():
			return
		await msg.delete()

		view = Blackjack(self.bot, interaction.channel, joinGameView.players, owner, self.cards, amntbet)

		await view.Start()


def setup(bot):
	bot.add_cog(BJMultiplayer(bot))