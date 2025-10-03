# Multi-Modal-Alignment
kVCT–MVCT Alignment 3D-Slicer

This repository contains **research scripts** for automating two tasks inside [3D Slicer](https://www.slicer.org/):

1. **Alignment** → Align kVCT (moving) to MVCT (fixed) volumes  
2. **Body Mask Extraction** → Extract binary BODY mask from MVCT segmentations  

⚠️ **Disclaimer**: These scripts are for research purposes only. Not for clinical use.

---

## 📂 Repository Structure

```
kvct-mvct-alignment/
├─ scripts/
│  ├─ slicer_alignment.py       # alignment automation script
│  └─ slicer_bodymask.py        # body mask extraction script
├─ docs/
│  ├─ usage_alignment.md        # detailed alignment steps
│  ├─ usage_bodymask.md         # detailed mask extraction steps
│  └─ overview.md               # optional workflow notes
├─ examples/
│  ├─ example_scene.png
│  └─ example_output_mask.npy
├─ .gitignore
├─ LICENSE
└─ README.md
```

---

## 🚀 Quick Start

1. Open **3D Slicer**  
2. Load patient scene (kVCT + MVCT)  
3. Open the **Python Interactor** (`Ctrl+3`)  
4. Run one of the provided scripts:  
   - `scripts/slicer_alignment.py` → align kVCT to MVCT  
   - `scripts/slicer_bodymask.py` → extract BODY mask  
5. See detailed instructions in the [docs/](docs/) folder  

---

## 🩻 Workflow 1 — Alignment (kVCT → MVCT)

This script automates alignment of kVCT to MVCT inside **3D Slicer**.

### Steps
1. **Load Patient Data**
   - Open patient scene in Slicer  
   - Verify volumes:  
     - `kct_p1` (moving)  
     - `mct_p1` (fixed)

2. **Update Script Variables**
   ```python
   patientID = '01'            # Patient no:1 - Folder Name
   kctVolumeName = 'kct_p1'    # Patient no:1 kVCT modality
   mctVolumeName = 'mct_p1'    # Patient no:1 MVCT modality
   path2SaveAligned = r'C:\Folder_Path'
   ```

3. **Resample kVCT**
   - Module: *Resample Scalar Volume*  
   - Spacing: `(0.754, 0.754, 2.0)`  
   - Interpolation: **BSpline**  
   - Save as: `kct_p1_resliced`

4. **Crop Volume**
   - Module: *Crop Volume* → “Fit to Volume”  
   - Save as: `kct_p1_resliced_cropped`

5. **Apply Transform**
   - Module: *Transforms* → add **Linear Transform**  
   - Assign to `kct_p1_resliced_cropped`  
   - Adjust → **Harden Transform**

6. **Save Outputs**
   - `kctAligned_<patientID>.npy` → aligned kVCT  
   - `final_transform.tfm` → transform parameters  
   - Scene file (`File → Save`, check all)

---

## 🩺 Workflow 2 — Body Mask Extraction (MVCT → Mask)

This script extracts a binary body mask from MVCT segmentations inside **3D Slicer**.

### Steps
1. **Load Patient Scene**
   - Open from `CRO_Dataset`  
   - Verify MVCT segmentation exists  

2. **Update Script Variables**
   ```python
   patientID = '58'
   segmentationName = '814102716: RTSTRUCT: CT_1'  # segmentation node in Slicer
   segmentName = 'BODY'                           # segment to extract
   path2SaveMask = r'C:\Mubashara\Dataset_Working\AI_Dataset_UNIUD'
   ```

3. **Prepare Output Folder**
   - Ensure `kctAlignedMask` folder exists at:  
     `C:\Mubashara\Dataset_Working\AI_Dataset_UNIUD`

4. **Run Script**
   - Open Python Interactor (`Ctrl+3`)  
   - Paste + run script  

5. **Verify Outputs**
   - BODY mask saved as `.npy` in `path2SaveMask`  
   - Scene updated with segmentation nodes  

6. **Save Scene**
   - `File → Save` → check all boxes → confirm  

---

## 📊 Outputs

- **Alignment**  
  - `kctAligned_<patientID>.npy` → aligned kVCT  
  - `final_transform.tfm` → transform parameters  
  - Updated Slicer scene  

- **Body Mask Extraction**  
  - `<patientID>_BODY_mask.npy` → binary body mask  

---

## 🖼 Example

Alignment result in 3D Slicer slice views:

![Example Scene](images/Alignment_result_3DSlicer.png)

---

## 🚫 Data Privacy

- Do **not** commit real patient DICOM/NIfTI volumes  
- `.gitignore` already excludes sensitive formats:  
  ```
  *.nii
  *.nii.gz
  *.nrrd
  *.mha
  *.mhd
  *.dcm
  *.npy
  outputs/
  ```

---
