from base import Tool

class SearchTool(Tool):
    """
    智能混合搜索工具

    支持多种搜索引擎后端，智能选择最佳搜索源:
    1. 混合模式 (hybrid) - 智能选择TAVILY或SERPAPI
    2. Tavily API (tavily) - 专业AI搜索
    3. SerpApi (serpapi) - 传统Google搜索
    """
    def __init__(self, backend: str, tavily_key: str, serpapi_key: str):
        super().__init__(name="search", description="一个智能网页搜索引擎。支持混合搜索模式，自动选择最佳搜索源。")

    def search_hybrid(self, query: str) -> str:
        """执行搜索"""
        return self.func(query)

    def search_tavily(self, query: str) -> str:
        """执行Tavily搜索"""
        return self.func(query)