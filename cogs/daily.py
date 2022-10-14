import nextcord
from nextcord.ext import commands 
from nextcord import Interaction
from nextcord import FFmpegPCMAudio 
from nextcord import Member 
from nextcord.ext.commands import has_permissions, MissingPermissions

import sqlite3
import asyncio

import json
import time
import math

import config
from db import DB

class Daily(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.levelReward = [550, 1500, 3000, 7500, 13500, 18500, 24000, 29000, 35000, 42000, 50000]
		self.coin = "<:coins:585233801320333313>"

	@nextcord.slash_command()
	async def daily(self, interaction:Interaction):
		userId = interaction.user.id

		if not await self.bot.get_cog("Economy").accCheck(interaction.user):
			await self.bot.get_cog("Economy").start(interaction, interaction.user)
		else:
			with open(r"rewards.json", 'r') as f:
				rewards = json.load(f)

			if (str(userId) in rewards) and ('daily' in rewards[f'{userId}']):
				if rewards[f'{userId}']['daily'] > time.time():
					waittime = rewards[f'{userId}']['daily'] - time.time()
					await interaction.response.send_message(f"Please wait **{math.floor(waittime/3600)}h {math.floor((waittime/60) % 60)}m** to use this again!")
					return

			elif not str(userId) in rewards:
				rewards[f'{userId}'] = dict()
			rewards[f'{userId}']['daily'] = time.time() + 86400

			with open(r"rewards.json", 'w') as f:
				json.dump(rewards, f, indent=4)


		dailyReward = await self.getDailyReward(interaction)
		multiplier = self.bot.get_cog("Economy").getMultiplier(interaction.user)
		extraMoney = int(dailyReward * (multiplier - 1))
		await self.bot.get_cog("Economy").addWinnings(userId, dailyReward + extraMoney)
		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		embed = nextcord.Embed(color=1768431)
		embed.add_field(name = f"You got {dailyReward} (+{extraMoney}) {self.coin}", 
						value = f"You have {balance} credits\nMultiplier: {multiplier}x\nExtra Money: {extraMoney}", inline=False)
		await interaction.response.send_message(embed=embed)



	async def getDailyReward(self, interaction:Interaction):
		dailyReward = DB.fetchOne("SELECT DailyReward FROM Economy WHERE DiscordID = ?;", [interaction.user.id])[0]
		return dailyReward

def setup(bot):
	bot.add_cog(Daily(bot))