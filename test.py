import tkinter as tk


def update_label(value):
    label.config(text=f"当前值：{value}")


# 创建主窗口
root = tk.Tk()
root.title("滑块示例")

# 创建滑块和标签
slider = tk.Scale(root, from_=0, to=2, orient=tk.HORIZONTAL,
                  length=300, resolution=0.1, command=update_label)
slider.pack(pady=20)

label = tk.Label(root, text="当前值：0")
label.pack()

# 运行主循环
root.mainloop()
