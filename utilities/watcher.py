import sys
from os import path
from os import name as operating_system
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from kickassanime_scraper import kickass, player, debug
from aiohttp import ClientSession, TCPConnector
import asyncio
import subprocess
import json

with open("./Config/watch_config.json") as file:
    data = json.loads(file.read())
    priority = data["priority"]
    ext_priority = data["ext_priority"]
    mpv_args = data["mpv_args"]
    
names = list(priority.keys())

async def get_watch_link(anime_link, ep_num, session, ext_only=False, custom_server: str=''):
    var = kickass(session, anime_link)
    print(var.name)
    # dont touch this as its a generator
    all_episodes = await var.scrape_episodes()  # just to set var.last_episode
    try:
        if ep_num == var.last_episode:
            data = await var.get_episodes_embeds_range(
                start=ep_num, end=None, episodes_tuple=all_episodes
            ).__anext__()  # because async generator
        else:
            data = await var.get_episodes_embeds_range(
                start=ep_num, end=ep_num, episodes_tuple=all_episodes
            ).__anext__()  # because async generator
        data = await data
        ext_links = data["ext_servers"]
        player_links = data["player"]

    except StopAsyncIteration:
        print("Episode range exceeded")
        return None

    player_scraper = player(session)
    if len(player_links) > 1:  # just some experimental stuff
        print(f"number of player links is {len(player_links)}")

    embed_links = None

    async def try_ext(index=0):
        if index == 0 :print("Trying ext_servers")
        else: print('Trying next.')
        if len(ext_priority)-1 == index: 
            print("Cannot play using ext_servers. Try disabling the flag")
            print(data)
            # import pyperclip
            # pyperclip.copy(f'{data}')
            return None

        try:
            assert ext_links[ext_priority[index]]
            print(ext_priority[index])
            link = await player_scraper.get_ext_server(
                ext_links[ext_priority[index]], ext_priority[index]
            )
            return link
        except:
            return await try_ext(index=index+1)

    if not ext_only:
        try:
            embed_links = await player_scraper.get_player_embed_links(player_links[0])
        except IndexError:
            print("Try adding --ext flag next time.")
            return await try_ext()
    else:
        return await try_ext()

    available = []
    if embed_links is not None and not ext_only:
        for i in embed_links:
            if i["name"] in names:
                available.append(i)

        if len(available) == 0:
            print("No player available")
            return await try_ext()

        flag = 999
        final = None
        for i in available:
            if i["name"] == custom_server:
                final = i
                break
            elif names.index(i["name"]) < flag:
                flag = names.index(i["name"])
                final = i            
            else:
                continue
        
        if custom_server and (final["name"] != custom_server): #if no custom server then it is an empty string
            print(f"Server {custom_server} not available.")
            # print(available)

        print(final["name"])
        # print([i["name"] for i in embed_links])
        link = await player_scraper.get_from_server(final["name"], final["src"])
        if priority[final["name"]]:
            return link[1][priority[final["name"]]]  # link is like [server_name, link]
        else:
            return link[1]
    else:
        return await try_ext()


def play(link):
    if debug:
        print(link)
    try:
        assert link is not None
        if operating_system == 'nt':
            query = f'vlc --play-and-exit -f --http-referrer="https://betaplayer.life/" --one-instance --no-playlist-enqueue "{link}"'
            subprocess.run(query, shell=True)
        else:
            cmd = ["mpv", f'"{link}"', "--http-header-fields='Referer: https://betaplayer.life/'"] + mpv_args # I know hardcoding is bad
            subprocess.run(' '.join(cmd), shell=True)
            # print(' '.join(cmd))
            # process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            # process.wait()
    except:
        exit()


async def watch(episode, query=None, link=None, option_number=None, ext_only=False, custom_server='', stop=False):

    async with ClientSession(connector=TCPConnector(ssl=False)) as session:
        if (not link) and query:
            dict_info = await player.search(query, session, option=option_number)
            if not dict_info:
                print('Check for typos in the query. Exiting...')
                return None
            link = "https://www2.kickassanime.rs" + dict_info["slug"]
        elif (query is None) and link:
            pass
        else:
            print("No link or query supplied")
            return None
        print(link)
        if stop: return None
        player_link = await get_watch_link(link, episode, session, ext_only, custom_server=custom_server)
        # print(player_link)
        play(player_link)


if __name__ == "__main__":
    episode = 1
    # link = "https://www2.kickassanime.rs/anime/summer-wars-dub-100201" and None
    link = None
    query = 'vivy'
    opt = 0
    flag = False
    server = '' or 'PINK-BIRD'
    asyncio.get_event_loop().run_until_complete(
        watch(episode, link=link, query=query, option_number=opt, ext_only=flag, custom_server=server)
    )
