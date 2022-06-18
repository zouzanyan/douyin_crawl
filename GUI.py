from tkinter import *
from tkinter.ttk import *
import threading
import crawl_one
import crawl_majority


def crawl_one_entry(number):
    txt.insert(END, '开始爬取单视频...请等待\n')
    crawl_one.crawl_main(number)
    txt.insert(END, '爬取完成!\n')
    entry_one.delete(0, END)


def crawl_majority_entry(number):
    txt.insert(END, '开始爬取个人主页全部视频...请等待\n')
    crawl_majority.crawl_main(number)
    txt.insert(END, '全部视频爬取完成!\n')
    entry_majority.delete(0, END)


def display_info():
    txt.insert(0, '')


def thread_(func, *args):
    t = threading.Thread(target=func, args=args)
    t.start()


root = Tk()
root.title('抖音视频爬取v1.0')
root.geometry('720x540')

txt = Text(root)

lb = Label(root, text='抖音单视频爬取', font=('Arial', 12))
lb.pack()

entry_one = Entry(root)
entry_one.pack()

button = Button(root, text="执行", command=lambda: thread_(crawl_one_entry, entry_one.get()))
button.pack()

lb = Label(root, text='抖音主页视频批量爬取', font=('Arial', 12))
lb.pack()

entry_majority = Entry(root)
entry_majority.pack()

button = Button(root, text="执行", command=lambda: thread_(crawl_majority_entry, entry_majority.get()))
button.pack()

txt.place(relwidth=1, relheight=0.5)
txt.pack()

root.mainloop()
