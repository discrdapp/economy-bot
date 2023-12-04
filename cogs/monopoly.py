import nextcord
from nextcord.ext import commands, tasks
from nextcord import Interaction

# import cooldowns
from random import randint, randrange, choice
import asyncio, cooldowns, datetime

import emojis
from db import DB
import config
from cogs.util import SendConfirmButton

gameStartingTimes = list()
gameEndingTimes = list()
for x in range(0, 24, 2):
	gameStartingTimes.append(datetime.time(hour=x, minute=0, second=0))
	gameEndingTimes.append(datetime.time(hour=x, minute=40, second=0))


class Monopoly(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.table = "۝"
		self.person = "웃"

		self.tables = ["""
				 
\u1CBC\u1CBC
\u1CBC\u1CBC۝
\u1CBC\u1CBC۝
\u1CBC\u1CBC
\n
""",
# 1
"""
\u1CBC\u1CBC
웃۝
\u1CBC\u1CBC۝
\u1CBC\u1CBC
\n
""",
# 2
"""
\u1CBC\u1CBC
웃۝웃
\u1CBC\u1CBC۝
\u1CBC\u1CBC
\n
""",
# 3
"""
\u1CBC\u1CBC
웃۝웃
웃۝
\u1CBC\u1CBC
\n
""",
# 4
"""
\u1CBC\u1CBC
웃۝웃
웃۝웃
\u1CBC\u1CBC
\n
""",
# 5
"""
\u1CBC\u1CBC웃
웃۝웃
웃۝웃
\u1CBC\u1CBC
\n
""",
# 6
"""
\u1CBC\u1CBC웃
웃۝웃
웃۝웃  
\u1CBC\u1CBC웃
\n
""", 
# 7
"""
\u1CBC웃웃
웃۝웃
웃۝웃  
\u1CBC\u1CBC웃
\n
""",
# 8
"""
\u1CBC웃웃
웃۝웃
웃۝웃  
\u1CBC웃웃
\n
""",
# 9
"""
웃웃웃
웃۝웃
웃۝웃  
\u1CBC웃웃
\n
""",
# 10
"""
웃웃웃
웃۝웃
웃۝웃  
웃웃웃
\n
"""
		]

		self.isGameInProgress = False
	
	@commands.Cog.listener()
	async def on_ready(self):
		if not self.StartGame.is_running():
			self.StartGame.start()
		if not self.EndGame.is_running():
			self.EndGame.start()

	# runs every 2 hours, on the hour
	@tasks.loop(time=gameStartingTimes)
	# @tasks.loop(seconds=15)
	async def StartGame(self):
		try:
			self.isGameInProgress = True

			# remove people who are expired
			discordIDs = dict()

			peopleDatesToRemove = list()
			expires = DB.fetchAll("SELECT DiscordID, Expires FROM MonopolyPeople;")
			if expires:
				for person in expires:
					expireDate = datetime.datetime.strptime(person[1], '%Y-%d-%m %H:%M:%S')
					if expireDate < datetime.datetime.now():
						peopleDatesToRemove.append(person[1])
						if person[0] in discordIDs.keys():
							discordIDs[person[0]] += 1
						else:
							discordIDs[person[0]] = 1

			if peopleDatesToRemove:
				# for discordID in discordIDs:
					# DB.update("UPDATE Monopoly SET PeopleCount = PeopleCount - ? WHERE DiscordID = ?;", [discordIDs[discordID], discordID])
				sqlStatement = "DELETE FROM MonopolyPeople WHERE Expires IN ("
				for date in peopleDatesToRemove:
					sqlStatement += f"'{date}', "
				sqlStatement = sqlStatement[:-2] + ");"
				DB.delete(sqlStatement)
		except Exception as e:
			print(f"error in StartGame monopoly:\n{e}")

	
	# runs every 2 hours, 00:40 after the hour
	@tasks.loop(time=gameEndingTimes)
	# @tasks.loop(seconds=20)
	async def EndGame(self):
		self.isGameInProgress = False
		try:
			data = DB.fetchAll("SELECT COUNT(1), DiscordID FROM MonopolyPeople GROUP BY DiscordID;")

			if not data:
				return

			#80% they'll earn money
			#10% they'll break even
			#10% they'll be negative


			globalTotalEarnings = 0
			values = list()
			for user in data:
				peopleCount = user[0]
				discordID = user[1]

				userTotalEarnings = 0
				for _ in range(0, peopleCount):
					makeMoney = randint(1, 10)
					if makeMoney == 1:
						earnings = 0
					elif makeMoney == 2:
						earnings = randrange(-750, -500, 10)
					else:
						earnings = randrange(500, 1000, 10)
					userTotalEarnings += earnings
					values.append(earnings)
				globalTotalEarnings += userTotalEarnings

				DB.update("UPDATE Monopoly SET CreditsToCollect = CreditsToCollect + ? WHERE DiscordID = ?;", [userTotalEarnings, discordID])

				updateSQL = "UPDATE MonopolyPeople SET Earnings = CASE"
				for x in range(0, len(values)):
					updateSQL += f" WHEN ID = {x+1} THEN {values[x]}"
				updateSQL += f" ELSE 0 END WHERE DiscordID = {discordID};"

				DB.update(updateSQL)

				values.clear()


			totalPlayers = DB.fetchOne("SELECT COUNT(1) FROM MonopolyPeople;")[0]

			chnl = self.bot.get_channel(config.channelIDForMonopoly)
			embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Monopoly | Game Start")
			embed.description = f"Game ended. There was {totalPlayers} players, and a total of {globalTotalEarnings:,}{emojis.coin} was earned!"
			await chnl.send(embed=embed)

		except Exception as e:
			print(f"error in StopGame monopoly:\n{e}")


	def GetGameEndTimestamp(self):
		return f"<t:{int(self.EndGame.next_iteration.replace(tzinfo=datetime.timezone.utc).timestamp())}:R>"


	cooldowns.define_shared_cooldown(1, 5, cooldowns.SlashBucket.author, cooldown_id="monopoly")

	@nextcord.slash_command()
	@cooldowns.shared_cooldown("monopoly")
	async def monopoly(self, interaction:Interaction):
		pass

	@monopoly.subcommand(description="Withdraw the credits your people have earned you")
	@cooldowns.shared_cooldown("monopoly")
	async def withdraw(self, interaction:Interaction):
		amnt = DB.fetchOne("SELECT CreditsToCollect FROM Monopoly WHERE DiscordID = ?;", [interaction.user.id])
		if not amnt:
			amnt = 0
		else: amnt = amnt[0]

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Monopoly | Withdraw")
		if amnt <= 0:
			embed.description = f"You have {amnt:,}{emojis.coin} to withdraw. You can only withdraw an amount greater than 0."
			await interaction.send(embed=embed)
			return

		DB.update("UPDATE Monopoly SET CreditsToCollect = 0 WHERE DiscordID = ?;", [interaction.user.id])
		logID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, amnt, giveMultiplier=False, activityName="BJ", amntBet=0)

		embed.description = f"Withdrew {amnt:,} {emojis.coin}"
		embed.set_footer(text=f"LogID: {logID}")

		await interaction.send(embed=embed)

	
	@monopoly.subcommand()
	@cooldowns.shared_cooldown("monopoly")
	async def stats(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Monopoly | Stats")

		creditsToWithdraw = DB.fetchOne("SELECT CreditsToCollect FROM Monopoly WHERE DiscordID = ?;", [interaction.user.id])
		if creditsToWithdraw and creditsToWithdraw[0] > 0:
			embed.set_footer(text=f"You have {creditsToWithdraw[0]:,} credits ready for withdrawal")

		if self.isGameInProgress:
			embed.description = f"Game is currently in progress. Please check back {self.GetGameEndTimestamp()}"
			await interaction.send(embed=embed)
			return
		data = DB.fetchAll("SELECT Name, Earnings FROM MonopolyPeople WHERE DiscordID = ?;", [interaction.user.id])
		if not data:
			embed.description = "You had no people who played in the previous game"
			await interaction.send(embed=embed)
			return
		
		msg = ""
		for count in range(len(data)):
			name = data[count][0]
			earnings = data[count][1]

			msg += f"{name}\n:man_standing:\t"
			if earnings == -99999:
				msg += "has not played yet\n"
			elif earnings > 0:
				msg += f"earned {earnings:,}\n"
			elif earnings < 0:
				msg += f"lost {earnings:,}\n"
			elif earnings == 0:
				msg += f"broke even\n"
		
		embed.description = msg
		await interaction.send(embed=embed)


	@monopoly.subcommand()
	async def help(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Monopoly | Help")

		msg = ""
		msg += "Welcome to your warehouse. You're training people to play blackjack and earn you money. You will need to buy tables and hire people to gamble for you.\n\n"
		msg += f"Is game currently in progress: {self.isGameInProgress}\n"
		if self.isGameInProgress:
			msg += f"Game will be finished {self.GetGameEndTimestamp()}\n"

		msg += "\n**What does this mean?**\n*Every two hours on the hour* (ex: 2:00, 4:00, 6:00), a \"game\" starts, meaning your hired people will go and try to earn money for you.\n"
		msg += "\nEach game lasts only 40 minutes. This is when your people will come back and give you their earnings! Beware, there's a small chance they can lose money too!"

		msg += "\n\nWant more info? [Click here](https://docs.justingrah.am/thecasino/monopoly)"

		embed.description = msg
		await interaction.send(embed=embed)


	@monopoly.subcommand()
	@cooldowns.shared_cooldown("monopoly")
	async def view(self, interaction:Interaction):
		DB.insert('INSERT OR IGNORE INTO Monopoly(DiscordID) VALUES (?);', [interaction.user.id])
		data = DB.fetchOne("SELECT COUNT(1) FROM MonopolyPeople WHERE DiscordID = ?;", [interaction.user.id])

		tableCount = self.bot.get_cog("Inventory").getCountForItem(interaction.user, 'Table')

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Monopoly | View")

		if data[0] == 0 or not self.isGameInProgress:
			peopleLeftToSeat = data[0]
		else:
			peopleLeftToSeat = 0
			embed.description = f"Game currently in progress! Your people will come back {self.GetGameEndTimestamp()}"
		

		for _ in range(tableCount):
			if peopleLeftToSeat >= 10:
				embed.add_field(name="_ _", value=self.tables[-1])
				peopleLeftToSeat -= 10
			else:
				embed.add_field(name="_ _", value=self.tables[peopleLeftToSeat])
				peopleLeftToSeat = 0

		# for x in self.tables:
		# 	embed.add_field(name="_ _", value=x)

		await interaction.send(embed=embed)
	
	@monopoly.subcommand()
	@cooldowns.shared_cooldown("monopoly")
	async def hire(self, interaction:Interaction):
		pass

	@hire.subcommand()
	# @cooldowns.shared_cooldown("monopoly")
	@cooldowns.cooldown(1, 25, bucket=cooldowns.SlashBucket.author, cooldown_id='person')
	async def person(self, interaction:Interaction, amnt:int):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Monopoly | Hire | Person")
		
		if self.isGameInProgress:
			embed.description = (f"You cannot hire people while a game is in progress. Please check back <t:{int(self.EndGame.next_iteration.replace(tzinfo=datetime.timezone.utc).timestamp())}:R>")
			await interaction.send(embed=embed, ephemeral=True)
			return
		cost = amnt*10000
		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		if balance < cost:
			embed.description = f"That will cost you {round(cost):,}{emojis.coin}, but you only have {balance:,}{emojis.coin}"
			await interaction.send(embed=embed, ephemeral=True)
			return
		data = DB.fetchOne("SELECT COUNT(*) FROM MonopolyPeople WHERE DiscordID = ?;", [interaction.user.id])
		tableCount = self.bot.get_cog("Inventory").getCountForItem(interaction.user, 'Table')
		peopleCount = data[0]

		seatsAvailable = 10*tableCount-peopleCount

		if seatsAvailable < amnt:
			embed.description = "You do not have enough seats available on your tables."
			await interaction.send(embed=embed, ephemeral=True)
			return

		if not await SendConfirmButton(interaction, f"This will cost you {cost:,}{emojis.coin}. Proceed?"):
			embed.description = "You have cancelled this transaction."
			await interaction.send(embed=embed, ephemeral=True)
			return
		
		logID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, -cost, activityName=f"Bought {amnt} People")
		DB.insert('INSERT OR IGNORE INTO Monopoly(DiscordID) VALUES (?);', [interaction.user.id])

		expires = datetime.datetime.now() + datetime.timedelta(days=2)
		count = peopleCount + 1
		for _ in range(amnt):
			name = choice(["Zeus", "Apollo", "Heracles", "Poseidon", "Hermes", "Ares", "Hephaestus", "Hades", "Chronos", 
				  "Dionysus", "Eros", "Helios", "Paean", "Thanatos", "Triton", "Chaos", "Notus", "Pan", "Erebus", "Oceanus", 
				  "Momus", "Prometheus", "Boreas", "Morpheus", "Hesperus", "Pontus", "Hypnos", "Nereus", "Plutus", "Aeolus", 
				  "Asclepius", "Ourea", "Tartarus", "Uranus", "Aether", "Cronus", "Hyperion", "Iapetus", "Coeus", "Alastor", 
				  "Dinlas", "Aion", "Priapus", "Kratos", "Crius", "Deimos", "Aristaeus", "Agathodaemon", "Pallas", "Zelus", 
				  "Athena", "Hera", "Artemis", "Aphrodite", "Hestia", "Iris", "Demeter", "Hebe", "Hecate", "Electryone", "Nike", 
				  "Gaia", "Enyo", "Cybele", "Pheme", "Tyche", "Althea", "Eris", "Achlys", "Ananke", "Hemera", "Nemesis", "Nesoi", 
				  "Nyx", "Thalassa", "Elpis", "Tethys", "Theia", "Phoebe", "Themis", "Mnemosyne", "Calliope", "Doris", "Asteria", 
				  "Eileithyia", "Delia", "Selene", "Clio", "Echo", "Ceto", "Electra", "Achelois", "Aura", "Eos", "Metis", "Harmonia", "Brizo", "Atropos", "Thalia", "Circe"])
			# expires = datetime.datetime.now()
			DB.insert("INSERT INTO MonopolyPeople VALUES(?, ?, ?, ?, 0);", [count, interaction.user.id, name, DB.ConvertDatetimeToSQLTime(expires)])

			count += 1

		embed.description = f"You hired {amnt} people for the next 48 hours. They will leave <t:{int(expires.timestamp())}:R>"
		embed.set_footer(text=f"LogID: {logID}")
		await interaction.send(embed=embed)


def setup(bot):
	bot.add_cog(Monopoly(bot))
