from playwright.sync_api import sync_playwright
from pathlib import Path

# 定义主页面路径（仅含无 ID iframe 标签）
index_file = Path.cwd() / "index.html"

# 启动 Playwright 同步实例
p = sync_playwright().start()

# 启动 Chromium 有头模式
browser = p.chromium.launch(headless=False)

# 创建新页面
page = browser.new_page()

# 访问本地主页面
page.goto(f"file://{index_file.resolve()}")  # 补充 resolve() 确保路径是绝对路径，避免兼容问题

# ========== 核心修改：获取无 ID iframe 内部渲染后的 HTML ==========
# 1. 等待主页面中的 iframe 元素加载完成（通过标签名定位无 ID iframe）
iframe_elem = page.wait_for_selector("iframe")  # 页面只有一个 iframe，直接用标签名定位

# 2. 切换到 iframe 的独立上下文（Frame 对象）
iframe_frame = iframe_elem.content_frame()

# 3. 等待 iframe 自身加载完成（确保内部内容渲染完毕，静态/动态内容都适用）
iframe_frame.wait_for_load_state("load")  # 等待 iframe 所有资源加载完成

# 4. 获取 iframe 内部渲染后的 HTML
iframe_html = iframe_frame.content()

# ========== 打印结果（对比主页面和 iframe 内容） ==========
print("===== 主页面的 HTML（仅含 iframe 标签） =====")
page_html = page.content()
print(page_html)

print("\n===== iframe 内部渲染后的 HTML =====")
print(iframe_html)

# ========== 关闭浏览器（优化规范：去掉分号，分两行写） ==========
input("按回车退出...")
browser.close()

# 停止 Playwright 实例（原代码遗漏，补充上避免资源泄漏）
p.stop()
