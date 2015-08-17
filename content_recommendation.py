# -*- coding: utf-8 -*-
import random
import cv2
import numpy as np
import time
import os
import sys
import threading
import Queue
import logging
from content.jokes import jokes
from content.math_jokes import math_jokes
from content.anti_jokes import anti_jokes
from content.content import *
from Tkinter import Tk, BOTH
from ttk import Frame, Button, Style
from config import *

# Enable logging
logging.basicConfig(filename='logs/log' + time.strftime("%Y%m%d--%H-%M-%S") + '.log', level=logging.INFO)

# Add pycaffe to the path
sys.path.insert(0, CAFFE_ROOT + 'python')
# Deactivate caffe's logging
os.environ['GLOG_minloglevel'] = '2'
import caffe

# Use the first camera available
try:
    camera = cv2.VideoCapture(-1)
except:
    logging.critical("Error trying to find a usable camera.")
    raise

# Get an image from the camera
def get_image():
    _, image = camera.read()
    return image

# Wait for the webcam to be synchronized
for i in xrange(RAMP_FRAMES):
     temp = get_image()

def load_caffe_network():
    if GPU_MODE:
        # Use GPU mode (needs CUDA)
        caffe.set_mode_gpu()
    else:
        # Use CPU mode
        caffe.set_mode_cpu()

    # Import the caffe model
    net = caffe.Net(CAFFE_MODEL_PATH,
                    CAFFE_WEIGHTS_PATH,
                    caffe.TEST)
    return net

# Load caffe
net = load_caffe_network()

# Populate the content
def populate_content():
    Content.all_content.append(Text('Blague Carambar', map(lambda j: '\n'.join(j), jokes), categories = ['text', 'naive humor', 'carambar']))
    Content.all_content.append(Text('Math joke', map(lambda j: '\n'.join(j), math_jokes), categories = ['text', 'science', 'math_jokes jokes']))
    Content.all_content.append(Text('Anti-joke', map(lambda j: '\n'.join(j), anti_jokes), categories = ['text', 'dark humor', 'anti jokes']))
    Content.all_content.append(WebImage('Chaton', kitten, categories = ['image', 'pets', 'kitten']))
    Content.all_content.append(WebImage('Calvin & Hobbes', calvin_and_hobbes, categories=['comic strip', 'naive humor', 'calvin and hobbes']))
    Content.all_content.append(WebImage('Cyanide & Happiness', cyanide_and_happiness, categories=['comic strip', 'dark humor', 'cyanide and happiness']))
    Content.all_content.append(WebImage('xkcd', xkcd, categories=['comic strip', 'science', 'xkcd']))
    Content.all_content.append(WebGif('Gif d\'animaux', animal_gifs, categories = ['image', 'pets', 'animal gifs']))

def preprocess_image(image):
    ## Brightness and contrast enhancement
    #max_intensity = 255.0
    #phi = 1.1
    #theta = 1.1
    #net_data = (max_intensity/phi)*(camera_capture/(max_intensity/theta))**0.5
    #return net_data
    return image

# Detect the bouding box of the faces
def detect_face(image):
    # See http://docs.opencv.org/modules/objdetect/doc/cascade_classification.html
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_alt.xml')
    # We ask a minimum size of 150px*150px for the face
    # Helps remove false positives
    min_size = (150,150)
    # To find the faces, HaarDetectObjets will try the original image, then
    # downsize it by haar_scale, try again, and so on
    haar_scale = 1.1 
    # Specify how many neighbors a candidate rectangle should have to retain it
    min_neighbors = 5

    # Detect the faces
    faces = face_cascade.detectMultiScale(
                        image,
                        scaleFactor=haar_scale,
                        minNeighbors=min_neighbors,
                        minSize=min_size,
                        flags = cv2.cv.CV_HAAR_SCALE_IMAGE)
    return faces

# Crop the CV image according to a rectangle
def img_crop(image, crop_box):
    # crop_box (x, y, width, height)
    return image[crop_box[1]:crop_box[1] + crop_box[3], crop_box[0]:crop_box[0] + crop_box[2]]

def get_emotion(net):
    # Get the picture from the camera
    camera_capture = get_image()
    
    # Detect the faces in the greyscale image
    cv_im=cv2.cvtColor(camera_capture, cv2.COLOR_BGR2GRAY)
    faces=detect_face(cv_im)
    
    if len(faces) > 0:
        # Crop the face and resize to 256x256
        camera_capture = img_crop(camera_capture, faces[0])
        camera_capture = cv2.resize(camera_capture, (256, 256))
    else:
        # Abort if no face has been found
        return None
    
    # Preprocessing
    net_data = preprocess_image(camera_capture)
    transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})
    transformer.set_transpose('data', (2,0,1))
    transformer.set_raw_scale('data', 255)
    # TODO: substract the mean file ?
    # BUG: incompatible shapes
    #transformer.set_mean('data', np.load(CAFFE_ROOT + 'data/custom/custom_training_mean.npy').mean(1).mean(1))
    
    net.blobs['data'].reshape(1,3,227,227)
    net.blobs['data'].data[...] = transformer.preprocess('data', net_data)
    # Send the picture through the network
    return net.forward()

# Quantify the boost value according to the probability of each emotion
def convert_emotions_to_boost(probabilities):
    happy_probability = probabilities[1]
    sad_probability = probabilities[2]
    angry_probability = probabilities[3]
   
    # Positive emotion = happiness
    positive = happy_probability
    # Negative emotion = sadness + anger
    # TODO : where should we include "neutral" emotions (neutral and surprise) ?
    negative = (sad_probability + angry_probability) / 2

    if positive > 2 * negative:
        logging.info("Enjoyed a lot")
        return STRONG_BOOST
    elif positive > negative:
        logging.info("Enjoyed a bit")
        return DEFAULT_BOOST
    else:
        logging.info("Didn't like it")
        return NEGATIVE_BOOST

# Custom thread for the emotion detector
class EmotionDetector(threading.Thread):
    def __init__(self, q):
        super(EmotionDetector, self).__init__()
        self._stop = threading.Event()
        self._queue = q

    def stop(self):
        self._stop.set()

    def run(self):
        try:
            # Run until the user stops it
            while not self._stop.isSet():
                out = get_emotion(net)
                # Add the output of the network to the queue
                if out:
                    self._queue.put(out['prob'][0])
        except Exception as e:
            logging.critical("Emotion detector died..." + str(e))
            return

sequence = None
detector = None
last_content = None

# Finish the current content and detection
# Switch to the next content and start a new detection sequence
def show_next_content():
    global last_content
    # Create a new thread and a new queue
    sequence = Queue.Queue()
    detector = EmotionDetector(sequence)
    if last_content:
        # Stop the previous detection and clear the UI
        stop_detection()
    # Get the next content to show
    content = Content.get_content(weighted=WEIGHTED_RECOMMENDATION)
    logging.info("Current content : " + str(content))
    # Update the last_content variable
    last_content = content
    # Try to show the content
    try:
        content.show(gui=root) 
    except:
        logging.warn("Unexpected error" + str(sys.exc_info()[0]))
        return
    # Start the emotion detector
    detector.start()

# Stop the detector and clear the UI
def stop_detection():
    global sequence
    global detector
    if last_content:
        # Clear the UI
        last_content.hide(gui=root)
    # If the detector is running, send it the stop signal and wait for it to finish
    if detector and detector.isAlive():
        detector.stop()
        detector.join()
    # Extract the emotion sequence
    if sequence:
        emotions = sequence.queue
        logging.info(map(lambda e: EMOTIONS[e.argmax()], emotions))

        if len(emotions) > 0:
            # Compute the average for each emotion
            probabilities = sum(emotions) / len(emotions)
            logging.info(probabilities)
            # Quantify the boost value
            boost_type = convert_emotions_to_boost(probabilities)
            # Boost the content preferences
            last_content.boost(boost_type)
        else:
            logging.info("No face detected")
            return
    # Log the new content values
    logging.info(Content.all_categories)

# Main window
class MainFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.parent.title("Content recommendation - Test prototype")
        self.style = Style()
        self.style.theme_use("clam")
        self.pack(fill=BOTH, expand=1)
        # Create the buttons
        quitButton = Button(self, text="Quit", command=self.quit)
        quitButton.pack()
        button = Button(self, text="Show next content", command=show_next_content)
        button.pack()

    def quit(self):
        stop_detection()
        Frame.quit(self)

root = None

# Centering function
def center(win, size):
    w = win.winfo_screenwidth()
    h = win.winfo_screenheight()
    x = w/2 - size[0]/2
    y = h/2 - size[1]/2
    root.geometry("%dx%d+%d+%d" % (size + (x, y)))

def main():
    global root
    # Populate the content
    populate_content()
    
    # Launch the GUI
    root = Tk()
    # Center the window
    center(root, (800, 800))
    app = MainFrame(root)
    root.bind('<Control-c>', root.quit)
    root.mainloop()

def exit():
    logging.info("Exit, bye !")
    # Release the camera
    global camera
    camera.release()
    del(camera)
    
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    exit()
