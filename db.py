import nextcord
from nextcord.ext import commands 
from nextcord import Interaction
from nextcord import FFmpegPCMAudio 
from nextcord import Member 
from nextcord.ext.commands import has_permissions, MissingPermissions

import sqlite3

from math import ceil
from random import randint

import config

class DB(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.coin = "<:coins:585233801320333313>"

	@staticmethod
	def fetchOne(sql, values: list=None):
		conn = sqlite3.connect(config.db)

		if values:
			cursor = conn.execute(sql, values)
		else:
			cursor = conn.execute(sql)
		data = cursor.fetchone()

		conn.close()

		return data

	@staticmethod
	def fetchAll(sql, values: list=None):
		conn = sqlite3.connect(config.db)

		if values:
			cursor = conn.execute(sql, values)
		else:
			cursor = conn.execute(sql)
		data = cursor.fetchall() 

		conn.close()

		return data

	@staticmethod
	def insert(sql, values: list=None):
		conn = sqlite3.connect(config.db)
		conn.execute(sql, values)
		conn.commit()
		conn.close()


	@staticmethod
	def update(sql, values: list=None):
		conn = sqlite3.connect(config.db)
		if values:
			conn.execute(sql, values)
		else:
			conn.execute(sql)
		conn.commit()
		conn.close()

	@staticmethod
	def delete(sql, values: list=None):
		conn = sqlite3.connect(config.db)
		if values:
			conn.execute(sql, values)
		else:
			conn.execute(sql)
		conn.commit()
		conn.close()

	@staticmethod
	async def calculateXP(self, interaction:Interaction, initBal, amntBet, embed):
		minBet = initBal * 0.05
		minBet = int(ceil(minBet / 10.0) * 10.0)
		if amntBet >= minBet:
			xp = randint(50, 500)
			embed.set_footer(text=f"Earned {xp:,} XP!")
			await self.bot.get_cog("XP").addXP(interaction, xp)
		else:
			embed.set_footer(text=f"You have to bet your minimum to earn xp.")
		return embed

	@staticmethod
	async def addProfitAndBalFields(self, interaction, profit:int, embed, redEmbed=False):
		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		multiplier = self.bot.get_cog("Multipliers").getMultiplier(interaction.user.id)

		name = "Result"
		if profit > 0 and redEmbed != True:
			embed.color = nextcord.Color(0x23f518)
		else:
			embed.color = nextcord.Color(0xff2020)
		if profit >= 0:
			profit = int(float(profit) * (multiplier))
			embed.add_field(name=name, value=f"+{profit:,} (+{int(profit * (multiplier - 1))}){self.coin}", inline=True)
		else:
			embed.add_field(name=name, value=f"{profit:,}{self.coin}", inline=True)

		embed.add_field(name="Credits", value=f"{balance:,}{self.coin}", inline=True)
		return embed

allItemNames = DB.fetchAll('SELECT Name FROM Items;')
allItemNamesList = [item for sublist in allItemNames for item in sublist]
buyableItems = DB.fetchAll('SELECT * FROM Items WHERE Buyable = 1;')
buyableItemNames = DB.fetchAll("SELECT Name FROM Items WHERE Buyable = 1;")
buyableItemNamesList = [item for sublist in buyableItemNames for item in sublist]
usableItemNames = DB.fetchAll("SELECT Name FROM Items WHERE Type = 'Usable';")
usableItemNamesList = [item for sublist in usableItemNames for item in sublist]


def setup(bot):
	bot.add_cog(DB(bot))