# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# Modified: API Based YouTube Downloader (No Cookies)

import os
import re
import asyncio
import aiohttp
import random
from pathlib import Path

from py_yt import Playlist, VideosSearch

from anony import logger
from anony.helpers import Track, utils

API_URL = "https://shrutibots.site"


async def download_song(video_id: str) -> str | None:
    if not video_id or len(video_id) < 3:
        return None

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.webm")

    if os.path.exists(file_path):
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            params = {"url": video_id, "type": "audio"}

            async with session.get(
                f"{API_URL}/download",
                params=params,
                timeout=aiohttp.ClientTimeout(total=7),
            ) as response:

                if response.status != 200:
                    return None

                data = await response.json()
                token = data.get("download_token")

                if not token:
                    return None

                stream_url = f"{API_URL}/stream/{video_id}?type=audio&token={token}"

                async with session.get(
                    stream_url,
                    timeout=aiohttp.ClientTimeout(total=300),
                ) as file_response:

                    if file_response.status == 302:
                        redirect = file_response.headers.get("Location")
                        if redirect:
                            async with session.get(redirect) as final:
                                if final.status != 200:
                                    return None
                                with open(file_path, "wb") as f:
                                    async for chunk in final.content.iter_chunked(
                                        16384
                                    ):
                                        f.write(chunk)

                    elif file_response.status == 200:
                        with open(file_path, "wb") as f:
                            async for chunk in file_response.content.iter_chunked(
                                16384
                            ):
                                f.write(chunk)
                    else:
                        return None

        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path

    except Exception as ex:
        logger.warning("Audio download failed: %s", ex)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    return None


async def download_video(video_id: str) -> str | None:
    if not video_id or len(video_id) < 3:
        return None

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")

    if os.path.exists(file_path):
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            params = {"url": video_id, "type": "video"}

            async with session.get(
                f"{API_URL}/download",
                params=params,
                timeout=aiohttp.ClientTimeout(total=7),
            ) as response:

                if response.status != 200:
                    return None

                data = await response.json()
                token = data.get("download_token")

                if not token:
                    return None

                stream_url = f"{API_URL}/stream/{video_id}?type=video&token={token}"

                async with session.get(
                    stream_url,
                    timeout=aiohttp.ClientTimeout(total=600),
                ) as file_response:

                    if file_response.status == 302:
                        redirect = file_response.headers.get("Location")
                        if redirect:
                            async with session.get(redirect) as final:
                                if final.status != 200:
                                    return None
                                with open(file_path, "wb") as f:
                                    async for chunk in final.content.iter_chunked(
                                        16384
                                    ):
                                        f.write(chunk)

                    elif file_response.status == 200:
                        with open(file_path, "wb") as f:
                            async for chunk in file_response.content.iter_chunked(
                                16384
                            ):
                                f.write(chunk)
                    else:
                        return None

        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path

    except Exception as ex:
        logger.warning("Video download failed: %s", ex)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    return None


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="

        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)"
        )

        self.iregex = re.compile(
            r"https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)"
        )

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    def invalid(self, url: str) -> bool:
        return bool(re.match(self.iregex, url))

    async def search(self, query: str, m_id: int, video: bool = False):
        try:
            search = VideosSearch(query, limit=1, with_live=False)
            results = await search.next()
        except Exception:
            return None

        if results and results["result"]:
            data = results["result"][0]

            return Track(
                id=data.get("id"),
                channel_name=data.get("channel", {}).get("name"),
                duration=data.get("duration"),
                duration_sec=utils.to_seconds(data.get("duration")),
                message_id=m_id,
                title=data.get("title")[:25],
                thumbnail=data.get("thumbnails", [{}])[-1]
                .get("url")
                .split("?")[0],
                url=data.get("link"),
                view_count=data.get("viewCount", {}).get("short"),
                video=video,
            )

        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool):
        tracks = []

        try:
            plist = await Playlist.get(url)

            for data in plist["videos"][:limit]:
                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails")[-1]
                    .get("url")
                    .split("?")[0],
                    url=data.get("link").split("&list=")[0],
                    user=user,
                    view_count="",
                    video=video,
                )

                tracks.append(track)

        except Exception:
            pass

        return tracks

    async def download(self, video_id: str, video: bool = False):
        try:
            if video:
                file = await download_video(video_id)
            else:
                file = await download_song(video_id)

            if file:
                return file

        except Exception as ex:
            logger.warning("Download error: %s", ex)

        return None
