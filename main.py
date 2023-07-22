import io, os, threading
from concurrent.futures import ThreadPoolExecutor

# 设置临时环境变量，供给rarfile模块使用，需要先设置环境变量，再导入rarfile模块
os.environ['UNRAR_LIB_PATH'] = './UnRAR64.dll'
from unrar import rarfile

with open('./pwd.txt', 'r', encoding="utf-8") as f:  # 把密码字典读入内存
    buffer = io.StringIO(f.read())
print_lock = threading.Lock()  # 打印时加锁，防止多个线程同时打印
read_lock = threading.Lock()  # 读取密码字典时加锁，防止重复或者遗漏读取
src = rarfile.RarFile('./src.rar')  # 读取压缩包，在这里更改需要解压的压缩包的位置
cpu_count = os.cpu_count()  # 获取系统变量中的CPU核心数
file_read_lock = threading.BoundedSemaphore(len(src.namelist()))  # 限制同时读取文件的线程数，避免文件占用


# 初始化线程池
def pool_init():
    print("初始化线程池，CPU核心数为：", cpu_count)
    # 创建一个最大容量为cpu_count的线程池
    with ThreadPoolExecutor(cpu_count) as pool:
        # 通过map函数将解压函数和密码字典分配给线程池
        pool.map(unlock, pre_file_data())


# 准备需要解压的压缩包内的文件，todo 注意：压缩包内文件数量应大于等于CPU核心数，以避免多个线程同时读同一个文件造成文件占用。
def pre_file_data():
    counts = min(cpu_count, len(src.namelist()))
    filename = [None] * cpu_count
    # 读取压缩包内的文件数量
    for i in range(0, cpu_count):
        filename[i] = src.namelist()[i % counts]
    return filename


# 准备每个线程需要尝试的密码
def pre_pwd_data():
    with read_lock:
        crack = buffer.readline().strip()
        if crack == '':
            return None
        return crack


# 解压函数，也是创建的线程任务，尝试密码.
def unlock(file):
    crack = '0'
    while crack is not None:
        try:
            with file_read_lock:
                src.extract(file, path='./unrarData/', pwd=crack)
            with print_lock:
                print(f"解压成功，密码为：{crack}")
            os._exit(0)  # 解压成功后，退出整个程序（关闭了所有线程）
        except Exception as e:
            # pass
            # 注释掉输出语句，可以加运行速度
            with print_lock:
                print(f"解压失败，尝试的值位为：{crack}，错误信息为：{e}")
        crack = pre_pwd_data()
    return 0


if __name__ == '__main__':
    print("开始运行,请耐心等待(取消解压失败的输出语句，可以加快运行速度)")
    pool_init()
    with print_lock:
        print("运行结束，退出程序")
