import discord
from discord.ext import commands
import pymysql
import asyncio
import config

import random

class Shop(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.items = [1000, 5000, 25000, 100000, 150000, 250000, 20000]
		self.coin = "<:coins:585233801320333313>"


	@commands.group(invoke_without_command=True)
	async def shop(self, ctx):
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))
			
		if ctx.invoked_subcommand is None:
			await ctx.send("```ML\nID            ITEMS                COST\n"
								+ "----------------------------------------\n"
								+ "1            1 crate               1,000\n"
								+ "2             1 key                5,000\n"
								+ "3      +1,000 to daily reward     25,000\n\n"
								# + "4       +500 to lvl reward       100,000\n"
								# + "5      ---------------------     150,000\n"
								# + "6   +1.5x Profit on Future Games 250,000\n"
								+ "7     +1,500 to donator reward    20,000\n"
								+ "----------------------------------------\n"
								+ "Use .shop buy <id> <amount>\n\n\tSHOP IS A WORK IN PROGRESS!```")

	@shop.command()
	async def buy(self, ctx, ID, amnt: int=1):
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start')) 
		try:
			ID = int(ID)
		except:
			if ID == "crate" or ID == "crates":
				ID = 1
			elif ID == "key" or ID == "keys":
				ID = 2
			else:
				ID = 100

		if ID != 1 and ID != 2 and ID != 3 and ID != 7:
			await ctx.send("Invalid item ID.")
			await ctx.invoke(self.bot.get_command('shop'))
			return
		if ID == 7 and not self.bot.get_cog("Economy").isDonator(ctx.author.id):
			embed = discord.Embed(color=1768431)
			embed.set_thumbnail(url=ctx.author.avatar_url)
			embed.add_field(name = f"Shop", 
							value = f"That can only be used by Donators! To donate, type .donate", inline=False)
			embed.set_footer(text=f"{ctx.author}")
			await ctx.send(embed=embed)
			return

		discordId = ctx.author.id
		cost = self.items[ID - 1] * amnt
		balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
		
		if balance < cost:
			embed = discord.Embed(color=1768431, title=f"{self.bot.user.name} | Shop")
			embed.set_thumbnail(url=ctx.author.avatar_url)
			embed.add_field(name="Error", value=f"That will cost you {cost}{self.coin}, but you only have {balance}{self.coin}")
			embed.set_footer(text=f"{ctx.author}")
			await ctx.send(embed=embed)
			return

		await self.bot.get_cog("Economy").addWinnings(discordId, -(cost))
		db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
		cursor = db.cursor()
		
		if ID == 1:
			sql = f"""UPDATE Inventory
				  SET Crates = Crates + {amnt}
				  WHERE DiscordID = '{discordId}';"""
			cursor.execute(sql)
			db.commit()
			await ctx.invoke(self.bot.get_command('balance'))

		elif ID == 2:
			sql = f"""UPDATE Inventory
				  SET Keyss = Keyss + {amnt}
				  WHERE DiscordID = '{discordId}';"""
			cursor.execute(sql)
			db.commit()
			await ctx.invoke(self.bot.get_command('balance'))

		elif ID == 3:
			sql = f"""UPDATE Economy
				  SET DailyReward = DailyReward + {amnt * 1000}
				  WHERE DiscordID = '{discordId}';"""
			cursor.execute(sql)
			db.commit()	

			embed = discord.Embed(color=1768431)
			embed.set_thumbnail(url=ctx.author.avatar_url)
			embed.set_footer(text=f"{ctx.author}")
			embed.add_field(name = f"Shop", 
							value = f"Successfully added {amnt * 1000}{self.coin} to daily reward")
			await ctx.send(embed=embed)

		# elif ID == 4:
		# 	sql = f"""UPDATE Economy
		# 		  SET LevelReward = LevelReward + 500
		# 		  WHERE DiscordID = '{discordId}';"""
		# 	cursor.execute(sql)
		# 	db.commit()	

		# elif ID == 5:
		# 	pass

		# elif ID == 6:
		# 	sql = f"""UPDATE Economy
		# 		  SET Multiplier = Multiplier + 0.5
		# 		  WHERE DiscordID = '{discordId}';"""
		# 	cursor.execute(sql)
		# 	db.commit()	

		elif ID == 7:
			sql = f"""UPDATE Economy
				  SET DonatorReward = DonatorReward + {amnt * 1500}
				  WHERE DiscordID = '{discordId}';"""
			cursor.execute(sql)
			db.commit()	

			embed = discord.Embed(color=1768431)
			embed.add_field(name = f"Shop", 
							value = f"Successfully added {amnt * 1000}{self.coin} to donator reward")
			embed.set_thumbnail(url=ctx.author.avatar_url)
			embed.set_footer(text=f"{ctx.author}")
			await ctx.send(embed=embed)


		db.close()


	@shop.command()
	async def sell(self, ctx, ID: int, amnt: int=1):
		await ctx.send("WORK IN PROGRESS!")

	@commands.group(aliases=['open'])
	async def crate(self, ctx):
		# await ctx.send(".crate open 1*")
		if ctx.invoked_subcommand is None:
			embed = discord.Embed(color=1768431, title=f"{self.bot.user.name} | Open a crate to receive a prize!")
			embed.add_field(name="Possible prizes and their chances:", value=f"**(30%)** 0-3 Crates\n**(30%)** 1-3 Keys\n**(20%)** 5000-12500{self.coin}\n**(20%)** 0 - 500{self.coin}\nMore coming soon...")
			embed.set_footer(text=".crate open")
			embed.set_thumbnail(url=ctx.author.avatar_url)

			await ctx.send(embed=embed)


	@crate.command()
	async def open(self, ctx, amnt=1):
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))

		embed = discord.Embed(color=1768431, title=f"{self.bot.user.name} | Shop")
		embed.set_thumbnail(url=ctx.author.avatar_url)

		crates, keys = await self.bot.get_cog("Economy").getInventory(ctx.author)
		if crates < amnt:
			embed.add_field(name="Invalid Amount", value=f"{ctx.author.mention}, you only have {crates} crates. You cannot open {amnt} crate(s).")
			embed.set_footer(text="Buy more crates from the shop!")
		elif keys < amnt:
			embed.add_field(name="Invalid Amount", value=f"{ctx.author.mention}, you only have {keys} keys. You cannot use {amnt} key(s).")
			embed.set_footer(text="Buy more keys from the shop!")
		elif amnt > 0:
			await self.bot.get_cog("Economy").subtractInv(ctx.author.id, amnt)
			
			crates = crates - amnt
			keys = keys - amnt
			for x in range(0, amnt):
				choice = random.randint(1, 10)
				if choice <= 3:
					amnt = random.randint(0, 3)
					embed.add_field(name="Crate opened...", value=f"You found {amnt} crates!")
					crates += amnt

				elif choice <= 6:
					amnt = random.randint(1, 3)
					embed.add_field(name="Crate opened...", value=f"You found {amnt} keys!")
					keys += amnt

				elif choice <= 8:
					bal = random.randint(5000, 12500)
					embed.add_field(name="Crate opened...", value=f"You found {bal}{self.coin}!")
					await self.bot.get_cog("Economy").addWinnings(ctx.author.id, bal)
					
				elif choice <= 10:
					bal = random.randint(0, 500)
					embed.add_field(name="Crate opened...", value=f"You found {bal}{self.coin}!")
					await self.bot.get_cog("Economy").addWinnings(ctx.author.id, bal)
			await ctx.send(embed=embed)

			db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
			cursor = db.cursor()
			sql = f"""UPDATE Inventory
					  SET Crates = {crates}, Keyss = {keys}
					  WHERE DiscordID = '{ctx.author.id}';"""
			cursor.execute(sql)
			db.commit()

			db.close()

			await ctx.invoke(self.bot.get_command('balance'))
			return
		else:
			embed.add_field(name="Invalid Amount", value=f"{ctx.author.mention}, you cannot open a negative amount of crates.")

		await ctx.send(embed=embed)



def setup(bot):
	bot.add_cog(Shop(bot))