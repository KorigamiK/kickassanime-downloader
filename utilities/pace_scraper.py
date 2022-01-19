from typing import List
import requests
from bs4 import BeautifulSoup as bs
import base64
import subprocess
import re
import csv
import asyncio

# import os # will add ability to set download location
from tabulate import tabulate


class COLOUR():
    _end = '\033[0m'
    def _background(code):
        return "\33[{code}m".format(code=code)
  
    def _style_text(code):
        return "\33[{code}m".format(code=code)
  
    def _color_text(code):
        return "\33[{code}m".format(code=code)
        
    @staticmethod
    def blue(text: str):
        return COLOUR._color_text(94) + (text or 'None') + COLOUR._end
    @staticmethod
    def error(text: str):
        return COLOUR._color_text(41) + text + COLOUR._end

    @staticmethod
    def grey(text):
        return COLOUR._color_text(2) + text + COLOUR._end

    @staticmethod
    def purple_back(text):
        return COLOUR._color_text(45) + COLOUR._color_text(1) + text + COLOUR._end

    @staticmethod
    def warn(text):
        return COLOUR._color_text(103) + COLOUR._color_text(34) + text + COLOUR._end

    @staticmethod
    def info(text: str):
        return COLOUR._color_text(95) + (text or 'None') + COLOUR._end

class scraper:
    def __init__(self, url, session=None, get_method=None):
        self.orig_url = url
        self.host = url.split("/")[2]
        self.anime = url.split("/")[-2]
        self.final_dow_urls = []  # new downloads will be appended to this i.e. url(s)
        self.options = []  # carries the options to download final_dow_urls
        self.name = (
            url.split("/")[url.split("/").index("anime") + 1]
            .replace("-", " ")
            .capitalize()
        )
        self.session = session
        self.get_method:bs = get_method

    @property
    def episode(self):
        return self.orig_url.split("/")[-1]

    def animepace_get_servers(self):
        data = {
            "email": "bnb35317@cuoly.com",
            "password": "origami",
            "submit": "login",
        }
        with requests.session() as client:
            client.post("https://www3.animepace.si/user/login", data=data)
            response = client.get(self.orig_url).text
            soup = bs(response, "html.parser")
            servers = soup.find_all("iframe")[-1][
                "src"
            ]  # gets the iframe of downloadlinks after login
        return servers

    def get_animopace(self, x):
        soup = bs(requests.get(x).content, "html.parser")
        option_list = []  # link to all servers
        flag = True

        servers = [["ser num", "server"]]
        for j, i in enumerate(soup.find_all("option")):
            try:
                self.server_opt
                flag = False
            except:
                servers.append([j, i.text])
            option_list += [i["value"]]

        if len(option_list) == 0:
            print("No downloads availible")
            return None

        if flag == True:
            print(tabulate(servers, headers="firstrow"))
            opt = int(input("Enter server number: "))
            setattr(self, "server_opt", opt)

        if self.server_opt == "downloader":
            return option_list
        else:
            return option_list[self.server_opt]

    # sample SERVER url returned is like https://haloani.ru/Theta-Original-v4/d.php?q=f7ynJF1F1beE-b0beC4UUk_2j3EeFojNSJD90rofQIg
    def get_server_link(self):
        r = scraper.get_animopace(self, scraper.animepace_get_servers(self))
        if r:
            return r
        else:
            print(f"{self.episode} not available. It will be skipped")
            return [None]  # because we iterate through it

    def _kickassanimex(self, link):
        html = requests.get(link).text
        soup = bs(html, "html.parser")
        script = soup.select("script")
        for i in script:
            if "document.write" in str(i):
                try:
                    script = (
                        str(i)
                        .replace("atob", "Base64.decode")
                        .split('javascript">')[1]
                        .split("</script>")[0]
                        .split('document.write(Base64.decode("')[1]
                        .split('"));')[0]
                    )
                    break
                except Exception as e:
                    print("Something went wrong with the server", e)
                    return None
        data = base64.b64decode(script)
        soup = bs(data.decode("utf-8"), "html.parser")

        flag = True
        dow_urls_allqualities = []
        for j, i in enumerate(soup.find_all("a")):
            try:
                self.quality
                flag = False
            except:
                print(j, i.text)
            dow_urls_allqualities += [str("".join(i["href"]))]
        if flag == True:
            setattr(self, "quality", int(input("Enter quality number: ")))
        if dow_urls_allqualities[self.quality] == "https://kaa-play.com/redirector.php?link=": # this is a dead link
            return None

        self.final_dow_urls += [dow_urls_allqualities[self.quality]]
        self.options += [
            '--header="Referer: https://haloani.ru"'
            + " -O "
            + (self.name + " " + self.episode + ".mp4").replace(" ", "_")
        ]

    def _kickassanimev2(self, link):
        html = requests.get(link).text
        soup = bs(html, "html.parser")
        script = soup.find("div", class_="text-center").select("script")[0]
        script = str(
            str(script).split('document.write(atob("')[1].split('"))</script>')[0]
        )
        script += "=" * ((4 - len(script) % 4) % 4)  # ugh from stack exchange
        data = base64.b64decode(script)
        soup = bs(data.decode("utf-8"), "html.parser")
        flag = True
        dow_urls_allqualities = []
        available_qualities = []
        for j, i in enumerate(soup.select("a")):
            try:
                self.quality
                flag = False
            except:
                print(j, i.text)
            dow_urls_allqualities += ["/".join(link.split('/')[:-1]) + "/" + i["href"]]
            available_qualities.append(i.text.strip())

        if flag == True:
            setattr(self, "quality", int(input("Enter quality number: ")))
        try:
            self.final_dow_urls += [dow_urls_allqualities[self.quality]]
        except IndexError:
            print(COLOUR.warn(f'Index {self.quality} not found in {", ".join(available_qualities)}'))
            print(COLOUR.warn(f'Defaulting to {available_qualities[-1]}'))
            self.final_dow_urls.append(dow_urls_allqualities[-1])

        self.options += [
            "-O " + (self.name + " " + self.episode + ".mp4").replace(" ", "_")
        ]

    def _betaserver(self, link):
        html = requests.get(link).text
        soup = bs(html, "html.parser")
        dow_urls_allqualities = []
        flag = True
        data = soup.find_all("a", rel="nofollow")
        if len(data) == 0:
            return None
        else:
            pass
        for j, i in enumerate(data):
            try:
                assert self.quality
                flag = False
            except:
                print(j, i.text)
            dow_urls_allqualities += [i["href"]]

        if flag == True:
            setattr(self, "quality", int(input("Enter quality number: ")))
        self.final_dow_urls += [dow_urls_allqualities[self.quality]]
        self.options += [
            '--header="Referer: https://haloani.ru"'
            + " -O "
            + (self.name + " " + self.episode + ".mp4").replace(" ", "_")
        ]

    def _html5(self, link):
        soup = bs(requests.get(link).text, "html.parser")
        links = []
        for i in soup.find_all("a"):
            links.append((i.text, i["href"]))
        try:
            assert self.quality
        except Exception:
            for j, i in enumerate(links):
                print(j, i[0])
            self.quality = int(input("Enter quality number: "))
        try:
            self.final_dow_urls += [links[self.quality][1]]
        except IndexError:
            return None
        self.options += [
            f"-O {(self.name + ' ' + self.episode + '.mp4').replace(' ', '_')}"
        ]
    
    async def _magenta(self, link):
        # return scraper._kickassanimex(self, link) # still works
        if not self.session: 
            soup = bs(requests.get(link).text, "html.parser")
        else:
            soup = await self.get_method(link, self.session)
        script = [i for i in soup.select('script[type="text/javascript"]') if 'document.write' in str(i)][0]
        res = base64.b64decode(re.search(r'decode\("(.+)"\)', str(script)).group(1))
        html = bs(res, 'html.parser')
        link_and_quality = [(i['href'], i.text) for i in html.find_all('a')]
        if not link_and_quality:
            print(COLOUR.error('No download links available for this episode. Try changing the priority of this server down in config.json and try again.'))
            return None
        flag = True
        for index, data in enumerate(link_and_quality):
            try:
                self.quality
                flag = False
                break
            except:
                print(index, data[1])

        if flag == True:
            setattr(self, "quality", int(input("Enter quality number: ")))

        self.final_dow_urls += [link_and_quality[self.quality][0]]
        self.options += [
            '--header="Referer: https://kaa-play.com"'
            + " -O "
            + (self.name + " " + self.episode + ".mp4").replace(" ", "_")
        ]

        return True

    async def get_final_links(self, link):  # link here is for server
        # print(link) # use for debugging
        try:
            # print("Its the new server kaa-play")
            # server = link.split("https://kaa-play.com")[1].split("/")[1]
            server = re.search(r'((\.me)|(\.com)|(\.ru)|(\.xyz))\/(.*?)\/', link).group(6)
        except AttributeError:
            print(f"Bad serverlink {link}. It does not follow known pattern, please make an issue on github.")
            return

        self.server = server
        if server == "KickAssAnimeX":
            await scraper._magenta(self, link)
            self.options = [{'Referer': 'https://betaplayer.life/api/embed/1615556106095'}]

        elif server == "Kickassanimev2":
            scraper._kickassanimev2(self, link)

        elif server == "Theta-Original-v4":
            scraper._kickassanimex(self, link)
            self.options[-1] = "-O " + (
                self.name + " " + self.episode + ".mp4"
            ).replace(" ", "_")

        elif server == "Dr.Hoffmann":
            scraper._kickassanimex(self, link)
            self.options[-1] = "-O " + (
                self.name + " " + self.episode + ".mp4"
            ).replace(" ", "_")

        elif server == "Original-quality-v2":
            scraper._kickassanimev2(self, link)

        elif server == "BetaServer3":
            scraper._betaserver(self, link)

        elif server == "Beta-Server":
            scraper._kickassanimex(self, link)
        # betaserver1 doesn't work (no links)
        elif server == "mobile-v2":
            scraper._betaserver(self, link)

        elif server == "Theta-Original":
            scraper._kickassanimex(self, link)

        elif server == "kickassanime1":
            print("mightnot work")
            scraper._kickassanimex(self, link)

        elif server == "a-kickassanime":
            scraper._kickassanimex(self, link)

        elif server == "html5":
            scraper._html5(self, link)

        elif server == "Magenta02":
            await scraper._magenta(self, link)

        elif server == "Magenta13":
            await scraper._magenta(self, link)

        else:
            print("Not supported")
            print(self.server, link)
            return None

    @staticmethod
    def download(link, options):
        #         query = f"""wget "{link}" -q --show-progress --no-check-certificate {options}"""
        query = f"""wget "{link}" --no-check-certificate {options}"""
        subprocess.run(query, shell=True)


class downloader:
    def __init__(self, url, start, end, opt="low"):
        self.mode = opt
        self.anime_url = url
        self.start = start
        self.end = end

    @property
    def fetch_episodes(self):
        for i in range(self.start, self.end + 1):
            if len(str(i)) <= 2:
                yield f"{self.anime_url}episode-{i:0>2d}"
            else:
                yield f"{self.anime_url}episode-{i}"

    priority = {
        "low": {
            "Kickassanimev2": 1,
            "KickAssAnimeX": -2,
            "Beta-Server": 1,
            "BetaServer3": 2,
            "mobile-v2": -1,
            "html5": -1,
            "a-kickassanime": -1,
            "Theta-Original": -1,
        }
    }

    async def make_downloads(self):
        priority_list = list(downloader.priority[self.mode].keys())
        var = scraper(self.anime_url + "episode-04")
        var.server_opt = "downloader"
        f = self.start
        for i in self.fetch_episodes:
            toggle_no_new_episodes = False
            episode_error = False
            print(f"Fetching {f}")
            f += 1
            var.orig_url = i
            try:
                serverlinks = (
                    var.get_server_link()
                )  # only for "downloader" class it gives the whole list of servers
            except:
                print("Episode error")
                serverlinks = [None]
                episode_error = True
            pattern = r"(https:\/\/haloani.ru\/)([A-Za-z-1-9.]+)(\/[^=]+)"
            servers = []
            pattern2 = r"(https:\/\/kaa-play.com\/)([A-Za-z-1-9.]+)(\/[^=]+)"
            for k in serverlinks:
                if k:
                    try:
                        servers += [re.search(pattern, k).group(2)]
                    except:
                        try:
                            servers += [re.search(pattern2, k).group(2)]
                        except:
                            print(f"bad serverlink {k}")
                            serverlinks.remove(k)
                            continue
                else:
                    print("skipping")
                    toggle_no_new_episodes = True
                    break
            if toggle_no_new_episodes or episode_error:
                break
            else:
                pass
            flag = 10  # arbitrary large number
            needed_server: str = None
            for j, i in enumerate(servers):
                if i in priority_list:
                    print("yes")
                    if priority_list.index(i) < flag:
                        flag = priority_list.index(i)
                        needed_server = serverlinks[j]
                        var.quality = downloader.priority[self.mode][i]
                    else:
                        pass
                else:
                    print("no")
            try:
                try:
                    print(re.search(pattern, needed_server).group(2))
                except:
                    print(re.search(pattern2, needed_server).group(2))

                await var.get_final_links(needed_server)
            except Exception as e:
                try:
                    print(COLOUR.warn(f"Server/ quality not found, trying any available quality, with error {e}"))
                    print()
                    var.quality = -1
                    await var.get_final_links(needed_server)
                    continue
                except:
                    print(COLOUR.warn("Found bad server. trying another one..."))
                    var.quality = -1
                    serverlinks.remove(needed_server)
                    await var.get_final_links(serverlinks[-1])
                    continue
            print()
        downloader.csv_updater(var.final_dow_urls, var.options)
        if input("download now? y/n: ") == "y":
            for url, opt in zip(var.final_dow_urls, var.options):
                scraper.download(url, opt)

    @staticmethod
    def csv_updater(dow_links, dow_opts):
        with open("all_links.txt", "a") as file:
            write = csv.writer(file)
            write.writerows(list(zip(dow_links, dow_opts)))


class searcher:
    def __init__(self, search_input):
        self.query = search_input

    def _call_api(self):
        response = requests.post(
            "https://www3.animepace.si/search", data={"keyword": self.query}
        )
        return response.json()

    def print_search(self):  # also returns url
        links = []
        for j, i in enumerate(search_and_get._call_api()):
            print(COLOUR.blue(j, i["name"]))
            links.append(i["slug"])
        inp = int(input("Enter anime number: "))
        self.url = f"https://www3.animepace.si/anime/{links[inp]}/"
        return self.url

    async def download_from_search(self):
        var = downloader(
            self.print_search(),
            int(input("Enter start number: ")),
            int(input("Enter end number: ")),
        )
        await downloader.make_downloads(var)


if __name__ == "__main__":
    x = {1: "use code", 2: "use url and download", 3: "search and download"}
    for i, j in x.items():
        print(i, j)
    option_input = int(input("Enter option number: "))
    if option_input == 1:
        if input("Search? y/n : ") == "y":
            search_and_get = searcher(input("Enter anime name: "))
            a = scraper(search_and_get.print_search())
            dummy_url = search_and_get.url
        else:
            dummy_url = input("Enter url: ")[:-10]
            a = scraper(dummy_url)
        print(a.name)
        if a.host == "www3.animepace.si":
            for i in range(
                int(input("Enter starting: ")), int(input("Enter ending: ")) + 1
            ):
                a.orig_url = f"{dummy_url}episode-{i:02d}"
                print(a.orig_url)
                serverlink = a.get_server_link()
                #             print(serverlink)
                asyncio.run(a.get_final_links(serverlink))
        #     print(list(zip(a.final_dow_urls, a.options)))
        #     print(a.options)
        #     print(a.final_dow_urls)
        downloader.csv_updater(a.final_dow_urls, a.options)
        if input("download now y/n? :") == "y":
            for url, opt in zip(a.final_dow_urls, a.options):
                scraper.download(url, opt)
        else:
            pass
    elif option_input == 2:
        a = downloader(
            input("Enter anime url: "),
            int(input("Enter start number: ")),
            int(input("Enter end number: ")),
        )
        asyncio.run(downloader.make_downloads(a))
    elif option_input == 3:
        search_and_get = searcher(input("Enter anime name: "))
        asyncio.run(search_and_get.download_from_search())
    else:
        print("not implemented yet.")
