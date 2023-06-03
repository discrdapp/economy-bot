import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import cooldowns
import json


class Vote(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.coin = "<:coins:585233801320333313>"

	@nextcord.slash_command(description="Vote")
	@commands.bot_has_guild_permissions(send_messages=True, embed_links=True, use_external_emojis=True)
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author)
	async def vote(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Vote")
		embed.set_thumbnail(url=interaction.user.avatar)

		with open(r"votes.json", 'r') as f:
			votes = json.load(f)

		try:
			numOfVotes = votes[f"{interaction.user.id}"]
		except:
			embed.add_field(name="Links", value="[top.gg](https://top.gg/bot/585235000459264005/vote/)\n" + 
				"[discordbotlist](https://discordbotlist.com/bots/casino-bot/upvote)\n")
			await interaction.send("You have not voted yet.", embed=embed)
			return

		if numOfVotes == 1: times = "Time"
		else: times = "Times"

		moneyToAdd = 8500 * numOfVotes
		await self.bot.get_cog("Economy").addWinnings(interaction.user.id, moneyToAdd)
		self.bot.get_cog("Inventory").addItemToInventory(interaction.user.id, 1, 'Voter Chip')
		
		embed.add_field(name=f"Thanks for Voting {numOfVotes} {times}!", value=f"{moneyToAdd}{self.coin} has been added to your account and you received your Voter Chip!")
		embed.set_footer(text="/use to use your Voter Chip")
		msg = await interaction.send(embed=embed)
		msg = await msg.fetch()
		await msg.add_reaction("❤️")

		del votes[f"{interaction.user.id}"]
		with open(r"votes.json", 'w') as f:
			json.dump(votes, f, indent=4)

def setup(bot):
	bot.add_cog(Vote(bot))