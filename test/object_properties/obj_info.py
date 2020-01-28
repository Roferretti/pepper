from util import clean_color_name, detect_objects, dominant_cluster, stats, color_mapping

from matplotlib import colors as mcolors
from matplotlib import pyplot as plt
from PIL import Image
from datetime import datetime

import numpy as np

import os
import json
import sqlite3


ROOT = './data/20190930_133826'
OBJ_HANDLE = "_obj.json"
RGB_HANDLE = "_rgb.png"
DEPTH_HANDLE = "_depth.npy"
META_HANDLE = "_meta.json"


def read_dir(root):
    """
    Read the directory with generated images, objects and associated metadata.
    :param root: directory path
    :return: images and objects in the directory (AbstractImage, list)
    """

    images = [item for item in os.listdir(root) if os.path.isdir(os.path.join(root, item))]

    for image in images:
        img_path = os.path.join(root, image)
        objects = [os.path.join(img_path, obj) for obj in os.listdir(img_path)]

        yield img_path, objects


def read_object_properties(obj_path):
    """
    Retrieve object data and metadata.
    :param obj_path: object path
    :return: object data and metadata
    """

    with open(os.path.join(obj_path, META_HANDLE[1:])) as meta_file:
        meta_info = json.load(meta_file)

    obj_type = meta_info['name']
    obj_confidence = meta_info['confidence']
    obj_bounds = meta_info['bounds']
    obj_img = Image.open(os.path.join(obj_path, RGB_HANDLE[1:]))
    obj_rgb = np.array(obj_img).astype('float')

    return obj_type, obj_confidence, obj_bounds, obj_rgb, obj_img


def map_colors(keywords):
    """
    Translate matplotlib colors from hex to rgb
    :return: dictionary mapping from normalized rgb values to 1099 cleaned matplotlib color names
    """

    rgb_mapping = dict()

    for name, value in dict(mcolors.get_named_colors_mapping()).items():
        rgb_value = mcolors.to_rgb(value)
        color_name = clean_color_name(name, keywords)
        rgb_mapping[rgb_value] = color_name

    return rgb_mapping


def save_types(obj, rgb_mapping):
    """
    Save object images to type directories.
    :param obj:
    :param rgb_mapping:
    :return:
    """
    obj_type, obj_confidence, obj_bounds, obj_rgb, obj_img = read_object_properties(obj)
    if obj_confidence < 0.5 or obj_type == 'person':
        return 'id', 'features'
    else:
        result, clusters = detect_objects(obj_rgb, obj_img)
        dom_cluster = dominant_cluster(result, clusters)
        dom_result = [res for res in result if res[1] == dom_cluster]
        avg_triplet, mode_triplet, median_triplet = stats(dom_result)
        obj_features = avg_triplet + mode_triplet + median_triplet
        obj_color = color_mapping(avg_triplet, rgb_mapping)
        obj_id = os.path.basename(obj)
        print('{} {}'.format(obj_color, obj_type))

        if not os.path.exists(os.path.join('./results', obj_type)):
            os.makedirs(os.path.join('./results', obj_type))
        plt.savefig('./results/{}/{}'.format(obj_type, obj_id))

        return obj_id, obj_features, obj_color


def total_count(paths):
    """

    :return:
    """
    img = len([(img_path, objects) for img_path, objects in read_dir(ROOT) if any(obj not in paths for obj in objects)])
    obj = len([obj for img_path, objects in read_dir(ROOT) for obj in objects if obj not in paths])

    return img, obj


def read_color_mapping(c):

    c.execute('SELECT * FROM rgb_mapping')
    mapping = dict()
    for row in c:
        mapping[eval(row[0])] = row[1]

    return mapping


def create_color_mapping(conn, c):

    color_keywords = ['aqua', 'black', 'blue', 'fuchsia', 'gray', 'green', 'lime', 'maroon', 'navy', 'olive',
                      'purple', 'red', 'silver', 'teal', 'white', 'yellow', 'grey', 'brown', 'orange', 'pink',
                      'turquoise', 'lavender', 'magenta']

    mapping = map_colors(color_keywords)

    c.execute('CREATE TABLE rgb_mapping(rgb TEXT, name TEXT);')
    for key, value in mapping.items():
        c.execute('INSERT INTO rgb_mapping VALUES (?, ?);', (str(key), str(value)))
    conn.commit()

    return mapping


def read_object_info(c):
    c.execute('SELECT path FROM object_info')
    paths = []
    for row in c:
        paths.append(str(row[0]))

    return paths


def create_object_info(conn, c):
    c.execute('CREATE TABLE object_info(id TEXT, path TEXT, features TEXT, color TEXT);')
    conn.commit()


def main():

    total_start = datetime.now()
    conn = sqlite3.connect('instances.db')
    cur = conn.cursor()
    try:
        rgb_mapping = read_color_mapping(cur)
    except sqlite3.OperationalError:
        rgb_mapping = create_color_mapping(conn, cur)
    try:
        known_paths = read_object_info(cur)
    except sqlite3.OperationalError:
        create_object_info(conn, cur)
        known_paths = []

    total_img, total_obj = total_count(known_paths)
    img_count = 0
    obj_count = 0

    for image, objects in read_dir(ROOT):
        unknown_objects = [obj for obj in objects if obj not in known_paths]
        if len(unknown_objects) > 0:
            img_count += 1
        for obj_path in unknown_objects:
            obj_count += 1
            obj_start = datetime.now()
            print('Processing image {}/{}, object {}/{}.'.format(img_count, total_img, obj_count, total_obj))
            print(obj_path)
            obj_id, obj_features, obj_color = save_types(obj_path, rgb_mapping)
            if obj_id == 'id':
                print('Object could not be processed.')
            else:
                cur.execute('INSERT INTO object_info VALUES (?, ?, ?, ?);',
                            (str(obj_id), str(obj_path), str(obj_features), str(obj_color)))
                conn.commit()
                obj_end = datetime.now()
                print('Object processing time: {}'.format(obj_end - obj_start))
                print('Total elapsed time: {}'.format(obj_end - total_start))
                print('\n')

    conn.close()


if __name__ == '__main__':

    main()