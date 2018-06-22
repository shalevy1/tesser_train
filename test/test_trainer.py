# coding:utf-8
import django_web.django_setting
from django_web.tesseract_trainer import TesseractTrainer
import os
from img_ai_trainer.settings import BASE_DIR
from django_web.util import file_util as fu
from django.conf import settings
import pytesseract
from PIL import Image
from libtiff import TIFF
import random

resource = os.path.join(BASE_DIR, "django_web/resource")
if settings.WIN_PLATFORM:
    tessdata_path = "C:\\Program Files (x86)\\Tesseract-OCR\\tessdata"
else:
    tessdata_path = os.path.join(resource, "tess_data")

# ref_path = os.path.join(BASE_DIR, "temp")
ref_path = "/web/train_data"
# *** 以下两个最好需要同时改
lang_name = "han_without_shape"
training_test_file = "han"
# ********
base_lang = "chi_sim"
base_psm = 6
shuffle = False
font_name = "myfont"
# ttf_file = os.path.join(resource, "ttf", "msyh.ttf")
ttf_file_list = []
# ttf_file_list.append(os.path.join(resource, "ttf", "msyh.ttf"))  # 微软雅黑
ttf_file_list.append(os.path.join(resource, "ttf", "simhei.ttf"))  # 黑体
# ttf_file_list.append(os.path.join(resource, "ttf", "STXIHEI.TTF"))  # 华文细黑
# ttf_file_list.append(os.path.join(resource, "ttf", "STZHONGS.TTF"))  # 华文中宋
# ttf_file_list.append(os.path.join(resource, "ttf", "STSONG.TTF"))   # 华文宋体
ttf_file_list.append(os.path.join(resource, "ttf", "simsun.ttc"))  # 宋体
ttf_file_list.append(os.path.join(resource, "ttf", "SIMYOU.TTF"))  # 幼圆
ttf_file_list.append(os.path.join(resource, "ttf", "ARIALUNI.TTF"))  # Arial Unicode MS
font_size = 60
train_id = 0  # 训练编号
font_properties = (0, 0, 0, 0, 0)


def train_lang():
    training_text = fu.read_file(os.path.join(resource, "train_text"), training_test_file)
    if shuffle:
        training_text = list(training_text)
        random.shuffle(training_text)
        training_text = "".join(training_text)
    # tessdata_path = os.path.join(resource, "tess_data")
    trainer = TesseractTrainer(ref_path,
                               base_lang,
                               base_psm,
                               lang_name,
                               font_name,
                               training_text,
                               ttf_file_list,
                               font_properties,
                               font_size,
                               train_id,
                               tessdata_path,
                               verbose=False)
    trainer.training()  # generate a multipage tif from args.training_text, train on it and generate a traineddata file
    trainer.add_trained_data()
    # trainer.clean()  # remove all files generated in the training process (except the traineddata file)


def case_test(lang, psm, sample):
    print("************ CASE CHECK ************")
    image_path = os.path.join(resource, "check_case/%s.tif"%sample)
    tif = TIFF.open(image_path, mode='r')
    index = 0
    for im in tif.iter_images():
        # test
        text = pytesseract.image_to_string(im, lang, config="-psm %d" % psm)
        print("idx =%d result = %s" % (index, text))
        index += 1


if __name__ == '__main__':
    train_lang()
    case_test(lang_name, base_psm,"address_sample")
    case_test(lang_name, base_psm, "address_sample")
    # case_test("han", 6)



