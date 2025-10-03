# Multi-Modal-Alignment
kVCT–MVCT Alignment 3D-Slicer

This repository contains **research scripts** for automating two tasks inside [3D Slicer](https://www.slicer.org/):

1. **Alignment** → Align kVCT (moving) to MVCT (fixed) volumes.  
2. **Body Mask Extraction** → Extract binary BODY mask from MVCT segmentations.  

⚠️ **Disclaimer**: These scripts are for research purposes only.

---

## 📂 Repository Structure
kvct-mvct-alignment/
├─ scripts/
│ ├─ slicer_alignment.py # alignment automation script
│ └─ slicer_bodymask.py # body mask extraction script
├─ docs/
│ ├─ usage_alignment.md # detailed alignment steps
│ ├─ usage_bodymask.md # detailed mask extraction steps
│ └─ overview.md # optional workflow notes
├─ examples/
│ ├─ example_scene.png
│ └─ example_output_mask.npy
├─ .gitignore
├─ LICENSE
└─ README.md
