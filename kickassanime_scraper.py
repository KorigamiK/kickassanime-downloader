import re
import json
import asyncio
from utilities.async_web import fetch
from aiohttp import ClientSession
from utilities.anime_pace_scraperasdf import scraper
import os
from aiodownloader import downloader, utils
from typing import List
from base64 import b64decode
from bs4 import BeautifulSoup as bs

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
        results = [None]
        for i in soup.find_all("script"):
            if "appUrl" in str(i):
                data = await kickass._get_data(i)
                # print(data.keys())
                results = data["anime"]["episodes"]
        try:
            self.last_episode = int(results[0]["slug"].split("/")[-1].split("-")[1])
        except ValueError:  # for ovas and stuff
            self.last_episode = 0

        return ("https://www2.kickassanime.rs" + i["slug"] for i in results)

    async def get_embeds(self, episode_link=None) -> dict:
        """player, download, ep_num, ext_servers, episode_countdown
        either pass the download link or set self.episode_link manually"""
        if episode_link == None:
            if self.episode_link == None:
                raise Exception("no url supplied")
            else:
                pass
        else:
            self.episode_link = episode_link

        try:
            episode_num = int(self.episode_link.split("/")[-1].split("-")[1])
        except ValueError:  # for ovas and stuff
            episode_num = 0

        print(f"Getting episode {episode_num}")
        soup = await fetch(self.episode_link, self.session)
        data: dict[str] = None
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
            except TypeError:  # means
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

        if "countdown" in ret["player"][0]:
            ret["episode_countdown"] = True
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
        """returns tuple like (link, file_name)
        :download_links: are the available server links"""
        available = []
        # print(type(priority))
        for i in download_links:
            # print(i[0])
            if i[0] in priority.keys():
                available.append(i)
        # print(available)
        if len(available) == 0:
            print(f"No available server in config.json for episode {episode_number}")
            return (None, None)

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
        await a.get_final_links(final[1])
        file_name = f"{self.name} ep_{episode_number:02d}.mp4"
        # print(file_name)
        if len(a.final_dow_urls) != 0:
            return (a.final_dow_urls[0].replace(" ", "%20"), file_name)
        else:
            print(f"cannot download {episode_number}")
            return (None, None)

    async def get_from_player(self, player_links: list, episode_number: int) -> str:
        a = player(self.session)
        print(f"writing episode {episode_number}\n")
        flag = False
        if len(player_links) > 1:
            print(f"number of player links is {len(player_links)}")
            flag = True
        else:
            pass

        with open("episodes.txt", "a+") as f:
            f.write(f"\n{self.name} episode {episode_number}: \n")
            for i, j in await a.get_player_embeds(player_links[0]):
                # await a.get_from_server(j)
                f.write(f"\t{i}: {j}\n")
                if flag == True:
                    for i in player_links[1:]:
                        f.write(f"\t{i}\n")
                else:
                    pass
        return f"No download links for {self.name} episode {episode_number}. Written player links"


class player:
    def __init__(self, session):
        self.session = session

    @staticmethod
    async def _get_from_script(script):
        try:
            a = re.findall(r"\{.+\}", str(script))[0]
            return json.loads(f"[{a}]")
        except:
            print("invalid player url supplied")
            return None

    async def get_player_embeds(self, player_link: str) -> List[str]:
        """ returns list[("name", "link"), ...]"""
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
            print("Player link error")
            return [(None, None)]
        res = [self.get_from_server(i["name"], i["src"]) for i in result]
        return await asyncio.gather(*res)

    async def get_from_server(self, server_name, server_link):
        """ returns list: [[server_name, link], ...]"""
        iframe_url = server_link.replace("player.php?", "pref.php?")
        soup = await fetch(iframe_url, self.session)
        def get_script():
            for i in soup.find_all("script"):
                x = str(i)
                if "document.write" in x and len(x) > 783:
                    return b64decode(
                        re.search(r'\.decode\("(.+)"\)', str(i)).group(1)
                    )

        if server_name == "PINK-BIRD":
            script_tag: str = get_script()
            return [server_name, bs(script_tag, "html.parser").find("source")["src"]]

        elif server_name == "SAPPHIRE-DUCK":
            script_tag: str = get_script()
            sap_duck = bs(script_tag, "html.parser")
            java_script = str(sap_duck.select_one("script"))

            return [
                server_name,
                re.search(r'(http.*)"', java_script).group(1).replace(r"\/", r"/"),
            ]
        elif server_name == "BETASERVER3":
            res = ''
            links_list = []
            for i in soup.find_all('script'):
                if 'file' in str(i):
                    links_list = json.loads(re.findall(r'\[{.*}]', str(i))[0])
                    break
            for i in links_list:
                res += f"\t\t{i['label']}: {i['file']}\n"
                        
            return [server_name, res]

        else:
            # print(f"not implemented server {server_name}")
            return [server_name, server_link]


async def automate_scraping(
    link,
    start_episode=None,
    end_episode=None,
    automatic_downloads=False,
    download_location=os.getcwd(),
    only_player=False,
):
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
            if i["ext_servers"] != None:
                print(f"available ext servers are {i['ext_servers']}")
            if i["episode_countdown"] == True:
                print(f'episode {i["ep_num"]} is still in countdown')
                continue
            elif i["can_download"] and not only_player:
                download_tasks.append(var.get_download(i["download"], i["ep_num"]))
            else:
                player_tasks.append(var.get_from_player(i["player"], i["ep_num"]))

        links_and_names = await asyncio.gather(*download_tasks)

        def dow_maker(url, name):
            return downloader.DownloadJob(sess, url, name, download_location)

        def write_links(links_list):
            with open("episodes.txt", "a+") as f:
                for i in links_list:
                    f.write("\n")
                    l, n = i
                    f.write(f"{n}: {l} \n")
        ans = 'n'
        if automatic_downloads:
            ans = "y"
        else:
            if not only_player:
                ans = input("\ndownload now y/n?: ")

        if ans == "y" and not only_player:
            if len(links_and_names) != 0:
                print(f"starting all downloads for {var.name} \nPlease Wait.....")
                jobs = [dow_maker(*i) for i in links_and_names if None not in i]
                tasks_3 = [asyncio.ensure_future(job.download()) for job in jobs]
                if len(jobs) != 0:
                    await utils.multi_progress_bar(jobs)
                    await asyncio.gather(*tasks_3, return_exceptions=True)
                else:
                    # to avoid too much stdout
                    if automatic_downloads == False:
                        print(
                            "Nothing to download"
                        )  # when countdown links may give none and non empty links_and_names

            else:
                # to avoid too much stdout
                if automatic_downloads == False:
                    print("Nothing to download")

        else:
            if not only_player:
                write_links(links_and_names)

        to_play = await asyncio.gather(*player_tasks)

        for i in to_play:
            if not only_player:
                print(i)

        if len(links_and_names) == 0:
            return (var.name, None)
        else:
            return (var.name, links_and_names[0][1])


if __name__ == "__main__":
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    link = "https://www2.kickassanime.rs/anime/dr-stone-stone-wars-802545/episode-02-114680"
    asyncio.get_event_loop().run_until_complete(automate_scraping(link, 1, 2, only_player=True))
    print("\nOMEDETO !!")
elif False:

    async def main_test():
        async with ClientSession() as sess:
            var = player(sess)
            f = 1
            ser = "https://kaa-play.com/dust/player.php?link=lMPAFDFNWf9Bx5XWn@LhO@YLW@9Yf5A0V71PhAAfaBs9nxid3Y3vlRNYUJRauxgN0QGZGKQ0eoPEg70m4enjkQWFP06/yZ/RXKkgWYrt6qUgneW7OcOBk9OJ/LR7s@MUKInqY1VmRzV2gHGxn26ryOZZoVEUsWU3b00q5u1Bm86bCNcBW0lb&link2=lMPAFDFNWf9Bx5XWn@LhO@YLW@9Yf5A0V71PhAAfaBs9nxid3Y3vlRNYUJRauxgN0QGZGKQ0eoPEg70m4enjkQWFP06/yZ/RXKkgWYrt6qUgneW7OcOBk9OJ/LR7s@MUKInqY1VmRzV2gHGxn26ryOZZoVEUsWU3b00q5u1Bm86bCNcBW0lb&link3=&link4=&link5=&link6=&link7=&link8=&link9=&link10=&link11="
            for i in await var.get_player_embeds(ser):
                if f == 2:
                    print(await var.get_from_server(*i), end="\n\n")
                f += 1

    asyncio.run(main_test())
