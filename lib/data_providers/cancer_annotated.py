from data_provider import DataProvider
import os
from paths import Paths
import pandas as pd
import numpy as np
import random
import cv2


EXPEND_LENGTH = 100

class CancerAnnotated(DataProvider):
    def __init__(self, data_name):
        self._data_name = data_name
        train_path = os.path.join(Paths.data_path, data_name, 'annotations/train.csv')
        test_path = os.path.join(Paths.data_path, data_name, 'annotations/test.csv')
        data_type = {
            'image_name': np.str,
            'x1': np.int,
            'y1': np.int,
            'x2': np.int,
            'y2': np.int
        }
        self._train_df = pd.read_csv(train_path, dtype=data_type)
        self._test_df = pd.read_csv(test_path, dtype=data_type)
        self._train_list = list(self._train_df.index)
        random.shuffle(self._train_list)
        self._test_list = list(self._test_df.index)
        self._test_size = len(self._test_list)
        self._train_index = 0
        self._test_index = 0

    @staticmethod
    def _get_batch_ids(id_list, id_index, batch_size):
        if id_index + batch_size <= len(id_list):
            batch_ids = id_list[id_index:(id_index + batch_size)]
        else:
            batch_ids = id_list[id_index:] + id_list[:(batch_size + id_index - len(id_list))]
        next_id_index = (id_index + batch_size) % len(id_list)
        return batch_ids, next_id_index

    def _crop_image(self, image_name, x1, y1, x2, y2):
        image_path = os.path.join(Paths.data_path, self._data_name, 'images', image_name)
        assert os.path.exists(image_path), \
            'image {} is not existed'.format(image_path)
        img = cv2.imread(image_path)
        height, width, _ = img.shape
        x1 = max(x1-EXPEND_LENGTH, 0)
        y1 = max(y1-EXPEND_LENGTH, 0)
        x2 = min(x2+EXPEND_LENGTH, width-1)
        y2 = min(y2+EXPEND_LENGTH, height-1)
        img_crop = img[x1: x2, y1: y2, :]
        return img_crop

    def _get_batch_data(self, df, batch_ids):
        batch_data = np.hstack([
            self._crop_image(df['image_name'][index_id], df['x1'][index_id], df['y1'][index_id], \
                             df['x2'][index_id], df['y2'][index_id])
            for index_id in batch_ids
        ])
        batch_label = np.hstack([
            df['label'][index_id] for index_id in batch_ids
        ])
        return batch_data, batch_label

    def next_batch(self, batch_size, phase):
        assert phase in ('train', 'test')
        batch_data = None
        batch_label = None
        if phase == 'train':
            batch_ids, self._train_index = self._get_batch_ids(self._train_list, self._train_index, batch_size)
            batch_data, batch_label = self._get_batch_data(self._train_df, batch_ids)
        elif phase == 'test':
            batch_ids, self._test_index = self._get_batch_ids(self._test_list, self._test_index, batch_size)
            batch_data, _ = self._get_batch_data(self._test_df, batch_ids)
        return batch_data, batch_label
