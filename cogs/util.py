import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import cooldowns, asyncio, random

class Util(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.jobs = ["Administrative Assistant", "Executive Assistant", "Marketing Manager", "Customer Service Representative", "Nurse Practitioner", "Software Engineer", "Sales Manager", "Data Entry Clerk", "Office Assistant", "Accounting Specialist", "Payroll Specialist", "Dentist", "Registered Nurse", "Pharmacist", "Computer Systems Analyst", "Physician", "Database Administrator", "Software Developer", "Physical Therapist", "Web Developer", "Dental Hygienist", "Occupational Therapist", "Veterinarian", "Computer Programmer", "School Psychologist", "Physical Therapist Assistant", "Interpreter & Translator", "Mechanical Engineer", "Veterinary Technologist & Technician", "Epidemiologist", "IT Manager", "Market Research Analyst", "Diagnostic Medical Sonographer", "Computer Systems Administrator", "Respiratory Therapist", "Medical Secretary", "Civil Engineer", "Substance Abuse Counselor", "Speech-Language Pathologist", "Landscaper & Groundskeeper", "Radiologic Technologist", "Cost Estimator", "Financial Advisor", "Marriage & Family Therapist", "Medical Assistant", "Lawyer", "Accountant", "Compliance Officer", "High School Teacher", "Clinical Laboratory Technician", "Maintenance & Repair Worker", "Bookkeeping, Accounting, & Audit Clerk", "Financial Manager", "Recreation & Fitness Worker", "Insurance Agent", "Elementary School Teacher", "Dental Assistant", "Management Analyst", "Home Health Aide", "Pharmacy Technician", "Construction Manager", "Public Relations Specialist", "Middle School Teacher", "Massage Therapist", "Paramedic", "Preschool Teacher", "Hairdresser", "Marketing Manager", "Patrol Officer", "School Counselor", "Executive Assistant", "Financial Analyst", "Personal Care Aide", "Clinical Social Worker", "Business Operations Manager", "Loan Officer", "Meeting, Convention & Event Planner", "Mental Health Counselor", "Nursing Aide", "Sales Representative", "Architect", "Sales Manager", "HR Specialist", "Plumber", "Real Estate Agent", "Glazier", "Art Director", "Customer Service Representative", "Logistician", "Auto Mechanic", "Bus Driver", "Restaurant Cook", "Child & Family Social Worker", "Administrative Assistant", "Receptionist", "Paralegal", "Cement Mason & Concrete Finisher", "Painter", "Sports Coach", "Teacher Assistant", "Brickmason & Blockmason", "Cashier", "Janitor", "Electrician", "Delivery Truck Driver", "Maid & Housekeeper", "Carpenter", "Security Guard", "Construction Worker", "Fabricator", "Telemarketer"]


	async def getChoice(self, interaction:Interaction):
		await interaction.send("Type something...")
		def is_me(m):
			return m.author == interaction.user
		try:
			msg = await self.bot.wait_for('message', check=is_me, timeout=10)
		except asyncio.TimeoutError:
			raise Exception("timeoutError")
		return msg

	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5400, bucket=cooldowns.SlashBucket.author)
	async def work(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Work")

		job = random.choice(self.jobs)
		pay = random.randrange(6000, 20001)
		await self.bot.get_cog("Economy").addWinnings(interaction.user.id, pay)

		embed.description = f"You worked as a {job} and earned {pay:,}<:coins:585233801320333313>"
		await interaction.send(embed=embed)


	@nextcord.slash_command()
	@cooldowns.cooldown(1, 20, bucket=cooldowns.SlashBucket.author)
	async def rob(self, interaction:Interaction, *, member: nextcord.Member):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Rob")
		if interaction.user == member:
			embed.description = "Trying to rob yourself? That doesn't make sense. :joy:"
			await interaction.send(embed=embed)
			return
			
		if not await self.bot.get_cog("Economy").accCheck(member):
			await self.bot.get_cog("Economy").StartPlaying(interaction, member)

		bal1 = await self.bot.get_cog("Economy").getBalance(interaction.user)
		if bal1 < 500:
			embed.description = f"{interaction.user}, you need at least 500<:coins:585233801320333313> to rob."
			await interaction.send(embed=embed)
			return
		
		bal2 = await self.bot.get_cog("Economy").getBalance(member)
		if bal2 < 500:
			embed.description = f"{member.mention} needs at least 500<:coins:585233801320333313> to be robbed."
			await interaction.send(embed=embed)
			return

		choice = random.randrange(0, 10)
		# amnt = random.range(500, 5000)

		if choice > 7: # 30% chance
			embed.description = f"{member.mention} caught you red-handed! But they decided to forgive you... No money has been robbed!"
			await interaction.send(embed=embed)
			return

		coin = "<:coins:585233801320333313>"
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
			if thebal <= 500:
				thebal = 501
			amnt = random.randrange(500, thebal)
		else:
			amnt = random.randrange(500, 25001)

		if choice <= 4: # 0 - 4		(50%)
			message = f"While {member.mention} was sleeping, you took {amnt:,}{coin} out of their pockets."
		else: # 5, 6, or 7			(30%)
			message = f"As you walk past {member.mention}, you try to pick pocket them, but they notice. They beat you up and steal {amnt:,}{coin} from you instead."


		await self.bot.get_cog("Economy").addWinnings(robber.id, amnt)
		await self.bot.get_cog("Economy").addWinnings(robbee.id, -amnt)

		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)

		embed.description = f"{message}\nYour new balance is {balance:,}{coin}"
		await interaction.send(embed=embed)




def setup(bot):
	bot.add_cog(Util(bot))