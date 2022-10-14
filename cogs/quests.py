import nextcord
from nextcord.ext import commands 
from nextcord import Interaction
from nextcord import FFmpegPCMAudio 
from nextcord import Member 
from nextcord.ext.commands import has_permissions, MissingPermissions

from typing import Optional

import sqlite3
import asyncio

from dataclasses import dataclass

import emojiss as e
import config
from db import DB

# @dataclass
# class GameResults:
# 	game : str
# 	profit : float

class Quests(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.coin = "<:coins:585233801320333313>"
		self.games = ["Slt", "BJ", "Crsh", "Rltte", "CF", "RPS"]
		self.realGameNames = ["Slots", "Blackjack", "Crash", "Roulette", "Coinflip", "Rock-Paper-Scissors"]
		self.realGameNamesDict = {"Slt": "Slots", "BJ": "Blackjack", "Crsh": "Crash", "Rltte": "Roulette", "CF": "Coinflip", "RPS": "Rock-Paper-Scissors"}
		self.quests = ["Games", "Wins", "Profit"]

		self.goals = {"Games": 30, "Wins": 20, "Profit": 50000}
		self.objectives = {"Games": "play 30 games", "Wins": "win 20 games", "Profit": f"earn a profit of 50,000{self.coin}"}

	@nextcord.slash_command()
	async def quests(self, interaction:Interaction):
		pass

	@quests.subcommand()
	async def info(self, interaction:Interaction, gameselection:Optional[int]=nextcord.SlashOption(name="game", required=False,
																			choices={"Slots":1, "Blackjack":2, "Crash":3, 
																			"Roulette":4, "Coinflip":5, "Rock-Paper-Scissors":6})):
		if gameselection:
			embed=nextcord.Embed(color=0x109D00, title=f"{self.realGameNames[gameselection-1]}",
					description = f"{gameselection}1. Play 30 games\n{gameselection}2. Win 20 games\n{gameselection}3. Earn a profit of 50,000{self.coin}")
			embed.set_footer(text=f"Type /quests start to start a quest")

			await interaction.response.send_message(embed=embed)
		
			return
		currQuest = self.GetQuest(interaction.user)
		if not self.InQuestsDB(interaction.user) or not currQuest:
			embed=nextcord.Embed(color=0x109D00, title="Quests", description="1. Slots\n2. Blackjack\n3. Crash\n4. Roulette\n5. Coinflip\n6. Rock-Paper-Scissors")
			embed.set_footer(text=f"ALL quests give 5000 credits and 200 XP!")
			await interaction.response.send_message(embed=embed)
			# embed = nextcord.Embed(color=0xFF0000, description="You do not have any active quests")
			await interaction.response.send_message(embed=nextcord.Embed(color=0xFF0000, description="You do not have any active quests"))
		elif currQuest:
			questStr = await self.Decode(interaction, currQuest)
			await interaction.response.send_message(embed=nextcord.Embed(color=0x109D00, description=f"{questStr}\n"))

	@quests.subcommand()
	async def start(self, interaction:Interaction, game=nextcord.SlashOption(name="gamechoice", required=True,
																					choices={"Slots":"1", "Blackjack":"2", "Crash":"3", 
																					"Roulette":"4", "Coinflip":"5", "Rock-Paper-Scissors":"6"}),
													quest=nextcord.SlashOption(name="questchoice", required=True,
																					choices={"Play 30 games": "1", "Win 20 games": "2", "Earn a profit of 50,000": "3"})):
		questselection = game + quest

		newQuest = str(self.games[int(questselection[0])-1] + self.quests[int(questselection[1])-1])

		embed = nextcord.Embed(color = 0x109D00)
		if not self.InQuestsDB(interaction.user): # user not in database
			conn = sqlite3.connect(config.db)
			sql = "INSERT INTO Quests(DiscordID, ActiveQuest) VALUES (?, ?);"
			conn.execute(sql, (interaction.user.id, newQuest))
			conn.commit()
			embed.description = f"You have successfully started your first quest! Good luck."

		elif not self.GetQuest(interaction.user): # user not currently have active quest
			DB.update("UPDATE Quests SET ActiveQuest = ? WHERE DiscordID = ?;", [newQuest, interaction.user.id])
			embed.description = f"You have successfully started a new quest! Good luck."

		else: # user has active quest
			embed.color = 0xFF0000
			embed.description = f"You must first complete your current quest before you can begin a new one."
			embed.set_footer(text=f"Type `/quests cancel` to cancel your current quest")

		await interaction.response.send_message(embed=embed)

	@quests.subcommand()
	async def cancel(self, interaction:Interaction):
		currQuest = self.GetQuest(interaction.user)
		if not self.InQuestsDB(interaction.user) or not currQuest:
			await interaction.response.send_message(embed=nextcord.Embed(color=0xFF0000, description="You do not have any active quests"))
			return

		DB.update("UPDATE Quests SET ActiveQuest = NULL, Games = 0, Wins = 0, Profit = 0 WHERE DiscordID = ?;", [interaction.user.id])
		await interaction.response.send_message(embed=nextcord.Embed(color=0x109D00, description=f"You have successfully canceled your current quest"))




	async def Decode(self, interaction:Interaction, activeQuest:str):
		pos = 0
		for x in self.games:
			if x in activeQuest:
				game = x
				break
			pos += 1
		

		rest = activeQuest[len(game):]

		goal = self.GetGoal(rest)

		total = self.goals[rest]

		amnt = DB.fetchOne("SELECT " + rest + " FROM Quests WHERE DiscordID = ? and ActiveQuest = ?;", [interaction.user.id, activeQuest])[0]
		return f"Your current quest is to {goal} in {self.realGameNamesDict[game]}.\nProgress: {amnt}/{total} ({round((amnt/total)*100, 2)}%)\n{await self.PrintProgress(interaction, amnt/total)}"


	# game must be "Slt", "BJ", "Crsh", "Rltte", "CF", "RPS"
	# start of quest must also be one of those
	async def AddQuestProgress(self, interaction:Interaction, user: nextcord.Member, game, profit): 
		if not self.InQuestsDB(user):
			return

		activeQuest = self.GetQuest(user)
		if not activeQuest:
			return

		if game not in activeQuest: # if game played is not user's active quest game
			return

		questType = activeQuest[len(game):]
		
		if questType == "Games":
			fieldToSet = "Games = Games + 1"
		else:
			if profit <= 0:
				return

			if questType == "Wins":
				fieldToSet = "Wins = Wins + 1"
			elif questType == "Profit":
				fieldToSet = "Profit = Profit + " + str(profit) 


		DB.update("UPDATE Quests SET " + fieldToSet + " WHERE DiscordID = ? and ActiveQuest = ?", [user.id, activeQuest])

		if self.IsQuestComplete(self.goals[f'{questType}'], questType, user, activeQuest):
			goal = self.GetGoal(questType)

			await self.bot.get_cog("Economy").addWinnings(user.id, 5000)
			await self.bot.get_cog("XP").addXP(interaction, 200)

			await interaction.followup.send(embed=nextcord.Embed(color=0x109D00, title="Quest Complete!", description=f"Your quest to {goal} in {self.realGameNamesDict[game]} is now complete!" +
				f"\n5000{self.coin} and 200 XP has been added to your account!\n"))
			DB.update("UPDATE Quests SET ActiveQuest = NULL, " + questType + " = 0 WHERE DiscordID = ? and ActiveQuest = ?;", [user.id, activeQuest])



	def InQuestsDB(self, user: nextcord.Member):
		# checks if they already have a wallet in database
		userAcc = DB.fetchOne("SELECT 1 FROM Quests WHERE DiscordID = ?;", [user.id])
		if userAcc: # getRow will not be None if account is found, therefor return True
			return True
		
		return False


	def GetQuest(self, user: nextcord.Member):
		quest = DB.fetchOne("SELECT ActiveQuest FROM Quests WHERE DiscordID = ?;", [user.id])
		if quest:
			return quest[0]
		return None

	def GetQuestStatus(self, questType, user: nextcord.Member, activeQuest):
		quest = DB.fetchOne("SELECT " + questType + " FROM Quests WHERE DiscordID = ? and ActiveQuest = ?;", [user.id, activeQuest])[0]
		return quest

	def IsQuestComplete(self, goal, questType, user: nextcord.Member, activeQuest):
		currProgress = DB.fetchOne("SELECT " + questType + " FROM Quests WHERE DiscordID = ? and ActiveQuest = ?;", [user.id, activeQuest])[0]

		if currProgress >= goal:
			return True
		return False

	def GetGoal(self, questType):
		if questType == "Games":
			return "play 30 games"
		if questType == "Wins":
			return "win 20 games"
		if questType == "Profit":
			return f"earn a profit of 50,000{self.coin}"

	async def PrintProgress(self, interaction:Interaction, percentFilled):
		if percentFilled <= 0.03:
			percentFilled = 0
		elif percentFilled < 0.1:
			percentFilled = 1
		elif percentFilled >= 0.9:
			percentFilled = 9
		else:
			percentFilled = round(percentFilled * 10)

		progress = ""
		for x in range(1, 11):
			if x == 1: # left side 
				if x <= percentFilled:
					progress += e.tlf
				else:
					progress += e.tl
			elif x == 10: # right side
				if x <= percentFilled:
					progress += e.trf
				else:
					progress += e.tr
			else: # middle
				if x <= percentFilled:
					progress += e.tf
				else:
					progress += e.t

		progress += "\n"
		for x in range(1, 11):
			if x == 1: # left side 
				if x <= percentFilled:
					progress += e.blf
				else:
					progress += e.bl
			elif x == 10: # right side
				if x <= percentFilled:
					progress += e.brf
				else:
					progress += e.br
			else: # middle
				if x <= percentFilled:
					progress += e.bf
				else:
					progress += e.b

		return progress


def setup(bot):
	bot.add_cog(Quests(bot))