#!/usr/bin/eny python
# -*- coding: utf-8 -*-
"""
@Time    :2025/12/13 15:15
#Author  :Emcikem
@File    :playwright_browser.py
"""
import asyncio
import logging
from typing import Optional

from playwright.async_api import Playwright, Browser, Page, async_playwright

from app.domain.external.browser import Browser as BrowserProtocol
from app.domain.external.llm import LLM

logger = logging.getLogger(__name__)


class PlaywrightBrowser(BrowserProtocol):
    """基于Playwright管理的浏览器扩展"""

    def __init__(
            self,
            cdp_url: str,  # CDP的连接地址
            llm: Optional[LLM] = None,  # 可选参数，传递LLM，如果传递了则会使用LLM对页面内容进行整理变成Markdown格式
    ) -> None:
        """构造函数，完成playwright浏览器的初始化"""
        # LLM相关
        self.llm: Optional[LLM] = llm

        # 浏览器相关
        self.cdp_url: str = cdp_url
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def _ensure_browser(self) -> None:
        """确保浏览器存在，如果不存在则初始化"""
        if not self.browser or not self.page:
            if not await self.initialize():
                raise Exception("初始化Playwright浏览器失败")

    async def _ensure_page(self) -> None:
        """确保浏览器存在，如果不存在则新建"""
        # 1.先保证浏览器存在
        await self._ensure_browser()

        # 2.如果页面不存在则创建新上下文+页面
        if not self.page:
            self.page = await self.browser.new_page()  # 等同于self.browser.new_context().new_page()
        else:
            # 3.如果页面存在则提取所有上下文
            contexts = self.browser.contexts
            if contexts:
                # 4.获取默认上下文及页面
                default_context = contexts[0]
                pages = default_context.pages

                # 5.判定页面是否存在
                if pages:
                    # 6.获取当前最新页面(Chrome浏览器新增页面时，默认往右侧添加，相当于pages中序号较大的页面)
                    latest_page = pages[-1]

                    # 7.判定当前页面是否是最新页面，如果不是则更新
                    if self.page != latest_page:
                        self.page = latest_page

    async def initialize(self) -> bool:
        """初始化并确保资源是可用的"""
        # 1.定义重试次数+重试延迟确保资源存在
        max_retries = 3
        retry_interval = 1

        # 2.循环开始资源构建
        for attempt in range(max_retries):
            try:
                # 3.创建playwright上下文并连接到cdp浏览器
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)

                # 4.获取浏览器的所有上下文
                contexts = self.browser.contexts

                # 5.如果上下文存在，并且第一个上下文只有一个页面则执行如下逻辑
                if contexts and len(contexts[0].pages) == 1:
                    # 6.获取当前上下文的第一个页面
                    page = contexts[0].pages[0]

                    # 7.判定当前页面是不是空页面，如果是则直接使用page，否则新建一个
                    if (
                            not page.url or
                            page.url in
                            ["about:blank", "chrome://newtab/", "chrome://new-tab-page/"]
                    ):
                        self.page = page
                    else:
                        # 8.当前页面以及有数据则新建一个页面
                        self.page = await contexts[0].new_page()
                else:
                    # 9.上下文不存在或者页面不唯一则表示数据被污染，新建一个页面
                    context = contexts[0] if contexts else await self.browser.new_context()
                    self.page = await context.new_page()

                return True
            except Exception as e:
                # 10.清除所有资源
                await self.cleanup()

                # 11.判定重试次数是否等于最大重试次数
                if attempt == max_retries - 1:
                    logger.error(f"初始化playwright浏览器失败(已重试{max_retries}次)：{str(e)}")
                    return False

                # 12.使用指数级增长进行休眠，最大休眠时间为10s
                retry_interval = min(retry_interval * 2, 10)
                logger.warning(f"初始化playwright浏览器失败，即将进行第{attempt + 1}次重试: {str(e)}")
                await asyncio.sleep(retry_interval)

    async def cleanup(self) -> None:
        """清除playwright资源，包含浏览器+页面+playwright"""
        try:
            # 1.检测浏览器是否存在，如果存在则删除该浏览器下的所有tabs页面
            if self.browser:
                # 2.获取该浏览器的所有上下文
                contexts = self.browser.contexts
                if contexts:
                    # 3.循环遍历所有上下文逐个处理
                    for context in contexts:
                        # 4.获取每个上下文的所有页面
                        pages = context.pages
                        for page in pages:
                            # 5.循环遍历清除所有页面
                            if not page.is_closed():
                                await page.close()

            # 6.判定self.page是否关闭
            if self.page and not self.page.is_closed():
                await self.page.close()

            # 7.关闭浏览器
            if self.browser:
                await self.browser.close()

            # 8.停止playwright
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            # 9.记录错误日志
            logger.error(f"清理Playwright浏览器资源出错：{str(e)}")
        finally:
            # 10.重置所有资源
            self.page = None
            self.browser = None
            self.playwright = None

    async def wait_for_page_load(self, timeout: int = 15) -> bool:
        """传递超时时间，等待当前页面是否加载完毕"""
        # 1.确保当前页面存在
        await self._ensure_page()

        # 2.使用异步任务事件循环中的时间来作为开始时间(只和异步任务相关)
        start_time = asyncio.get_event_loop().time()
        check_interval = 5

        # 3.循环检测网页是否加载成功
        while asyncio.get_event_loop().time() - start_time < timeout:
            # 4.使用js代码判断网页是否加载成功
            is_completed = await self.page.evaluate("""() => document.readyState === 'complete'""")
            if is_completed:
                return True

            # 5.未加载成功则休眠对应时间
            await asyncio.sleep(check_interval)

        return False
