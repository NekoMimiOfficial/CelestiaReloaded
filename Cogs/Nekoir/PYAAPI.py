import sys
import requests
import subprocess

HELP_MSG= """\
Nekoir Py Adaptor API
~~~~~~~~~~~~~~~~~~~~~
--help              shows this help message
--api=              sets the api endpoint
--play=             plays the first suggestion for a term
--dl=               downloads a specific song ID
--lyrics=           gets lyrics for a specific song ID
--get-id=           get the song ID for the first result of the search term

Examples
~~~~~~~~
python3 PYAAPI.py --api=http://server.com/api/ --play="yoasobi watch me"

version: 1.0.0
author: NekoMimiOfficial (https://nekomimi.tilde.team)"""

def download_file(url, save_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes

        print(f"Download file: {save_path}")
        print(f"Download URL/source: {url}")
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"File downloaded successfully to {save_path}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")

def fix_hyphen(string: str):
    return string # looks like python aleady does this internally, silly me :3

def api_check(api: str):
    if api== "":
        print("Please provide an API endpoint: --api=http://some.api/api/")
        exit()
    elif not api.endswith("/"):
        return api+"/"
    else:
        return api

def sid_check(sid):
    if sid== "":
        print("Please provide a song id after the action: --dl=1897392 or --lyrics=2398717")
        exit()
    else:
        try:
            int(sid)
        except:
            print("Song ID must be a numerical value")
            exit()

def term_check(term: str):
    if term== "":
        print("Please provide a term to query or play: --play=\"some song term\" or --query=\"song to query\"")
        exit()

class SearchType:
    ALBUM= "albums"
    TRACK= "tracks"

class Resolution:
    HIRES= "HIRES_LOSSLESS"
    NORMAL= "LOSSLESS"

class ApiService:
    def __init__(self, base_url: str):
        self.base_url= base_url
        self.headers= {'User-Agent': 'ktor-client', 'X-App-Version': '39.0'}

    def search(self, term: str, search_type: str):
        req= requests.get(url= self.base_url+ "search", params= {'query': term, 'type': search_type}, headers= self.headers)
        return req.json()

    def track(self, track_id: str, track_quality: str):
        req= requests.get(url= self.base_url+ "track/playback", params= {'id': track_id, 'quality': track_quality}, headers= self.headers)
        return req.json()

    def metadata(self, track_id: str):
        req= requests.get(url= self.base_url+ "track/metadata", params= {'id': track_id}, headers= self.headers)
        return req.json()

    def album(self, album_id: str):
        req= requests.get(url= self.base_url+ "album/tracks", params= {'id': album_id}, headers= self.headers)
        return req.json()

    def lyrics(self, track_id: str):
        req= self.metadata(track_id)
        try:
            return req["LYRICS"]
        except:
            return False

class Wrapper:
    def __init__(self, base_url: str):
        self.service= ApiService(base_url)

    def link_play(self, search: str, resolution= Resolution.NORMAL):
        try:
            if resolution in (Resolution.HIRES, Resolution.NORMAL):
                search_res= self.service.search(search, SearchType.TRACK)
                return self.service.track(search_res[0]["id"], resolution)["urls"][0]
        except:
            return False

    def mpv_play(self, search: str, resolution= Resolution.NORMAL):
        get= self.link_play(search, resolution)
        if get:
            subprocess.getoutput(f"mpv {get}")

    def lyrics(self, request):
        try:
            return request["LYRICS"]
        except:
            return False

    def download(self, track_id: str, resolution= Resolution.NORMAL):
        try:
            if not resolution in (Resolution.HIRES, Resolution.NORMAL):
                return False
            data= self.service.track(track_id, resolution)
            meta= self.service.metadata(track_id)
            download_file(data["urls"][0], f"[{meta['TRACKNUMBER']}] {meta['ARTIST']} - {meta['TITLE']} ({meta['YEAR']}).{data['codec']}")
        except Exception as e:
            print("Error:", end= " ")
            print(e)

def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print(HELP_MSG)
        exit()

    api= ""
    sid= ""
    term= ""
    dl= False
    play= False
    query= False
    lyrics= False
    api_debug= False

    for arg in sys.argv:
        if arg.startswith("--api="):
            api= fix_hyphen(arg.split("=", 1)[1])

        if arg.startswith("--lyrics="):
            lyrics= True
            sid= fix_hyphen(arg.split("=", 1)[1])

        if arg.startswith("--dl="):
            dl= True
            sid= fix_hyphen(arg.split("=", 1)[1])

        if arg.startswith("--play="):
            play= True
            term= fix_hyphen(arg.split("=", 1)[1])

        if arg.startswith("--get-id="):
            query= True
            term= fix_hyphen(arg.split("=", 1)[1])

        if arg.startswith("--debug-api="):
            api_debug= True
            term= arg.split("=", 1)[1]

    if dl:
        api= api_check(api)
        sid_check(sid)
        wrapper= Wrapper(api)
        try:
            wrapper.download(sid)
        except Exception as e:
            print("Error:", end=" ")
            print(e)

    if play:
        api= api_check(api)
        term_check(term)
        wrapper= Wrapper(api)
        try:
            wrapper.mpv_play(term)
        except Exception as e:
            print("Error:",  end=" ")
            print(e)

    if query:
        api= api_check(api)
        service= ApiService(api)
        term_check(term)
        try:
            search= service.search(term, SearchType.TRACK)
        except:
            print("API down or unstable internet connection")
            exit()
        try:
            print("ID for \""+search[0]["title"]+"\" by \""+search[0]["artists"][0]+"\": "+str(search[0]["id"]))
        except:
            print("Search term not found")

    if lyrics:
        api= api_check(api)
        service= ApiService(api)
        wrapper= Wrapper(api)
        sid_check(sid)
        try:
            meta= service.metadata(sid)
            lyr= wrapper.lyrics(meta)
        except:
            print("API down or internet unstable")
            exit()
        try:
            print(lyr)
        except:
            print("Search term not found")

    if api_debug:
        api= api_check(api)
        term_check(term)
        service= ApiService(api)
        res= service.search(term, SearchType.TRACK)
        print("Track:")
        print("~~~~~~")
        print(res[0])
        print("=========================")
        print("Track Data:")
        print("~~~~~~~~~~~")
        print(service.track(res[0]["id"], Resolution.NORMAL))
        print("=========================")
        print("Track Meta:")
        print("~~~~~~~~~~~")
        print(service.metadata(res[0]["id"]))
        print("=========================")

if __name__ == '__main__':
    main()
