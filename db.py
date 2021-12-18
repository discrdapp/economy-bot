import discord
from discord.ext import commands
import sqlite3

from math import ceil
from random import randint

import config

class DB(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@staticmethod
	def fetchOne(sql, values: list):
		conn = sqlite3.connect(config.db)

		cursor = conn.execute(sql, values) 
		data = cursor.fetchone()
		conn.close()

		return data

	@staticmethod
	def update(sql, values: list):
		conn = sqlite3.connect(config.db)
		conn.execute(sql, values)
		conn.commit()
		conn.close()

	@staticmethod
	async def calculateXP(self, ctx, initBal, amntBet, embed):
		minBet = initBal * 0.05
		minBet = int(ceil(minBet / 10.0) * 10.0)
		if amntBet >= minBet:
			xp = randint(50, 500)
			embed.set_footer(text=f"Earned {xp} XP!")
			await self.bot.get_cog("XP").addXP(ctx, xp)
		else:
			embed.set_footer(text=f"You have to bet your minimum to earn xp.")
		return embed

	@staticmethod
	async def addProfitAndBalFields(self, ctx, profit, embed):
		balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
		embed.add_field(name="Profit", value=f"{profit}{self.coin}", inline=True)
		embed.add_field(name="Credits", value=f"**{balance}**{self.coin}", inline=True)
		return embed

def setup(bot):
	bot.add_cog(DB(bot))