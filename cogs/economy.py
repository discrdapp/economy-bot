# economy-related stuff like betting and gambling, etc.

import discord
from discord.ext import commands
import pymysql
import asyncio
import random
import config

class Economy(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.coin = "<:coins:585233801320333313>"


	@commands.command(aliases=['begin', 'new'], pass_context=True)
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def start(self, ctx):
		if not await self.accCheck(ctx.author):
			db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
			cursor = db.cursor()
			sql = f"""INSERT INTO Economy(DiscordID)
					  VALUES ('{ctx.author.id}');"""
			cursor.execute(sql)
			db.commit()

			sql = f"""INSERT INTO Inventory(DiscordID)
					  VALUES ('{ctx.author.id}');"""
			cursor.execute(sql)
			db.commit()

			sql = f"""INSERT INTO Totals(DiscordID)
					  VALUES ('{ctx.author.id}');"""
			cursor.execute(sql)
			db.commit()

			db.close()

			await ctx.send("You are now successfully registered! Thank you, and have fun.")

			ch = self.bot.get_channel(705118255161016431)
			await ch.send(f"{ctx.author.name}#{ctx.author.discriminator} has registered.")
		else:
			await ctx.send("You are already registered, silly")

	@commands.command(aliases=['reward'], pass_context=True)
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def rewards(self, ctx):
		if not await self.accCheck(ctx.author):
			await ctx.send("Hello! Please type .start to create your wallet. :smiley:")
			return

		dailyReward = await self.bot.get_cog("Daily").getDailyReward(ctx)
		multiplier = self.getMultiplier(ctx.author)

		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Daily", value = f"{dailyReward}{self.coin}", inline=True)
		embed.add_field(name = "Multiplier", value = f"{multiplier}x", inline=True)

		if self.isDonator(ctx.author.id):
			embed.add_field(name = "_ _\nDonator Reward", value = f"{self.getDonatorReward(ctx.author.id)}{self.coin}", inline=False)
		else:
			embed.add_field(name = "_ _\nDonator Reward", value = f"You are not a donator", inline=False)
		await ctx.send(embed=embed)
		

	@commands.command(aliases=['bal', 'credits', 'bank'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def balance(self, ctx):
		""" Show your balance """
		if await self.accCheck(ctx.author) == True:
			balance = await self.getBalance(ctx.author)
			crates, keys = await self.getInventory(ctx.author)
			embed = discord.Embed(color=1768431)
			embed.add_field(name = "Credits", value = f"You have **{balance}**{self.coin}", inline=False)
			embed.add_field(name = "_ _\nCrates", value = f"You have **{crates}** crates", inline=True)
			embed.add_field(name = "_ _\nKeys", value = f"You have **{keys}** keys", inline=True)
			embed.set_footer(text="Use `.search` or `.daily` to get credits")
			await ctx.send(embed=embed)
		else:
			await ctx.send("Hello! Please type .start to create your wallet. :smiley:")

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def search(self, ctx):
		if await self.accCheck(ctx.author) == True:
			if await self.getBalance(ctx.author) < 100:
				amnt = random.randint(50, 250)
				await self.addWinnings(ctx.author.id, amnt)
				balance = await self.getBalance(ctx.author)
				
				embed = discord.Embed(color=1768431)
				embed.add_field(name = f"You found {amnt}{self.coin}", value = f"You have {balance}{self.coin}", inline=False)
				await ctx.send(embed=embed)
			else:
				await ctx.send(ctx.author.mention + f", you can't use this if you have over 100{self.coin}.")
		else:
			await ctx.send("Hello! Please type .start to create your wallet. :smiley:")

	@commands.command(aliases=['earn', 'free'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def freemoney(self, ctx):
		await ctx.send("Here are all the commands you can type for free money:\n\t\t`.search`\n\t\t`.daily`")

	@commands.command(aliases=['donate'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def donator(self, ctx):
		if self.isDonator(ctx.author.id):
			donatorReward = self.getDonatorReward(ctx.author.id)
			multiplier = self.getMultiplier(ctx.author)
			extraMoney = int(donatorReward * (multiplier - 1))
			await self.addWinnings(ctx.author.id, donatorReward + extraMoney)

			balance = await self.getBalance(ctx.author)
			embed = discord.Embed(color=1768431)
			embed.add_field(name = f"You got {donatorReward} {self.coin}", 
							value = f"You have {balance} credits\nMultiplier: {multiplier}x\nExtra Money: {extraMoney}", inline=False)
			await ctx.send(embed=embed)
			return

		embed = discord.Embed(color=1768431)
		embed.add_field(name = f"Donator Reward", value = f"To be able to claim the Donator Reward, you first need to donate!\n" +
															"Join the server shown in the .help menu to learn how!", inline=False)
		await ctx.send(embed=embed)



	def isDonator(self, discordID):
		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor() # DonatorCheck is either 0 or 1 (0 for not donator, 1 for donator)
		sql = f"""SELECT DonatorCheck 
				  FROM Economy
				  WHERE DiscordID = '{discordID}';"""
		cursor.execute(sql)
		db.commit()
		getRow = cursor.fetchone()
		donatorCheck = getRow[0] # assign donatorCheck to grabbed column DonatorCheck for the row that has {discordID}
		db.close()

		return donatorCheck

	def getDonatorReward(self, discordID):
		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()
		sql = f"""SELECT DonatorReward 
				  FROM Economy
				  WHERE DiscordID = '{discordID}';"""
		cursor.execute(sql)
		db.commit()
		getRow = cursor.fetchone()
		donatorReward = getRow[0] # assign donatorReward to grabbed column DonatorCheck for the row that has {discordID}
		db.close()

		return donatorReward


	def getMultiplier(self, user):
		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()
		sql = f"""SELECT Multiplier
				  FROM Economy
				  WHERE DiscordID = '{user.id}';"""
		cursor.execute(sql)
		db.commit()
		getRow = cursor.fetchone()
		multiplier = getRow[0]
		db.close()

		return multiplier


	async def subtractBet(self, user, amntBet): # subtracts the bet users place when they play games
		if await self.accCheck(user) == True:
			balance = await self.getBalance(user)
			if amntBet <= balance and amntBet > 0:
				db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
				cursor = db.cursor()
				sql = f"""UPDATE Economy
						  SET Credits = Credits - {amntBet}
						  WHERE DiscordID = '{user.id}';"""
				cursor.execute(sql)
				db.commit()
				db.close()
				return True # return 1 if user has enough $$$ to bet their amount entered
			else:
				return False # return 0 if user trying to bet more $$$ than they have
		else:
			return False



	async def addWinnings(self, discordId, winnings): # add the amount won 
		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()
		
		sql = f"""UPDATE Economy
				  SET Credits = Credits + {winnings}
				  WHERE DiscordID = '{discordId}';"""
		cursor.execute(sql)
		db.commit()
		db.close()


	async def getBalance(self, user):
		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()

		sql = f"""SELECT Credits
				  FROM Economy
				  WHERE DiscordID = '{user.id}';"""
		cursor.execute(sql)
		db.commit()
		getRow = cursor.fetchone()
		db.close()
		balance = getRow[0]
		return balance
	

	async def getInventory(self, user): # grabs all the crates and keys from database
		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor() 
		# "Keys" is a special word and can't be used in SQL statements for some reason
		sql = f"""SELECT Crates, Keyss
				  FROM Inventory
				  WHERE DiscordID = {user.id};"""

		cursor.execute(sql)
		db.commit()
		getRow = cursor.fetchone()
		db.close()
		crates = getRow[0]
		keys = getRow[1]
		return crates, keys


	async def subtractInv(self, discordId, amnt): # called when people open crates (subtracts them from inv.)
		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()
		sql = f"""UPDATE Inventory
				  SET Crates = Crates - {amnt}, Keyss = Keyss - {amnt}
				  WHERE DiscordID = '{discordId}';"""
		cursor.execute(sql)
		db.commit()
		db.close()


	@commands.command()
	async def top(self, ctx): # scoreboard to display top 10 richest individuals
		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()
		sql = f"""SELECT DiscordID, Credits
				  FROM Economy"""
		cursor.execute(sql) 
		db.commit()
		records = cursor.fetchall() 
		db.close()

		records = sorted(records, key = lambda x: x[1], reverse=True) # sort rows by credits  

		topUsers = ""
		count = 1
		for x in records: 
			user = await self.bot.fetch_user(x[0]) # grab the user from the current record
			topUsers += f"{count}. < {user.name} > - " + "{:,}".format(x[1]) + "\n"
			if count == 10:
				break
			count += 1 # number the users from 1 - 10

		await ctx.send(f"```MD\nTop 10\n======\n{topUsers}```") # send the list with the top 10


	@commands.command(aliases=['pos'])
	async def position(self, ctx, usr: discord.User=None): # scoreboard to display top 10 richest individuals
		if not usr:
			usr = ctx.author

		if not await self.accCheck(ctx.author):
			await ctx.send("Hello! Please type .start to create your wallet. :smiley:")
			return

		name = usr.name

		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()
		sql = f"""SELECT DiscordID, Credits
				  FROM Economy"""
		cursor.execute(sql) 
		db.commit()
		records = cursor.fetchall() 
		db.close()

		records = sorted(records, key = lambda x: x[1], reverse=True) # sort rows by credits  

		pos = 0
		for x in records:
			if str(usr.id) == x[0]:
				break
			pos += 1

		diff = ""
		if pos > 0:
			diff = f" and needs {str(records[pos-1][1] - records[pos][1] + 1)} coin(s) to beat the person above them"
		# else:
		# 	diff = " so no one is beating them!"
		topUsers = ""
		for x in range(-3, 4):
			if pos + x < 0 or pos + x > len(records):
				continue
			user = await self.bot.fetch_user(records[pos+x][0])
			if x == 0:
				topUsers += f"** {pos+x+1}. < {user.name} > - {records[pos+x][1]} **\n"
			else:
				topUsers += f"{pos+x+1}. < {user.name} > - {records[pos+x][1]}\n"

		await ctx.send(f"```MD\n{name} is #{pos+1}{diff}\n======\n{topUsers}```") # send the list with the top 10



	async def accCheck(self, user):
		# checks if they already have a wallet in database
		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()

		sql = f"""SELECT DiscordID
				  FROM Economy
				  WHERE DiscordID = '{user.id}';"""

		cursor.execute(sql) 
		db.commit()

		getRow = cursor.fetchone()
		db.close()

		if getRow != None: # getRow will not be None if account is found, therefor return True
			return True
		
		return False



def setup(bot):
	bot.add_cog(Economy(bot))