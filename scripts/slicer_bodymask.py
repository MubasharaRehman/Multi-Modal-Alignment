import slicer
import vtk
import numpy as np
import re
import shutil
import os
import DICOMScalarVolumePlugin
import vtkSegmentationCorePython as vtkSegmentationCore
import sys
import qt

# variables----------------------------------
patientID = '58'
segmentationName = '814102716: RTSTRUCT: CT_1'
segmentName = 'BODY'
path2SaveMask = fr'Dataset_Folder_Path\'

# variables----------------------------------

segmentationNode = slicer.util.getNode(segmentationName)
segmentID = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(segmentName)


kctAlignedVolumeNode = slicer.util.getNode('kctResampledCropped')
transformNode = slicer.util.getNode('transformElastix')
newSegmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode",
                                                                'kctMaskSegmentation')

def maskVolume(segmentEditorWidget, maskedVolumeName, segmentationNode, 
               segmentID, volumeNode, insideVal=1, outsideVal=0):
    # Mask image
    segmentEditorWidget.setActiveEffectByName("Mask volume")
    effect = segmentEditorWidget.activeEffect()
    
    # Settings
    segmentEditorNode = segmentEditorWidget.mrmlSegmentEditorNode()
    segmentEditorNode.SetMaskMode(0) # Editable area = everywhere
    segmentEditorNode.SetOverwriteMode(1) #Modify other segments = overwrite visible
    segmentEditorNode.SetMasterVolumeIntensityMask(0) # Editable intensity range = False
    
    maskedVolumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
    maskedVolumeNode.SetName(maskedVolumeName)
    effect.self().maskVolumeWithSegment(segmentationNode, segmentID, 
                                        "FILL_INSIDE_AND_OUTSIDE", 
                                        [insideVal, outsideVal],
                                        volumeNode, maskedVolumeNode)
    
    # Put masked volume inside the original study
    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    maskedvolumeShItemID = shNode.GetItemByDataNode(maskedVolumeNode)
    subjectHierarchyItemID = shNode.GetItemByDataNode(volumeNode)
    studyItemID = shNode.GetItemParent(subjectHierarchyItemID)
    
    shNode.SetItemParent(maskedvolumeShItemID, studyItemID)
    
    return maskedVolumeNode, shNode, studyItemID

def applyTransformToSegment(segmentToMoveID, segmentationNode, 
                            auxiliarSegmentationNode, transformNode, 
                            transformedSegmentName = 'bodySegmentKctAligned'):
    
    """Apply a transformation to a segment (keeping it in the same segmentation). 
    :segmentToMoveID: segment ID to transform
    :segmentationNode: segmentation node where segmentToMoveID is
    :auxiliarSegmentationNode: segmentation node where to move segmentToMoveID
        and apply transformation before taking it back to segmentationNode
    :transformNode: transformation node with the transform we want to apply
    :transformedSegmentName: name of the segment we have transformed
    
    """


    # Slicer only allows transform segmentations, not segments, so we will move
    # the current displaced segment to a new segmentation, apply the displacement
    # and bring back the segment to the original segmentation.
    
    # Select the segment we want to copy and apply the transformation
    segmentToCopy = segmentationNode.GetSegmentation().GetSegment(segmentToMoveID)
    
    # Make a copy of the segment
    segmentCopied = slicer.vtkSegment()
    segmentCopied.DeepCopy(segmentToCopy)
    segmentCopied.SetName(transformedSegmentName)
    
    # Add to SegmentationNew the copied segment:
    auxiliarSegmentationNode.GetSegmentation().AddSegment(segmentCopied)
    
    # Apply the transformation matrix to SegmentationNew:  
    auxiliarSegmentationNode.SetAndObserveTransformNodeID(transformNode.GetID())
    slicer.vtkSlicerTransformLogic().hardenTransform(auxiliarSegmentationNode)
    auxiliarSegmentationNode.GetSegmentation().SetConversionParameter("Smoothing factor","0.0")
    auxiliarSegmentationNode.CreateClosedSurfaceRepresentation()
    
    # Select the displaced segment and bring it back to the segmentation node:
    segmentToAddID = auxiliarSegmentationNode.GetSegmentation().GetSegmentIdBySegmentName(transformedSegmentName)
    
    
    
    # we leave the segment in the new segmentation
    # segmentToCopy = auxiliarSegmentationNode.GetSegmentation().GetSegment(segmentToAddID)
    # segmentCopied = slicer.vtkSegment()
    # segmentCopied.DeepCopy(segmentToCopy)
    # segmentationNode.GetSegmentation().AddSegment(segmentCopied)
    
    return segmentToAddID
    
def exportVolume(outputPath, volumeNode):
    
    try:
        shutil.rmtree(outputPath)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
        

    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    volumeShItemID = shNode.GetItemByDataNode(volumeNode)
    
    outputFolderAux = outputPath + "_Aux"
    if(not os.path.exists(outputFolderAux)):
        os.mkdir(outputFolderAux)
    
    exporter = DICOMScalarVolumePlugin.DICOMScalarVolumePluginClass()
    exportables = exporter.examineForExport(volumeShItemID)
    for exp in exportables:
        exp.directory = outputFolderAux
    
    exporter.export(exportables)
    
    #Slicer creates a folder named ScalarVolume_X but we do not want files in inside that folder
    #we want files in outputFolder directly
    
    # Source path
    source = os.path.join(outputFolderAux, os.listdir(outputFolderAux)[0])
    
    # Destination path
    destination = outputPath
    
    # Move the content of the ScalarVolume_X folder to the final destination folder
    # source to destination
    dest = shutil.move(source, destination, copy_function = shutil.copytree)
    
    #Remove auxiliary folder
    os.rmdir(outputFolderAux)
    

# Run code----------------------------------------------------------------------------------

segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
segmentEditorWidget.setSegmentationNode(newSegmentationNode)
segmentEditorWidget.setSourceVolumeNode(kctAlignedVolumeNode)

# Transform segment
transformedSegmentID = applyTransformToSegment(segmentToMoveID=segmentID, segmentationNode=segmentationNode, auxiliarSegmentationNode=newSegmentationNode, transformNode=transformNode, transformedSegmentName = 'bodySegmentKctAligned')

# Mask volume
maskedVolumeNode, shNode, studyItemID = maskVolume(segmentEditorWidget, maskedVolumeName='alignedMaskVolume', segmentationNode=newSegmentationNode, 
               segmentID=transformedSegmentID, volumeNode=kctAlignedVolumeNode, insideVal=1, outsideVal=0)
               
# Export mask in .npy
# exportVolume(path2SaveMask, maskedVolumeNode) # This exports the files in .dcm

# Save kct and mct matrices in .npy format
kctResampledCroppedMaskArray = slicer.util.arrayFromVolume(maskedVolumeNode) # shape is (nSlices, 512, 512)

# Create patient folder
if not os.path.exists(os.path.join(path2SaveMask, 'kctAlignedMask', patientID)): 
    os.makedirs(os.path.join(path2SaveMask, 'kctAlignedMask', patientID)) 

print('Saving kct aligned masks at ' + os.path.join(path2SaveMask, 'kctAlignedMask', patientID))

# Update slicer gui
slicer.app.processEvents()

for nSlice in range(kctResampledCroppedMaskArray.shape[0]):
    np.save(os.path.join(path2SaveMask, 'kctAlignedMask', patientID, str(nSlice) + '.npy'), kctResampledCroppedMaskArray[nSlice])
    

    
