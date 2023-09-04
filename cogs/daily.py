import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import cooldowns, json, time, math

import emojis
from db import DB

class Daily(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.levelReward = [550, 1500, 3000, 7500, 13500, 18500, 24000, 29000, 35000, 42000, 50000]

	@nextcord.slash_command()
	@cooldowns.cooldown(1, 86401, bucket=cooldowns.SlashBucket.author, cooldown_id='daily')
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
		# multiplier = self.bot.get_cog("Multipliers").getMultiplier(interaction.user.id)
		# extraMoney = int(dailyReward * (multiplier - 1))
		logID = await self.bot.get_cog("Economy").addWinnings(userId, dailyReward, giveMultiplier=True, activityName="Daily Reward", amntBet=0)
		# balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		# embed.add_field(name = f"You got {(dailyReward+extraMoney):,} {emojis.coin}", 
						# value = f"You have {balance:,} credits\nMultiplier: {multiplier}x\nExtra Money: {extraMoney:,}", inline=False)
		embed.description = f"You got {dailyReward:,} {emojis.coin}"
		embed.set_footer(text=f"Log ID: {logID}")
		embed = await DB.addProfitAndBalFields(self, interaction, dailyReward, embed)
		await interaction.send(embed=embed)



	async def getDailyReward(self, interaction:Interaction):
		dailyReward = DB.fetchOne("SELECT DailyReward FROM Economy WHERE DiscordID = ?;", [interaction.user.id])[0]
		return dailyReward

def setup(bot):
	bot.add_cog(Daily(bot))