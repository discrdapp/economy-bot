import nextcord
from nextcord import Color, Interaction
from nextcord.ext import commands, menus

import cooldowns

import emojis
from db import DB

from cogs.util import PrintProgress


class DisplayAchievements(menus.ListPageSource):
	def __init__(self, data):
		super().__init__(data, per_page=5)
		

	async def format_page(self, menu, entries):
		embed = nextcord.Embed(color=1768431, title=f"The Casino | Achievements")

		for x in range(0, len(entries)):
			name = f"{entries[x][0]}"


			# achievements that dont have progress
			if entries[x][2] == 1:
				if not entries[x][3]:
					value = f"{entries[x][1]}\n"
					value += await PrintProgress(0)
				else:
					value = f"{entries[x][1]}\n**Unlocked!**\n"
					value += await PrintProgress(1)


			elif not entries[x][3]:
				value = f"{entries[x][1]}\n0/{entries[x][2]}\n"
				value += await PrintProgress(0)
			else:
				progress = entries[x][3]
				if progress == -1:
					value = f"{entries[x][1]}\n**Unlocked!**\n"
					progress = entries[x][2]
				else:
					print(progress)
					value = f"{entries[x][1]}\n{progress}/{entries[x][2]}\n"
				value += await PrintProgress(progress/int(entries[x][2]))
			embed.add_field(name=name, value=value, inline=False)
		
		embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
		return embed

class Achievements(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot

		self.achievementCount = DB.fetchOne("SELECT COUNT(*) FROM AchievementList;")[0]

		self.bjAchievementIDs = DB.fetchAll("SELECT ID FROM AchievementList WHERE Activity = 'Blackjack';")
		self.cfAchievementIDs = DB.fetchAll("SELECT ID FROM AchievementList WHERE Activity = 'Coinflip';")
		self.crashAchievementIDs = DB.fetchAll("SELECT ID FROM AchievementList WHERE Activity = 'Crash';")
		self.dondAchievementIDs = DB.fetchAll("SELECT ID FROM AchievementList WHERE Activity = 'Dond';")
		self.horseAchievementIDs = DB.fetchAll("SELECT ID FROM AchievementList WHERE Activity = 'Horse';")
		self.minesAchievementIDs = DB.fetchAll("SELECT ID FROM AchievementList WHERE Activity = 'Mines';")
		self.pokerAchievementIDs = DB.fetchAll("SELECT ID FROM AchievementList WHERE Activity = 'Poker';")
		self.rouletteAchievementIDs = DB.fetchAll("SELECT ID FROM AchievementList WHERE Activity = 'Roulette';")
		self.rpsAchievementIDs = DB.fetchAll("SELECT ID FROM AchievementList WHERE Activity = 'rockpaperscissors';")
		self.slotsAchievementIDs = DB.fetchAll("SELECT ID FROM AchievementList WHERE Activity = 'Slots';")
	
	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='achievements')
	async def achievements(self, interaction:Interaction):
		data = DB.fetchAll("""SELECT AL.Name, AL.Description, AL.Goal, AP.Progress 
								FROM AchievementList as AL LEFT OUTER JOIN AchievementProgress as AP ON AL.ID = AP.ID 
								AND AP.DiscordID = ? WHERE AL.Showable = 1;""", [interaction.user.id])

		pages = menus.ButtonMenuPages(
			source=DisplayAchievements(data),
			clear_buttons_after=True,
			style=nextcord.ButtonStyle.primary,
		)
		await pages.start(interaction=interaction, ephemeral=True)

		# get all of achievements, and combine it with all of user's earned/progressing ones 

	async def EarnProgressAchievement(self, interaction:Interaction, discordId, achievementIDs):
		strIDs = ','.join([str(y) for x in achievementIDs for y in x])
		progress = DB.fetchAll(f"""SELECT AL.ID, AL.Name, AL.Reward 
						 FROM AchievementProgress as AP JOIN AchievementList as AL ON AL.ID = AP.ID 
						 WHERE AP.Progress >= AL.Goal AND AP.DiscordID = {discordId} AND AP.ID in ({strIDs}) AND AP.Progress != -1;""")

		if not progress:
			print("returning")
			return
		# achievement: ID, Name
		for achievement in progress:
			DB.update("UPDATE AchievementProgress SET Progress = -1 WHERE DiscordID = ? AND ID = ?;", [discordId, achievement[0]])
			if achievement[2] > 0:
				await self.bot.get_cog("Economy").addWinnings(discordId, achievement[2], activityName=f"Earned achievement#{achievement[0]}", amntBet=0)

			await self.SendEarnedAchievementMsg(interaction, achievement[1], achievement[2])
	
	async def FindAchievementIDWithDesc(self, activity, desc):
		achievementID = DB.fetchOne(f"SELECT ID FROM AchievementList WHERE Activity = '{activity}' AND Description LIKE '%{desc}%'")
		if not achievementID:
			return None
		return achievementID[0]

	async def EarnAchievementByID(self, interaction:Interaction, discordId, achievementID):
		alreadyHasAchievement = DB.fetchOne("SELECT 1 FROM AchievementProgress WHERE DiscordID = ? AND ID = ?;", [discordId, achievementID])
		print(alreadyHasAchievement)
		if alreadyHasAchievement:
			return
		achievement = DB.fetchOne("SELECT Name, Reward FROM AchievementList WHERE ID = ?;", [achievementID])
		if not achievement:
			return
		DB.insert("INSERT INTO AchievementProgress VALUES(?, ?, ?)", [discordId, achievementID, -1])

		await self.SendEarnedAchievementMsg(interaction, achievement[0], achievement[1])

	async def SendEarnedAchievementMsg(self, interaction:Interaction, name, reward):
		embed = nextcord.Embed(color=Color.green(), title=f"{self.bot.user.name} | Achievement Earned!")
		
		if reward:
			embed.description = f"You unlocked an Achievement:\n**{name}**\n**Reward:** {reward}{emojis.coin}"
		else:
			embed.description = f"You unlocked an Achievement:\n**{name}**"
		embed.set_footer(text="Check all your /achievements")

		await interaction.send(embed=embed)


	async def AddAchievementProgress(self, interaction:Interaction, activity, data, discordId):
		DB.insert("INSERT OR IGNORE INTO AchievementProgress SELECT ?, ID, 0 FROM AchievementList WHERE Activity = ? AND Goal != 1", [discordId, activity])

		# results will be dict... starting with amount bet, then results
		if activity == "Blackjack":
			# amntBet | won? | isBlackjack
			gameIDs = await self.ProcessBlackjackProgress(interaction, data, discordId)
			pass
		elif activity == "Coinflip":
			# amntBet | won? | sidepicked
			gameIDs = await self.ProcessCoinflipProgress(interaction, data, discordId)
		elif activity == "Crash":
			# amntBet | won? | crashedAt
			gameIDs = await self.ProcessCrashProgress(interaction, data, discordId)
		elif activity == "Dond":
			# amntBet | won? | caseCount | pickedOwnCaseTrueOrFalse
			gameIDs = await self.ProcessDondProgress(interaction, data, discordId)
		elif activity == "Horse":
			# amntBet | won? | horsePicked
			gameIDs = await self.ProcessHorseProgress(interaction, data, discordId)
		elif activity == "Mines":
			# amntBet | won? | numberOfMines | numberOfClicks
			gameIDs = await self.ProcessMinesProgress(interaction, data, discordId)
		elif activity == "Poker":
			# amntBet | won? | if won, won with
			gameIDs = await self.ProcessPokerProgress(interaction, data, discordId)
		elif activity == "Roulette":
			# amntBet | won? | numberpicked | high/low | color | parity
			gameIDs = await self.ProcessRouletteProgress(interaction, data, discordId)
		elif activity == "rockpaperscissors":
			# amntBet | won? | sidepicked | opponentpicked
			gameIDs = await self.ProcessRPSProgress(interaction, data, discordId)
		elif activity == "Slots":
			# amntBet | won? | if win, 2 or 3 fruit
			gameIDs = await self.ProcessSlotsProgress(interaction, data, discordId)
		
		if gameIDs:
			await self.EarnProgressAchievement(interaction, discordId, gameIDs)

	async def ProcessBlackjackProgress(self, interaction:Interaction, data, discordId):
		# ID 1 = blackjack 21 times 
		# ID 2 = blackjack 3 times in a row
		# if won with blackjack
		if data[2]:
			DB.update("UPDATE AchievementProgress SET Progress = Progress + 1 WHERE DiscordID = ? AND (ID = 201 OR ID = 202) AND Progress != -1", [discordId])

		else:
			# Win 3 games in a row. if lost, reset it 
			DB.update("UPDATE AchievementProgress SET Progress = 0 WHERE DiscordID = ? AND ID = 202 AND Progress != -1", [discordId])
			return None # return since no progress possible to be gained

		return self.bjAchievementIDs

	async def ProcessCoinflipProgress(self, interaction:Interaction, data, discordId):
		return self.cfAchievementIDs

	async def ProcessCrashProgress(self, interaction:Interaction, data, discordId):
		return self.crashAchievementIDs

	async def ProcessDondProgress(self, interaction:Interaction, data, discordId):
		return self.dondAchievementIDs

	async def ProcessHorseProgress(self, interaction:Interaction, data, discordId):
		return self.horseAchievementIDs

	async def ProcessMinesProgress(self, interaction:Interaction, data, discordId):
		# amntBet | won? | numberOfMines | numberOfClicks
		return self.minesAchievementIDs

	async def ProcessPokerProgress(self, interaction:Interaction, data, discordId):
		# amntBet | won? | if won, won with
		if data[1]:
			strIDs = ','.join([str(y) for x in self.pokerAchievementIDs for y in x])
			achievementID = DB.fetchOne(f"SELECT ID FROM AchievementLIST WHERE ID IN ({strIDs}) AND Description LIKE '%{data[2]}%'")[0]
			await self.EarnAchievementByID(interaction, discordId, achievementID)

			count = DB.fetchOne(f"""SELECT COUNT(*) 
					   FROM AchievementProgress 
					   WHERE DiscordID = {discordId} AND ID IN ({strIDs}) AND Description LIKE 'Win a game with %'""")[0]
			if count == 10:
				await self.EarnAchievementByID(800)

		return self.pokerAchievementIDs

	async def ProcessRouletteProgress(self, interaction:Interaction, data, discordId):
		return self.rouletteAchievementIDs

	async def ProcessRPSProgress(self, interaction:Interaction, data, discordId):
		return self.rpsAchievementIDs
	
	async def ProcessSlotsProgress(self, interaction:Interaction, data, discordId):
		# if won
		if data[1]:
			DB.update("UPDATE AchievementProgress SET Progress = Progress + 1 WHERE DiscordID = ? AND ID = 900 AND Progress != -1", [discordId])


		return self.slotsAchievementIDs




def setup(bot):
	bot.add_cog(Achievements(bot))
