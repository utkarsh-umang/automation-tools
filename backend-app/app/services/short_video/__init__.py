"""Media pipeline for the Short Video tool.

Download a source video, cut it into clips, and hand the files to the storage
layer. The *decision* about what to clip is not made here — that comes from
``ai_agents.agents.short_video_generator.run_short_video_agent``, which returns
timestamps and never touches video bytes. Same division as the Thumbnail
Creator, where the agent returns PNG bytes and this backend owns S3.

Everything here takes an explicit directory. Use ``job_workspace`` to get one
per job; nothing is shared between jobs and nothing deletes what it did not
create.
"""

from app.services.short_video.cut_video import create_clips
from app.services.short_video.download import download_youtube_video
from app.services.short_video.ffmpeg import FFmpegNotFound, ffmpeg_dir, resolve_ffmpeg
from app.services.short_video.workspace import job_workspace

__all__ = [
    "job_workspace",
    "download_youtube_video",
    "create_clips",
    "resolve_ffmpeg",
    "ffmpeg_dir",
    "FFmpegNotFound",
]
