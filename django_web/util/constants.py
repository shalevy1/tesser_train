# -*- coding: utf-8 -*-
"""
psm model:
 0    Orientation and script detection (OSD) only.
 1    Automatic page segmentation with OSD.
 2    Automatic page segmentation, but no OSD, or OCR.
 3    Fully automatic page segmentation, but no OSD. (Default)
 4    Assume a single column of text of variable sizes.
 5    Assume a single uniform block of vertically aligned text.
 6    Assume a single uniform block of text.
 7    Treat the image as a single text line.
 8    Treat the image as a single word.
 9    Treat the image as a single word in a circle.
 10    Treat the image as a single character.
 11    Sparse text. Find as much text as possible in no particular order.
 12    Sparse text with OSD.
 13    Raw line. Treat the image as a single text line,
  """
PSM_AUTO = 3
PSM_AUTO_ONLY = 2
PSM_AUTO_OSD = 1
PSM_CIRCLE_WORD = 9
PSM_COUNT = 14
PSM_OSD_ONLY = 0
PSM_RAW_LINE = 13
PSM_SINGLE_BLOCK = 6
PSM_SINGLE_BLOCK_VERT_TEXT = 5
PSM_SINGLE_CHAR = 10
PSM_SINGLE_COLUMN = 4
PSM_SINGLE_LINE = 7
PSM_SINGLE_WORD = 8
PSM_SPARSE_TEXT = 11
PSM_SPARSE_TEXT_OSD = 12

# 最大图片体积 单位byte
MAX_IMG_SIZE = 4 * 1024 * 1024

# error message
IDCARD_NOT_FIND = "未识别到有效的身份证区域，请尽量将身份证置于中心，不要覆盖其他物品或是图片水印"
WRONG_IMG_SIZE = "图片最长边不能超过4096，最短边不能小于15"
IMAGE_EXCEED_SIZE_LIMIT = "图片体积过大，请缩小图片至4MB以内"

# check flag
CHECK_FLAG_CORRECT = 0
CHECK_FLAG_ERROR = 1

# risk type
RISK_TYPE_NORMAL = 0  # 普通无风险
RISK_TYPE_COPY = 1  # 复印件
RISK_TYPE_TEMP = 2  # 临时身份证
RISK_TYPE_REFILM = 3  # 翻拍
RISK_TYPE_FAKE = 4  # 伪造
