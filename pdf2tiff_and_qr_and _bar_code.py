import io
import os
import argparse
#import subprocess
import cv2
import time
import threading
from wand.image import Image
from pyzbar.pyzbar import decode
from pdf2image import convert_from_path
from pdf2image import pdfinfo_from_path
from subprocess import Popen, PIPE


ap = argparse.ArgumentParser()
ap.add_argument("-i","--input", required = True, help="path to input pdf file")
ap.add_argument("-d","--decode", required = False, help="decode bar code or qr code")
args = vars(ap.parse_args())


file_path=args["input"]
poppler_path=r"C:\Program Files\poppler-20.12.1\Library\bin"
image_path=r"C:\Users\alex\Desktop\pdf2tiff\tiff"
gm_path=r"C:\Program Files\GraphicsMagick-1.3.36-Q16\gm.exe"
im_path=r"C:\Program Files\ImageMagick-7.0.11-Q16-HDRI\magick.exe"


info = pdfinfo_from_path(file_path, userpw=None, poppler_path=poppler_path)
maxPages = info["Pages"]

if args["decode"] != None:
   print("File :"+ file_path)
else:
   t0= time.time()
   print("Start time: ",time.strftime("%H:%M:%S", time.localtime(t0)))
   
def binarize_im_wand(input):
    with Image() as img:
#         img.read(input)
#         img.read(filename=image_path+'\\' + str(image_counter) + '.tif')
         img_byte_arr = input.getvalue()
         img.read(blob=img_byte_arr)                  
         img.resolution = 300
         img.type='bilevel'
         img.ordered_dither(threshold_map='h8x8o')
         img.compression ='group4'
         img.save(filename=image_path+'\\' + str(image_counter) + '.tif')
         
def binarize_gm(input):
    output=input
    cmd = [
    '"'+gm_path+'"',
    'convert',
    '-density 300',
    '-type Bilevel',
    '-monochrome',
    '-ordered-dither All 8x8',
    '-compress Group4',
    input,
    output
    ]
    cmd = ' '.join(cmd) 
    process = Popen(cmd, shell=False,bufsize=-1)


def binarize_gm_from_pipe(input_stream, output):
    cmd = [
    '"'+gm_path+'"',
    'convert',
    '-density 300',
#    '-type Bilevel',
    '-monochrome',
    '-ordered-dither All 8x8',
    '-compress Group4',
    '-',
    output
    ]
    cmd = ' '.join(cmd) 
    process = Popen(cmd, stdin=PIPE, shell=False,bufsize=-1)
    input_stream.seek(0)
    page = input_stream.getvalue()
    process.communicate(input=page)
    process.stdin.close()
    process.wait()

    
def binarize_im(input):
    output=input
    cmd = [
    '"'+im_path+'"',
    'convert',
    '-density 300',
    '-type Bilevel',
    '-monochrome',
    '-ordered-dither h8x8o',
    '-compress Group4',
    input,
    output
    ]
    cmd = ' '.join(cmd) 
    process = Popen(cmd, shell=False,bufsize=-1)     
    
def decode_bar_qr_codes(input):
    img = cv2.imread(input)
    code = decode(img)
    if code == []:
       print("Page :"+ os.path.basename(input)[:-4])
       print("Bar code or Qr code was not decoded")
       print("----------------------------------------------------------------------")
    for i in code:
        print("Page :"+ os.path.basename(input)[:-4])
        print("Type: "+i.type)
        print("Data: "+i.data.decode("utf-8"))
        print("----------------------------------------------------------------------")
    
image_counter = 1

for page in range(maxPages):
       page = convert_from_path(
       file_path,
       dpi=300,
       first_page=image_counter,
       last_page=image_counter + 1,
       grayscale=True,
       poppler_path=poppler_path,
       thread_count=4,
       single_file=False,
       paths_only=True,
       use_pdftocairo=False
       )
       
       for i in page:
           output = image_path+'\\' + str(image_counter) + '.tif'
#           i.save(output, format='TIFF')           
#           binarize_im_wand(img_byte_arr)
#           binarize_gm(output)
           # Create two threads as follows
           if args["decode"] == None:
              img_byte_arr = io.BytesIO() 
              i.save(img_byte_arr, format='TIFF')          
              try:
                 convert_thread = threading.Thread(target=binarize_gm_from_pipe, args=(img_byte_arr,output))
                 convert_thread.start()
              except:
                 print("Error: unable to start thread")
#           binarize_gm_from_pipe(img_byte_arr, output)
#           print(args["decode"])
           if args["decode"] != None:
              i.save(output, format='TIFF')
#              print("File :"+ file_path)
              decode_bar_qr_codes(output)
           image_counter += 1
           
           
if args["decode"] == None:           
   t1 = time.time() - t0
   print("End time: ",time.strftime("%H:%M:%S", time.localtime(time.time())) )
   totaltime = time.strftime("%H:%M:%S", time.gmtime(t1)) 
   print("Processing time: ", totaltime)