# economy-related stuff like betting and gambling, etc.

import discord
from discord.ext import commands
import pymysql
import asyncio
import random
import time
import datetime
import config
from PIL import Image, ImageDraw, ImageFont, ImageColor
from math import floor

import json

actualGame = ["Slt", "BJ", "Crsh", "RLTTE", "CF", "RPS"]

def log(discordID, creditsSpent, creditsWon, gameNumber, bal): # Logs what credits have been spent where, by who, to who, why and the time which this has happened
	#localtime = time.asctime(time.localtime(time.time()))
	x = datetime.datetime.now()
						#  MON DAY HOUR:MIN:SEC
	localtime = x.strftime("%b %d %H:%M:%S")
	logs = open("logs.txt", "a")
	logs.write(f"{localtime} : {discordID} : {creditsSpent} : {creditsWon} : {bal} : {actualGame[gameNumber]}\n")
	logs.flush()
	logs.close()

class Totals(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		# self.bot.user.name = self.bot.user.name
		self.gameBadge = 250
		self.balBadge = 10000
		self.profitBadge = 1000
		self.lvlBadge = 5
		self.XPtoLevelUp = []
		for x in range(0,101):
			self.XPtoLevelUp.append(5000 + (x * 500)) 
		self.colors = {
			"white": 0xFFFFFF,
			"silver": 0xC0C0C0,
			"gray": 0x808080,
			"black": 0x000000,
			"red": 0xFF0000,
			"maroon": 0x800000,
			"yellow": 0xFFFF00,
			"blue": 0x0000FF,
			"navy": 0x000080,
			"fuchsia": 0xFF00FF,
			"pink": 0xFFC0CB,
			"purple": 0x800080,

			# green and shades
			"green": 0x008000,
			"aqua": 0x00FFFF,
			"aquamarine": 0x7FFFD4,
			"army": 0x454B1B,
			"blue": 0x088F8F,
			"bright": 0xAAFF00,
			"cadmium": 0x097969,
			"celadon": 0xAFE1AF,
			"chartreuse": 0xDFFF00,
			"citrine": 0xE4D00A,
			"cyan": 0x1AFBEF,
			"darkgreen": 0x023020,
			"emerald": 0x50C878,
			"eucalyptus": 0x5F8575,
			"fern": 0x4F7942,
			"forest": 0x228B22,
			"grass": 0x7CFC00,
			"hunter": 0x355E3B,
			"jade": 0x00A36C,
			"jungle": 0x2AAA8A,
			"kelly": 0x4CBB17,
			"lightgreen": 0x90EE90,
			"lime": 0x32CD32,
			"lincoln": 0x478778,
			"malachite": 0x0BDA51,
			"mint": 0x98FB98,
			"moss": 0x8A9A5B,
			"neon": 0x0FFF50,
			"nyanza": 0xECFFDC,
			"olive": 0x808000,
			"pastel": 0xC1E1C1,
			"pear": 0xC9CC3F,
			"peridot": 0xB4C424,
			"pistachio": 0x93C572,
			"sage": 0x8A9A5B,
			"sea": 0x2E8B57,
			"seafoam": 0x9FE2BF,
			"shamrock": 0x009E60,
			"spring": 0x00FF7F,
			"teal": 0x008080,
			"turquoise": 0x40E0D0,
			"verdigris": 0x40B5AD,
			"viridian": 0x40826D,

			# orange and shades
			"orange": 0xFFA500,
			"darkorange": 0xAA7E00,
			"amber": 0xFFBF00,
			"apricot": 0xFBCEB1,
			"bisque": 0xF2D2BD,
			"bronze": 0xCD7F32,
			"buff": 0xDAA06D,
			"cinnamon": 0xD27D2D,
			"copper": 0xB87333,
			"coral": 0xFF7F50,
			"desert": 0xFAD5A5,
			"gamboge": 0xE49B0F,
			"goldenrod": 0xDAA520,
			"mahogany": 0xC04000,
			"mango": 0xF4BB44,
			"ochre": 0xCC7722,
			"peach": 0xFFE5B4,
			"persimmon": 0xEC5800,
			"poppy": 0xE35335,
			"salmon": 0xFA8072,
			"seashell": 0xFFF5EE,
			"sienna": 0xA0522D,
			"tangerine": 0xF08000
		}

	@commands.group(invoke_without_command=True)
	async def profile(self, ctx):
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))
		if ctx.invoked_subcommand is not None:
			return

		conn = pymysql.connect(config.db)

		sql = f"""SELECT Profit, Games
				  FROM Totals
				  WHERE DiscordID = '{ctx.author.id}';"""
		cursor = conn.execute(sql)
		# conn.commit()
		getRow = cursor.fetchone()

		profit = getRow[0]
		games = getRow[1]

		# conn.close()

		# conn = pymysql.connect(config.db)
		# cursor = conn.cursor()

		sql = f"""SELECT Credits, Level, XP
				  FROM Economy
				  WHERE DiscordID = '{ctx.author.id}';"""
		cursor = conn.execute(sql)
		# conn.commit()
		getRow = cursor.fetchone()
		conn.close()
		balance = getRow[0]
		level = getRow[1]
		xp = getRow[2]
 
		requiredXP = self.XPtoLevelUp[level]

		crates, keys = await self.bot.get_cog("Economy").getInventory(ctx.author)


		with open(r"profiles.json", 'r') as f:
			profileFile = json.load(f)

		try:
			embedColor = profileFile[f"{ctx.author.id}"]["embedColor"]
			textColor = profileFile[f"{ctx.author.id}"]["textColor"]
			background = profileFile[f"{ctx.author.id}"]["background"]
		except:
			embedColor = 1768431
			textColor = (170,126,0)
			background = "scroll.png"

			profileFile[f"{ctx.author.id}"] = dict()
			profileFile[f"{ctx.author.id}"]["embedColor"] = embedColor
			profileFile[f"{ctx.author.id}"]["textColor"] = textColor
			profileFile[f"{ctx.author.id}"]["background"] = background
			with open(r"profiles.json", 'w') as f:
				json.dump(profileFile, f, indent=4)

		embed = discord.Embed(color=embedColor, title=f"{self.bot.user.name} | Profile")
		embed.set_thumbnail(url=ctx.author.avatar_url)
		# embed.add_field(name = "User", value = f"{ctx.author.name}", inline=True)
		# embed.add_field(name = "Level", value = f"{level}", inline=True)
		# embed.add_field(name = "Balance", value = f"{balance}", inline=True)
		embed.add_field(name = "XP / Next Level", value = f"{xp} / {requiredXP}", inline=True)
		embed.add_field(name = "Profit", value = f"{profit}", inline=True)
		embed.add_field(name = "Games Played", value = f"{games}", inline=True)
		embed.add_field(name = "Crates", value = f"{crates}", inline=True)
		embed.add_field(name = "Keys", value = f"{keys}", inline=True)

		img = Image.open(f"./images/writingbackgrounds/{background}")

		if games >= self.gameBadge:
			img250 = Image.open("./images/badges/250.png")
			newSize = (60, 48)
			img250 = img250.resize(newSize)
			img.paste(img250, (100, 270), img250)

		if balance >= self.balBadge:
			img10k = Image.open("./images/badges/10k.png")
			newSize = (75, 55)
			img10k = img10k.resize(newSize)
			img.paste(img10k, (200, 267), img10k)

		if profit >= self.profitBadge:
			img1k = Image.open("./images/badges/1k.png")
			newSize = (75, 75)
			img1k = img1k.resize(newSize)
			img.paste(img1k, (320, 256), img1k)

		if level >= self.lvlBadge:
			img1k = Image.open("./images/badges/level5.png")
			newSize = (75, 75)
			img1k = img1k.resize(newSize)
			img.paste(img1k, (430, 256), img1k)

		font_type = ImageFont.truetype('arial.ttf',25)
		draw = ImageDraw.Draw(img)
		draw.text(xy=(100,100), text=f"{ctx.author.name}", fill=tuple(textColor), font=ImageFont.truetype('HappyMonksMedievalLookingScript',55))
		draw.text(xy=(420,160), text=f"Level {level}", fill=tuple(textColor), font=font_type)
		draw.text(xy=(100,160), text=f"Balance: {balance}", fill=tuple(textColor), font=font_type)
		draw.text(xy=(100,230), text=f"Badges", fill=tuple(textColor), font=font_type)
		img.save("images/profile.png")
		file = discord.File("images/profile.png", filename="image.png")
		embed.set_image(url="attachment://image.png")

		embed.set_footer(text=f"Customize your profile with {ctx.prefix}profile edit")

		await ctx.send(file=file, embed=embed)


	@commands.command()
	async def colors(self, ctx):
		embed = discord.Embed(color=1768431, title=f"{self.bot.user.name} | Colors")
		embed1 = discord.Embed(color=self.colors["green"], title=f"Shades of Green")
		embed2 = discord.Embed(color=self.colors["darkorange"], title=f"Shades of Orange")
		count = 0
		msg = ""
		msg1 = ""
		msg2 = ""
		for color in self.colors.keys():
			if color == "green" or color == "orange":
				count += 1

			if count == 0: msg += f"{color}\n"
			if count == 1: msg1 += f"{color}\n"
			if count == 2: msg2 += f"{color}\n"

		embed.add_field(name="Regular colors", value=f"{msg}")
		embed1.add_field(name="_ _", value=f"{msg1}")
		embed2.add_field(name="_ _", value=f"{msg2}")
		await ctx.send(embed=embed)
		await ctx.send(embed=embed1)
		await ctx.send(embed=embed2)

	@commands.command(aliases=['bg'])
	async def background(self, ctx, choice:str=None):
		await ctx.invoke(self.bot.get_command(f'profile edit'), "3", choice)

	@commands.command()
	async def edit(self, ctx, field=None, choice=None):
		await ctx.invoke(self.bot.get_command('profile edit'), field, choice)

	@profile.command(name='edit', aliases=['help'])
	async def _edit(self, ctx, field=None, choice=None):
		# if ctx.author.id != 547475078082985990:
		# 	if ctx.guild.id != 585226670361804827:
		# 		await ctx.send("This is currently being worked on... Feel free to join the support server for updates.")
		# 		return
		# 	await ctx.send("This is currently being worked on...")
		# 	return

		embed = discord.Embed(color=1768431, title=f"{self.bot.user.name} | Edit Profile")
		embed.set_thumbnail(url=ctx.author.avatar_url)

		if (not field or not choice) and field != "3":
			embed.add_field(name = "_ _\nAvailable profile features you can edit:", value = f"1. Color of embed (DEFAULT: cyan)\n" +
				"2. Color of text in the scroll (DEFAULT: darkorange)\n" +
				"3. Image background (DEFAULT: scroll) (type: .background or .bg)", inline=True)
			embed.set_footer(text="Edit a property with: .edit <property> <value> such as .edit 1 green\nType .colors to see a list of all available colors")

			await ctx.send(embed=embed)
			
			return

		if choice: choice = choice.lower()

		with open(r"profiles.json", 'r') as f:
			profileFile = json.load(f)


		if field == "1":
			try:
				newColor = self.colors[choice]
			except:
				embed.add_field(name="Error", value="Color not found.")
				await ctx.send(embed=embed)
				return

			with open(r"profiles.json", 'r') as f:
				profileFile = json.load(f)

			profileFile[f"{ctx.author.id}"]["embedColor"] = newColor
			with open(r"profiles.json", 'w') as f:
				json.dump(profileFile, f, indent=4)

		elif field == "2":
			try:
				newColor = str(hex(self.colors[choice])) # convert to the literal hexadecimal string
			except:
				embed.add_field(name="Error", value="Color not found.")
				await ctx.send(embed=embed)
				return
			newColor = "#" + "0"*(8-len(newColor))+ newColor[2:] # append trailing 0's and switch out 0x for #

			newColor = ImageColor.getcolor(newColor, "RGB") # get RGB version of color 
			
			with open(r"profiles.json", 'r') as f:
				profileFile = json.load(f)

			profileFile[f"{ctx.author.id}"]["textColor"] = newColor
			with open(r"profiles.json", 'w') as f:
				json.dump(profileFile, f, indent=4)

		elif field == "3" and not choice:
			embed.add_field(name="Pick an option:", value=f"1. Scroll\n2. Ink Paper\n3. Spiral Notebook")
			embed.set_footer(text=".background 3")

			await ctx.send(embed=embed)
			return

		elif field == "3":
			with open(r"profiles.json", 'r') as f:
				profileFile = json.load(f)

			if choice == "1" or "scroll" in choice.lower():
				background = "scroll.png"
			elif choice == "2" or "ink" in choice.lower():
				background = "inkpaper.png"
			elif choice == "3" or "spiral" in choice.lower():
				background = "spiralnotebook.png"
			else:
				await ctx.send("Invalid choice for background.")
				return

			profileFile[f"{ctx.author.id}"]["background"] = background
			with open(r"profiles.json", 'w') as f:
				json.dump(profileFile, f, indent=4)

			background = profileFile[f"{ctx.author.id}"]["background"]
			file = discord.File(f"./images/writingbackgrounds/{background}", filename="image.png")
			embed.set_image(url="attachment://image.png")
			embed.add_field(name="Edited!", value=f"Successfully changed to {choice}.")
			await ctx.send(file=file, embed=embed)
			return

		embedColor = profileFile[f"{ctx.author.id}"]["embedColor"]
		embed = discord.Embed(color=embedColor, title=f"{self.bot.user.name} | Edit Profile")
		embed.set_thumbnail(url=ctx.author.avatar_url)

		embed.add_field(name="Edited!", value=f"Successfully changed to {choice}.")

		await ctx.send(embed=embed)


	@commands.command()
	async def badges(self, ctx):
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))
			
		conn = pymysql.connect(config.db)

		sql = f"""SELECT E.Credits, E.Level, T.Profit, T.Games
				  FROM Economy E
				  INNER JOIN Totals T
				  ON E.DiscordID = T.DiscordID
				  WHERE E.DiscordID = '{ctx.author.id}';"""

		cursor = conn.execute(sql)
		getRow = cursor.fetchone()
		conn.close()
		games = getRow[3]
		balance = getRow[0]
		profit = getRow[2]
		level = getRow[1]

		if games >= self.gameBadge:
			gameMsg = ":white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark:" 
		else:
			gameMsg = ":red_square::red_square::red_square::red_square::red_square::red_square::red_square::red_square::red_square::red_square:"
			for _ in range(0, floor(games/25)):
				gameMsg = gameMsg.replace(":red_square:",":white_check_mark:",1)
		
		if balance >= self.balBadge:
			balMsg = ":white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark:"
		else:	
			balMsg = ":red_square::red_square::red_square::red_square::red_square::red_square::red_square::red_square::red_square::red_square:"
			for _ in range(0, floor(balance/1000)):
				balMsg = balMsg.replace(":red_square:",":white_check_mark:",1)

		if profit >= self.profitBadge:
			profitMsg = ":white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark:" 
		else:
			profitMsg = ":red_square::red_square::red_square::red_square::red_square::red_square::red_square::red_square::red_square::red_square:"
			for _ in range(0, floor(profit/100)):
				profitMsg = profitMsg.replace(":red_square:",":white_check_mark:" ,1)

		if level >= self.lvlBadge:
			lvlMsg = ":white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark::white_check_mark:"
		else:
			lvlMsg = ":red_square::red_square::red_square::red_square::red_square::red_square::red_square::red_square::red_square::red_square:`"	
			for _ in range(0, level*2):
				lvlMsg = lvlMsg.replace(":red_square:",":white_check_mark:",1)

		embed = discord.Embed(color=1768431, title=f"{self.bot.user.name} | Badges")
		embed.add_field(name="Games Badge", value=f"{gameMsg} {self.gameBadge}", inline=False)
		embed.add_field(name="Balance Badge", value=f"{balMsg} {self.balBadge}", inline=False)
		embed.add_field(name="Profit Badge", value=f"{profitMsg} {self.profitBadge}", inline=False)
		embed.add_field(name="Level Badge", value=f"{lvlMsg} {self.lvlBadge}", inline=False)

		embed.set_footer(text="Badges can be viewed in your .profile")
		
		await ctx.send(embed=embed)


	@commands.command(pass_context=True, aliases=['totals', 'me'])
	async def stats(self, ctx):
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))
			
		conn = pymysql.connect(config.db)

		sql = f"""SELECT Paid, Won, Profit, Games, Slots, Blackjack, Crash, Roulette, Coinflip, RPS
				  FROM Totals
				  WHERE DiscordID = '{ctx.author.id}';"""
		cursor = conn.execute(sql)
		conn.commit()
		getRow = cursor.fetchone()

		creditsSpent = getRow[0]
		creditsWon = getRow[1]
		profit = getRow[2]
		games = getRow[3]
		slots = getRow[4]
		blackjack = getRow[5]
		crash = getRow[6]
		roulette = getRow[7]
		coinflip = getRow[8]
		rps = getRow[9]

		conn.close()

		embed = discord.Embed(color=1768431, title=f"{self.bot.user.name} | Stats")
		embed.add_field(name = "Total Spent", value = f"{creditsSpent}", inline=True)
		embed.add_field(name = "Total Won", value = f"{creditsWon}", inline=True)
		embed.add_field(name = "Profit", value = f"{profit}", inline=True)
		embed.add_field(name = "Games Played", value = f"{games}", inline=True)
		embed.add_field(name = "Slots", value = f"{slots}", inline=True)
		embed.add_field(name = "Blackjack", value = f"{blackjack}", inline=True)
		embed.add_field(name = "Crash", value = f"{crash}", inline=True)
		embed.add_field(name = "Roulette", value = f"{roulette}", inline=True)
		embed.add_field(name = "Coinflip", value = f"{coinflip}", inline=True)
		embed.add_field(name = "Rock-Paper-Scissors", value = f"{rps}", inline=True)

		await ctx.send(embed=embed)



	async def addTotals(self, ctx, spent, won, game):
		discordID = ctx.author.id
		profit = won - spent
		conn = pymysql.connect(config.db)

		if game == 0: gameName = "Slots"		  
		elif game == 1: gameName = "Blackjack"
		elif game == 2: gameName = "Crash"
		elif game == 3: gameName = "Roulette"
		elif game == 4: gameName = "Coinflip"
		elif game == 5: gameName = "RPS"

		sql = f"""UPDATE Totals
				  SET Paid = Paid + {spent}, Won = Won + {won}, Profit = Profit + {profit}, Games = Games + 1, {gameName} = {gameName} + {profit}
				  WHERE DiscordID = '{ctx.author.id}';"""

		cursor = conn.execute(sql)
		conn.commit()

		bal = await self.bot.get_cog("Economy").getBalance(ctx.author)
		log(discordID, spent, won, game, bal)

		conn.close()

def setup(bot):
	bot.add_cog(Totals(bot))