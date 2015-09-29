# -*- encoding:utf-8 -*-
from __future__ import print_function, absolute_import
import numpy as np
from datetime import datetime
from pytz import UTC
import requests
from . import Check

import skimage.io as io
import skimage
import numpy as np

def timestamp():
    return datetime.utcnow().strftime('%Y%m%d_%H%M%S')

class CamResponseInRoi:
    """
    in: 
        image url
            __init__(url)
        
        Regions of Interest (RoIs)
            add_roi_disc_in_row_col_with_radius(row,col,radius)
            You can call add_roi several times on different image parts 
            to enlarge the total RoI

    out:
        ratio of actual to maximal possible camera response in RoI
            get_relative_response()
        
        image can be saved to disc
            imsave(path)
    """
    def __init__(self,url):
        self.url = url
        self.raw = io.imread(self.url)
        self._to_gray_scale()
        self._init_roi_mask()
        
    def _to_gray_scale(self):
        self.img = (255.0*skimage.color.rgb2gray(self.raw)).astype('uint8')

    def add_roi_disc_in_row_col_with_radius(self, row, col, radius):
        additional_mask = self._create_disc_mask(self.img, row, col, radius)
        self.roi_mask = self.roi_mask + additional_mask.astype('int')

    def _init_roi_mask(self):
        self.roi_mask = np.zeros(self.img.shape[0:2]).astype('int')

    def _create_disc_mask(self,img,row,col,radius):
        X, Y = np.ogrid[:img.shape[0],:img.shape[1]]
        return (X-row)**2.0 + (Y-col)**2.0 > radius**2.0

    def _make_roi_mask_boolsh(self):
        m = np.max(np.max(self.roi_mask))
        self.roi_mask[self.roi_mask<m] = 0
        self.roi_mask = self.roi_mask.astype('bool')

    def _max_possible_response_in_roi(self):
        outside_roi = np.sum(np.sum(self.roi_mask)).astype('float')
        all_image = self.roi_mask.size
        return 255.0*float(all_image-outside_roi)

    def _response_in_roi(self):
        return np.sum(np.sum(self.roi)).astype('float')

    def _init_roi(self):
        self.roi = np.copy(self.img)
        self.roi[self.roi_mask] = 0

    def get_relative_response(self):
        self._make_roi_mask_boolsh()    
        self._init_roi()
        return self._response_in_roi()/self._max_possible_response_in_roi()

    def _imsave_with_mask(self, path):
        self._make_roi_mask_boolsh()
        self._init_roi()
        io.imsave(path, np.hstack((self.roi, self.img)))

    def imsave(self, path):
        io.imsave(path,self.raw)

class LidCamCheck(Check):
    """
    FACT's focal plane is expected to be dark during operation.
    The roi is on the focal plane and camera housing visible
    from the lid cam on FACT's shoulder.
    Since we dont know absolute fluxes, we call it an alarm when the 
    ratio of possible brightness in the roi to maximum possible brightness
    in the roi reaches a threshold of about 1%.
    """

    def check(self):
        url = "http://www.fact-project.org/cam/lidcam.php"
        res = CamResponseInRoi(url)
        res.add_roi_disc_in_row_col_with_radius(415,525,75)
        relative_response = res.get_relative_response()

        fmt = '{:2.1f}'
        self.update_system_status(
            'lid cam response', 
            fmt.format(100.0*relative_response),
            '%')

        if relative_response >= 0.05:
            mesg = "lid cam image is bright, response > 1%: {:2.1f} %"
            self.queue.append(mesg.format(100.0*relative_response))
            res.imsave("plots/fact_lid_camera_"+timestamp()+".jpg")

class IrCamCheck(Check):
    """
    FACT's IR cam on the container is meant to see only a dark frame during
    operation.
    """

    def check(self):
        url = "http://www.fact-project.org/cam/cam.php"
        res = CamResponseInRoi(url)
        res.add_roi_disc_in_row_col_with_radius(240,320,240)
        relative_response = res.get_relative_response()

        fmt = '{:2.1f}'
        self.update_system_status(
            'IR cam response', 
            fmt.format(100.0*relative_response),
            '%')

        if relative_response >= 0.05:
            mesg = "IR camera is bright, response > 1%: {:2.1f} %"
            self.queue.append(mesg.format(100.0*relative_response))
            res.imsave("plots/fact_ir_camera_"+timestamp()+".jpg")