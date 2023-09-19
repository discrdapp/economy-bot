# Stock market crash game

import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import cooldowns, asyncio, random

import emojis
from db import DB


def GetPrintableMsg(msg:str):
	return msg.replace("_", "\_")

class Modal(nextcord.ui.Modal):
	def __init__(self):
		super().__init__(title="Guess the Phrase", timeout=60)
		self.add_item(nextcord.ui.TextInput("Enter the phrase below", placeholder="It is not case-sensitive"))
	
	async def callback(self, interaction:Interaction):
		assert self.view is not None
		view: View = self.view
		if interaction.user.id != view.userId:
			await interaction.send(f"This is not your game", ephemeral=True)
			return

		await interaction.response.defer()
		self.stop()

class Button(nextcord.ui.Button):
	def __init__(self, label, style):
		super().__init__(label=label, style=style)
	
	async def callback(self, interaction: Interaction):
		assert self.view is not None
		view: View = self.view

		if interaction.user.id != view.userId:
			await interaction.send(f"This is not your game", ephemeral=True)
			return


		await view.GuessThePhrase(interaction)



class View(nextcord.ui.View):
	def __init__(self, bot:commands.bot.Bot, userId):
		super().__init__()
		self.bot = bot

		self.userId = userId
		self.interaction = None
		self.embed = None

		self.remainingLetters = "abcdefghijklmnopqrstuvwxy"

		self.attempts = 5

		self.modal = Modal()

		self.sentence = random.choice(["vote for us to get a usable multiplier",
								 "i am the best bot out there",
								 "make sure to check out all my games",
								 "thank you for choosing me",
								 "invest in your favorite stocks today",
								 "the spooky season is among us",
								 "i do not have a gambling problem",
								 "counting cards should be allowed",
								 "blackjack is my favorite game"])

		# self.sentence = "a bc"
		
		self.hiddenMsg = ""
		for letter in self.sentence:
			if letter == ' ':
				self.hiddenMsg += " "
			else:
				self.hiddenMsg += "_"

		self.select = None
		self.button = Button("Guess the Phrase", nextcord.ButtonStyle.blurple)

	
	def RefreshSelect(self):
		options = list()
		for letter in self.remainingLetters:
			options.append(nextcord.SelectOption(label=f"{letter}"))
		self.select = nextcord.ui.Select(options=options, min_values=1, max_values=1)
		self.select.callback = self.selectCallback

	async def selectCallback(self, interaction:Interaction):
		value = interaction.data['values'][0]
		self.remainingLetters = self.remainingLetters.replace(value, "")


		if value in self.sentence:
			for pos in range(0, len(self.sentence)):
				if value == self.sentence[pos]:
					self.hiddenMsg = self.hiddenMsg[:pos] + value + self.hiddenMsg[pos+1:]
			if "_" not in self.hiddenMsg:
				await self.GameOver(interaction, True)
				return
		else:
			self.attempts -= 1
			if self.attempts == 0:
				await self.GameOver(interaction, False)
				return


		self.embed.description = f"{self.attempts} attempts left\n{GetPrintableMsg(self.hiddenMsg)}"

		self.remove_item(self.children[0])
		self.remove_item(self.children[0])
		self.RefreshSelect()

		self.add_item(self.select)
		self.add_item(self.button)
		await interaction.edit(embed=self.embed, view=self)
	
	async def GuessThePhrase(self, interaction:Interaction):
		await interaction.response.send_modal(modal=self.modal)
		await self.modal.wait()
		guess:str = self.modal.children[0].value
		if guess and guess.lower() == self.sentence.lower():
			await self.GameOver(interaction, True)
			return
		else:
			await interaction.send("Incorrect guess!", ephemeral=True)
			self.attempts -= 1
			self.embed.description = f"{self.attempts} attempts left\n{GetPrintableMsg(self.hiddenMsg)}"
			await interaction.edit(embed=self.embed)

	
	async def GameOver(self, interaction:Interaction, won:bool):
		try:
			await interaction.response.defer()
		except:
			pass
		for child in self.children:
			child.disabled = True
		
		if won:
			self.embed.description = f"{self.attempts} attempts left\n{GetPrintableMsg(self.sentence)}\n\nYou win!"
			moneyToAdd = 2500
			self.embed.color = nextcord.Color(0x23f518)
			msg = f"+2,500{emojis.coin}"
		else:
			self.embed.description = f"{self.attempts} attempts left\n{GetPrintableMsg(self.hiddenMsg)}\n\nYou ran out of attempts!"
			moneyToAdd = 0
			self.embed.color = nextcord.Color(0xff2020)
			msg = f"0{emojis.coin}"

		gameID = None
		if moneyToAdd > 0:
			gameID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, moneyToAdd, giveMultiplier=False, activityName="Hangman", amntBet=0)
		
		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)

		self.embed.add_field(name="Money Added", value=msg, inline=True)
		self.embed.add_field(name="Credits", value=f"{balance:,}{emojis.coin}", inline=True)

		if gameID:
			self.embed.set_footer(text=f"GameID: {gameID}")

		await self.interaction.edit(view=self, embed=self.embed)
	
	async def Start(self, interaction:Interaction):
		self.RefreshSelect()
		self.add_item(self.select)
		self.add_item(self.button)

		self.embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Hangman")

		self.embed.description = f"{self.attempts} attempts left\n{GetPrintableMsg(self.hiddenMsg)}"

		self.interaction = await interaction.send(view=self, embed=self.embed)




class Hangman(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot


	@nextcord.slash_command()
	@commands.bot_has_guild_permissions(send_messages=True, embed_links=True, use_external_emojis=True)
	@cooldowns.cooldown(1, 300, bucket=cooldowns.SlashBucket.author, cooldown_id='hangman')
	async def hangman(self, interaction:Interaction, ):
		view = View(self.bot, interaction.user.id)
		await view.Start(interaction)



def setup(bot):
	bot.add_cog(Hangman(bot))