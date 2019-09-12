# File: capture.py , Lars Schönherr & Felix Schürmann
# student project @ Bergische Universität Wuppertal (2019)
# License: WTFPL
from __future__ import print_function

import sys
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QFile, Qt
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import QObject, Signal
from oct2py import Oct2Py

import PySide2.QtOpenGL
import logging
import os
import subprocess
import sys
import platform
import threading
import time
import serial
import gphoto2 as gp
import threading
import queue
import capture



r=0




#This Thread handles the whole capturing process. Downloading of the images, creating folders and giving instructions to the arduino.
class myThread(threading.Thread):
    def __init__(self, iD, name,ordner,slider):
        threading.Thread.__init__(self)
        self.iD =iD
        self.name = name
        self.ordner = ordner
        self.slider = slider
    def run(self):
        print("Capturing Thread started")
        window.label_2.setText("Capturing Thread started!")
        #filename
        image="image"
        logging.basicConfig(
        format='%(levelname)s: %(name)s: %(message)s', level=logging.WARNING)

        #braker variable stops the capturing process.
        global breaker
        breaker = False

        #opening connection to the camera:
        try:
            callback_obj = gp.check_result(gp.use_python_logging())
            camera = gp.check_result(gp.gp_camera_new())
            gp.check_result(gp.gp_camera_init(camera))

        except   gp.GPhoto2Error as ex:
            if ex.code == gp.GP_ERROR_MODEL_NOT_FOUND:
                print("Camera is not turned on!")
                window.label_2.setText("Camera is not turned on!")
                return 0
            elif ex.code == -53:
                print ("Unmount the Camera!")
                window.label_2.setText("Unmount the Camera!")
                return 0
            else:
                print ("b")


        ser = serial.Serial(arduino)  # open serial port

        #subfolder for capturing
        self.ordner=str(self.ordner)
        print(self.ordner)
        #list all items in current folder
        path, dirs, files = next(os.walk(os.path.join(os.path.expanduser('~'),cfd,self.ordner,'images')))
        capcount=len(files)
        print(files)
        time.sleep(1)

        #initialize arduino
        ser.write(b'A')
        time.sleep(2)

        #transmit number of samples to be taken
        ser.write(b'C')
        time.sleep(1)
        ser.write(self.slider.to_bytes(1,byteorder='little'))
        testread = ser.read()
        print (str(testread))
        time.sleep(1)

        #namelist consists of file image names, is used for deleting the last batch button
        global namelist
        namelist= []

        #Loop Capturing preferred samplesize(slider) is reached.
        for x in range(0,self.slider):
            if breaker:
                ser.write(b'B')
                print("Stopping..")
                window.label_2.setText("Stopping Capturing")
                if x == 0:
                    #setting the correct capture count
                    global r
                    r -= 1
                    window.lcdNumber.display(r)
                break

            #define the names under which the captured images are stored.
            imagename=image+str(x+capcount)+".jpg"
            rz_imagename=image+str(x+capcount)+"RZ"+".jpg"

            #initiate capturing process
            ser.write(b'A')
            if x == 0:
                time.sleep(1)
            time.sleep(2)
            print('Capturing image')
            window.label_2.setText("Capturing Image "+ str(x+1))
            try:
                file_path = gp.check_result(gp.gp_camera_capture(
                    camera, gp.GP_CAPTURE_IMAGE))
            except gp.GPhoto2Error as ex:
                if ex.code==-110:
                    print("Focus error")
                    window.label_2.setText("Camera Focus Error")
                if x == 0:
                    r -= 1
                    window.lcdNumber.display(r)
                break
            file_path_jpg = file_path.name.replace("cr2", "jpg")


            print('Camera file path: {0}/{1}'.format(file_path.folder, file_path_jpg))

            #image storing location:
            target = os.path.join(os.path.expanduser('~'),cfd,self.ordner,'images',imagename)
            rzdest = os.path.join(os.path.expanduser('~'),cfd,self.ordner,'preview', rz_imagename)

            #Gphoto check Result

            camera_file = gp.check_result(gp.gp_camera_file_get(
                    camera, file_path.folder, file_path_jpg, gp.GP_FILE_TYPE_NORMAL))
            gp.check_result(gp.gp_file_save(camera_file, target))


            namelist.append(target)

            calcProgressbar(x)



            gp.check_result(gp.gp_camera_exit(camera))

            # displaying image previews in the GUI
            window.label_6.setPixmap(window.graph1.pixmap())
            resizeImageWithQT(target,rzdest)
            pixmap = QtGui.QPixmap(rzdest)
            window.graph1.setPixmap(pixmap)

        ser.close()

#meshThread calculates the masks for the object and generates black and white images with an instance of GNU Octave
class meshThread(threading.Thread):
    def __init__(self, iD, name):
        threading.Thread.__init__(self)
        self.iD=id
        self.name=name

    def run(self):
        print("Calculating Masks")
        window.label_2.setText("Calculating Masks")
        #start instance of Octave with oct2py
        oc= Oct2Py();
        #packages needed for the calculations
        oc.eval('pkg load statistics')
        oc.eval('pkg load image')
        path, dirs, files = next(os.walk(os.path.join(os.path.expanduser('~'),cfd,run,'images')))
        imagecount=len(files)
        progressBar(0)
        for x in range(0,imagecount):
            if not os.path.isfile(os.path.join(os.path.expanduser('~'),cfd,run,'masks','image'+str(x)+'_mask.jpg')):
                #if mask doesnt already exist, calculate it with detect_sherd function
                print("Calculation Image"+str(x)+".jpg")
                window.label_2.setText("Calculating Mask for Image "+str(x+1))
                oc.detect_sherd(os.path.join(os.path.expanduser('~'),cfd,run),'image'+str(x)+'.jpg')
            progressBar((x+1)/imagecount*100)

        #Open Folder containing the masks
        subprocess.Popen(["xdg-open",os.path.join(os.path.expanduser('~'),cfd,run,'masks')])

# Thread that generates the 3D Model, Preview or High - Res
class modelThread(threading.Thread):
    def __init__(self, iD, name, cmd, test):
        threading.Thread.__init__(self)
        self.iD=iD
        self.name=name
        self.cmd = cmd
        self.test = test
    def run(self):
        os.system(self.cmd)
        if self.test:
            subprocess.run(["g3dviewer", os.path.join(os.path.expanduser('~'),cfd,run)+"/preview_model.obj"])
        else:
            subprocess.run(["g3dviewer", os.path.join(os.path.expanduser('~'),cfd,run)+"/model.obj"])


# opens the capturing folder in the file explorer
def show_browser():
    path=os.path.join(os.path.expanduser('~'),cfd,run)
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


# resizeImageWithQT loads the JPGs that have been copied to the disk and resizes them to be displayed in the GUI
def resizeImageWithQT(src, dest):
    pixmap = QtGui.QPixmap(src)
    pixmap_resized = pixmap.scaled(360, 320, QtCore.Qt.KeepAspectRatio)
    if not os.path.exists(os.path.dirname(dest)): os.makedirs(os.path.dirname(dest))
    pixmap_resized.save(dest)

# calculates the current state of the progress bar. takes in the current state of capturing.
def calcProgressbar(prog):
        max=window.horizontalSlider.value()
        hprog= (100/max)*(prog+1)
        window.progressBar.setValue(hprog)

def progressBar(prog):
    window.progressBar.setValue(prog)

#displays the Settings Window
def settingsKlick():
    setwin.show()

#Starts the capturing process
def startCapture():
    window.label_6.clear
    #r counts the number of Runs
    global r
    r=r+1
    window.lcdNumber.display(r)

    #create folder for images
    if not os.path.isdir(os.path.join(os.path.expanduser('~'),cfd,run,'images')):
        os.mkdir(os.path.join(os.path.expanduser('~'),cfd,run,'images'))


    # initialize Thread with name and number of samples
    t1=myThread(1,"t1",run,window.horizontalSlider.value())
    t1.start()


def exit():
    window.close()

# deleteBatch removes entries from namelist List
def delBatch():
    global namelist
    if len(namelist) > 0:
        global r
        r -= 1
        window.lcdNumber.display(r)
    while len(namelist) > 0:
        os.remove(namelist.pop())
    window.label_6.clear()
    window.graph1.clear()
    window.label_2.setText("Last Batch deleted")

#Stop Button:
def breakLoop():
    global breaker
    breaker=True

#saves the project name in config file.
def projectApply():
    global run
    run =window.lineEdit.text()
    namelist=[]
    if not os.path.isdir(os.path.join(os.path.expanduser('~'),cfd,run)):
        os.mkdir(os.path.join(os.path.expanduser('~'),cfd,run))
    f= open("proj.txt","w+")
    f.write(run)
    f.close()


#get called when apply in settings window is pressed. saves capturing folder destination in config file.
def settingsApply():
    #read UI lineedits and store them in .txt files as config.
    global cfd
    cfd= setwin.lineEdit_2.text()
    global arduino
    arduino=setwin.lineEdit.text()
    global metapath
    metapath=setwin.lineEdit_3.text()
    setwin.close()
    if not os.path.isdir(os.path.join(os.path.expanduser('~'),cfd)):
        os.mkdir(os.path.join(os.path.expanduser('~'),cfd))
        os.mkdir(os.path.join(os.path.expanduser('~'),cfd,run))
    f= open("cfd.txt","w+")
    f.write(cfd)
    f.close()
    f= open("arduino.txt", "w+")
    f.write(arduino)
    f.close()
    f=open("metapath.txt", "w+")
    f.write(metapath)
    f.close()


def calcMesh():
    #initialize and start mask generation thread.
    mT=meshThread(1,"mT")
    mT.start()


def preview():
    print("Calculating Low Res 3d Object Preview")
    window.label_2.setText("Calculating Low Res 3D Object Preview")
    path = os.path.join(os.path.expanduser('~'),cfd,run)
    cmd = metapath+"/metashape.sh -r photoscan_script.py -t " + path +"/"
    calc=modelThread(1,"moT",cmd,True)
    calc.start()

def calcModel():
    print("Calculating High Res 3d Object")
    window.label_2.setText("Calculating High Res 3D Object")
    path = os.path.join(os.path.expanduser('~'),cfd,run)
    #scriptpath = os.path.join(os.path.expanduser('~'),'git-TeamPrak','sc')
    cmd = metapath+"/metashape.sh -r photoscan_script.py " + path +"/"
    calc=modelThread(2,"moT",cmd,False)
    calc.start()


if __name__ == "__main__":

# read config files
    cfd='photocapture'
    conf=open("cfd.txt","r+")
    cfd=conf.read()
    conf.close()

    conf=open("proj.txt","r+")
    run=conf.read()
    conf.close()

    conf=open("arduino.txt","r+")
    arduino=conf.read()
    conf.close()

    conf=open("metapath.txt","r+")
    metapath=conf.read()
    conf.close()


    #start GUI
    app = QApplication(sys.argv)
    # load UI files created with QT
    ui_file = QFile("main.ui")
    ui_2file = QFile("settings.ui")
    ui_file.open(QFile.ReadOnly)
    loader = QUiLoader()
    window = loader.load(ui_file)
    ui_file.close()
    window.show()
    window.setWindowTitle("Sherd Capture")
    loader2=QUiLoader()
    setwin= loader2.load(ui_2file)
    ui_2file.close()

    #GUI functions that get called on buttons pressed.
    window.actionSettings.triggered.connect(settingsKlick)
    window.actionExit.triggered.connect(exit)
    window.capture.clicked.connect(startCapture)
    window.pushButton_2.clicked.connect(show_browser)
    window.pushButton.clicked.connect(breakLoop)
    window.pushButton_4.clicked.connect(projectApply)
    setwin.setApply.clicked.connect(settingsApply)
    window.deletebutton.clicked.connect(delBatch)
    window.pushButton_5.clicked.connect(calcMesh)
    window.pushButton_6.clicked.connect(preview)
    window.pushButton_3.clicked.connect(calcModel)

    window.lineEdit.setText(run)
    setwin.lineEdit_2.setText(cfd)
    setwin.lineEdit.setText(arduino)
    setwin.lineEdit_3.setText(metapath)

    sys.exit(app.exec_())
