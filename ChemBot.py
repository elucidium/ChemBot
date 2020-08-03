import os

import discord
from discord.ext import commands
from chemspipy import ChemSpider

from dotenv import load_dotenv
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHEMSPIDER_TOKEN = os.getenv('CHEMSPIDER_TOKEN')

cs = ChemSpider(CHEMSPIDER_TOKEN)

client = commands.Bot(command_prefix="!")

@client.event
async def on_ready():
    print('Logged in as ' + str(client.user.name) + '(' + str(client.user.id) + ')')

def print_details(c):
    formula = c.molecular_formula
    formula = formula.replace('{', '').replace('}', '').replace('_', '')
    return ('**ChemSpider ID**: ' + str(c.record_id)
        + '\n**Molecular formula**: ' + formula
        + '\n**Average mass**: ' + str(c.average_mass)
        + '\n**Molecular weight**: ' + str(c.molecular_weight)
        + '\n**Common name**: ' + c.common_name
        + '\n**Image**: ' + c.image_url
    )

@client.command(pass_context=True)
async def search(ctx, arg):
    print(arg)
    results = cs.search(arg)
    if len(results) == 0:
        await ctx.channel.send('No results found.')
    else:
        await ctx.channel.send(print_details(results[0]))

client.run(DISCORD_TOKEN)