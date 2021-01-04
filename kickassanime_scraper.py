import re
import json
import asyncio
from async_web import fetch
from aiohttp import ClientSession
        
class kickass:
    def __init__(self, session, url = 'https://www2.kickassanime.rs/anime/dummy', arbitrary_name = False, episode_link=None):
        if 'episode' not in url.split('/')[-1]:
            self.base_url = url
        else:
            self.base_url = '/'.join(url.split('/')[:-1])
        if arbitrary_name:
            self.name = 'anything'
        else:
            self.name = ' '.join(self.base_url.split('/')[-1].split('-')[:-1])
        self.episode_link = episode_link
        self.session = session
        
    @staticmethod
    async def _get_data(script):
        result = re.findall(r'\{.+\}', str(script))
        a = result[0].replace(r' || {}','')
        return json.loads(a)
    
    async def scrape_episodes(self) -> GeneratorExit:
        soup = await fetch(self.base_url, self.session)
        for i in soup.find_all('script'): 
            if 'appUrl' in str(i):
                data = await kickass._get_data(i)
                # print(data.keys())
                results = data['anime']['episodes']
        self.last_episode = int(results[0]['slug'].split('/')[-1].split('-')[1])        
        return ('https://www2.kickassanime.rs'+i['slug'] for i in results)

    async def get_embeds(self, episode_link = None):        
        if episode_link == None:
            if self.episode_link == None:
                raise Exception('no url supplied')
            else:
                pass
        else:
            self.episode_link = episode_link       
        self.episode_num = int(self.episode_link.split('/')[-1].split('-')[1])
        print(f'Getting episode {self.episode_num}')        
        soup = await fetch(self.episode_link, self.session)
        for i in soup.find_all('script'): 
            if 'appUrl' in str(i):
                data = await kickass._get_data(i)
                break            
        # print(data['episode'])
        result = []
        for i in data['episode'].values():
            try:
                if 'http' in i:
                    result.append(i)
            except TypeError:
                pass            
        ret = {'player': None, 'download': None}
        for j, i in enumerate(result):
            ret[list(ret.keys())[j]] = i    
        return ret

class player(kickass):
    def __init__(self):
        pass
    @staticmethod
    def _get_from_script(script):
        a = re.findall(r'\{.+\}', str(script))[0]
        return json.loads(f'[{a}]')
        
    def get_player_embeds(self, player_link):
        import requests
        from bs4 import BeautifulSoup as bs
        request = requests.session()
        soup = bs(request.get(player_link).text, 'html.parser')
        for i in soup.find_all('script'):
            if 'var' in str(i):
                result = player._get_from_script(i)
                break
        return ((i['name'], i['src']) for i in result)

if __name__ == '__main__':
    async def main():
        link = 'https://www2.kickassanime.rs/anime/jujutsu-kaisen-dub-306353/episode-07-249138'
        async with ClientSession() as sess:
            var = kickass(sess, link)
            print(var.name, var.base_url)
            res = await var.scrape_episodes()
            tasks = []
            for _ in range(2):
                eplink = res.__next__()
                tasks.append(var.get_embeds(eplink))
            print(var.last_episode)
            return await asyncio.gather(*tasks)
        
    # print(asyncio.run(main()))
    p = 'https://kaa-play.com/dust/player.php?link=lMPAFDFNWf9Bx5XWn@LhO@YLW@9Yf5A0V71PhAAfaBs9nxid3Y3vlRNEHYJM514CxhjcXIctd57Gga8t2KOdvFrlI3CLvcnxeLgWUrDQ7agyuqHLJPizr8q99qN9j@VOFa7kTxYGZjlLi3e9uFe55/gDiREKw1o0anUU5cMAz42lXswNCw4V9AjJXAF5CJSiVJ2mFiJhDXpBZEV3Xj92kgAEo3TgCHdaQ0aZjRmIPmJemX1b&link2=lMPAFDFNWf9Bx5XWn@LhO@YLW@9Yf5A0V71PhAAfaBs9nxid3Y3vlRNEHYJM514CxhjcXIctd57Gga8t2KOdvFrlI3CLvcnxeLgWUrDQ7agyuqHLJPizr8q99qN9j@VOFa7kTxYGZjlLi3e9uFe55/gDiREKw1o0anUU5cMAz42lXswNCw4V9AjJXAF5CJSiVJ2mFiJhDXpBZEV3Xj92kgAEo3TgCHdaQ0aZjRmIPmJemX1b&link3=&link4=&link5=&link6=&link7=&link8=&link9=&link10=&link11='
    a = player()
    for i,j in a.get_player_embeds(p):
        print(i, j)