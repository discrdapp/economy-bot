import discord
from discord.ext import commands
import asyncio
import random
import topgg

import config
import json


class Vote(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.coin = "<:coins:585233801320333313>"

	@commands.command(description="Vote")
	@commands.bot_has_guild_permissions(send_messages=True, embed_links=True, use_external_emojis=True)
	@commands.cooldown(1, 60, commands.BucketType.user)
	async def vote(self, ctx):
		embed = discord.Embed(color=1768431, title=f"{self.bot.user.name} | Vote")
		embed.set_thumbnail(url=ctx.author.avatar_url)

		with open(r"votes.json", 'r') as f:
			votes = json.load(f)

		try:
			numOfVotes = votes[f"{ctx.author.id}"]
		except:
			embed.add_field(name="Links", value="[top.gg](https://top.gg/bot/585235000459264005/vote/)\n" + 
				"[discordbotlist](https://discordbotlist.com/bots/casino-bot/upvote)\n" + 
				"[discord.boats](https://discord.boats/bot/585235000459264005/vote)")
			await ctx.send("You have not voted yet." + 
				f"\n**\*\**NEW* \*\*** You can now vote on THREE different websites and get 8500{self.coin} for each vote!", embed=embed)
			return

		if numOfVotes == 1: times = "Time"
		else: times = "Times"

		moneyToAdd = 8500 * numOfVotes
		await self.bot.get_cog("Economy").addWinnings(ctx.author.id, moneyToAdd)
		
		embed.add_field(name=f"Thanks for Voting {numOfVotes} {times}!", value=f"{moneyToAdd}{self.coin} has been added to your account")
		msg = await ctx.send(embed=embed)
		await msg.add_reaction("❤️")

		del votes[f"{ctx.author.id}"]
		with open(r"votes.json", 'w') as f:
			json.dump(votes, f, indent=4)

def setup(bot):
	bot.add_cog(Vote(bot))