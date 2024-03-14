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
			prestigeLvl = 0
			insert = True
		else:
			prestigeLvl = prestigeLvl[0]
		
		if prestigeLvl == 0:
			# 500,000
			cost = 500000
			levelRequirement = 5
			gamesRequirement = 100
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
		elif prestigeLvl >= 10:
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

		DB.delete("DELETE FROM ActiveBuffs WHERE DiscordID = ?;", [interaction.user.id])
		DB.delete("DELETE FROM Crypto WHERE DiscordID = ?;", [interaction.user.id])
		DB.delete("DELETE FROM CryptoMiner WHERE DiscordID = ?;", [interaction.user.id])
		DB.delete("DELETE FROM Economy WHERE DiscordID = ?;", [interaction.user.id])
		DB.delete("DELETE FROM Inventory WHERE DiscordID = ?;", [interaction.user.id])
		DB.delete("DELETE FROM MinerInventory WHERE DiscordID = ?;", [interaction.user.id])
		DB.delete("DELETE FROM Monopoly WHERE DiscordID = ?;", [interaction.user.id])
		DB.delete("DELETE FROM MonopolyPeople WHERE DiscordID = ?;", [interaction.user.id])
		DB.delete("DELETE FROM Multipliers WHERE DiscordID = ?;", [interaction.user.id])
		DB.delete("DELETE FROM MultipliersPerm WHERE DiscordID = ?;", [interaction.user.id])
		DB.delete("DELETE FROM Quests WHERE DiscordID = ?;", [interaction.user.id])
		DB.delete("DELETE FROM RankedUsers WHERE DiscordID = ?;", [interaction.user.id])
		DB.delete("DELETE FROM Totals WHERE DiscordID = ?;", [interaction.user.id])

		DB.insert('INSERT INTO Economy(DiscordID, Credits) VALUES (?, ?);', [interaction.user.id, 50000*(prestigeLvl+1)])
		DB.insert('INSERT INTO Totals(DiscordID) VALUES (?);', [interaction.user.id])

		permMultiplierAmnt = 0
		if prestigeLvl+1 == 1: 
			permMultiplierAmnt = 0.1
		if prestigeLvl+1 == 2: 
			permMultiplierAmnt = 0.15
		if prestigeLvl+1 == 3: 
			permMultiplierAmnt = 0.17
		if prestigeLvl+1 == 4: 
			permMultiplierAmnt = 0.20
		if prestigeLvl+1 == 5: 
			permMultiplierAmnt = 0.22
		if prestigeLvl+1 == 6: 
			permMultiplierAmnt = 0.24
		if prestigeLvl+1 == 7: 
			permMultiplierAmnt = 0.26
		if prestigeLvl+1 == 8: 
			permMultiplierAmnt = 0.28
		if prestigeLvl+1 == 9: 
			permMultiplierAmnt = 0.31
		if prestigeLvl+1 == 10: 
			permMultiplierAmnt = 0.35

		DB.insert('INSERT INTO MultipliersPerm VALUES(?, ?)', [interaction.user.id, permMultiplierAmnt])

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
		
		embed.description = f"""
Welcome... to the NEXT level of The Casino.\nPrestiging is like how it is in Call of Duty or Cookie Clicker

Specific requirements must be met to Prestige.
Prestiging grants Badges, coins, and permanent rewards. The rewards get better each time you Prestige.

**REWARDS ARE BELOW**
Prestiging is a **WORK IN PROGRESS**. Join the [Support Server]({config.serverInviteURL}) to stay up-to-date!

Prestige 1: 1.1x multiplier, 50,000 {emojis.coin}
Prestige 2: 1.15x multiplier, 100,000 {emojis.coin}
Prestige 3: 1.17x multiplier, 150,000 {emojis.coin}
Prestige 4: 1.20x multiplier, 200,000 {emojis.coin}
Prestige 5: 1.22x multiplier, 250,000 {emojis.coin}
Prestige 6: 1.24x multilpier, 300,000 {emojis.coin}
Prestige 7: 1.26x multiplier, 350,000 {emojis.coin}
Prestige 8: 1.28x multiplier, 400,000 {emojis.coin}
Prestige 9: 1.31x multiplier, 450,000 {emojis.coin}
Prestige 10: 1.35x multiplier, 500,000 {emojis.coin}

**Unlike all other multipliers, these are the ONLY multipliers that are stackable with the other multipliers**
"""

		await interaction.send(embed=embed)
	
	@prestige.subcommand()
	async def requirements(self, interaction:Interaction):
		embed = nextcord.Embed(color=Color.red(), title=f"{self.bot.user.name} | Prestige | Requirements")
		
		prestigeLvl = DB.fetchOne("SELECT Prestige FROM Prestige WHERE DiscordID = ?", [interaction.user.id])
		if not prestigeLvl:
			prestigeLvl = 0
		else:
			prestigeLvl = prestigeLvl[0]
		
		if prestigeLvl == 0:
			# 500,000
			cost = 500000
			levelRequirement = 5
			gamesRequirement = 100
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
		elif prestigeLvl >= 10:
			embed.description = "Already at max Prestige!"
			await interaction.send(embed=embed)
			return

		embed.add_field(name=f"Prestige {prestigeLvl+1} Requirements", value=f"""\nLevel {levelRequirement} in /level
				  \n{cost}{emojis.coin} in /balance\n{gamesRequirement} Games in /stats\n""")

		await interaction.send(embed=embed)

		




def setup(bot):
	bot.add_cog(Prestige(bot))