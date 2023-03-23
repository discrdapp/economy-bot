import nextcord
from nextcord.ext import commands 
from nextcord import Interaction
from nextcord import FFmpegPCMAudio 
from nextcord import Member 
from nextcord.ext.commands import has_permissions, MissingPermissions

import sqlite3
import asyncio

from dataclasses import dataclass

import emojiss as e
import config
from db import DB


class Achievements(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.coin = "<:coins:585233801320333313>"
		self.games = ["Slt", "BJ", "Crsh", "Rltte", "CF", "RPS"]
		self.realGameNames = ["Slots", "Blackjack", "Crash", "Roulette", "Coinflip", "Rock-Paper-Scissors"]
		self.realGameNamesDict = {"Slt": "Slots", "BJ": "Blackjack", "Crsh": "Crash", "Rltte": "Roulette", "CF": "Coinflip", "RPS": "Rock-Paper-Scissors"}
		self.quests = ["Games", "Wins", "Profit"]

	async def AddAchievementProgress(self, interaction:Interaction, user: nextcord.Member, game, type, profit):
		if game:

		else:

		if self.IsAchievementComplete(self.goals[f'{questType}'], questType, user, activeQuest):
			goal = self.GetGoal(questType)

			await self.bot.get_cog("Economy").addWinnings(user.id, 5000)
			await self.bot.get_cog("XP").addXP(interaction, 200)

			await interaction.send(embed=nextcord.Embed(color=0x109D00, title="Achievement Complete!", description=f"Your achivement to {goal} in {self.realGameNamesDict[game]} is now complete!" +
				f"\n5000{self.coin} and 200 XP has been added to your account!\n"))

	async def IsAchievementComplete(self, goal, questType, user: nextcord.Member, activeQuest):
		pass

	async def GiveAchievement(self, interaction:Interaction, user: nextcord.Member, name, level=0:int):
		# if not have achievement

		pass

	async def HasAchievement(self, user: nextcord.Member, name, level=0:int):
		pass


def setup(bot):
	bot.add_cog(Achievements(bot))
