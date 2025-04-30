import pickle
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("cookie_saver")

def save_cookies():
    """手动登录并保存Cookie"""
    logger.info("=== 知网 Cookie 保存工具 ===")
    logger.info("请按照以下步骤操作:")
    logger.info("1. 程序将打开Chrome浏览器")
    logger.info("2. 请在浏览器中手动登录知网")
    logger.info("3. 登录成功后，按回车键继续")
    
    # 配置浏览器
    options = Options()
    options.add_argument("--window-size=1920,1080")
    
    # 添加一些伪装参数，减少被检测风险
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    service = Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=service, options=options)
    
    # 访问知网
    browser.get("https://www.cnki.net/")
    
    # 等待用户手动登录
    input("\n请完成登录后按回车键继续...")
    
    # 检查是否成功登录
    if "cnki.net" in browser.current_url:
        logger.info("检测到知网页面，正在保存Cookie...")
        cookies = browser.get_cookies()
        
        # 保存cookies
        with open('cnki_cookies.pkl', 'wb') as f:
            pickle.dump(cookies, f)
        
        logger.info(f"Cookie已保存到 cnki_cookies.pkl")
    else:
        logger.error("未检测到知网页面，可能登录失败")
    
    # 拍个页面快照
    browser.save_screenshot("logged_in.png")
    logger.info("已保存页面截图: logged_in.png")
    
    # 关闭浏览器
    browser.quit()

if __name__ == "__main__":
    save_cookies()