import re
import json
import asyncio
from utilities.async_web import fetch
from aiohttp import ClientSession
from utilities.anime_pace_scraperasdf import scraper
import os
from aiodownloader import downloader, utils
from typing import Tuple
from base64 import b64decode

with open("config.json") as file:
    priority = json.loads(file.read())
    
class kickass:
    def __init__(
        self,
        session,
        url="https://www2.kickassanime.rs/anime/dummy",
        arbitrary_name=False,
        episode_link=None,
    ):
        if "episode" not in url.split("/")[-1]:
            self.base_url = url
        else:
            self.base_url = "/".join(url.split("/")[:-1])
        if arbitrary_name:
            self.name = "anything"
        else:
            self.name = " ".join(self.base_url.split("/")[-1].split("-")[:-1])
        self.episode_link = episode_link
        self.session = session

    @staticmethod
    async def _get_data(script):
        result = re.findall(r"\{.+\}", str(script))
        a = result[0].replace(r" || {}", "")
        return json.loads(a)

    async def scrape_episodes(self) -> GeneratorExit:
        soup = await fetch(self.base_url, self.session)
        for i in soup.find_all("script"):
            if "appUrl" in str(i):
                data = await kickass._get_data(i)
                # print(data.keys())
                results = data["anime"]["episodes"]
        self.last_episode = int(results[0]["slug"].split("/")[-1].split("-")[1])
        return ("https://www2.kickassanime.rs" + i["slug"] for i in results)

    async def get_embeds(self, episode_link=None) -> dict:
        """ player, download, ep_num, ext_servers, episode_countdown """
        if episode_link == None:
            if self.episode_link == None:
                raise Exception("no url supplied")
            else:
                pass
        else:
            self.episode_link = episode_link
        episode_num = int(self.episode_link.split("/")[-1].split("-")[1])
        print(f"Getting episode {episode_num}")
        soup = await fetch(self.episode_link, self.session)
        for i in soup.find_all("script"):
            if "appUrl" in str(i):
                data = await kickass._get_data(i)
                break

        result = []
        # for i,j in data["episode"].items():
        #     print(i,j)
        for i in data["episode"].values():
            try:
                if "http" in i:
                    result.append(i)
            except TypeError:
                pass
        # print(result)
        ret = {
            "player": [],
            "download": None,
            "ext_servers": None,
            "can_download": True,
            "episode_countdown": False,
        }
        for i in result:
            if "mobile2" in i.split("/"):
                # print('yes')
                ret["download"] = i.strip()
            else:
                # print('no')
                ret["player"].append(i.strip())
        try:
            if data["ext_servers"] != None:
                ret["ext_servers"] = data["ext_servers"]
            else:
                pass
        except:
            print("ext server error")
        if ret["download"] != None:
            ret["download"] = await self.get_servers(ret["download"])
        else:
            ret["can_download"] = False
        ret["ep_num"] = episode_num

        if 'countdown' in ret["player"][0]:
            ret['episode_countdown'] = True
        else:
            pass

        return ret

    async def get_servers(self, dow_link):
        if dow_link != None:
            soup = await fetch(dow_link, self.session)
            return ((i.text, i["value"]) for i in soup.find_all("option"))
        else:
            return (None, None)

    async def get_episodes_embeds_range(self, start=0, end=None):
        if start == None:
            start = 0
        gen = await self.scrape_episodes()
        ed = end or self.last_episode
        x = 0
        if end != None:
            for _ in gen:
                if x != self.last_episode - ed - 1:
                    x += 1
                    pass
                else:
                    x += 1
                    break
        else:
            pass
        flag = ed - start + 1
        n = 0
        for i in gen:
            if n < flag:
                n += 1
                yield self.get_embeds(i)

    async def get_download(self, download_links: tuple, episode_number: int) -> tuple:
        """ returns tuple like (link, file_name)
            :download_links: are the available server links"""
        available = []
        # print(type(priority))
        for i in download_links:
            # print(i[0])
            if i[0] in priority.keys():
                available.append(i)
        # print(available)
        await asyncio.sleep(0)
        flag = 999
        final = None
        for i in available:
            if list(priority.keys()).index(i[0]) <= flag:
                flag = list(priority.keys()).index(i[0])
                final = i
        print(final[0])
        a = scraper(self.base_url)
        a.quality = priority[final[0]]
        a.get_final_links(final[1])
        file_name = f"{self.name} ep_{episode_number:02d}.mp4"
        # print(file_name)
        if len(a.final_dow_urls) != 0:
            return (a.final_dow_urls[0].replace(" ", "%20"), file_name)
        else:
            print(f'cannot download {episode_number}')
            return (None, None)

    async def get_from_player(self, player_links: list, episode_number: int) -> str:
        a = player(self.session)
        print(f'writing episode {episode_number}\n')
        flag = False
        if len(player_links) > 1:
            print(f'number of player links is {len(player_links)}')
            flag = True
        else:
            pass

        with open('episodes.txt', 'a+') as f:
            f.write(f'{self.name} episode {episode_number}: \n')
            for i,j in await a.get_player_embeds(player_links[0]):
                # await a.get_from_server(j)
                f.write(f"\t{i}: {j}\n")
                if flag == True:
                    for i in player_links[1:]:
                        f.write(f'\t{i}\n')
                else:
                    pass
        return f'done episode {episode_number}'


class player():
    def __init__(self, session):
        self.session = session

    @staticmethod
    async def _get_from_script(script):
        try:
            a = re.findall(r"\{.+\}", str(script))[0]
            return json.loads(f"[{a}]")
        except:
            print('invalid player url supplied')
            return None
        
    async def get_player_embeds(self, player_link: str) -> Tuple['name', 'link'] :
        soup = await fetch(player_link, self.session)
        for i in soup.find_all("script"):
            if "var" in str(i):
                data = await player._get_from_script(i)
                if data:
                    result = data
                    break
                else:
                    continue
        else:
            print('Player link error')
            return [(None, None)]
        return ((i["name"], i["src"]) for i in result)

    async def get_from_server(self, server_link):
        soup = await fetch(server_link, self.session)
        for i in soup.find_all('script'):
            x = str(i)
            if "document.write" in x and len(x) > 783:
                link = b64decode(re.search(r'\.decode\("(.+)"\)', str(i)).group(1))
                break
        return link

async def automate_scraping(link, start_episode = None, end_episode = None, automatic_downloads = False):
    async with ClientSession() as sess:
        var = kickass(sess, link)
        print(var.name)
        tasks = []
        async for i in var.get_episodes_embeds_range(start_episode, end_episode):
            tasks.append(i)
        embed_result = await asyncio.gather(*tasks)

        download_tasks = []
        player_tasks = []
        for i in embed_result:
            print(f"Starting episode {i['ep_num']}")
            if i['ext_servers'] != None:
                print(f"available ext servers are {i['ext_servers']}")
            if i["episode_countdown"] == True:
                print(f'episode {i["ep_num"]} is still in countdown')
                continue
            elif i["can_download"]:
                download_tasks.append(var.get_download(i["download"], i["ep_num"]))
            else:
                player_tasks.append(var.get_from_player(i["player"], i['ep_num']))

        links_and_names = await asyncio.gather(*download_tasks)

        def dow_maker(url, name):
            return downloader.DownloadJob(sess, url, name, os.getcwd())
        
        def write_links(links_list):
            with open('episodes.txt', 'a+') as f:
                for i in links_list:
                    l, n = i
                    f.write(f'{n}: {l} \n')

        if automatic_downloads:
            ans = 'y'
        else:
            ans = input("\ndownload now y/n?: ")    

        if ans == "y":
            if len(links_and_names) != 0:
                print(f"starting all downloads for {var.name} \nPlease Wait.....")
                jobs = [dow_maker(*i) for i in links_and_names if None not in i]
                tasks_3 = [asyncio.ensure_future(job.download()) for job in jobs]
                if len(jobs) != 0:
                    await utils.multi_progress_bar(jobs)
                    await asyncio.gather(*tasks_3, return_exceptions=True)
                else:
                    print('Nothing to download')

            else:
                print('Nothing to download')

        else:
            write_links(links_and_names)

        to_play = await asyncio.gather(*player_tasks)
        for i in to_play:
            print(i)
        
        if len(links_and_names) == 0:
            return (var.name, None)
        else:
            return (var.name, links_and_names[0][1])
if __name__ == "__main__":
    # import uvloop
    # asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    link = "https://www2.kickassanime.rs/anime/tokyo-godfathers-485925/episode-01-603407"
    asyncio.get_event_loop().run_until_complete(automate_scraping(link))
    print("\nOMEDETO !!")
