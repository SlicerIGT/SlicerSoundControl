cmake_minimum_required(VERSION 2.8.9)

project(SoundControl)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/SoundControl")
set(EXTENSION_CATEGORY "IGT")
set(EXTENSION_CONTRIBUTORS "David Black (Fraunhofer Mevis), Julian Hettig (Uni. Magdeburg), Andras Lasso (PerkLab)")
set(EXTENSION_DESCRIPTION "Navigate using sound feedback")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/SoundControl.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/SoundControl/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(OpenSoundControl)
add_subdirectory(SoundNav)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
