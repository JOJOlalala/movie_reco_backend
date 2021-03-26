from .face_classify import cv_imread, hist_compare
import cv2
import shutil
from pathlib import Path
import os
import urllib3
import datetime
import base64
import json


# classify photos and choose one for identification
def processed_video(path):
    # 检测photo_capture文件夹是否存在
    # if not Path(path+'/photo_capture').is_dir():
    #     raise Exception
    for root, dirs, files in os.walk(path+'/photo_capture'):
        index = len(files)
    baseDir = path+'/photo_capture/'
    # 初始化处理第一个文件，建立文件夹

    dir_id = 1
    currentDir = baseDir+'id_'+str(dir_id)+'/'
    dir_id += 1
    Path(currentDir).mkdir(parents=True, exist_ok=True)
    # 预处理一位
    shutil.move(baseDir+'0.jpg', currentDir+'0.jpg')
    for i in range(0, index-1):
        old_path = currentDir+str(i)+'.jpg'
        new_path = baseDir+str(i+1)+'.jpg'
        img1 = cv_imread(old_path)
        img2 = cv_imread(new_path)
        if hist_compare(img1, img2, 0) > 0.5:
            # 相似
            currentDir = currentDir
        else:
            # 不像似，移到新的目录
            currentDir = baseDir+'id_'+str(dir_id)+'/'
            Path(currentDir).mkdir(parents=True, exist_ok=True)
            dir_id += 1
        shutil.move(new_path, currentDir+str(i+1)+'.jpg')


# use huawei face detect api for actor tracing
def huawei_search_actor(img_path):
    # 因为是读取图片使用rb
    pic1 = str(base64.b64encode(
        open(img_path, 'rb').read()), encoding='utf-8')
    # 华为明星搜索
    # api地址
    request_url = "https://image.cn-north-1.myhuaweicloud.com/v1.0/image/celebrity-recognition"
    params = json.dumps({
        "image": pic1
    })
    if not Path('./token.json').is_file():
        # 创建token文件夹并保存
        data = huawei_token_request()
        with open('./token.json', 'w', encoding='utf-8') as file2:
            file2.write(json.dumps(data, indent=2, ensure_ascii=False))
    with open('./token.json', 'r', encoding='utf-8') as file1:
        data = json.load(file1)
        access_token = data['token']

    http = urllib3.PoolManager(timeout=3.0)
    counter = 0
    # check token once by default
    while(counter < 2):
        counter += 1
        r = http.request(
            "POST",
            request_url,
            body=params,
            headers={
                'content-type': 'application/json;charset=UTF-8',
                'X-Auth-Token': access_token
            }
        )

        if r.status == 200:
            reponse = r.data
            data = json.loads(reponse)
            return data
        else:
            print('huawei actor search failed with code:'+str(r.status))
            check_token_expire()

    return None


# before call that api, check whether token got expired first
def check_token_expire():

    # 读取token 并检查expire time
    needed = False
    with open('./token.json', 'r', encoding='utf-8') as file1:
        data = json.load(file1)
        expire_time = data['expires_at']
        now = datetime.datetime.now().timestamp()
        if now > expire_time:
            # print('token expire, nend re-auth:')
            needed = True
    if needed:
        data = huawei_token_request()
        with open('./token.json', 'w', encoding='utf-8') as file2:
            file2.write(json.dumps(data, indent=2, ensure_ascii=False))


# if expired, request token
def huawei_token_request():
    data = {
        "auth": {
            "identity": {
                "methods": [
                    "password"
                ],
                "password": {
                    "user": {
                        "domain": {
                            "name": "Emoless"
                        },
                        "name": "Emoless",
                        "password": "qwj969144994"
                    }
                }
            },
            "scope": {
                "project": {
                    "name": "cn-north-1"
                }
            }
        }
    }
    encoded_data = json.dumps(data).encode("utf-8")
    http = urllib3.PoolManager(timeout=3.0)
    r = http.request(
        "POST",
        "https://iam.myhuaweicloud.com/v3/auth/tokens?nocatalog=true",
        body=encoded_data,
        headers={
            'content-type': 'application/json;charset=UTF-8'
        }
    )
    if r.status == 201:
        reponse = r.data

        data = json.loads(reponse)
        datetime_str = data['token']['expires_at']
        datetime_stamp = datetime.datetime.timestamp(
            datetime.datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%f%z'))
        data = {'token': r.headers.get(
            'X-Subject-Token'), 'expires_at': datetime_stamp}
        return data
    else:
        print('huawei token auth failed with code:'+r.status)
        return None
