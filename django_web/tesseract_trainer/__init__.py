# coding:utf-8
"""
A small training framework for Tesseract 3.0.1, taking over the tedious manual process
of training Tesseract 3described in the Tesseract Wiki:
https://code.google.com/p/tesseract-ocr/wiki/TrainingTesseract3
"""

__version__ = '0.1'
__author__ = 'Balthazar Rouberol, rouberol.b@gmail.com'
import time
import shutil
import os
import subprocess
import logging
from django_web.model import *

logger = logging.getLogger('django_logger')

from os.path import join, exists

from .multipage_tif import MultiPageTif

# list of files generated during the training procedure
GENERATED_DURING_TRAINING = ['unicharset', 'pffmtable', 'inttemp', 'normproto', 'shapetable']

FONT_SIZE = 25  # Default font size, used during tif generation
TESSDATA_PATH = '/usr/local/share/tessdata'  # Default path to the 'tessdata' directory
WORD_LIST = None  # Default path to the "word_list" file, contaning frequent words
VERBOSE = True  # verbosity enabled by default. Set to False to remove all text outputs


class TesseractTrainer:
    """ Object handling the training process of tesseract """

    def __init__(self,
                 ref_path,
                 base_lang,
                 base_psm,
                 lang_name,
                 font_name,
                 training_text,
                 ttf_file_list,
                 font_properties,
                 font_size=FONT_SIZE,
                 train_id=0,
                 tessdata_path=TESSDATA_PATH,
                 word_list=WORD_LIST,
                 verbose=VERBOSE):
        """
        训练tesseract字库
        :param ref_path: 存储中间文件的目录
        :param base_lang: 训练基于的基础语言包
        :param base_psm:
        :param lang_name: 新的语言包名称
        :param font_name: 新的语言包对应字体名
        :param training_text: 训练字符集
        :param ttf_file_list: trueTypeFont文件
        :param font_properties: (<italic>,<bold>,<fixed>,<serif>,<fraktur>) 0-with  1-without
        :param font_size: 字体大小，单位px
        :param train_id: 训练标识数
        :param tessdata_path: 放置最终训练数据的路径
        :param word_list: 暂时用不上
        :param verbose:
        """
        # 为训练任务单独创建一个文件夹
        folder_name = "%s_%s" % (lang_name, train_id)
        training_path = os.path.join(ref_path, folder_name)
        if not os.path.exists(training_path):
            os.mkdir(training_path)
        else:
            key = input("已经存在一个同名的训练%s! 是否删除？ Y/N" % training_path)
            if key == "Y" or key == "y":
                self.clean(training_path)
                time.sleep(1)
                os.mkdir(training_path)
            else:
                raise ServiceException("训练终止！")
        self.folder_name = folder_name
        self.training_path = training_path
        self.base_lang = base_lang
        self.base_psm = base_psm
        # Training text: the text used for the multipage tif generation
        # we replace all \n by " " as we'll split the text over " "s
        # self.training_text = open(text).read().replace("\n", " ")
        self.training_text = training_text.replace("\n", " ")

        # 初始化exp_number为0
        self.exp_number = 0

        # The name of the result Tesseract "dictionary", trained on a new language/font
        self.lang_name = lang_name

        # The name of the font you're training tesseract on.
        # WARNING: this name must match a font name in the font_properties file
        # and must not contain spaces
        self.font_name = font_name
        if ' ' in self.font_name:
            raise ServiceException("The font_name argument must not contain any spaces. Aborting.")

        # The local path to the TrueType/OpentType file of the training font
        self.ttf_file_list = ttf_file_list
        if len(ttf_file_list) < 1:
            raise ServiceException("need at least one truetype file")
        for ttf_file in ttf_file_list:
            if not exists(ttf_file):
                raise ServiceException("The %s file does not exist. Aborting." % ttf_file)

        # The font size (in px) used during the multipage tif generation
        self.font_size = font_size

        # Local path to the 'font_propperties' file
        self.font_properties_file = font_properties
        self.font_properties_file = os.path.join(training_path, "font_properties")
        if (not isinstance(font_properties, tuple)) and (len(font_properties) != 5):
            raise ServiceException("font properties must be tuple with length of 5")
        content = font_name + " %d %d %d %d %d" % font_properties
        with open(self.font_properties_file, 'w') as fp:
            fp.write(content)
            fp.flush()
            fp.close()
        # Local path to the 'tessdata' directory
        self.tessdata_path = tessdata_path
        if not exists(self.tessdata_path):
            raise ServiceException("The %s directory does not exist. Aborting." % (self.tessdata_path))
        # Local path to a file containing frequently encountered words
        self.word_list = word_list
        # Set verbose to True to display the training commands output
        self.verbose = verbose

    def _generate_boxfile(self, ttf):
        """ Generate a multipage tif, filled with the training text and generate a boxfile
            from the coordinates of the characters inside it
        """
        ttf_list = [ttf]
        mp = MultiPageTif(self.training_path, self.training_text, self.font_name, ttf_list,
                          self.font_size, self.exp_number, self.lang_name, self.verbose)
        mp.generate_tif()  # generate a multi-page tif, filled with self.training_text
        mp.generate_boxfile()  # generate the boxfile, associated with the generated tif

    def _train_on_boxfile(self):
        """ Run tesseract on training mode, using the generated boxfiles """

        cmd = 'tesseract {prefix}.tif {prefix} -l {lang} -psm {psm} nobatch box.train'.format(
            prefix=self._form_file_prefix(self.exp_number),
            lang=self.base_lang,
            psm=self.base_psm)
        print("cmd: %s" % cmd)
        run = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.training_path)
        display_output(run, self.verbose)

    def _form_file_prefix(self, exp_num):
        prefix = '%s.%s.exp%s' % (self.lang_name, self.font_name, exp_num)
        return prefix

    def _compute_character_set(self):
        """ Computes the character properties set: isalpha, isdigit, isupper, islower, ispunctuation
            and encode it in the 'unicharset' data file

            examples:
            ';' is an punctuation character. Its properties are thus represented
                by the binary number 10000 (10 in hexadecimal).
            'b' is an alphabetic character and a lower case character.
                Its properties are thus represented by the binary number 00011 (3 in hexadecimal).
            W' is an alphabetic character and an upper case character. Its properties are
                thus represented by the binary number 00101 (5 in hexadecimal).
            '7' is just a digit. Its properties are thus represented by the binary number 01000 (8 in hexadecimal).
            '=' does is not punctuation not digit or alphabetic character. Its properties
                 are thus represented by the binary number 00000 (0 in hexadecimal).
        """
        cmd = ['unicharset_extractor']
        for idx in range(self.exp_number):
            cmd.append('%s.box' % (self._form_file_prefix(idx)))
        print("cmd: %s" % " ".join(cmd))
        run = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.training_path)
        display_output(run, self.verbose)

    def _shape_cluster(self):
        """ Shape Cluster character features from all the training pages, and create shapetable """
        cmd = ['shapeclustering -F font_properties -U unicharset']
        for idx in range(self.exp_number):
            cmd.append('%s.tr' % (self._form_file_prefix(idx)))
        cmd = " ".join(cmd)
        print("cmd: %s" % cmd)
        run = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.training_path)
        display_output(run, self.verbose)

    def _mf_training(self):
        """ Cluster character features from all the training pages, and create characters prototype """
        cmd = ['mftraining -F font_properties -U unicharset']
        for idx in range(self.exp_number):
            cmd.append('%s.tr' % (self._form_file_prefix(idx)))
        cmd = " ".join(cmd)
        print("cmd: %s" % cmd)
        run = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.training_path)
        display_output(run, self.verbose)

    def _cntraining(self):
        """ Generate the 'normproto' data file (the character normalization sensitivity prototypes) """
        cmd = ['cntraining']
        for idx in range(self.exp_number):
            cmd.append('%s.tr' % (self._form_file_prefix(idx)))
        print("cmd: %s" % " ".join(cmd))
        run = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.training_path)
        display_output(run, self.verbose)

    def _rename_files(self):
        """ Add the self.dictionary_name prefix to each file generated during the tesseract training process """
        for source_file in GENERATED_DURING_TRAINING:
            target_file = '%s.%s' % (self.lang_name, source_file)
            target_path = os.path.join(self.training_path, target_file)
            source_path = os.path.join(self.training_path, source_file)
            if not os.path.exists(target_path):
                os.rename(source_path, target_path)

    def _dictionary_data(self):
        """ Generate dictionaries, coded as a Directed Acyclic Word Graph (DAWG),
            from the list of frequent words if those were submitted during the Trainer initialization.
        """
        if self.word_list:
            cmd = 'wordlist2dawg %s %s.freq-dawg %s.unicharset' % (self.word_list, self.lang_name,
                                                                   self.lang_name)
            print("cmd: %s" % cmd)
            run = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   cwd=self.training_path)
            display_output(run, self.verbose)

    def _combine_data(self):
        cmd = 'combine_tessdata %s.' % (self.lang_name)
        print("cmd: %s" % cmd)
        run = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.training_path)
        display_output(run, self.verbose)

    def training(self):
        print("**** start training language = %s ****" % self.lang_name)
        """ Execute all training steps """
        for ttf in self.ttf_file_list:
            self._generate_boxfile(ttf)
            self._train_on_boxfile()
            self.exp_number += 1
        self._compute_character_set()

        # self._shape_cluster()
        self._mf_training()
        self._cntraining()
        self._rename_files()
        # 跳过dictionary
        # self._dictionary_data()
        self._combine_data()
        if self.verbose:
            print('The %s.traineddata file has been generated !' % (self.lang_name))

    def clean(self, path=None):
        """ Remove all files generated during tesseract training process """
        print('cleaning...')
        if path is None:
            path = self.training_path
        for root, dirs, files in os.walk(path):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.removedirs(os.path.join(root, name))
            os.removedirs(root)

    def add_trained_data(self):
        """ Copy the newly trained data to the tessdata/ directory """
        traineddata_name = '%s.traineddata' % self.lang_name
        traineddata_path = os.path.join(self.training_path, traineddata_name)
        if self.verbose:
            print('Copying %s to %s.' % (traineddata_path, self.tessdata_path))
        print("**** move traineddata from %s to %s" % (traineddata_path, self.tessdata_path))
        try:
            shutil.copyfile(traineddata_path,
                            join(self.tessdata_path, traineddata_name))  # Copy traineddata fie to the tessdata dir
        except IOError:
            raise IOError("Permission denied. Super-user rights are required to copy %s to %s." % (
                traineddata_name, self.tessdata_path))


def display_output(run, verbose):
    """ Display the output/error of a subprocess.Popen object
        if 'verbose' is True.
    """
    out, err = run.communicate()
    if verbose:
        print(str(out,'utf-8'))
        if err:
            print(str(err,'utf-8'))
