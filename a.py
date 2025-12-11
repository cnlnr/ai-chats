from playwright.sync_api import sync_playwright

# 上下文管理器：自动管理浏览器的启动与关闭（推荐）
with sync_playwright() as p:
    # 1. 启动 Chromium 浏览器（默认无头模式，无界面）
    browser = p.chromium.launch(headless=False)

    # 2. 创建新的页面（标签页）
    page = browser.new_page()

    # 3. 执行操作（例如访问网页）
    page.goto("https://www.doubao.com")
    print("页面标题：", page.title())

    input("按回车退出")

    # 4. 关闭浏览器（上下文管理器会自动关闭，也可手动调用）
    browser.close()
