# coding:utf-8
import os


def read_file(path, filename):
    """
    读取文件
    :param filename:
    :param test_rate: 测试集切割的比例
    :param sample_num
    :return:
    """
    file_path = os.path.join(path, filename)
    fopen = open(file_path, 'r',encoding="UTF-8")
    result = ""
    for eachline in fopen:
        # 剪切开头的日期得到操作对象的json字符串
        result += eachline
    fopen.close()
    return result


def writeFile(path, filename, data):
    """
    往文件里写入信息
    :param filename:
    :param data:
    :return:
    """
    file_path = os.path.join(path, filename)
    fopen = open(file_path, 'w')
    fopen.write(data)
    fopen.flush()
    fopen.close()


if __name__ == '__main__':
    from django_web.django_setting import *
    resource = os.path.join(BASE_DIR,"django_web/resource/train_text")
    text = read_file(resource,"output.txt")
    print(text)