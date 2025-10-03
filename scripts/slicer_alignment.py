import os
import DICOMScalarVolumePlugin
import shutil
import slicer
import vtkSegmentationCorePython as vtkSegmentationCore
import importlib
import sys
import qt
import shutil

# Parameters to change-------------------------------------------------------
patientID = '3'
#path2saveResults = r'D:\Belen\CRO\AIDataset'
#path2data = r'D:\Belen\CRO\Dataset'
#path2AnnotationsFile = r'D:\Belen\CRO\CRO_UNIUD\annotationsFileSlicer.csv'

path2saveResults = r'C:\Mubashara\Dataset_Working\AI_Dataset_UNIUD'
path2data = r'C:\Mubashara\CRO_Files\Dataset backup\Backup Dataset CRO\CRO_Dataset'
path2AnnotationsFile = r'C:\Mubashara\Dataset_Working\annotationsFileSlicer.csv'
path2saveAlignedKCT = fr'C:\Mubashara\Dataset_Working\AI_Dataset_UNIUD\alignedDicomVolumes\{patientID}'

# askUserRegionSlices = True
# --------------------------------------------------------------------------

def loadVolume(path, name=None):
    """
    Loads a dcm volume in 3D Slicer
    
    :path: path to dcm files
    :name: volume name
    """
    loadedNodeIDs = []
    from DICOMLib import DICOMUtils
    with DICOMUtils.TemporaryDICOMDatabase() as db:
        DICOMUtils.importDicom(path, db)
        patientUIDs = db.patients()
        for patientUID in patientUIDs:
            loadedNodeIDs.extend(DICOMUtils.loadPatientByUID(patientUID))
	
    #volumeName = loadedNodeIDs[0]
    volumeNode = slicer.util.getNode(loadedNodeIDs[0])  #specify volume
    if(not name==None):
        volumeNode.SetName(name)
 
    return volumeNode

def exportVolume(outputPath, volumeNode):
    try:
        shutil.rmtree(outputPath)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))

    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    volumeShItemID = shNode.GetItemByDataNode(volumeNode)

    outputFolderAux = outputPath + "_Aux"
    if (not os.path.exists(outputFolderAux)):
        os.mkdir(outputFolderAux)

    exporter = DICOMScalarVolumePlugin.DICOMScalarVolumePluginClass()
    exportables = exporter.examineForExport(volumeShItemID)
    for exp in exportables:
        exp.directory = outputFolderAux

    exporter.export(exportables)

    # Slicer creates a folder named ScalarVolume_X but we do not want files in inside that folder
    # we want files in outputFolder directly

    # Source path
    source = os.path.join(outputFolderAux, os.listdir(outputFolderAux)[0])

    # # Destination path
    destination = outputPath

    # Move the content of the ScalarVolume_X folder to the final destination folder
    # source to destination
    dest = shutil.move(source, destination, copy_function = shutil.copytree)

    # Remove auxiliary folder
    os.rmdir(outputFolderAux)

def resample(volumeNode, resolution=[0.754,0.754,2.0], name='resampled'):
    
    """
    Automatization of Resample Scalar Volume in 3D Slicer. Interpolation is 
    set as bspline in the code below. 
    
    :volumeNode: node of the reference images
    :resolution: new spacing in all dimensions (x, y, z)
    :name: new resliced volume name
    
    :return: new resliced volume node
    """

    resampledVolumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", name)
    parameters = {
        "outputPixelSpacing":"{:},{:},{:}".format(*resolution),
        "InputVolume":volumeNode.GetID(),
        "interpolationMode":'bspline',
        "referenceVolume": volumeNode.GetID(),
        "OutputVolume":resampledVolumeNode.GetID()}
    
    cliNode = slicer.cli.runSync(slicer.modules.resamplescalarvolume, None, parameters)
    
    if cliNode.GetStatus() & cliNode.ErrorsMask:
        # error
        errorText = cliNode.GetErrorText()
        slicer.mrmlScene.RemoveNode(cliNode)
        raise ValueError("CLI execution failed in reslice: " + errorText)

    # success
    slicer.mrmlScene.RemoveNode(cliNode)
    
    resampledVolumeNode.GetDisplayNode().SetAutoWindowLevel(0)
    resampledVolumeNode.GetDisplayNode().SetWindowLevel(400,40)
    
    return resampledVolumeNode
    

def cropVolumeUsingResampleScalarVector(volumeNode, referenceVolumeNode, name='kctResampledCropped', 
        transformNode = None, interpolationType = 'linear'):

    resampledCroppedVolumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", name)
    
    # outputVectorNode = slicer.mrmlScene.AddNewNodeByClass(“vtkMRMLVectorVolumeNode”)
    #outputVectorNode.SetName(‘disp_PIPER_skinskel_afterDemons_afterresample’)

    parameters = {}
    parameters['inputVolume'] = volumeNode
    #Set output as vector volume
    parameters['outputVolume'] = resampledCroppedVolumeNode
    parameters['referenceVolume'] = referenceVolumeNode
    if (not transformNode is None):
        parameters['transformationFile'] = transformNode
    parameters['interpolationType'] = interpolationType

    cliNode = slicer.cli.runSync(slicer.modules.resamplescalarvectordwivolume,None,parameters)

    # slicer.util.saveNode(outputVectorNode, outputDisplacementfield_resampled,{“useCompression”: 0})
    
    return resampledCroppedVolumeNode


def RAStoIJK(xyz, volumeNode, RAS = True):
    """
    Transforms a list of points or np array of shape (n,3) in RAS coordinates
    to IJK coordinates. 
    
    :xyz: list of lists (Ex: [[1,2,3], [4,5,6]]) or np array with the RAS coordinates
            of the points.
    :volumeNode: node of the reference images
    :RAS: True if coordinates are in RAS coordinate system (could be LPS)
    """
    
    transf = vtk.vtkMatrix4x4()
    volumeNode.GetRASToIJKMatrix(transf)

    transf = arrayFromVTKMatrix(transf)
    
    correccion = np.array([1, 1, 1]) if RAS else np.array([-1, -1, 1])
    
    puntos_malla = np.hstack((xyz*correccion, np.ones(len(xyz)).reshape(-1, 1))).T

    puntos_ijk = np.round(transf.dot(puntos_malla)).astype(int).T[:, :-1]
    
    return puntos_ijk # Coordenadas en la matriz (vóxeles)
    

def IJKtoRAS(xyz, volumeNode, RAS = True):
    
    """
    Transforms a list of points or np array of shape (n,3) in IJK coordinates
    to RAS coordinates. 
    
    :xyz: list of lists (Ex: [[1,2,3], [4,5,6]]) or np array with the RAS coordinates
            of the points.
    :volumeNode: node of the reference images
    :RAS: True if coordinates are in RAS coordinate system (could be LPS)
    """
    
    transf = vtk.vtkMatrix4x4()
    volumeNode.GetIJKToRASMatrix(transf)

    transf = arrayFromVTKMatrix(transf)
    
    correccion = np.array([1, 1, 1]) if RAS else np.array([-1, -1, 1])
    
    puntos_malla = np.hstack((xyz*correccion, np.ones(len(xyz)).reshape(-1, 1))).T

    point_Ras = transf.dot(puntos_malla).astype(float).T[:, :-1]
    
    return point_Ras # Coordenadas en la matriz (vóxeles)
    
# Script------------------------------------------------------------------------------------------------------------
# Load kct volume 
print('Loading kct volume')
# Update slicer gui
slicer.app.processEvents()
kctVolumeNode = loadVolume(os.path.join(path2data, fr'{patientID}\CT-SIM'), name='kct')

# Load mct volume 
print('Loading mct volume')
# Update slicer gui
slicer.app.processEvents()
mctVolumeNode = loadVolume(os.path.join(path2data, fr'{patientID}\xMVCT'), name='mct')

# Resample kct volume so kct and mct have the same resolution
print('Resampling kct volume')
# Update slicer gui
slicer.app.processEvents()

mctSpacing = list(mctVolumeNode.GetSpacing())
if(not (mctSpacing == [0.754, 0.754, 2.0])):
    print('Warning. Resolution is: ' + str(mctSpacing))
    
kctResampledVolumeNode = resample(kctVolumeNode, resolution=mctSpacing, name='kctResampled')

# Crop kct resampled volume
print('Cropping kct volume')
# Update slicer gui
slicer.app.processEvents()

kctResampledCroppedVolumeNode = cropVolumeUsingResampleScalarVector(kctResampledVolumeNode, mctVolumeNode, name='kctResampledCropped', 
        transformNode = None, interpolationType = 'linear')

# Apply Elastix for alignment 
print('Aligning kctResampledCropped and mct volumes')
# Update slicer gui
slicer.app.processEvents()

# Input volumes
slicer.modules.elastix.widgetRepresentation().self().ui.fixedVolumeSelector.setCurrentNode(kctResampledCroppedVolumeNode)
slicer.modules.elastix.widgetRepresentation().self().ui.movingVolumeSelector.setCurrentNode(mctVolumeNode)

# Output volume
mctAlignedVolumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", 'mctAligned')
slicer.modules.elastix.widgetRepresentation().self().ui.outputVolumeSelector.setCurrentNode(mctAlignedVolumeNode)
# Output transform 
transformElastixNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", 'transformElastix') #slicer.vtkMRMLTransformNode()
slicer.modules.elastix.widgetRepresentation().self().ui.outputTransformSelector.setCurrentNode(transformElastixNode)

# Apply
slicer.modules.elastix.widgetRepresentation().self().ui.applyButton.click()

# # Save kct and mct matrices in .npy format
# kctResampledCroppedArray = slicer.util.arrayFromVolume(kctResampledCroppedVolumeNode) # shape is (nSlices, 512, 512)
# mctAlignedArray = slicer.util.arrayFromVolume(mctAlignedVolumeNode)

# # Create patient folder
# if not os.path.exists(os.path.join(path2saveResults, 'imgs', patientID)): 
    # os.makedirs(os.path.join(path2saveResults, 'imgs', patientID)) 
# if not os.path.exists(os.path.join(path2saveResults, 'labels', patientID)): 
    # os.makedirs(os.path.join(path2saveResults, 'labels', patientID)) 

# print('Saving imgs at ' + os.path.join(path2saveResults, 'imgs', patientID))
# print('Saving labels at ' + os.path.join(path2saveResults, 'labels', patientID))
# # Update slicer gui
# slicer.app.processEvents()

# for nSlice in range(kctResampledCroppedArray.shape[0]):
    # np.save(os.path.join(path2saveResults, 'imgs', patientID, str(nSlice) + '.npy'), kctResampledCroppedArray[nSlice])
    # np.save(os.path.join(path2saveResults, 'labels', patientID,  str(nSlice) + '.npy'), mctAlignedArray[nSlice])
    
    
# # Added funcionalities ----------------------------------------------------------------------------------------------
# # Compute maximum and minimum values for kct and mct 
# kctMax = np.max(kctResampledCroppedArray)
# kctMin = np.min(kctResampledCroppedArray)
# mctMax = np.max(mctAlignedArray)
# mctMin = np.min(mctAlignedArray)

# # Select head middle point as the origin point of the original kct
# middlePointNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "middlePoint")
# slicer.modules.markups.logic().StartPlaceMode(0)
# input("Place middle point and press key to continue...")

# # Convert RAS coordinates to IJK coordinates
# middlePointRAS = slicer.util.arrayFromMarkupsControlPoints(middlePointNode)
# middlePointIJK = RAStoIJK(middlePointRAS, kctResampledCroppedVolumeNode, RAS = True)[0]

# # Ask for head slices 
# firstHead = input("Enter the first head slice... ")
# lastHead = input("Enter the last head slice... ")
# # Sort
# if(int(firstHead) > int(lastHead)):
    # temp = firstHead
    # firstHead = lastHead
    # lastHead = temp

# # Ask for neck slices 
# firstNeck = input("Enter the first neck slice... ")
# lastNeck = input("Enter the last neck slice... ")
# # Sort
# if(int(firstNeck) > int(lastNeck)):
    # temp = firstNeck
    # firstNeck = lastNeck
    # lastNeck = temp

# # Ask for body slices 
# firstBody = input("Enter the first body slice... ")
# lastBody = input("Enter the last body slice... ")
# # Sort
# if(int(firstBody) > int(lastBody)):
    # temp = firstBody
    # firstBody = lastBody
    # lastBody = temp

# # Save results
# if(not(os.path.isfile(path2AnnotationsFile))): # if file does not exist
    # with open(path2AnnotationsFile, "w") as file:
        # file.write("patientID,headSlices,neckSlices,bodySlices,maxValueKct,minValueKct,maxValueMct,minValueMct,headMiddlePoint\n")

# with open(path2AnnotationsFile, "a") as file:
    # file.write(f"{patientID},{firstHead};{lastHead},{firstNeck};{lastNeck},{firstBody};{lastBody},{kctMax},{kctMin},{mctMax},{mctMin},{middlePointIJK[0]};{middlePointIJK[1]};{middlePointIJK[2]}\n")


exportVolume(path2saveAlignedKCT, slicer.util.getNode('kctResampledCropped'))

print('Process completed :)')