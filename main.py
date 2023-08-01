import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import config
import ztoken

bot = commands.Bot()
bot.remove_command('help')

extensions = ["db", 
			  "cogs.games.bj",
			  "cogs.games.coinflip",
			  "cogs.games.color_guesser",
			  "cogs.games.crash", 
			  "cogs.games.dond",
			  "cogs.games.lottery",
			  "cogs.games.miner",
			  "cogs.games.mines",
			  "cogs.games.roulette", 
			  "cogs.games.rps",
			  "cogs.games.scratch", 
			  "cogs.games.slots", 
			  "cogs.admin", 
			  "cogs.bank", 
			  "cogs.daily",
			  "cogs.economy", 
			  "cogs.error_handling",
			  "cogs.fish",
			  "cogs.inventory",
			  "cogs.multipliers",
			  "cogs.others", 
			  "cogs.quests", 
			  "cogs.shop", 
			  "cogs.totals",
			  "cogs.ttt", 
			  "cogs.user_settings", 
			  "cogs.util", 
			  "cogs.vote",
			  "cogs.weeklymonthly",
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
	if not await bot.get_cog("Economy").accCheck(interaction.user):
		await bot.get_cog("Economy").StartPlaying(interaction, interaction.user)
		if interaction.data['name'] == 'blackjack':
			await interaction.send("You can now play blackjack now that you're registered. Please run command again.", ephemeral=True)
			return

	await bot.process_application_commands(interaction)


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