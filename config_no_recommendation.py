# -*- coding: utf-8 -*-

CAFFE_ROOT = 'distribute/'
CAFFE_MODEL_PATH = 'model/deploy.prototxt'
CAFFE_WEIGHTS_PATH = 'model/fer_alexnet_weights.caffemodel'

GPU_MODE = False

DEFAULT_BOOST = 1.4
STRONG_BOOST = 1.9
NEGATIVE_BOOST = 0.715

EMOTIONS = ["neutral","happy","sad","angry/disgusted","(unused #4)","surprised/afraid","(unused #6)"]

# Ignore the first 30 frames so the webcam can synchronize and adjust to light
RAMP_FRAMES = 30

MAX_CONTENT = 50

WEIGHTED_RECOMMENDATION = False
