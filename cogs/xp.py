import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import math, cooldowns

import emojis
from db import DB

class XP(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.XPtoLevelUp = []
		for x in range(0,101):
			self.XPtoLevelUp.append(5000 + (x * 500)) 


	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='level')
	async def level(self, interaction:Interaction):
		getRow = DB.fetchOne(f"SELECT XP, TotalXP, Level FROM Economy WHERE DiscordID = ?;", [interaction.user.id])
		level = getRow[2]
		xp = getRow[0]
		try:
			requiredXP = self.XPtoLevelUp[level]
		except:
			requiredXP = xp

		totalXP = getRow[1]

		multiplier, expiration = self.bot.get_cog("Multipliers").getMultiplierAndExpiration(interaction.user.id)

		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		minBet = balance * 0.05
		minBet = int(math.ceil(minBet / 10.0) * 10.0)

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name}' Casino | Level")
		embed.add_field(name = "Level", value = f"You are level **{level:,}**", inline=True)
		embed.add_field(name = "XP / Next Level", value = f"**{xp:,}** / **{requiredXP:,}**", inline=True)
		embed.add_field(name = "Minimum Bet", value = f"**{minBet:,}**{emojis.coin}", inline=True)
		embed.add_field(name = "Total XP", value = f"**{totalXP:,}**", inline=True)
		embed.add_field(name = "XP Until Level Up", value = f"**{(requiredXP - xp):,}**", inline=True)
		embed.add_field(name = "Multiplier", value = f"**{multiplier}x**", inline=False)
		if expiration:
			embed.add_field(name = "Expires In", value = f"**{expiration}x**", inline=True)
		await interaction.send(embed=embed)


	async def addXP(self, interaction:Interaction, xp):
		DB.update("UPDATE Economy SET XP = XP + ?, totalXP = totalXP + ? WHERE DiscordID = ?;", [xp, xp, interaction.user.id])
		await self.levelUp(interaction, interaction.user.id)
	
	async def addLevel(self, discordId, level):
		DB.update("UPDATE Economy SET Level = Level + ? WHERE DiscordID = ?;", [level, discordId])


	async def levelUp(self, interaction:Interaction, discordid):
		getRow = DB.fetchOne("SELECT XP, Level FROM Economy WHERE DiscordID = ?;", [discordid])
		xp = getRow[0]
		level = getRow[1]

		if xp >= self.XPtoLevelUp[level]:

			embed = nextcord.Embed(color=1768431, title="Level Up!")
			file = nextcord.File("./images/levelup.png", filename="image.png")

			credits = (level+1)*5000

			DB.update("UPDATE Economy SET XP = XP - ?, Level = Level + 1, Credits = Credits + ? WHERE DiscordID = ?;", [self.XPtoLevelUp[level], credits, discordid])
			embed.add_field(name = f"{interaction.user.name}, you Leveled Up!", value = "_ _", inline=False)

			embed.set_thumbnail(url="attachment://image.png")
			embed.add_field(name = f"Credits Bonus!", value = f"**{credits}**{emojis.coin}")
			await interaction.channel.send(file=file, embed=embed)
			# await interaction.send(file=file, embed=embed)


	def getLevel(self, discordid):
		level = DB.fetchOne("SELECT Level FROM Economy WHERE DiscordID = ?;", [discordid])[0]
		return level
	
	def IsHighEnoughLevel(self, discordId, levelRequirement):
		return self.getLevel(discordId) >= levelRequirement


		
def setup(bot):
	bot.add_cog(XP(bot))