from selectmenu import SelectMenu
from kickassanime_scraper import automate_scraping, player
from automatic_checker import download_location, main as checker
from sys import platform
import os
import asyncio

base_url = 'https://www2.kickassanime.rs'
async def search_and_download():
    query = input('Enter anime name: ')
    data = await player.search(query)
    print(data["name"])
    print('Skip episode numbers to default to first or latest episode')
    link = base_url + data['slug']
    ep_start = int(input('Enter Episode to start from: ')) or None
    ep_end = int(input('Enter Episode to end from: ')) or None
    await automate_scraping(link, ep_start, ep_end, only_player=False, get_ext_servers=True, download_location=download_location)

async def play():
    if platform.startswith('win'):
        os.system('play.bat')
    else:
        os.system('bash play.sh')

async def auto_update():
    await checker()
    input('Enter to exit...')

async def config():
    print('Go to your download location -> Config')
    print('To see current configuration settings')

menu = SelectMenu()
choices = {"Play Episode": play, "Search And Download": search_and_download, "Autoupdate Library": auto_update, "See Config": config}
menu.add_choices(list(choices.keys()))
result = menu.select("What would you like?")
print(result)

asyncio.get_event_loop().run_until_complete(choices[result]())