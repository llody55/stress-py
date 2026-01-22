import os
import time
import signal
import multiprocessing
import psutil
import sys

# ================= 环境变量适配 =================
# 从你的 docker-compose 中读取配置
CPU_TARGET = int(os.getenv("CPU_PERCENT", 0)) # 目标CPU占用百分比
MEM_TARGET_MB = int(os.getenv("MEM_MB", 0))    # 内存占用大小
DURATION = int(os.getenv("DURATION", 0))       # 持续时间，0为永久
# 新增：磁盘压测配置（建议通过环境变量开启）
DISK_WORKERS = int(os.getenv("DISK_WORKERS", 0)) 
DISK_PATH = os.getenv("DISK_PATH", "/data")    # 对应你容器内挂载 /lgdata 的路径
# ===============================================

def disk_worker(path, stop_event):
    """
    核心修复：带 fsync 的磁盘压测
    """
    os.makedirs(path, exist_ok=True)
    file_path = os.path.join(path, f"stress_{os.getpid()}.dat")
    # 1MB 随机数据
    chunk = os.urandom(1024 * 1024)
    
    try:
        # buffering=0 绕过 Python 内部缓冲
        with open(file_path, "wb", buffering=0) as f:
            while not stop_event.is_set():
                # 状态检测：防止磁盘变只读后继续作死
                if not os.access(path, os.W_OK):
                    print(f"进程 {os.getpid()} 检测到磁盘已设为只读，停止写入。")
                    break
                
                f.write(chunk)
                # --- 关键修复：强制刷入物理硬件，保护宿主机内核 ---
                os.fsync(f.fileno()) 
                # 极短休眠，给宿主机内核喘息机会
                time.sleep(0.01)
    except Exception as e:
        print(f"磁盘进程异常: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def cpu_worker(target_percent, stop_event):
    """
    CPU 压测：通过控制执行/休眠比例实现百分比控制
    """
    chunk_time = 0.1 # 100ms 一个周期
    run_time = chunk_time * (target_percent / 100.0)
    sleep_time = chunk_time - run_time
    
    while not stop_event.is_set():
        start = time.time()
        while time.time() - start < run_time:
            _ = 100 * 100 # 空转负载
        time.sleep(sleep_time)

def mem_worker(target_mb, stop_event):
    """
    内存压测：具备 OOM 保护
    """
    data = []
    # 实际分配时预留一小部分，防止容器被 Docker 直接杀掉
    safe_target = int(target_mb * 0.95)
    print(f"内存任务：准备占用约 {safe_target} MB")
    
    try:
        # 每次分配 64MB
        for _ in range(0, safe_target, 64):
            if stop_event.is_set(): break
            data.append(' ' * (64 * 1024 * 1024))
            time.sleep(0.1)
        
        while not stop_event.is_set():
            time.sleep(1)
    finally:
        del data

def main():
    stop_event = multiprocessing.Event()
    processes = []

    # 信号处理 (Docker stop)
    def exit_gracefully(signum, frame):
        stop_event.set()
    signal.signal(signal.SIGTERM, exit_gracefully)
    signal.signal(signal.SIGINT, exit_gracefully)

    print(f"--- Stress-py 启动 (Duration: {DURATION if DURATION > 0 else 'Forever'}) ---")

    # 1. 启动 CPU 压测 (根据逻辑核心数平摊百分比)
    if CPU_TARGET > 0:
        cores = multiprocessing.cpu_count()
        for _ in range(cores):
            p = multiprocessing.Process(target=cpu_worker, args=(CPU_TARGET, stop_event))
            p.start()
            processes.append(p)

    # 2. 启动内存压测
    if MEM_TARGET_MB > 0:
        p = multiprocessing.Process(target=mem_worker, args=(MEM_TARGET_MB, stop_event))
        p.start()
        processes.append(p)

    # 3. 启动磁盘压测
    if DISK_WORKERS > 0:
        for _ in range(DISK_WORKERS):
            p = multiprocessing.Process(target=disk_worker, args=(DISK_PATH, stop_event))
            p.start()
            processes.append(p)

    # 4. 计时逻辑
    if DURATION > 0:
        time.sleep(DURATION)
        stop_event.set()
    else:
        while not stop_event.is_set():
            time.sleep(1)

    print("--- 正在清理资源并退出 ---")
    for p in processes:
        p.terminate()
        p.join()

if __name__ == "__main__":
    main()