from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time


@dataclass
class CrawlResult:
    """爬取结果类"""
    url: str
    content: str
    status_code: int
    headers: Dict[str, str]
    images: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    @property
    def is_success(self) -> bool:
        """判断爬取是否成功"""
        return (
            self.status_code >= 200 
            and self.status_code < 300
            and bool(self.content)
            and not self.error
        )
        
    @property
    def is_error(self) -> bool:
        """判断是否存在错误"""
        return bool(self.error) or self.status_code >= 400
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "url": self.url,
            "content": self.content,
            "status_code": self.status_code,
            "headers": self.headers,
            "images": self.images,
            "metadata": self.metadata,
            "error": self.error,
            "timestamp": self.timestamp,
            "is_success": self.is_success,
        }

