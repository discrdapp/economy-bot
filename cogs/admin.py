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

	def isOwner(self, theid):
		return theid == 547475078082985990

	@nextcord.slash_command(guild_ids=[821015960931794964, 585226670361804827, 825179206958055425, 467084194200289280])
	async def send(self, interaction:Interaction, user: nextcord.Member, amnt):
		if not await self.bot.get_cog("Economy").accCheck(interaction.user):
			await self.bot.get_cog("Economy").StartPlaying(interaction, interaction.user)
		if not await self.bot.get_cog("Economy").accCheck(user):
			await self.bot.get_cog("Economy").StartPlaying(interaction, user)

		amnt = await self.bot.get_cog("Economy").GetBetAmount(interaction, amnt)
		amntToReceive = math.floor(amnt * .95)

		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, amnt):
			await interaction.send(f"**ERROR:** {interaction.user.mention}, you do not have enough credits to send that.")
			return

		await self.bot.get_cog("Economy").addWinnings(user.id, amntToReceive)

		await interaction.send(f"Successfully sent {amntToReceive} (5% tax)!")



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

		
	# 	await interaction.send(msg)

		# msg = ""
		# for _ in range(0, 6):
		# 	msg += str(round(random.uniform(1.2, 2.4), 1)) + "\n"

		# await interaction.send(msg)

	@nextcord.slash_command(guild_ids=[585226670361804827])
	async def delete(self, interaction:Interaction, user: nextcord.Member):
		if not self.isOwner(interaction.user.id):
			await interaction.send("You cannot do this.")
			return
		if not await self.bot.get_cog("Economy").accCheck(user):
			await interaction.send("User not registered in system...")
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

		await interaction.send("Deleted user.")

	@nextcord.slash_command(guild_ids=[585226670361804827])
	async def resetmultipliers(self, interaction:Interaction):
		if not self.isOwner(interaction.user.id):
			await interaction.send("You cannot do this.")
			return
		db.update(f"UPDATE Economy SET Multiplier = 1;", None)
		await interaction.send(f"All multipliers have been reset.\nUpdated {cursor.rowcount} rows.")


	@nextcord.slash_command(guild_ids=[585226670361804827])
	async def getmultipliers(self, interaction:Interaction):
		if not self.isOwner(interaction.user.id):
			await interaction.send("You cannot do this.")
			return
		pass


	@nextcord.slash_command(guild_ids=[585226670361804827])
	async def servers(self, interaction:Interaction):
		if not self.isOwner(interaction.user.id):
			await interaction.send("You cannot do this.")
			return
		await interaction.send(f"I am currently in {len(self.bot.guilds)} servers")

	@nextcord.slash_command(guild_ids=[585226670361804827])
	async def end(self, interaction:Interaction):
		if not self.isOwner(interaction.user.id):
			await interaction.send("You cannot do this.")
			return
		await self.bot.logout()


	@nextcord.slash_command(guild_ids=[585226670361804827])
	async def copy(self, interaction:Interaction, *, words):
		if not self.isOwner(interaction.user.id):
			await interaction.send("You cannot do this.")
			return
		await interaction.send(words) # send the message


	@nextcord.slash_command(guild_ids=[585226670361804827])
	async def addmoney(self, interaction:Interaction, user: nextcord.Member, amnt: int):
		if not self.isOwner(interaction.user.id):
			await interaction.send("You cannot do this.")
			return
		await self.bot.get_cog("Economy").addWinnings(user.id, amnt)
		await interaction.send("Money added, Master.")


	@nextcord.slash_command(guild_ids=[585226670361804827])
	async def givexp(self, interaction:Interaction, user: nextcord.Member, xp: int):
		if not self.isOwner(interaction.user.id):
			await interaction.send("You cannot do this.")
			return
		db.update("UPDATE Economy SET XP = XP + ?, TotalXP = TotalXP + ? WHERE DiscordID = ?;", [xp, xp, user.id])
		await self.bot.get_cog("XP").levelUp(interaction, user.id) # checks if they lvl up


	@nextcord.slash_command(guild_ids=[585226670361804827])
	async def givedonator(self, interaction:Interaction, *, member: nextcord.Member): # grabs member from input
		if not self.isOwner(interaction.user.id):
			await interaction.send("You cannot do this.")
			return
		await interaction.send(f"Thanks for donating {member.mention}! Giving you perks now.")
		donatorRole = nextcord.utils.get(interaction.guild.roles, name = "Donator")
		await member.add_roles(donatorRole)
		await self.bot.get_cog("Economy").addWinnings(member.id, 10000)

		db.update("UPDATE Economy SET DonatorCheck = 1 WHERE DiscordID = ?;", [member.id])
		db.update("UPDATE Economy SET DonatorReward = DonatorReward + 5000 WHERE DiscordID = ?;", [member.id])

		await interaction.send(f"Donator role added.\n10000 credits added.\n5000 credits added to your Donator Reward")


	@nextcord.slash_command(guild_ids=[585226670361804827])
	async def showallcommands(self, interaction:Interaction):
		if not self.isOwner(interaction.user.id):
			await interaction.send("You cannot do this.")
			return
		msg = ""
		for cmd in self.bot.commands:
			if not cmd.description:
				msg += f"{cmd.name}\n"
		await interaction.send(msg)

def setup(bot):
	bot.add_cog(Admin(bot))
