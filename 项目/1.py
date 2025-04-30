import os
import time
import random
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from db_manager import DatabaseManager
from config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cnki_spider.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("cnki_spider")

class CNKISpider:
    def __init__(self, config):
        self.config = config
        self.db_manager = DatabaseManager(config.db_config)
        self.setup_browser()
        self.download_dir = config.download_dir
        
        # 确保下载目录存在
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
    
    def setup_browser(self):
        """配置并初始化浏览器"""
        chrome_options = Options()
        
        # 配置Chrome下载设置
        prefs = {
            "download.default_directory": os.path.abspath(self.config.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True  # 不在浏览器中预览PDF
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 随机生成User-Agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36"
        ]
        chosen_agent = random.choice(user_agents)
        chrome_options.add_argument(f"user-agent={chosen_agent}")
        logger.info(f"使用User-Agent: {chosen_agent}")

        if self.config.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # 添加更多的伪装参数
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--lang=zh-CN")
        
        # 使用webdriver-manager自动管理驱动程序
        service = Service(ChromeDriverManager().install())
        self.browser = webdriver.Chrome(service=service, options=chrome_options)
        
        # 注入JS来隐藏WebDriver特征
        self.browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 覆盖 navigator.plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // 覆盖 navigator.languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en-US', 'en']
            });
            
            // 隐藏自动化工具特征
            window.chrome = {
                runtime: {}
            };
            """
        })

        # 使用webdriver-manager自动管理驱动程序
        service = Service(ChromeDriverManager().install())
        self.browser = webdriver.Chrome(service=service, options=chrome_options)
        self.browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
            """
        })

    def login_with_cookies(self):
        """使用Cookie登录知网"""
        logger.info("尝试使用Cookie登录")
        
        cookie_file = 'cnki_cookies.pkl'
        if not os.path.exists(cookie_file):
            logger.error(f"Cookie文件不存在: {cookie_file}")
            logger.info("请先运行 save_cookies.py 生成Cookie")
            return False
        
        try:
            # 先访问知网首页
            self.browser.get("https://www.cnki.net/")
            time.sleep(2)
            
            # 加载Cookie
            import pickle  # 添加到文件顶部的导入部分
            with open(cookie_file, 'rb') as f:
                cookies = pickle.load(f)
            
            # 添加Cookie到浏览器
            for cookie in cookies:
                # 有些cookie无法直接添加，需要处理
                try:
                    # 删除可能导致问题的属性
                    if 'expiry' in cookie:
                        del cookie['expiry']
                    self.browser.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"添加Cookie时出错: {e}")
            
            # 刷新页面使Cookie生效
            self.browser.refresh()
            time.sleep(3)
            
            # 截图
            self.browser.save_screenshot("cookie_login.png")
            
            # 检查是否登录成功
            success_indicators = [
                ".username", 
                ".user-name",
                "#header1_divUserInfo",
                "//span[contains(text(), '退出')]",
                "//a[contains(text(), '退出')]",
                "//a[contains(@href, 'logout')]"
            ]
            
            for selector in success_indicators:
                try:
                    if selector.startswith("//"):
                        element = WebDriverWait(self.browser, 5).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                    else:
                        element = WebDriverWait(self.browser, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    logger.info(f"Cookie登录成功，找到标识: {selector}")
                    return True
                except Exception:
                    pass
            
            logger.warning("Cookie可能已过期，登录失败")
            return False
        except Exception as e:
            logger.error(f"使用Cookie登录出错: {e}")
            return False
    
    def login(self):
            """登录知网"""
            logger.info("开始登录知网")
            try:
                # 先访问首页
                self.browser.get("https://www.cnki.net/")
                time.sleep(2)  # 给页面加载一些时间
                
                # 截图调试
                self.browser.save_screenshot("homepage.png")
                logger.info("已截图首页: homepage.png")
                
                # 尝试多种定位方式找到登录入口
                login_selectors = [
                    ".laylocate",                 # 原选择器
                    "#header1_divLogin",          # 另一种可能的选择器
                    ".login-btn", 
                    "a[href*='login']",           # 包含login的链接
                    "//a[contains(text(), '登录')]"  # XPath: 包含"登录"文本的链接
                ]
                
                login_btn = None
                for selector in login_selectors:
                    try:
                        logger.info(f"尝试使用选择器: {selector}")
                        if selector.startswith("//"):
                            # XPath 选择器
                            login_btn = WebDriverWait(self.browser, 5).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            # CSS 选择器
                            login_btn = WebDriverWait(self.browser, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        if login_btn:
                            logger.info(f"成功找到登录按钮: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"选择器 {selector} 未找到登录按钮: {e}")
                
                if not login_btn:
                    logger.error("无法找到登录按钮")
                    return False
                    
                # 点击登录按钮
                login_btn.click()
                time.sleep(2)
                
                # 截图调试
                self.browser.save_screenshot("login_page.png")
                logger.info("已截图登录页面: login_page.png")
                
                # 检查当前URL，确认是否进入了登录页面
                current_url = self.browser.current_url
                logger.info(f"当前URL: {current_url}")
                
                # 尝试查找用户名和密码输入框
                username_selectors = ["#userName", "input[name='username']", "input[placeholder*='用户名']"]
                password_selectors = ["#password", "input[name='password']", "input[type='password']"]
                
                # 定位用户名输入框
                username_input = None
                for selector in username_selectors:
                    try:
                        username_input = WebDriverWait(self.browser, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if username_input:
                            logger.info(f"找到用户名输入框: {selector}")
                            break
                    except:
                        pass
                
                if not username_input:
                    logger.error("找不到用户名输入框")
                    return False
                
                # 定位密码输入框
                password_input = None
                for selector in password_selectors:
                    try:
                        password_input = WebDriverWait(self.browser, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if password_input:
                            logger.info(f"找到密码输入框: {selector}")
                            break
                    except:
                        pass
                
                if not password_input:
                    logger.error("找不到密码输入框")
                    return False
                
                # 输入用户名密码
                username_input.clear()
                username_input.send_keys(self.config.username)
                password_input.clear()
                password_input.send_keys(self.config.password)
                
                # 查找登录按钮
                login_button_selectors = [
                    ".btn-login", 
                    "input[type='submit']", 
                    "button[type='submit']",
                    "//button[contains(text(), '登录')]",
                    "//input[@value='登录']"
                ]
                
                login_submit = None
                for selector in login_button_selectors:
                    try:
                        if selector.startswith("//"):
                            login_submit = WebDriverWait(self.browser, 5).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            login_submit = WebDriverWait(self.browser, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        if login_submit:
                            logger.info(f"找到登录提交按钮: {selector}")
                            break
                    except:
                        pass
                
                if not login_submit:
                    logger.error("找不到登录提交按钮")
                    return False
                
                # 点击登录
                login_submit.click()
                
                # 等待一段时间，看是否有验证码或其他提示
                time.sleep(5)
                
                # 截图调试
                self.browser.save_screenshot("after_login.png")
                logger.info("已截图登录后页面: after_login.png")
                
                # 检查是否登录成功
                success_indicators = [
                    ".username", 
                    ".user-name",
                    "#header1_divUserInfo",
                    "//span[contains(text(), '退出')]",
                    "//a[contains(text(), '退出')]",
                    "//a[contains(@href, 'logout')]"
                ]
                
                for selector in success_indicators:
                    try:
                        if selector.startswith("//"):
                            WebDriverWait(self.browser, 5).until(
                                EC.presence_of_element_located((By.XPATH, selector))
                            )
                        else:
                            WebDriverWait(self.browser, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                        logger.info(f"登录成功，找到标识: {selector}")
                        return True
                    except:
                        pass
                
                # 如果没有找到成功标识，检查是否有错误信息
                try:
                    error_message = self.browser.find_element(By.CSS_SELECTOR, ".login-error-msg").text
                    logger.error(f"登录失败，错误信息: {error_message}")
                except:
                    logger.error("登录失败，无法找到成功标识")
                
                return False
                    
            except Exception as e:
                logger.error(f"登录过程中出错: {e}")
                self.browser.save_screenshot("login_error.png")
                logger.info("已截图错误状态: login_error.png")
                return False
            
    def search(self, query, filters=None):
        """
        执行搜索查询
        query: 查询关键词
        filters: 额外的过滤条件，如发表年份、来源类别等
        """
        logger.info(f"开始搜索: {query}")
        self.browser.get("https://www.cnki.net/")
        time.sleep(3)  # 增加等待时间确保页面加载
        
        # 截图调试
        self.browser.save_screenshot(f"search_page_{query}.png")
        
        # 输入搜索关键词 - 更新为新的ID: txt_search
        search_selectors = ["#txt_search", ".search-input", "#SearchText", "#txt_SearchText"]
        
        search_input = None
        for selector in search_selectors:
            try:
                search_input = WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if search_input:
                    logger.info(f"找到搜索框: {selector}")
                    break
            except Exception as e:
                logger.debug(f"搜索框选择器 {selector} 未找到: {e}")
        
        if not search_input:
            logger.error("无法找到搜索框")
            raise Exception("无法找到搜索框")
            
        search_input.clear()
        search_input.send_keys(query)
        
        # 点击搜索按钮
        search_btn_selectors = [".search-btn", "#search-btn", "input[type='button'].search-btn"]
        
        search_btn = None
        for selector in search_btn_selectors:
            try:
                search_btn = WebDriverWait(self.browser, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if search_btn:
                    logger.info(f"找到搜索按钮: {selector}")
                    break
            except Exception as e:
                logger.debug(f"搜索按钮选择器 {selector} 未找到: {e}")
        
        if not search_btn:
            logger.error("无法找到搜索按钮")
            raise Exception("无法找到搜索按钮")
            
        search_btn.click()
        
        # 等待搜索结果加载 - 多种可能的选择器
        result_page_selectors = [
            ".result-table-list", 
            ".search-result",
            ".list-item",
            "#ModuleSearchResult",
            ".module-result"
        ]
        
        for selector in result_page_selectors:
            try:
                WebDriverWait(self.browser, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                logger.info(f"搜索结果已加载，匹配选择器: {selector}")
                break
            except Exception as e:
                logger.debug(f"结果页选择器 {selector} 未找到: {e}")
        
        # 保存搜索结果页面以便分析
        self.browser.save_screenshot(f"search_result_{query}.png")
        
        # 保存页面源码以供分析
        with open(f"search_result_{query}.html", "w", encoding="utf-8") as f:
            f.write(self.browser.page_source)
        
        logger.info("已保存搜索结果页面截图和源代码")
    
    def get_search_results(self, max_pages=1):
        """
        获取搜索结果列表
        max_pages: 最多爬取的页数
        """
        results = []
        current_page = 1
        
        while current_page <= max_pages:
            logger.info(f"正在爬取第 {current_page} 页")
            
            # 截图调试
            self.browser.save_screenshot(f"page_{current_page}.png")
            
            # 等待页面完全加载
            time.sleep(3)
            
            # 2025年知网新版本的结果项选择器
            result_item_selectors = [
                ".result-table-list tr",                # 新版选择器
                ".data-table tbody tr",                 # 新版可能的选择器
                "#gridTable tr",                        # 可能的新表格选择器
                "tbody .odd, tbody .even",              # 常见的表格行选择器
                "#ModuleSearchResult div[class*='item']", # 通用选择器
                ".result-list div[class*='item']"       # 通用选择器
            ]
            
            items = []
            for selector in result_item_selectors:
                try:
                    logger.info(f"尝试使用选择器: {selector}")
                    # 增加等待时间确保元素已加载
                    WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    items = self.browser.find_elements(By.CSS_SELECTOR, selector)
                    if items:
                        # 排除表头行
                        if "tr" in selector:
                            items = [item for item in items if "表头" not in item.get_attribute("class") 
                                    and "title" not in item.get_attribute("class")]
                        
                        logger.info(f"使用选择器 {selector} 找到 {len(items)} 个结果")
                        break
                except Exception as e:
                    logger.debug(f"选择器 {selector} 查找失败: {e}")
            
            if not items:
            # 如果仍未找到，尝试使用JavaScript检查页面内容
                try:
                    # 使用JS获取页面内的文本内容
                    page_text = self.browser.execute_script(
                        "return document.body.innerText"
                    )
                    
                    if "没有找到相关结果" in page_text:
                        logger.warning("页面显示没有找到相关结果")
                    elif "请输入检索词" in page_text:
                        logger.warning("页面提示需要输入检索词")
                    else:
                        # 检查是否由于登录失效导致的问题
                        if "请登录" in page_text:
                            logger.error("登录状态已失效，请重新登录")
                        else:
                            logger.warning("未找到任何结果项，但页面加载正常，可能是选择器不匹配")
                    
                    # 保存页面源码
                    with open(f"page_source_{current_page}.html", "w", encoding="utf-8") as f:
                        f.write(self.browser.page_source)
                    logger.info(f"已保存页面源码: page_source_{current_page}.html")
                except Exception as e:
                    logger.error(f"执行JavaScript检查失败: {e}")
                
                break
            
            # 处理每个结果项
            for item in items:
                try:
                    # 使用多种可能的选择器提取标题和链接
                    title_selectors = [
                        "a.fz14",                    # 新版知网标题选择器
                        ".name a",                   # 可能的标题选择器
                        ".text a",                   # 可能的标题选择器
                        "td a.left",                 # 表格中的左对齐链接
                        "a[href*='detail']",         # 包含detail的链接
                        "a"                          # 通用选择器
                    ]
                    
                    # 提取标题和链接
                    title = ""
                    link = ""
                    for selector in title_selectors:
                        try:
                            title_elems = item.find_elements(By.CSS_SELECTOR, selector)
                            for title_elem in title_elems:
                                title_text = title_elem.text.strip()
                                link_href = title_elem.get_attribute("href")
                                # 过滤无效链接或按钮
                                if (title_text and link_href and 
                                    "javascript:" not in link_href and
                                    len(title_text) > 5):  # 标题应该有一定长度
                                    title = title_text
                                    link = link_href
                                    break
                            if title and link:
                                break
                        except:
                            continue
                    
                    if not title or not link:
                        # 如果常规方法失败，使用JavaScript提取
                        try:
                            title_script = """
                            var row = arguments[0];
                            var links = row.getElementsByTagName('a');
                            for(var i=0; i<links.length; i++) {
                                var link = links[i];
                                if(link.textContent.length > 5 && link.href.indexOf('detail') > -1) {
                                    return {text: link.textContent.trim(), href: link.href};
                                }
                            }
                            return null;
                            """
                            result = self.browser.execute_script(title_script, item)
                            if result:
                                title = result['text']
                                link = result['href']
                        except Exception as js_error:
                            logger.debug(f"JavaScript提取失败: {js_error}")
                    
                    if not title or not link:
                        logger.warning("无法提取标题或链接，跳过此项")
                        continue
                    
                    # 提取其他信息（作者、来源、日期）
                    authors = self.extract_text(item, [".author", ".writers", "td:nth-child(3)"])
                    source = self.extract_text(item, [".source", ".journal", "td:nth-child(4)"])
                    date = self.extract_text(item, [".date", ".year", "td:nth-child(5)"])
                    
                    # 创建结果对象
                    result = {
                        "title": title,
                        "authors": authors,
                        "source": source,
                        "date": date,
                        "link": link,
                        "download_url": None,
                        "local_path": None
                    }
                    
                    results.append(result)
                    logger.info(f"已提取文献: {title}")
                    
                except Exception as e:
                    logger.error(f"提取文献信息失败: {e}")
            
            logger.info(f"当前页面共提取 {len(results)} 条文献信息")
            
            # 如果这一页有结果，继续检查下一页
            if len(results) > 0:
            
                # 尝试找到下一页按钮
                next_page_found = False
                next_page_selectors = [
                    ".next-page", 
                    ".next a", 
                    ".page-next",
                    ".pagination .next",
                    "//a[contains(text(), '下一页')]"
                ]
                
                for selector in next_page_selectors:
                    try:
                        if selector.startswith("//"):
                            next_page = self.browser.find_element(By.XPATH, selector)
                        else:
                            next_page = self.browser.find_element(By.CSS_SELECTOR, selector)
                        
                        # 检查是否可点击
                        if next_page and "disabled" not in next_page.get_attribute("class"):
                            logger.info(f"找到下一页按钮: {selector}")
                            next_page.click()
                            current_page += 1
                            next_page_found = True
                            # 等待新页面加载
                            time.sleep(random.uniform(3, 5))
                            break
                    except Exception as e:
                        logger.debug(f"下一页选择器 {selector} 查找失败: {e}")
                
                if not next_page_found:
                    logger.info("没有下一页或已到达最后一页")
                    break
            
            logger.info(f"共获取到 {len(results)} 条文献信息")
        return results
    
    def extract_text(self, parent_element, selectors):
        """辅助方法：从元素中提取文本"""
        for selector in selectors:
            try:
                element = parent_element.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text:
                    return text
            except:
                pass
        return ""   
     
    def download_document(self, document_info):
        """
        下载单个文档
        document_info: 包含文档元数据和链接的字典
        """
        try:
            # 打开文献详情页
            self.browser.get(document_info["link"])
            
            # 截图调试
            self.browser.save_screenshot(f"detail_{document_info['title'][:10]}.png")
            
            # 等待详情页加载
            detail_selectors = [
                ".docinfo-actions",
                ".operate-btn",
                ".btn-dlpdf",
                ".download-btn"
            ]
            
            download_btn = None
            for selector in detail_selectors:
                try:
                    # 等待元素出现
                    WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    
                    # 找到下载按钮
                    download_selectors = [
                        ".btn-dlpdf", 
                        ".operate-btn .btn-download",
                        ".download-btn", 
                        "a[title='下载']",
                        "//a[contains(text(), '下载')]"
                    ]
                    
                    for dl_selector in download_selectors:
                        try:
                            if dl_selector.startswith("//"):
                                download_btn = self.browser.find_element(By.XPATH, dl_selector)
                            else:
                                download_btn = self.browser.find_element(By.CSS_SELECTOR, dl_selector)
                            
                            if download_btn:
                                logger.info(f"找到下载按钮: {dl_selector}")
                                break
                        except:
                            pass
                    
                    if download_btn:
                        break
                except Exception as e:
                    logger.debug(f"选择器 {selector} 未找到: {e}")
            
            if not download_btn:
                logger.error("无法找到下载按钮")
                with open(f"detail_page_{document_info['title'][:10]}.html", "w", encoding="utf-8") as f:
                    f.write(self.browser.page_source)
                return None
            
            # 点击下载按钮
            download_btn.click()
            
            # 等待下载对话框
            time.sleep(2)
            
            # 处理可能的下载选项对话框
            try:
                dialog_selectors = [
                    ".download-dialog",
                    ".pdf-dialog",
                    ".download-options"
                ]
                
                for selector in dialog_selectors:
                    try:
                        dialog = WebDriverWait(self.browser, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        logger.info(f"找到下载对话框: {selector}")
                        
                        # 选择PDF格式(如果有选择)
                        pdf_selectors = [
                            ".download-item[data-format='PDF']",
                            "input[value='PDF']",
                            ".pdf-option"
                        ]
                        
                        for pdf_selector in pdf_selectors:
                            try:
                                pdf_option = dialog.find_element(By.CSS_SELECTOR, pdf_selector)
                                pdf_option.click()
                                logger.info("已选择PDF格式")
                                break
                            except:
                                pass
                        
                        # 点击确认下载按钮
                        confirm_selectors = [
                            ".download-dialog .btn-primary",
                            ".pdf-dialog .confirm",
                            ".download-options .submit",
                            "input[type='submit']",
                            "button.confirm"
                        ]
                        
                        for confirm_selector in confirm_selectors:
                            try:
                                confirm_btn = dialog.find_element(By.CSS_SELECTOR, confirm_selector)
                                confirm_btn.click()
                                logger.info("已点击确认下载")
                                break
                            except:
                                pass
                        
                        break
                    except:
                        pass
            except Exception as e:
                logger.debug(f"处理下载对话框失败: {e}，可能直接下载")
            
            # 等待下载完成(延长等待时间)
            time.sleep(8)  
            
            # 检查下载目录中最新的文件
            files = [f for f in os.listdir(self.download_dir) if os.path.isfile(os.path.join(self.download_dir, f))]
            if not files:
                logger.warning(f"下载目录中没有文件: {self.download_dir}")
                return None
                    
            files.sort(key=lambda x: os.path.getmtime(os.path.join(self.download_dir, x)), reverse=True)
            latest_file = files[0]
            
            # 更新文档信息中的本地路径
            document_info["local_path"] = os.path.join(self.download_dir, latest_file)
            logger.info(f"文档已下载: {document_info['local_path']}")
            
            return document_info
        except Exception as e:
            logger.error(f"下载文档失败: {e}")
            return None
    
    def bulk_download(self, results, max_downloads=None):
        """批量下载文档"""
        if not results:
            logger.warning("没有搜索结果可供下载")
            return []
            
        downloaded = []
        count = 0
        max_count = max_downloads if max_downloads else len(results)
        
        for result in results:
            if count >= max_count:
                break
                
            logger.info(f"正在下载第 {count+1}/{max_count} 个文档: {result['title']}")
            download_result = self.download_document(result)
            
            if download_result:
                downloaded.append(download_result)
                # 更新数据库
                self.db_manager.insert_document(download_result)
                count += 1
                
                # 添加随机延迟，避免被封
                delay = random.uniform(3, 8)
                logger.debug(f"等待 {delay:.2f} 秒后继续...")
                time.sleep(delay)
            else:
                logger.warning(f"文档下载失败: {result['title']}")
                
        logger.info(f"下载完成，共下载 {len(downloaded)}/{max_count} 个文档")
        return downloaded
        
    def close(self):
        """关闭浏览器和数据库连接"""
        if hasattr(self, 'browser'):
            self.browser.quit()
        if hasattr(self, 'db_manager'):
            self.db_manager.close()
        logger.info("爬虫资源已释放")

def main():
    # 加载配置
    config = Config()
    
    try:
        spider = CNKISpider(config)
        
        # 先尝试使用Cookie登录
        login_success = spider.login_with_cookies()
        
        # 如果Cookie登录失败，再尝试表单登录
        if not login_success:
            logger.info("Cookie登录失败，尝试使用常规方式登录...")
            login_success = spider.login()
        
        if not login_success:
            logger.error("所有登录方式均失败，程序终止")
            return
        
        keywords = [
            "人工智能",
            "机器学习",
            "深度学习",
            "数据挖掘",
            "神经网络",
            "纤维"
        ]

        for keyword in keywords:
            logger.info(f"开始处理关键词: {keyword}")
            
            # 搜索
            spider.search(keyword, filters=config.search_filters)
            
            # 获取搜索结果
            results = spider.get_search_results(max_pages=config.max_pages)
            
            # 下载文档
            spider.bulk_download(results, max_downloads=config.max_downloads_per_keyword)
            
            # 添加延迟
            time.sleep(random.uniform(5, 10))
    
    except Exception as e:
        logger.error(f"程序执行出错: {e}", exc_info=True)
    finally:
        if 'spider' in locals():
            spider.close()
        
if __name__ == "__main__":
    main()