import discord
from discord.ext import commands
import random
import asyncio
from discord.ext.commands import has_permissions
from discord.utils import find
import time
import json

import ztoken

async def get_prefix(bot, message):
	with open(r"prefix.json", 'r') as f:
		prefixFile = json.load(f)

	try:
		prefix = prefixFile[f"{message.guild.id}"]
	except:
		prefix = "."
	return prefix

bot = commands.Bot(command_prefix = get_prefix, case_insensitive=True)
bot.remove_command('help')

extensions = ["cogs.admin", "cogs.bank", "cogs.bj", "cogs.coinflip", "cogs.color_guesser", "cogs.crash",
			  "cogs.daily", "cogs.economy", "cogs.error_handling", "cogs.lottery", "cogs.miner", "cogs.others", "cogs.roulette", "cogs.rps", 
			  "cogs.scratch", "cogs.shop", "cogs.slots", "cogs.totals", "cogs.ttt", "cogs.user_settings", "cogs.util", "cogs.vote", "cogs.weeklymonthly",
			   "cogs.xp"] # list of cogs to call
# took out "cogs.minesweeper"

# async def background_loop():
#     await bot.wait_until_ready()
#     while not bot.is_closed():
#         channels = [585234678106030083, 585234706568708106]
#         amnts = [10, 15, 20, 25, 30, 35, 50, 75, 100]
#         #time = [60, 120, 150, 180]
#         time = 10
#         channel = bot.get_channel(random.choice(channels))
#         amnt = random.choice(amnts)
#         coin = "<:coins:585233801320333313>"
#         await channel.send(f"A random treasure chest appears with {amnt}{coin}\nType $claim to grab it!", file=discord.File('crate.gif'))
#         def is_me(m):
#             return m.content == "claim" and m.channel == channel
#         crateClaim = await bot.wait_for('message', check=is_me, timeout=40)
#         await bot.get_cog("Economy").addWinnings(crateClaim.author.id, amnt)
#         balance = bot.get_cog("Economy").getBalance(crateClaim.author.id)
#         await channel.send(f"Congrats {crateClaim.author.mention}, you won {amnt}{coin}!\n**Credits:** {balance}{coin}")
#         # Type !claim to random.choice(messages))
#         await asyncio.sleep(100000)


@bot.event
async def on_ready():
	global LogFile

	LogFile = open("Logs.txt", "a")

	print(f"{bot.user.name} - {bot.user.id}")
	print(discord.__version__)
	print("Ready...")

	await bot.change_presence(activity=discord.Game(name="Do .help for help!"))

# @bot.command()
# async def button(ctx):
# 	await ctx.send(
# 		"gg no ree",
# 		components = [
# 			Button(label = "click me!");
# 			Button(label = "Yeet");
# 		]
# 	)

# 	interaction = await bot.wait_for("button_click")
# 	await interaction.respond(content="YEET BITCH");

# 	if interaction.component.label == "click me!":
# 		pass
# 	elif interaction.component.label == "Yeet":
# 		pass

# COMMAND LOGGER

# @bot.event 
# async def on_message(message):
# 	if message.author.id != "585227426615787540" and message.content.startswith("$"):
# 		localTime = time.asctime(time.localtime(time.time()))
# 		LogFile.write(f"\n{message.author}:{message.guild}:{localTime}:{message.content}")
# 		LogFile.flush()

# @bot.event
# async def on_guild_join(guild):
# 	ch = bot.get_channel(790282431860047882)
# 	await ch.send(f"Added to {guild.name}")
# 	general = find(lambda x: 'general' in x.name.lower(), guild.text_channels)
# 	if general and general.permissions_for(guild.me).send_messages:
# 		await general.send(f'Hello {guild.name}, and thanks for adding me!\nType `.help` for my commands.\nEveryone will need to type `.start` in order to register!')
# 	else:
# 		await guild.owner.send('Error: I either do not have permissions to send messages or there is not a `general` channel for me to send my welcome message.')

# @bot.event
# async def on_guild_remove(guild):
# 	ch = bot.get_channel(790282431860047882)
# 	await ch.send(f"Removed from {guild.name}")
	
# manually load a cog
@bot.command()
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
@bot.command()
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
@bot.command()
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

if __name__ == '__main__':
	for extension in extensions:
		try:
			bot.load_extension(extension)
			print(f"Loaded cog: {extension}")
		except Exception as error:
			print(f"{extension} could not be loaded. [{error}]")
	# bot.loop.create_task(background_loop())
	bot.run(ztoken.token)
