# Art Tracing Overlay

Desktop utility designed mainly for me but also for other artists or designers. Allows users to overlay references images on top of other applications for tracing and other features to get rid of the need to switch windows constantly.

## Overview

Project provides a lightweight overlay window that can display images from local files or URLs provided as input by the user. There are quality of life shortcuts to toggle visibility completely off or on instantly instead of incrementally, a ghost mode to click through the image and a drag and drop feature for input.

## Features

* **Interactability**:
    * **Ghost Mode**: Make the window ignore mouse inputs, allowing user to work on the canvas underneath
    * **Interactive Mode**: Enables dragging, resizing, and accessing the control bar
    * **Appearance Adapatation**: For the user's comfort and for design's sake, the UI adjusts its control bar background and buttons color based on the average color of the current image
* **Various Settings**:
    * **Opacity Control**: Make the window ignore mouse inputs, allowing user to work on the canvas underneath
    * **Vanish/Display Shortcut**: Enables dragging, resizing, and accessing the control bar
* **Color Inspector**: Color picker available that allows the user to copy the hexcode of a clicked area of the image (area of pixels averaged color) to their clipboard
* **Quality of Life**:
    * **Drag & Drop**: The user can provide their input images by dragging it from somewhere else onto the application control bar
    * **Clipboard**: Can take in an image from the user's clipboard
    * **Media Types**: Accepts URLs leading to images and local files

## Prerequisites

* **Operating System**: Any (may require administrative permission if incorrectly flagged as malware due to global input reading)
* **Runtime**: Python 3.x
* **Libraries**: `PyQt5`, `keyboard`, `requests`

## Quick Start

To use this program, simply run the main.py file and there will be a control bar presented with various buttons. The meanings of the buttons are provided below:

* **K** stands for keybind, it will wait for you to click a button on your keyboard of which will be used to toggle ghost mode.
* **O** stands for open file, it will open explorer and wait for you to select an image.
* **C** stands for clipboard, if there is an image in your clipboard then it will be inputted.
* **H** stands for hexcode and **A** means it's active, if you click anywhere on an image then it will update your clipboard to contain the hexcode value for the average color of the area you clicked.
* **U** stands for unshow and **S** stands for show, these are quick ways to hide or show the image (transparency set to 1 or 0).
* **D** and **I** modify the transparency of the image incrementally.
* **-** and **+** decrease and increase the resolution/size of the image in a way that doesn't compress or widen the image to make sure the image is shown how it was meant to be.
