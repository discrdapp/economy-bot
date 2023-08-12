# economy-related stuff like betting and gambling, etc.
import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import sqlite3, datetime, json, cooldowns, uuid
from PIL import Image, ImageDraw, ImageFont, ImageColor
from math import floor

import config
from db import DB

actualGame = ["Slt", "BJ", "Crsh", "RLTTE", "CF", "RPS"]

def log(discordID, creditsSpent, creditsWon, activity, bal): # Logs what credits have been spent where, by who, to who, why and the time which this has happened
	# #localtime = time.asctime(time.localtime(time.time()))
	x = datetime.datetime.now()
						#  MON DAY YY HOUR:MIN:SEC
	localtime = x.strftime("%b/%d/%y %H:%M:%S")
	# logs = open("logs.txt", "a")
	# logs.write(f"{localtime} : {discordID} : {creditsSpent} : {creditsWon} : {bal} : {actualGame[gameNumber]}\n")
	# logs.flush()
	# logs.close()

	gameID = (str(uuid.uuid4())[:8]).upper()

	if type(activity) == int:
		print("IS INTEGER!")
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
	async def log(self, interaction:Interaction, gameid):
		game = DB.fetchOne("SELECT * FROM Logs WHERE ID = ? LIMIT 1;", [gameid])

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Logs")

		if not game:
			embed.description =f"No log found for ID \n{gameid}"
			await interaction.send(embed=embed, ephemeral=True)
			return

		if str(interaction.user.id) != game[2]:
			embed.description = "This is not your log to view!"
			await interaction.send(embed=embed, ephemeral=True)
			return

		embed.add_field(name="Activity", value=game[6], inline=False)
		embed.add_field(name="Credits Spent", value=f"{game[3]:,}")
		embed.add_field(name="Credits Gained", value=f"{game[4]:,}")
		embed.add_field(name="New Balance", value=f"{game[5]:,}", inline=False)

		embed.set_footer(text=f"ID: {game[0]}\nDate: {game[1]}")

		await interaction.send(embed=embed, ephemeral=True)

	@nextcord.slash_command()
	async def profile(self, interaction:Interaction):
		pass
	
	@profile.subcommand()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='view')
	async def view(self, interaction:Interaction):
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

		try:
			embedColor = profileFile[f"{interaction.user.id}"]["embedColor"]
			textColor = profileFile[f"{interaction.user.id}"]["textColor"]
			background = profileFile[f"{interaction.user.id}"]["background"]
		except:
			embedColor = 1768431
			textColor = (170,126,0)
			background = "scroll.png"

			profileFile[f"{interaction.user.id}"] = dict()
			profileFile[f"{interaction.user.id}"]["embedColor"] = embedColor
			profileFile[f"{interaction.user.id}"]["textColor"] = textColor
			profileFile[f"{interaction.user.id}"]["background"] = background
			with open(r"profiles.json", 'w') as f:
				json.dump(profileFile, f, indent=4)

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
		draw.text(xy=(100,100), text=f"{interaction.user.name}", fill=tuple(textColor), font=ImageFont.truetype('HappyMonksMedievalLookingScript.ttf',55))
		draw.text(xy=(420,160), text=f"Level {level:,}", fill=tuple(textColor), font=font_type)
		draw.text(xy=(100,160), text=f"Balance: {balance:,}", fill=tuple(textColor), font=font_type)
		draw.text(xy=(100,230), text=f"Badges", fill=tuple(textColor), font=font_type)
		img.save("images/profile.png")
		file = nextcord.File("images/profile.png", filename="image.png")
		embed.set_image(url="attachment://image.png")

		embed.set_footer(text=f"Customize your profile with /profile edit")

		await interaction.send(file=file, embed=embed)


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
		await interaction.send(embed=embed)
		await interaction.send(embed=embed1)
		await interaction.send(embed=embed2)


	@profile.subcommand()
	async def edit(self, interaction:Interaction):
		pass

	@edit.subcommand(description="Get color list from /colors")
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='embedcolor')
	async def embedcolor(self, interaction:Interaction, choice):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Edit Profile")
		embed.set_thumbnail(url=interaction.user.avatar)
		try:
			newColor = self.colors[choice]
		except:
			embed.add_field(name="Error", value="Color not found. Type /colors to see all available colors")
			await interaction.send(embed=embed)
			return

		with open(r"profiles.json", 'r') as f:
			profileFile = json.load(f)

		profileFile[f"{interaction.user.id}"]["embedColor"] = newColor
		with open(r"profiles.json", 'w') as f:
			json.dump(profileFile, f, indent=4)

		embed.add_field(name="Success!", value=f"Your profile's embed color has been changed to {choice}")
		embed.color = newColor
		await interaction.send(embed=embed)
	
	@edit.subcommand(description="Get color list from /colors")
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='textcolor')
	async def textcolor(self, interaction:Interaction, choice):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Edit Profile")
		embed.set_thumbnail(url=interaction.user.avatar)
		try:
			newColor = str(hex(self.colors[choice])) # convert to the literal hexadecimal string
		except:
			embed.add_field(name="Error", value="Color not found. Type /colors to see all available colors")
			await interaction.send(embed=embed)
			return
		newColor = "#" + "0"*(8-len(newColor))+ newColor[2:] # append trailing 0's and switch out 0x for #

		newColor = ImageColor.getcolor(newColor, "RGB") # get RGB version of color 
		
		with open(r"profiles.json", 'r') as f:
			profileFile = json.load(f)

		profileFile[f"{interaction.user.id}"]["textColor"] = newColor
		with open(r"profiles.json", 'w') as f:
			json.dump(profileFile, f, indent=4)

		embed.add_field(name="Success!", value=f"Your profile's text color has been changed to {choice}")
		embed.color = self.colors[choice]
		await interaction.send(embed=embed)

	@edit.subcommand()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='backgroundimage')
	async def backgroundimage(self, interaction:Interaction, choice = nextcord.SlashOption(
																required=True,
																name="bgimg", 
																choices=("scroll", "inkpaper", "spiralnotebook"))):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Edit Profile")
		embed.set_thumbnail(url=interaction.user.avatar)
		with open(r"profiles.json", 'r') as f:
			profileFile = json.load(f)

		if choice == "scroll":
			background = "scroll.png"
		elif choice == "inkpaper":
			background = "inkpaper.png"
		elif choice == "spiralnotebook":
			background = "spiralnotebook.png"

		profileFile[f"{interaction.user.id}"]["background"] = background
		with open(r"profiles.json", 'w') as f:
			json.dump(profileFile, f, indent=4)

		background = profileFile[f"{interaction.user.id}"]["background"]
		file = nextcord.File(f"./images/writingbackgrounds/{background}", filename="image.png")
		embed.set_image(url="attachment://image.png")
		embed.add_field(name="Edited!", value=f"Successfully changed to {choice}.")
		await interaction.send(file=file, embed=embed)


	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='badges')
	async def badges(self, interaction:Interaction):
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
		
		await interaction.send(embed=embed)


	@nextcord.slash_command()
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='stats')
	async def stats(self, interaction:Interaction):		
		getRow = DB.fetchOne("SELECT Paid, Won, Profit, Games, Slots, Blackjack, Crash, Roulette, Coinflip, RPS FROM Totals WHERE DiscordID = ?;", [interaction.user.id])

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

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Stats")
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

		await interaction.send(embed=embed)



	async def addTotals(self, interaction:Interaction, spent, won, game):
		discordID = interaction.user.id

		if game == 0: gameName = "Slots"		  
		elif game == 1: gameName = "Blackjack"
		elif game == 2: gameName = "Crash"
		elif game == 3: gameName = "Roulette"
		elif game == 4: gameName = "Coinflip"
		elif game == 5: gameName = "RPS"

		# bal = await self.bot.get_cog("Economy").getBalance(interaction.user)
		# log(discordID, spent, won, game, bal)

		if won < 0:
			won = 0
		if spent < 0:
			spent = 0
		profit = won - spent

		# DB.update("""UPDATE Totals
		# 		  SET Paid = Paid + ?, Won = Won + ?, Profit = Profit + ?, Games = Games + 1, ? = ? + ?
		# 		  WHERE DiscordID = ?;""", [spent, won, profit, gameName, gameName, profit, interaction.user.id])
		sql = f"""UPDATE Totals
				  SET Paid = Paid + {spent}, Won = Won + {won}, Profit = Profit + {profit}, Games = Games + 1, {gameName} = {gameName} + {profit}
				  WHERE DiscordID = '{interaction.user.id}';"""

		conn = sqlite3.connect(config.db)
		cursor = conn.execute(sql)
		conn.commit()
		conn.close()


def setup(bot):
	bot.add_cog(Totals(bot))