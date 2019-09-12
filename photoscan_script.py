import Metashape
import os
import argparse
import sys
from time import gmtime, strftime

print("\n")
print("************************************************************")
print("Script started at: ", strftime("%Y-%m-%d %H:%M:%S", gmtime()))
print("************************************************************")
print("\n")

parser = argparse.ArgumentParser(description='Automates a default workflow for a photoscan project')
parser.add_argument('-t', '--test', 
        action='store_true', 
        help='build project in lowest quality possible for testing purpose')
parser.add_argument('project_path', 
        help='specify the project path. Assumes existence of subfolder \'images\' and \'masks\'')

# *** Initialize photoscan variables ***
doc = Metashape.app.document
chunk = doc.addChunk()
# **************************************

# *** Set general variables ***
args = parser.parse_args()
path = args.project_path
image_path = path + "images/"
masks_path = path + "masks/"
print(image_path)
print(masks_path)
project_filename = os.path.basename(path.rstrip('/')) + ".psz"
if args.test:
   # project_accuracy = Metashape.LowestAccuracy
    #project_quality = Metashape.LowestQuality
     project_accuracy = Metashape.MediumAccuracy
     project_quality = Metashape.MediumQuality
    # project_accuracy = Metashape.LowAccuracy
    # project_quality = Metashape.LowQuality		
else:
    project_accuracy = Metashape.HighestAccuracy 
    project_quality = Metashape.UltraQuality
# ******************************

# *** Build project ***
os.chdir(image_path)
images = os.listdir(".")
for i, filename in enumerate(images):
    images[i] = image_path + images[i]
chunk.addPhotos(images)
chunk.importMasks(path=masks_path + "{filename}_mask.jpg", source=Metashape.MaskSourceFile, cameras=chunk.cameras)
doc.save(path + project_filename)
print("*** Match Photos ***")
chunk.matchPhotos(accuracy=project_accuracy, generic_preselection=True, reference_preselection=False, filter_mask=True, mask_tiepoints=True, keep_keypoints=True)
doc.save()
chunk.alignCameras()
doc.save()
print("*** Build Depth Map ***")
chunk.buildDepthMaps(quality=project_quality, filter=Metashape.AggressiveFiltering)
doc.save()
print("*** Build Dense Cloud ***")
chunk.buildDenseCloud()
doc.save()
print("*** Build Model ***")
chunk.buildModel(surface=Metashape.Arbitrary, interpolation=Metashape.EnabledInterpolation)
doc.save()
# **********************
print("*** Export Model ***")
if args.test:
	chunk.exportModel(path +'preview_model.obj', normals=False, format=Metashape.ModelFormatOBJ, 		texture_format=Metashape.ImageFormatJPEG, texture=True, colors= True)
else:
	chunk.exportModel(path +'model.obj', normals=False, format=Metashape.ModelFormatOBJ, texture_format=Metashape.ImageFormatJPEG, texture=True, colors= True)


print("\n")
print("************************************************************")
print("Script finished at: ", strftime("%Y-%m-%d %H:%M:%S", gmtime()))
print("************************************************************")
print("\n")

