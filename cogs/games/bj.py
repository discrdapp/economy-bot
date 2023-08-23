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

# import cooldowns
from random import randint
import asyncio, cooldowns

from db import DB

class CreditsToBet(nextcord.ui.TextInput):
	def __init__(self):
		super().__init__(label="Amount of credits", placeholder="Max amount is your bet", min_length=1)

class Insurance(nextcord.ui.Modal):
	def __init__(self, view, bot):
		super().__init__(title="Insurance")
		self.add_item(CreditsToBet())
		self.view = view
		self.bot:commands.bot.Bot = bot

	async def callback(self, interaction: Interaction):
		if interaction.user.id != self.view.ownerId:
			await interaction.send("This is not your game!", ephemeral=True)
			return
		if not self.children[0].value.isdigit():
			await interaction.send("Please enter a valid number!", ephemeral=True)
			return
		self.view.insuranceBet = int(self.children[0].value)
		if self.view.insuranceBet > self.view.amntbet:
			await interaction.send(f"You can't bet more than your original bet of {self.view.amntbet}!", ephemeral=True)
			return
		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, self.view.insuranceBet):
			await interaction.send("You don't have enough credits for that bet", ephemeral=True)
			return
		
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

		if view.ownerId != interaction.user.id:
			await interaction.send("This is not your game!", ephemeral=True)
			return

		if self.label == "Insurance":
			self.modal = Insurance(view, view.bot)
			await interaction.response.send_modal(self.modal)
			await self.modal.wait()

			await interaction.edit_original_message(content=f"{interaction.user.mention}\nChecking for blackjack")
			await asyncio.sleep(0.6)
			await interaction.edit_original_message(content=f"{interaction.user.mention}\nChecking for blackjack.")
			await asyncio.sleep(0.6)
			await interaction.edit_original_message(content=f"{interaction.user.mention}\nChecking for blackjack..")
			await asyncio.sleep(0.6)
			await interaction.edit_original_message(content=f"{interaction.user.mention}\nChecking for blackjack...")
			await asyncio.sleep(0.6)
			if view.dealerNum[1] == 10: # checks if dealer's second card is a 10
				await interaction.edit_original_message(content=f"{interaction.user.mention}\nChecking for blackjack... Protected by insurance!")
				await view.displayWinner(999)
				return
			else:
				await interaction.edit_original_message(content=f"{interaction.user.mention}\nDealer does not have blackjack... game will continue")
		if self.label == "Double Down":
			if not await self.bot.get_cog("Economy").subtractBet(interaction.user, self.view.amntbet):
				await interaction.send("You don't have enough credits for that bet", ephemeral=True)
				return
			self.view.amntbet *= 2
			await view.hit(True)
		if self.label == "Hit":
			await view.hit()
		elif self.label == "Stand":
			await view.stand()
			return

		if not view.insurance.disabled:
			view.insurance.disabled = True
		if not view.doubleDown.disabled:
			view.doubleDown.disabled = True
		await view.msg.edit(embed=view.embed, view=view)
		try:
			await interaction.response.defer()
		except:
			pass

class Blackjack(nextcord.ui.View):
	def __init__(self, bot, id, cards, amntbet):
		super().__init__(timeout=120)
		self.bot:commands.bot.Bot = bot
		self.coin = "<:coins:585233801320333313>"

		self.cards = cards
		self.pCARD = list()
		self.pCardSuit = list()
		self.pCardNum = list()

		self.interaction = None
		self.ownerId = id

		self.dealerNum = list()
		self.dealerHand = list()
		self.embed = None
		self.msg = None

		self.amntbet = amntbet

		self.doubleDown = Button(bot, label="Double Down", style=nextcord.ButtonStyle.blurple, row=1)
		self.add_item(self.doubleDown)
		self.insurance = Button(bot, label="Insurance", style=nextcord.ButtonStyle.blurple, row=1, disabled=True)
		self.add_item(self.insurance)

		self.insuranceBet = None
	
	async def on_timeout(self):
		self.clear_items()
		await self.interaction.edit_original_message(embed=None, view=self, 
					       content=f"{self.interaction.user.mention}\nYou took too long to respond, staying with your current hand")
		await self.stand()

	async def Start(self, interaction: Interaction):
		self.interaction = interaction
		# generate the starting cards
		self.dealer_first_turn()
		
		self.add_item(Button(self.bot, label="Hit", style=nextcord.ButtonStyle.green))
		self.add_item(Button(self.bot, label="Stand", style=nextcord.ButtonStyle.red))

		self.embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Blackjack")
		file = nextcord.File("./images/bj.png", filename="image.png")
		self.embed.set_thumbnail(url="attachment://image.png")

		await self.player_first_turn()

	async def player_first_turn(self):
		for x in range(0,2):
			# player draws a card
			# if x == 0:
			# 	pDrawnCard = "♦ A"
			# else:
			# 	pDrawnCard = "♦ 10"
			pDrawnCard = self.take_card()
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
			self.pCardNum = self.eval_ace(self.pCardNum)

		# used to make display for all p cards
		pTotal = ""
		for x in self.pCARD:
			pTotal += f"{x} "

		# used to make display for all d cards
		dTotal = ""
		for x in self.dealerHand:
			dTotal += f"{x} "


		self.embed.add_field(name = f"{self.interaction.user.name}'s CARD:", value = f"{pTotal}\n**Score**: {sum(self.pCardNum)}", inline=True)
		self.embed.add_field(name = f"{self.bot.user.name}' CARD", value = f"{self.dealerHand[0]}\n**Score**: {self.dealerNum[0]}\n", inline=True)
		self.embed.add_field(name = "_ _", value = "**Options:** hit or stay", inline=False)
		self.embed.set_footer(text=f"Cards in Deck: {len(self.cards)}")

		botMsg = await self.interaction.send(f"{self.interaction.user.mention}", embed=self.embed, view=self)
		self.msg = await botMsg.fetch()

		if (self.is_blackjack(self.pCardNum)):
			if self.dealerHand[0].split()[1] == "A":
				self.remove_item(self.doubleDown)
				for child in self.children:
					if child.label == "Hit":
						self.remove_item(child)
				await self.interaction.edit_original_message(embed=self.embed, view=self, content=f"{self.interaction.user.mention}\nYou got a blackjack! Dealer has an ace, would you like to take insurance or stand?")
			else:
				await self.stand()
			return 


	async def hit(self, isDoubleDown=False):
		# player draws a card 
		pDrawnCard = self.take_card()
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
		self.pCardNum = self.eval_ace(self.pCardNum)

		# used to make display for all p cards
		pTotal = ""
		for x in self.pCARD:
			pTotal += f"{x} "

		# used to make display for all d cards
		dTotal = ""
		for x in self.dealerHand:
			dTotal += f"{x} "

		self.embed.set_field_at(0, 
			name = f"{self.interaction.user.name}'s CARD:", 
			value = f"{pTotal}\n**Score**: {sum(self.pCardNum)}", 
			inline=True)

		self.embed.set_footer(text=f"Cards in Deck: {len(self.cards)}")

		# ends game if player busted or has 21
		if (self.is_bust(self.pCardNum) or self.is_blackjack(self.pCardNum)):
			if self.is_blackjack(self.pCardNum):
				await self.stand()
			else:
				await self.EndGame()
			return
		if isDoubleDown:
			await self.stand()


	async def stand(self):
		# generate dealer's hand
		self.dealer_turn()
		await self.EndGame()


	async def EndGame(self):
		winner = self.compare_between()
		await self.displayWinner(winner) 


	def take_card(self):
		# if all 52 cards have been used, reset the deck
		if len(self.cards) == 0:
			self.cards = ["♣ A", "♣ 2", "♣ 3", "♣ 4", "♣ 5", "♣ 6", "♣ 7", "♣ 8", "♣ 9", "♣ 10", "♣ Jack", "♣ Queen", "♣ King",
						  "♦ A", "♦ 2", "♦ 3", "♦ 4", "♦ 5", "♦ 6", "♦ 7", "♦ 8", "♦ 9", "♦ 10", "♦ Jack", "♦ Queen", "♦ King",
						  "♥ A", "♥ 2", "♥ 3", "♥ 4", "♥ 5", "♥ 6", "♥ 7", "♥ 8", "♥ 9", "♥ 10", "♥ Jack", "♥ Queen", "♥ King",
						  "♠ A", "♠ 2", "♠ 3", "♠ 4", "♠ 5", "♠ 6", "♠ 7", "♠ 8", "♠ 9", "♠ 10", "♠ Jack", "♠ Queen", "♠ King"]

		randNum = randint(0, len(self.cards)-1)
		drawnCard = self.cards.pop(randNum)

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
		# dDrawnCard = "♦ A"
		for x in range(0, 2):
			# if x == 0:
			# 	dDrawnCard = "♦ A"
			# else:
			# 	dDrawnCard = "♦ 10"
			# else:
			dDrawnCard = self.take_card()
			self.dealerHand.append(dDrawnCard)

			dDrawnCard = dDrawnCard.split()

			if dDrawnCard[1] == "Jack" or dDrawnCard[1] == "Queen" or dDrawnCard[1] == "King":
				dDrawnCard[1] = "10"
			elif dDrawnCard[1] == "A":
				dDrawnCard[1] = "11"
				if x == 0:
					self.insurance.disabled = False # if dealer's FIRST card is Ace, ask player if they want to buy insurance


			self.dealerNum.append(int(dDrawnCard[1]))

			self.dealerNum = self.eval_ace(self.dealerNum)
		
		

	def dealer_turn(self):
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


	def compare_between(self):
		total_player = sum(self.pCardNum)
		total_dealer = sum(self.dealerNum)
		player_bust = self.is_bust(self.pCardNum)
		dealer_bust = self.is_bust(self.dealerNum)
		player_blackjack = self.is_blackjack(self.pCardNum)
		dearler_blackjack = self.is_blackjack(self.dealerNum)

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

	async def displayWinner(self, winner):
		for child in self.children:
			if not child.disabled:
				child.disabled = True
		self.stop()
		await self.msg.edit(view=self)

		user = self.interaction.user
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

		file = None

		moneyToAdd = 0
		if winner == 999: # won by insurance
			moneyToAdd = self.insuranceBet * 3
			# if bought insurance and has blackjack
			if self.is_blackjack(self.pCardNum):
				profitInt = moneyToAdd - self.insuranceBet
			else:
				profitInt = moneyToAdd - self.amntbet - self.insuranceBet
				
			result = "DEALER 21 ON HAND, BUT WON INSURANCE"

			self.embed.color = nextcord.Color(0x23f518)
			file = nextcord.File("./images/insurance.png", filename="image.png")
			
		elif winner == 1:
			moneyToAdd = self.amntbet * 2 
			profitInt = moneyToAdd - self.amntbet
			result = "YOU WON"
			
			self.embed.color = nextcord.Color(0x23f518)
			if sum(self.pCardNum) == 21:
				file = nextcord.File("./images/21.png", filename="image.png")
			else:
				file = nextcord.File("./images/bjwon.png", filename="image.png")

		elif winner == -1:
			moneyToAdd = 0 # nothing to add since loss
			profitInt = -self.amntbet # profit = amntWon - amntbet; amntWon = 0 in this case
			result = "YOU LOST"
			file = nextcord.File("./images/bjlost.png", filename="image.png")


		elif winner == 0:
			moneyToAdd = self.amntbet # add back their bet they placed since it was pushed (tied)
			profitInt = 0 # they get refunded their money (so they don't make or lose money)
			result = "PUSHED"
			file = nextcord.File("./images/bjpushed.png", filename="image.png")

		if file:
			self.embed.set_thumbnail(url="attachment://image.png")

		gameID = await self.bot.get_cog("Economy").addWinnings(self.interaction.user.id, moneyToAdd, giveMultiplier=True, activityName="BJ", amntBet=self.amntbet)
		self.embed.set_field_at(2, name = f"**--- {result} ---**", value = "_ _", inline=False)

		self.embed = await DB.addProfitAndBalFields(self, self.interaction, profitInt, self.embed)

		balance = await self.bot.get_cog("Economy").getBalance(user)
		self.embed = await DB.calculateXP(self, self.interaction, balance - profitInt, self.amntbet, self.embed, gameID)

		# if winner == 999:
		# await self.interaction.send(content=f"{user.mention}", file=file, embed=self.embed)

		# await interaction.send(content=f"{interaction.user.mention}", file=file, embed=self.embed)

		await self.msg.edit(embed=self.embed, view=None)

		await self.bot.get_cog("Totals").addTotals(self.interaction, self.amntbet, moneyToAdd, 1)	
		await self.bot.get_cog("Quests").AddQuestProgress(self.interaction, user, "BJ", profitInt)


class bj(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.cards = ["♣ A", "♣ 2", "♣ 3", "♣ 4", "♣ 5", "♣ 6", "♣ 7", "♣ 8", "♣ 9", "♣ 10", "♣ Jack", "♣ Queen", "♣ King",
					  "♦ A", "♦ 2", "♦ 3", "♦ 4", "♦ 5", "♦ 6", "♦ 7", "♦ 8", "♦ 9", "♦ 10", "♦ Jack", "♦ Queen", "♦ King",
					  "♥ A", "♥ 2", "♥ 3", "♥ 4", "♥ 5", "♥ 6", "♥ 7", "♥ 8", "♥ 9", "♥ 10", "♥ Jack", "♥ Queen", "♥ King",
					  "♠ A", "♠ 2", "♠ 3", "♠ 4", "♠ 5", "♠ 6", "♠ 7", "♠ 8", "♠ 9", "♠ 10", "♠ Jack", "♠ Queen", "♠ King"]

	@nextcord.slash_command(description="Play BlackJack!")
	@commands.bot_has_guild_permissions(send_messages=True, manage_messages=True, embed_links=True, use_external_emojis=True, attach_files=True)
	@cooldowns.cooldown(1, 9, bucket=cooldowns.SlashBucket.author, cooldown_id='blackjack')
	async def blackjack(self, interaction:Interaction, amntbet):
		amntbet = await self.bot.get_cog("Economy").GetBetAmount(interaction, amntbet)

		if amntbet < 100:
			raise Exception("minBet 100")
		
		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, amntbet):
			raise Exception("tooPoor")
		
		view = Blackjack(self.bot, interaction.user.id, self.cards, amntbet)
		await view.Start(interaction)


def setup(bot):
	bot.add_cog(bj(bot))