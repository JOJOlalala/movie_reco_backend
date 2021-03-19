# -*- coding: UTF-8 -*-
import json

# 自定义类


class MyClass:
    # 初始化
    def __init__(self):
        self.a = 2
        self.b = 'bb'


##########################
# 创建MyClass对象
myClass = MyClass()
# 添加数据c
myClass.c = 123
myClass.a = 3
# 对象转化为字典
myClassDict = myClass.__dict__
# 打印字典
print(myClassDict)
# # 字典转化为json
# myClassJson = json.dumps(myClassDict)
# # 打印json数据
# print(myClassJson)
