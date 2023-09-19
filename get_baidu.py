import psutil

def get_process_status(pid):
    try:
        process = psutil.Process(pid)
        return process.status()
    except psutil.NoSuchProcess:
        return "进程不存在"
    except Exception as e:
        return f"未知错误: {str(e)}"

# 使用示例
status = get_process_status(84208)  # 假设1234是你想查询的PID
print(f"进程状态: {status}")