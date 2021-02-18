from kickassanime_scraper import kickass, player
from aiohttp import ClientSession, TCPConnector
import asyncio
import subprocess
import json

with open('./Config/watch_config.json') as file:
    data = json.loads(file.read())
    priority = data['priority']
    ext_priority = data['ext_priority']

async def get_watch_link(anime_link, ep_num, session):
    var = kickass(session, anime_link)
    print(var.name)
    # dont touch this as its a generator
    all_episodes = await var.scrape_episodes() # just to set var.last_episode
    try:            
        if ep_num == var.last_episode:
            data = await var.get_episodes_embeds_range(start=ep_num, end=None, episodes_tuple=all_episodes).__anext__() # because async generator
        else:
            data = await var.get_episodes_embeds_range(start=ep_num, end=ep_num, episodes_tuple=all_episodes).__anext__() # because async generator
        data = await data 
        ext_links = data['ext_servers']
        player_links = data['player']

    except StopAsyncIteration:
        print('Episode range exceeded')
        return None

    player_scraper = player(session)
    if len(player_links) > 1: # just some experimental stuff
        print(f"number of player links is {len(player_links)}")

    available = []
    names = list(priority.keys())
    embed_links = await player_scraper.get_player_embed_links(player_links[0])
    if embed_links is not None or False:
        for i in embed_links:
            if i['name'] in names:
                available.append(i)

        if len(available) == 0:
            print('no player available')
            return None

        flag = 999
        final = None
        for i in available:
            if names.index(i['name']) < flag:
                flag = names.index(i['name'])
                final = i
            else:
                continue
        
        print(final['name'])
        link = await player_scraper.get_from_server(final['name'], final['src'])
        if priority[final['name']]:
            return link[1][priority[final['name']]] # link is like [server_name, link]
        else:
            return link[1]
    else:
        print('Trying ext_servers')
        link = await player_scraper.get_ext_server(ext_links[ext_priority[0]], ext_priority[0])
        return link

def play(link):
    cmd = ['cvlc', link]
    try:
        assert link is not None
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        process.wait()
    except:
        exit()

async def watch(episode, query=None, link=None, option_number=None):

    async with ClientSession(connector=TCPConnector(ssl=False)) as session:
        if (not link) and query:
            dict_info = await player.search(query, session, option=option_number)
            link = 'https://www2.kickassanime.rs'+dict_info['slug']
        else:
            print('No link or query supplied')
            return None
        player_link = await get_watch_link(link, episode, session)
        print(player_link)
        play(player_link)

if __name__ == '__main__':
    episode = 5
    link = 'https://www2.kickassanime.rs/anime/rezero-kara-hajimeru-isekai-seikatsu-2nd-season-part-2-613847/episode-07-619966'
    query = 'kobayashi'
    opt = None or None
    asyncio.get_event_loop().run_until_complete(watch(episode, link=None, query=query, option_number=opt))