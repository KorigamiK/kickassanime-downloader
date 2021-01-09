import re
import json
import asyncio
from async_web import fetch
from aiohttp import ClientSession
from anime_pace_scraperasdf import scraper
import os
from aiodownloader import downloader, utils


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
        """ player, download, ep_num, ext_servers """
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
            i["can_download"] = False
        ret["ep_num"] = episode_num
        return ret

    async def get_servers(self, dow_link):
        if dow_link != None:
            soup = await fetch(dow_link, self.session)
            return ((i.text, i["value"]) for i in soup.find_all("option"))
        else:
            return (None, None)

    async def get_episodes_embeds_range(self, start=0, end=None):
        gen = await self.scrape_episodes()
        ed = end or self.last_episode
        if end != None:
            for i, _ in enumerate(gen):
                if i != self.last_episode - ed - 1:
                    pass
                else:
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
        """ returns tuple like (link, file_name)"""
        with open("config.json") as file:
            priority = json.loads(file.read())
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
            if list(priority.keys()).index(i[0]) < flag:
                flag = list(priority.keys()).index(i[0])
                final = i
        print(final[0])
        a = scraper(self.base_url)
        a.quality = priority[final[0]]
        a.get_final_links(final[1])
        file_name = f"{self.name} ep_{episode_number:02d}.mp4"
        # print(file_name)
        return (a.final_dow_urls[0].replace(" ", "%20"), file_name)

    async def get_from_player(self, player: list) -> str:
        print("not implemented yet")
        return


class player(kickass):
    def __init__(self):
        pass

    @staticmethod
    def _get_from_script(script):
        a = re.findall(r"\{.+\}", str(script))[0]
        return json.loads(f"[{a}]")

    async def get_player_embeds(self, player_link):
        import requests
        from bs4 import BeautifulSoup as bs

        request = requests.session()
        soup = bs(request.get(player_link).text, "html.parser")
        for i in soup.find_all("script"):
            if "var" in str(i):
                result = player._get_from_script(i)
                break
        return ((i["name"], i["src"]) for i in result)


if __name__ == "__main__":

    # import uvloop
    # asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    async def main():
        link = "https://www2.kickassanime.rs/anime/cells-at-work-code-black-335844/episode-01-553373"
        async with ClientSession() as sess:
            var = kickass(sess, link)
            print(var.name)
            tasks = []
            async for i in var.get_episodes_embeds_range(1):
                tasks.append(i)
            embed_result = await asyncio.gather(*tasks)

            tasks_2 = []
            for i in embed_result:
                print(f"Starting episode {i['ep_num']}")
                print(f"available ext servers are i['ext_servers']")
                if i["can_download"]:
                    tasks_2.append(var.get_download(i["download"], i["ep_num"]))
                else:
                    tasks_2.append(var.get_from_player(i["player"]))
            links_and_names = await asyncio.gather(*tasks_2)

            def dow_maker(url, name):
                return downloader.DownloadJob(sess, url, name, os.getcwd())

            if input("download now y/n?: ") == "y":
                print("starting all downloads \nPlease Wait.....")
                jobs = [dow_maker(*i) for i in links_and_names]
                tasks_3 = [asyncio.ensure_future(job.download()) for job in jobs]
                await utils.multi_progress_bar(jobs)
                await asyncio.gather(*tasks_3)
                return None
            else:
                print(links_and_names)
                return None

    asyncio.get_event_loop().run_until_complete(main())
    print("\n\nOMEDETO !!")
    # p = 'https://kaa-play.com/dust/player.php?link=lMPAFDFNWf9Bx5XWn@LhO@YLW@9Yf5A0V71PhAAfaBs9nxid3Y3vlRNEHYJM514CxhjcXIctd57Gga8t2KOdvFrlI3CLvcnxeLgWUrDQ7agyuqHLJPizr8q99qN9j@VOFa7kTxYGZjlLi3e9uFe55/gDiREKw1o0anUU5cMAz42lXswNCw4V9AjJXAF5CJSiVJ2mFiJhDXpBZEV3Xj92kgAEo3TgCHdaQ0aZjRmIPmJemX1b&link2=lMPAFDFNWf9Bx5XWn@LhO@YLW@9Yf5A0V71PhAAfaBs9nxid3Y3vlRNEHYJM514CxhjcXIctd57Gga8t2KOdvFrlI3CLvcnxeLgWUrDQ7agyuqHLJPizr8q99qN9j@VOFa7kTxYGZjlLi3e9uFe55/gDiREKw1o0anUU5cMAz42lXswNCw4V9AjJXAF5CJSiVJ2mFiJhDXpBZEV3Xj92kgAEo3TgCHdaQ0aZjRmIPmJemX1b&link3=&link4=&link5=&link6=&link7=&link8=&link9=&link10=&link11='
    # a = player()
    # for i,j in a.get_player_embeds(p):
    #     print(i, j)
