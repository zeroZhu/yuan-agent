import os
from typing import Literal
from base import Tool
from pydantic import BaseModel, Field

class SearchToolOptions(BaseModel):
    """搜索工具参数"""
    query: str = Field(description="搜索查询")
    backend: Literal['hybrid', 'tavily'] = Field(default='hybrid', description="搜索后端模式")

class SearchTool(Tool):
    """
    智能混合搜索工具

    支持多种搜索引擎后端，智能选择最佳搜索源:
    1. 混合模式 (hybrid) - 智能选择TAVILY或SERPAPI
    2. Tavily API (tavily) - 专业AI搜索
    3. SerpApi (serpapi) - 传统Google搜索
    """
    def __init__(self, opt: SearchToolOptions):
        super().__init__(name="search", description="一个智能网页搜索引擎。支持混合搜索模式，自动选择最佳搜索源。")
        self.options = opt
        self.search_sources = []
        self._set_search_sources()

    def _set_search_sources(self):
        """设置搜索后端"""
        # 检查Tavily可用性
        if os.getenv("TAVILY_API_KEY"):
            try:
                from tavily import TavilyClient
                self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
                self.search_sources.append("tavily")
                print("✅ Tavily搜索源已启用")
            except ImportError:
                print("⚠️ Tavily库未安装")

        # 检查SerpApi可用性
        if os.getenv("SERPAPI_API_KEY"):
            try:
                import serpapi
                self.search_sources.append("serpapi")
                print("✅ SerpApi搜索源已启用")
            except ImportError:
                print("⚠️ SerpApi库未安装")

        if self.search_sources:
            print(f"🔧 可用搜索源: {', '.join(self.search_sources)}")
        else:
            print("⚠️ 没有可用的搜索源，请配置API密钥")
    
    def search_hybrid(self, query: str) -> str:
        """执行搜索"""
        if not query.strip():
            return "❌ 错误:搜索查询不能为空"

        # 检查是否有可用的搜索源
        if not self.search_sources:
            return """❌ 没有可用的搜索源，请配置以下API密钥之一:

            1. Tavily API: 设置环境变量 TAVILY_API_KEY
            获取地址: https://tavily.com/

            2. SerpAPI: 设置环境变量 SERPAPI_API_KEY
            获取地址: https://serpapi.com/

            配置后重新运行程序。"""

        print(f"🔍 开始智能搜索: {query}")

        for source in self.search_sources:
            result = ""
            try:
                match source:
                    case "tavily":
                        result = self.search_tavily(query)
                    case "serpapi":
                        result = self.search_serpapi(query)
                    case _:
                        result = f"❌ 未知搜索源: {source}"
            except Exception as e:
                result = f"❌ 搜索源 {source} 发生错误: {str(e)}"
            return result
    
    def search_tavily(self, query: str) -> str:
        """使用Tavily API搜索"""
        if not self.tavily_client:
            return "❌ Tavily API未配置"
        try:
            results = self.tavily_client.search(query)
            return results
        except Exception as e:
            return f"❌ Tavily API搜索失败: {str(e)}"
   
    def search_serpapi(self, query: str) -> str:
        """使用SerpApi搜索"""
        try:
            import serpapi
            results = serpapi.search({"q": query })
            return results
        except Exception as e:
            return f"❌ SerpApi搜索失败: {str(e)}"  