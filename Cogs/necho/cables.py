import requests

def time_chatting(p: int):
    sec= p
    mins= 0
    hours= 0
    if sec >= 60:
        mins= int(sec/60)
    if mins >= 60:
        hours= int(mins/60)

    return f"{hours}:{mins%60}:{sec%60}"

def get_track(term, api):
    req= requests.get(url= api+ "/search/", params= {'s': term})
    jsonObj= req.json()
    if not "items" in jsonObj:
        return False
    items= jsonObj["items"]
    if len(items) < 1:
        return False
    songID= items[0]["id"]
    getUrlPlayable= requests.get(url= api+ "/track/", params= {'id': songID, 'quality': 'LOW'})
    gson= getUrlPlayable.json()
    if not len(gson) > 0:
        return False
    if getUrlPlayable.text.replace("\"", "'").startswith("{'detail"):
        return False
    return {
            'url': gson[-1]["OriginalTrackUrl"],
            'cover': "https://resources.tidal.com/images/"+ items[0]["album"]["cover"].replace("-", "/")+ "/640x640.jpg",
            'id': songID,
            'title': items[0]['title'],
            'duration': time_chatting(int(items[0]['duration'])),
            'artist': items[0]["artist"]["name"],
            'album': items[0]["album"]["title"]
            }
