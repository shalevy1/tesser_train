import django_web.django_setting
from django_web.tesseract_trainer import TesseractTrainer
import os
from img_ai_trainer.settings import BASE_DIR
from django_web.util import file_util as fu
from django.conf import settings
import pytesseract
from PIL import Image
from libtiff import TIFF

resource = os.path.join(BASE_DIR, "django_web/resource")
if settings.WIN_PLATFORM:
    tessdata_path = "C:\\Program Files (x86)\\Tesseract-OCR\\tessdata"
else:
    tessdata_path = os.path.join(resource, "tess_data")

ref_path = os.path.join("/web", "train_data")
lang_name = "focus"
base_lang = "chi_sim"
base_psm = 3
training_text = fu.read_file(os.path.join(resource, "train_text"), "focus")
font_name = "myfont"
# ttf_file = os.path.join(resource, "ttf", "msyh.ttf")
ttf_file_list = []
ttf_file_list.append(os.path.join(resource, "ttf", "msyh.ttf"))
ttf_file_list.append(os.path.join(resource, "ttf", "simhei.ttf"))
# ttf_file_list.append(os.path.join(resource, "ttf", "STXIHEI.TTF"))
# ttf_file_list.append(os.path.join(resource, "ttf", "STZHONGS.TTF"))
# ttf_file_list.append(os.path.join(resource, "ttf", "STSONG.TTF"))
ttf_file_list.append(os.path.join(resource, "ttf", "simsun.ttc"))
# ttf_file_list.append(os.path.join(resource, "ttf", "SIMYOU.TTF"))

font_size = 60
exp_number = 0
font_properties = (0, 1, 0, 0, 0)


def train_lang():
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
                               exp_number,
                               tessdata_path,
                               verbose=False)
    trainer.training()  # generate a multipage tif from args.training_text, train on it and generate a traineddata file
    trainer.add_trained_data()
    # trainer.clean()  # remove all files generated in the training process (except the traineddata file)


def case_test(lang, psm):
    print("************ CASE CHECK ************")
    image_path = os.path.join(resource, "check_case/test_sample.tif")
    tif = TIFF.open(image_path, mode='r')
    index = 0
    for im in tif.iter_images():
        # test
        text = pytesseract.image_to_string(im, lang, config="-psm %d" % psm)
        print("idx =%d result = %s" % (index, text))
        index += 1


if __name__ == '__main__':
    # char = ord('A')
    # word = ""
    # for i in range(52):
    #     word += chr(char)
    #     char += 1
    # print(word)
    train_lang()
    case_test(lang_name, base_psm)
    # case_test("chi_sim", 6)
