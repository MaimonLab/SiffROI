#!/usr/bin/env python
import sys
import pathlib

import napari
import fourcorr
from siffpy import SiffReader
from siffroi.protocerebral_bridge.rois.mustache import GlobularMustache


def on_done_clicked(siffpath, event):
    corr_window : 'fourcorr.FourCorrAnalysis' = event.source
    roi = GlobularMustache(
        globular_glomeruli_masks=corr_window.masks,
        view_direction = 'posterior',
        name = 'Protocerebral bridge'
    )

    siffpath = pathlib.Path(siffpath)
    roi.save(siffpath.parent / siffpath.stem)

def main():
    if len(sys.argv) < 2:
        #Import QApplication
        # from PyQt5.QtWidgets import QApplication
        # from PyQt5.QtWidgets import QFileDialog

        # QApplication([])


        # filename = QFileDialog.getOpenFileName(
        #     caption='Open file',
        #     directory='',
        #     filter='SIFF files (*.siff)',
        #     initialFilter='SIFF files (*.siff)',
        #     options=QFileDialog.Options()
        # )[0]
        # Open a file dialog window and get the file

        print("Usage: fca_protocerebral_bridge.py <siff file>")
        sys.exit(1)
        
    else:    
        filename = sys.argv[1]
    siff = SiffReader(filename)

    if not hasattr(siff, 'reference_frames'):
        raise ValueError("No reference frames found in siff file")

    fca = fourcorr.FourCorrAnalysis(
        frames = siff.get_frames(
            frames = siff.im_params.flatten_by_timepoints(),
            registration_dict= siff.registration_dict,
        ).reshape(siff.im_params.array_shape).squeeze(),
        annotation_images = siff.reference_frames,
    )

    fca.done_clicked.connect(lambda x: on_done_clicked(filename, x))

    napari.run()

if __name__ == "__main__":
    main()