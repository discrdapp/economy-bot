import nextcord
from nextcord.ext import commands
from nextcord import Interaction
from nextcord import FFmpegPCMAudio 
from nextcord import Member 

from nextcord.ui import View, Select

import random

class Minesweeper(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.gridSize = 12
		self.mineCount = 20
		self.mines = []
		self.grid = []
		self.selectCount = 0
		self.view = None
		self.revealed = []

	def GenerateSelects(self):
		numOptions = []
		for x in range(0, 12):
			numOptions.append(nextcord.SelectOption(label=f"{x}", value=x))

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
		x = Select(options=letterOptions)
		y = Select(options=numOptions)

		return x,y

	async def GameOver(self, msg, won=bool):
		embed = nextcord.Embed(color=1768431, title=f"Mine")
		embed.add_field(name="Minesweeper", value=self.draw_grid(True))

		await msg.clear_reactions()
		await msg.edit(embed=embed, view=None)
		print("Gameover!")



	@nextcord.slash_command()	
	async def minesweeper(self, interaction:Interaction):
		self.mines = []
		self.grid = []
		self.selectCount = 0
		self.view = None
		self.revealed = []
		self.flags = []

		embed = nextcord.Embed(color=1768431, title=f"Mine")

		self.GenerateBoard()
		self.GenerateMines()
		self.SetCounts()

		embed.add_field(name="Minesweeper", value=self.draw_grid())

		# async def my_callback(interaction):
		# 	self.selectCount += 1
		# 	if self.selectCount > 1:
		# 		self.view.stop()

		def check(reaction, user):
			return user == interaction.user and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '🚩')

		async def ResetEmbed(fetchMsg):
			self.selectCount = 0
			self.view = View()

			x, y = self.GenerateSelects()
			self.view.add_item(x)
			self.view.add_item(y)

			# x.callback = my_callback
			# y.callback = my_callback
			if fetchMsg:
				await fetchMsg.remove_reaction("✅", interaction.user)
				await fetchMsg.remove_reaction("🚩", interaction.user)

			return x, y

		x, y = await ResetEmbed(None)

		msg = await interaction.send(embed=embed, view=self.view)
		fetchMsg = await msg.fetch()
		await fetchMsg.add_reaction("✅")
		await fetchMsg.add_reaction("🚩")


		while True:
			# await self.view.wait()
			try:
				reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
			except Exception as e:
				print(e)

			if not x.values or not y.values:
				await fetchMsg.remove_reaction("✅", interaction.user)
				await fetchMsg.remove_reaction("🚩", interaction.user)
				continue

			xValue = int(x.values[0])
			yValue = int(y.values[0])

			if str(reaction.emoji) == "✅":
				if self.grid[xValue][yValue] == "*":
					await self.GameOver(fetchMsg, False)
					return
				if (xValue, yValue) in self.flags:
					self.flags.remove((xValue, yValue))	
				self.RevealCell(xValue, yValue)
				if len(self.revealed) + self.mineCount >= self.gridSize*self.gridSize:
					await self.GameOver(fetchMsg, True) 
					return
			elif str(reaction.emoji) == "🚩" and (xValue, yValue) not in self.revealed:
				self.flags.append((xValue, yValue))
			embed.set_field_at(0, name="Minesweeper", value=self.draw_grid())


			x, y = await ResetEmbed(fetchMsg)

			await msg.edit(embed=embed, view=self.view)



		# Define the function to draw the grid
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


def setup(bot):
	bot.add_cog(Minesweeper(bot))