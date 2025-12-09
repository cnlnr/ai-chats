# install: pip install playwright
# setup: playwright install firefox  # 需要安装 Firefox 驱动

from playwright.sync_api import sync_playwright
from pathlib import Path

# 获取当前目录下的 index.html 文件路径
current_dir = Path.cwd()
index_file = current_dir / "index.html"

# 检查文件是否存在
if not index_file.exists():
    print(f"错误：文件不存在 - {index_file}")
    exit(1)

# 构建 file:// URL
file_url = f"file://{index_file.resolve()}"

# 启动浏览器
with sync_playwright() as p:
    browser = p.firefox.launch(headless=False)  # 改用 Firefox，headless=False 显示浏览器窗口
    page = browser.new_page()
    
    print(f"正在使用 Firefox 打开: {file_url}")
    page.goto(file_url)
    
    input()
    
    browser.close()