import cv2
import numpy as np


# 输入灰度图，返回hash
def getHash(img):
    # 转换为灰度
    image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    image = cv2.resize(image, (64, 64))
    avreage = np.mean(image)  # 计算像素平均值
    hash = []
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            if image[i, j] > avreage:
                hash.append(1)
            else:
                hash.append(0)
    return hash


# 计算汉明距离
# hamming单纯衡量的就是两个向量之间不同值得个数
# 所以比较hamming方法一定要设置响亮的长度相同
def hamming_distance(img1, img2):
    hash1 = getHash(img1)
    hash2 = getHash(img2)
    num = 0
    for index in range(len(hash1)):
        if hash1[index] != hash2[index]:
            num += 1
    return num / (64*64)


def hist_compare(img1, img2, method):
    # 直方图比较法
    H1 = cv2.calcHist([img1], [1], None, [256], [0, 256])
    H1 = cv2.normalize(H1, H1, 0, 1, cv2.NORM_MINMAX, -1)  # 对图片进行归一化处理

    # 计算图img2的直方图
    H2 = cv2.calcHist([img2], [1], None, [256], [0, 256])
    H2 = cv2.normalize(H2, H2, 0, 1, cv2.NORM_MINMAX, -1)

    # 利用compareHist（）进行比较相似度
    # 相关性比较 (method=cv.HISTCMP_CORREL) 值越大，相关度越高，最大值为1，最小值为0
    # 卡方比较(method=cv.HISTCMP_CHISQR 值越小，相关度越高，最大值无上界，最小值0
    # 巴氏距离比较(method=cv.HISTCMP_BHATTACHARYYA) 值越小，相关度越高，最大值为1，最小值为0
    similarity = cv2.compareHist(H1, H2, method=method)
    return similarity


def get_image_from_path(path):

    img = cv2.imread(path)
    # # 转换为灰度
    # img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # img = cv2.resize(img, (64, 64))
    return img

# 路径有中文名读取不了


def cv_imread(filePath):
    cv_img = cv2.imdecode(np.fromfile(filePath, dtype=np.uint8), -1)
    return cv_img


if __name__ == '__main__':
    # 获取当前工作目录
    img1 = cv_imread(
        'D:/我的文件/学科/大四上/毕设/backend/django_rest_test/media/tasks/buaa/JackyChan/photo_capture/0.jpg')
    img2 = get_image_from_path(
        r'D:/我的文件/学科/大四上/毕设/backend/django_rest_test/media/tasks/buaa/JackyChan/photo_capture/1.jpg')
    cv2.imshow('image', img1)
    # 单纯来看hamming距离在1000以内可以归类
    # print('hamming distance:'+str(hamming_distance(img1, img2)))
    # print('hist compare:'+str(hist_compare(img1, img2, 0)))
