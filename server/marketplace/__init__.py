"""AdeBuddy 插件市场服务模块。

作为 Flask Blueprint 挂载到主应用，提供插件市场的浏览/发布/下载/安装/移除功能。
数据存储在 config/marketplace/（index.json + packages/*.zip）。
"""
from .routes import create_marketplace_bp

__all__ = ["create_marketplace_bp"]
