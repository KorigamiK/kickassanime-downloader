# Kickassanime Downloader
A nice nd fast asynchronous anime downloader, streamer and more for kickassanime. 

[Here's a demo](#some-usage-examples) of this tool.

## Installation :

The setup is a little tedious at the moment but I might make a nice installable package using pip. But right now these are the installation steps:

1. Install [python 3](https://www.python.org/) with python and pip on path.

2. Clone this repository using `git clone https://github.com/KorigamiK/kickassanime-downloader` or download and extract this repository to a directory. For example: `~/Documents/kickassanime-downloader` .

3. Open terminal/command prompt and navigate to the directory using: `cd /home/origami/Documents/kickassanime-downloader` .

4. Run `pip install -r requirements.txt`

5. `[Optional]` if you are on Linux also run `pip install SelectMenu` to get the nice looking command line menu.

6. Navigate to your download directory and navigate to the `Config` folder (`~/Documents/kickassanime-downloader/Config` for example). 

7. Rename all the `.eg.json` and remove the `.eg` from the file name. Open each one of them and adjust the configurations as you want.


8. Setup the command line aliases [from the wiki](#to-set-up-the-command-alias) or run the command line interface directly by running `python cli.py` .

9. You may need to download tools like [mpv](https://mpv.io/) or [vlc](https://www.videolan.org/) and add them to your path to stream the shows. [This website](https://www.vlchelp.com/add-vlc-command-prompt-windows/) shows how to add VLC to path on Windows.

10. Now profit.

## To set up the command alias:
1. [For windows](https://github.com/KorigamiK/kickassanime-downloader/wiki/Command-alias-Windows)

2. [For Linux/Mac](https://github.com/KorigamiK/kickassanime-downloader/wiki/Command-alias-Linux-Mac)

## Usage :

1. Run the alias with no commands/arguments or just `python cli.py` to get the menu of all the actions you have.

2. Run the alias with commands to stream any anime that you want. `kaa --help` or `python cli.py --help` for list of all the commands.

3. Here's the out of the above command: 
```
$ kaa -h 

usage: play.py [-h] [--list] [--ep EP] [--url URL] [--opt OPT] [--ext]
               [--stop] [--encode] [--custom_server [CUSTOM_SERVER]]
               [name [name ...]]

play anime directly

positional arguments:
  name                  Name of the anime to search

optional arguments:
  -h, --help            show this help message and exit
  --list, -L            Optional switch to list available player servers (not
                        ext) with their index
  --ep EP, -e EP        Episode number. Default is the latest episode.
  --url URL, -u URL     Optional kickass anime url
  --opt OPT, -o OPT     Optional way to select search result number.
  --ext                 Optional switch to play only from ext servers (its
                        faster if it works). Needs no arguments
  --stop, -s            Optional switch to stop the script after searching
                        without playing anything. Will also display the url of
                        the anime.
  --encode              Optional switch to print ffmpeg command to encode the
                        stream
  --custom_server [CUSTOM_SERVER], -c [CUSTOM_SERVER]
                        Name of the player/server you want or the INDEX number
                        in the watch_config priority dictionary. Overrides the
                        current priority.
```

## FAQ :

If you have any questions about errors or installation you can check the [issues page](https://github.com/KorigamiK/kickassanime-downloader/issues) and read the [already closed issues](https://github.com/KorigamiK/kickassanime-downloader/issues?q=is%3Aissue+is%3Aclosed). I have answered most of the problems that you might be facing.

```
You are welcome to make an issue for any bug or error or feature that you might need.
```

#### ```If you encounter any problems due to repeated requests and cloudflare protection, wait for some time and then run the script again.```


## Some usage examples:

1. Auto update your ongoing series for new episodes
![autoupdate](/example/autoupdate.gif)

2. Play any episode of any show
![play episode](/example/play_ep.gif)

3. Dowload a range of episodes of any show
![search and download](/example/search_and_download.gif)

Make sure to correctly create the config files or remove the `.eg` from the file names in the `config` folder.