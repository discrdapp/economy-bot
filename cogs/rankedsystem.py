import nextcord
from nextcord.ext import commands, tasks, application_checks
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
		
		self.guild = None

		# actual server
		self.roleIDs = {"Noobie Gambler": 1198730494578266163, 
				  "Mediocre Gambler": 1198730592183931000, 
				  "Competent Gambler": 1198730733024448602, 
				  "Proficient Gambler": 1198730805606875187, 
				  "Professional Gambler": 1198731426095439942, 
				  "Expert Gambler": 1198730831783542877, 
				  "Prestigious Gambler": 1198730889279058081, 
				  "Cracked Gambler": 1198730915598319647}
		
		# test server
		# self.roleIDs = {"Noobie Gambler": 1199091278252609587, 
		# 		  "Mediocre Gambler": 1199086647535468584, 
		# 		  "Competent Gambler": 1199091394468393072, 
		# 		  "Proficient Gambler": 1199091422687674388, 
		# 		  "Professional Gambler": 1199091469470937128, 
		# 		  "Expert Gambler": 1199091499695095902, 
		# 		  "Prestigious Gambler": 1199091537456414830, 
		# 		  "Cracked Gambler": 1199091566216757329}
	
	@commands.Cog.listener()
	async def on_ready(self):
		if not self.SendRanks.is_running():
			self.SendRanks.start()

		self.guild = await self.bot.fetch_guild(config.adminServerID)
	
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
			
	
	async def UpdateDiscordRole(self, user:nextcord.User, roleToAdd, roleToRemove):
		member = await self.guild.fetch_member(user.id)
		if not member:
			return
		await member.add_roles(self.guild.get_role(self.roleIDs[roleToAdd]))
		await member.remove_roles(self.guild.get_role(self.roleIDs[roleToRemove]))
		
	
	def GetRankPointsHighest(self, user:nextcord.Member):
		data = DB.fetchOne("SELECT Rank, CasinoPoints, HighestEarned FROM RankedUsers WHERE DiscordID = ?;", [user.id])

		if not data:
			DB.insert('INSERT OR IGNORE INTO RankedUsers(DiscordID) VALUES (?);', [user.id])
			return 0, 0, 0

		return data[0], data[1], data[2]
	
	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def forceaddrankedpoints(self, interaction:Interaction, won:bool):
		if won:
			await interaction.send("Adding points")
		else:
			await interaction.send("Removing points")
		await self.AddRankedPoints(interaction, won)

	
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

			await self.UpdateDiscordRole(interaction.user, self.ranks[rank], self.ranks[rank+1])

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

			await self.UpdateDiscordRole(interaction.user, self.ranks[rank], self.ranks[rank-1])

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