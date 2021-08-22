# import dbl
import discord
from discord.ext import commands
import asyncio
import random
import topgg


class Vote(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(description="Vote")
	@commands.bot_has_guild_permissions(send_messages=True, embed_links=True, use_external_emojis=True)
	@commands.cooldown(1, 43200, commands.BucketType.user)
	async def vote(self, ctx):
		token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjU4NTIzNTAwMDQ1OTI2NDAwNSIsImJvdCI6dHJ1ZSwiaWF0IjoxNjA4Nzc3NzE0fQ.8Bu5bRL6-64ITKOimvi93GSdolUGxyOy5WhLvTmQPi8' # set this to your DBL token
		topggpy = topgg.DBLClient(self.bot, token)

		embed = discord.Embed(color=1768431, title=f"{self.bot.user.name} | Vote")
		embed.set_thumbnail(url=ctx.author.avatar_url)
		try:
			if await topggpy.get_user_vote(ctx.author.id):
				await self.bot.get_cog("Economy").addWinnings(ctx.author.id, 8500)
				embed.set_thumbnail(url=ctx.author.avatar_url)
				embed.add_field(name="Thanks for Voting!", value="8500<:coins:585233801320333313> has been added to your account")
			else:
				embed.add_field(name="Cannot Claim", value="You have not voted yet.\n[Click here](https://top.gg/bot/585235000459264005/vote/) to vote.")
				await ctx.send("You have not voted yet.")
				ctx.command.reset_cooldown(ctx)
		finally:
			await topggpy.close()
		await ctx.send(embed=embed)

def setup(bot):
	bot.add_cog(Vote(bot))