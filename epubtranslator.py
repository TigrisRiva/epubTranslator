import sys
import openai
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup,NavigableString
import threading
from queue import Queue
import traceback
import time
from collections import deque
import re

# 设置OpenAI的API密钥
#如果你是OpenAI
'''
openai.api_key = 'WRITE YOUR API KEY HERE'
'''
#如果你是Azure OpenAI
openai.api_type = "azure"
openai.api_key = "WRITE YOUR AZURE API KEY HERE"
openai.api_base = "AZURE OpenAI END POINT"
openai.api_version = "AZURE API VERSION" #e.g 2023-05-15

class TranslationResult:
    def __init__(self, result, errorcode, data):
        self.result = result
        self.errorcode = errorcode
        self.data = data
def check_string(s):
    # 检查字符串是否只包含英文单词、句子、适量的标点和空格
    # 允许字符串中有数字和其他字符，但不能只有这些字符
    # 这个正则表达式匹配包含至少一个英文字母的字符串，并允许空格、标点符号和数字
    match = re.search(r'[A-Za-z]', s)
    
    # 如果match不是None，则字符串是有效的
    return match is not None

def translate_text(text):
    # 调用OpenAI的API进行翻译
    #print("需要翻译的文本：",text)
    try:
        if (check_string(text)==False):
            print("不需要翻译！")
            return TranslationResult(True, 0, text)
        response = openai.ChatCompletion.create(
            deployment_id="Azure OpenAI Deployment ID", # 如果你是Azure OpenAI
            #model="gpt-3.5-turbo", # 如果你是OpenAI
            messages=[
                {
                    "role":"system",
                    "content":"Starting now, you are an English translator. You will not engage in any conversation with me; you will only translate my words from English to Chinese. You will return a pure translation result, without adding anything else, including Chinese pinyin."},
                    #"content":"我将发一段HTML代码给你，其中包含了英文文本，请根据具体情况翻译英文文本到中文，维持原有HTML格式。如果翻译会破坏原有格式，请不做任何处理原样发回。"},
                {
                    "role": "user", 
                    "content": f"{text}"
                }
            ],
            max_tokens=256,
            temperature=0.0,
            request_timeout = 10            
        )
        if (response==None):
            print("翻译失败！")
            return text
        translated_text = response.choices[0].message['content']
        #print("翻译后：",translated_text)
        return TranslationResult(True, 0, translated_text)
    except Exception as e:
        print("发生异常：", e)
        traceback.print_exc()
        return TranslationResult(False, 1001, None)
    
def translate_html(text):
    # 调用OpenAI的API进行翻译
    #print("需要翻译的文本：",text)
    try:
        if (check_string(text)==False):
            print("不需要翻译！")
            return TranslationResult(True, 0, text)
        response = openai.ChatCompletion.create(
            deployment_id="chatgpt",
            #model="gpt-3.5-turbo",
            messages=[
                {
                    "role":"system",
                    #"content":"Starting now, you are an English translator. You will not engage in any conversation with me; you will only translate my words from English to Chinese. You will return a pure translation result, without adding anything else, including Chinese pinyin."},
                    "content":"我将发一段HTML代码给你，其中包含了英文文本，请根据具体情况翻译英文文本到中文，维持原有HTML格式。如果翻译会破坏原有格式，请不做任何处理原样发回。"},
                {
                    "role": "user", 
                    "content": f"{text}"
                }
            ],
            max_tokens=256,
            temperature=0.0,
            request_timeout = 10            
        )
        if (response==None):
            print("翻译失败！")
            return text
        translated_text = response.choices[0].message['content']
        #print("翻译后：",translated_text)
        return TranslationResult(True, 0, translated_text)
    except Exception as e:
        print("发生异常：", e)
        traceback.print_exc()
        return TranslationResult(False, 1001, None)

def update_epub_title(epub_path, new_title):
    # 读取epub文件
    book = epub.read_epub(epub_path)
    print("当前标题:", book.get_metadata('DC', 'title')[0][0])
    
    # 更新标题
    book.title = new_title
    book.set_unique_metadata('DC', 'title', new_title)
    # 保存修改
    epub.write_epub(epub_path, book, {})
    
    # 重新读取文件查看更新后的标题
    updated_book = epub.read_epub(epub_path)
    print("更新后的标题:", updated_book.get_metadata('DC', 'title')[0][0])

stop_event = threading.Event()

def worker(queue, output_epub, new_book, lock):
    try:
        while True:
            if stop_event.is_set():
                break
            item = queue.get()
            if item is None:
                break
            current_thread = threading.current_thread()
            if item.get_type() == 4 or item.get_type() == 9:
                print(f"{current_thread.name} 正在处理 {item.file_name}")
            translate_and_save_item(item, output_epub, new_book, lock)
            queue.task_done()
    except Exception as e:
        print(f"{current_thread.name}发生异常")
        traceback.print_exc()
        queue.task_done()
        quit()

def translate_and_save_item(item, output_epub, new_book, lock):
    #current_thread = threading.current_thread()
    if item.get_type() == 9:
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        p_list = soup.findAll("p")
        if len(p_list) == 0:
            new_book.add_item(item)
            return
        for p in p_list:
            if stop_event.is_set():
                break
            print("翻前HTML：",p)
            tresult = translate_html(str(p))
            if (tresult.result):
                translated_text = tresult.data
                newtag = BeautifulSoup(translated_text,'html.parser').p
                p.replace_with(newtag)
                print(f"翻后HTML：{newtag}")
        item.set_content(str(soup).encode('utf-8'))
    new_book.add_item(item)
    with lock:
        epub_options = {'ignore_ncx': False}
        epub.write_epub(output_epub, new_book,epub_options)

def modify_links(item):
    #print(f"当前item,{item}")
    if isinstance(item, epub.Link):
        # Modify the title of the link
        print(f"开始翻译LINK： {item.title}")
        tresult = translate_text(item.title)
        if (tresult.result == False):
            return epub.Link(item.href, item.title, item.uid)
        else:
            translated_text = tresult.data
            new_title = translated_text
            print(f"翻译完成： {new_title}")
            return epub.Link(item.href, new_title, item.uid)
    elif isinstance(item, tuple):
        # 解包
        toc_section, toc_links = item  # 解包元组
        print ("Section Title:",toc_section.title)
        new_title = toc_section.title
        tresult = translate_text(toc_section.title)
        if (tresult.result):
            translated_text = tresult.data
            new_title = translated_text
            print(f"翻译完成： {new_title}")
        new_links = [modify_links(link) for link in toc_links]
        # Return a tuple with the modified section and links
        return (epub.Section(new_title, toc_section.href), new_links)
    else:
        # Return the item unmodified if it's not a link or a section
        print("****啥也不是!****",type(item),item)
        # 如果 TOC 有不同类型的对象，可以在这里处理
        return item

def translate_epub(input_epub, output_epub, num_threads=5):
    try:
        epub_options = {'ignore_ncx': False}
        book = epub.read_epub(input_epub, epub_options)
        new_book = epub.EpubBook()
        new_book.metadata = book.metadata
        new_book.spine = book.spine
        #new_book.toc = book.toc
        # 遍历现有的 TOC并翻译
        
        print(f"开始翻译目录")
        new_toc = [modify_links(link) for link in book.toc]
        # 更新书籍的 TOC
        new_book.toc = tuple(new_toc)
        new_book.set_language('zh-cn')
        queue = Queue()
        lock = threading.Lock()
        threads = []
        for _index in range(num_threads):
            thread = threading.Thread(target=worker, args=(queue, output_epub, new_book, lock), name="Thread-"+_index.__str__())
            thread.start()
            threads.append(thread)

        for item in book.get_items():
            queue.put(item)

        all_tasks_completed = False
        while not all_tasks_completed:
            try:
                time.sleep(1)  # 短暂睡眠，允许主线程检查 KeyboardInterrupt
                all_tasks_completed = queue.unfinished_tasks == 0
            except KeyboardInterrupt:
                print("侦测到Ctrl+C，正在退出...")
                # 通知终止所有子线程的操作
                stop_event.set()
                break
        print("进入退出程序...")
        for _ in threads:
            queue.put(None)
        for thread in threads:
            thread.join()
        print("退出程序执行完毕...")
    except KeyboardInterrupt:
        print("主线程侦测到Ctrl+C，正在退出...")
        for _ in threads:
            queue.put(None)
        for thread in threads:
            thread.join() 

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python translate_epub.py <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not input_file.endswith('.epub'):
        print("The input file must be an epub file.")
        sys.exit(1)

    output_file = input_file.replace('.epub', '_cn.epub')
    print("开始翻译...")
    translate_epub(input_file, output_file)
