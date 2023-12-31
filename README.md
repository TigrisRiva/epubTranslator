# ePubTranslator

将英文EPUB书籍翻译为纯中文EPUB，目前只支持这种语言翻译

## 为什么要做这个项目

OPENAI开放API以后，现有的翻译器很多。但是有几个问题：  
1、一般都是做成了双语版。虽然这是为了让英语不错的选手能对照原文准确理解，但是很多人其实都跳过英文不看，更关键的是，如果用微信读书里的听书功能，这种双语读物就不够友好了。被迫要把英文和中文都听一遍。  
2、之前有一些书的翻译效果欠佳，并不是说不够信达雅。而是有些作者喜欢弄各种格式，一会儿粗体一会儿斜体。目前市面上的翻译方式是用bs抽取p标签中的text部分，翻译后写回去。这些格式都消失了，我直接让chatgpt翻译一整个标签，原来的格式得到最大程度的保留，效果不错。  
3、可以自己控制线程数量，开足马力并行翻译。一般书10分钟左右就翻译完了。建议使用AZURE的接口，速度比OPENAI的快很多，差了大概3-4倍。  
4、可能我之前找的开源翻译忘了做菜单模块。所以就做了个菜单翻译  

## 运行指南

```bash
# 如何运行
python epubtranslator.py xxxx.epub
```
然后等它运行结束就好。注意这个程序没有断点保存的功能，所以如果中途退出，只能重新开始

## 其他问题
1、Azure Content Filter问题
建议关闭Content Filter，可以提交申请关闭，如果无法关闭，就把Content Filter调到最低
2、中间断了怎么办？
目前没有断点续传。建议不要上来就翻大部头，毕竟每次翻译都要花银子

