# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# Shruti API Based YouTube Module for Anony

import os
import re
import asyncio
import aiohttp
import yt_dlp
from pathlib import Path
from typing import Union

from py_yt import Playlist, VideosSearch

from anony import logger
from anony.helpers import Track, utils

API_URL = "https://shrutibots.site"


# --------------------------------------------------
# API AUDIO DOWNLOAD
# --------------------------------------------------

async def download_song(link: str) -> str | None:

    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link

    if not video_id:
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

                async with session.get(stream_url) as file_response:

                    if file_response.status == 302:

                        redirect = file_response.headers.get("Location")

                        async with session.get(redirect) as final:

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

    return None


# --------------------------------------------------
# API VIDEO DOWNLOAD
# --------------------------------------------------

async def download_video(link: str) -> str | None:

    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link

    if not video_id:
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

                async with session.get(stream_url) as file_response:

                    if file_response.status == 302:

                        redirect = file_response.headers.get("Location")

                        async with session.get(redirect) as final:

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

    return None


# --------------------------------------------------
# SHELL COMMAND
# --------------------------------------------------

async def shell_cmd(cmd):

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    out, err = await proc.communicate()

    if err:
        return err.decode()

    return out.decode()


# --------------------------------------------------
# YOUTUBE CLASS
# --------------------------------------------------

class YouTube:

    def __init__(self):

        self.base = "https://www.youtube.com/watch?v="

        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)"
        )

    # -----------------------------------------------

    async def exists(self, link: str):

        return bool(re.search(self.regex, link))

    # -----------------------------------------------

    async def search(self, query: str, m_id: int, video=False):

        try:

            search = VideosSearch(query, limit=1)

            results = await search.next()

        except Exception:

            return None

        if results and results["result"]:

            data = results["result"][0]

            return Track(
                id=data.get("id"),
                title=data.get("title")[:25],
                duration=data.get("duration"),
                duration_sec=utils.to_seconds(data.get("duration")),
                channel_name=data.get("channel", {}).get("name"),
                thumbnail=data.get("thumbnails")[-1]["url"].split("?")[0],
                url=data.get("link"),
                message_id=m_id,
                video=video,
            )

    # -----------------------------------------------

    async def playlist(self, limit, user, url, video):

        tracks = []

        try:

            plist = await Playlist.get(url)

            for data in plist["videos"][:limit]:

                track = Track(
                    id=data.get("id"),
                    title=data.get("title")[:25],
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    channel_name=data.get("channel", {}).get("name"),
                    thumbnail=data.get("thumbnails")[-1]["url"].split("?")[0],
                    url=data.get("link"),
                    user=user,
                    video=video,
                )

                tracks.append(track)

        except Exception:
            pass

        return tracks

    # -----------------------------------------------

    async def track(self, link):

        search = VideosSearch(link, limit=1)

        data = (await search.next())["result"][0]

        return {
            "title": data["title"],
            "link": data["link"],
            "vidid": data["id"],
            "duration": data["duration"],
            "thumb": data["thumbnails"][0]["url"].split("?")[0],
        }

    # -----------------------------------------------

    async def formats(self, link):

        ydl_opts = {"quiet": True}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            r = ydl.extract_info(link, download=False)

            formats = []

            for f in r["formats"]:

                try:

                    if "dash" not in str(f["format"]).lower():

                        formats.append(
                            {
                                "format": f["format"],
                                "filesize": f.get("filesize"),
                                "format_id": f["format_id"],
                                "ext": f["ext"],
                                "format_note": f["format_note"],
                                "yturl": link,
                            }
                        )

                except:
                    continue

        return formats, link

    # -----------------------------------------------

    async def slider(self, link, query_type):

        search = VideosSearch(link, limit=10)

        result = (await search.next())["result"]

        data = result[query_type]

        return (
            data["title"],
            data["duration"],
            data["thumbnails"][0]["url"].split("?")[0],
            data["id"],
        )

    # -----------------------------------------------

    async def download(self, video_id: str, video=False):

        try:

            if video:

                file = await download_video(video_id)

            else:

                file = await download_song(video_id)

            if file:

                return file

        except Exception as e:

            logger.warning("Download error: %s", e)

        return None
