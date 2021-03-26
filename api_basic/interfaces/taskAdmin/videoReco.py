import cv2
import os
import sys
from pathlib import Path
from .face_classify import hist_compare


'''
    camera_idx：视频源文件地址
    maximum_index：最大的索引数目（不连续的人物最大取样数量）
    maximum_frame_per_index：单个连续帧取样最多图片数目
    maximum_num：最大总体人物图片取样数目
    path_name：处理文件保存地址
    CONTINUE_FRAME：最低连续取样帧数要求（如果是4，就是连续4帧才会进行取样）
    simular_param：相似度阈值（区分两次连续采样的相似置信度）
'''


def CatchPICFromVideo(camera_idx, maximum_index, maximum_frame_per_index, maximum_num, path_name, CONTINUE_FRAME=4, simular_param=0.45):
    # cv2.namedWindow(window_name)

    # 视频源
    cap = cv2.VideoCapture(camera_idx)
    # OpenCV使用人脸识别分类器
    classfier = cv2.CascadeClassifier(
        cv2.data.haarcascades+"haarcascade_frontalface_alt.xml")

    Path(path_name+'/photo_capture/').mkdir(parents=True, exist_ok=True)
    Path(path_name+'/processed_video/').mkdir(parents=True, exist_ok=True)
    # 识别出人脸后要画的边框的颜色，RGB格式, color是一个不可增删的数组
    color = (0, 255, 0)
    # 保存视频
    fourcc = cv2.VideoWriter_fourcc(*'avc1')  # 指定fourcc编码
    # fourcc = cv2.VideoWriter_fourcc('H', '2', '6', '4')
    size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    out = cv2.VideoWriter(
        path_name+'/processed_video/output.mp4', fourcc, 20.0, size)
    # num 是帧顺序，index是提取任务序号
    num = 0
    index = 0
    # 保留图片的两个指针
    old_img = None
    new_img = None
    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 将当前桢图像转换成灰度图像
        # 人脸检测，1.2和2分别为图片缩放比例和需要检测的有效点数
        faceRects = classfier.detectMultiScale(
            grey, scaleFactor=1.2, minNeighbors=3, minSize=(32, 32))
        if len(faceRects) > 0:  # 大于0则检测到人脸
            for faceRect in faceRects:  # 单独框出每一张人脸
                x, y, w, h = faceRect
                old_img = frame[y - 10: y + h + 10, x - 10: x + w + 10]
                # 将当前帧保存为图片
                num += 1

                # 只有连续帧数才能够采样
                # save_path = path_name + \
                #     '/photo_capture/id_'+str(index)
                # Path(save_path).mkdir(parents=True, exist_ok=True)
                # img_name = "%s/%d.jpg" % (save_path, index)
                # print(img_name)
                # # cv2.imwrite(img_name, old_img, [
                # #     int(cv2.IMWRITE_PNG_COMPRESSION), 9])
                # cv2.imencode('.jpg', old_img)[1].tofile(img_name)

                # 画出矩形框
                cv2.rectangle(frame, (x - 10, y - 10),
                              (x + w + 10, y + h + 10), color, 2)

                # 显示当前捕捉到了多少人脸图片了
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(frame, 'num:%d/%d' %
                            (num, maximum_num), (x + 30, y + 30), font, 1, (255, 0, 255), 4)
                if num > (maximum_num):  # 如果超过指定最大保存数量退出循环
                    break
                break
            # 找到第一个人脸，退出循环
            break
        out.write(frame)  # 保存
    # 设置计数器，每次取第四帧
    counter = 1
    while cap.isOpened():
        ok, frame = cap.read()  # 读取一帧数据
        if not ok:
            break

        grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 将当前桢图像转换成灰度图像

        # 人脸检测，1.2和2分别为图片缩放比例和需要检测的有效点数
        faceRects = classfier.detectMultiScale(
            grey, scaleFactor=1.2, minNeighbors=3, minSize=(32, 32))

        if len(faceRects) > 0:  # 大于0则检测到人脸
            for faceRect in faceRects:  # 单独框出每一张人脸
                x, y, w, h = faceRect
                new_img = frame[y - 10: y + h + 10, x - 10: x + w + 10]
                compare_value = hist_compare(
                    old_img, new_img, 0)
                old_img = new_img
                if compare_value > simular_param:
                    counter += 1
                    # 相似，并且只有连续四帧出现的人脸能够被提取
                    if counter < maximum_frame_per_index+CONTINUE_FRAME:
                        if counter == CONTINUE_FRAME:
                            # 这一帧是默认的关键帧，默认情况下将使用该帧进行演员的检索
                            index += 1
                            save_path = path_name + \
                                '/photo_capture/id_'+str(index)
                            Path(save_path).mkdir(parents=True, exist_ok=True)
                            Path(
                                save_path+'/key_frame').mkdir(parents=True, exist_ok=True)
                            img_name = "%s/%d.jpg" % (save_path+'/key_frame',
                                                      counter-CONTINUE_FRAME+1)
                            print(img_name+':'+str(compare_value))
                            try:
                                cv2.imencode('.jpg', new_img)[
                                    1].tofile(img_name)
                            except:
                                print('Seems image goes None. Just skip.')
                            if index >= maximum_index:
                                break
                        elif counter > CONTINUE_FRAME:
                            img_name = "%s/%d.jpg" % (save_path,
                                                      counter-CONTINUE_FRAME+1)
                            print(img_name+':'+str(compare_value))
                            try:
                                cv2.imencode('.jpg', new_img)[
                                    1].tofile(img_name)
                            except:
                                print('Seems image goes None. Just skip.')

                else:
                    counter = 0
                num += 1
                if num > (maximum_num):  # 如果超过指定最大保存数量退出循环
                    break
                # 画出矩形框
                cv2.rectangle(frame, (x - 10, y - 10),
                              (x + w + 10, y + h + 10), color, 2)

                # 显示当前捕捉到了多少人脸图片了
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(frame, 'num:%d/%d,index:%d/%d' %
                            (num, maximum_num, index, maximum_index), (x + 30, y + 30), font, 1, (255, 0, 255), 4)

        out.write(frame)  # 保存
        # 超过指定最大保存数量结束程序
        if index >= maximum_index:
            break
        if num > (maximum_num):
            break

    # 释放摄像头并销毁所有窗口
    cap.release()
    cv2.destroyAllWindows()
    out.release()


if __name__ == '__main__':
    # 获取当前工作目录
    path = os.path.dirname(__file__)
    # 连续截100张人脸图像
    CatchPICFromVideo(path + "/Titan.mp4",
                      10, 10, 1000, path + "/Titan")
