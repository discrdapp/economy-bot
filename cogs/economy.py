# economy-related stuff like betting and gambling, etc.

import nextcord
from nextcord.ext import commands
from nextcord import Interaction

import cooldowns, asyncio, random, math

import emojis
from db import DB
from cogs.totals import log

class Economy(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot


	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author)
	async def start(self, interaction:Interaction):
		await self.StartPlaying(interaction, interaction.user)

	async def StartPlaying(self, interaction:Interaction, user:nextcord.Member=None):
		if not user:
			user = interaction.user 
		embed = nextcord.Embed(color=1768431, title=self.bot.user.name)
		embed.set_thumbnail(url=user.avatar)
		embed.set_footer(text=user)
		if await self.accCheck(user):
			embed.description = "You are already registered, silly"
			await interaction.send(embed=embed)
			return
		DB.insert('INSERT INTO Economy(DiscordID) VALUES (?);', [user.id])
		DB.insert('INSERT INTO Totals(DiscordID) VALUES (?);', [user.id])
		log(interaction.user.id, 0, 0, "Registered", 2500)

		embed.description = f"You are now successfully registered. Enjoy {self.bot.user.name}."

		# if interaction.application_command.qualified_name == 'start'
		# 	await interaction.send(embed=embed)
		# else
		await interaction.send(embed=embed)

	async def GetBetAmount(self, interaction:Interaction, amntbet):
		if amntbet.isdigit():
			return int(amntbet)
		if amntbet == "all" or amntbet == "allin" or amntbet == "everything":
			return await self.getBalance(interaction.user)
		if amntbet == "half":
			return math.floor(await self.getBalance(interaction.user) / 2)
		if amntbet == "third":
			return math.floor(await self.getBalance(interaction.user) / 3)
		if amntbet == "fourth":
			return math.floor(await self.getBalance(interaction.user) / 4)
		if "%" == amntbet[-1]:
			return math.floor(await self.getBalance(interaction.user) * (int(amntbet.replace('%','')) / 100))
		if "." in amntbet and amntbet[0] == "0":
			return math.floor(await self.getBalance(interaction.user) * float(amntbet))
		if "/" in amntbet:
			pos = amntbet.find("/")
			return math.floor(await self.getBalance(interaction.user) * float(int(amntbet[:pos]) / int(amntbet[pos+1:])))
		raise commands.BadArgument(f'You entered {amntbet} for the amount you want to bet. Please enter a number instead.')

	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='rewards')
	async def rewards(self, interaction:Interaction):

		dailyReward = await self.bot.get_cog("Daily").getDailyReward(interaction)
		multiplier, expiration = self.bot.get_cog("Multipliers").getMultiplierAndExpiration(interaction.user.id)

		embed = nextcord.Embed(color=1768431, title=self.bot.user.name)
		embed.add_field(name = "Daily", value = f"{dailyReward}{emojis.coin}", inline=True)
		embed.add_field(name = "Weekly", value = f"12,500{emojis.coin}", inline=True)
		embed.add_field(name = "Monthly", value = f"36,000{emojis.coin}", inline=True)
		embed.add_field(name = "Multiplier", value = f"{multiplier}x", inline=True)
		if expiration:
			embed.add_field(name = "Expires In", value=f"{expiration}", inline=True)


		# embed.add_field(name = "Weekly", value = f"12500{emojis.coin}", inline=False)
		# embed.add_field(name = "Monthly", value = f"36000{emojis.coin}", inline=True)

		if self.isDonator(interaction.user.id):
			embed.add_field(name = "_ _\nDonator Reward", value = f"{self.getDonatorReward(interaction.user.id)}{emojis.coin}", inline=False)
		else:
			embed.add_field(name = "_ _\nDonator Reward", value = f"You are not a donator", inline=False)

		embed.set_footer(text="Don't forget to /work /vote /beg and /crime for extra credits")
		await interaction.send(embed=embed)


	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='balance')
	async def balance(self, interaction:Interaction, user:nextcord.Member=None):
		embed = nextcord.Embed(color=1768431)
		if not user:
			user = interaction.user
			pronouns = "You"
		else:
			pronouns = "They"
			if not await self.accCheck(user):
				embed.description = "User has not registered yet. They need to play a game or use `/start` to register."
				await interaction.send(embed=embed, ephemeral=True)
				return

		balance = await self.getBalance(user)
		cryptoBalances = DB.fetchAll(f"SELECT Name, Quantity FROM Crypto WHERE DiscordID = ?;", [interaction.user.id])
		# crates, keys = self.bot.get_cog("Inventory").getInventory(user)

		embed.add_field(name = "Credits", value = f"{pronouns} have **{balance:,}**{emojis.coin}", inline=False)

		if not cryptoBalances:
			embed.add_field(name="Crypto", value="You have no crypto.")
		else:
			for crypto in cryptoBalances:
				if crypto[0] == "Bitcoin":
					emoji = emojis.bitcoinEmoji
				elif crypto[0] == "Litecoin":
					emoji = emojis.litecoinEmoji
				elif crypto[0] == "Ethereum":
					emoji = emojis.ethereumEmoji
				
				embed.add_field(name=f"{crypto[0]} {emoji}", value=crypto[1])

		# embed.add_field(name = "_ _\nCrates", value = f"{pronouns} have **{crates}** crates", inline=True)
		# embed.add_field(name = "_ _\nKeys", value = f"{pronouns} have **{keys}** keys", inline=True)
		embed.set_footer(text="Want easy money? Don't forget to check out your /rewards")
		
		await interaction.send(embed=embed)
		
	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='search')
	async def search(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431)
		if await self.getBalance(interaction.user) < 300:
			amnt = random.randint(50, 250)
			await self.addWinnings(interaction.user.id, amnt)
			balance = await self.getBalance(interaction.user)
			
			embed.add_field(name = f"You found {amnt:,}{emojis.coin}", value = f"You have {balance:,}{emojis.coin}", inline=False)
		else:
			embed.add_field(name = f"Error", value = f"{interaction.user.mention}, you can only use this if you have less than 300{emojis.coin}.", inline=False)

		await interaction.send(embed=embed)
		
	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='freemoney')
	async def freemoney(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431, title=self.bot.user.name)
		embed.add_field(name="Free Money Commands", value="`/vote`\n`/search`\n`/daily`\n`/weekly`\n`/monthly`\n`/work`\n`/crime`\n`/beg`")
		await interaction.send(embed=embed)

	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='donator')
	async def donator(self, interaction:Interaction):
		if not self.isDonator(interaction.user.id):
			embed = nextcord.Embed(color=1768431, title=self.bot.user.name)
			embed.add_field(name = f"Donator Reward", value = "To be able to claim the Donator Reward, you first need to donate!\n" +
																f"Join the server shown in the /help menu to learn how!", inline=False)
			await interaction.send(embed=embed)
			return

		donatorReward = self.getDonatorReward(interaction.user.id)
		multiplier = self.bot.get_cog("Multipliers").getMultiplier(interaction.user.id)
		extraMoney = int(donatorReward * (multiplier - 1))
		logID = await self.addWinnings(interaction.user.ii, donatorReward, giveMultiplier=True, activityName="Donator Reward", amntBet=0)

		balance = await self.getBalance(interaction.user)
		embed = nextcord.Embed(color=1768431, title=self.bot.user.name)
		embed.add_field(name = f"You got {donatorReward:,} {emojis.coin}", 
						value = f"You have {balance:,} credits\nMultiplier: {multiplier}x\nExtra Money: {extraMoney:,}", inline=False)
		embed.set_footer(text=f"Log ID: {logID}")
		await interaction.send(embed=embed)


	def isDonator(self, discordid):
		donatorCheck = DB.fetchOne("SELECT 1 FROM Donators WHERE DiscordID = ?;", [discordid])
		return donatorCheck

	def getDonatorReward(self, discordid):
		donatorReward = DB.fetchOne("SELECT DonatorReward FROM Donators WHERE DiscordID = ?;", [discordid])
		if donatorReward:
			return donatorReward[0]
		return None


	async def subtractBet(self, user, amntbet): # subtracts the bet users place when they play games
		if not await self.accCheck(user):
			return False
		balance = await self.getBalance(user)
		if amntbet <= balance and amntbet > 0:
			DB.update("UPDATE Economy SET Credits = Credits - ? WHERE DiscordID = ?;", [amntbet, user.id])
			
			# add xp
			return True # return 1 if user has enough $$$ to bet their amount entered
		else:
			return False # return 0 if user trying to bet more $$$ than they have


	async def addWinnings(self, discordid, winnings, giveMultiplier=False, activityName=None, amntBet=None): # add the amount won 
		if winnings > 0 and giveMultiplier:
			multiplier = self.bot.get_cog("Multipliers").getMultiplier(discordid)
			if multiplier > 1:
				if amntBet > winnings: profitAmnt = amntBet - winnings
				else: profitAmnt = winnings - amntBet
				extraMoney = int(profitAmnt * (multiplier - 1))
				winnings += extraMoney
		if winnings != 0:
			DB.update("UPDATE Economy SET Credits = Credits + ? WHERE DiscordID = ?;", [math.ceil(winnings), discordid])

		gameID = None
		balance = DB.fetchOne("SELECT Credits FROM Economy WHERE DiscordID = ?;", [discordid])[0]
		if activityName and "Bought" in activityName: # if using shop
			gameID = log(discordid, winnings, 0, activityName, balance)
		elif activityName and amntBet != None:
			gameID = log(discordid, amntBet, winnings, activityName, balance)
			
		return gameID




	async def getBalance(self, user: nextcord.User):
		balance = DB.fetchOne("SELECT Credits FROM Economy WHERE DiscordID = ?;", [user.id])[0]
		return balance
	

	@nextcord.slash_command()
	@cooldowns.cooldown(1, 120, bucket=cooldowns.SlashBucket.author, cooldown_id='top')
	async def top(self, interaction:Interaction, 
			   option = nextcord.SlashOption(
					required=False,
					name="option", 
					choices=("Balance", "Level", "Profit")), 
				local = nextcord.SlashOption(
					required=False,
					name="local", 
					choices=("local", "global"))):
		
		if not self.bot.get_cog("XP").IsHighEnoughLevel(interaction.user.id, 2):
			raise Exception("lowLevel 2")

		if option and option != "Balance":
			if option == "Level":
				sql = f"SELECT DiscordID, Level FROM Economy"
				orderBy = "Level"
			elif option == "Profit":
				sql = f"SELECT DiscordID, Profit FROM Totals"
				orderBy = "Profit"
		else:
			option = "Balance"
			sql = f"SELECT DiscordID, Credits FROM Economy"
			orderBy = "Credits"
		
		topUsers = ""
		count = 1
		if local == "global":
			sql += f" ORDER BY {orderBy} DESC LIMIT 10;"
			data = DB.fetchAll(sql)

		else:
			local = "local"
			data = DB.fetchAll(f"{sql} WHERE DiscordID IN (SELECT DiscordID FROM Guilds WHERE GuildID = '{interaction.guild.id}') ORDER BY {orderBy} DESC LIMIT 10;")


		for x in data: 
			user = await self.bot.fetch_user(x[0]) # grab the user from the current record
			topUsers += f"{count}. < {user.name} > - " + "{:,}".format(x[1]) + "\n"

			count += 1 # number the users from 1 - 10
		await interaction.send(f"```MD\n{local.title()} Leaderboards Top 10 for {option}\n======\n{topUsers}```Use `/opt in` to add yourself to the local leaderboard") # send the list with the top 10


	@nextcord.slash_command()
	@cooldowns.cooldown(1, 30, bucket=cooldowns.SlashBucket.author, cooldown_id='position')
	async def position(self, interaction:Interaction, usr: nextcord.Member=None, option = nextcord.SlashOption(
																required=False,
																name="option", 
																choices=("Balance", "Level", "Profit"))):
		if not usr:
			usr = interaction.user

		if not self.bot.get_cog("XP").IsHighEnoughLevel(interaction.user.id, 2):
			raise Exception("lowLevel 2")

		if await self.getBalance(usr) < 5000:
			await interaction.send("You need at least 5,000 credits to use this command.")
			return


		if option and option != "Balance":
			if option == "Level":
				sql = f"""SELECT Position from (SELECT ROW_NUMBER () OVER ( 
								ORDER BY Level DESC
							) Position, DiscordID
						  FROM Economy) WHERE DiscordID = ?;"""
			elif option == "Profit":
				sql = f"""SELECT Position from (SELECT ROW_NUMBER () OVER ( 
								ORDER BY Profit DESC
							) Position, DiscordID
						  FROM Totals) WHERE DiscordID = ?;"""
		else:
			sql = f"""SELECT Position from (SELECT ROW_NUMBER () OVER ( 
								ORDER BY Credits DESC
							) Position, DiscordID
						  FROM Economy) WHERE DiscordID = ?;"""
		
		position = DB.fetchOne(sql, [usr.id])[0]

		await interaction.send(f"You are in position #{position}") # send the list with the top 10


	async def accCheck(self, user):
		# checks if they already have a wallet in database
		userAcc = DB.fetchOne("SELECT 1 FROM Economy WHERE DiscordID = ?;", [user.id])
		if userAcc: # getRow will not be None if account is found, therefor return True
			return True
		
		return False

	async def notEnoughMoney(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | {str(interaction.application_command.qualified_name).title()}")
		embed.set_thumbnail(url=interaction.user.avatar)
		embed.add_field(name="ERROR", value="You do not have enough credits to do that or you are trying to bet an amount less than 1.")

		embed.set_footer(text=interaction.user)

		await interaction.send(embed=embed)


def setup(bot):
	bot.add_cog(Economy(bot))