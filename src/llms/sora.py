import os
import time
import httpx
import logging
from typing import Optional
from pathlib import Path
from src.config.yaml_loader import load_yaml_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SoraAPIError(Exception):
    """Sora API异常基类"""


class SoraClient:
    """Azure OpenAI Sora 视频生成 API 客户端"""
    API_VERSION = "preview"
    MODEL_NAME = "sora"
    OUTPUT_DIR = "generated_videos"

    def __init__(self):
        # 确保输出目录存在
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

        # 优先环境变量，其次 conf.yaml
        conf_path = Path(__file__).parent.parent.parent / "conf.yaml"
        config = load_yaml_config(str(conf_path.resolve()))
        video_config = config.get("VIDEO_MODEL", {})

        self.endpoint = os.getenv("ENDPOINT_URL", video_config.get("azure_endpoint"))
        self.deployment = os.getenv("DEPLOYMENT_NAME", video_config.get("azure_deployment"))
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY", video_config.get("api_key"))
        self.api_version = video_config.get("api_version", "preview")

        if not self.endpoint or not self.deployment or not self.api_key:
            raise ValueError("请配置 ENDPOINT_URL、DEPLOYMENT_NAME、AZURE_OPENAI_API_KEY 或在 conf.yaml 的 VIDEO_MODEL 中设置。")

        self.client = httpx.Client(timeout=30.0)
        self.headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json"
        }

    def start_video_generation(
        self,
        prompt: str,
        n_seconds: int = 5,
        height: int = 1080,
        width: int = 1080,
        n_variants: int = 1,
        model: Optional[str] = None,
    ) -> str:
        """启动视频生成任务并返回任务ID"""
        path = "openai/v1/video/generations/jobs"
        params = f"?api-version={self.api_version}"
        url = self.endpoint.rstrip("/") + "/" + path + params

        body = {
            "prompt": prompt,
            "n_variants": str(n_variants),
            "n_seconds": str(n_seconds),
            "height": str(height),
            "width": str(width),
            "model": model or self.deployment,
        }

        logging.info(f"请求生成视频: {body}")
        resp = self.client.post(url, headers=self.headers, json=body)
        if not resp.is_success:
            logging.error(f"视频生成请求失败: {resp.text}")
            raise Exception(f"视频生成失败: {resp.text}")

        job = resp.json()
        job_id = job.get("id")
        logging.info(f"视频生成任务已启动，任务ID: {job_id}")
        return job_id

    def get_job_details(self, job_id: str) -> dict:
        """获取视频生成任务的详情"""
        status_url = f"{self.endpoint.rstrip('/')}/openai/v1/video/generations/jobs/{job_id}?api-version={self.api_version}"
        try:
            resp = self.client.get(status_url, headers=self.headers)
            resp.raise_for_status()
            job = resp.json()
            logging.info(f"任务 {job_id} 的详情: {job}")
            return job
        except httpx.HTTPStatusError as e:
            logging.error(f"获取任务详情失败: {e.response.text}")
            raise SoraAPIError(f"获取任务详情失败: {e.response.text}") from e
        except Exception as e:
            logging.error(f"获取任务详情时发生未知错误: {e}")
            raise SoraAPIError(f"获取任务详情时发生未知错误: {e}") from e

    def get_video_url(self, job_id: str, poll_interval: int = 3) -> str:
        """轮询任务状态直到完成，并返回视频URL"""
        logging.info(f"开始轮询任务 {job_id} 的状态")
        while True:
            job = self.get_job_details(job_id)
            status = job.get("status")
            if status == "succeeded":
                generations = job.get("generations", [])
                if generations:
                    generation_id = generations[0].get("id")
                    params = f"?api-version={self.api_version}"
                    video_url = f'{self.endpoint.rstrip("/")}/openai/v1/video/generations/{generation_id}/content/video{params}'
                    logging.info(f"视频生成成功，下载地址: {video_url}")
                    return video_url
                else:
                    logging.warning("任务成功但未返回 generations。")
                    return ""
            elif status == "failed":
                logging.error(f"视频生成失败: {job}")
                raise SoraAPIError(f"视频生成失败: {job}")
            
            logging.info(f"任务 {job_id} 当前状态: {status}，等待 {poll_interval} 秒后重试")
            time.sleep(poll_interval)

    def download_video(self, video_url: str, output_filename: Optional[str] = None) -> str:
        """下载视频并保存到本地"""
        if not output_filename:
            output_filename = f"{video_url.split('/')[-3]}.mp4"

        logging.info(f"开始下载视频: {video_url}")
        try:
            video_resp = self.client.get(video_url, headers=self.headers)
            video_resp.raise_for_status()
            output_path = os.path.join(self.OUTPUT_DIR, output_filename)
            with open(output_path, "wb") as f:
                f.write(video_resp.content)
            logging.info(f"视频已保存为 {output_path}")
            return output_path
        except httpx.HTTPStatusError as e:
            logging.error(f"视频下载失败: {e.response.text}")
            raise SoraAPIError(f"视频下载失败: {e.response.text}") from e
        except Exception as e:
            logging.error(f"下载视频时发生未知错误: {e}")
            raise SoraAPIError(f"下载视频时发生未知错误: {e}") from e
        

if __name__ == "__main__":    
    # 测试代码
    client = SoraClient()
    job_id = client.start_video_generation(
        prompt="""
Cinematic wide shot in pure white void space. Colorful LEGO bricks floating and flying through empty space, magically assembling into complex architectural structure. Bricks rotate and snap together with precise movements - bright red, blue, yellow, green pieces creating intricate geometric patterns. Camera slowly orbits around the growing construction, revealing the assembly from multiple angles. Shallow depth of field keeps focus on active building area while background bricks blur into motion. Crisp plastic snap sounds, gentle whooshing of bricks flying through air, rhythmic clicking of connections. Light ambient electronic music building in intensity. No other objects in frame, just pure white background and vibrant LEGO pieces. 4K resolution, perfect lighting shows plastic texture and vibrant colors. (no subtitles)
"""
        ,
        n_seconds=20,
        height=1080,
        width=1080,
        n_variants=1
    )
    video_url = client.get_video_url(job_id)
    print(f"视频生成成功，下载地址: {video_url}")

    # 测试下载视频
    # https://lingli-agent-resource.openai.azure.com/openai/v1/video/generations/gen_01jzqmn4kcfjwtxwrz46qy1p34/content/video?api-version=preview
    client.download_video(video_url, "sunset_video.mp4")