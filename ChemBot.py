import os

import discord
from discord.ext import commands

from chemspipy import ChemSpider
from chemspipy.errors import ChemSpiPyUnavailableError
import wolframalpha

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from dotenv import load_dotenv
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHEMSPIDER_TOKEN = os.getenv('CHEMSPIDER_TOKEN')
WOLFRAM_TOKEN = os.getenv('WOLFRAM_TOKEN')

cs = ChemSpider(CHEMSPIDER_TOKEN)
wolfram = wolframalpha.Client(WOLFRAM_TOKEN)

client = commands.Bot(command_prefix='!')

op = webdriver.ChromeOptions()
op.binary_location = os.getenv('GOOGLE_CHROME_BIN')
op.add_argument('--headless')
op.add_argument('--no-sandbox')
op.add_argument('--disable-dev-sh-usage')

driver = webdriver.Chrome(executable_path=os.getenv('CHROMEDRIVER_PATH'), chrome_options=op)
# for local testing purposes only; comment out when deployed to Heroku
#driver = webdriver.Firefox()

driver.get('https://www.sigmaaldrich.com/united-states.html')

@client.event
async def on_ready():
    print('Logged in as ' + str(client.user.name) + '(' + str(client.user.id) + ')')
    await client.change_presence(activity=discord.Game("run !help for more info"))

def details_to_embed(c, query):
    formula = c.molecular_formula
    formula = formula.replace('{', '').replace('}', '').replace('_', '')
    embedVar = discord.Embed(title='Chemical Search', color=0x05668d)
    embedVar.add_field(
        name='ChemSpider ID',
        value='[' + str(c.record_id) + '](http://www.chemspider.com/Chemical-Structure.' + str(c.record_id) + '.html) (click for more information)',
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
    try:
        results = cs.search(query)
        if len(results) == 0:
            await ctx.channel.send('No results found.')
        else:
            await ctx.channel.send(embed=details_to_embed(results[0], query))
    except ChemSpiPyUnavailableError:
        await ctx.channel.send('ChemSpider is temporarily unavailable.')

@client.command(pass_context=True)
async def sds(ctx, *args):
    query = ' '.join(args)
    results = cs.search(query)
    name = results[0].common_name if len(results) > 0 else query
    try:
        # check for the feedback popup blocking everything
        if driver.find_elements_by_css_selector('#fsrFocusFirst'):
            driver.find_element_by_id('fsrFocusFirst').click()
        search = driver.find_element_by_id('Query')
        search.clear()
        search.send_keys(query)
        search.send_keys(Keys.RETURN)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'msdsBulletPoint'))
        )
        driver.find_element_by_class_name('msdsBulletPoint').click()
        WebDriverWait(driver, 5)
        embedVar = discord.Embed(
            title='SDS Search',
            description='[SDS for ' + name + '](' + driver.current_url + ') (Sigma-Aldrich)',
            color=0x05668d
        )
        await ctx.channel.send(embed=embedVar)
    except:
        await(ctx.channel.send('SDS not found for ' + name + '.'))

@client.command(pass_context=True)
async def wolf(ctx, *args):
    query = ' '.join(args)
    result = wolfram.query(query)
    diagram = [pod for pod in result.pods if pod['@title'] == 'Structure diagram']
    basic = [pod for pod in result.pods if pod['@title'] == 'Basic properties']
    if len(basic) == 0:
        await ctx.channel.send('No results with "Basic properties" section found on Wolfram-Alpha for the query "' + query + '.')
    fields = basic[0]['subpod']['plaintext'].split('\n')
    embedVar = discord.Embed(title = "Wolfram|Alpha Search", color=0x05668d)
    embedVar.add_field(
        name='query',
        value='[' + query + '](https://www.wolframalpha.com/input/?i=' + query.replace(' ', '+') + ') (click for more information)', 
        inline=False)
    for field in fields:
        parse = field.split(" | ")
        embedVar.add_field(name=parse[0], value=parse[1], inline=False)
    embedVar.set_image(url=diagram[0]['subpod']['img']['@src'])
    await(ctx.channel.send(embed=embedVar))

# override default help command
client.remove_command('help')
@client.command(pass_context=True)
async def help(ctx):
    embedVar = discord.Embed(title="ChemBot Help", color=0x05668d)
    embedVar.add_field(
        name='!sds',
        value='Searches for SDS of given chemical on Sigma-Aldrich. (Please allow up to 20 seconds for the search to complete.)\nExample: `!sds methylene chloride`',
        inline=False
    )
    embedVar.add_field(
        name='!search',
        value='Searches for basic chemical information on ChemSpider.\nExample: `!search ethanol`',
        inline=False
    )
    embedVar.add_field(
        name='!wolf',
        value='Searches for chemical properties on Wolfram|Alpha.\nExample: `!wolf acetone`',
        inline=False
    )
    embedVar.add_field(
        name='Have more feature ideas? ✨',
        value='Feel free to [contribute](https://github.com/elucidium/ChemBot) or send feature suggestions to <@110416449306128384>!'
    )
    await(ctx.channel.send(embed=embedVar))

client.run(DISCORD_TOKEN)
