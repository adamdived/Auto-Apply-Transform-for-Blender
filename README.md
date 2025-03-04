# Auto-Apply-Transform-for-Blender
The "Auto Apply Transform" addon addresses a common workflow issue in Blender - forgetting to apply transformations. By automatically applying scale, location, or rotation after you make changes, this addon ensures your geometry maintains clean transform values, preventing unexpected behavior during modeling, animation, and export.

# Features
1) Automatically applies transformations as you work
2) Choose which transformations to auto-apply (scale, location, rotation)
3) Apply scale selectively to X, Y, or Z axes
4) Optional on-screen display showing when auto-apply is active
5) Optional Alt+A hotkey for quickly toggling the feature
6) Settings panel in the 3D viewport sidebar

# Use Cases
1) 3D modelers who need geometry with unified scale
2) Character artists working with armatures
3) Technical artists preparing assets for game engines
4) Anyone who wants to avoid scale issues in their projects

# Installation
1) Download the .py file from this repository
2) In Blender, go to Edit > Preferences > Add-ons
3) Click "Install..." and select the downloaded file
4) Enable the addon by checking the box

# How to Use
1) After installation, find the "Auto Apply Transform" panel in the 3D viewport sidebar (press N to open)
2) Enable the main toggle to activate auto-apply
3) Select which transforms to automatically apply (scale is enabled by default)
4) For scale, optionally select which axes should have scale applied
5) Continue working as normal - transformations will be applied automatically

# Compatibility
Blender 3.0 and newer
Works with Mesh, Curve, Armature, and Empty objects
