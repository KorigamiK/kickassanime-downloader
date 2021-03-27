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


async def get_watch_link(anime_link, ep_num, session, ext_only=False):
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

    available = []
    names = list(priority.keys())
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

    if embed_links is not None and not ext_only:
        for i in embed_links:
            if i["name"] in names:
                available.append(i)

        if len(available) == 0:
            print("no player available")
            return None

        flag = 999
        final = None
        for i in available:
            if names.index(i["name"]) < flag:
                flag = names.index(i["name"])
                final = i
            else:
                continue

        print(final["name"])
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
            query = f'vlc --play-and-exit -f --http-referrer="https://betaplayer.life/api/embed/1615556106095" --one-instance --no-playlist-enqueue "{link}"'
            subprocess.run(query, shell=True)
        else:
            cmd = ["mpv", f'"{link}"', "--http-header-fields='Referer: https://betaplayer.life/api/embed/1615556106095'"] # I know hardcoding is bad
            subprocess.run(' '.join(cmd), shell=True)
            # process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            # process.wait()
    except:
        exit()


async def watch(episode, query=None, link=None, option_number=None, ext_only=False):

    async with ClientSession(connector=TCPConnector(ssl=False)) as session:
        if (not link) and query:
            dict_info = await player.search(query, session, option=option_number)
            link = "https://www2.kickassanime.rs" + dict_info["slug"]
        elif (query is None) and link:
            pass
        else:
            print("No link or query supplied")
            return None
        print(link)
        player_link = await get_watch_link(link, episode, session, ext_only)
        # print(player_link)
        play(player_link)


if __name__ == "__main__":
    episode = 2
    # link = "https://www2.kickassanime.rs/anime/summer-wars-dub-100201" and None
    link = None
    query = 'jojo'
    opt = 1
    flag = False
    asyncio.get_event_loop().run_until_complete(
        watch(episode, link=link, query=query, option_number=opt, ext_only=flag)
    )
