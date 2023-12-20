import nextcord
from nextcord.ext import commands
from nextcord import Interaction 

import cooldowns, random, datetime, math, config
from cogs.economy import Economy

import emojis
from db import DB


class Button(nextcord.ui.Button):
	def __init__(self, label, style):
		super().__init__(label=label, style=style)
	
	async def callback(self, interaction:Interaction):
		self.view.stop()
		self.view.job = self.label



class ConfirmButtonView(nextcord.ui.View):
	def __init__(self):
		super().__init__(timeout=20)
		self.doProceed = False

class ConfirmButton(nextcord.ui.Button):
	def __init__(self, label, style):
		super().__init__(label=label, style=style)
	
	async def callback(self, interaction:Interaction):
		assert self.view is not None
		view: ConfirmButtonView = self.view
		
		if self.label == "Confirm":
			view.doProceed = True
		view.stop()


def IsDonatorCheck(userId):
	check = DB.fetchOne("SELECT 1 FROM Donators WHERE DiscordID = ?;", [userId])
	if not check:
		return 1
	return 0

async def SendConfirmButton(interaction:Interaction, msg):
	embed = nextcord.Embed(color=1768431)
	embed.description = msg

	view = ConfirmButtonView()
	view.add_item(ConfirmButton("Confirm", nextcord.ButtonStyle.green))
	view.add_item(ConfirmButton("Reject", nextcord.ButtonStyle.red))

	msgSent = await interaction.send(embed=embed, view=view, ephemeral=True)
	await view.wait()

	await msgSent.delete()

	return view.doProceed

def GetMaxBet(game):
	if game == "Blackjack": return 1000000
	if game == "Coinflip": 	return 1000000
	if game == "Crash": 	return 1000000
	if game == "DOND": 		return 1000000
	if game == "Horse": 	return 1000000
	if game == "Mines": 	return 1000000
	if game == "Poker": 	return 1000000
	if game == "Roulette": 	return 1000000
	if game == "RPS": 		return 1000000
	if game == "Scratch": 	return 1000000
	if game == "Slots": 	return 1000000

	return 1000000


async def PrintProgress(percentFilled):
	if percentFilled <= 0.03:
		percentFilled = 0
	elif percentFilled < 0.1:
		percentFilled = 1
	elif percentFilled >= 0.9:
		percentFilled = 9
	else:
		percentFilled = round(percentFilled * 10)

	topLine = ""
	bottomLine = ""
	for x in range(1, 11):
		if x == 1: # left side 
			if x <= percentFilled:
				topLine += emojis.tlf
				bottomLine += emojis.blf
			else:
				topLine += emojis.tl
				bottomLine += emojis.bl
		elif x == 10: # right side
			if x <= percentFilled:
				topLine += emojis.trf
				bottomLine += emojis.brf
			else:
				topLine += emojis.tr
				bottomLine += emojis.br
		else: # middle
			if x <= percentFilled:
				topLine += emojis.tf
				bottomLine += emojis.bf
			else:
				topLine += emojis.t
				bottomLine += emojis.b


	return topLine + "\n" + bottomLine

class Util(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.jobs = ["Administrative Assistant", "Executive Assistant", "Marketing Manager", "Customer Service Representative", "Nurse Practitioner", "Software Engineer", "Sales Manager", "Data Entry Clerk", "Office Assistant", "Accounting Specialist", "Payroll Specialist", "Dentist", "Registered Nurse", "Pharmacist", "Computer Systems Analyst", "Physician", "Database Administrator", "Software Developer", "Physical Therapist", "Web Developer", "Dental Hygienist", "Occupational Therapist", "Veterinarian", "Computer Programmer", "School Psychologist", "Physical Therapist Assistant", "Interpreter & Translator", "Mechanical Engineer", "Veterinary Technologist & Technician", "Epidemiologist", "IT Manager", "Market Research Analyst", "Diagnostic Medical Sonographer", "Computer Systems Administrator", "Respiratory Therapist", "Medical Secretary", "Civil Engineer", "Substance Abuse Counselor", "Speech-Language Pathologist", "Landscaper & Groundskeeper", "Radiologic Technologist", "Cost Estimator", "Financial Advisor", "Marriage & Family Therapist", "Medical Assistant", "Lawyer", "Accountant", "Compliance Officer", "High School Teacher", "Clinical Laboratory Technician", "Maintenance & Repair Worker", "Bookkeeping, Accounting, & Audit Clerk", "Financial Manager", "Recreation & Fitness Worker", "Insurance Agent", "Elementary School Teacher", "Dental Assistant", "Management Analyst", "Home Health Aide", "Pharmacy Technician", "Construction Manager", "Public Relations Specialist", "Middle School Teacher", "Massage Therapist", "Paramedic", "Preschool Teacher", "Hairdresser", "Marketing Manager", "Patrol Officer", "School Counselor", "Executive Assistant", "Financial Analyst", "Personal Care Aide", "Clinical Social Worker", "Business Operations Manager", "Loan Officer", "Meeting, Convention & Event Planner", "Mental Health Counselor", "Nursing Aide", "Sales Representative", "Architect", "Sales Manager", "HR Specialist", "Plumber", "Real Estate Agent", "Glazier", "Art Director", "Customer Service Representative", "Logistician", "Auto Mechanic", "Bus Driver", "Restaurant Cook", "Child & Family Social Worker", "Administrative Assistant", "Receptionist", "Paralegal", "Cement Mason & Concrete Finisher", "Painter", "Sports Coach", "Teacher Assistant", "Brickmason & Blockmason", "Cashier", "Janitor", "Electrician", "Delivery Truck Driver", "Maid & Housekeeper", "Carpenter", "Security Guard", "Construction Worker", "Fabricator", "Telemarketer"]
		# self.jobs = ["1", "2", "3", "4"]
	
	@nextcord.slash_command()
	@cooldowns.cooldown(1, 180, bucket=cooldowns.SlashBucket.author, cooldown_id='opt')
	async def opt(self, interaction:Interaction,  choice = nextcord.SlashOption(
				required=True,
				name="choice", 
				choices=("in", "out"))):
		if choice == "in":
			DB.insert("INSERT OR IGNORE INTO Guilds VALUES(?, ?);", [interaction.guild.id, interaction.user.id])
			await interaction.send("We've added you to this guild's local leaderboard!")

		elif choice == "out":
			DB.delete("DELETE FROM Guilds WHERE GuildID = ? AND DiscordID = ?;", [interaction.guild.id, interaction.user.id])
			await interaction.send("We've removed you from this guild's local leaderboard!")
	
	@nextcord.slash_command()
	@cooldowns.cooldown(1, 3, bucket=cooldowns.SlashBucket.author, cooldown_id='referral')
	async def referral(self, interaction:Interaction, user:nextcord.Member):
		await interaction.response.defer(with_message=True, ephemeral=True)
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Referrals")

		# make sure user has not used command before
		data = DB.fetchOne("SELECT * FROM UsedReferralCommand WHERE DiscordID = ?;", [interaction.user.id])
		if data:
			embed.description = "You can only use this command once!"

		elif not await self.bot.get_cog("Economy").accCheck(user):
			embed.description = "User has not registered yet. They need to use any command or type `/start` to register."
		
		elif interaction.user.id == user.id:
			embed.description = "You cannot pick yourself!"
		else:
			if not await SendConfirmButton(interaction, f"You will be setting {user.mention} as your referral? You can only use this command once. Proceed?"):
				await interaction.send("Cancelled!", ephemeral=True)
				return
			# add user so he cant use command again
			DB.insert('INSERT INTO UsedReferralCommand VALUES (?);', [interaction.user.id])

			# add refferer to database (if not in it already)
			DB.insert('INSERT OR IGNORE INTO ReferralCount VALUES (?, 0);', [user.id])

			# get referrer's referral count
			count = DB.fetchOne("SELECT Amount FROM ReferralCount WHERE DiscordID = ?;", [user.id])[0]
			cmdUseReward = 20000 # the cmd issuer's reward
			referrerReward = 15000 + (count*1000) # calculate referral reward. 15k + 1000 per user already referred

			# add 1 to the referrer's referral count
			DB.update("UPDATE ReferralCount SET Amount = Amount + 1 WHERE DiscordID = ?;", [user.id])

			usedCmdLogID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, cmdUseReward, activityName="Used /referral", amntBet=0)
			referrerLogID = await self.bot.get_cog("Economy").addWinnings(user.id, referrerReward, activityName=f"Referred {interaction.user.id}", amntBet=0)

			embed.description = f"Thank you for setting your referrer!\
			\nYou received 20,000{emojis.coin} (LogID: {usedCmdLogID}) \n{user.mention} received {referrerReward:,}{emojis.coin} (LogID: {referrerLogID}) for having {count+1} referral(s)."
			embed.set_footer(text=f"You get 15,000 for referring, PLUS an extra 1,000 per extra person!\n(1 = 15k, 2 = 16k, 3 = 17k, etc.)")

		await interaction.send(embed=embed)



	@nextcord.slash_command()
	@cooldowns.cooldown(1, 3600, bucket=cooldowns.SlashBucket.author, cooldown_id='feedback')
	async def feedback(self, interaction:Interaction, 
		    message,
		    type = nextcord.SlashOption(
				required=True,
				name="type", 
				choices=("Bug", "Suggestion", "Question", "Comment"))):

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Feedback")
		embed.description = f"Thank you for your {type}.\nPlease feel free to [join the bot's official support server](https://discord.gg/ggUksVN) if you'd like a response"
		await interaction.send(embed=embed, ephemeral=True)

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | {type}")
		embed.description = message
		embed.set_footer(text=interaction.user)
		ch = self.bot.get_channel(config.channelIDForSuggestions)
		await ch.send(content=f"<@{config.botOwnerDiscordID}>", embed=embed)

	
	@nextcord.slash_command()
	async def cooldown(self, interaction:Interaction):
		msg = ""
		for cmd in self.bot.get_all_application_commands():
			try:
				cooldown = cooldowns.get_shared_cooldown(cmd.qualified_name)
			except:
				continue
			bucket = cooldown.get_bucket(interaction)

			ctp = cooldown._get_cooldown_for_bucket(bucket=bucket)

			if not ctp:
				continue

			if not ctp.next_reset:
				continue


			# resetInCST = ctp.next_reset - datetime.timedelta(hours=5)
			resetInCST = ctp.next_reset

			diff = resetInCST - datetime.datetime.now()

			totalSeconds = round(diff.total_seconds())

			timeLeft = ""
			if totalSeconds > 86400: # days
				timeLeft += f"{math.floor(totalSeconds / 86400)}d"
				totalSeconds = totalSeconds % 86400
			if totalSeconds > 3600: # hours
				timeLeft += f"{math.floor(totalSeconds / 3600)}h"
				totalSeconds = totalSeconds % 3600
			if totalSeconds > 60: # minutes
				timeLeft += f"{math.floor(totalSeconds / 60)}m"
				totalSeconds = totalSeconds % 60
			timeLeft += f"{totalSeconds}s"

			msg += f"{cmd.qualified_name.title()}: **{timeLeft}**\n"
		
		if not msg:
			msg = "You currently have no commands on cooldown!"

		await interaction.send(msg)


	@nextcord.slash_command(description="Quick game. Guess if chosen number is lower than 50 or equal/higher")
	@cooldowns.cooldown(1, 2, bucket=cooldowns.SlashBucket.author, cooldown_id='gamble')
	async def highlow(self, interaction:Interaction, amntbet:int, choice=nextcord.SlashOption(required=True, choices=["high", "low"])):
		await interaction.response.defer(with_message=True)
		deferMsg = await interaction.original_message()

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | HighLow")
		if amntbet < 100:
			raise Exception("minBet 100")

		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, amntbet):
			raise Exception("tooPoor")
		
		number = random.randint(0, 100)

		if (number >= 50 and choice == "high") or (number < 50 and choice == "low"):
			moneyToAdd = amntbet * 2
		else:
			moneyToAdd = 0

		profitInt = moneyToAdd - amntbet
		
		embed.description = f"I chose {number}"
		gameID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, moneyToAdd, giveMultiplier=True, activityName="HighLow", amntBet=amntbet)
		
		
		embed, file = await DB.addProfitAndBalFields(self, interaction, profitInt, embed)

		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		embed = await DB.calculateXP(self, interaction, balance - profitInt, amntbet, embed, gameID)

		await deferMsg.edit(embed=embed, file=file)

		self.bot.get_cog("Totals").addTotals(interaction, amntbet, moneyToAdd, "HighLow")



	@nextcord.slash_command()
	@cooldowns.cooldown(1, 3000, bucket=cooldowns.SlashBucket.author, cooldown_id='dig')
	async def dig(self, interaction:Interaction):
		await interaction.response.defer(with_message=True)
		deferMsg = await interaction.original_message()
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Dig")
		
		if not self.bot.get_cog("Inventory").checkInventoryFor(interaction.user, "Shovel"):
			embed.description = "You need a Shovel to dig.\nYou can buy one from the /shop"
			await deferMsg.edit(embed=embed)
			cooldowns.reset_bucket(self.dig.callback, interaction)
			return
		
		# 33% chance to not get anything
		if random.randint(0, 2) == 0:
			response = random.choice(["You dug for hours, but your fatigue overtook your enthusiasm, and you found nothing.",
						"As you dug, your shovel suddenly snapped, leaving you empty-handed and frustrated.",
						"Despite your determination, the stubborn, compacted dirt resisted your efforts, yielding no results.",
						"You made valiant attempts, but the hardness of the ground thwarted your digging, and you came up empty.",
						"After a short while, you realized the task was more demanding than anticipated and abandoned your search empty-handed.",
						"With each shovelful of earth, your energy waned until you decided to call it quits, having found nothing.",
						"The promise of treasure didn't match the reality of digging through unyielding soil, resulting in a fruitless effort.",
						"You gave it your all, but the tough ground defeated your attempts, and you had to stop with nothing to show.",
						"Your hopes were dashed when your shovel encountered an impenetrable rock, leaving you with empty hands and a weary heart.",
						"As time went on, your enthusiasm waned, and the empty holes in the ground told the story of your unfruitful efforts.",
						"Despite your initial excitement, the lack of immediate success led to a feeling of discouragement and an empty hole.",
						"The ground seemed to hide its treasures well, and despite your best efforts, your digging yielded no rewards.",
						"Your determination was tested by the unforgiving soil, leaving you with sore muscles and nothing but a hole to show for it.",
						"As the hours passed, your shovel's progress became slower, and eventually, you stopped, your hands empty and tired.",
						"With great anticipation, you began to dig, but the reality of empty dirt reminded you that not all searches end in discovery."
			])
			embed.description = response
			await deferMsg.edit(embed=embed)
		# 66% chance to get something
		else:
			pay = random.randrange(5000, 15000)
			logID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, pay, giveMultiplier=False, activityName=f"Dig", amntBet=0)

			embed.description = f"You were given {pay:,}{emojis.coin}"
			embed.set_footer(text=f"Log ID: {logID}")
			await deferMsg.edit(embed=embed)

			if random.randint(0, 1) == 0: # 33% chance to get a random item
				await self.bot.get_cog("Inventory").GiveRandomItem(interaction)

	@nextcord.slash_command()
	@cooldowns.cooldown(1, 1800, bucket=cooldowns.SlashBucket.author, cooldown_id='beg')
	async def beg(self, interaction:Interaction):
		await interaction.response.defer(with_message=True)
		deferMsg = await interaction.original_message()

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Beg")

		# 33% chance to not get anything
		if random.randint(0, 2) == 0:
			embed.description = random.choice(["You extended your hand, hoping for kindness, but the world seemed as tight-fisted as you felt.",
									"Despite your heartfelt plea, the city's bustle drowned out your voice, and your cup remained empty.",
									"Your request for help echoed in the urban chaos, but the only response was silence.",
									"The coins didn't find their way to your palm, and your outstretched hand was met with indifference.",
									"You reached out for aid, but your appeal was lost amidst the crowds and left unanswered.",
									"The streets were unforgiving, and your beggar's plea went unnoticed, leaving you with empty hands.",
									"Your plea faded into the noise of the city, and your attempt to elicit help ended in silence.",
									"Despite your hope, your open hand returned empty, a reflection of the challenges you faced.",
									"The urban rhythm continued, indifferent to your request for assistance, leaving you with nothing.",
									"Your plea for help lingered for a moment, only to be carried away by the wind, unanswered."
									"Despite your heartfelt plea, no one seemed willing to extend a helping hand when you needed it the most.",
									"Just as you thought your luck had turned, a deceitful individual stole all the coins you had received.",
									"The bustling city drowned out your beggar's call, and your efforts to seek assistance went unanswered.",
									"The rhythm of the city carried on, indifferent to your plea for help, leaving you with empty hands.",
									"You humbled yourself and asked for assistance, but your cup remained unfilled and your hopes dashed.",
									"Doors of generosity remained closed, and your request for help left you with a feeling of isolation.",
									"Despite your sign held high, the passersby continued on their way, leaving your cup untouched.",
									"Fate seemed to conspire against you as you sought help, and your plea went unheard and unanswered.",
									"The world moved on, barely noticing your plea, and you were left feeling invisible and alone.",
									"Your attempt at begging led to an unfortunate encounter with a police officer who arrested you.",
									"The generosity you hoped for was nowhere to be found, and your plea was met with silence.",
									"A moment of vulnerability allowed a cunning individual to steal the meager coins you had gathered.",
									"Your humble request for assistance echoed through the city, but the response was disappointing.",
									"As you bared your need for help, the world's indifference left you feeling abandoned and unheard."
			])
			await deferMsg.edit(embed=embed)
		# 67% chance to get something
		else:
			pay = random.randrange(5000, 10000)
			logID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, pay, giveMultiplier=False, activityName=f"Beg", amntBet=0)

			embed.description = f"You were donated {pay:,}{emojis.coin}"
			embed.set_footer(text=f"Log ID: {logID}")
			await deferMsg.edit(embed=embed)

			if random.randint(0, 2) == 0: # 16.5% chance to get a random item
				await self.bot.get_cog("Inventory").GiveRandomItem(interaction)

	@nextcord.slash_command()
	@cooldowns.cooldown(1, 3000, bucket=cooldowns.SlashBucket.author, cooldown_id='crime')
	async def crime(self, interaction:Interaction):
		await interaction.response.defer(with_message=True)
		deferMsg = await interaction.original_message()
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Crime")

		# 33% chance to not get anything
		if random.randint(0, 2) == 0:
			embed.description = random.choice(["You attempted a robbery and got caught!",
				      "Attempting to scam someone, you got scammed yourself and broke even... don't scam again!", 
				      "Successfully stole a bitcoin drive! No bitcoin was on it though...",
				      "You jumped a homeless man, but got nothing because he's homeless... duh!"
			])
			await deferMsg.edit(embed=embed)
		# 67% chance to get something
		else:
			pay = random.randrange(5000, 15000)
			logID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, pay, giveMultiplier=False, activityName=f"Beg", amntBet=0)

			embed.description = f"You were given {pay:,}{emojis.coin}"
			embed.set_footer(text=f"Log ID: {logID}")
			await deferMsg.edit(embed=embed)

			if random.randint(0, 1) == 0: # 25% chance to get a random item
				await self.bot.get_cog("Inventory").GiveRandomItem(interaction)

	@nextcord.slash_command()
	@cooldowns.cooldown(1, 3600, bucket=cooldowns.SlashBucket.author, cooldown_id="work")
	async def work(self, interaction:Interaction):
		await interaction.response.defer(with_message=True, ephemeral=True)
		deferMsg = await interaction.original_message()
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Work")
		embed.description = "What would you like to work as?"

		jobs = random.sample(self.jobs, 3)

		view = nextcord.ui.View(timeout=30)

		job1 = Button(label=jobs[0], style=nextcord.ButtonStyle.green)
		job2 = Button(label=jobs[1], style=nextcord.ButtonStyle.green)
		job3 = Button(label=jobs[2], style=nextcord.ButtonStyle.green)

		view.add_item(job1)
		view.add_item(job2)
		view.add_item(job3)

		await deferMsg.edit(embed=embed, view=view)
		# msg = newMsg.fetch()

		if await view.wait():
			embed.set_footer(text="Timed out. First job auto-picked")
			view.job = job1.label

		if not view.job:
			return
		
		# 25% chance of not getting anything from /work
		if random.randint(0, 3) == 0:
			embed.description = random.choice(["Despite your dedication, the expected paycheck didn't come through due to an unexpected payroll issue.",
									"Your hard work yielded personal growth, but a sudden economic downturn impacted your compensation.",
									"Your effort was commendable, yet a workplace error resulted in your paycheck being delayed or misplaced.",
									"The fruits of your labor were overshadowed by budget cuts, leading to a smaller paycheck than anticipated.",
									"Your work contributed to personal development, but organizational changes led to reduced hours and earnings.",
									"You devoted yourself to your task, but your project's funding fell through, leaving your paycheck empty.",
									"The task you tackled held promise, but an unexpected project cancellation left you without compensation.",
									"Despite your dedication, an unforeseen company restructuring led to job losses, including your paycheck.",
									"Your endeavors were valuable, yet unexpected market shifts resulted in reduced earnings for everyone.",
									"Your hard work increased your skill set, but an unexpected change in job roles led to reduced compensation."
			])
			await deferMsg.edit(embed=embed, view=None)
		# 75% chance to get something
		else:
			pay = random.randrange(6000, 20001)
			logID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, pay, giveMultiplier=False, activityName=f"Work", amntBet=0)

			aan = "an" if view.job[0].lower() in "aeiou" else "a"
			embed.description = f"You worked as {aan} {view.job} and earned {pay:,}{emojis.coin}"
			embed.set_footer(text=f"Log ID: {logID}")
			await deferMsg.edit(embed=embed, view=None)

			if random.randint(0, 2) == 0: # 24.75% chance to get a random item
				await self.bot.get_cog("Inventory").GiveRandomItem(interaction)


	@nextcord.slash_command()
	@cooldowns.cooldown(1, 45, bucket=cooldowns.SlashBucket.author, cooldown_id='rob')
	async def rob(self, interaction:Interaction, *, member: nextcord.Member):
		await interaction.response.defer(with_message=True)
		deferMsg = await interaction.original_message()

		if not self.bot.get_cog("XP").IsHighEnoughLevel(interaction.user.id, 1):
			raise Exception("lowLevel 1")
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Rob")
		if interaction.user == member:
			embed.description = "Trying to rob yourself? That doesn't make sense. :joy:"
			await deferMsg.edit(embed=embed)
			return

		if not await self.bot.get_cog("Economy").accCheck(member):
			embed.description = f"{member} has not registed yet. Cannot rob them."
			await deferMsg.edit(embed=embed)

			cooldowns.reset_bucket(self.rob.callback, interaction)
			return

		bal1 = await self.bot.get_cog("Economy").getBalance(interaction.user)
		if bal1 < 2500:
			embed.description = f"{interaction.user}, you need at least 2500{emojis.coin} to rob."
			await deferMsg.edit(embed=embed)

			cooldowns.reset_bucket(self.rob.callback, interaction)
			return
		
		bal2 = await self.bot.get_cog("Economy").getBalance(member)
		if bal2 < 2500:
			embed.description = f"{member.mention} needs at least 2500{emojis.coin} to be robbed."
			await deferMsg.edit(embed=embed)

			cooldowns.reset_bucket(self.rob.callback, interaction)
			return

		choice = random.randrange(0, 10)
		# amnt = random.range(500, 5000)

		if choice > 7: # 20% chance
			embed.description = f"{member.mention} caught you red-handed! But they decided to forgive you... No money has been robbed!"
			await deferMsg.edit(embed=embed)
			return
	
		# amnt = -1

		if choice <= 4: # 0 - 4		(50%)
			robber = interaction.user
			robbee = member
			robbedBal = bal2
		else: # 5, 6, or 7			(30%)
			robber = member
			robbee = interaction.user
			robbedBal = bal1

		# bal is person getting robbed 
		if robbedBal <= 100000:
			thebal = int(robbedBal/4)
			if thebal <= 2500:
				thebal = 2501
			amnt = random.randrange(2500, thebal)
		else:
			amnt = random.randrange(2500, 25000)

		if choice <= 4: # 0 - 4		(50%)
			message = f"While {member.mention} was sleeping, you took {amnt:,}{emojis.coin} out of their pockets."
		else: # 5, 6, or 7			(30%)
			message = f"As you walk past {member.mention}, you try to pick pocket them, but they notice. They beat you up and steal {amnt:,}{emojis.coin} from you instead."


		await self.bot.get_cog("Economy").addWinnings(robber.id, amnt)
		await self.bot.get_cog("Economy").addWinnings(robbee.id, -amnt)

		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)

		embed.description = f"{message}\nYour new balance is {balance:,}{emojis.coin}"
		await deferMsg.edit(embed=embed)




def setup(bot):
	bot.add_cog(Util(bot))