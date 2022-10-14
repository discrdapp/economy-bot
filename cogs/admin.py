import nextcord
from nextcord.ext import commands 
from nextcord import Interaction
from nextcord import FFmpegPCMAudio 
from nextcord import Member 
from nextcord.ext.commands import has_permissions, MissingPermissions

import asyncio
import sqlite3
import random
import math

import config
from db import DB as db

class Admin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@nextcord.slash_command()
	async def send(self, interaction:Interaction, user: nextcord.Member, amnt):
		if interaction.guild.id != 821015960931794964 and interaction.guild.id != 585226670361804827 and interaction.guild.id != 825179206958055425 and interaction.guild.id != 467084194200289280:
			await interaction.response.send_message("This command is only allowed in premium servers.")
			return

		if not await self.bot.get_cog("Economy").accCheck(interaction.user):
			await self.bot.get_cog("Economy").start(interaction, interaction.user)
		if not await self.bot.get_cog("Economy").accCheck(user):
			await self.bot.get_cog("Economy").start(interaction, user)

		amnt = await self.bot.get_cog("Economy").GetBetAmount(interaction, amnt)
		amntToReceive = math.floor(amnt * .95)

		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, amnt):
			await interaction.response.send_message(f"**ERROR:** {interaction.user.mention}, you do not have enough credits to send that.")
			return

		await self.bot.get_cog("Economy").addWinnings(user.id, amntToReceive)

		await interaction.response.send_message("Successfully sent!")



	# @nextcord.slash_command()
	# async def randNum(self, interaction:Interaction):

	# 	# 50% chance of it crashing at 1.2
	# 	# 20% crashing 
	# 	msg = ""
	# 	for _ in range(0, 6):
	# 		percChance = random.randint(1, 10)

	# 		randNum = 0
	# 		if 1 <= percChance <= 5:
	# 			print(1)
	# 			randNum = 1.2
	# 		elif 6 <= percChance <= 7:
	# 			print(2)
	# 			randNum = round(random.uniform(1.2, 1.4), 1)
	# 		elif 8 <= percChance <= 9:
	# 			print(3)
	# 			randNum = round(random.uniform(1.4, 1.8), 1)
	# 		else:
	# 			print(4)
	# 			randNum = round(random.uniform(1.8, 2.6), 1)
	# 		msg += str(randNum) + "\n"

		
	# 	await interaction.response.send_message(msg)

		# msg = ""
		# for _ in range(0, 6):
		# 	msg += str(round(random.uniform(1.2, 2.4), 1)) + "\n"

		# await interaction.response.send_message(msg)

	@nextcord.slash_command()
	@commands.is_owner()
	async def delete(self, interaction:Interaction, user: nextcord.Member):
		if not await self.bot.get_cog("Economy").accCheck(user):
			await interaction.response.send_message("User not registered in system...")
			return
		conn = sqlite3.connect(config.db)
		sql = f"DELETE FROM Economy WHERE DiscordID={user.id};"
		conn.execute(sql)
		sql = f"DELETE FROM Inventory WHERE DiscordID={user.id};"
		conn.execute(sql)
		sql = f"DELETE FROM Totals WHERE DiscordID={user.id};"
		conn.execute(sql)
		conn.commit()
		conn.close()

		await interaction.response.send_message("Deleted user.")

	@nextcord.slash_command()
	@commands.is_owner()
	async def resetmultipliers(self, interaction:Interaction):
		db.update(f"UPDATE Economy SET Multiplier = 1;", None)
		await interaction.response.send_message(f"All multipliers have been reset.\nUpdated {cursor.rowcount} rows.")


	@nextcord.slash_command()
	@commands.is_owner()
	async def getmultipliers():
		pass


	@nextcord.slash_command()
	@commands.is_owner()
	async def servers(self, interaction:Interaction):
		await interaction.response.send_message(f"I am currently in {len(self.bot.guilds)} servers")

	@nextcord.slash_command()
	@commands.is_owner()
	async def end(self, interaction:Interaction):
		await self.bot.logout()


	@nextcord.slash_command()
	@commands.is_owner()
	async def copy(self, interaction:Interaction, *, words):
		await interaction.response.send_message(words) # send the message


	@nextcord.slash_command()
	@commands.is_owner()
	async def addmoney(self, interaction:Interaction, user: nextcord.Member, amnt: int):
		await self.bot.get_cog("Economy").addWinnings(user.id, amnt)
		await interaction.response.send_message("Money added, Master.")


	@nextcord.slash_command()
	@commands.is_owner()
	async def givexp(self, interaction:Interaction, user: nextcord.Member, xp: int):
		db.update("UPDATE Economy SET XP = XP + ?, TotalXP = TotalXP + ? WHERE DiscordID = ?;", [xp, xp, user.id])
		await self.bot.get_cog("XP").levelUp(interaction, user.id) # checks if they lvl up


	@nextcord.slash_command()
	@commands.is_owner()
	async def givedonator(self, interaction:Interaction, *, member: nextcord.Member): # grabs member from input
		await interaction.response.send_message(f"Thanks for donating {member.mention}! Giving you perks now.")
		donatorRole = nextcord.utils.get(interaction.guild.roles, name = "Donator")
		await member.add_roles(donatorRole)
		await self.bot.get_cog("Economy").addWinnings(member.id, 10000)

		db.update("UPDATE Economy SET DonatorCheck = 1 WHERE DiscordID = ?;", [member.id])
		db.update("UPDATE Economy SET DonatorReward = DonatorReward + 5000 WHERE DiscordID = ?;", [member.id])

		await interaction.response.send_message(f"Donator role added.\n10000 credits added.\n5000 credits added to your Donator Reward")


	@nextcord.slash_command()
	@commands.is_owner()
	async def showallcommands(self, interaction:Interaction):
		msg = ""
		for cmd in self.bot.commands:
			if not cmd.description:
				msg += f"{cmd.name}\n"
		await interaction.response.send_message(msg)

def setup(bot):
	bot.add_cog(Admin(bot))
