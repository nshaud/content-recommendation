# Content recommendation based on emotion recognition with Caffe

## Requirements

* Python 2.7
* Linux 64 bits (or 32 bits if you compile caffe yourself)
* A connection to the Internet for content recovery
* The requirements for *pycaffe*, i.e. :

    `for req in $(cat distribute/python/requirements.txt); do pip install $req; done`

## Features

This software uses an artificial neural network and feeds it the webcam stream. The neural network (derived from *AlexNet*) is implemented with [Caffe](http://github.com/BVLC/caffe) and does emotion recognition. Different categories of content are shown. According to the user's emotional response to the content, some categories will be prefered.

## Usage

Before running this software, please configure the `config.py` file to suit your needs. Importantly, if you already have Caffe installed on your computer, you should provide the path your Caffe installation.

* Run `content_recommendation.sh`
* Logs are kept under the `logs/` directory
