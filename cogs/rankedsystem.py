import nextcord
from nextcord.ext import commands, tasks
from nextcord import Interaction, Color

import cooldowns, emojis, config
from random import randrange
from db import DB
from cogs.util import PrintProgress


class RankedSystem(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot

		self.ranks:list = ["Noobie Gambler", 
		   "Mediocre Gambler", 
		   "Competent Gambler", 
		   "Proficient Gambler", 
		   "Professional Gambler",
		   "Expert Gambler",
		   "Prestigious Gambler",
		   "Cracked Gambler"]
	
	@commands.Cog.listener()
	async def on_ready(self):
		if not self.SendRanks.is_running():
			self.SendRanks.start()
	
	@tasks.loop(hours=6)
	async def SendRanks(self):
		try:
			rankData = [0]*len(self.ranks)
			chnl = self.bot.get_channel(config.channelIDForRanks)
			msg = await chnl.fetch_message(config.messageIDForRanks)

			newMsg = ""
			data = DB.fetchAll("SELECT Rank, Count(1) FROM RankedUsers GROUP BY Rank;")

			for eachRank in data:
				rankData[eachRank[0]] = eachRank[1]
		
			for x in range(len(rankData)):
				newMsg += f"{self.ranks[x]}: {rankData[x]}\n"

			await msg.edit(content=newMsg)
		except Exception as e:
			print(f"Exception in SendRanks\n{e}")
			
		
	
	def GetRankPointsHighest(self, user:nextcord.Member):
		data = DB.fetchOne("SELECT Rank, CasinoPoints, HighestEarned FROM RankedUsers WHERE DiscordID = ?;", [user.id])

		if not data:
			DB.insert('INSERT OR IGNORE INTO RankedUsers(DiscordID) VALUES (?);', [user.id])
			return 0, 0, 0

		return data[0], data[1], data[2]

	
	async def AddRankedPoints(self, interaction:Interaction, won:bool):
		pointsToAdd = randrange(101, 200)
		if not won:
			pointsToAdd *= -1
		
		rank, currPoints, highestEarned = self.GetRankPointsHighest(interaction.user)

		newPoints = currPoints + pointsToAdd

		# demote, but at lowest rank
		if newPoints < 0 and rank == 0:
			newPoints = 0
		# demote
		elif newPoints < 0:
			rank -= 1
			newPoints += 1000

			embed = nextcord.Embed(color=Color.red(), title=f"{self.bot.user.name} | Demoted")
			embed.description = f"You have been demoted to {self.ranks[rank]}"
			embed.set_footer(text="Check your rank with /rank")

			await interaction.send(embed=embed)

		# promote, but not at highest rank
		elif newPoints > 1000 and rank != len(self.ranks)-1:
			rank += 1
			newPoints -= 1000

			msg = ""
			embed = nextcord.Embed(color=Color.green(), title=f"{self.bot.user.name} | Promoted")
			if rank > highestEarned:
				reward = 10000*rank
				await self.bot.get_cog("Economy").addWinnings(interaction.user.id, reward, activityName="Ranked Up", amntBet=0)
				msg = f"\n+{reward:,}{emojis.coin}"
			
			embed.description = f"You have been promoted to {self.ranks[rank]}{msg}"
			embed.set_footer(text="Check your rank with /rank")

			await interaction.send(embed=embed)

		if rank > highestEarned:
			DB.update("UPDATE RankedUsers SET Rank = ?, CasinoPoints = ?, HighestEarned = ? WHERE DiscordID = ?", [rank, newPoints, rank, interaction.user.id])
		else:
			DB.update("UPDATE RankedUsers SET Rank = ?, CasinoPoints = ? WHERE DiscordID = ?", [rank, newPoints, interaction.user.id])


	@nextcord.slash_command(description="Check your rank")
	@commands.bot_has_guild_permissions(send_messages=True, use_external_emojis=True, attach_files=True)
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='rank')
	async def rank(self, interaction:Interaction, user:nextcord.User=None):
		if not user:
			user = interaction.user
		# self.RegisterUser(user)

		rank, points, _ = self.GetRankPointsHighest(user)

		embed = nextcord.Embed(color=Color.blurple(), title=f"{self.bot.user.name} | Rank")
		embed.description = f"You are {self.ranks[rank]}, with {points} Casino Points\n{await PrintProgress(points/1000)}"
		if rank == len(self.ranks)-1:
			embed.set_footer(text="You are at the highest rank!")
		await interaction.send(embed=embed)


def setup(bot):
	bot.add_cog(RankedSystem(bot))