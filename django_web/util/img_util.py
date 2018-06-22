# -*- coding: utf-8 -*-
import os
import cv2
from numpy import ndarray, array
import numpy as np
import sys
import time
from django.conf import settings
from libtiff import TIFF
import logging
from PIL import Image

logger = logging.getLogger('django_logger')
BASE_DIR = settings.BASE_DIR

RESOURCE = os.path.join(BASE_DIR, "django_web/resource")
TEMP = os.path.join(BASE_DIR, "django_web/temp")
SHOW_IMG = sys.platform == "win32"


def get_imgs_from_path(file_dir):
    if not os.path.exists(file_dir):
        return []
    return os.listdir(file_dir)


def read_img(file_path, width=1000, flags=1):
    if not os.path.exists(file_path):
        return None
    image = cv2.imread(file_path, flags=flags)
    shape = image.shape
    h_after_resize = int(shape[0] / shape[1] * width)
    image = cv2.resize(image, (width, h_after_resize))
    return image


def get_mask(file_name, flags=1, scale=1):
    file_path = os.path.join(RESOURCE, "mask", file_name)
    image = cv2.imread(file_path, flags=flags)
    if scale != 1:
        dwidth = image.shape[1] * scale
        image = img_resize(image, dwidth=dwidth)
    return image


def write_image(img, file_path, file_name):
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    cv2.imwrite(os.path.join(file_path, file_name), img)


save_result = write_image



def write_tif_image(img, path, file_name):
    """
    存放tif格式的图片
    :param img:
    :param file_path:
    :param file_name:
    :return:
    """
    if not os.path.exists(path):
        os.makedirs(path)
    # 存储图片文件必须为tif格式
    if file_name.find(".tif") < 0:
        file_name += ".tif"
    file_path = os.path.join(path, file_name)
    out_tiff = TIFF.open(file_path, mode='w')
    out_tiff.write_image(img, compression=None, write_rgb=True)
    out_tiff.close()


def write_middle_result(img, folder="result", file_name="mid.jpg"):
    result_file_path = os.path.join(TEMP, folder)
    if not os.path.exists(result_file_path):
        os.makedirs(result_file_path)
    cv2.imwrite(os.path.join(result_file_path, file_name), img)


def img_resize(img, dwidth):
    """
    :param img:
    :param dwidth:
    :return:
    """
    if isinstance(img, ndarray):
        size = img.shape
    elif isinstance(img, list):
        img = array(img)
        size = img.size
        if len(size) < 2:
            return None
    else:
        return None
    height = size[0]
    width = size[1]
    scale = dwidth / width
    dheight = int(height * scale)
    nImg = cv2.resize(img, dsize=(dwidth, dheight), interpolation=cv2.INTER_CUBIC)
    return nImg


def img_resize_with_scale(img, dwidth, restrict_width_to_long_side=False):
    """
    :param img:
    :param dwidth:
    :param restrict_width_to_long_side
    :return:
    """
    if isinstance(img, ndarray):
        size = img.shape
    elif isinstance(img, list):
        img = array(img)
        size = img.size
        if len(size) < 2:
            return None
    else:
        return None
    height, width = size[0:2]
    if restrict_width_to_long_side:
        scale = dwidth / max(height, width)
    else:
        scale = dwidth / width
    dheight = int(height * scale)
    dwidth = int(width * scale)
    nImg = cv2.resize(img, dsize=(dwidth, dheight), interpolation=cv2.INTER_CUBIC)
    return nImg, scale


def draw_rect_for_text(img, text_result, location_multi=1):
    img_clone = np.array(img, dtype=np.uint8)
    for label in text_result:
        location = text_result[label]["location"]
        top = int(location["top"] * location_multi)
        left = int(location["left"] * location_multi)
        width = int(location["width"] * location_multi)
        height = int(location["height"] * location_multi)
        cv2.rectangle(img_clone, (left, top), (left + width, top + height), 128, 2)
    showimg(img_clone, "box_text")


max_win_width = 1000
max_win_height = 800
min_win_width = 150


def showimg(img, win_name=None, wait_flag=True):
    # 非windows环境不画图
    if not SHOW_IMG:
        return
    if win_name is None:
        win_name = "test_%d" % int(time.time())
    height, width = img.shape[0:2]
    if width > max_win_width:
        height = int(height / width * max_win_width)
        width = max_win_width
    if height > max_win_height:
        width = int(width / height * max_win_height)
        height = max_win_height
    if width < min_win_width:
        height = int(height * min_win_width / width)
        width = min_win_width
        img = img_resize(img, width)
    cv2.namedWindow(win_name, cv2.WINDOW_KEEPRATIO)
    cv2.resizeWindow(win_name, width, height)
    cv2.imshow(win_name, img)
    if wait_flag:
        cv2.waitKey()


def img_joint(img_turple, axis=0, align=0.5, fill_pix=0):
    """
    横向拼接图片元组生成一张大图
    :param img_turple: array like object
    :param axis: 0-纵向拼接  1-横向拼接
    :param align: 0-向小坐标对其 0.5-居中 1-向大坐标对其
    :return:
    """
    if len(img_turple) < 1:
        raise ValueError("no pic param")
    if len(img_turple) == 1:
        return img_turple[0]

    # 选取图片数组当中维度最大的图片作为最终图片维度标准
    # 即如果有彩图则最后拼接结果为彩图，如果全是灰度图则最后的结果为灰度图
    max_shape_len = 0
    min_shape_len = 100
    for img in img_turple:
        img_shape_len = len(img.shape)
        max_shape_len = img_shape_len if img_shape_len > max_shape_len else max_shape_len
        min_shape_len = img_shape_len if img_shape_len < min_shape_len else min_shape_len

    if max_shape_len > 3 or min_shape_len < 2:
        raise ValueError("img joint error at wrong shape len: max=%d, min=%d" % (max_shape_len, min_shape_len))

    mask = np.ones((max_shape_len,), dtype=np.int32)
    mask[axis] = 0
    final_img = None
    for img in img_turple:
        shape = img.shape
        if len(shape) == 2 and max_shape_len == 3:
            img = img[:, :, np.newaxis]
            # 将灰度图转成伪彩图
            img = np.concatenate((img, img, img), axis=2)
        # elif len(shape) == 3 and max_shape_len == 2:
        #     img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if final_img is None:
            # 初始化拼接整图
            final_shape = img.shape * mask
            final_img = np.zeros(final_shape, dtype=np.uint8)
        # 计算整图和待拼接图片的尺寸差
        shape_dif = (np.asarray(final_img.shape) - np.asarray(img.shape)) * mask
        # 补全尺寸
        for i in range(max_shape_len):
            dif_i = shape_dif[i]
            if dif_i > 0:
                img = enlarge(img, len=dif_i, axis=i, align=align, fill_pix=fill_pix)
            else:
                final_img = enlarge(final_img, len=-dif_i, axis=i, align=align, fill_pix=fill_pix)
        # 拼接图片
        final_img = np.concatenate((final_img, img), axis=axis)
    return final_img


def enlarge(img, len=0, axis=0, align=0.5, fill_pix=0):
    """
    将图片沿指定坐标轴方向伸展
    :param img:
    :param len:
    :param axis:
    :return:
    """
    if len == 0:
        return img
    len_up = int(len * align)
    len_down = len - len_up
    shape = np.asarray(img.shape, dtype=np.int32)
    shape[axis] = len_up
    up_part = np.ones(shape, dtype=np.uint8) * fill_pix
    img = np.concatenate((up_part, img), axis=axis)
    shape[axis] = len_down
    down_part = np.ones(shape, dtype=np.uint8) * fill_pix
    img = np.concatenate((img, down_part), axis=axis)
    return img


def get_angle_from_transform(mat):
    """
    通过变换矩阵得到图片的旋转角度
    :param mat:
    :return:
    """
    mat = np.array(mat)
    if len(mat.shape) != 2:
        return 0
    h, w = mat.shape
    if h != 3 or w != 3:
        return 0
    # 抽取旋转矩阵
    rot_mat = mat[0:2, 0:2]
    # 缩放矩阵数值，确保旋转矩阵中sin和cos的平方和为1
    square_sum = np.sum(rot_mat * rot_mat)
    ratio = np.sqrt(2 / square_sum)
    rot_mat = rot_mat * ratio
    cos = rot_mat[0][0]
    sin = rot_mat[0][1]
    if cos > 1:
        cos = 1
    elif cos < -1:
        cos = -1
    angle = np.arccos(cos) / np.pi * 180
    if sin < 0:
        angle = -1 * angle
    return angle


def find_max_region(region_list):
    """
    找到能够包围区域的最大区域
    :param region_list: [region1,region2,....] region:[x,y,w,h]
    :return:
    """
    if len(region_list) == 0:
        raise ValueError("region list is empty")
    if len(region_list) == 1:
        return region_list[0]
    box_point_list = []
    for region in region_list:
        box_point_list.append(region_to_boxPoints(region))
    points = np.concatenate(box_point_list)
    xmin, ymin = np.min(points, axis=0)
    xmax, ymax = np.max(points, axis=0)
    max_region = [xmin, ymin, xmax - xmin, ymax - ymin]
    return max_region


def region_to_boxPoints(region):
    """
    [x,y,w,h] -->  [point1, point2, point3, point4]
    :param region:
    :return:
    """
    if not len(region) == 4:
        raise ValueError("region size error")
    x_min, y_min, width, height = region
    x_max = x_min + width
    y_max = y_min + height
    # 逆时针走点
    points = [[x_min, y_min], [x_min, y_max], [x_max, y_max], [x_min, y_max]]
    return np.intp(points)


def time_spend(start, label):
    now = time.time()
    time_spend = now - start
    logger.info("%s timeUsed = %d ms" % (label, int(time_spend * 1000)))
    return now


if __name__ == '__main__':
    file_dir = get_imgs_from_path(os.path.join(RESOURCE, "idcard_img"))
    file_path_1 = os.path.join(RESOURCE, "idcard_img", file_dir[0])
    image_1 = read_img(file_path_1)
    file_path_2 = os.path.join(RESOURCE, "idcard_img", file_dir[1])
    image_2 = read_img(file_path_2)
    file_path_3 = os.path.join(RESOURCE, "idcard_img", file_dir[2])
    image_3 = read_img(file_path_3)
    img = img_joint((image_1, image_2, image_3), axis=2)
    # cv2.imwrite("test.jpg", img)
    showimg(img, wait_flag=True)
