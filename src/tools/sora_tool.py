from langchain_core.tools import tool
from src.llms.sora import SoraClient, SoraAPIError
from typing import Optional

@tool
def start_sora_video_generation(prompt: str, n_seconds: Optional[int] = 5, height: Optional[int] = 1080, width: Optional[int] = 1080, n_variants: Optional[int] = 1) -> str:
    """Starts a video generation task using the Sora model from a text prompt and returns a job ID.

    Args:
        prompt: The text prompt describing the video to be generated.
        n_seconds: The duration of the video in seconds.
        height: The height of the video in pixels.
        width: The width of the video in pixels.
        n_variants: The number of video variants to generate.

    Returns:
        A string containing the job ID for the video generation task or an error message.
    """
    try:
        client = SoraClient()
        job_id = client.start_video_generation(
            prompt=prompt,
            n_seconds=n_seconds,
            height=height,
            width=width,
            n_variants=n_variants
        )
        return f"Video generation started. Job ID: {job_id}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@tool
def get_sora_video_url(job_id: str) -> str:
    """Gets the video URL from a completed Sora video generation task.

    Args:
        job_id: The job ID for the video generation task.

    Returns:
        A string containing the URL of the generated video or an error message.
    """
    try:
        client = SoraClient()
        video_url = client.get_video_url(job_id=job_id)
        return f"Video URL retrieved successfully: {video_url}"
    except SoraAPIError as e:
        return f"Error getting video URL: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@tool
def download_sora_video(video_url: str, output_filename: Optional[str] = None) -> str:
    """Downloads a video from a URL.

    Args:
        video_url: The URL of the video to download.
        output_filename: The optional filename for the downloaded video.

    Returns:
        A string containing the path to the downloaded video or an error message.
    """
    try:
        client = SoraClient()
        video_path = client.download_video(video_url=video_url, output_filename=output_filename)
        return f"Video downloaded successfully: {video_path}"
    except SoraAPIError as e:
        return f"Error downloading video: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"



if __name__ == "__main__":
    # 生成视频

    # 下载视频
    video_url = "https://lingli-agent-resource.openai.azure.com/openai/v1/video/generations/gen_01jzqmn4kcfjwtxwrz46qy1p34/content/video?api-version=preview"
    download_sora_video(video_url)