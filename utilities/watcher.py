import os
import sys
from os import path
from typing import Coroutine, Dict, Tuple, Union
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from kickassanime_scraper import kickass, player, debug, DOMAIN_REGEX, WEBSITE_DOMAIN
from utilities.pace_scraper import COLOUR
from aiohttp import ClientSession, TCPConnector
import asyncio
import subprocess
import json

with open("./Config/watch_config.json") as file:
    data = json.loads(file.read())
    priority = data["priority"]
    ext_priority = data["ext_priority"]
    mpv_args = data["mpv_args"]
    try:
        operating_system = data["system"]
    except KeyError:
        from os import name as operating_system
        
names = list(priority.keys())

async def get_watch_link(anime_link, ep_num, session, ext_only=False, custom_server='')-> Union[None, str, Tuple[str, Union[dict, None]]]:
    '''Returns Either None or tuple with link, header=None, dict'''
    
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
        print(f"number of player links is {len(player_links)}", player_links)

    embed_links = None

    async def try_ext(index=0):
        if index == 0: print(f"Trying ext_servers {ext_priority[index]}")
        else: print(f'Trying next {ext_priority[index]}')
        if len(ext_priority)-1 == index: 
            print("Cannot play using ext_servers. Try disabling the flag")
            print(data)
            # import pyperclip
            # pyperclip.copy(f'{data}')
            return None

        try:
            assert ext_links[ext_priority[index]]
            print(ext_priority[index])
            link, header = await player_scraper.get_ext_server(ext_links[ext_priority[index]], ext_priority[index])
            return link, header

        except KeyError:
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
        header = link[2]
        if priority[final["name"]] and link[1]: # checks if any options are mentioned in the watch_config
            return link[1][priority[final["name"]]], header  # link is like [server_name, link] link can be str | dict | None
        else:
            return link[1], header
    else:
        return await try_ext()


def play(link, encode, header: Union[None, Dict[str, str]]=None):
    try:
        assert link is not None
        if debug:
            print(COLOUR.blue(link))
        if encode and 'm3u8' in link:
            print(f'Headers for this episode are: \n{header}')
            print('Run this to download the stream ->')
            print(f'ffmpeg -i "{link}" -map 0:p:{mpv_args[0][-1]} -c:v libx265 -c:a copy -preset fast -x265-params crf=26 out.ts')
            print('Run this to encode the stream ->')
            print(f'ffmpeg -i out.ts -c:v copy -c:a copy final.mp4')
            print('Change them however you like')
            return None

        elif encode:
            print('Cannot encode non m3u8 episodes. Try disabling the flag')
            return None
        
        if operating_system == 'nt':
            query = f'vlc --play-and-exit -f --one-instance --no-playlist-enqueue "{link}"'
            if 'streamani' not in link:
                if header:
                    query += f' --http-referrer="{header["Referer"]}"'
                    if header.get('Subtitle') and len(header.get('Subtitle')):
                        query += ' --sub-files="'+':'.join([i.replace(':', '\:') for i in header.get('Subtitle')])+'"'
                else:
                    query += ' --http-referrer="https://betaplayer.life/"'
            subprocess.run(query, shell=True)
        else:
            cmd = ["mpv", f'"{link}"'] # I know hardcoding is bad
            if 'streamani' not in link:
                if header:
                    cmd.append(f'--http-header-fields="Referer: {header.get("Referer")}"')
                    if header.get('Subtitle') and len(header.get('Subtitle')):
                        cmd.append('--sub-files="'+':'.join([i.replace(':', '\:') for i in header.get('Subtitle')])+'"')

                else:
                    cmd.append('--http-header-fields="Referer: https://betaplayer.life/"')
            cmd += mpv_args

            if os.system == 'nt':
                cmd = [r'C:\Windows\System32\cmd.exe'] + cmd
            subprocess.run(' '.join(cmd), shell=True)
            # print(' '.join(cmd))
            # process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            # process.wait()
    except AssertionError:
        print(COLOUR.error('This server did not work. Try to decrease the priority of this server or try with --ext flag.'))
        exit()


async def watch(episode, query=None, link=None, option_number=None, ext_only=False, custom_server='', stop=False, encode=False):

    async with ClientSession(connector=TCPConnector(ssl=False)) as session:
        if (not link) and query:
            dict_info = await player.search(query, session, option=option_number)
            if not dict_info:
                print('Check for typos in the query. Exiting...')
                return None
            link = (DOMAIN_REGEX.sub(WEBSITE_DOMAIN, "https://www2.kickassanime.rs")) + dict_info["slug"]
        elif (query is None) and link:
            pass
        else:
            print("No link or query supplied")
            return None
        print(link)
        if stop: return None
        player_link = await get_watch_link(link, episode, session, ext_only, custom_server=custom_server)
        try:
            header = player_link[1]
            play(player_link[0], encode, header)
        except Exception:
            play(player_link, encode)


if __name__ == "__main__":
    episode = 3
    link = "https://www2.kickassanime.ro/anime/shingeki-no-kyojin-the-final-season-part-2-264095/episode-03-807343"# and None
    # query = 'maid dragon'
    query = None
    opt = -2
    flag = False
    server = '' # or 'PINK-BIRD'
    asyncio.run(
        watch(episode, link=link, query=query, option_number=opt, ext_only=flag, custom_server=server, encode=False)
    )
