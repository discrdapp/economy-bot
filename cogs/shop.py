import discord
from discord.ext import commands
import utils
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
		if await self.bot.get_cog("Economy").accCheck(ctx.author):
			if ctx.invoked_subcommand is None:
				await ctx.send("```ML\nID            ITEMS                COST\n"
									+ "----------------------------------------\n"
									+ "1            1 crate               1,000\n"
									+ "2             1 key                5,000\n"
									 + "3        +1,000 to daily          25,000\n\n"
									# + "4       +500 to lvl reward       100,000\n"
									# + "5      ---------------------     150,000\n"
									# + "6   +1.5x Profit on Future Games 250,000\n"
									 + "7     +1,500 to donator reward    20,000\n"
									+ "----------------------------------------\n"
									+ "Use .shop buy <id> <amount>\n\n\tSHOP IS A WORK IN PROGRESS!```")

		else:
			await ctx.send("Hello! Please type .start to create your wallet. :smiley:")
			return 0

	@shop.command()
	async def buy(self, ctx, ID: int=0, amnt: int=1):
		if ID != 1 and ID != 2 and ID != 3 and ID != 7:
			await ctx.send("Invalid item ID.")
			await ctx.invoke(self.bot.get_command('shop'))
			return
		if ID == 7 and not self.bot.get_cog("Economy").isDonator(ctx.author.id):
			embed = discord.Embed(color=1768431)
			embed.add_field(name = f"Shop", 
							value = f"That can only be used by Donators! To donate, type .donate", inline=False)
			await ctx.send(embed=embed)
			return

		if await self.bot.get_cog("Economy").accCheck(ctx.author):
			discordId = ctx.author.id
			cost = self.items[ID - 1] * amnt
			balance = await self.bot.get_cog("Economy").getBalance(ctx.author)
			
			if balance < cost:
				await ctx.send(f"That will cost you {cost}{self.coin}, but you only have {balance}{self.coin}")
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
				await ctx.send(embed=embed)


			db.close()
		else:
			await ctx.send("Hello! Please type $start to create your wallet. :smiley:")


	@shop.command()
	async def sell(ctx, ID: int, amnt: int):
		await ctx.send("WORK IN PROGRESS!")

	@commands.group()
	async def crate(self, ctx):
		# await ctx.send(".crate open 1*")
		if ctx.invoked_subcommand is None:
			await ctx.send(f"Open a crate to receive a prize. \nPossible prizes and their chance:\n\t\t**(30%)** 0-3 Crates\n\t\t**(30%)** 1-3 Keys\n\t\t**(20%)** 5000-10000{self.coin}\n\t\t**(20%)** 0 - 500{self.coin}\n.crate open *amnt*")


	@crate.command()
	async def open(self, ctx, amnt=1):
		if await self.bot.get_cog("Economy").accCheck(ctx.author) == True:
			crates, keys = await self.bot.get_cog("Economy").getInventory(ctx.author)
			if crates < amnt:
				await ctx.send(f"{ctx.author.mention}, you only have {crates} crates. You cannot open {amnt} crate(s).")
			elif keys < amnt:
				await ctx.send(f"{ctx.author.mention}, you only have {keys} keys. You cannot open {amnt} key(s).")
			elif amnt > 0:
				await self.bot.get_cog("Economy").subtractInv(ctx.author.id, amnt)
				
				crates = crates - amnt
				keys = keys - amnt
				for x in range(0, amnt):
					choice = random.randint(1, 10)
					if choice <= 3:
						amnt = random.randint(0, 3)
						await ctx.send(f"You found {amnt} crates!")
						crates += amnt

					elif choice <= 6:
						amnt = random.randint(1, 3)
						await ctx.send(f"You found {amnt} keys!")
						keys += amnt

					elif choice <= 8:
						bal = random.randint(5000, 10000)
						await ctx.send(f"You found {bal}{self.coin}!")
						await self.bot.get_cog("Economy").addWinnings(ctx.author.id, bal)
						
					elif choice <= 10:
						bal = random.randint(0, 500)
						await ctx.send(f"You found {bal}{self.coin}!")
						await self.bot.get_cog("Economy").addWinnings(ctx.author.id, bal)

				db = pymysql.connect(host=config.host, port=3306, user=config.user, passwd=config.passwd, db=config.db, autocommit=True)
				cursor = db.cursor()
				sql = f"""UPDATE Inventory
						  SET Crates = {crates}, Keyss = {keys}
						  WHERE DiscordID = '{ctx.author.id}';"""
				cursor.execute(sql)
				db.commit()

				db.close()

				await ctx.invoke(self.bot.get_command('balance'))
			else:
				await ctx.send(f"\n{ctx.author.mention}, you cannot open a negative amount of crates.")
		else:
			await ctx.send("Hello! Please type $start to create your wallet. :smiley:")



def setup(bot):
	bot.add_cog(Shop(bot))