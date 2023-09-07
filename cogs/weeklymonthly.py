import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import json, time, math, cooldowns

import emojis

class WeeklyMonthly(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.levelReward = [550, 1500, 3000, 7500, 13500, 18500, 24000, 29000, 35000, 42000, 50000]

	@nextcord.slash_command()
	@cooldowns.cooldown(1, 120, bucket=cooldowns.SlashBucket.author)
	async def weekly(self, interaction:Interaction):
		userId = interaction.user.id

		with open(r"rewards.json", 'r') as f:
			rewards = json.load(f)

		embed = nextcord.Embed(color=1768431)

		if (str(userId) in rewards) and ('weekly' in rewards[f'{userId}']):
			if rewards[f'{userId}']['weekly'] > time.time():
				waittime = rewards[f'{userId}']['weekly'] - time.time()
				embed.description = f"Please wait **{math.floor(waittime/86400)}d {math.floor((waittime/3600) % 24)}h {math.floor((waittime/60) % 60)}m** to use this again!"
				await interaction.send(embed=embed)
				return

		elif not str(userId) in rewards:
			rewards[f'{userId}'] = dict()
		rewards[f'{userId}']['weekly'] = time.time() + 604800

		with open(r"rewards.json", 'w') as f:
			json.dump(rewards, f, indent=4)



		weeklyReward = 12500
		multiplier = self.bot.get_cog("Multipliers").getMultiplier(interaction.user.id)
		extraMoney = int(weeklyReward * (multiplier - 1))
		logID = await self.bot.get_cog("Economy").addWinnings(userId, weeklyReward, giveMultiplier=True, activityName="Weekly Reward", amntBet=0)
		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		embed.add_field(name = f"You got {(weeklyReward+extraMoney):,} {emojis.coin}", 
						value = f"You have {balance:,} credits\nMultiplier: {multiplier}x\nExtra Money: {extraMoney:,}", inline=False)
		embed.set_footer(text=f"Log ID: {logID}")
		await interaction.send(embed=embed)



	@nextcord.slash_command()
	@cooldowns.cooldown(1, 120, bucket=cooldowns.SlashBucket.author)
	async def monthly(self, interaction:Interaction):
		userId = interaction.user.id

		with open(r"rewards.json", 'r') as f:
			rewards = json.load(f)

		embed = nextcord.Embed(color=1768431)
		
		if (str(userId) in rewards) and ('monthly' in rewards[f'{userId}']):
			if rewards[f'{userId}']['monthly'] > time.time():
				waittime = rewards[f'{userId}']['monthly'] - time.time()
				embed.description = f"Please wait **{math.floor(waittime/86400)}d {math.floor((waittime/3600) % 24)}h {math.floor((waittime/60) % 60)}m** to use this again!"
				await interaction.send(embed=embed)
				return

		elif not str(userId) in rewards:
			rewards[f'{userId}'] = dict()
		rewards[f'{userId}']['monthly'] = time.time() + 2592000

		with open(r"rewards.json", 'w') as f:
			json.dump(rewards, f, indent=4)




		monthlyReward = 36000
		multiplier = self.bot.get_cog("Multipliers").getMultiplier(interaction.user.id)
		extraMoney = int(monthlyReward * (multiplier - 1))
		logID = await self.bot.get_cog("Economy").addWinnings(userId, monthlyReward, giveMultiplier=True, activityName="Monthly Reward", amntBet=0)
		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		embed = nextcord.Embed(color=1768431)
		embed.add_field(name = f"You got {(monthlyReward+extraMoney):,} {emojis.coin}", 
						value = f"You have {balance:,} credits\nMultiplier: {multiplier}x\nExtra Money: {extraMoney:,}", inline=False)
		embed.set_footer(text=f"Log ID: {logID}")
		await interaction.send(embed=embed)

def setup(bot):
	bot.add_cog(WeeklyMonthly(bot))