from utilities.watcher import watch
import asyncio
import argparse

parser = argparse.ArgumentParser(description='play anime directly')

# Required positional argument
# parser.add_argument('posarg', type=int,
#                     help='A required integer positional argument')

# Optional positional argument
parser.add_argument('name', type=str, nargs='*',
                    help='name of the anime to search')

# Optional argument
parser.add_argument('--ep', type=int,
                    help='episode number')

parser.add_argument('--url', type=str,
                    help='optional kickass anime url')

parser.add_argument('--opt', type=int,
                    help='optional select anime number')
                
parser.add_argument('--ext', type=int, nargs='*',
                    help='optional flag to play from only ext servers (faster is works). Needs no arguments')
# Switch
# parser.add_argument('--switch', action='store_true',
#                     help='A boolean switch')

args = parser.parse_args()
episode = args.ep
link = args.url
query = ' '.join(args.name) if args.name else None
opt = args.opt
ext_only = True if args.ext is not None else False

asyncio.get_event_loop().run_until_complete(watch(episode, link=link, query=query, option_number=opt, ext_only=ext_only))