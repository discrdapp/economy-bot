import dbl
import discord
from discord.ext import commands
import asyncio


class Vote(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjU4NTIzNTAwMDQ1OTI2NDAwNSIsImJvdCI6dHJ1ZSwiaWF0IjoxNjA4Nzc3NzE0fQ.8Bu5bRL6-64ITKOimvi93GSdolUGxyOy5WhLvTmQPi8' # set this to your DBL token
		self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=True) # Autopost will post your guild count every 30 minutes
		self.claimAvailable = list()

	@commands.command(description="Vote")
	@commands.bot_has_guild_permissions(send_messages=True, embed_links=True, use_external_emojis=True)
	async def vote(self, ctx):
		if ctx.author in self.claimAvailable:
			await ctx.send("Claimed successfully!")
		else:
			await ctx.send("You have not voted yet.")

	@commands.Cog.listener()
	async def on_dbl_vote(data):
		print(data)
		print(f"User who voted is {data[1]}")
		self.claimAvailable.append(data[1])
		# print(f"User who voted is {data.user}")

	@commands.command()
	async def showUnclaimed(self, ctx):
		msg = ""
		for x in self.claimAvailable:
			msg += f"{x}\n"
		await ctx.send(f"Claims are available for:\n{msg}")

def setup(bot):
	bot.add_cog(Vote(bot))