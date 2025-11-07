#!/usr/bin/env python3
import os
import sys
import time
import signal
import multiprocessing as mp

# 读取环境变量
CPU_PERCENT = int(os.getenv("CPU_PERCENT", "90"))
MEM_MB = int(os.getenv("MEM_MB", "2048"))
DURATION = int(os.getenv("DURATION", "0"))  # 0 = 无限

stop_event = mp.Event()

def cpu_worker():
    """单核 100% 负载，多个进程并行实现百分比"""
    while not stop_event.is_set():
        start = time.time()
        while time.time() - start < 0.05:
            _ = sum(i * i for i in range(1000))
        if CPU_PERCENT < 100:
            time.sleep(0.05 * (100 - CPU_PERCENT) / CPU_PERCENT)

def mem_holder():
    """常驻内存，不被 swap"""
    chunk = 50 * 1024 * 1024  # 50MB chunks
    chunks = MEM_MB // 50 + 1
    data = []
    for _ in range(chunks):
        data.append(bytearray(chunk))
        # 每分配一块就 touch 一下，防止 OS 延迟分配
        data[-1][0] = 1
    print(f"[INFO] Allocated {MEM_MB} MB memory")
    while not stop_event.is_set():
        time.sleep(10)
        # 每10秒 touch 一次，防止被换出
        for d in data:
            d[0] = (d[0] + 1) % 256

def signal_handler(*_):
    print("\n[INFO] Received shutdown signal, stopping workers...")
    stop_event.set()
    
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"""
[START] Python Resource Stresser
  CPU: {CPU_PERCENT}% 
  Memory: {MEM_MB} MB
  Duration: {DURATION if DURATION > 0 else '无限'} seconds
    """)

    cores = mp.cpu_count()
    workers = max(1, int(cores * CPU_PERCENT / 100))
    print(f"[INFO] Starting {workers} CPU workers on {cores} cores")

    procs = []
    for _ in range(workers):
        p = mp.Process(target=cpu_worker, daemon=True)
        p.start()
        procs.append(p)
    
    mem_p = mp.Process(target=mem_holder, daemon=True)
    mem_p.start()
    procs.append(mem_p)

    start_time = time.time()
    try:
        if DURATION > 0:
            while time.time() - start_time < DURATION:
                time.sleep(1)
                if stop_event.is_set():
                    break
        else:
            while not stop_event.is_set():
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Ctrl+C received")
    finally:
        print("[INFO] Terminating workers...")
        stop_event.set()
        for p in procs:
            p.terminate()
            p.join(timeout=2)
            if p.is_alive():
                p.kill()
                p.join()
        print("[DONE] All resources released")