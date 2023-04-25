import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import json, time, math

from db import DB

class Daily(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.levelReward = [550, 1500, 3000, 7500, 13500, 18500, 24000, 29000, 35000, 42000, 50000]
		self.coin = "<:coins:585233801320333313>"

	@nextcord.slash_command()
	async def daily(self, interaction:Interaction):
		userId = interaction.user.id

		with open(r"rewards.json", 'r') as f:
			rewards = json.load(f)

		embed = nextcord.Embed(color=1768431)
		if (str(userId) in rewards) and ('daily' in rewards[f'{userId}']):
			if rewards[f'{userId}']['daily'] > time.time():
				waittime = rewards[f'{userId}']['daily'] - time.time()
				embed.description = f"Please wait **{math.floor(waittime/3600)}h {math.floor((waittime/60) % 60)}m** to use this again!"
				await interaction.send(embed=embed)
				return

		elif not str(userId) in rewards:
			rewards[f'{userId}'] = dict()
		rewards[f'{userId}']['daily'] = time.time() + 86400

		with open(r"rewards.json", 'w') as f:
			json.dump(rewards, f, indent=4)


		dailyReward = await self.getDailyReward(interaction)
		multiplier = self.bot.get_cog("Multipliers").getMultiplier(interaction.user)
		extraMoney = int(dailyReward * (multiplier - 1))
		await self.bot.get_cog("Economy").addWinnings(userId, dailyReward + extraMoney)
		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		embed.add_field(name = f"You got {(dailyReward+extraMoney):,} {self.coin}", 
						value = f"You have {balance:,} credits\nMultiplier: {multiplier}x\nExtra Money: {extraMoney:,}", inline=False)
		await interaction.send(embed=embed)



	async def getDailyReward(self, interaction:Interaction):
		dailyReward = DB.fetchOne("SELECT DailyReward FROM Economy WHERE DiscordID = ?;", [interaction.user.id])[0]
		return dailyReward

def setup(bot):
	bot.add_cog(Daily(bot))