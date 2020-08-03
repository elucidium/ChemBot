import os

import discord
from discord.ext import commands
from chemspipy import ChemSpider

from dotenv import load_dotenv
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHEMSPIDER_TOKEN = os.getenv('CHEMSPIDER_TOKEN')

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

cs = ChemSpider(CHEMSPIDER_TOKEN)

client = commands.Bot(command_prefix='!')

driver = webdriver.Firefox()
driver.get('https://www.sigmaaldrich.com/united-states.html')

@client.event
async def on_ready():
    print('Logged in as ' + str(client.user.name) + '(' + str(client.user.id) + ')')

def details_to_embed(c, query):
    formula = c.molecular_formula
    formula = formula.replace('{', '').replace('}', '').replace('_', '')
    embedVar = discord.Embed(title='Chemical Search', color=0x05668d)
    embedVar.add_field(
        name='ChemSpider ID',
        value='[' + str(c.record_id) + '](http://www.chemspider.com/Chemical-Structure.' + str(c.record_id) + '.html)',
        inline=False
    )
    embedVar.add_field(name='Molecular formula', value=formula, inline=True)
    embedVar.add_field(name='Molecular weight', value=str(c.molecular_weight), inline=True)
    embedVar.add_field(name='Common name', value=c.common_name, inline=True)
    embedVar.set_image(url=c.image_url)
    return embedVar

@client.command(pass_context=True)
async def search(ctx, *args):
    query = ' '.join(args)
    results = cs.search(query)
    if len(results) == 0:
        await ctx.channel.send('No results found.')
    else:
        await ctx.channel.send(embed=details_to_embed(results[0], query))

@client.command(pass_context=True)
async def sds(ctx, *args):
    query = ' '.join(args)
    results = cs.search(query)
    if len(results) == 0:
        await ctx.channel.send('No results found.')
    else:
        try:
            c = results[0]
            search = driver.find_element_by_id('Query')
            search.clear()
            search.send_keys(c.inchi)
            search.send_keys(Keys.RETURN)
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'productNumberValue'))
            )
            driver.find_element_by_css_selector('.productNumberValue > a').click()
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, 'btn-msds'))
            )
            driver.find_element_by_id('btn-msds').click()
            WebDriverWait(driver, 1)
            embedVar = discord.Embed(
                title='SDS Search',
                description='[SDS for ' + c.common_name + '](' + driver.current_url + ')',
                color=0x05668d
            )
            await ctx.channel.send(embed=embedVar)
        except:
            await(ctx.channel.send('SDS not found for' + c.common_name + '.'))

client.run(DISCORD_TOKEN)