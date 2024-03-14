from nextcord import File, Interaction
from random import randint

# used for displaying the progress bar for active /quests
bf = "<:bottom_filled:894039100926070784>"
brf = "<:bottom_right_filled:894039100858961941>"
tr = "<:top_right:894039100854767628>"
trf = "<:top_right_filled:894039100804452382>"
tl = "<:top_left:894039100821209148>"
tlf = "<:top_left_filled:894039100821229578>"
bl = "<:bottom_left:894039100745744415>"
blf = "<:bottom_left_filled:894039100808626196>"
t = "<:top:894039100733157388>"
tf = "<:top_filled:894039100754133022>"
b = "<:bottom:894039100666052630>"
br = "<:bottom_right:894039100523421738>"

small_l = "<:small_l:1203108335021461545>"
small_lf = "<:small_lf:1203108336468369459>"
small_r = "<:small_r:1203108346266386493>"
small_rf = "<:small_rf:1203108348329861190>"
small_m = "<:small_m:1203108337802027008>"
small_mf = "<:small_mf:1203108339102523422>"


coin = "<:credits:1102297413357686965>"
bitcoinEmoji = "<:bitcoin:1143401555656196237>"
litecoinEmoji = "<:Litecoin:1143402028832407633>"
ethereumEmoji = "<:Ethereum:1143402400581959691>"

async def SendInteractionWithWave(interaction:Interaction, embed):
	if randint(0, 1) == 0:
		file = File("images/wumpus/pokerwumpus.png", filename="helpImage.png")
	else:
		file = File("images/wumpus/blackjackwumpus.png", filename="helpImage.png")

	embed.set_thumbnail(url="attachment://helpImage.png")
	await interaction.send(embed=embed, file=file)
	file.close()

async def SendInteractionWithStop(interaction:Interaction, embed, ephemeral:bool):
	file = File("images/wumpus/stop.png", filename="stopImage.png")

	embed.set_thumbnail(url="attachment://stopImage.png")
	await interaction.send(embed=embed, file=file)
	file.close()

async def SendInteractionWithError(interaction:Interaction, embed, ephemeral:bool):
	file = File("images/wumpus/error.png", filename="errorImage.png")

	embed.set_thumbnail(url="attachment://errorImage.png")
	await interaction.send(embed=embed, file=file)
	file.close()

def GetWin():
	return File("images/wumpus/win.png", filename="results.png")

def GetLose():
	return File("images/wumpus/lose.png", filename="results.png")


def GetRandomFace():
	x = randint(0, 2)

	if x == 0:
		file = File("images/wumpus/disappointed.png", filename="randomImage.png")
	elif x == 1:
		file = File("images/wumpus/sus.png", filename="randomImage.png")
	elif x == 2:
		file = File("images/wumpus/thinking.png", filename="randomImage.png")
	
	return file