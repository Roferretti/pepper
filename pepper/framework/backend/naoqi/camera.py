from pepper.framework.abstract.camera import AbstractCamera, AbstractImage
from pepper import NAOqiCameraIndex, CameraResolution

import numpy as np

from random import getrandbits
from threading import Thread
from time import time, sleep


class NAOqiImage(AbstractImage):
    def __init__(self, image, origin, aov):
        super(NAOqiImage, self).__init__(image)

        self._origin = origin
        self._aov = aov

    @property
    def origin(self):
        return self._origin

    @property
    def aov(self):
        return self._aov


class NAOqiCamera(AbstractCamera):
    """
    NAOqi Camera

    Parameters
    ----------
    session: qi.Session
        NAOqi Application Session
    resolution: CameraResolution
        NAOqi Camera Resolution
    rate: int
        NAOqi Camera Rate
    callbacks: list of callable
        On Image Event Callbacks
    index: int
        Which NAOqi Camera to use
    """

    SERVICE = "ALVideoDevice"
    COLOR_SPACE = 9  # YUV442

    RESOLUTION_CODE = {
        CameraResolution.NATIVE: 2,
        CameraResolution.QQQQVGA: 8,
        CameraResolution.QQQVGA: 7,
        CameraResolution.QQVGA: 0,
        CameraResolution.QVGA: 1,
        CameraResolution.VGA: 2,
        CameraResolution.VGA4: 3,
    }

    def __init__(self, session, resolution, rate, callbacks=[], index=NAOqiCameraIndex.TOP):
        super(NAOqiCamera, self).__init__(resolution, rate, callbacks)

        # Get random camera id, to prevent name collision
        self._id = str(getrandbits(128))

        self._resolution = resolution
        self._rate = rate
        self._index = index

        # Connect to Camera Service and Subscribe with Settings
        self._service = session.service(NAOqiCamera.SERVICE)
        self._client = self._service.subscribeCamera(
            self._id, int(index), NAOqiCamera.RESOLUTION_CODE[resolution], NAOqiCamera.COLOR_SPACE, rate)

        # Access Head Motion for Image Coordinates
        self._motion = session.service("ALMotion")

        self._aov = self._service.getAngularPositionFromImagePosition(int(index), [1, 1])

        # Run image acquisition in Thread
        self._thread = Thread(target=self._run)
        self._thread.setDaemon(True)
        self._thread.start()

        self._log.debug("Booted")

    def _run(self):
        while True:
            if self._running:

                t0 = time()

                # Get Yaw and Pitch from Head Sensors
                origin = self._motion.getAngles("HeadYaw", False)[0], self._motion.getAngles("HeadPitch", False)[0]

                # Get Image from Robot
                result = self._service.getImageRemote(self._client)

                if result:

                    # Split Data
                    X, Y, layers, color_space, seconds, milliseconds, data, camera, \
                    angle_left, angle_top, angle_right, angle_bottom = result

                    if self._index == NAOqiCameraIndex.DEPTH:
                        # Depth Images come as uint16
                        self.on_image(np.frombuffer(data, np.uint16).reshape(Y, X))
                    else:
                        # Some Color Math: YUV442 -> RGB Conversion(, which is faster on this machine than on the robot)
                        X2 = X // 2

                        YUV442 = np.frombuffer(data, np.uint8).reshape(Y, X2, 4)

                        RGB = np.empty((Y, X2, 2, 3), np.float32)
                        RGB[:, :, 0, :] = YUV442[..., 0].reshape(Y, X2, 1)
                        RGB[:, :, 1, :] = YUV442[..., 2].reshape(Y, X2, 1)

                        Cr = (YUV442[..., 1].astype(np.float32) - 128.0).reshape(Y, X2, 1)
                        Cb = (YUV442[..., 3].astype(np.float32) - 128.0).reshape(Y, X2, 1)

                        RGB[..., 0] += np.float32(1.402) * Cb
                        RGB[..., 1] += - np.float32(0.71414) * Cb - np.float32(0.34414) * Cr
                        RGB[..., 2] += np.float32(1.772) * Cr

                        # Call On Image Event
                        self.on_image(NAOqiImage(RGB.clip(0, 255).astype(np.uint8).reshape(Y, X, 3), origin, self._aov))
                else:
                    self._service.unsubscribe(self._id)
                    raise RuntimeError("{} could not fetch image".format(self.__class__.__name__))

                # Maintain frame rate
                sleep(max(0, 1. / self.rate - (time() - t0)))