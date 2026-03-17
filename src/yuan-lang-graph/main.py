
import os
from typing import TypedDict, List, Annotated
from dotenv import load_dotenv
from tavily import TavilyClient
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver 


load_dotenv()


# 定义全局状态的数据结构
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]      # 对话历史
    user_query: str      # 经过LLM理解后的用户需求总结
    search_query: str    # 优化后用于Tavily API的搜索查询
    search_results: str  # Tavily搜索返回的结果
    final_answer: str    # 最终生成的答案
    step: str            # 标记当前步骤
    # ... 任何其他需要追踪的状态

# 初始化Tavily客户端
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

llm = ChatOpenAI(
    model="qwen-max",
    api_key=os.getenv("DASHSCOPE_API_KEY") or "", # type: ignore
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 定义一个“理解查询”节点函数
def understand_query_node(state: AgentState) -> dict:
    """步骤1：理解用户查询并生成搜索关键词"""
    user_message = state["messages"][-1].content
    
    understand_prompt = f"""分析用户的查询："{user_message}"
    请完成两个任务：
    1. 简洁总结用户想要了解什么
    2. 生成最适合搜索引擎的关键词（中英文均可，要精准）

    格式：
    理解：[用户需求总结]
    搜索词：[最佳搜索关键词]"""

    response = llm.invoke([HumanMessage(content=understand_prompt)])
    print('response :', response)
    response_text = response.content
    
    # 解析LLM的输出，提取搜索关键词
    search_query = user_message # 默认使用原始查询
    if "搜索词：" in response_text:
        search_query = str(response_text).split("搜索词：")[1].strip()
    
    return {
        "user_query": response_text,
        "search_query": search_query,
        "step": "understood",
        "messages": [AIMessage(content=f"我将为您搜索：{search_query}")]
    }

def tavily_search_node(state: AgentState) -> dict:
    """步骤2：使用Tavily API进行真实搜索"""
    search_query = state["search_query"]
    try:
        print(f"🔍 正在搜索: {search_query}")
        response = tavily_client.search(query=search_query, search_depth="basic", max_results=5, include_answer=True)
        print('response :', response)
        query, anwser, results = response.values()
        results_formatted = []
        for i, result in enumerate(results, 1):
            title = result.get("title", "无标题")
            url = result.get("url", "")
            content = result.get("content", "")
            score = result.get("score", 0)
            
            # 清理内容，移除多余空白
            content_clean = "\n".join(line.strip() for line in content.split("\n") if line.strip())
            
            results_formatted.append(f"""### 来源 {i}: {title}
            - 相关度: {score:.2%}
            - 链接: {url}
            {content_clean[:1500]}""")
        
        return {
            "search_results": f"""
              问题：{query}
              答案：{anwser}
              搜索结果：
              {"\n\n".join(results_formatted) }
            """,
            "step": "searched",
            "messages": [AIMessage(content="✅ 搜索完成！正在整理答案...")]
        }
    except Exception as e:
        # ... (处理错误) ...
        return {
            "search_results": f"搜索失败：{e}",
            "step": "search_failed",
            "messages": [AIMessage(content="❌ 搜索遇到问题...")]
        }

def generate_answer_node(state: AgentState) -> dict:
    """步骤3：基于搜索结果生成最终答案"""
    if state["step"] == "search_failed":
        # 如果搜索失败，执行回退策略，基于LLM自身知识回答
        fallback_prompt = f"搜索API暂时不可用，请基于您的知识回答用户的问题：\n用户问题：{state['user_query']}"
        response = llm.invoke([HumanMessage(content=fallback_prompt)])
    else:
        # 搜索成功，基于搜索结果生成答案
        answer_prompt = f"""基于以下搜索结果为用户提供完整、准确的答案：
用户问题：{state['user_query']}
搜索结果：\n{state['search_results']}
请综合搜索结果，提供准确、有用的回答..."""
        response = llm.invoke([HumanMessage(content=answer_prompt)])
    
    return {
        "final_answer": response.content,
        "step": "completed",
        "messages": [AIMessage(content=response.content)]
    }


def create_search_agent():
    workflow = StateGraph(AgentState)
    workflow.add_node('UNDERSTANT', understand_query_node)
    workflow.add_node('SEARCH', tavily_search_node)
    workflow.add_node('ANWSER', generate_answer_node)
    workflow.add_edge(START, 'UNDERSTANT')
    workflow.add_edge('UNDERSTANT', 'SEARCH')
    workflow.add_edge('SEARCH', 'ANWSER')
    workflow.add_edge('ANWSER', END)

    # checkpointer = InMemorySaver()
    
    return workflow.compile()



def main():
    agent = create_search_agent()

    anwser = agent.invoke(
        {
            "messages": [HumanMessage(content="明天我要去北京，天气怎么样？有合适的景点吗?")],
            "user_query": "",
            "search_query": "",
            "search_results": "",
            "final_answer": "",
            "step": "",
        }
    )
    print("==============================")
    print(anwser["final_answer"])



if __name__ == "__main__":
    main()
# {
# {
#   "query": "明天我要去北京，天气怎么样？有合适的景点吗",
#   "follow_up_questions": null,
#   "answer": "Tomorrow in Beijing, expect sunny weather with a high of around 15°C. Popular attractions include the Forbidden City and the Temple of Heaven. Check local forecasts for the latest updates.",
#   "images": [],
#   "results": [
#     {
#       "url": "https://www.weather.com.cn/weather15d/101010100.shtml",
#       "title": "预报- 北京",
#       "content": "8-15天预报属于客观预报产品，反映的是未来天气变化趋势、请随时关注最新预报.....\n\n8-15天预报，是集合多家全球数值天气预报模式客观预报产品加工而成，未经预报员主观订正，反映未来一段时间内天气变化趋势，具有一定的不确定性，供公众参考，欲知更加准确的天气预报需随时关注短期天气预报和最新预报信息更新。\n\n# 天气资讯\n\n:   北京近日持续晴暖 山桃花绽放与轻轨构成早春画卷  中国天气网 2026-03-15 11:14\n\n:   江西今明天部分地区有小雨 昼夜温差较大早晚时段湿冷感明显  中国天气网 2026-03-15 10:44\n\n:   广西南宁持续晴暖天气 街道木棉花绽放一片火红  中国天气网 2026-03-15 09:31\n\n:   今明天北京晴天为主气温回升 最高气温可达15℃左右  中国天气网 2026-03-15 07:10\n\n:   用樱花打开春天 一组图带你感受春日美好  中国天气网 2026-03-14 15:12\n\n# 周边地区 | 周边景点 2026-03-15 11:30更新\n\n 香河\n\n  /\n\n  14/0°C\n 涿州\n\n  /\n\n  14/1°C\n 唐山\n\n  /\n\n  13/0°C\n 沧州\n\n  /\n\n  12/1°C\n 天津\n\n  /\n\n  14/4°C\n 廊坊\n\n  /\n\n  15/2°C\n 太原\n\n  /\n\n  11/0°C\n 石家庄\n\n  /\n\n  13/2°C\n 涿鹿\n\n  /\n\n  12/0°C\n 张家口\n\n  /\n\n  12/-1°C\n 保定\n\n  /\n\n  13/0°C\n 三河\n\n  /\n\n  15/1°C\n\n# 周边地区 | 周边景点 2026-03-15 11:30更新\n\n 北京孔庙\n\n  /\n\n  15/5°C\n 北京国子监\n\n  /\n\n  15/5°C\n 中国地质博物馆\n\n  / [...] 首页 预报 预警 雷达 云图 天气地图 专业产品 资讯 视频 节气 我的天空\n\n更多\n\n台风路径 空间天气 图片 专题 环境 旅游 碳中和 气象科普 一带一路 产创平台\n\n国内) 本地) 国际)\n\n:   北京 上海 成都 杭州 南京 天津 深圳 重庆 西安 广州 青岛 武汉\n\n:   故宫 阳朔漓江 龙门石窟 野三坡 颐和园 九寨沟 东方明珠 凤凰古城 秦始皇陵 桃花源\n\n高球\n:   佘山 春城湖畔 华彬庄园 观澜湖 依必朗 旭宝 博鳌 玉龙雪山 番禺南沙 东方明珠\n\n<<返回 全国\n\n河北下辖区域\n\n热门城市\n\n:   曼谷 东京 首尔 吉隆坡 新加坡 巴黎 罗马 伦敦 雅典 柏林 纽约 温哥华 墨西哥城 哈瓦那 圣何塞 巴西利亚 布宜诺斯艾利斯 圣地亚哥 利马 基多 悉尼 墨尔本 惠灵顿 奥克兰 苏瓦 开罗 内罗毕 开普敦 维多利亚 拉巴特\n\n选择洲际\n\n:   亚洲 欧洲 北美洲 南美洲 非洲 大洋洲\n\n全国> 北京 > 城区\n\n 今天\n 7天\n 8-15天\n 40天\n 雷达图\n\n 周日（22日） 多云 16℃/5℃ 西风转南风 <3级\n 周一（23日） 阴 18℃/6℃ 南风 <3级\n 周二（24日） 多云转阴 20℃/8℃ 南风 <3级\n 周三（25日） 雨 22℃/10℃ 西南风转东风 <3级\n 周四（26日） 阴 22℃/14℃ 南风转东南风 <3级\n 周五（27日） 阴转多云 24℃/14℃ 西南风转南风 3-4级转<3级\n 周六（28日） 阴 25℃/6℃ 北风转西北风 3-4级\n 周日（29日） 多云转晴 15℃/6℃ 西北风转西南风 <3级\n\n8-15天预报属于客观预报产品，反映的是未来天气变化趋势、请随时关注最新预报..... [...] 北京孔庙\n\n  /\n\n  15/5°C\n 北京国子监\n\n  /\n\n  15/5°C\n 中国地质博物馆\n\n  /\n\n  15/5°C\n 月坛公园\n\n  /\n\n  16/5°C\n 明城墙遗址公园\n\n  /\n\n  15/5°C\n 北京市规划展览馆\n\n  /\n\n  15/1°C\n 什刹海\n\n  /\n\n  16/4°C\n 南锣鼓巷\n\n  /\n\n  15/5°C\n 天坛公园\n\n  /\n\n  15/2°C\n 北海公园\n\n  /\n\n  15/5°C\n 景山公园\n\n  /\n\n  15/5°C\n 北京海洋馆\n\n  /\n\n  15/4°C\n\n# 高清图集\n\n青海海西遭遇沙尘天气 天空昏黄能见度不佳 北京近日持续晴暖 山桃花绽放与轻轨构成早春画卷 山东威海气温低迷 草木染霜“镶银边” 北京现日晕景观 太阳自带光环 植树节：河南汝州开展植树活动 建设绿色家园\n\n# 重大天气事件\n\n 3月15日\n\n  ## 南方阴雨持续北方雨雪暂歇 贵州湖南等地降温可超10℃\n\n  今天（3月15日）降温核心区域将向南转移，贵州东部、湖南西北部、湖北一带多地降温或超10℃，北方则以晴朗升温为主。\n 3月14日\n\n  ## 陕西山西等地局地仍有强降雪 长江中下游将进入连阴雨模式\n\n  今天降雪范围进一步向东推进，明天，北方雨雪会告一段落，降水重心将转移至西南地区东部到长江中下游一带。\n 3月13日\n\n  ## 北方降雪加强甘肃宁夏等地有暴雪 西南等地湿凉感加重\n\n  随着冷暖空气交汇，今明天将进入本轮雨雪过程的最强时段，青海、甘肃、宁夏、陕西等地部分地区有大到暴雪。\n 3月12日\n\n  ## 北方多地大到暴雪来袭 西北等地冷暖反差大\n\n  今起四天，较强冷空气继续向东推进，雨雪也会随之发展，明后天将为此轮过程最强降雪时段，注意防范。\n 3月11日\n\n  ## 我国大部今日晴暖格局延续 明起大范围雨雪降温来袭",
#       "score": 0.98959166,
#       "raw_content": null,
#       "favicon": "https://www.weather.com.cn/m2/i/favicon.ico?v=3"
#     },
#     {
#       "url": "https://www.ventusky.com/zh/beijing",
#       "title": "天气- 北京市- 14天预报：气温、风和雷达",
#       "content": "| 07:00 | 08:00 | 09:00 | 10:00 | 11:00 | 12:00 | 13:00 | 14:00 | 15:00 | 16:00 | 17:00 | 18:00 | 19:00 | 20:00 | 21:00 | 22:00 | 23:00 | 00:00 明天 | 01:00 明天 | 02:00 明天 | 03:00 明天 | 04:00 明天 | 05:00 明天 | 06:00 明天 | 07:00 明天 |\n ---  ---  ---  ---  ---  ---  ---  ---  ---  ---  ---  --- [...] | 晴朗的天空 5 °C 0 mm 0 %  北  5 km/h | 晴朗的天空 5 °C 0 mm 0 %  北  5 km/h | 晴朗的天空 5 °C 0 mm 0 %  北  5 km/h | [...] | 灰蒙蒙 2 °C 0 mm 10 %  北  5 km/h | 灰蒙蒙 2 °C 0 mm 0 %  东  3 km/h | 灰蒙蒙 3 °C 0 mm 0 %  北  3 km/h | 晴朗的天空，几朵云 4 °C 0 mm 10 %  北  5 km/h | 晴朗的天空 6 °C 0 mm 10 %  东北  6 km/h | 晴朗的天空 8 °C 0 mm 10 %  东北  4 km/h | 晴朗的天空 10 °C 0 mm 0 %  东  3 km/h | 晴朗的天空 12 °C 0 mm 0 %  东南  4 km/h | 晴朗的天空 12 °C 0 mm 0 %  南  5 km/h | 晴朗的天空 13 °C 0 mm 0 %  南  5 km/h | 晴朗的天空 13 °C 0 mm 0 %  南  7 km/h | 晴朗的天空 12 °C 0 mm 0 %  南  3 km/h | 晴朗的天空 11 °C 0 mm 0 %  东南  1 km/h | 晴朗的天空 10 °C 0 mm 0 %  东北  1 km/h | 晴朗的天空 9 °C 0 mm 0 %  北  3 km/h | 晴朗的天空 9 °C 0 mm 0 %  北  5 km/h | 晴朗的天空 7 °C 0 mm 0 %  北  3 km/h | 晴朗的天空 6 °C 0 mm 0 %  北  3 km/h | 晴朗的天空 6 °C 0 mm 0 %  西北  6 km/h | 晴朗的天空 6 °C 0 mm 0 %  西北  6 km/h | 晴朗的天空 6 °C 0 mm 0 %  北  5 km/h | 晴朗的天空 5 °C 0 mm 0 %  北  5 km/h | 晴朗的天空 5 °C 0 mm 0 %  北  5 km/h | 晴朗的天空 5 °C 0 mm 0 %",
#       "score": 0.97997653,
#       "raw_content": null,
#       "favicon": "https://static.ventusky.com/images_v2/apple-touch-icon-152x152.png"
#     },
#     {
#       "url": "https://www.visitbeijing.com.cn/article/47QrpKcpBbU",
#       "title": "下雨天北京最好玩的11个好去处",
#       "content": "中国园林博物馆\n\n雨天的北京本就是美的，在这样的天气里，在中国园林博物馆看着雨中的建筑，馆中的藏品，也不失为一种享受。\n\n中国美术馆\n\n雨天适合读书，也适合看画，到中国美术馆，看一看各类美术作品，黏湿的天气也多了些乐趣呢~\n\n埃里克运动世界体验馆\n\n不想跟阴雨天一样阴沉，那么就HIGH起来吧！到蹦床运动馆让全身动起来！忘了外面没完没了的雨，尽情地跳吧跳吧~\n\n浩泰冰上运动中心（新世界）\n\n如果觉得蹦床运动量太大，但又想活动活动，那么溜冰也是不错的选择，新世界的这家溜冰场可是真冰的，穿上一双溜冰鞋，在冰面上尽情驰骋吧！\n\n北京海洋馆\n\n忘掉外面的天气，去海洋馆看看游来游去的鱼群，也忘却了心中的浮躁。这里有彩色的热带鱼、活泼的海豚、萌萌的海龟，以及各种你没见过的珍稀鱼类，开拓眼界的同时，还能带来单纯的快乐。\n\n 编辑：张宁\n\n原创声明：本文是北京旅游网原创文章,其最终版权仍归北京旅游网所有，转载请注明来自北京旅游网\n\n征文启事\n\n为能让网友分享自己美好旅途，记录旅途美好回忆，北京旅游网特面向全球网友公开征集文旅类稿件。范围涵括吃喝玩乐游购娱展演等属于文旅范畴的内容均可，形式图文、视频均可。\n\n稿件必须原创。稿件一经采用，即有机会获得景区门票、精美礼品，更有机会参与北京旅游网年终盛典活动。\n\n投稿邮箱：tougao@visitbeijing.com.cn\n\n咨询QQ：490768046\n\n## 更多北京旅游攻略\n\n北京市一周演出预告（3月9日-15日）阅读\n\n 不止司马台长城免票！北京“三八”妇女节活动汇总来了——\n 快看！开了开了！北京3月花海预报——\n 美不胜收！北京“迎春第一花”盛放\n 今天21时59分，正式迎来——\n 今天，在北京看这种年度唯一“奇观”\n 开了！北京这里的“小鸟玉兰”破壳啦——\n\n分享到微信朋友圈\n\nx [...] ### 首页\n ### 文化北京\n\n  + 展览\n  + 演出\n  + 阅读\n  + 影视\n ### 特色文化\n\n  + 古都文化\n  + 红色文化\n  + 京味文化\n  + 创新文化\n ### 畅游北京\n\n  + 游玩\n  + 美食\n  + 住宿\n  + 购物\n  + 旅游地图\n  + 周末去哪玩\n  + 民宿大全\n ### 北京周边\n ### 旅游手册\n\n  + 景区\n  + 线路\n  + 酒店\n  + 北京老字号\n  + 开放日\n  + 虚拟导游\n  + 旅游行业信用信息\n  + 旅行社\n  + 一日游\n ### 视觉北京;)\n\n  + 图片\n  + 视频\n ### 《旅游》杂志\n ### 环游号\n ### 互动咨询;)\n\n  + 电子政务网\n  + 咨询站\n\n# 下雨天 北京最好玩的11个好去处\n\n 2017-07-26 18:05:40\n 北京旅游网\n\n故宫\n\n蓝天下的故宫是一番景象，雨中的故宫是另一番色彩，故宫的雨，不经意间凝固了岁月，惊艳了时光，让故宫里的一切变得素净清雅。\n\n颐和园\n\n都说雨中的荷花很美，自古以来也有很多赞美雨荷的诗句，可我们却很少有机会去欣赏。趁着这几天的雨，如能抽出时间来，静静地品味着这烟雨荷塘，暂时忘却这城市的喧嚣，甚好。\n\n古北水镇\n\n古北水镇被称作北方的江南水乡，鳞次栉比的房屋、青石板的老街、悠长的胡同，古朴、典雅、风景如画。古镇有两个时候去最美，一是下雪的时候，二是下雨的时候，说不定你会遇到一个打着油纸伞的姑娘。\n\n什刹海\n\n下着小雨的北京，最适合去什刹海了。这个时候，什刹海的湖景便朦胧起来了。烟雨濛濛，泛舟湖上，想想都很浪漫。\n\n中国国家博物馆\n\n中国国家博物馆的知名度无须赘述，每到节假日，来自世界各地的人都会到这里看一看。在雨天，逛一逛中国国家博物馆，感受一下这座历史与艺术并重的综合性国家博物馆吧，肯定有一番收获。 [...] 分享到微信朋友圈\n\nx\n\n打开微信，点击底部的“发现”，  \n使用“扫一扫”即可将网页分享至朋友圈。\n\n#### 短信获取验证码\n\n用户无需注册即可快捷登录，登录后可申请成为作家\n\n编辑推荐\n\n 1北京市一周演出预告（3月9日-15日）\n 2一定要来北京感受花开满城的浪漫，共探京城春晓\n 32026年北京市非物质文化遗产保护工作会召开\n 4不止司马台长城免票！北京“三八”妇女节活动汇总来了——\n 53月9日天安门广场升旗仪式观看指南\n 6演艺新空间 | 开心麻花A99剧场：隆福寺商圈里的演艺新空间\n 7快看！开了开了！北京3月花海预报——\n 83月8日天安门广场升旗仪式观看指南\n 9美不胜收！北京“迎春第一花”盛放\n 103月7日天安门广场升旗仪式观看指南\n\n关于北京旅游网/商务合作/网站声明/隐私政策/联系我们\n\n北京旅游网京ICP备17049735号-1京公网安备 11010502035003号",
#       "score": 0.94417685,
#       "raw_content": null,
#       "favicon": "https://r1.visitbeijing.com.cn/images/a4c09cdee78007d1ee26039bd25dc440.ico"
#     },
#     {
#       "url": "https://www.tour-beijing.com/chinese/10_major_attractions_in_beijing/",
#       "title": "北京十大旅游景点: 故宫、天坛、颐和园、八达岭长城 - Beijing Tour",
#       "content": "更多信息...\n\n首页 » 北京十大旅游景点\n\n北京十大旅游景点\n\n  北京是中国六朝古都，有着800多年的建城历史,是一座古老的现代化大都市。北京有6处世界文化遗产 - 故宫、天坛、颐和园、八达岭长城、定陵、长陵。此外，对外开放的旅游景点达200多处，其中有150个A级景点，分布在北京市区及所管辖的郊区县。有些重要的名胜古迹就在市区，您可以走着去游览；有些景点在近郊或远郊区，您可以搭乘旅游公交车，出租车或包车前往参观游览。北京具有丰富的旅游资源，有世界上最大的皇宫紫禁城、祭天神庙天坛、皇家花园北海、皇家园林颐和园，还有八达岭、慕田峪、箭扣长城，黄花城，司马台长城以及世界上最大的四合院恭王府，北京特色的胡同等各胜古迹。全市共有文物古迹7309项，其中国家文物保护单位42个，市级文物保护单位222个。  \n   \n   北京市目前每年接待国内旅游人数约4000万；海外入境旅游人数400万多万。其中大部分旅游者是第一次来北京。来北京的旅游观光者一般在北京停留时间为3-5天。如何有限的时间内参观最有价值的旅游景点，比较完整地了解北京，将是每个旅游者事先必须做的功课。北京旅游网根据20年的北京旅游经营和管理经验，加上多年的旅游数据，为广大第一次来北京参观游览的观光客推荐了北京10大旅游景点。当然，我们的推荐只能给您起一定的参考。原因很简单，每人的兴趣爱好不同，选择自己喜好的名胜古迹也不同。因此，我们欢迎广大旅游爱好者将你们心中的北京旅游10大景点发给我们(/cdn-cgi/l/email-protection#cebabcafb8aba28ebaa1bbbce3acaba7a4a7a0a9e0ada1a3)。我们将会在本页发表您的文章，供大家参考。  \n   \n  \n\n北京主要旅游景点及分布图 [...] ### 九、什刹海胡同：北京城享誉盛名的曆史文化旅游风景区\n\n 门票价格: 胡同游：50-100；恭王府及花园40、宋庆龄故居20、郭沫若纪念馆20、锺鼓楼10、德胜门箭楼10\n 开放时间: 9：00－18:00\n 地理位置及周围景观: 位于北京城区中轴线的西北部，东起地安门外大街北侧；南自地安门西大街向西至龙头井向西北接柳荫街、羊房胡同、新街口东街到新街口北大街，西自新街口北大街向北到新街口豁口；北自新街口豁口向东到德胜门，由德胜门沿鼓楼西大街到锺、鼓楼。景区中三海水面达33.6公顷(约占总面积的23％)。\n 交通线路: 乘13、107、111、118、701、850路北海北门站下\n 温馨小提示: 什刹海是了解北京古老的过去最佳大地方，您要预留至少半天的时间。\n\n  \n\n### 十、雍和宫：全国除西藏地区以外，保存最完整、规模最大的一处喇嘛教寺庙雍和宫\n\n 门票价格: 25元，学生可凭证半价\n 开放时间: 09：00-17：00\n 地理位置及周围景观: 北京东城区雍和宫大街12号。西面是成贤街，成贤街上有国子监，孔庙等；北面穿过二环路是地坛。\n 交通线路: 公交13、62、116、807等可达，也可乘地铁直达。\n 温馨小提示: 雍和宫是北京地铁唯一用景点命名的地铁站。 庙内可以烧香。\n\ntop\n\n  \n   \n\n2、如何根据您在北京的天数来安排北京旅游景点？ [...] | 慕田峪长城 | 幽谷神潭风景区 | 红螺寺 | 青龙峡 | 雁栖湖 |  |  |\n| 密云县： |\n| 金山岭长城 | 司马台长城 | 黑龙潭 |  |  |  |  |\n| 昌平区： |\n| 居庸关长城 | 明皇蜡像宫 | 北京雪世界滑雪场 | 军都山滑雪场 | 天龙源温泉花园 |  |  |\n| 延庆县： |\n| 古崖居 | 康西草原 | 龙庆峡 |  |  |  |  |\n| 北京周边地区： |\n| 清东陵 | 避暑山庄 | 清西陵 |  |  |  |  |",
#       "score": 0.929951,
#       "raw_content": null,
#       "favicon": "https://tour-beijing.com/favicon.ico"
#     },
#     {
#       "url": "https://weather.cma.cn/web/weather/54511.html",
#       "title": "北京 - 中国气象局-天气预报-城市预报",
#       "content": "1. 首页\n2. 国内\n3. 北京\n4. 北京\n\n 国内\n 国外\n\n|\n\n 北京市\n 天津市\n 河北省\n 山西省\n 内蒙古自治区\n 辽宁省\n 吉林省\n 黑龙江省\n 上海市\n 江苏省\n 浙江省\n 安徽省\n 福建省\n 江西省\n 山东省\n 河南省\n 湖北省\n 湖南省\n 广东省\n 广西壮族自治区\n 海南省\n 重庆市\n 四川省\n 贵州省\n 云南省\n 西藏自治区\n 陕西省\n 甘肃省\n 青海省\n 宁夏回族自治区\n 新疆维吾尔自治区\n 香港特别行政区\n 澳门特别行政区\n 台湾省\n\n|\n\n 顺义\n 北京\n 大兴\n 密云\n 平谷\n 延庆\n 怀柔\n 房山\n 昌平\n 通州\n 门头沟\n 丰台\n 朝阳\n 海淀\n 石景山\n\n更新\n\n7天天气预报（2026/03/13 12:00发布）\n\n星期五   \n03/13\n\n小雨\n\n南风\n\n微风\n\n8℃\n\n4℃\n\n小雨\n\n东北风\n\n微风\n\n星期六   \n03/14\n\n多云\n\n南风\n\n微风\n\n10℃\n\n0℃\n\n晴\n\n微风\n\n星期日   \n03/15\n\n晴\n\n西南风\n\n微风\n\n0℃\n\n晴\n\n西南风\n\n微风\n\n星期一   \n03/16\n\n晴\n\n南风\n\n微风\n\n13℃\n\n0℃\n\n晴\n\n微风\n\n星期二   \n03/17\n\n多云\n\n西南风\n\n微风\n\n晴\n\n星期三   \n03/18\n\n多云\n\n南风\n\n微风\n\n13℃\n\n1℃\n\n西南风\n\n微风\n\n星期四   \n03/19\n\n阴\n\n北风\n\n微风\n\n多云\n\n东北风\n\n微风 [...] |  |  |  |  |  |  |  |  |  |\n ---  ---  ---  --- \n| 时间 | 08:00 | 11:00 | 14:00 | 17:00 | 20:00 | 23:00 | 02:00 | 05:00 |\n| 天气 |\n| 气温 | 7.8℃ | 8.2℃ | 10.2℃ | 9.1℃ | 6.5℃ | 5.1℃ | 3.6℃ | 0.2℃ |\n| 降水 | 0.1mm | 无降水 | 无降水 | 无降水 | 无降水 | 无降水 | 无降水 | 无降水 |\n| 风速 | 2.6m/s | 3.1m/s | 2.4m/s | 1.9m/s | 3.3m/s | 3.3m/s | 2.8m/s | 2.4m/s |\n| 风向 | 东北风 | 东北风 | 东南风 | 西南风 | 西南风 | 西南风 | 西南风 | 西南风 |\n| 气压 | 1034.4hPa | 1034.9hPa | 1032.7hPa | 1032hPa | 1032.5hPa | 1032.6hPa | 1031.9hPa | 1031.7hPa |\n| 湿度 | 46.7% | 28.6% | 39.5% | 44.5% | 45.6% | 66.1% | 82.9% | 95.1% |\n| 云量 | 99.2% | 79.9% | 79.9% | 79.9% | 65.2% | 10% | 10% | 0% | [...] |  |  |  |  |  |  |  |  |  |\n ---  ---  ---  --- \n| 时间 | 08:00 | 11:00 | 14:00 | 17:00 | 20:00 | 23:00 | 02:00 | 05:00 |\n| 天气 |\n| 气温 | 3.1℃ | 8.6℃ | 13.2℃ | 13℃ | 10℃ | 5.7℃ | 3.3℃ | 0.1℃ |\n| 降水 | 无降水 | 无降水 | 无降水 | 无降水 | 无降水 | 无降水 | 无降水 | 无降水 |\n| 风速 | 2.8m/s | 1.7m/s | 1.9m/s | 3.3m/s | 1.6m/s | 3.3m/s | 2.5m/s | 2.3m/s |\n| 风向 | 西南风 | 西南风 | 西南风 | 西南风 | 西南风 | 西南风 | 西南风 | 西南风 |\n| 气压 | 1032.7hPa | 1032.2hPa | 1029hPa | 1027.5hPa | 1028.2hPa | 1028.3hPa | 1027.6hPa | 1027.1hPa |\n| 湿度 | 61.6% | 29.2% | 40% | 43.7% | 49.7% | 54.5% | 64.4% | 71.7% |\n| 云量 | 2.7% | 2.4% | 0.9% | 2.8% | 3% | 2.2% | 0.2% | 0% |",
#       "score": 0.8558512,
#       "raw_content": null,
#       "favicon": "http://weather.cma.cn/assets/favicon.ico"
#     }
#   ],
#   "response_time": 1.69,
#   "request_id": "2a92de5d-3780-4985-b467-9127b52b80ec"
# }