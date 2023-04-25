# economy-related stuff like betting and gambling, etc.

import nextcord
from nextcord.ext import commands
from nextcord import Interaction

import cooldowns, asyncio, random, math

from db import DB

class Economy(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.coin = "<:coins:585233801320333313>"


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
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author)
	async def rewards(self, interaction:Interaction):

		dailyReward = await self.bot.get_cog("Daily").getDailyReward(interaction)
		multiplier, expiration = self.bot.get_cog("Multipliers").getMultiplierAndExpiration(interaction.user)

		embed = nextcord.Embed(color=1768431, title=self.bot.user.name)
		embed.add_field(name = "Daily", value = f"{dailyReward}{self.coin}", inline=True)
		embed.add_field(name = "Multiplier", value = f"{multiplier}x", inline=True)
		if expiration:
			embed.add_field(name = "Expires In", value=f"{expiration}", inline=True)


		# embed.add_field(name = "Weekly", value = f"12500{self.coin}", inline=False)
		# embed.add_field(name = "Monthly", value = f"36000{self.coin}", inline=True)

		if self.isDonator(interaction.user.id):
			embed.add_field(name = "_ _\nDonator Reward", value = f"{self.getDonatorReward(interaction.user.id)}{self.coin}", inline=False)
		else:
			embed.add_field(name = "_ _\nDonator Reward", value = f"You are not a donator", inline=False)
		await interaction.send(embed=embed)
		

	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author)
	async def balance(self, interaction:Interaction, user:nextcord.Member=None):
		if not user:
			user = interaction.user
			pronouns = "You"
		else:
			pronouns = "They"

		balance = await self.getBalance(user)
		crates, keys = self.bot.get_cog("Inventory").getInventory(user)

		embed = nextcord.Embed(color=1768431)
		embed.add_field(name = "Credits", value = f"{pronouns} have **{balance:,}**{self.coin}", inline=False)
		embed.add_field(name = "_ _\nCrates", value = f"{pronouns} have **{crates}** crates", inline=True)
		embed.add_field(name = "_ _\nKeys", value = f"{pronouns} have **{keys}** keys", inline=True)
		embed.set_footer(text=f"Use /vote, /search, /daily, and /work to get credits")
		
		await interaction.send(embed=embed)
		
	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author)
	async def search(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431)
		if await self.getBalance(interaction.user) < 300:
			amnt = random.randint(50, 250)
			await self.addWinnings(interaction.user.id, amnt)
			balance = await self.getBalance(interaction.user)
			
			embed.add_field(name = f"You found {amnt}{self.coin}", value = f"You have {balance}{self.coin}", inline=False)
		else:
			embed.add_field(name = f"Error", value = f"{interaction.user.mention}, you can only use this if you have less than 300{self.coin}.", inline=False)

		await interaction.send(embed=embed)
		
	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author)
	async def freemoney(self, interaction:Interaction):
		prefix = "/"
		embed = nextcord.Embed(color=1768431, title=self.bot.user.name)
		embed.add_field(name="Free Money Commands", value=f"`{prefix}vote`\n`{prefix}search`\n`{prefix}daily`\n`{prefix}weekly`\n`{prefix}monthly`\n`{prefix}work`")
		await interaction.send(embed=embed)

	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author)
	async def donator(self, interaction:Interaction):
		if not self.isDonator(interaction.user.id):
			embed = nextcord.Embed(color=1768431, title=self.bot.user.name)
			embed.add_field(name = f"Donator Reward", value = "To be able to claim the Donator Reward, you first need to donate!\n" +
																f"Join the server shown in the /help menu to learn how!", inline=False)
			await interaction.send(embed=embed)
			return

		donatorReward = self.getDonatorReward(interaction.user.id)
		multiplier = self.bot.get_cog("Multipliers").getMultiplier(interaction.user)
		extraMoney = int(donatorReward * (multiplier - 1))
		await self.addWinnings(interaction.user.id, donatorReward + extraMoney)

		balance = await self.getBalance(interaction.user)
		embed = nextcord.Embed(color=1768431, title=self.bot.user.name)
		embed.add_field(name = f"You got {donatorReward:,} {self.coin}", 
						value = f"You have {balance:,} credits\nMultiplier: {multiplier}x\nExtra Money: {extraMoney:,}", inline=False)
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
			return True # return 1 if user has enough $$$ to bet their amount entered
		else:
			return False # return 0 if user trying to bet more $$$ than they have


	async def addWinnings(self, discordid, winnings): # add the amount won 
		DB.update("UPDATE Economy SET Credits = Credits + ? WHERE DiscordID = ?;", [math.ceil(winnings), discordid])


	async def getBalance(self, user):
		balance = DB.fetchOne("SELECT Credits FROM Economy WHERE DiscordID = ?;", [user.id])[0]
		return balance
	

	@nextcord.slash_command()
	async def top(self, interaction:Interaction, option = nextcord.SlashOption(
																required=False,
																name="option", 
																choices=("Balance", "Level", "Profit"))):
		

		if option and option != "Balance":
			if option == "Level":
				sql = f"""SELECT DiscordID, Level
					  	  FROM Economy ORDER BY Level DESC LIMIT 10"""
			elif option == "Profit":
				sql = f"""SELECT DiscordID, Profit
					  	  FROM Totals ORDER BY Profit DESC LIMIT 10"""
		else:
			sql = f"""SELECT DiscordID, Credits
					  FROM Economy ORDER BY Credits DESC LIMIT 10"""
		
		topUsers = ""
		count = 1
		data = DB.fetchAll(sql, None)
		for x in data: 
			user = await self.bot.fetch_user(x[0]) # grab the user from the current record
			topUsers += f"{count}. < {user.name} > - " + "{:,}".format(x[1]) + "\n"

			count += 1 # number the users from 1 - 10

		await interaction.send(f"```MD\nTop 10\n======\n{topUsers}```") # send the list with the top 10


	@nextcord.slash_command()
	async def position(self, interaction:Interaction, usr: nextcord.Member=None, option = nextcord.SlashOption(
																required=False,
																name="option", 
																choices=("Balance", "Level", "Profit"))):
		if not usr:
			usr = interaction.user

		if await self.getBalance(usr) < 5000:
			await interaction.send("You need at least 5,000 credits to use this command.")
			return

		if option and option != "Balance":
			if option == "Level":
				sql = f"""SELECT DiscordID, Level
					  	  FROM Economy ORDER BY Level DESC LIMIT 10"""
			elif option == "Profit":
				sql = f"""SELECT DiscordID, Profit
					  	  FROM Totals ORDER BY Profit DESC LIMIT 10"""
		else:
			sql = f"""SELECT DiscordID, Credits
					  FROM Economy ORDER BY Credits DESC LIMIT 10"""
		
		data = DB.fetchAll(sql, None)

		pos = 0
		for x in data:
			if str(usr.id) == x[0]:
				break
			pos += 1

		diff = ""
		if pos > 0:
			diff = f" and needs {str(data[pos-1][1] - data[pos][1] + 1)} coin(s) to beat the person above them"
		# else:
		# 	diff = " so no one is beating them!"
		topUsers = ""
		for x in range(-3, 4):
			if pos + x < 0 or pos + x > len(data):
				continue
			user = await self.bot.fetch_user(data[pos+x][0])
			if x == 0:
				topUsers += f"** {pos+x+1}. < {user.name} > - {data[pos+x][1]} **\n"
			else:
				topUsers += f"{pos+x+1}. < {user.name} > - {data[pos+x][1]}\n"

		await interaction.send(f"```MD\n{user.name} is #{pos+1}{diff}\n======\n{topUsers}```") # send the list with the top 10



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


	async def getInput(self, interaction:Interaction, user, timeout):
		def is_me(m):
			return m.author == user
		try:
			msg = await self.bot.wait_for('message', check=is_me, timeout=timeout)
		except asyncio.TimeoutError:
			raise Exception("timeoutError")
		return msg




def setup(bot):
	bot.add_cog(Economy(bot))