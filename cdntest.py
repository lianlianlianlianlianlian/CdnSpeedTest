# -*- coding: utf-8 -*-
import asyncio  # 导入异步编程库
import aiohttp  # 导入异步HTTP客户端库
import sys  # 导入系统库，用于访问与Python解释器相关的变量和函数
import os  # 导入操作系统库，用于与操作系统交互
import time  # 导入时间库，用于时间相关的操作
import psutil  # 导入系统监控库，用于获取系统和网络信息
from threading import Thread  # 导入线程库，用于创建和管理线程
from urllib.parse import quote  # 导入URL编码函数

# 自定义参数
USER_AGENT = "CDN速度测试"  # 自定义用户代理字符串，用于HTTP请求
DOWNLOAD_URL = 'https://oss.darklotus.cn/img/2024/10/11/favicon.ico'  # 要下载的文件URL
NUM_TASKS = 10  # 同时发起的下载任务数量（可以根据需要调整）

def restart_program():
    """重启当前程序，清理文件对象和描述符。"""
    python = sys.executable  # 获取当前Python解释器的路径
    os.execl(python, python, *sys.argv)  # 重新执行当前脚本

class NetworkSpeedMonitor:
    """网络速度监控类，用于监控网络接口的接收和发送速度。"""
    def __init__(self, interval=2):
        self.interval = interval  # 设置监控间隔时间（秒）
        self.last_io_counters = psutil.net_io_counters(pernic=True)  # 获取当前网络IO统计信息

    def calculate_speed(self):
        """计算并打印网络速度。"""
        while True:
            time.sleep(self.interval)  # 等待指定的间隔时间
            new_io_counters = psutil.net_io_counters(pernic=True)  # 获取新的网络IO统计信息

            # 计算接收字节的变化
            diff_rx = sum(new_io_counters[n].bytes_recv - self.last_io_counters[n].bytes_recv 
                          for n in new_io_counters if n in self.last_io_counters)
            # 计算发送字节的变化
            diff_tx = sum(new_io_counters[n].bytes_sent - self.last_io_counters[n].bytes_sent 
                          for n in new_io_counters if n in self.last_io_counters)

            # 将字节转换为MB/s
            speed_rx = diff_rx / self.interval / 1024**2  
            speed_tx = diff_tx / self.interval / 1024**2

            # 打印网络速度
            print(f"Network Speed: 接收: {speed_rx:.2f} MB/s | 发送: {speed_tx:.2f} MB/s")

            # 更新上一次的IO统计信息
            self.last_io_counters.update(new_io_counters)

async def download_file(url):
    """异步下载文件的函数。"""
    try:
        headers = {
            'User-Agent': USER_AGENT  # 设置HTTP请求的用户代理
        }
        async with aiohttp.ClientSession() as session:  # 创建异步HTTP会话
            while True:
                # 禁用SSL验证，允许不安全的连接
                async with session.get(url, ssl=False, headers=headers) as response:  # 发送GET请求
                    if response.status == 200:  # 检查响应状态
                        content = await response.read()  # 读取响应的二进制内容
                        # 这里可以将内容保存到文件，或进行其他处理
                    else:
                        print(f"Failed to download file: {response.status}")  # 打印下载失败的状态码
                    await asyncio.sleep(0)  # 稍微延时以控制请求频率
    except Exception as e:
        print(f"An error occurred: {e}")  # 打印错误信息
        restart_program()  # 发生错误时重启程序

async def main():
    """主函数，启动下载任务和网络监控。"""
    # 对URL进行编码以适配中文路径
    encoded_url = quote(DOWNLOAD_URL, safe=':/')  # 编码URL，保留协议和路径的特殊字符
    tasks = [download_file(encoded_url) for _ in range(NUM_TASKS)]  # 创建多个下载任务

    # 创建并启动网络速度监控器
    network_speed_monitor = NetworkSpeedMonitor(interval=2)  # 实例化网络监控器
    monitor_thread = Thread(target=network_speed_monitor.calculate_speed)  # 创建监控线程
    monitor_thread.start()  # 启动监控线程

    await asyncio.gather(*tasks)  # 并发执行所有下载任务

if __name__ == "__main__":
    try:
        asyncio.run(main())  # 运行主函数
    except Exception as e:
        print(f"Critical error occurred: {e}. Restarting the program.")  # 打印严重错误信息
        restart_program()  # 发生严重错误时重启程序
