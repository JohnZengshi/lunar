import time
import mmap
import threading
import struct


class SharedMemoryWriter:
    def __init__(self, file_path, memory_size):
        self.file_path = file_path
        self.memory_size = memory_size
        self.shared_file = None
        self.shared_memory = None
        self.thread = None
        self.is_running = False

    def initialize(self):
        self.shared_file = open(self.file_path, "r+b")
        self.shared_memory = mmap.mmap(self.shared_file.fileno(), 0)

    def write_values(self, x, y):
        packed_values = struct.pack("<ii", x, y)
        self.shared_memory.seek(0)
        self.shared_memory.write(packed_values)

    def start_writing_thread(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._writing_thread)
        self.thread.start()

    def stop_writing_thread(self):
        self.is_running = False
        self.thread.join()

    def _writing_thread(self):
        while self.is_running:
            self.write_values(1031, 519)
            print("Python: Writing values - x: 1031, y: 519")

    def close(self):
        self.shared_memory.close()
        self.shared_file.close()


# shared_memory_writer = SharedMemoryWriter(
#     "shared_memory.bin", 8)  # 假设每个值占用 4 个字节
# shared_memory_writer.initialize()
# shared_memory_writer.start_writing_thread()

# # 在这里启动 Kotlin 线程来接收共享内存数据

# # 主线程等待一段时间
# time.sleep(50000)

# shared_memory_writer.stop_writing_thread()
# shared_memory_writer.close()
