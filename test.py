import win32gui
import win32con
import win32process
import win32event
import win32api


def hide_process():
    # 获取当前进程ID
    pid = win32api.GetCurrentProcessId()

    # 获取当前进程句柄
    handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, pid)

    # 设置进程窗口隐藏
    win32gui.ShowWindow(win32gui.GetForegroundWindow(), win32con.SW_HIDE)

    # 获取Shell进程ID
    shell_pid = win32process.GetProcessId(win32process.GetShellWindow())

    # 将当前进程的父进程设置为Shell进程
    win32process.AttachConsole(shell_pid)

    # 创建一个新的控制台窗口，用于隐藏进程输出
    win32gui.ShowWindow(win32gui.GetForegroundWindow(), win32con.SW_HIDE)

    # 解除对控制台的绑定
    win32process.FreeConsole()

    # 创建一个新的进程组，使得进程在父进程结束时不会受到影响
    win32process.SetProcessGroupID(handle, 0)

    # 关闭进程句柄
    win32api.CloseHandle(handle)


if __name__ == "__main__":
    hide_process()
    # 在这里添加您需要隐藏执行的代码
