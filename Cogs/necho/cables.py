import httpx
import asyncio
from httpx import HTTPStatusError, RequestError, TimeoutException

def time_chatting(p: int):
    sec = p
    mins = 0
    hours = 0
    if sec >= 60:
        mins = int(sec / 60)
    if mins >= 60:
        hours = int(mins / 60)

    return f"{hours}:{mins % 60}:{sec % 60}"

async def get_track(term, api):
    try:
        async with httpx.AsyncClient() as client:
            try:
                req = await client.get(url=api + "/search/", params={'s': term})
                req.raise_for_status()
            except (HTTPStatusError, RequestError, TimeoutException):
                return False

            jsonObj = req.json()
            if not "items" in jsonObj:
                return False
            items = jsonObj["items"]
            if len(items) < 1:
                return False
            songID = items[0]["id"]

            try:
                getUrlPlayable = await client.get(url=api + "/track/", params={'id': songID, 'quality': 'LOW'})
                getUrlPlayable.raise_for_status()
            except (HTTPStatusError, RequestError, TimeoutException):
                return False

            gson = getUrlPlayable.json()
            if not len(gson) > 0:
                return False
            if getUrlPlayable.text.replace("\"", "'").startswith("{'detail"):
                return False
            return {
                'url': gson[-1]["OriginalTrackUrl"],
                'cover': "https://resources.tidal.com/images/" + items[0]["album"]["cover"].replace("-", "/") + "/640x640.jpg",
                'id': songID,
                'title': items[0]['title'],
                'duration': time_chatting(int(items[0]['duration'])),
                'artist': items[0]["artist"]["name"],
                'album': items[0]["album"]["title"]
                }
    except Exception:
        return False
