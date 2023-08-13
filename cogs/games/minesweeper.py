import nextcord
from nextcord.ext import commands
from nextcord import Interaction

import random

class TicTacToeButton(nextcord.ui.Select['TicTacToe']):
	def __init__(self, options, placeholder):
		super().__init__(options=options, placeholder=placeholder, min_values=1, max_values=1)
	
	# This function is called whenever this particular button is pressed
	# This is part of the "meat" of the game logic
	async def callback(self, interaction: nextcord.Interaction):
		assert self.view is not None
		view: TicTacToe = self.view

		if super().placeholder.startswith("Select a letter"):
			view.x = int(self.values[0])
		else:
			view.y = int(self.values[0])


		# if view.optionsSelected == 1:
		# 	view.optionsSelected = 0
			
		# 	x = view.children[0].values[0]
		# 	y = view.children[1].values[0]

		# 	view.RevealCell
		# 	await interaction.response.edit_message(view=view)


# This is our actual board View
class TicTacToe(nextcord.ui.View):
	def __init__(self, interaction, bot, minecount:int):
		super().__init__()
		self.bot:commands.bot.Bot = bot
		
		self.gridSize = 12
		self.mineCount = minecount
		self.mines = []
		self.grid = []
		self.selectCount = 0
		self.view = None
		self.revealed = []
		self.flags = []
		numOptions = []

		self.x = None
		self.y = None

		self.optionsSelected = 0

		self.ownerId = interaction.user.id

		letterOptions = [
			nextcord.SelectOption(label="A", value = 0),
			nextcord.SelectOption(label="B", value = 1),
			nextcord.SelectOption(label="C", value = 2),
			nextcord.SelectOption(label="D", value = 3),
			nextcord.SelectOption(label="E", value = 4),
			nextcord.SelectOption(label="F", value = 5),
			nextcord.SelectOption(label="G", value = 6),
			nextcord.SelectOption(label="H", value = 7),
			nextcord.SelectOption(label="I", value = 8),
			nextcord.SelectOption(label="J", value = 9),
			nextcord.SelectOption(label="K", value = 10),
			nextcord.SelectOption(label="L", value = 11)
		]
		self.add_item(TicTacToeButton(letterOptions, "Select a letter"))

		for x in range(0, 12):
			numOptions.append(nextcord.SelectOption(label=f"{x}", value=x))
		self.add_item(TicTacToeButton(numOptions, "Select a number"))

		self.GenerateBoard()
		self.GenerateMines()
		self.SetCounts()
	
	async def Start(self, interaction):
		grid = self.draw_grid()
		msg = await interaction.send(content=grid, view=self)
		fetchMsg = await msg.fetch()

		# TicTacToe(interaction, minecount)
		def check(reaction, user):
			return user == interaction.user and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '🚩')
		
		
		while True:
			self.x = None
			self.y = None

			await fetchMsg.add_reaction("✅")
			await fetchMsg.add_reaction("🚩")
			reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)

			if not self.x or not self.y:
				await interaction.send("You need to select a letter and a number!", ephemeral=True)
				continue
			elif (self.x, self.y) in self.revealed:
				await interaction.send("You already revealed that cell!", ephemeral=True)
				continue
			else:
				if (self.x, self.y) in self.flags:
					self.flags.remove((self.x, self.y))
				elif (self.x, self.y) not in self.revealed:
					if str(reaction.emoji) == "✅":
						if self.grid[self.x][self.y] == "*":
							await self.GameOver(fetchMsg, False)
							return
						self.RevealCell(self.x, self.y)
						if len(self.revealed) + self.mineCount >= self.gridSize*self.gridSize:
							await self.GameOver(fetchMsg, True) 
							return
					elif str(reaction.emoji) == "🚩" and (self.x, self.y) not in self.revealed:
							self.flags.append((self.x, self.y))

			# embed.set_field_at(0, name="Minesweeper", value=self.draw_grid())

			await fetchMsg.clear_reactions()
			await fetchMsg.edit(content=self.draw_grid())


	async def GameOver(self, msg, won=bool):
		embed = nextcord.Embed(color=1768431, title=f"Mine")
		embed.add_field(name="Minesweeper", value=self.draw_grid(True))

		await msg.clear_reactions()
		await msg.edit(embed=embed, view=None)
	def draw_grid(self, isGameOver=False):
		msg = "⬛"
		for x in range(0, self.gridSize):
			msg += f"{self.getNumEmoji(x)}"
		msg += "\n"
		for x in range(0, self.gridSize):
			msg += f"{self.getLetterEmoji(x)}"
			for y in range(0, self.gridSize):
				if isGameOver or (x,y) in self.revealed:
					if self.grid[x][y] == "*": msg += "💣"
					else: 
						if self.grid[x][y] <= 0:
							msg += f"{self.getNumEmoji(0)}"
						else:
							msg += f"{self.getNumEmoji(self.grid[x][y])}"
				elif (x,y) in self.flags:
					msg += "🚩"
				else:
					msg += "⬜"
			msg += "\n"

		return msg

	def SetCounts(self):
		for x in range(self.gridSize):
			for y in range(self.gridSize):
				if self.grid[x][y] == "*":
					continue
				self.grid[x][y] = self.count_adjacent(x, y)

	# Define a function to check for adjacent mines
	def count_adjacent(self, x, y):
		count = 0
		for i in range(-1, 2):
			for j in range(-1, 2):
				if i == 0 and j == 0:
					continue
				if self.is_valid(x+i, y+j) and self.grid[x+i][y+j] == '*':
					count += 1
		return count


	def reveal_adjacent(self, x, y):
		for i in range(-1, 2):
			for j in range(-1, 2):
				if i == 0 and j == 0:
					continue
				if self.is_valid(x+i, y+j) and self.grid[x+i][y+j] == ' ':
					count = self.count_adjacent(x+i, y+j)
					self.grid[x+i][y+j] = count
					if count == 0:
						self.reveal_adjacent(x+i, y+j)

	def RevealCell(self, row, column):
		if (row, column) in self.revealed:
			return True # i made this one
		self.revealed.append((row, column))
		if self.grid[row][column] == "*":
			return True # was false
		elif self.grid[row][column] > 0:
			return True
		else:
			self.grid[row][column] = -2
			if row > 0:
				self.RevealCell(row - 1, column)
				if column > 0:
					self.RevealCell(row - 1, column - 1)
				if column < self.gridSize - 1:
					self.RevealCell(row - 1, column + 1)
			if column > 0:
				self.RevealCell(row, column - 1)
			if column < self.gridSize - 1:
				self.RevealCell(row, column + 1)
			if row < self.gridSize - 1:
				self.RevealCell(row + 1, column)
				if column > 0:
					self.RevealCell(row + 1, column - 1)
				if column < self.gridSize - 1:
					self.RevealCell(row + 1, column + 1)
			return True

	def is_valid(self, x, y):
		if x < 0 or y < 0: return False
		if x+1 > self.gridSize or y+1 > self.gridSize: return False
		return True

	def GenerateBoard(self):
		for i in range(self.gridSize):
			row = []
			for j in range(self.gridSize):
				row.append(' ')
			self.grid.append(row)

	def GenerateMines(self):
		# Place the mines randomly
		while len(self.mines) < self.mineCount:
			x = random.randint(0, self.gridSize-1)
			y = random.randint(0, self.gridSize-1)
			if (x,y) not in self.mines:
				self.mines.append((x,y))
				self.grid[x][y] = '*'


	def getNumEmoji(self, num):
		if num == "":return ""
		elif num == 0:return ":zero:"
		elif num == 1:return ":one:"
		elif num == 2:return ":two:"
		elif num == 3:return ":three:"
		elif num == 4:return ":four:"
		elif num == 5:return ":five:"
		elif num == 6:return ":six:"
		elif num == 7:return ":seven:"
		elif num == 8:return ":eight:"
		elif num == 9:return ":nine:"
		elif num == 10:return ":keycap_ten:"
		elif num == 11:return ":one::one:"
		elif num == 12:return ":one::two:"
		elif num == 13:return ":one::three:"
		elif num == 14:return ":one::four:"
		elif num == 15:return ":one::five:"

	def getLetterEmoji(self, num):
		if num == "":return ""
		elif num == 0:return "🇦"
		elif num == 1:return "🇧"
		elif num == 2:return "🇨"
		elif num == 3:return "🇩"
		elif num == 4:return "🇪"
		elif num == 5:return "🇫"
		elif num == 6:return "🇬"
		elif num == 7:return "🇭"
		elif num == 8:return "🇮"
		elif num == 9:return "🇯"
		elif num == 10:return "🇰"
		elif num == 11:return "🇱"
		elif num == 12:return "🇲"
		elif num == 13:return "🇳"
		elif num == 14:return "🇴"
		elif num == 15:return "🇵"

	

class Minesweeper(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
	
	@nextcord.slash_command()
	async def play(self, interaction, minecount:int = nextcord.SlashOption(required=True,name="Number of Mines", choices=[x for x in range(20, 141, 10)])):
		ttt = TicTacToe(interaction, self.bot, minecount)
		await ttt.Start(interaction)

def setup(bot):
	bot.add_cog(Minesweeper(bot))