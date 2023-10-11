# economy-related stuff like betting and gambling, etc.
import nextcord
from nextcord.ext import commands, application_checks 
from nextcord import Interaction

import sqlite3, datetime, json, cooldowns, uuid
from PIL import Image, ImageDraw, ImageFont, ImageColor
from math import floor

import config, io
from db import DB

actualGame = ["Slt", "BJ", "Crsh", "RLTTE", "CF", "RPS"]

def log(discordID, creditsSpent, creditsWon, activity, bal): # Logs what credits have been spent where, by who, to who, why and the time which this has happened
	# #localtime = time.asctime(time.localtime(time.time()))
	x = datetime.datetime.now()
						#  MON DAY YY HOUR:MIN:SEC
	localtime = x.strftime("%b/%d/%y %H:%M:%S")
	gameID = (str(uuid.uuid4())[:8]).upper()

	if creditsSpent < 0:
		creditsSpent *= -1

	if type(activity) == int:
		activity = actualGame[activity]
	while True:
		try:
			DB.insert("INSERT INTO Logs VALUES(?, ?, ?, ?, ?, ?, ?)", [gameID, localtime, discordID, creditsSpent, creditsWon, bal, activity])
			break
		except sqlite3.IntegrityError:
			gameID = str(uuid.uuid4())[:8]
	return gameID


class Totals(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
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

	@nextcord.slash_command()
	@cooldowns.cooldown(1, 3, bucket=cooldowns.SlashBucket.author, cooldown_id='rob')
	async def log(self, interaction:Interaction, gameid):
		await interaction.response.defer(with_message=True, ephemeral=True)
		deferMsg = await interaction.original_message()
		game = DB.fetchOne("SELECT * FROM Logs WHERE ID = ? LIMIT 1;", [gameid])

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Logs")

		if not game:
			embed.description =f"No log found for ID \n{gameid}"
			await deferMsg.edit(embed=embed)
			return

		if str(interaction.user.id) != game[2]:
			embed.description = "This is not your log to view!"
			await deferMsg.edit(embed=embed)
			return

		embed.add_field(name="Activity", value=game[6], inline=False)
		embed.add_field(name="Credits Spent", value=f"{game[3]:,}")
		embed.add_field(name="Credits Gained", value=f"{game[4]:,}")
		embed.add_field(name="New Balance", value=f"{game[5]:,}", inline=False)

		embed.set_footer(text=f"ID: {game[0]}\nDate: {game[1]}")

		await deferMsg.edit(embed=embed)


	def GetProfile(self, profileFile, userId, embedColor=None, textColor=None, background=None):
		if f"{userId}" not in profileFile:
			profileFile[f"{userId}"] = dict()
			profileFile[f"{userId}"]["embedColor"] = 1768431
			profileFile[f"{userId}"]["textColor"] = (170,126,0)
			profileFile[f"{userId}"]["background"] = "scroll.png"

			with open(r"profiles.json", 'w') as f:
				json.dump(profileFile, f, indent=4)
		
		if embedColor or textColor or background:
			if embedColor:
				profileFile[f"{userId}"]["embedColor"] = embedColor
			if textColor:
				profileFile[f"{userId}"]["textColor"] = textColor
			if background:
				profileFile[f"{userId}"]["background"] = background
			
			with open(r"profiles.json", 'w') as f:
				json.dump(profileFile, f, indent=4)
		
		return profileFile

	@nextcord.slash_command()
	async def profile(self, interaction:Interaction):
		pass
	
	@profile.subcommand()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='view')
	async def view(self, interaction:Interaction):
		await interaction.response.defer(with_message=True)
		deferMsg = await interaction.original_message()

		totals = DB.fetchOne("SELECT Profit, Games FROM Totals WHERE DiscordID = ?;", [interaction.user.id])
		profit = totals[0]
		games = totals[1]

		eco = DB.fetchOne("SELECT Credits, Level, XP FROM Economy WHERE DiscordID = ?;", [interaction.user.id])
		balance = eco[0]
		level = eco[1]
		xp = eco[2]
 
		requiredXP = self.XPtoLevelUp[level]

		crates, keys = self.bot.get_cog("Inventory").getInventory(interaction.user)


		with open(r"profiles.json", 'r') as f:
			profileFile = json.load(f)

		profileFile = self.GetProfile(profileFile, interaction.user.id)
		profile = profileFile[f"{interaction.user.id}"]

		embedColor = profile["embedColor"]
		textColor = profile["textColor"]
		background = profile["background"]

		embed = nextcord.Embed(color=embedColor, title=f"{self.bot.user.name} | Profile")
		embed.set_thumbnail(url=interaction.user.avatar)
		# embed.add_field(name = "User", value = f"{interaction.user.name}", inline=True)
		# embed.add_field(name = "Level", value = f"{level}", inline=True)
		# embed.add_field(name = "Balance", value = f"{balance}", inline=True)
		embed.add_field(name = "XP / Next Level", value = f"{xp:,} / {requiredXP:,}", inline=True)
		embed.add_field(name = "Profit", value = f"{profit:,}", inline=True)
		embed.add_field(name = "Games Played", value = f"{games:,}", inline=True)
		embed.add_field(name = "Crates", value = f"{crates:,}", inline=True)
		embed.add_field(name = "Keys", value = f"{keys:,}", inline=True)

		img = Image.open(f"./images/writingbackgrounds/{background}")

		badgeList = list()
		if games >= self.gameBadge:
			img250 = Image.open("./images/badges/250.png")
			newSize = (50, 50)
			img250 = img250.resize(newSize)
			badgeList.append(img250)

		if balance >= self.balBadge:
			img10k = Image.open("./images/badges/10k.png")
			newSize = (50, 50)
			img10k = img10k.resize(newSize)
			badgeList.append(img10k)

		if profit >= self.profitBadge:
			img1k = Image.open("./images/badges/1k.png")
			newSize = (50, 50)
			img1k = img1k.resize(newSize)
			badgeList.append(img1k)

		if level >= self.lvlBadge:
			level5 = Image.open("./images/badges/level5.png")
			newSize = (50, 50)
			level5 = level5.resize(newSize)
			badgeList.append(level5)

		yPos = 215
		xPos = 100
		for x in range(len(badgeList)):
			if x != 0 and x % 7 == 0:
				yPos += 50
				xPos -= 420
			img.paste(badgeList[x-1], (xPos+(x*60), yPos), badgeList[x-1])

		font_type = ImageFont.truetype('arial.ttf',25)
		draw = ImageDraw.Draw(img)
		draw.text(xy=(100,70), text=f"{interaction.user.name}", fill=tuple(textColor), font=ImageFont.truetype('fonts/HappyMonksMedievalLookingScript.ttf',55))
		draw.text(xy=(420,130), text=f"Level {level:,}", fill=tuple(textColor), font=font_type)
		draw.text(xy=(100,130), text=f"Balance: {balance:,}", fill=tuple(textColor), font=font_type)
		draw.text(xy=(100,180), text=f"Badges", fill=tuple(textColor), font=font_type)

		embed.set_footer(text=f"Customize your profile with /profile edit")

		with io.BytesIO() as image_binary:
			img.save(image_binary, 'PNG')
			image_binary.seek(0)
			# await self.msg.edit(embed=self.embed, file=nextcord.File(fp=image_binary, filename='image.png'))
			file = nextcord.File(image_binary, filename="image.png")
			embed.set_image(url="attachment://image.png")
			await deferMsg.edit(embed=embed, file=file)
	
	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def profileeverything(self, interaction:Interaction):
		if interaction.user.id != config.botOwnerDiscordID:
			await interaction.send("No.")
			return

		eco = DB.fetchOne("SELECT Credits, Level, XP FROM Economy WHERE DiscordID = ?;", [interaction.user.id])
		balance = eco[0]
		level = eco[1]


		with open(r"profiles.json", 'r') as f:
			profileFile = json.load(f)

		profileFile = self.GetProfile(profileFile, interaction.user.id)
		profile = profileFile[f"{interaction.user.id}"]

		embedColor = profile["embedColor"]
		textColor = profile["textColor"]

		embed = nextcord.Embed(color=embedColor, title=f"{self.bot.user.name} | Profile")
		# for x in range(3):
		# if x == 0:
		img = Image.open(f"./images/writingbackgrounds/inkpaper.png")
		# elif x == 1:
		# 	img = Image.open(f"./images/writingbackgrounds/scroll.png")
		# elif x == 2:
		# 	img = Image.open(f"./images/writingbackgrounds/spiralnotebook.png")

		badgeList = list()
		# if games >= self.gameBadge:
		img250 = Image.open("./images/badges/250.png")
		img250 = img250.resize((50, 45))
		badgeList.append(img250)

		# if balance >= self.balBadge:
		img10k = Image.open("./images/badges/10k.png")
		img10k = img10k.resize((50, 50))
		badgeList.append(img10k)

		# if profit >= self.profitBadge:
		img1k = Image.open("./images/badges/1k.png")
		img1k = img1k.resize((50, 50))
		badgeList.append(img1k)

		# if level >= self.lvlBadge:
		level5 = Image.open("./images/badges/level5.png")
		level5 = level5.resize((50, 50))
		badgeList.append(level5)

		#if has aceofspades
		aceOfSpades = Image.open("./images/emojis/AceofSpades.png")
		aceOfSpades = aceOfSpades.resize((40, 50))
		badgeList.append(aceOfSpades)

		#if has threeofakind
		threeOfAKind = Image.open("./images/emojis/3ofakind.png")
		threeOfAKind = threeOfAKind.resize((50, 50))
		badgeList.append(threeOfAKind)

		#if has straight
		straight = Image.open("./images/emojis/straight.png")
		straight = straight.resize((50, 50))
		badgeList.append(straight)

		#if has fourofakind
		fourOfAKind = Image.open("./images/emojis/4ofakind.png")
		fourOfAKind = fourOfAKind.resize((50, 50))
		badgeList.append(fourOfAKind)

		yPos = 215
		xPos = 100
		for x in range(len(badgeList)):
			if x != 0 and x % 7 == 0:
				yPos += 55
				xPos -= 420
			try:
				img.paste(badgeList[x-1], (xPos+(x*60), yPos), badgeList[x-1])
			except Exception as e:
				print(e)

		font_type = ImageFont.truetype('arial.ttf',25)
		draw = ImageDraw.Draw(img)
		draw.text(xy=(100,70), text=f"{interaction.user.name}", fill=tuple(textColor), font=ImageFont.truetype('fonts/HappyMonksMedievalLookingScript.ttf',55))
		draw.text(xy=(420,130), text=f"Level {level:,}", fill=tuple(textColor), font=font_type)
		draw.text(xy=(100,130), text=f"Balance: {balance:,}", fill=tuple(textColor), font=font_type)
		draw.text(xy=(100,180), text=f"Badges", fill=tuple(textColor), font=font_type)
		# img.save("images/profile.png")
		# file = nextcord.File("images/profile.png", filename="image.png")
		# embed.set_image(url="attachment://image.png")

		with io.BytesIO() as image_binary:
			img.save(image_binary, 'PNG')
			image_binary.seek(0)
			# await self.msg.edit(embed=self.embed, file=nextcord.File(fp=image_binary, filename='image.png'))
			file = nextcord.File(image_binary, filename="image.png")
			embed.set_image(url="attachment://image.png")
			await interaction.send(embed=embed, file=file)


	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='colors')
	async def colors(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Colors")
		embed1 = nextcord.Embed(color=self.colors["green"], title=f"Shades of Green")
		embed2 = nextcord.Embed(color=self.colors["darkorange"], title=f"Shades of Orange")
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
		await interaction.send(embed=embed, ephemeral=True)
		await interaction.send(embed=embed1, ephemeral=True)
		await interaction.send(embed=embed2, ephemeral=True)


	@profile.subcommand()
	async def edit(self, interaction:Interaction):
		pass

	@edit.subcommand(description="Get color list from /colors")
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='embedcolor')
	async def embedcolor(self, interaction:Interaction, choice):
		await interaction.response.defer(with_message=True)
		deferMsg = await interaction.original_message()

		if not self.bot.get_cog("XP").IsHighEnoughLevel(interaction.user.id, 1):
			raise Exception("lowLevel 1")

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Edit Profile")
		embed.set_thumbnail(url=interaction.user.avatar)

		try:
			newColor = self.colors[choice]
		except:
			embed.add_field(name="Error", value="Color not found. Type /colors to see all available colors")
			await deferMsg.edit(embed=embed)
			return

		with open(r"profiles.json", 'r') as f:
			profileFile = json.load(f)
		
		profileFile = self.GetProfile(profileFile, interaction.user.id, embedColor=newColor)

		embed.add_field(name="Success!", value=f"Your profile's embed color has been changed to {choice}")
		embed.color = newColor
		await deferMsg.edit(embed=embed)

	@edit.subcommand(description="Get color list from /colors")
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='textcolor')
	async def textcolor(self, interaction:Interaction, choice):
		await interaction.response.defer()
		deferMsg = await interaction.original_message()
		
		if not self.bot.get_cog("XP").IsHighEnoughLevel(interaction.user.id, 2):
			raise Exception("lowLevel 2")
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Edit Profile")
		embed.set_thumbnail(url=interaction.user.avatar)
		try:
			newColor = str(hex(self.colors[choice])) # convert to the literal hexadecimal string
		except:
			embed.add_field(name="Error", value="Color not found. Type /colors to see all available colors")
			await deferMsg.edit(embed=embed)
			return
		newColor = "#" + "0"*(8-len(newColor))+ newColor[2:] # append trailing 0's and switch out 0x for #

		newColor = ImageColor.getcolor(newColor, "RGB") # get RGB version of color 

		with open(r"profiles.json", 'r') as f:
			profileFile = json.load(f)

		profileFile = self.GetProfile(profileFile, interaction.user.id, textColor=newColor)
		with open(r"profiles.json", 'w') as f:
			json.dump(profileFile, f, indent=4)

		embed.add_field(name="Success!", value=f"Your profile's text color has been changed to {choice}")
		embed.color = self.colors[choice]
		await deferMsg.edit(embed=embed)

	@edit.subcommand()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='backgroundimage')
	async def backgroundimage(self, interaction:Interaction, choice = nextcord.SlashOption(
																required=True,
																name="bgimg", 
																choices=("scroll", "inkpaper", "spiralnotebook"))):
		await interaction.response.defer(with_message=True)
		deferMsg = await interaction.original_message()

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Edit Profile")
		embed.set_thumbnail(url=interaction.user.avatar)
		with open(r"profiles.json", 'r') as f:
			profileFile = json.load(f)

		if choice == "scroll":
			background = "scroll.png"
		elif choice == "inkpaper":
			background = "inkpaper.png"
		else:
			background = "spiralnotebook.png"

		profileFile = self.GetProfile(profileFile, interaction.user.id, background=background)

		file = nextcord.File(f"./images/writingbackgrounds/{background}", filename="image.png")
		embed.set_image(url="attachment://image.png")
		embed.add_field(name="Edited!", value=f"Successfully changed to {choice}.")
		await deferMsg.edit(file=file, embed=embed)


	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='badges')
	async def badges(self, interaction:Interaction):
		await interaction.response.defer(with_message=True)
		deferMsg = await interaction.original_message()

		getRow = DB.fetchOne("SELECT E.Credits, E.Level, T.Profit, T.Games FROM Economy E INNER JOIN Totals T ON E.DiscordID = T.DiscordID WHERE E.DiscordID = ?;", [interaction.user.id])
		
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
			lvlMsg = ":red_square::red_square::red_square::red_square::red_square::red_square::red_square::red_square::red_square::red_square:"	
			for _ in range(0, level*2):
				lvlMsg = lvlMsg.replace(":red_square:",":white_check_mark:",1)

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Badges")
		embed.add_field(name="Games Badge", value=f"{gameMsg} {self.gameBadge}", inline=False)
		embed.add_field(name="Balance Badge", value=f"{balMsg} {self.balBadge}", inline=False)
		embed.add_field(name="Profit Badge", value=f"{profitMsg} {self.profitBadge}", inline=False)
		embed.add_field(name="Level Badge", value=f"{lvlMsg} {self.lvlBadge}", inline=False)

		embed.set_footer(text="Badges can be viewed in your `/profile view`")
		
		await deferMsg.edit(embed=embed)


	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='stats')
	async def stats(self, interaction:Interaction):	
		await interaction.response.defer(with_message=True)
		deferMsg = await interaction.original_message()
	
		getRow = DB.fetchOne("SELECT Paid, Won, Profit, Games, Slots, Blackjack, Crash, Roulette, Coinflip, RPS, Mines, HighLow, Horse, DOND, Scratch FROM Totals WHERE DiscordID = ?;", [interaction.user.id])

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
		mines = getRow[10]
		highLow = getRow[11]
		horse = getRow[12]
		dond = getRow[13]
		scratch = getRow[14]

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Stats")
		embed.add_field(name = "Total Spent", value = f"{creditsSpent:,}", inline=True)
		embed.add_field(name = "Total Won", value = f"{creditsWon:,}", inline=True)
		embed.add_field(name = "Profit", value = f"{profit:,}", inline=True)
		embed.add_field(name = "Games Played", value = f"{games:,}", inline=True)
		embed.add_field(name = "Slots", value = f"{slots:,}", inline=True)
		embed.add_field(name = "Blackjack", value = f"{blackjack:,}", inline=True)
		embed.add_field(name = "Crash", value = f"{crash:,}", inline=True)
		embed.add_field(name = "Roulette", value = f"{roulette:,}", inline=True)
		embed.add_field(name = "Coinflip", value = f"{coinflip:,}", inline=True)
		embed.add_field(name = "Rock-Paper-Scissors", value = f"{rps:,}", inline=True)
		embed.add_field(name = "Mines", value = f"{mines:,}", inline=True)
		embed.add_field(name = "HighLow", value = f"{highLow:,}", inline=True)
		embed.add_field(name = "Horse", value = f"{horse:,}", inline=True)
		embed.add_field(name = "DOND", value = f"{dond:,}", inline=True)
		embed.add_field(name = "Scratch", value = f"{scratch:,}", inline=True)

		await deferMsg.edit(embed=embed)



	def addTotals(self, interaction:Interaction, spent, won, game=None):
		if won < 0:
			won = 0
		if spent < 0:
			spent = 0
		profit = won - spent

		# DB.update("""UPDATE Totals
		# 		  SET Paid = Paid + ?, Won = Won + ?, Profit = Profit + ?, Games = Games + 1, ? = ? + ?
		# 		  WHERE DiscordID = ?;""", [spent, won, profit, gameName, gameName, profit, interaction.user.id])
		if game:
			sql = f"""UPDATE Totals
					SET Paid = Paid + {spent}, Won = Won + {won}, Profit = Profit + {profit}, Games = Games + 1, {game} = {game} + {profit}
					WHERE DiscordID = '{interaction.user.id}';"""
		else:
			sql = f"""UPDATE Totals
				SET Paid = Paid + {spent}, Won = Won + {won}, Profit = Profit + {profit}, Games = Games + 1
				WHERE DiscordID = '{interaction.user.id}';"""

		conn = sqlite3.connect(config.db)
		conn.execute(sql)
		conn.commit()
		conn.close()


def setup(bot):
	bot.add_cog(Totals(bot))