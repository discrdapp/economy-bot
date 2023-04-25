import nextcord
from nextcord.ext import commands, application_checks
from nextcord import Interaction
# from nextcord import FFmpegPCMAudio 
from nextcord import Member 
# from nextcord.ext.commands import has_permissions, MissingPermissions

import math, datetime

import config
from db import DB

class Admin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def isOwner(self, theid):
		return theid == config.botOwnerDiscordID

	@nextcord.slash_command(guild_ids=[821015960931794964, 585226670361804827, 825179206958055425, 467084194200289280, 601446508121817088])
	async def send(self, interaction:Interaction, user: nextcord.Member, amnt):

		amnt = await self.bot.get_cog("Economy").GetBetAmount(interaction, amnt)
		amntToReceive = math.floor(amnt * .95)

		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, amnt):
			await interaction.send(f"**ERROR:** {interaction.user.mention}, you do not have enough credits to send that.")
			return

		await self.bot.get_cog("Economy").addWinnings(user.id, amntToReceive)

		await interaction.send(f"Successfully sent {amntToReceive} (5% tax)!")



	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def delete(self, interaction:Interaction, user: nextcord.Member):
		if not await self.bot.get_cog("Economy").accCheck(user):
			await interaction.send("User not registered in system...")
			return
			
		DB.delete("DELETE FROM Economy WHERE DiscordID = ?;", [user.id])
		DB.delete("DELETE FROM Inventory WHERE DiscordID = ?;", [user.id])
		DB.delete("DELETE FROM Totals WHERE DiscordID = ?;", [user.id])

		await interaction.send("Deleted user.")

	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def resetmultipliers(self, interaction:Interaction):
		DB.update(f"UPDATE Economy SET Multiplier = '2023-18-04 20:21:00';")
		await interaction.send(f"All multipliers have been reset.\nUpdated all rows.")


	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def getmultipliers(self, interaction:Interaction):
		multipliers = DB.fetchAll("SELECT DiscordID, Multiplier FROM Economy WHERE DiscordID == 547475078082985990;", None)

		msg = "Multipliers are below:\n"
		for multiplier in multipliers:
			expireDate = datetime.datetime.strptime(multiplier[1], '%Y-%d-%m %H:%M:%S')
			if expireDate > datetime.datetime.now():
				seconds = (expireDate - datetime.datetime.now()).total_seconds()
				
				timeLeft = ""
				if seconds > 86400: # days
					timeLeft += f"{math.floor(seconds / 86400)} days "
					seconds = seconds % 86400
				if seconds > 3600: # hours
					timeLeft += f"{math.floor(seconds / 3600)} hours "
					seconds = seconds % 3600
				if seconds > 60: # minutes
					timeLeft += f"{math.floor(seconds / 60)} minutes "
					seconds = seconds % 60
				# seconds will now be the left over seconds
				seconds = round(seconds)
				timeLeft += f"{seconds} seconds"

				msg += f"ID: {multiplier[0]}'s expires at {expireDate}. They have {timeLeft} left."


		# print(f"datetime is {datetime.now()}")


		await interaction.send(msg)


	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def servers(self, interaction:Interaction):
		await interaction.send(f"I am currently in {len(self.bot.guilds)} servers")

	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def end(self, interaction:Interaction):
		await self.bot.logout()


	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def copy(self, interaction:Interaction, *, words):
		await interaction.send(words) # send the message


	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def addmoney(self, interaction:Interaction, user: nextcord.Member, amnt:int):
		await self.bot.get_cog("Economy").addWinnings(user.id, amnt)
		await interaction.send("Money added, Master.")


	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def givexp(self, interaction:Interaction, user: nextcord.Member, xp:int):
		DB.update("UPDATE Economy SET XP = XP + ?, TotalXP = TotalXP + ? WHERE DiscordID = ?;", [xp, xp, user.id])
		await self.bot.get_cog("XP").levelUp(interaction, user.id) # checks if they lvl up


	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def givedonator(self, interaction:Interaction, member: nextcord.Member, level:int=1): # grabs member from input
		if self.bot.get_cog("Economy").isDonator(interaction.user.id):
			await interaction.send(f"{member.mention} is already a donator!")
			return

		await interaction.send(f"Thanks for donating {member.mention}! Giving you perks now.")
		donatorRole = nextcord.utils.get(interaction.guild.roles, name = "Donator")
		try:
			await member.add_roles(donatorRole)
		except:
			pass

		creditsGiven = 10000
		donatorReward = 5000
		if level == 2:
			creditsGiven = 20000
			donatorReward = 10000
		elif level == 3:
			creditsGiven = 35000
			donatorReward = 20000
		await self.bot.get_cog("Economy").addWinnings(member.id, creditsGiven)


		DB.insert("INSERT INTO Donator(DiscordID, Level, DonatorReward) VALUES(?, ?, ?)", [member.id, level, donatorReward])

		await interaction.send(f"Donator role added.\n{creditsGiven} credits added.\n{donatorReward} credits added to your Donator Reward")


	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def showallcommands(self, interaction:Interaction):
		msg = ""
		for cmd in self.bot.commands:
			if not cmd.description:
				msg += f"{cmd.name}\n"
		await interaction.send(msg)

def setup(bot):
	bot.add_cog(Admin(bot))
