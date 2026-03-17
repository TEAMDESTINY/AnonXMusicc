# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import shutil
from pathlib import Path

from anony import logger


def ensure_dirs():
    """
    Ensure that the necessary directories exist.
    """

    # Check optional dependencies
    if not shutil.which("deno"):
        logger.warning("Deno not found in PATH. Some features may not work.")

    if not shutil.which("ffmpeg"):
        logger.warning("FFmpeg not found in PATH. Some features may not work.")

    # Ensure required directories exist
    for dir in ["cache", "downloads"]:
        Path(dir).mkdir(parents=True, exist_ok=True)

    logger.info("Cache directories updated.")
