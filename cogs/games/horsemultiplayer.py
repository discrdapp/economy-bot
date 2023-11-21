import nextcord
from nextcord.ext import commands 
from nextcord import Interaction, InteractionMessage

import cooldowns, asyncio, random

import emojis
from db import DB

import time


class JoinGameButton(nextcord.ui.Button):
	def __init__(self, label, style):
		super().__init__(label=label, style=style)
	
	async def callback(self, interaction:Interaction):
		assert self.view is not None
		view:JoinGameView = self.view

		if self.label == "Join":
			balance = await view.bot.get_cog("Economy").getBalance(interaction.user)

			if interaction.user.id in [player.id for player in view.players.keys()]:
				await interaction.send("You have already joined the game", ephemeral=True)
				return
			if view.amntbet > balance:
				await interaction.send(f"You need at least {view.amntbet:,} to join this game", ephemeral=True)
				return
			view.players[interaction.user] = None

			await interaction.send("You joined the game!", ephemeral=True)
			await view.UpdateJoinMsg()
		elif self.label == "Start":
			if interaction.user.id != view.owner.id:
				await interaction.send(f"Only {view.owner.mention} can start the game", ephemeral=True)
				return
			if len(view.players.keys()) == 1:
				await interaction.send("Cannot start game with just you!", ephemeral=True)
				return
			view.stop()


class JoinGameView(nextcord.ui.View):
	def __init__(self, bot, owner, amntbet):
		super().__init__(timeout=180)
		joinGameButton = JoinGameButton("Join", nextcord.ButtonStyle.blurple)
		startGameButton = JoinGameButton("Start", nextcord.ButtonStyle.green)
		self.add_item(joinGameButton)
		self.add_item(startGameButton)

		self.bot = bot
		self.owner = owner
		self.amntbet = amntbet
		self.players = dict()
		self.players[owner] = None

		self.msg = None

	async def on_timeout(self):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Horse Multiplayer")
		embed.description = f"{self.owner.mention} took too long to start game. Game cancelled."
		embed.set_footer(text="Your balance was not changed")
		await self.msg.edit(embed=embed, view=None)
	

	async def UpdateJoinMsg(self):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Horse Multiplayer")

		usersInGame = ""
		for player in self.players.keys():
			usersInGame += f"{player.mention}\n"
		embed.description = f"Waiting for players...\nPeople currently in game:\n{usersInGame}"

		await self.msg.edit(embed=embed)



class Button(nextcord.ui.Button):
	def __init__(self, label, style, row=1):
		super().__init__(label=label, style=style, row=row)
	
	async def callback(self, interaction: Interaction):
		assert self.view is not None
		view: View = self.view

		if interaction.user.id not in [player.id for player in list(view.players.keys())]:
			await interaction.send("You are not apart of this game!", ephemeral=True)
			return

		if self.label == "Start":
			if any(elem is None for elem in view.players.values()):
				# lst = [key.mention for key,val in view.players.items() if val is None]
				msg = ""
				for key,val in view.players.items():
					if val is None: msg += f"{key.mention} "
				await interaction.send(f"Waiting for {msg}", ephemeral=True)
				return
			if view.owner.id != interaction.user.id:
				await interaction.send(f"Only {view.owner.mention} can start the game", ephemeral=True)
			else:
				try:
					await interaction.response.defer()
				except:
					pass
				await view.HorseRace(interaction)
		else:
			view.players[interaction.user] = self.label
			await view.UpdateHorseSelections()

			try:
				await interaction.response.defer()
			except:
				pass


class View(nextcord.ui.View):
	def __init__(self, bot:commands.bot.Bot, owner, players:dict, interaction:Interaction, amntbet:int):
		super().__init__()
		self.bot = bot
		self.owner = owner
		self.players = players
		self.interaction = interaction

		self.amntbet = amntbet

		self.embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Horse")

		msg = ""
		for player in self.players.keys():
			msg += f"{player.mention} has not picked yet\n"
		self.embed.description = msg

		self.raceTrack = None

		self.horses = list()
	
	async def UpdateHorseSelections(self):
		msg = ""
		for key, val in self.players.items():
			if val is None:
				msg += f"{key.mention} has not picked yet\n"
			else:
				msg += f"{key.mention} is betting on {val}\n"
		self.embed.description = msg
		await self.msg.edit(embed=self.embed)


	def GetDisplay(self, horseTrack):
		msg = ""
		for element in horseTrack:
			msg += f"{element}"
		return msg

	def GetFullDisplay(self, horses):
		msg = "-------------------------------------------------"
		x = 0
		for horse in horses:
			if x == 0: indicator = ":red_circle:"
			elif x == 1: indicator = ":blue_circle:"
			elif x == 2: indicator = ":green_circle:"
			elif x == 3: indicator = ":white_circle:"
			else: indicator = ":warning:"
			msg += f"\n{indicator}|"
			msg += self.GetDisplay(horse)
			x += 1
		self.raceTrack = "-------------------------------------------------"
		return msg


	
	async def Start(self):
		self.add_item(Button("Red", nextcord.ButtonStyle.red))
		self.add_item(Button("Blue", nextcord.ButtonStyle.blurple))
		self.add_item(Button("Green", nextcord.ButtonStyle.green))
		self.add_item(Button("Grey", nextcord.ButtonStyle.grey))

		self.add_item(Button("Start", nextcord.ButtonStyle.green, row=2))

		self.raceTrack = "-------------------------------------------------"

		for x in range(4):
			self.horses.append(list())
		for x in range(4):	
			for char in self.raceTrack:
				self.horses[x].append(char)
			self.horses[x].append(":horse_racing:")
		
		self.raceTrack = self.GetFullDisplay(self.horses)

		self.msg = await self.interaction.send(content=self.raceTrack, view=self, embed=self.embed)
		# self.msg = await msg.fetch()

	async def HorseRace(self, interaction:Interaction):
		await self.msg.edit(view=None)

		notWon = True
		winner = None
		while notWon:
			for _ in range(20):
				raceToMove = random.randint(0, 4)
				# raceToMove = 0
				if raceToMove == 0:
					self.horses[0] = self.horses[0][1:]
				elif raceToMove == 1:
					self.horses[1] = self.horses[1][1:]
				elif raceToMove == 2:
					self.horses[2] = self.horses[2][1:]
				elif raceToMove == 3:
					self.horses[3] = self.horses[3][1:]
				
				if self.horses[0][0] != "-" or self.horses[1][0] != "-" or self.horses[2][0] != "-" or self.horses[3][0] != "-":
					if self.horses[0][0] != "-":
						winner = "Red"
					elif self.horses[1][0] != "-":
						winner = "Blue"
					elif self.horses[2][0] != "-":
						winner = "Green"
					elif self.horses[3][0] != "-":
						winner = "Grey"
					notWon = False
					break


			await self.msg.edit(content=self.GetFullDisplay(self.horses), view=None, embed=self.embed)

			time.sleep(0.5)
		await self.EndGame(interaction, winner)

	async def EndGame(self, interaction:Interaction, winner):

		gameIDsMsg = ""
		wonMsg = ""
		for player, value in self.players.items():
			if value == winner:
				wonMsg += f"{player.mention} "
				moneyToAdd = self.amntbet * 4
			else:
				moneyToAdd = 0
			gameID = await self.bot.get_cog("Economy").addWinnings(player.id, moneyToAdd, giveMultiplier=False, activityName="Multiplayer Horse", amntBet=self.amntbet)
			
			gameIDsMsg += f"{player.mention}'s GameID: {gameID}\n"

		if wonMsg: wonMsg += "won!\n"
		else: wonMsg = "No one bet on the winning horse\n"
		self.embed.description = wonMsg + "\n" + gameIDsMsg
		await self.msg.edit(embed=self.embed)

class HorseMultiplayer(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot

	@nextcord.slash_command(description="Play Multiplayer Horse Race Betting!")
	@commands.bot_has_guild_permissions(send_messages=True, manage_messages=True, embed_links=True, use_external_emojis=True, attach_files=True)
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='mhorse')
	async def multiplayerhorse(self, interaction:Interaction, amntbet:int):

		if amntbet < 100:
			raise Exception("minBet 100")
		
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Horse Multiplayer")

		joinGameView = JoinGameView(self.bot, interaction.user, amntbet)

		embed.description = f"Waiting for players...\nPeople currently in game:\n{interaction.user.mention}"
		msg = await interaction.send(embed=embed, view=joinGameView)
		joinGameView.msg = msg

		if await joinGameView.wait():
			return
		await msg.delete()

		view = View(self.bot, interaction.user, joinGameView.players, interaction, amntbet)

		await view.Start()


def setup(bot):
	bot.add_cog(HorseMultiplayer(bot))