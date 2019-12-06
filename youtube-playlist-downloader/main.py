import os
import requests
import animation
import re
import numpy as np
import sys
import subprocess
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup
from pytube import YouTube
from colorama import init, Fore

def load_config():
    with open('config.json') as json_config_file:
        config = json.load(json_config_file)
        global youtube_playlist_url
        global mp3_download_location 
        global downloaded_history_file_location 
        global top_n 
        youtube_playlist_url = config["youtube_playlist_url"]
        mp3_download_location = r"" + config["mp3_download_location"]
        downloaded_history_file_location = r"" + config["downloaded_history_file_location"]
        top_n = config["top_n"]

def get_valid_filename(s):
    s = re.sub(r'[\(\[].*?[\)\]]', '', s).strip() # removes brackets and its contents (e.g. text [official] => text)
    return re.sub(r'[\\/:"*?<>&\'|]+', '', s) # removes all invalid characters in filename

def on_progress(stream, chunk, file_handle, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining 
    percentage_of_completion = bytes_downloaded / total_size * 100
    done = int(50 * bytes_downloaded / total_size)
    sys.stdout.write('\r{0}[{1}{2}{3}{4}] {5}% | {6}/{7} MB'.format(Fore.LIGHTWHITE_EX, Fore.LIGHTGREEN_EX, '█' * done, '.' * (50-done), Fore.LIGHTWHITE_EX, round(percentage_of_completion), round(bytes_downloaded * 0.000001, 2), round(total_size * 0.000001, 2)))
    sys.stdout.flush()

def main():
    downloaded_count = 0
    unique_list = []
    init(autoreset=True) # initialize the colours printed in terminal
    load_config()

    # create \tmp directory in the project folder if it does not exist
    temp_download_location = os.path.abspath(os.curdir) + r"\tmp"
    if not os.path.exists(temp_download_location):
        os.makedirs(temp_download_location)

    wait = animation.Wait()
    wait.text = "{0}[{1}] Retrieving all the video links from the youtube playlist. Please wait ".format(Fore.LIGHTWHITE_EX, datetime.now())
    wait.start()
    r = requests.get(youtube_playlist_url) # Get the play list from youtube
    soup = BeautifulSoup(r.text, "lxml")

    tgt_list = [a['href'] for a in soup.find_all('a', href=True) if re.search('watch', a['href'])]

    for n in tgt_list:
        if "v=" in n and "list=" in n and "index=" in n:
            index = int([indx.replace("index=","") for indx in n.split("&") if "index=" in indx][0])
            if index >= 1 and index <= top_n: # top n songs
                if n not in unique_list:
                    unique_list.append('https://www.youtube.com' + n)
 
    wait.stop()
    print(" ")

    ## database to keep track of downloaded songs
    if os.path.isfile(downloaded_history_file_location):
        downloaded_music = np.load(downloaded_history_file_location, allow_pickle=True).item()
    else:
        downloaded_music = {}
    
    total_count = len(unique_list)

    for link in unique_list:
        try:
            id = link[link.find("=") + 1:link.find("&")]
            if id in downloaded_music:
                print("{0}[{1}] {2} has already been downloaded.".format(Fore.LIGHTWHITE_EX, datetime.now(), downloaded_music[id]))
                downloaded_count += 1
            else:
                y = YouTube(link, on_progress_callback=on_progress)
                id = y.video_id
                file_name_mp3 = "{0}.mp3".format(get_valid_filename(y.title)) 

                downloaded_music[id] = file_name_mp3
                print("{0}[{1}] Downloading {2} ...".format(Fore.LIGHTWHITE_EX, datetime.now(), file_name_mp3))
           
                t = y.streams.filter(only_audio=True).first()
                t.download(output_path=temp_download_location)

                print(" ")
                default_filename = t.default_filename
                subprocess.run(['ffmpeg','-n','-i', os.path.join(temp_download_location, default_filename), os.path.join(mp3_download_location, file_name_mp3)])
                print("{0}[{1}] Downloading {2} completed.".format(Fore.LIGHTGREEN_EX, datetime.now(), file_name_mp3))
                np.save(downloaded_history_file_location, downloaded_music)
                downloaded_count += 1
             
                # delete mp4 file from tmp folder
                os.unlink(os.path.join(temp_download_location, default_filename))     
        
            print("{0}[{1}] {2}/{3} downloaded.".format(Fore.LIGHTWHITE_EX, datetime.now(), downloaded_count, total_count))
        except Exception as ex:
            print("{0}[{1}] Exception: {2}".format(Fore.LIGHTRED_EX, datetime.now(), str(ex)))
            continue
        np.save(downloaded_history_file_location, downloaded_music)

if __name__ == "__main__":
    main()

