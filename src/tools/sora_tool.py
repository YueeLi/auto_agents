from langchain_core.tools import tool
from src.llms.sora import SoraClient, SoraAPIError
from typing import Optional

@tool
def generate_sora_video(
    prompt: str,
    n_seconds: Optional[int] = 5,
    height: Optional[int] = 1080,
    width: Optional[int] = 1080,
    n_variants: Optional[int] = 1,
    download: bool = False,
    output_filename: Optional[str] = None,
) -> str:
    """Generates a video using the Sora model from a text prompt.
    Can either return the video URL or download it to a local path.

    Args:
        prompt: The text prompt describing the video to be generated.
        n_seconds: The duration of the video in seconds.
        height: The height of the video in pixels.
        width: The width of the video in pixels.
        n_variants: The number of video variants to generate.
        download: If True, downloads the video and returns the local path.
                  If False, returns the video URL.
        output_filename: Optional filename for the downloaded video. Used only if `download` is True.

    Returns:
        A string containing the video URL or the local path to the downloaded video, or an error message.
    """
    try:
        client = SoraClient()
        job_id = client.start_video_generation(
            prompt=prompt,
            n_seconds=n_seconds,
            height=height,
            width=width,
            n_variants=n_variants,
        )

        # This method is assumed to block until the video is ready.
        video_url = client.get_video_url(job_id=job_id)

        if download:
            video_path = client.download_video(
                video_url=video_url, output_filename=output_filename
            )
            return f"Video downloaded successfully: {video_path}"
        else:
            return f"Video URL retrieved successfully: {video_url}"

    except SoraAPIError as e:
        return f"Error during video generation: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


if __name__ == "__main__":
    # The previous test code has been removed as it called a deleted function.
    pass
