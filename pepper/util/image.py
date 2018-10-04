from pepper.sensor import CocoClassifyClient, OpenFace, FaceClassifier
from pepper import config

from PIL import Image, ImageDraw, ImageFont
import colorsys
import numpy as np

import time
import os


class ImageWriter(object):
    def __init__(self, path=os.path.join(config.PROJECT_ROOT, 'imglog'), extension=".jpeg"):
        """
        Utility to Write Images to File

        Parameters
        ----------
        path: str
            Root directory for images
        extension: str
            Image file type
        """
        self._path = os.path.join(path, time.strftime("%y%m%d-%H%M%S"))
        self._extension = extension
        self._index = 0

        if not os.path.exists(self._path): os.makedirs(self._path)

    @property
    def path(self):
        return self._path

    @property
    def extension(self):
        return self._extension

    def write(self, image):
        Image.fromarray(image).save(os.path.join(self._path, "{:05d}{}".format(self._index, self.extension)))
        self._index += 1


class ImageAnnotator(object):
    def __init__(self):
        """
        Annotate Images with CoCo & OpenFace Bounding Boxes

        Parameters
        ----------
        path: str
            Folder with stored faces
        """

        self._coco = CocoClassifyClient()
        self._openface = OpenFace()
        self._face_classifier = FaceClassifier.from_directory(config.FACE_DIRECTORY)

        self._font_size = 12
        self._font_name = "Montserrat-Regular.ttf"
        self._font = ImageFont.truetype(os.path.join(os.path.dirname(__file__), self._font_name), self._font_size)

    @property
    def coco(self):
        return self._coco

    @property
    def openface(self):
        return self._openface

    @property
    def face_classifier(self):
        return self._face_classifier

    def annotate_batch(self, directory, output_directory=None, extension='.png',
                       object_threshold=config.OBJECT_CONFIDENCE_THRESHOLD,
                       face_threshold=config.FACE_RECOGNITION_KNOWN_CONFIDENCE_THRESHOLD):

        if not output_directory:
            output_directory = os.path.join(directory, 'annotated')
        if not os.path.exists(output_directory): os.makedirs(output_directory)

        image_paths = [path for path in os.listdir(directory) if os.path.isfile(os.path.join(directory, path))]

        for index, image_path in enumerate(image_paths):
            print "\rAnnotating Image {:d}/{:d}".format(index + 1, len(image_paths)),
            image = Image.open(os.path.join(directory, image_path))
            image = self.annotate(image, object_threshold, face_threshold)
            image.save(os.path.join(output_directory, image_path.replace(os.path.splitext(image_path)[1], extension)))
        print("\n")

    def annotate(self, image,
                 object_threshold=config.OBJECT_CONFIDENCE_THRESHOLD,
                 face_threshold=config.FACE_RECOGNITION_KNOWN_CONFIDENCE_THRESHOLD):
        """
        Annotate Image

        Parameters
        ----------
        image: Image.Image
            Input Image
        object_threshold: float
            Confidence Threshold for Object Recognition Annotations
        face_threshold: float
            Confidence Threshold for Face Recognition Annotations

        Returns
        -------
        image: Image.Image
            Annotated Image
        """
        draw = ImageDraw.Draw(image)
        image_np = np.array(image)

        # Annotate Objects
        object_infos = self.coco.classify(image_np)
        for object_info, confidence, bounds in zip(*object_infos):
            if confidence > object_threshold:

                text = "[{:4.0%}] {}".format(confidence, object_info['name'])

                color = colorsys.hsv_to_rgb(float(object_info['id'] - 1) / self.coco.CLASSES, 1, 1)
                color = tuple((np.array(color) * 255).astype(np.uint8))

                y0, x0, y1, x1 = bounds
                x0 *= image.width
                y0 *= image.height
                x1 *= image.width
                y1 *= image.height

                self._draw_bounds(draw, [x0, y0, x1, y1], color, 3)
                self._draw_text(draw, [x0, y0, x1, y1], text, color, (0, 0, 0))

        # Annotate Faces
        face = self.openface.represent(image_np)

        if face:
            bounds, representation = face
            name, confidence, distance = self._face_classifier.classify(representation)

            text = "[{:4.0%}] {}".format(confidence, name)

            x0, y0, x1, y1 = int(bounds.x), int(bounds.y), int(bounds.x + bounds.width), int(bounds.y + bounds.height)


            color = (255, 255, 255)

            self._draw_bounds(draw, [x0, y0, x1, y1], color, 3)
            self._draw_text(draw, [x0, y0, x1, y1], text, color, (0, 0, 0))

        return image

    @staticmethod
    def _draw_bounds(draw, bounds, fill, width):
        """
        Parameters
        ----------
        draw: ImageDraw.ImageDraw
            ImageDraw Object
        bounds: list
            [x0, y0, x1, y1]
        """
        x0, y0, x1, y1 = bounds
        draw.line([x0, y0, x0, y1], fill, width)
        draw.line([x0, y0, x1, y0], fill, width)
        draw.line([x1, y1, x0, y1], fill, width)
        draw.line([x1, y1, x1, y0], fill, width)

    def _draw_text(self, draw, bounds, text, fill, color):
        """
        Parameters
        ----------
        draw: ImageDraw.ImageDraw
            ImageDraw Object
        bounds: list
            [x0, y0, x1, y1]
        text: str
        """
        x0, y0, x1, y1 = bounds
        draw.rectangle([x0, y1 - self._font_size, x1, y1], fill)
        draw.text([x0 + 5, y1 - self._font_size], text, color, self._font)


if __name__ == '__main__':
    ImageAnnotator().annotate_batch("/Users/bram/Documents/pepper/pepper/imglog/181004-120211")
