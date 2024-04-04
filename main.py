import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

# from cogs.auctions import AuctionScheduler

import config
import ztoken

bot = commands.AutoShardedBot(intents=nextcord.Intents.all())
bot.remove_command('help')

restartingSoon = False

extensions = ["db", 
			  "cogs.achievements",
			  "cogs.alerts",
			  "cogs.auctions",
			  "cogs.games.bj",				# removable
			  "cogs.games.bjmultiplayer",	# removable
			  "cogs.games.coinflip",		# removable
			  "cogs.games.color_guesser",	# removable
			  "cogs.games.crash", 			# removable
			  "cogs.games.dond",			# removable
			  "cogs.games.hangman",			# removable
			  "cogs.games.horse",			# removable
			  "cogs.games.horsemultiplayer",# removable
			  "cogs.games.lottery",			# removable
			  "cogs.games.miner",			# removable
			  "cogs.games.mines",			# removable
			  "cogs.games.poker",			# removable
			  "cogs.games.pokermultiplayer",# removable
			  "cogs.games.roulette", 		# removable
			  "cogs.games.rps",				# removable
			  "cogs.games.scratch", 		# removable
			  "cogs.games.slots", 			# removable
			  "cogs.admin", 				# removable
			  "cogs.bank", 					# removable
			  "cogs.codes",
			  "cogs.crypto",
			  "cogs.daily",					# removable
			  "cogs.economy", 
			  "cogs.error_handling",
			  "cogs.fish",					# removable
			  "cogs.inventory",
			  "cogs.monopoly",				# removable
			  "cogs.multipliers",
			  "cogs.others", 				# removable
			  "cogs.prestige",				# removable
			  "cogs.quests", 
			  "cogs.rankedsystem",			# removable
			  "cogs.settings",				# removable
			  "cogs.shop", 
			  "cogs.totals",
			  "cogs.ttt", 					# removable
			  "cogs.util", 
			  "cogs.vote",					# removable
			  "cogs.weeklymonthly",			# removable
			  "cogs.xp"] 


@bot.event
async def on_ready():
	global LogFile

	LogFile = open("Logs.txt", "a")

	print(f"{bot.user.name} - {bot.user.id}")
	print(nextcord.__version__)
	print("Ready...")

	await bot.change_presence(activity=nextcord.Game(name="Do /help for help! SLASH COMMANDS!!!"))



@bot.event
async def on_interaction(interaction: Interaction):
	# if interaction.user.id != config.botOwnerDiscordID:
	# 	await interaction.send("Updating bot!!! Check back in 10 minutes! :partying_face: ")
	# 	return
	# print(interaction.type)
	if restartingSoon and interaction.type == 2:
		await interaction.send(f"Bot will be updating soon! Join the [Support Server]({config.serverInviteURL})] for updates.")
		return

	if isinstance(interaction.channel, nextcord.PartialMessageable):
		await interaction.send("Commands are not allowed in DMs! They can only be done in servers.", ephemeral=True)
		return
	if not await bot.get_cog("Economy").accCheck(interaction.user):
		embed = nextcord.Embed(color=1768431, title=f"{bot.user.name} | Welcome!")
		await bot.get_cog("Economy").StartPlaying(interaction, interaction.user)
		
		img = nextcord.File("./images/wumpus/wave.png", filename="wave.png")
		embed.set_thumbnail(url="attachment://wave.png")
		embed.description = f"{interaction.user.mention}, now that you're successfully registered, you can use commands. Please run command again!"
		await interaction.send(embed=embed, file=img)
		return

	await bot.process_application_commands(interaction)

# manually load a cog
@bot.slash_command(guild_ids=[config.adminServerID])
@commands.is_owner()
async def restartsoon(ctx):
	global restartingSoon
	restartingSoon = True
	await ctx.send("Disabled commands")

# manually load a cog
@bot.slash_command(guild_ids=[config.adminServerID])
@commands.is_owner()
async def load(ctx, extension):
	try:
		bot.load_extension(extension)
		print(f"Loaded {extension}.\n")
		await ctx.send(f"Loaded {extension}")
	except Exception as error:
		print(f"{extension} could not be loaded. [{error}]")
		await ctx.send(f"{extension} could not be loaded. [{error}]")


# manually unload a cog
@bot.slash_command(guild_ids=[config.adminServerID])
@commands.is_owner()
async def unload(ctx, extension):
	try:
		bot.unload_extension(extension)
		print(f"Unloaded {extension}.\n")
		await ctx.send(f"Unloaded {extension}")
	except Exception as error:
		print(f"{extension} could not be unloaded. [{error}]")
		await ctx.send(f"{extension} could not be unloaded. [{error}]")


# manually reload a cog
@bot.slash_command(guild_ids=[config.adminServerID])
@commands.is_owner()
async def reload(ctx, extension: str):
	if extension == 'all':
		lst = bot.extensions.copy()
		for ext in lst:
			try:
				if ext == "cogs.vote":
					continue
				bot.reload_extension(ext)
				print(f"Reloaded {ext}.")
				# await ctx.send(f"Reloaded {ext}")
			except Exception as error:
				print(f"{ext} could not be reloaded. [{error}]")
				await ctx.send(f"{ext} could not be reloaded. [{error}]")
		await ctx.send("Finished reloading.")
	else:
		try:
			bot.reload_extension(extension)
			print(f"Reloaded {extension}.\n")
			await ctx.send(f"Reloaded {extension}")
		except Exception as error:
			print(f"{extension} could not be reloaded. [{error}]")
			await ctx.send(f"{extension} could not be reloaded. [{error}]")



async def main():
	# if you need to, initialize other things, such as aiohttp
	for extension in extensions:
		try:
			bot.load_extension(extension)
			print(f"Loaded cog: {extension}")
		except Exception as error:
			print(f"{extension} could not be loaded. [{error}]")

	await bot.start(ztoken.token)

bot.loop.run_until_complete(main())