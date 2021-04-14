import discord
from discord.ext import commands
from discord.ext.commands import has_permissions

import asyncio
import pymysql
import random
import math

import config

class Admin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def send(self, ctx, user: discord.Member, amnt:int):
		if ctx.guild.id != 821015960931794964 and ctx.guild.id != 585226670361804827:
			await ctx.send("This command is only allowed in premium servers.")
			return
		if amnt <= 0:
			await ctx.send("Amount must be greater than 0.. don't be *silly*...")
			return
		if not await self.bot.get_cog("Economy").accCheck(user):
			await ctx.send(f"{user.mention} does not have an account. They must type .start")
			return

		amntToReceive = math.floor(amnt * .95)
		msg = await ctx.send(f"{ctx.author.mention}, you will send {str(amnt)} to {user.mention} and they will receive {str(amntToReceive)} (5% transfer fee)\nContinue? (type yes)")

		def is_me(m):
			return m.author.id == ctx.author.id and m.content == "yes"

		try:
			await self.bot.wait_for('message', check=is_me, timeout=15)
		except asyncio.TimeoutError:
			await msg.edit(message="Timed out.")
			return


		if not await self.bot.get_cog("Economy").subtractBet(ctx.author, amnt):
			await ctx.send(f"**ERROR:** {ctx.author.mention}, you do not have enough credits to send that.")
			return

		await self.bot.get_cog("Economy").addWinnings(user.id, amntToReceive)

		await ctx.send("Successfully sent!")



	# @commands.command()
	# async def randNum(self, ctx):

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

		
	# 	await ctx.send(msg)

		# msg = ""
		# for _ in range(0, 6):
		# 	msg += str(round(random.uniform(1.2, 2.4), 1)) + "\n"

		# await ctx.send(msg)

	@commands.command()
	@commands.is_owner()
	async def delete(self, ctx, user: discord.Member):
		if not await self.bot.get_cog("Economy").accCheck(user):
			await ctx.send("User not registered in system...")
			return
		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()
		sql = f"DELETE FROM Economy WHERE DiscordID={user.id};"
		cursor.execute(sql)
		sql = f"DELETE FROM Inventory WHERE DiscordID={user.id};"
		cursor.execute(sql)
		sql = f"DELETE FROM Totals WHERE DiscordID={user.id};"
		cursor.execute(sql)
		db.commit()
		db.close()

		await ctx.send("Deleted user.")

	@commands.command()
	@commands.is_owner()
	async def servers(self, ctx):
		msgNum = 0
		count = 1
		message1 = ""
		message2 = ""
		message3 = ""
		for guild in self.bot.guilds:
			invites = ""
			inviteCount = 0
			if guild.owner:
				if 'pycord' in guild.name.lower() or 'pycord' in guild.owner.name.lower():
					continue
			
			if msgNum == 0:	
				message1 += f"{count}) {guild.name}\n"
				if 2000 - len(message1) <= 100:
					msgNum = 1
			elif msgNum == 1:	
				message2 += f"{count}) {guild.name}\n"
				if 2000 - len(message2) <= 100:
					msgNum = 2
			elif msgNum == 2:	
				message3 += f"{count}) {guild.name}\n"
			
			count += 1

		if message1:
			await ctx.send(f"{message1}")
		if message2:
			await ctx.send(f"{message2}")
		if message3:
			await ctx.send(f"{message3}")


	@commands.command()
	@commands.is_owner()
	async def end(self, ctx):
		await self.bot.logout()


	@commands.command()
	@commands.is_owner()
	async def copy(self, ctx, *, words):
		await ctx.message.delete() # delete the original message
		await ctx.send(words) # send the message


	@commands.command(aliases=['add', 'givemoney', 'give'])
	@commands.is_owner()
	async def addmoney(self, ctx, user: str, amnt: int):
		await self.bot.get_cog("Economy").addWinnings(user, amnt)


	@commands.command()
	@commands.is_owner()
	async def givexp(self, ctx, discordId: str, xp: int):
		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()
		sql = f"""Update Economy
				  SET XP = XP + {xp}, TotalXP = TotalXP + {xp}
				  WHERE DiscordID = '{discordId}';"""
		cursor.execute(sql)
		db.commit()
		await self.bot.get_cog("XP").levelUp(ctx, db, discordId) # checks if they lvl up
		db.close()


	@commands.command()
	@commands.is_owner()
	async def givedonator(self, ctx, *, member: discord.Member): # grabs member from input
		await ctx.send(f"Thanks for donating {member.mention}! Giving you perks now.")
		donatorRole = discord.utils.get(ctx.guild.roles, name = "Donator")
		await member.add_roles(donatorRole)
		await self.bot.get_cog("Economy").addWinnings(member.id, 10000)

		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()

		sql = f"""UPDATE Economy
				  SET DonatorCheck = 1
				  WHERE DiscordID = '{member.id}';"""
		cursor.execute(sql)
		db.commit()

		sql = f"""UPDATE Economy
		  SET DonatorReward = DonatorReward + 5000
		  WHERE DiscordID = '{member.id}';"""
		cursor.execute(sql)
		db.commit()

		db.close()

		await ctx.send(f"Donator role added.\n10000 credits added.\n5000 credits added to your Donator Reward")


	@commands.command()
	@commands.is_owner()
	async def showallcommands(self, ctx):
		msg = ""
		for cmd in self.bot.commands:
			if not cmd.description:
				msg += f"{cmd.name}\n"
		await ctx.send(msg)

def setup(bot):
	bot.add_cog(Admin(bot))
