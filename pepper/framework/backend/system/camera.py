from pepper.framework.abstract import AbstractCamera, AbstractImage
from pepper.framework.util import Scheduler
from pepper import CameraResolution

import cv2

from time import time, sleep


class SystemImage(AbstractImage):
    @property
    def origin(self):
        return 0, 0

    @property
    def aov(self):
        return 0.55, 0.41


class SystemCamera(AbstractCamera):
    def __init__(self, resolution, rate, callbacks=[], index=0):
        """
        System Camera

        Parameters
        ----------
        resolution: pepper.framework.CameraResolution
        rate: int
        callbacks: list of callable
        index: int
        """
        super(SystemCamera, self).__init__(resolution, rate, callbacks)

        # Get Camera and request resolution
        self._camera = cv2.VideoCapture(index)

        if not self.resolution == CameraResolution.NATIVE:
            self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        # Check if camera is working
        if not self._camera.isOpened():
            raise RuntimeError("{} could not be opened".format(self.__class__.__name__))

        # Run Image acquisition in Thread
        self._scheduler = Scheduler(self._run, name="SystemCameraThread")
        self._scheduler.start()

        self._log.debug("Booted")

    def _run(self):
        t0 = time()

        # Get frame from camera
        status, image = self._camera.read()

        if status:
            if self._running:

                # Resize Image and Convert to RGB
                image = cv2.resize(image, (self.width, self.height))
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                # Call On Image Event
                self.on_image(SystemImage(image))
        else:
            self._camera.release()
            raise RuntimeError("{} could not fetch image".format(self.__class__.__name__))

        # Maintain frame rate
        sleep(max(0, 1. / self.rate - (time() - t0)))
