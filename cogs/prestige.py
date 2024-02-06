import nextcord
from nextcord.ext import commands
from nextcord import Interaction, Color

import config, emojis
from db import DB

from cogs.util import SendConfirmButton

class Prestige(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot


	@nextcord.slash_command()
	async def prestige(self, interaction:Interaction):
		pass
	
	@prestige.subcommand()
	async def now(self, interaction:Interaction):
		counts = DB.fetchOne("SELECT Games, Profit FROM Totals WHERE DiscordID = ?", [interaction.user.id])
		gamesCount = counts[0]
		profit = counts[1] > 0

		embed = nextcord.Embed(color=Color.red(), title=f"{self.bot.user.name} | Prestige")
		if not profit:
			embed.description = "You need to have positive profit to Prestige"
			await interaction.send(embed=embed)
			return

		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		currLvl = self.bot.get_cog("XP").getLevel(interaction.user.id)

		prestigeLvl = DB.fetchOne("SELECT Prestige FROM Prestige WHERE DiscordID = ?", [interaction.user.id])

		insert = False
		if not prestigeLvl:
			# 500,000
			cost = 500000
			levelRequirement = 5
			gamesRequirement = 100
			prestigeLvl = 0
			insert = True
		else:
			prestigeLvl = prestigeLvl[0]
			if prestigeLvl == 1:
				# 1,000,000
				cost = 1000000
				levelRequirement = 7
				gamesRequirement = 250
			elif prestigeLvl == 2:
				# 2,500,000
				cost = 2500000
				levelRequirement = 10
				gamesRequirement = 10000
			elif prestigeLvl == 3:
				# 5,000,000
				cost = 5000000
				levelRequirement = 12
				gamesRequirement = 10000
			elif prestigeLvl == 4:
				# 10,000,000
				cost = 10000000
				levelRequirement = 15
				gamesRequirement = 10000
			elif prestigeLvl == 5:
				# 15,000,000
				cost = 15000000
				levelRequirement = 20
				gamesRequirement = 10000
			elif prestigeLvl == 6:
				# 25,000,000
				cost = 25000000
				levelRequirement = 25
				gamesRequirement = 10000
			elif prestigeLvl == 7:
				# 55,000,000
				cost = 55000000
				levelRequirement = 30
				gamesRequirement = 10000
			elif prestigeLvl == 8:
				# 250,000,000
				cost = 250000000
				levelRequirement = 35
				gamesRequirement = 10000
			elif prestigeLvl == 9:
				# 750,000,000
				cost = 750000000
				levelRequirement = 40
				gamesRequirement = 10000
			elif prestigeLvl == 9:
				# 1,000,000,000
				cost = 1000000000
				levelRequirement = 50
				gamesRequirement = 100000
			elif prestigeLvl == 10:
				embed.description = "Already at max prestige!"
				await interaction.send(embed=embed)
				return

		if balance < cost or currLvl < levelRequirement or gamesCount < gamesRequirement:
			embed = nextcord.Embed(color=Color.red(), title=f"{self.bot.user.name} | Prestige | Requirements")
			embed.description = "Requirements not met."
			embed.set_footer(text="See the list in /prestige requirements")
			await emojis.SendInteractionWithStop(interaction, embed, True)
			return

		prestigeMsg = "You are about to Prestige. This will completely reset your profile, but you will receive permanent rewards. Continue?"
		if not await SendConfirmButton(interaction, prestigeMsg):
			await interaction.send("Cancelled.", ephemeral=True)
			return

		# DB.delete("DELETE FROM ActiveBuffs WHERE DiscordID = ?;", [interaction.user.id])
		# DB.delete("DELETE FROM Crypto WHERE DiscordID = ?;", [interaction.user.id])
		# DB.delete("DELETE FROM CryptoMiner WHERE DiscordID = ?;", [interaction.user.id])
		# DB.delete("DELETE FROM Economy WHERE DiscordID = ?;", [interaction.user.id])
		# DB.delete("DELETE FROM Inventory WHERE DiscordID = ?;", [interaction.user.id])
		# DB.delete("DELETE FROM MinerInventory WHERE DiscordID = ?;", [interaction.user.id])
		# DB.delete("DELETE FROM Monopoly WHERE DiscordID = ?;", [interaction.user.id])
		# DB.delete("DELETE FROM MonopolyPeople WHERE DiscordID = ?;", [interaction.user.id])
		# DB.delete("DELETE FROM Multipliers WHERE DiscordID = ?;", [interaction.user.id])
		# DB.delete("DELETE FROM Quests WHERE DiscordID = ?;", [interaction.user.id])
		# DB.delete("DELETE FROM RankedUsers WHERE DiscordID = ?;", [interaction.user.id])
		# DB.delete("DELETE FROM Totals WHERE DiscordID = ?;", [interaction.user.id])

		# DB.insert('INSERT INTO Economy(DiscordID, Credits) VALUES (?, ?);', [interaction.user.id, 50000*(prestigeLvl+1)])
		# DB.insert('INSERT INTO Totals(DiscordID) VALUES (?);', [interaction.user.id])


		if insert:
			DB.insert("INSERT INTO Prestige VALUES(?, ?)", [interaction.user.id, 1])
		else:
			DB.insert("UPDATE Prestige SET Prestige = Prestige + 1 WHERE DiscordID = ?", [interaction.user.id])
		
		await interaction.send(f"You are now Prestige {prestigeLvl+1}")

		achievementID = await self.bot.get_cog("Achievements").FindAchievementIDWithDesc("Prestige", f"Prestige {prestigeLvl+1}")
		if not achievementID:
			print("ERROR: no achievement ID")
			return
		await self.bot.get_cog("Achievements").EarnAchievementByID(interaction, interaction.user.id, achievementID)
	
	@prestige.subcommand()
	async def info(self, interaction:Interaction):
		embed = nextcord.Embed(color=Color.blurple(), title=f"{self.bot.user.name} | Prestige | Info")
		
		embed.description = f"""Welcome... to the next level of The Casino.\nPrestiging is like how it is in Call of Duty or games like Cookie Clicker
		\nSpecific requirements must be met to prestige.
		Prestiging grants a Badge and permanent rewards, and each time you prestige, the rewards get better:

		**REWARDS ARE A WORK IN PROGRESS**\nPrestiging will currently not give you anything, but you will start with some extra credits. 
		\nJoin the [Support Server]({config.serverInviteURL}) to stay up-to-date on this!
		"""
		
		# Prestige 1: 1.1x multiplier
		# Prestige 2: 1.15x multiplier
		# Prestige 3
		# Prestige 4
		# Prestige 5
		# Prestige 6
		# Prestige 7
		# Prestige 8
		# Prestige 9
		# Prestige 10"""

		await interaction.send(embed=embed)
	
	@prestige.subcommand()
	async def requirements(self, interaction:Interaction):
		prestigeLvl = DB.fetchOne("SELECT Prestige FROM Prestige WHERE DiscordID = ?", [interaction.user.id])
		if not prestigeLvl:
			# 10,000,000
			cost = pow(10, 7)
			levelRequirement = 7
			gamesRequirement = 250
			prestigeLvl = 0
			insert = True
		else:
			prestigeLvl = prestigeLvl[0]
			if prestigeLvl == 1:
				# 1,000,000,000
				cost = pow(10,9)
				levelRequirement = 15
				gamesRequirement = 1000
			elif prestigeLvl == 2:
				# 1,000,000,000,000
				cost = pow(10, 12)
				levelRequirement = 30
				gamesRequirement = 10000
			else:
				# 1,000,000,000,000,000,000
				cost = pow(10, 18)
				levelRequirement = 50
				gamesRequirement = 100000

		embed = nextcord.Embed(color=Color.red(), title=f"{self.bot.user.name} | Prestige | Requirements")
		embed.add_field(name=f"Prestige {prestigeLvl+1} Requirements", value=f"""\nLevel {levelRequirement} in /level
				  \n{cost}{emojis.coin} in /balance\n{gamesRequirement} Games in /stats\n""")

		await interaction.send(embed=embed)

		




def setup(bot):
	bot.add_cog(Prestige(bot))