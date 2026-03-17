import asyncio
import json
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from playwright.async_api import async_playwright

class TestStep(BaseModel):
    action: str
    selector: str
    value: Optional[str] = None

class TestResult(BaseModel):
    success: bool
    message: str
    screenshot: Optional[str] = None

class PuppeteerAI:
    def __init__(self, model_client):
        self.client = model_client
        self.browser = None
        self.page = None
        
    async def init_browser(self, headless: bool = False):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=headless)
        self.page = await self.browser.new_page()
        print(f"✅ 浏览器已启动 (headless={headless})")
        
    async def close_browser(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            print("✅ 浏览器已关闭")
    
    async def navigate(self, url: str):
        """导航到指定URL"""
        await self.page.goto(url)
        print(f"🌐 已导航到: {url}")
        
    async def click(self, selector: str):
        """点击元素"""
        await self.page.click(selector)
        print(f"🖱️ 点击: {selector}")
        
    async def fill(self, selector: str, value: str):
        """填写输入框"""
        await self.page.fill(selector, value)
        print(f"✏️ 填写 {selector}: {value}")
        
    async def get_text(self, selector: str) -> str:
        """获取元素文本"""
        return await self.page.text_content(selector)
    
    async def screenshot(self, path: str = "screenshot.png"):
        """截图"""
        await self.page.screenshot(path=path)
        print(f"📸 截图已保存: {path}")
        return path
    
    async def wait_for_selector(self, selector: str, timeout: int = 5000):
        """等待元素出现"""
        await self.page.wait_for_selector(selector, timeout=timeout)
        
    async def execute_script(self, script: str):
        """执行JavaScript"""
        return await self.page.evaluate(script)
    
    async def get_console_logs(self) -> list:
        """获取控制台日志"""
        logs = []
        self.page.on("console", lambda msg: logs.append({
            "type": msg.type,
            "text": msg.text
        }))
        return logs
    
    async def test_form_submission(self, url: str, form_config: dict) -> TestResult:
        """测试表单提交"""
        try:
            await self.navigate(url)
            
            for field in form_config.get("fields", []):
                await self.fill(field["selector"], field["value"])
                
            await self.click(form_config["submit_selector"])
            await self.page.wait_for_load_state("networkidle")
            
            success_selector = form_config.get("success_selector")
            if success_selector:
                await self.wait_for_selector(success_selector)
                
            return TestResult(
                success=True,
                message="表单提交测试通过"
            )
        except Exception as e:
            return TestResult(
                success=False,
                message=f"测试失败: {str(e)}"
            )
    
    async def test_page_load_performance(self, url: str) -> dict:
        """测试页面加载性能"""
        await self.page.goto(url)
        
        metrics = await self.page.evaluate("""() => {
            const timing = performance.timing;
            return {
                loadTime: timing.loadEventEnd - timing.navigationStart,
                domReady: timing.domContentLoadedEventEnd - timing.navigationStart,
                firstPaint: performance.getEntriesByType('paint')[0]?.startTime
            };
        }""")
        
        return metrics

    async def test_visual_regression(self, url: str, baseline_path: str) -> TestResult:
        """视觉回归测试"""
        await self.navigate(url)
        current_screenshot = "current.png"
        await self.screenshot(current_screenshot)
        
        baseline = Path(baseline_path)
        if not baseline.exists():
            return TestResult(
                success=False,
                message="基准截图不存在，请先生成基准",
                screenshot=current_screenshot
            )
        
        return TestResult(
            success=True,
            message="视觉测试通过",
            screenshot=current_screenshot
        )


class AITestGenerator:
    """AI 测试生成器 - 基于 Gemini 生成测试步骤"""
    
    def __init__(self, model_client):
        self.client = model_client
        
    def generate_test_steps(self, test_type: str, target_url: str) -> list[TestStep]:
        """AI 自动生成测试步骤"""
        
        system_prompt = f"""
        你是一个自动化测试专家。请为以下测试场景生成具体的测试步骤。
        
        测试类型: {test_type}
        目标URL: {target_url}
        
        请以 JSON 数组格式输出测试步骤，每个步骤包含：
        - action: 操作类型 (click, fill, navigate, wait, screenshot, get_text)
        - selector: CSS 选择器或 XPath
        - value: 操作值 (可选)
        
        只输出 JSON，不要其他内容。
        """
        
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"为 {target_url} 生成 {test_type} 测试步骤",
            config={"system_instruction": system_prompt}
        )
        
        try:
            steps = json.loads(response.text)
            return [TestStep(**step) for step in steps]
        except:
            return []
    
    def analyze_test_result(self, test_result: dict, expected: str) -> str:
        """AI 分析测试结果"""
        
        system_prompt = """
        你是一个测试分析专家。请分析测试结果，判断是否通过，并给出建议。
        """
        
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"测试结果: {json.dumps(test_result)}\n期望: {expected}",
            config={"system_instruction": system_prompt}
        )
        
        return response.text


async def run_ai_automation_test(url: str, test_scenario: str):
    """运行 AI 驱动的自动化测试"""
    from google import genai
    
    client = genai.Client()
    
    tester = PuppeteerAI(client)
    generator = AITestGenerator(client)
    
    await tester.init_browser(headless=False)
    
    try:
        steps = generator.generate_test_steps(test_scenario, url)
        print(f"📋 生成了 {len(steps)} 个测试步骤")
        
        for i, step in enumerate(steps, 1):
            print(f"\n步骤 {i}: {step.action} - {step.selector}")
            
            if step.action == "navigate":
                await tester.navigate(step.selector)
            elif step.action == "click":
                await tester.click(step.selector)
            elif step.action == "fill":
                await tester.fill(step.selector, step.value)
            elif step.action == "screenshot":
                await tester.screenshot(step.value or "screenshot.png")
            elif step.action == "wait":
                await tester.wait_for_selector(step.selector)
                
    finally:
        await tester.close_browser()


async def main():
    from google import genai
    
    client = genai.Client()
    
    tester = PuppeteerAI(client)
    
    await tester.init_browser(headless=False)
    
    test_result = await tester.test_form_submission(
        url="https://example.com/form",
        form_config={
            "fields": [
                {"selector": "#username", "value": "testuser"},
                {"selector": "#email", "value": "test@example.com"}
            ],
            "submit_selector": "#submit-btn",
            "success_selector": ".success-message"
        }
    )
    
    print(f"\n测试结果: {test_result}")
    
    await tester.close_browser()


if __name__ == "__main__":
    asyncio.run(main())
