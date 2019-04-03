from __future__ import print_function
from sys import stdout, stderr

from pepper.framework.abstract import AbstractComponent
from pepper.framework.util import Scheduler
from pepper.framework.component import SpeechRecognitionComponent

import threading
from time import time


class StatisticsComponent(AbstractComponent):

    PERFORMANCE_ERROR_THRESHOLD = 0.8

    LIVE_SPEECH = ""
    LIVE_SPEECH_TIMEOUT = 3
    LIVE_SPEECH_TIME = 0

    def __init__(self, backend):
        """
        Construct Statistics Component

        Parameters
        ----------
        backend: Backend
        """
        super(StatisticsComponent, self).__init__(backend)

        speech_recognition = self.require(StatisticsComponent, SpeechRecognitionComponent)  # type: SpeechRecognitionComponent
        vad = speech_recognition.vad
        asr = speech_recognition.asr

        def worker():

            # Create Activation Bar
            activation = int(vad.activation * 10)
            activation_print = "|" * activation + "." * (10 - activation)
            voice_print = ("<{:10s}>" if vad._utterance else "[{:10s}]").format(activation_print)
            empty_voice_print = "[          ]"

            mic_running = self.backend.microphone.running

            mic_rate = self.backend.microphone.rate
            mic_rate_true = self.backend.microphone.true_rate

            cam_rate = self.backend.camera.rate
            cam_rate_true = self.backend.camera.true_rate

            error = (cam_rate_true < cam_rate * self.PERFORMANCE_ERROR_THRESHOLD or
                     mic_rate_true < float(mic_rate) * self.PERFORMANCE_ERROR_THRESHOLD)

            if asr.live:
                self.LIVE_SPEECH = asr.live
                self.LIVE_SPEECH_TIME = time()
            elif time() - self.LIVE_SPEECH_TIME > self.LIVE_SPEECH_TIMEOUT:
                self.LIVE_SPEECH = ""

            print("\rThreads {:2d} | Cam {:4.1f} Hz | Mic {:4.1f} kHz | TTS {:12s} >>> {}".format(
                threading.active_count(),
                cam_rate_true,
                mic_rate_true / 1000.0,
                voice_print if mic_running else empty_voice_print,
                self.LIVE_SPEECH),
                end="", file=(stderr if error else stdout))

        schedule = Scheduler(worker, 0.1)
        schedule.start()
