import discord
from discord.ext import commands#, tasks
import asyncio

import random


class Util(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.jobs = ["Administrative Assistant", "Executive Assistant", "Marketing Manager", "Customer Service Representative", "Nurse Practitioner", "Software Engineer", "Sales Manager", "Data Entry Clerk", "Office Assistant", "Accounting Specialist", "Payroll Specialist", "Dentist", "Registered Nurse", "Pharmacist", "Computer Systems Analyst", "Physician", "Database Administrator", "Software Developer", "Physical Therapist", "Web Developer", "Dental Hygienist", "Occupational Therapist", "Veterinarian", "Computer Programmer", "School Psychologist", "Physical Therapist Assistant", "Interpreter & Translator", "Mechanical Engineer", "Veterinary Technologist & Technician", "Epidemiologist", "IT Manager", "Market Research Analyst", "Diagnostic Medical Sonographer", "Computer Systems Administrator", "Respiratory Therapist", "Medical Secretary", "Civil Engineer", "Substance Abuse Counselor", "Speech-Language Pathologist", "Landscaper & Groundskeeper", "Radiologic Technologist", "Cost Estimator", "Financial Advisor", "Marriage & Family Therapist", "Medical Assistant", "Lawyer", "Accountant", "Compliance Officer", "High School Teacher", "Clinical Laboratory Technician", "Maintenance & Repair Worker", "Bookkeeping, Accounting, & Audit Clerk", "Financial Manager", "Recreation & Fitness Worker", "Insurance Agent", "Elementary School Teacher", "Dental Assistant", "Management Analyst", "Home Health Aide", "Pharmacy Technician", "Construction Manager", "Public Relations Specialist", "Middle School Teacher", "Massage Therapist", "Paramedic", "Preschool Teacher", "Hairdresser", "Marketing Manager", "Patrol Officer", "School Counselor", "Executive Assistant", "Financial Analyst", "Personal Care Aide", "Clinical Social Worker", "Business Operations Manager", "Loan Officer", "Meeting, Convention & Event Planner", "Mental Health Counselor", "Nursing Aide", "Sales Representative", "Architect", "Sales Manager", "HR Specialist", "Plumber", "Real Estate Agent", "Glazier", "Art Director", "Customer Service Representative", "Logistician", "Auto Mechanic", "Bus Driver", "Restaurant Cook", "Child & Family Social Worker", "Administrative Assistant", "Receptionist", "Paralegal", "Cement Mason & Concrete Finisher", "Painter", "Sports Coach", "Teacher Assistant", "Brickmason & Blockmason", "Cashier", "Janitor", "Electrician", "Delivery Truck Driver", "Maid & Housekeeper", "Carpenter", "Security Guard", "Construction Worker", "Fabricator", "Telemarketer"]


	async def getChoice(self, ctx):
		await ctx.send("Type something...")
		def is_me(m):
			return m.author == ctx.author
		try:
			msg = await self.bot.wait_for('message', check=is_me, timeout=10)
		except asyncio.TimeoutError:
			raise Exception("timeoutError")
		return msg
	
	@commands.command()
	async def test(self, ctx):
		getInput = await self.getChoice(ctx)
		await ctx.send(f"User chose {getInput.content}")

	@commands.command()
	@commands.cooldown(1, 5400, commands.BucketType.user)
	async def work(self, ctx):
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))

		job = random.choice(self.jobs)
		pay = random.randrange(6000, 20001)

		await ctx.send(f"You worked as a {job} and earned {pay}<:coins:585233801320333313>")

		await self.bot.get_cog("Economy").addWinnings(ctx.author.id, pay)


	@commands.command()
	@commands.cooldown(1, 20, commands.BucketType.user)
	async def rob(self, ctx, *, member: discord.Member):
		if ctx.author == member:
			await ctx.send("Trying to rob yourself? That doesn't make sense. :joy:")
			return
			
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))
		if not await self.bot.get_cog("Economy").accCheck(member):
			await ctx.invoke(self.bot.get_command('start'), member)

		bal1 = await self.bot.get_cog("Economy").getBalance(ctx.author)
		if bal1 < 500:
			await ctx.send(f"{ctx.author}, you need at least 500<:coins:585233801320333313> to rob.")
			return
		
		bal2 = await self.bot.get_cog("Economy").getBalance(member)
		if bal2 < 500:
			await ctx.send(f"{member.mention} needs at least 500<:coins:585233801320333313> to be robbed.")
			return

		choice = random.randrange(0, 10)
		# amnt = random.range(500, 5000)

		if choice > 7: # 30% chance
			await ctx.send(f"{member.mention} caught you red-handed! But they decided to forgive you... No money has been robbed!")
			return

		coin = "<:coins:585233801320333313>"
		# amnt = -1

		if choice <= 4: # 0 - 4		(50%)
			robber = ctx.author
			robbee = member
			robbedBal = bal2
		else: # 5, 6, or 7			(30%)
			robber = member
			robbee = ctx.author
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
			message = f"While {member.mention} was sleeping, you took {amnt}{coin} out of their pockets."
		else: # 5, 6, or 7			(30%)
			message = f"As you walk past {member.mention}, you try to pick pocket them, but they notice. They beat you up and steal {amnt}{coin} from you instead."


		await self.bot.get_cog("Economy").addWinnings(robber.id, amnt)
		await self.bot.get_cog("Economy").addWinnings(robbee.id, -amnt)

		balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
		await ctx.reply(message + f"\nYour new balance is {balance}{coin}")




def setup(bot):
	bot.add_cog(Util(bot))