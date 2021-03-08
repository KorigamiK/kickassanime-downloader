from utilities.watcher import watch
import asyncio
import argparse

parser = argparse.ArgumentParser(description="play anime directly")

# Required positional argument
# parser.add_argument('posarg', type=int,
#                     help='A required integer positional argument')

# Optional positional argument
parser.add_argument("name", type=str, nargs="*", help="Name of the anime to search")

# Optional argument
parser.add_argument("--ep", "-e", type=int, help="Episode number. Default is the latest episode.")

parser.add_argument("--url", "-u", type=str, help="Optional kickass anime url")

parser.add_argument(
    "--opt",
    "-o",
    type=int,
    help="Optional way to select search result number.",
)

parser.add_argument(
    "--ext",
    action="store_true",
    help="Optional switch to play only from ext servers (its faster if it works). Needs no arguments",
)

args = parser.parse_args()
episode = args.ep
link = args.url
query = " ".join(args.name) if args.name else None
opt = args.opt
ext_only = args.ext

asyncio.get_event_loop().run_until_complete(
    watch(episode, link=link, query=query, option_number=opt, ext_only=ext_only)
)
