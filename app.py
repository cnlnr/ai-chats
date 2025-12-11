from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from pathlib import Path
import subprocess
import sys

# ========== 前置：清理 Playwright 缓存（解决版本兼容问题，仅需执行一次，可注释） ==========
# subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
# subprocess.run([sys.executable, "-m", "playwright", "clean"], check=True)

def get_iframe_html(iframe_id, page, timeout=30000):
    """
    获取指定 id 的 iframe 内部渲染后的 HTML 内容（优化版：解决超时/Frame 分离问题）
    :param iframe_id: iframe 的 id 属性值（字符串）
    :param page: Playwright 的 page 对象（页面上下文）
    :param timeout: 超时时间（毫秒）
    :return: iframe 内部的 HTML 字符串；若失败返回 None
    """
    try:
        # 1. 按 id 定位 iframe 元素（等待元素可见，而非仅附加）
        iframe_selector = f"#{iframe_id}"
        iframe_elem = page.wait_for_selector(
            iframe_selector,
            timeout=timeout,
            state="visible"  # 确保 iframe 元素在页面上可见
        )

        # 2. 处理 Frame 分离问题：多次尝试获取 content_frame()
        iframe_frame = None
        for _ in range(3):  # 重试 3 次
            try:
                iframe_frame = iframe_elem.content_frame()
                if iframe_frame and not iframe_frame.is_detached():
                    break
            except Exception:
                page.wait_for_timeout(500)  # 间隔 500ms 重试
        if not iframe_frame or iframe_frame.is_detached():
            print(f"错误：iframe(id={iframe_id}) 的 Frame 上下文已分离！")
            return None

        # 3. 等待 iframe 加载完成（替换 networkidle 为 load，兼容 SPA/WebSocket 页面）
        iframe_frame.wait_for_load_state(
            "load",  # 仅等待 iframe 的 DOM + 资源加载完成（视觉上的加载完成）
            timeout=timeout * 2  # 超时时间翻倍
        )

        # 4. 兜底：等待 iframe 内的任意关键元素出现（可选，根据页面调整）
        # 示例：等待 iframe 内的 body 元素（必存在），确保内容已渲染
        iframe_frame.wait_for_selector("body", timeout=timeout)

        # 5. 获取并返回 iframe 内部的 HTML
        return iframe_frame.content()

    except PlaywrightTimeoutError:
        print(f"错误：iframe(id={iframe_id}) 加载超时（已尝试最大等待时间）！")
        # 兜底：强制获取当前 iframe 的内容（即使未完全加载）
        try:
            return iframe_elem.content_frame().content()
        except:
            return None
    except Exception as e:
        print(f"错误：获取 iframe(id={iframe_id}) 内容失败：{str(e)}")
        return None

# ========== 主程序 ==========
if __name__ == "__main__":
    # 定义主页面路径
    index_file = Path.cwd() / "index.html"
    if not index_file.exists():
        print(f"错误：主页面文件 {index_file} 不存在！")
        sys.exit(1)

    # 启动 Playwright（添加参数确保进程稳定）
    with sync_playwright() as p:  # 使用 with 语句自动清理 Playwright 资源（关键：解决 EPIPE）
        # 优化 Chromium 启动参数（减少不稳定，保留跨域支持）
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-web-security",  # 解决跨域 iframe 访问限制（必需）
                "--allow-running-insecure-content",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",  # 解决 Linux 下 /dev/shm 内存不足问题（关键：解决 EPIPE）
                "--disable-background-networking",  # 减少后台网络请求，提升稳定性
                "--disable-features=NetworkService",  # 禁用新的网络服务，兼容旧版逻辑
                "--timeout=30000"  # Chromium 启动超时
            ],
            slow_mo=100,  # 减慢操作速度，避免进程通信跟不上（可选）
            timeout=60000  # 浏览器启动超时
        )

        # 创建新页面（禁用资源缓存，避免旧内容干扰）
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},  # 设为大屏，避免元素被隐藏
            no_viewport=False,
            accept_downloads=False,
            bypass_csp=True,  # 绕过内容安全策略（解决部分页面渲染问题）
        )
        page = context.new_page()

        # 访问本地主页面（优化等待策略）
        try:
            page.goto(
                f"file://{index_file.resolve()}",
                wait_until="domcontentloaded",
                timeout=60000
            )
            # 等待主页面的所有 iframe 元素都出现
            page.wait_for_selector("iframe", timeout=30000)
            print("主页面加载完成！")
        except PlaywrightTimeoutError:
            print("错误：主页面加载超时！")
            browser.close()
            sys.exit(1)

        # ========== 逐个处理 iframe（避免资源竞争） ==========
        iframe_configs = [
            {"id": "doubao", "file": "doubao_content.html"},
            {"id": "kimi", "file": "kimi_content.html"},
            {"id": "deepseek", "file": "deepseek_content.html"}
        ]

        # 保存主页面 HTML
        with open("main_page.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        print("主页面 HTML 已保存！")

        # 逐个处理，每个 iframe 处理完后短暂休息
        for config in iframe_configs:
            iframe_id = config["id"]
            save_file = config["file"]
            print(f"\n开始处理 iframe：{iframe_id}...")

            # 调用函数获取 iframe 内容
            iframe_html = get_iframe_html(iframe_id, page, timeout=30000)

            # 保存内容
            if iframe_html:
                with open(save_file, "w", encoding="utf-8") as f:
                    f.write(iframe_html)
                print(f"{iframe_id} iframe 内容已保存到：{save_file}")
            else:
                print(f"{iframe_id} iframe 内容获取失败！")

            # 短暂休息，释放资源
            page.wait_for_timeout(1000)

        # ========== 关闭资源（确保进程正常退出，解决 EPIPE） ==========
        input("按回车退出...")
        page.close()
        context.close()
        browser.close()
