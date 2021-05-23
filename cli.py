from kickassanime_scraper import automate_scraping, player
from automatic_checker import download_location, main as checker
from sys import platform, argv
from os import system
import asyncio
try:
    from selectmenu import SelectMenu
except ImportError:
    print('\nSelectmenu not installed, using basic menu layout.')
    class SelectMenu:
        def add_choices(self, choices: list):
            self.choices = choices

        def select(self, prompt=None):
            print(prompt or "What would you like?")
            for j, i in enumerate(self.choices): print(j, i)
            print()
            return self.choices[int(input('Enter choice number: '))]

base_url = "https://www2.kickassanime.lol"

if len(argv) > 1:
    if platform.startswith("win"):
        system(f'python play.py {" ".join(argv[1:])}')
    else:
        system(f'python3 play.py {" ".join(argv[1:])}')
    exit()

async def search_and_download():
    query = input("Enter anime name: ")
    data = await player.search(query)
    print(data["name"])
    print("Skip episode numbers to default to first or latest episode")
    link = base_url + data["slug"]
    try:
        ep_start = int(input("Enter Episode to start from: "))
    except ValueError:
        ep_start = None
    try:
        ep_end = int(input("Enter Episode to end from: "))
    except:
        ep_end = None
    await automate_scraping(
        link,
        ep_start,
        ep_end,
        only_player=False,
        get_ext_servers=True,
        download_location=download_location,
    )


async def play():
    if platform.startswith("win"):
        system("play.bat")
    else:
        system("bash play.sh")


async def auto_update():
    await checker()
    input("Enter to exit...")


async def config():
    print("Go to your download location -> Config")
    print("To see current configuration settings")


menu = SelectMenu()
choices = {
    "Play Episode": play,
    "Search And Download": search_and_download,
    "Autoupdate Library": auto_update,
    "See Config": config,
}
menu.add_choices(list(choices.keys()))
result = menu.select("What would you like?")
print(result)

asyncio.get_event_loop().run_until_complete(choices[result]())