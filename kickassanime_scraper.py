import re
import json
import asyncio
from utilities.async_web import fetch
from utilities.helper.mavreckki import Mavereckki
from utilities.pace_scraper import scraper, COLOUR
from aiohttp import ClientSession, TCPConnector
from utilities.async_subprocess import async_subprocess, gather_limitter
import os
from aiodownloader import downloader, utils
from typing import List, Dict, Tuple, Union
from base64 import b64decode
from bs4 import BeautifulSoup as bs
from tabulate import tabulate
from __version__ import version as CURRENT_VERSION
from urllib.parse import urlparse, parse_qs
import enum

try:  # trying to apply uvloop
    import uvloop  # type: ignore
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    pass

with open("./Config/config.json") as file:
    data = json.loads(file.read())
    priority = data["priority"]
    debug = data["debug"]
    download_using = data["downloader"]
    max_subprocesses = data["max_subprocesses"]
    WEBSITE_DOMAIN = data["WEBSITE_DOMAIN"]
    check_updates: bool = data["check_updates"]

class CONFIGS(enum.Enum):
    config = 1
    to_update = 2
    watch_config = 3

def update_config(case: CONFIGS, config: dict):
    file_name = os.path.join('.', 'Config', case.name + '.json')

    with open(file_name, 'w') as config_to_change:
        print(file_name)
        json.dump(config, config_to_change, indent=4, ensure_ascii=False)
        print('done')

def format_float(num) -> str:
    return f"{num:04.1f}".rstrip("0").rstrip(".")


DOMAIN_REGEX = re.compile(r'\.(lol|rs|ro)', re.IGNORECASE)
GITHUB_REPOSITORY = 'https://github.com/KorigamiK/kickassanime-downloader'


class kickass:
    def __init__(
        self,
        session,
        url="https://www2.kickassanime.rs/anime/dummy",
        arbitrary_name=False,
        episode_link=None,
    ):
        url = DOMAIN_REGEX.sub(WEBSITE_DOMAIN, url)
        if url.endswith("/"):
            url = url[:-1]
        else:
            pass
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
        """returns urls of each episode in decreasing order"""
        soup = await fetch(self.base_url, self.session)
        results = [None]
        for i in soup.find_all("script"):
            if "appUrl" in str(i):
                data = await kickass._get_data(i)
                # print(data.keys())
                results = data["anime"]["episodes"]
                break

        if not results:
            print(COLOUR.warn(
                'This show has not yet been updated. Please try some time later.'))
            exit(1)

        try:
            self.last_episode = int(
                results[0]["slug"].split("/")[-1].split("-")[1])
        except ValueError:  # for ovas and stuff
            self.last_episode = 0

        return (DOMAIN_REGEX.sub(WEBSITE_DOMAIN, "https://www2.kickassanime.rs") + i["slug"] for i in results)

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
            # episode_num = int(self.episode_link.split("/")[-1].split("-")[1])
            episode_num = float(
                ".".join(
                    self.episode_link.split("/")[-1]
                    .replace("episode-", "")
                    .split("-")[:-1]
                )
            )
        except ValueError:  # for ovas and stuff
            episode_num = 0.0

        if debug:
            print(COLOUR.grey(f"Getting episode {format_float(episode_num)}"))

        soup = await fetch(self.episode_link, self.session)
        data: Dict[str, str] = None
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
                ret["ext_servers"] = {
                    i["name"]: i["link"] for i in data["ext_servers"] if i is not None
                }
            else:
                pass
        except:
            print(COLOUR.error(
                f"Ext server error. None available for {format_float(episode_num)}"))
        if ret["download"] != None:
            ret["download"] = await self.get_servers(ret["download"])
        else:
            ret["can_download"] = False
        ret["ep_num"] = episode_num

        try:
            if "countdown" in ret["player"][0]:
                ret["episode_countdown"] = True
            else:
                pass
        except IndexError:
            print(COLOUR.warn("No player links available"))

        return ret

    async def get_servers(self, dow_link):
        if dow_link != None:
            soup = await fetch(dow_link, self.session)
            return ((i.text, i["value"]) for i in soup.find_all("option"))
        else:
            return (None, None)

    async def get_episodes_embeds_range(self, start=0, end=None, episodes_tuple=None):
        if start == None:
            start = 0
        if episodes_tuple is None:
            gen = await self.scrape_episodes()
        else:
            gen = episodes_tuple
        if end == self.last_episode:
            end = None
        ed = end or self.last_episode
        x = 0
        if end != None:
            for _ in gen:
                if x != self.last_episode - ed - 1:
                    x += 1
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

    async def get_download(
        self, download_links: tuple, episode_number: float, no_stdout: bool = False
    ) -> tuple:
        """returns tuple like (link, file_name, headers)
        headers should only be checked if it is not None
        :download_links: are the available server links"""
        available = []
        file_name = f"{self.name} ep_{format_float(episode_number)}.mp4"
        tmp_serv = None
        for i in download_links:
            tmp_serv = i[0]
            if not (True or debug):  # always false I know it would print all available servers otherwise
                print(i[0])
            if i[0] in priority.keys():
                available.append(i)
        # print(available)
        if len(available) == 0:
            print(COLOUR.warn(
                f"No available server in config.json for {self.name} episode {format_float(episode_number)}"))
            print(COLOUR.warn(f"Try adding {tmp_serv} to the config file"))
            return (None, file_name, None)

        await asyncio.sleep(0)
        flag = 999
        final = None
        for i in available:
            if list(priority.keys()).index(i[0]) <= flag:
                flag = list(priority.keys()).index(i[0])
                final = i
        if (not no_stdout) or debug:
            print(final[0])  # server name
            print(final[1])  # server link
        a = scraper(self.base_url, session=self.session, get_method=fetch)
        a.quality = priority[final[0]]
        await a.get_final_links(final[1])
        # print(file_name)
        try:
            headers: dict = [i for i in a.options if type(i) == dict][0]
        except IndexError:
            headers = None

        if len(a.final_dow_urls) != 0:
            return (a.final_dow_urls[0].replace(" ", "%20"), file_name, headers)
        else:
            print(COLOUR.error(
                f"Cannot download {self.name} episode {format_float(episode_number)}"))
            return (None, file_name, headers)

    async def get_from_player(self, player_links: list, episode_number: float) -> str:
        a = player(self.session)
        print(COLOUR.info(
            f"Writing {self.name} episode {format_float(episode_number)}\n"))
        flag = False
        if len(player_links) > 1:
            print(COLOUR.info(
                f"Number of player links is {len(player_links)}"))
            flag = True
        else:
            pass

        with open("episodes.txt", "a+") as f:
            f.write(f"\n{self.name} episode {format_float(episode_number)}: \n")
            for i, j in await a.get_player_embeds(player_links[0]):
                # await a.get_from_server(j)
                f.write(f"\t{i}: {j}\n")
                if flag == True:
                    for k in player_links[1:]:
                        f.write(f"\t{k}\n")
                else:
                    pass
        return COLOUR.grey(f"No download links for {self.name} episode {format_float(episode_number)}. Written player links")


class player:
    latest_rss = 'https://www2.kickassanime.ro/feed/latest'
    max_table_length = 90

    def __init__(self, session: ClientSession):
        self.session = session

    @staticmethod
    async def _get_from_script(script):
        """ returns list[dict[name, scr]] """
        try:
            a = re.findall(r"\{.+\}", str(script))[0]
            return json.loads(f"[{a}]")
        except:
            print(COLOUR.error("Invalid player url supplied"))
            return None

    async def get_player_embed_links(self, player_link: str) -> list:
        """returns list[{"name": str, "src": str}] """
        if "axplayer/player" in player_link:  # happens for older anime
            return [
                {
                    "name": "Vidstreaming",
                    "src": (await self.get_ext_server(player_link, "Vidstreaming"))[0],
                }
            ]

        soup = await fetch(player_link, self.session)
        for i in soup.find_all("script"):
            if "var" in str(i):
                data = await player._get_from_script(i)
                if data:
                    return data
                else:
                    continue
        else:
            print(COLOUR.error("Player link error"))
            return None

    async def get_player_embeds(self, player_link: str) -> List[str]:
        """ returns list[("name", "link"), ...]"""

        result = await player.get_player_embed_links(self, player_link)
        if result is None:
            return [(None, None)]
        else:
            pass
        res = [self.get_from_server(i["name"], i["src"]) for i in result]
        return await asyncio.gather(*res)

    async def get_from_server(self, server_name, server_link):
        """ 
            returns [server_name, link, header] where
            link: str | {quality: link}
            header: None | {Referer: url, Subtitle?: list[url]}
        """

        header = None
        # from get_player_embed_links due to older anime. All the work has already been done
        if server_name == "Vidstreaming":
            header = {'Referer': 'https://goload.one'}
            return [server_name, server_link, header]

        elif server_name == "MAVERICKKI":
            return await Mavereckki(server_name, server_link, self.session)

        iframe_url = server_link.replace("player.php?", "pref.php?")
        soup = await fetch(iframe_url, self.session, {'referer': 'https://kaa-play.me/'})

        def get_script():
            for i in soup.find_all("script"):
                x = str(i)
                if "document.write" in x and len(x) > 783:
                    return b64decode(re.search(r'\.decode\("(.+)"\)', x).group(1))

        async def get_list(bs_soup):
            for i in bs_soup.find_all("script"):
                if "file" in str(i):
                    return json.loads(re.findall(r"\[{.*}]", str(i))[0].replace('\\', '\\\\').replace('"', '\"'))
            return list()

        if server_name == "PINK-BIRD":
            script_tag: str = get_script()
            try:
                return [server_name, bs(script_tag, "html.parser").find("source")["src"], header]
            except TypeError:
                print(COLOUR.error(f'Bad player link for {server_name}'))
                return [server_name, None, header]

        elif server_name == "SAPPHIRE-DUCK":
            script_tag: bytes = get_script()
            if not script_tag:
                print(COLOUR.error(f'Bad player link for {server_name}'))
                return [server_name, None, header]
            sap_duck = bs(script_tag, "html.parser")
            java_script = str(sap_duck.select_one("script"))

            return [
                server_name,
                re.search(r'(http.*)"',
                          java_script).group(1).replace(r"\/", r"/"),
                header
            ]

        elif server_name == "BETASERVER3" or server_name == "BETAPLAYER":
            res = ""
            links_list = await get_list(soup)
            # for i in links_list:
            #     res += "\t\t{i['label']}: {i['file']}\n"
            res = {i["label"]: i['file'].replace(' ', '%20').replace(
                '\\', '') for i in links_list if i["file"]}
            if res:
                return [server_name, res, header]
            else:
                return [server_name, None, header]

        elif server_name == "BETA-SERVER":
            script_tag = (
                str(get_script())
                .replace("file", r'"file"')
                .replace("label", r'"label"')
            )
            links_list = json.loads(
                re.search(r"\[\{.+\}\]", script_tag).group(0))
            res = {i["label"].strip(): i["file"].replace('\\', '')
                   for i in links_list}
            return [server_name, res, header]

        elif server_name == "DR.HOFFMANN":
            soup = await fetch(server_link, self.session)
            script_tag = str(get_script())
            res = re.search(r'"(http.+)",label', script_tag).group(1)
            return [server_name, res, header]

        elif server_name == "MAGENTA13":
            atob_regex = re.compile(r'(?<=atob\(").+(?=")')
            data_regex = re.compile(r'(?<=setup\().+(?=,)')
            validate_regex = re.compile('(?<!\\\\)\'')
            quote_keys_regex = r'([\{\s,])(\w+)(:)'

            def decode_atob(body: str):
                try:
                    found = atob_regex.search(body).group(0)
                    decoded = str(b64decode(found + '=' * (-len(body) % 4)))
                except:
                    return body

                return decode_atob(decoded)

            async with self.session.get(server_link.replace('player.php', 'pref.php')) as html:
                body = await html.text()
                first_data = decode_atob(body)  # fixes padding

            unvalidated_data = data_regex.search(
                decode_atob(first_data)).group(0) + '}'
            final_data = unvalidated_data.replace('\\', '')
            validated = validate_regex.sub('\"', final_data)
            # object is like {sources: [{file: string, type: 'hls'}], image: string}
            final_data = json.loads(
                re.sub(quote_keys_regex, r'\1"\2"\3', validated))
            if len(final_data['sources']) > 1:  # I haven't found this
                print(final_data)
            print(final_data)  # For test
            return [server_name, final_data['sources'][0]['file'], header]

        elif server_name == "THETA-ORIGINAL":
            decode_regex = r'(?<=decode\(").+(?="\))'
            sources_regex = re.compile(r'(?<=sources: )\[\{.*?\}\]')
            quote_keys_regex = r'([\{\s,])(\w+)(:)'

            async with self.session.get(server_link) as resp:
                html = await resp.text()

            decoded = str(b64decode(re.search(decode_regex, html).group(0)))
            sources = sources_regex.search(decoded).group(0)
            # this is of the format [{file: string, label: '1080p', type: 'mp4'}, ...]
            sources = json.loads(
                re.sub(quote_keys_regex, r'\1"\2"\3', sources))
            if len(sources) > 1:
                print(sources)  # Haven't seen this happen
            return [server_name, sources[0]['file'], header]

        else:
            # print(f"not implemented server {server_name}")
            return [server_name, iframe_url, header]

    async def _ext_gogo(self, url):
        page = await fetch(url, self.session)
        tag = str(page.find("div"))
        # the first (0) result can be .m3u8 or .mp4 but the second (1) is always .m3u8. Can be experimented on later
        return re.search(r"'(http.+)',label", tag).group(1)

    async def _vidstreaming(self, url):
        page = await fetch(url, self.session)
        # available servers are ['Multiquality Server', 'StreamSB', 'Doodstream', 'Server Hyrax', 'Mp4upload', 'YourUpload']
        servers = {i.text: i.get('data-video') for i in page.find_all(
            'li', {'class': 'linkserver'}) if i.get('data-video')}
        # download link can also be found.

        async def multiquality(key):
            try:
                page = await fetch(servers[key], self.session)
            except:
                raise Exception('Server multiquality not found.')
            tag = str(page.find('div', {'class': 'videocontent'}))
            # hls streaming url
            return re.search(r"(?<=file:\s')h.+?(?=',)", tag).group(0)

        async def streamsb(key):
            # page = await fetch(servers[key], self.session)
            url = servers[key]
            template = 'https://sbplay.org/play/{id}?auto=0&referer=&'
            _id = re.search(r'(?<=embed-).+(?=\.html)', url)
            if _id:
                player_link = template.format(id=_id.group(0))
                async with self.session.get(player_link) as resp:
                    page = await resp.text()
                    link = re.search(
                        r'''({file:\s?"|')(http.+)("|')}''', page).group(2)
                return link
            else:
                raise Exception('Not implemented') # this doesn't work for now
                async with self.session.get(url.replace('/e/', '/d/')) as resp:
                    soup = bs(await resp.text(), 'html.parser')
                    links = []
                    for tag in soup.find_all('a', {'href': '#', 'onclick': True}):
                        args = re.search(r'(?<=download_video\().+(?=\))', tag.attrs.get('onclick')).group(0)
                        code, mode, hashed = map(lambda x: x.replace("'", ''), args.split(','))
                dl_url = 'https://' + url.split('/')[2] +'/dl?op=download_orig&id='+code+'&mode='+mode+'&hash='+hashed
                async with self.session.post(dl_url) as resp:
                    soup = bs(await resp.text(), 'html.parser')

        parsers = {'StreamSB': streamsb, 'Multiquality Server': multiquality}
        available = list(parsers.keys())

        async def try_all(index=0):
            if index == len(available):
                COLOUR.error(
                    'Could not get stream. Try decreasing the priority of this server.')
                raise LookupError()
            print(f'Trying {available[index]}')
            try:
                return await parsers[available[index]](available[index])
            except Exception as e:
                print(e)
                return await try_all(index+1)

        try:
            return await try_all()
        except LookupError:
            if debug:
                print(servers)
                print(url)
            print(COLOUR.error("Didn't work try ext flag"))
        except:
            return None

    async def get_ext_server(self, ext_link, server_name) -> Tuple[str, Union[None, Dict[str, str]]]:
        '''Parses the kaa-play.me player urls'''
        params = parse_qs(urlparse(ext_link).query)
        url = params['data'][0]

        if not re.match(r'^https?:', url):
            url = 'https:' + url

        ret = None
        headers = None
        if server_name == "Vidcdn" or server_name == "Gogo server":
            ret = await self._ext_gogo(url)

        elif server_name == "Vidstreaming":
            # page = await fetch(url, self.session)
            # url = 'http:' + page.find('div', id="list-server-more").ul.find_all('li')[1]['data-video'] # more servers can be accounted for.
            url = url.replace("streaming.php?", "loadserver.php?")
            url = url.replace("embed.php", "loadserver.php")  # sometimes
            headers = {'Referer': 'https://goload.one'}
            ret = await self._vidstreaming(url)

        return ret, headers

    @staticmethod
    async def search(query: str, session: ClientSession = None, option: int = None) -> dict:
        """ returns dict[name, slug, image] """
        flag = False
        if session is None:
            session = await ClientSession().__aenter__()
            flag = True
        api_url = (DOMAIN_REGEX.sub(WEBSITE_DOMAIN,
                   "https://www2.kickassanime.rs/api/anime_search"))
        data = {"keyword": query}
        async with session.post(api_url, data=data) as resp:
            # print(await resp.text())
            resp_data = await resp.json(content_type=None)
        if flag:
            await session.close()  # for one time use
        if len(resp_data) != 0:
            if option is not None:
                return resp_data[option]
            else:
                for j, i in enumerate(resp_data):
                    print(COLOUR.blue(f"{j} {i['name']}"))
                option = int(input("Enter anime number: "))
                return resp_data[option]
        else:
            print(COLOUR.error(f"No anime avaiable for {query}"))
            return None

    @staticmethod
    async def fetch_latest(session: Union[ClientSession, None] = None) -> None:
        flag = False
        if session is None:
            session = await ClientSession().__aenter__()
            flag = True

        async with session.get(player.latest_rss) as resp:
            data = bs(await resp.text(), 'html.parser')

        if flag:
            await session.close()

        table = []
        headers = ['Title', 'Episode']

        for i in data.find_all('item'):
            name, episode = i.find('title').text.replace('English', '').replace(
                'Subbed', '').replace('Dubbed', 'Dub').split('Episode')
            episode = ' '.join([*filter(lambda x: x, episode.split(' '))])

            table.append(map(lambda x: '\n'.join((x[i: i + player.max_table_length].strip() for i in range(0, len(x), player.max_table_length))),
                             [COLOUR.blue(name), COLOUR.info(episode)]))

        print(tabulate(table, headers=headers, tablefmt='psql', showindex=True))


async def check_latest_version(session: Union[ClientSession, None] = None):
    flag = False
    if session is None:
        session = await ClientSession().__aenter__()
        flag = True

    VERSION_URL = 'https://raw.githubusercontent.com/KorigamiK/kickassanime-downloader/master/__version__.py'
    LATEST_VERSION_REGEX = re.compile(r'(?<=version = ).+')

    async with session.get(VERSION_URL) as resp:
        LATEST_VERSION: float = float(LATEST_VERSION_REGEX.search(await resp.text()).group(0))
    if flag:
        await session.close()

    if CURRENT_VERSION != LATEST_VERSION:
        print(COLOUR.info(
            f'New version {LATEST_VERSION} now available over current {CURRENT_VERSION} !'))
        print(COLOUR.info(f'Update your files now from {GITHUB_REPOSITORY}'))

        if os.path.isdir('./.git'):
            if input('\nWould you like to pull the latest changes using git? (y/n): ') == 'y':
                print(COLOUR.info('Running git pull...'))
                os.system('git pull')
                print(COLOUR.info(
                    'Please make sure to check the .eg.json files for new additions or changes, in case any breaking changes have been added.'))
        print()
    elif flag:
        print(COLOUR.info(
            f'You are on the latest Version {CURRENT_VERSION} !'))
    else:
        pass


async def automate_scraping(
    link,
    start_episode=None,
    end_episode=None,
    automatic_downloads=False,
    download_location=os.getcwd(),
    only_player=False,
    get_ext_servers=False,
    check_version=False,
):
    async with ClientSession(
        connector=TCPConnector(ssl=False), headers={"Connection": "keep-alive"}
    ) as sess:

        var = kickass(sess, link)
        print(COLOUR.info(var.name))
        tasks = []
        async for i in var.get_episodes_embeds_range(start_episode, end_episode):
            tasks.append(i)
        embed_result = await asyncio.gather(*tasks)

        def write_ext_servers(ext_dict, episode_number):
            with open("episodes.txt", "a+") as f:
                f.write(
                    f"\n{var.name} episode {format_float(episode_number)}:\n")
                for ext_name, ext_link in ext_dict.items():
                    f.write(f"\t\t{ext_name}: {ext_link}\n")

        download_tasks = []
        player_tasks = []

        for i in embed_result:
            if debug and not automatic_downloads:
                print(COLOUR.grey(
                    f"Starting episode {format_float(i['ep_num'])}"))
            if i["episode_countdown"] == True:
                print(COLOUR.info(
                    f'episode {format_float(i["ep_num"])} is still in countdown'))
                continue
            elif i["can_download"] and not only_player:
                download_tasks.append(
                    var.get_download(
                        i["download"], i["ep_num"], no_stdout=automatic_downloads
                    )
                )
            elif (i["ext_servers"] is not None) and get_ext_servers:
                write_ext_servers(i["ext_servers"], i["ep_num"])
                print(COLOUR.grey(
                    f"Written ext_servers for episode {format_float(i['ep_num'])}"))
            else:
                player_tasks.append(
                    var.get_from_player(i["player"], i["ep_num"]))

        links_and_names_and_headers = await asyncio.gather(*download_tasks)

        def dow_maker(url, name, headers=None):
            return downloader.DownloadJob(
                sess, url, name, download_location, headers=headers
            )

        def write_links(links_list):
            """for player links"""
            with open("episodes.txt", "a+") as f:
                for link, name, headers in links_list:
                    f.write("\n")
                    f.write(f"{name}: {link} \n")
                    if headers:
                        f.write(f"headers: {headers}\n")

        if len(player_tasks) != 0:
            to_play = await asyncio.gather(*player_tasks)
        else:
            to_play = [None]

        ans = "n"
        if automatic_downloads:
            ans = "y"
        else:
            if not only_player:
                ans = input("\ndownload now y/n?: ")

        async def use_aiodownloader():
            if len(links_and_names_and_headers) != 0 and [i[0] for i in links_and_names_and_headers] != [None]:
                print(COLOUR.purple_back(
                    f"Starting all downloads for {var.name}"))
                print(COLOUR.purple_back('Please Wait...'))
                # as last is the headers which can be None
                jobs = [
                    dow_maker(*i) for i in links_and_names_and_headers if None not in i[:-1]]
                tasks_3 = [asyncio.ensure_future(job.download(
                    return_exceptions=True)) for job in jobs]
                if len(jobs) != 0:
                    # will not get progress bars for automatic downloads to speed up the proceess or if multiple episodes are bing downloaded
                    if (not automatic_downloads) and len(jobs) == 1:
                        await utils.multi_progress_bar(jobs)
                    results = await asyncio.gather(*tasks_3, return_exceptions=True)
                    flag = False
                    for result in results:
                        if isinstance(result, Exception):
                            print(COLOUR.info(repr(result)))
                            flag = True

                    if flag and debug:
                        print(str(links_and_names_and_headers))

                else:
                    # to avoid too much stdout
                    if automatic_downloads == False:
                        # when countdown links may give none and non empty links_and_names_and_headers
                        print(COLOUR.info("Nothing to download"))

            else:
                # to avoid too much stdout
                if automatic_downloads == False:
                    print(COLOUR.info("No downloads found"))

        async def use_subprocess(l_n_h: tuple):
            def get_process(link, name, header) -> async_subprocess:
                head = f'-H "Referer: {header["Referer"]}" ' if header else ''
                optional_args = '-k --location '
                path = os.path.join(download_location, name)
                cmd = f'''curl -o "{path}" ''' + \
                    optional_args + head + f'"{link}"'
                if os.name == 'nt':
                    query = [r'C:\Windows\System32\cmd.exe']
                    return async_subprocess(*query, std_inputs=[cmd, 'exit'], print_stdin=False, print_stdout=False, description=name)
                else:
                    query = ["bash", "-c", cmd]
                    return async_subprocess(*query, description=name)

            tasks = [get_process(link, name, header)
                     for link, name, header in l_n_h if link]

            if len(tasks) == 0:
                print(COLOUR.info('Nothing to download'))
                return

            await gather_limitter(*tasks, max=max_subprocesses)

        if (check_version or check_updates):
            if not automatic_downloads:  # don't check if automatic downloads
                await check_latest_version(sess)

        if ans == "y" and not only_player:
            if download_using == 'aiodownloader':
                x = await use_aiodownloader()
                if x:
                    return x
            elif download_using == 'subprocess':
                await use_subprocess(links_and_names_and_headers)
            else:
                print(COLOUR.warn(
                    f'Config: downloader: {download_using} not supported.'))
        else:
            if not only_player:
                write_links(links_and_names_and_headers)

        for i in to_play:
            if not only_player and i:
                print(i)

        try:
            last_downloaded = [i[1]
                               for i in links_and_names_and_headers if i[0]][0]
            return (var.name, last_downloaded)
        except IndexError:
            # None when no server in config is available or there was no download link available for that episode
            return (var.name, None)

if __name__ == "__main__":
    link = "https://www2.kickassanime.rs/anime/edens-zero-279736"
    print(asyncio.run(
        automate_scraping(link, None, 1, only_player=False,
                          get_ext_servers=True, check_version=True),
    ))
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
