# -*- coding: utf-8 -*-

"""
API allowing the user to generate "black on white" multipage tif images
using a specified text, font and font-size, and to generate "box-files":
a file containing a list of characters and their associated box coordinates
and page number.

UTF-8 encoded characters are supported.
"""

import random
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import numpy as np
from django_web.model import *
import glob
import subprocess
import os
import codecs


class MultiPageTif(object):
    """ A class allowing generation of a multi-page tif. """

    def __init__(self, training_path, text, font_name, ttf_file_list, fontsize, exp_number,
                 lang_name, verbose):
        self.training_path = training_path
        # Width of the generated tifs (in px)
        self.W = 800
        # Height of the generated tifs (in px)
        self.H = 600
        # X coordinate of the first letter of the page
        self.start_x = 20
        # Y coordinate of the first letter of the page
        self.start_y = 20

        # Text to be written in generated multipage tif
        self.text = [word for word in text.split(' ')]

        # Font used when "writing" the text into the tif
        self.fontsize = fontsize
        self.true_type_list = list()
        for ttf_file in ttf_file_list:
            self.true_type_list.append(ImageFont.truetype(ttf_file, fontsize))
        # Name of the font, used for generating the file prefix
        self.font_name = font_name

        # Name of the tesseract dictionary to be generated. Used for generating the file prefix.
        self.dictionary_name = lang_name

        # Prefix of the generated multi-page tif file
        self.prefix = ".".join([lang_name, font_name, "exp" + str(exp_number)])

        # A list of boxfile lines, each one of the form "char x0 y x1 y1 page_number"
        self.boxlines = []

        # prefix of all temporary single-page tif files
        self.indiv_page_prefix = 'page'

        # Set verbose to True to display output
        self.verbose = verbose
        # 设定行间距和列间距
        self.row_gap = 30
        self.col_gap = 7
        self.word_per_page = 50
        self.wrap_len = 12

    def generate_tif(self):
        """ Create several individual tifs from text and merge them
            into a multi-page tif, and finally delete all individual tifs.
        """
        # self._fill_pages()
        self._new_fill_pages()
        self._multipage_tif()
        # FIXME
        self._clean()

    def generate_boxfile(self):
        """ Generate a boxfile from the multipage tif.
            The boxfile will be named {self.prefix}.box
        """
        boxfile_name = self.prefix + '.box'
        boxfile_path = os.path.join(self.training_path, boxfile_name)
        if self.verbose:
            print("Generating boxfile %s" % (boxfile_path))
        with codecs.open(boxfile_path, 'w', 'utf-8') as boxfile:
            for boxline in self.boxlines:
                # if sys.version_info.major == 3:
                #     boxfile.write(boxline + '\n')
                # else:
                #     boxfile.write(boxline.encode('utf-8') + '\n')  # utf-8 characters support
                boxfile.write(boxline + '\n')

    def _new_tif(self, color="white"):
        """ Create and returns a new RGB blank tif, with specified background color (default: white) """
        return Image.new("L", (self.W, self.H), color=color)

    def _save_tif(self, tif, page_number):
        """ Save the argument tif using 'page_number' argument in filename.
            The filepath will be {self.indiv_page_prefix}{self.page_number}.tif
        """
        file_name = "%s%s%s" % (self.indiv_page_prefix, str(page_number), '.tif')
        file_path = os.path.join(self.training_path, file_name)
        tif.save(file_path)

    def _fill_pages(self):
        """ Fill individual tifs with text, and save them to disk.
            Each time a character is written in the tif, its coordinates will be added to the self.boxlines
            list (with the exception of white spaces).

            All along the process, we manage to contain the text within the image limits.
        """
        tif = self._new_tif()
        draw = ImageDraw.Draw(tif)
        page_nb = 0
        x_pos = self.start_x
        y_pos = self.start_y
        if self.verbose:
            print('Generating individual tif image %s' % (self.indiv_page_prefix + str(page_nb) + '.tif'))
        for true_type in self.true_type_list:
            if x_pos != self.start_x or y_pos != self.start_y:
                x_pos = self.start_x
                y_pos = self.start_y
                self._save_tif(tif, page_nb)  # save individual tif
                page_nb += 1
                if self.verbose:
                    print('Generating individual tif image %s' % (self.indiv_page_prefix + str(page_nb) + '.tif'))
                tif = self._new_tif()  # new page
                draw = ImageDraw.Draw(tif)  # write on this new page
            for word in self.text:
                word += ' '  # add a space between each word
                wordsize_w, wordsize_h = true_type.getsize(word)
                # Check if word can fit the line, if not, newline
                # if newline, check if the newline fits the page
                # if not, save the current page and create a new one
                if not word_fits_in_line(self.W, x_pos, wordsize_w):
                    if newline_fits_in_page(self.H, y_pos, wordsize_h):
                        # newline
                        x_pos = self.start_x
                        y_pos += wordsize_h
                    else:
                        # newline AND newpage
                        x_pos = self.start_x
                        y_pos = self.start_y
                        self._save_tif(tif, page_nb)  # save individual tif
                        page_nb += 1
                        if self.verbose:
                            print(
                                'Generating individual tif image %s' % (self.indiv_page_prefix + str(page_nb) + '.tif'))
                        tif = self._new_tif()  # new page
                        draw = ImageDraw.Draw(tif)  # write on this new page
                # write word
                for char in word:
                    char_w, char_h = true_type.getsize(char)  # get character height / width
                    offset_x, offset_y = true_type.getoffset(char)
                    top_left = (x_pos + offset_x, y_pos + offset_y)  # character top-left corner coordinates
                    bottom_right = (x_pos + char_w, y_pos + char_h)  # character bottom-roght corner coordinates
                    draw.text((x_pos, y_pos), char, fill="black", font=true_type)  # write character in tif file
                    if char != ' ':
                        # draw.rectangle([(char_x0, char_y0),(char_x1, char_y1)], outline="red")
                        self._write_boxline(char, top_left, bottom_right, self.H, page_nb)  # add coordinates to boxfile
                    x_pos += char_w
        self._save_tif(tif, page_nb)  # save last tif

    def _write_boxline(self, char, top_left, bottom_right, height, page_nb):
        """ Generate a boxfile line given a character coordinates, and append it to the
            self.boxlines list.
        """
        # top-left corner coordinates in tesseract particular frame
        tess_top_left = pil_coord_to_tesseract(*top_left, height)
        # bottom-right corner coordinates in tessseract particular frame
        tess_bottom_right = pil_coord_to_tesseract(*bottom_right, height)
        tess_bottom_left = (tess_top_left[0], tess_bottom_right[1])
        tess_top_right = (tess_bottom_right[0], tess_top_left[1])
        boxline = '%s %d %d %d %d %d' % (
            char, tess_bottom_left[0], tess_bottom_left[1], tess_top_right[0], tess_top_right[1], page_nb)
        self.boxlines.append(boxline)

    def _multipage_tif(self):
        """ Generate a multipage tif from all the generated tifs.
            The multipage tif will be named {self.prefix}.tif
        """
        # cmd = ['convert']  # ImageMagick command `convert` can merge individual tifs into a multipage tif file
        cmd = ['magick']
        path = os.path.join(self.training_path, '%s*.tif' % self.indiv_page_prefix)
        tifs = sorted(glob.glob(path), key=os.path.getmtime)
        cmd.extend(tifs)  # add all individual tifs as arguments
        multitif_name = self.prefix + '.tif'
        multitif_path = os.path.join(self.training_path, multitif_name)
        cmd.append(multitif_path)  # name of the result multipage tif
        if self.verbose:
            print('Generating multipage-tif %s' % (multitif_path))
        subprocess.call(cmd)  # merge of all individul tifs into a multipage one

    def _clean(self):
        """ Remove all generated individual tifs """
        if self.verbose:
            print("Removing all individual tif images")
        path = os.path.join(self.training_path, '%s*.tif' % self.indiv_page_prefix)
        tifs = glob.glob(path)  # all individual tifd
        for tif in tifs:
            if os.path.exists(tif):
                os.remove(tif)

    def _new_fill_pages(self):
        word_per_page = self.word_per_page
        text = "".join(self.text)
        text = text.replace(" ", "")
        # text = list(text)
        # random.shuffle(text)
        word_len = len(text)
        page_sum = int(word_len / word_per_page) + (1 if word_len % word_per_page > 0 else 0)
        page_nb = 0
        for true_type in self.true_type_list:
            for index in range(page_sum):
                sub_text = text[index * word_per_page:(index + 1) * word_per_page]
                self._ttf_plot(true_type, sub_text, self.fontsize, page_nb, self.wrap_len)
                page_nb += 1

    def _ttf_plot(self, ttf_font, word: str, size: int, page_nb: int, wrap_len: int = 10):
        """
        根据给的true type字体生成文字图片和对应的box文件
        :param ttf_font: ImageFont.FreeTypeFont实例
        :param word: 需要绘制的文字
        :param size: 文字大小，即绘制在size x size的一个方格中
        :param wrap_len: 每行最多绘制的文字数量，超过则自动换行
        :return:
        """
        if self.verbose:
            print('Generating individual tif image %s' % (self.indiv_page_prefix + str(page_nb) + '.tif'))
        row_gap = self.row_gap  # 行间距
        col_gap = self.col_gap  # 列间距
        # if word is None or len(word) == 0:
        word_len = len(word)
        row_num = int(word_len / wrap_len) + (1 if word_len % wrap_len > 0 else 0)
        img_height = int(size * row_num + row_gap * row_num) + self.start_y*2  # 计算图片高度
        col_num = 0
        if word_len < wrap_len:
            col_num = word_len
        else:
            col_num = wrap_len
        img_width = int(col_num * size + col_gap * (col_num - 1)) + self.start_x*2  # 计算图片宽度
        image = Image.new("L", (img_width, img_height), 255)  # 生成空白图像
        draw = ImageDraw.Draw(image)  # 绘图句柄
        box_array = list()  # 存放文字的box信息
        y = self.start_y
        for row in range(row_num):
            # 计算文字左上角的坐标
            x = self.start_x
            for col in range(col_num):
                index = row * wrap_len + col
                if index >= word_len:
                    break
                char = word[index]
                draw.text((x, y), char, font=ttf_font)  # 绘图
                offsetx, offsety = ttf_font.getoffset(char)  # 获得文字的offset位置
                width, height = ttf_font.getsize(char)  # 获得文件的大小
                top_left =  [offsetx + x, offsety + y]
                # top_left = [x, y]
                bottom_right = [x + width, y + height]
                # 写入box行
                self._write_boxline(char, top_left, bottom_right, img_height, page_nb)
                # 改变横坐标位置
                x += width + col_gap
            y += size + row_gap
        # 存储图片
        self._save_tif(image, page_nb)


# Utility functions
def word_fits_in_line(pagewidth, x_pos, wordsize_w):
    """ Return True if a word can fit into a line. """
    return (pagewidth - x_pos - wordsize_w) > 0


def newline_fits_in_page(pageheight, y_pos, wordsize_h):
    """ Return True if a new line can be contained in a page. """
    return (pageheight - y_pos - (2 * wordsize_h)) > 0


def pil_coord_to_tesseract(pil_x, pil_y, tif_h):
    """ Convert PIL coordinates into Tesseract boxfile coordinates:
        in PIL, (0,0) is at the top left corner and
        in tesseract boxfile format, (0,0) is at the bottom left corner.
    """
    return pil_x, tif_h - pil_y
