# economy-related stuff like betting and gambling, etc.

import discord
from discord.ext import commands
import pymysql
import asyncio
import config
import math

from random import randint

class XP(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		# self.XPtoLevelUp = [5000, 5500, 6000, 6500, 7000, 7500, 8000, 8500, 9000, 9500, 10000, 10500, 11000, 11500, 12000, 12500, 13000, 13500, 14000]
		self.XPtoLevelUp = []
		# self.levelReward = []
		for x in range(0,101):
			self.XPtoLevelUp.append(5000 + (x * 500)) 
		# for x in range(0,101):
		# 	self.levelReward.append((x + 1) * 500) 
		self.coin = "<:coins:585233801320333313>"


	@commands.command(aliases=['xp'], pass_context=True)
	@commands.cooldown(1, 1, commands.BucketType.user)
	async def level(self, ctx):
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))
		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()

		sql = f"""SELECT XP, TotalXP, Level, Multiplier
				  FROM Economy
				  WHERE DiscordID = '{ctx.author.id}';""" # LevelReward
		cursor.execute(sql)
		db.commit()
		getRow = cursor.fetchone()

		multiplier = getRow[3]
		level = getRow[2]
		xp = getRow[0]
		requiredXP = self.XPtoLevelUp[level]
		#levelReward = getRow[0]
		progress = round((xp / requiredXP) * 100)
		totalXP = getRow[1]

		db.close()

		coin = "<:coins:585233801320333313>"
		balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
		minBet = balance * 0.05
		minBet = int(math.ceil(minBet / 10.0) * 10.0)

		embed = discord.Embed(color=1768431, title=f"{self.bot.user.name}' Casino | Level")
		embed.add_field(name = "Level", value = f"You are level **{level}**", inline=True)
		embed.add_field(name = "XP / Next Level", value = f"**{xp}** / **{requiredXP}**", inline=True)
		embed.add_field(name = "Minimum Bet", value = f"**{minBet}**{coin}", inline=True)
		embed.add_field(name = "Total XP", value = f"**{totalXP}**", inline=True)
		embed.add_field(name = "XP Until Level Up", value = f"**{requiredXP - xp}**", inline=True)
		embed.add_field(name = "Multiplier", value = f"**{multiplier}x**", inline=False)
		await ctx.send(embed=embed)


	async def addXP(self, ctx, xp):
		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()

		sql = f"""Update Economy
				  SET XP = XP + {xp}
				  WHERE DiscordID = '{ctx.author.id}';"""
		cursor.execute(sql)
		db.commit()

		await self.levelUp(ctx, db, ctx.author.id)

		sql = f"""Update Economy
				  SET totalXP = totalXP + {xp}
				  WHERE DiscordID = '{ctx.author.id}';"""
		cursor.execute(sql)
		db.commit()
		db.close()


	async def levelUp(self, ctx, db, discordId):
		cursor = db.cursor()
		sql_check = f"""SELECT XP, Level
						FROM Economy
						WHERE DiscordID = '{discordId}';"""
		cursor.execute(sql_check)
		db.commit()
		getRow = cursor.fetchone()
		xp = getRow[0]
		level = getRow[1]

		if xp >= self.XPtoLevelUp[level]:
			count = 0

			embed = discord.Embed(color=1768431, title="Level Up!")
			file = discord.File("./images/levelup.png", filename="image.png")
			multiplier = self.bot.get_cog("Economy").getMultiplier(ctx.author)

			credits = (level+1)*5000

			if multiplier == 1:
				choiceMult = randint(1, 10)

				if choiceMult <= 7:
					newMultiplier = 1.25
				elif choiceMult <= 9:
					newMultiplier = 1.5
				else:
					newMultiplier = 2
				sql = f"""Update Economy
						  SET XP = XP - {self.XPtoLevelUp[level]}, Level = Level + 1, Credits = Credits + {credits}, Multiplier = {newMultiplier}
						  WHERE DiscordID = '{discordId}';""" 
				cursor.execute(sql)
				sql = f"""CREATE EVENT IF NOT EXISTS event{str(ctx.author.id)}
						  ON SCHEDULE AT CURRENT_TIMESTAMP + INTERVAL 2 HOUR
						  DO UPDATE justingraham_db.Economy SET Multiplier = 1;"""
				cursor.execute(sql)
				embed.add_field(name = f"{ctx.author.name}, you Leveled Up!", value = f"You received a {newMultiplier}x multiplier for 2 hours!", inline=False)
			else:
				sql = f"""Update Economy
						  SET XP = XP - {self.XPtoLevelUp[level]}, Level = Level + 1, Credits = Credits + {credits}
						  WHERE DiscordID = '{discordId}';""" 
				cursor.execute(sql)
				embed.add_field(name = f"{ctx.author.name}, you Leveled Up!", value = "_ _", inline=False)

			db.commit()
			embed.set_thumbnail(url="attachment://image.png")
			embed.add_field(name = f"Credits Bonus!", value = f"**{credits}**{self.coin}")
			await ctx.send(file=file, embed=embed)


	async def getLevel(self, discordId):
		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()

		sql = f"""SELECT Level
				  FROM Economy
				  WHERE DiscordID = '{discordId}';"""
		cursor.execute(sql)
		db.commit()
		getRow = cursor.fetchone()
		db.close()
		level = getRow[0]
		return level


		
def setup(bot):
	bot.add_cog(XP(bot))