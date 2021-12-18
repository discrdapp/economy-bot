# economy-related stuff like betting and gambling, etc.

import discord
from discord.ext import commands
import sqlite3
import asyncio
import random
import math

import config
from db import DB

class Economy(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.coin = "<:coins:585233801320333313>"


	@commands.command(aliases=['begin', 'new'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def start(self, ctx, user:discord.Member=None):
		if not user:
			user = ctx.author 
		embed = discord.Embed(color=1768431, title=self.bot.user.name)
		embed.set_thumbnail(url=user.avatar_url)
		embed.set_footer(text=user)
		if await self.accCheck(user):
			embed.add_field(name="Error", value="You are already registered, silly")
			await ctx.send(embed=embed)
			return

		conn = sqlite3.connect(config.db)
		sql = "INSERT INTO Economy(DiscordID) VALUES (?);"
		conn.execute(sql, [user.id])

		sql = "INSERT INTO Inventory(DiscordID) VALUES (?);"
		conn.execute(sql, [user.id])

		sql = "INSERT INTO Totals(DiscordID) VALUES (?);"
		conn.execute(sql, [user.id])
		conn.commit()
		conn.close()

		embed.add_field(name="Welcome!", value="You are now successfully registered. Enjoy The Casino.")
		await ctx.send(embed=embed)

		ch = self.bot.get_channel(705118255161016431)
		await ch.send(f"{user} has registered.")

	async def GetBetAmount(self, ctx, amntBet):
		if amntBet.isdigit():
			return int(amntBet)
		if amntBet == "all" or amntBet == "allin" or amntBet == "everything":
			return await self.getBalance(ctx.author)
		if amntBet == "half":
			return math.floor(await self.getBalance(ctx.author) / 2)
		if amntBet == "third":
			return math.floor(await self.getBalance(ctx.author) / 3)
		if amntBet == "fourth":
			return math.floor(await self.getBalance(ctx.author) / 4)
		if "%" == amntBet[-1]:
			return math.floor(await self.getBalance(ctx.author) * (int(amntBet.replace('%','')) / 100))
		if "." in amntBet and amntBet[0] == "0":
			return math.floor(await self.getBalance(ctx.author) * float(amntBet))
		if "/" in amntBet:
			pos = amntBet.find("/")
			return math.floor(await self.getBalance(ctx.author) * float(int(amntBet[:pos]) / int(amntBet[pos+1:])))
		raise commands.BadArgument(f'You entered {amntBet} for the amount you want to bet. Please enter a number instead.')

	@commands.command(aliases=['reward'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def rewards(self, ctx):
		if not await self.accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))

		dailyReward = await self.bot.get_cog("Daily").getDailyReward(ctx)
		multiplier = self.getMultiplier(ctx.author)

		embed = discord.Embed(color=1768431, title=self.bot.user.name)
		embed.add_field(name = "Daily", value = f"{dailyReward}{self.coin}", inline=True)
		embed.add_field(name = "Multiplier", value = f"{multiplier}x", inline=True)
		# embed.add_field(name = "Weekly", value = f"12500{self.coin}", inline=False)
		# embed.add_field(name = "Monthly", value = f"36000{self.coin}", inline=True)

		if self.isDonator(ctx.author.id):
			embed.add_field(name = "_ _\nDonator Reward", value = f"{self.getDonatorReward(ctx.author.id)}{self.coin}", inline=False)
		else:
			embed.add_field(name = "_ _\nDonator Reward", value = f"You are not a donator", inline=False)
		await ctx.send(embed=embed)
		

	@commands.command(aliases=['bal', 'credits'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def balance(self, ctx, user:discord.Member=None):
		""" Show your balance """
		if not user:
			user = ctx.author
			pronouns = "You"
		else:
			pronouns = "They"

		if not await self.bot.get_cog("Economy").accCheck(user):
			await ctx.invoke(self.bot.get_command('start'), user)

		prefix = ctx.prefix

		balance = await self.getBalance(user)
		crates, keys = await self.getInventory(user)
		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Credits", value = f"{pronouns} have **{balance}**{self.coin}", inline=False)
		embed.add_field(name = "_ _\nCrates", value = f"{pronouns} have **{crates}** crates", inline=True)
		embed.add_field(name = "_ _\nKeys", value = f"{pronouns} have **{keys}** keys", inline=True)
		embed.set_footer(text=f"Use {prefix}vote, {prefix}search, {prefix}daily, and {prefix}work to get credits")
		await ctx.send(embed=embed)
		
	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def search(self, ctx):
		if not await self.accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))
		embed = discord.Embed(color=1768431)
		if await self.getBalance(ctx.author) < 300:
			amnt = random.randint(50, 250)
			await self.addWinnings(ctx.author.id, amnt)
			balance = await self.getBalance(ctx.author)
			
			embed.add_field(name = f"You found {amnt}{self.coin}", value = f"You have {balance}{self.coin}", inline=False)
		else:
			embed.add_field(name = f"Error", value = f"{ctx.author.mention}, you can only use this if you have less than 300{self.coin}.", inline=False)

		await ctx.send(embed=embed)
		
	@commands.command(aliases=['earn', 'free'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def freemoney(self, ctx):
		prefix = ctx.prefix
		embed = discord.Embed(color=1768431, title=self.bot.user.name)
		embed.add_field(name="Free Money Commands", value=f"`{prefix}vote`\n`{prefix}search`\n`{prefix}daily`\n`{prefix}weekly`\n`{prefix}monthly`\n`{prefix}work`")
		await ctx.send(embed=embed)

	@commands.command(aliases=['donate'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def donator(self, ctx):
		if not self.isDonator(ctx.author.id):
			embed = discord.Embed(color=1768431, title=self.bot.user.name)
			embed.add_field(name = f"Donator Reward", value = "To be able to claim the Donator Reward, you first need to donate!\n" +
																f"Join the server shown in the {ctx.prefix}help menu to learn how!", inline=False)
			await ctx.send(embed=embed)
			return

		donatorReward = self.getDonatorReward(ctx.author.id)
		multiplier = self.getMultiplier(ctx.author)
		extraMoney = int(donatorReward * (multiplier - 1))
		await self.addWinnings(ctx.author.id, donatorReward + extraMoney)

		balance = await self.getBalance(ctx.author)
		embed = discord.Embed(color=1768431, title=self.bot.user.name)
		embed.add_field(name = f"You got {donatorReward} {self.coin}", 
						value = f"You have {balance} credits\nMultiplier: {multiplier}x\nExtra Money: {extraMoney}", inline=False)
		await ctx.send(embed=embed)


	def isDonator(self, discordID):
		donatorCheck = DB.fetchOne("SELECT DonatorCheck FROM Economy WHERE DiscordID = ?;", [discordID])[0]
		return donatorCheck

	def getDonatorReward(self, discordID):
		donatorReward = DB.fetchOne("SELECT DonatorReward FROM Economy WHERE DiscordID = ?;", [discordID])[0]
		return donatorReward


	def getMultiplier(self, user):
		multiplier = DB.fetchOne("SELECT Multiplier FROM Economy WHERE DiscordID = ?;", [user.id])[0]
		return multiplier


	async def subtractBet(self, user, amntBet): # subtracts the bet users place when they play games
		if not await self.accCheck(user):
			return False
		balance = await self.getBalance(user)
		if amntBet <= balance and amntBet > 0:
			DB.update("UPDATE Economy SET Credits = Credits - ? WHERE DiscordID = ?;", [amntBet, user.id])
			return True # return 1 if user has enough $$$ to bet their amount entered
		else:
			return False # return 0 if user trying to bet more $$$ than they have


	async def addWinnings(self, discordID, winnings): # add the amount won 
		DB.update("UPDATE Economy SET Credits = Credits + ? WHERE DiscordID = ?;", [math.ceil(winnings), discordID])


	async def getBalance(self, user):
		balance = DB.fetchOne("SELECT Credits FROM Economy WHERE DiscordID = ?;", [user.id])[0]
		return balance
	

	async def getInventory(self, user): # grabs all the crates and keys from database
		inv = DB.fetchOne("SELECT Crates, Keyss FROM Inventory WHERE DiscordID = ?;", [user.id])
		crates = inv[0]
		keys = inv[1]
		return crates, keys


	async def subtractInv(self, discordId, amnt): # called when people open crates (subtracts them from inv.)
		DB.update("UPDATE Inventory SET Crates = Crates - ?, Keyss = Keyss - ? WHERE DiscordID = ?;", [amnt, amnt, discordId])


	@commands.command()
	async def top(self, ctx): # scoreboard to display top 10 richest individuals
		conn = sqlite3.connect(config.db)
		sql = f"""SELECT DiscordID, Credits
				  FROM Economy"""
		cursor = conn.execute(sql)
		data = cursor.fetchall() 
		conn.close()

		data = sorted(data, key = lambda x: x[1], reverse=True) # sort rows by credits  

		topUsers = ""
		count = 1
		for x in data: 
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
			await ctx.invoke(self.bot.get_command('start'))

		if await self.getBalance(usr) < 1025:
			await ctx.send("You need at least 1025 credits to use this command.")
			return

		name = usr.name

		conn = sqlite3.connect(config.db)
		sql = f"""SELECT DiscordID, Credits
				  FROM Economy"""
		cursor = conn.execute(sql) 
		# conn.commit()
		records = cursor.fetchall() 
		conn.close()

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
		userAcc = DB.fetchOne("SELECT 1 FROM Economy WHERE DiscordID = ?;", [user.id])
		if userAcc: # getRow will not be None if account is found, therefor return True
			return True
		
		return False

	async def notEnoughMoney(self, ctx):
		embed = discord.Embed(color=1768431, title=f"{self.bot.user.name} | {str(ctx.command).title()}")
		embed.set_thumbnail(url=ctx.author.avatar_url)
		embed.add_field(name="ERROR", value="You do not have enough credits to do that.")

		embed.set_footer(text=ctx.author)

		await ctx.send(embed=embed)


	async def getInput(self, ctx, user, timeout):
		def is_me(m):
			return m.author == user
		try:
			msg = await self.bot.wait_for('message', check=is_me, timeout=timeout)
		except asyncio.TimeoutError:
			raise Exception("timeoutError")
		return msg




def setup(bot):
	bot.add_cog(Economy(bot))