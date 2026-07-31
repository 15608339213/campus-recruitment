"""数据源模块。

包含 GitHub 开源校招仓库数据源等。每个数据源提供统一的抓取接口，
返回原始 job dict 列表，交由 pipeline 统一清洗。
"""
from .github_repos import GitHubRepoSource

__all__ = ["GitHubRepoSource"]
