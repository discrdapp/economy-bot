import nextcord
from nextcord.ext import commands 
from nextcord import Interaction
from nextcord import FFmpegPCMAudio 
from nextcord import Member 
from nextcord.ext.commands import has_permissions, MissingPermissions

import random
import asyncio
import time
import json

import ztoken

bot = commands.Bot()
bot.remove_command('help')

extensions = ["db", 
			  "cogs.admin", 
			  "cogs.bank", 
			  "cogs.bj",
			  "cogs.coinflip",
			  "cogs.color_guesser", 
			  "cogs.crash",
			  "cogs.daily",
			  "cogs.economy", 
			  "cogs.error_handling",
			  "cogs.miner",
			  "cogs.others", 
			  "cogs.quests", 
			  "cogs.roulette", 
			  "cogs.rps",
			  "cogs.scratch", 
			  "cogs.shop", 
			  "cogs.slots", 
			  "cogs.totals",
			  "cogs.ttt", 
			  "cogs.user_settings", 
			  "cogs.util", 
			  "cogs.vote",
			  "cogs.weeklymonthly",
			  "cogs.xp"] # list of cogs to call
# extensions = ["db", "cogs.daily", "cogs.admin"]


@bot.event
async def on_ready():
	global LogFile

	LogFile = open("Logs.txt", "a")

	print(f"{bot.user.name} - {bot.user.id}")
	print(nextcord.__version__)
	print("Ready...")

	await bot.change_presence(activity=nextcord.Game(name="Do /help for help! SLASH COMMANDS!!!"))


# stop user input
# @bot.event
# async def on_message(message):
# 	if message.author.bot:
# 		return
# 	if message.content[0] != '.':
# 		return
# 	if not await bot.is_owner(message.author):
# 		await message.channel.send("Improving bot... Please check back in 1 hour!")
# 		return
# 	await bot.process_commands(message)

# manually load a cog
@bot.slash_command()
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
@bot.slash_command()
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
@bot.slash_command()
@commands.is_owner()
async def reload(ctx, extension):
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