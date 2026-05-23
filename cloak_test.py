"""CloakBrowser 首次运行测试"""
from cloakbrowser import launch

print("正在启动 CloakBrowser（首次运行会自动下载 stealth Chromium ~200MB）...")
browser = launch()
print(f"浏览器已启动: {browser}")

page = browser.new_page()
print("正在访问 httpbin.org/get ...")
page.goto("https://httpbin.org/get")

content = page.content()
print(f"\n页面内容（前 800 字）:\n{content[:800]}")

# 检测 navigator.webdriver 是否被隐藏
result = page.evaluate("() => navigator.webdriver")
print(f"\nnavigator.webdriver = {result}（应为 False）")

browser.close()
print("测试完成 ✓")
