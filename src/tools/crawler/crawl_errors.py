"""爬虫相关异常定义"""

class CrawlerError(Exception):
    """爬虫基础异常类"""
    pass

class ConfigurationError(CrawlerError):
    """配置相关错误"""
    pass

class NetworkError(CrawlerError):
    """网络相关错误"""
    pass

class ContentExtractionError(CrawlerError):
    """内容提取错误"""
    pass

class RateLimitError(CrawlerError):
    """请求频率限制错误"""
    pass

class AuthenticationError(CrawlerError):
    """认证相关错误"""
    pass
