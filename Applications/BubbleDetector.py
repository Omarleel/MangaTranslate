import sys
import os
import cv2
import numpy as np
sys.path.append(os.path.dirname(os.getcwd()))
from Utils.Constantes import COLOR_BLANCO, COLOR_NEGRO

class BubbleDetector:
    def __init__(self, img):
        self.img = img
        self.orih, self.oriw = img.shape[0], img.shape[1]
        self.kernel = np.ones((3,3), np.uint8)

    def canny_flood(self, show_process=False, inpaint_sdthresh=10):
        kernel = np.ones((3,3),np.uint8)
        img = self.img
        orih, oriw = img.shape[0], img.shape[1]
        scaleR = 1
        if orih > 300 and oriw > 300:
            scaleR = 0.6
        elif orih < 120 or oriw < 120:
            scaleR = 1.4

        if scaleR != 1:
            h, w = img.shape[0], img.shape[1]
            orimg = np.copy(img)
            img = cv2.resize(img, (int(w*scaleR), int(h*scaleR)), interpolation=cv2.INTER_AREA)
        h, w = img.shape[0], img.shape[1]
        img_area = h * w

        cpimg = cv2.GaussianBlur(img,(3,3),cv2.BORDER_DEFAULT)
        detected_edges = cv2.Canny(cpimg, 70, 140, L2gradient=True, apertureSize=3)
        cv2.rectangle(detected_edges, (0, 0), (w-1, h-1), COLOR_BLANCO, 1, cv2.LINE_8)

        cons, hiers = cv2.findContours(detected_edges, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)

        cv2.rectangle(detected_edges, (0, 0), (w-1, h-1), COLOR_NEGRO, 1, cv2.LINE_8)

        ballon_mask, outer_index = np.zeros((h, w), np.uint8), -1

        min_retval = np.inf
        mask = np.zeros((h, w), np.uint8)
        difres = 10
        seedpnt = (int(w/2), int(h/2))
        for ii in range(len(cons)):
            rect = cv2.boundingRect(cons[ii])
            if rect[2]*rect[3] < img_area*0.4:
                continue

            mask = cv2.drawContours(mask, cons, ii, (255), 2)
            cpmask = np.copy(mask)
            cv2.rectangle(mask, (0, 0), (w-1, h-1), COLOR_BLANCO, 1, cv2.LINE_8)
            retval, _, _, rect = cv2.floodFill(cpmask, mask=None, seedPoint=seedpnt,  flags=4, newVal=(127), loDiff=(difres, difres, difres), upDiff=(difres, difres, difres))

            if retval <= img_area * 0.3:
                mask = cv2.drawContours(mask, cons, ii, (0), 2)
            if retval < min_retval and retval > img_area * 0.3:
                min_retval = retval
                ballon_mask = cpmask

        ballon_mask = 127 - ballon_mask
        ballon_mask = cv2.dilate(ballon_mask, kernel,iterations = 1)
        outer_area, _, _, rect = cv2.floodFill(ballon_mask, mask=None, seedPoint=seedpnt,  flags=4, newVal=(30), loDiff=(difres, difres, difres), upDiff=(difres, difres, difres))
        ballon_mask = 30 - ballon_mask
        retval, ballon_mask = cv2.threshold(ballon_mask, 1, 255, cv2.THRESH_BINARY)
        ballon_mask = cv2.bitwise_not(ballon_mask, ballon_mask)

        detected_edges = cv2.dilate(detected_edges, kernel, iterations = 1)
        for ii in range(2):
            detected_edges = cv2.bitwise_and(detected_edges, ballon_mask)
            mask = np.copy(detected_edges)
            bgarea1, _, _, rect = cv2.floodFill(mask, mask=None, seedPoint=(0, 0),  flags=4, newVal=(127), loDiff=(difres, difres, difres), upDiff=(difres, difres, difres))
            bgarea2, _, _, rect = cv2.floodFill(mask, mask=None, seedPoint=(detected_edges.shape[1]-1, detected_edges.shape[0]-1),  flags=4, newVal=(127), loDiff=(difres, difres, difres), upDiff=(difres, difres, difres))
            txt_area = min(img_area - bgarea1, img_area - bgarea2)
            ratio_ob = txt_area / outer_area
            ballon_mask = cv2.erode(ballon_mask, kernel,iterations = 1)
            if ratio_ob < 0.85:
                break

        mask = 127 - mask
        retval, mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)
        if scaleR != 1:
            img = orimg
            ballon_mask = cv2.resize(ballon_mask, (oriw, orih))
            mask = cv2.resize(mask, (oriw, orih))

        bg_mask = cv2.bitwise_or(mask, 255-ballon_mask)
        mask = cv2.bitwise_and(mask, ballon_mask)

        bground_aver, bground_region, sd = self.bground_calculator(img, bg_mask)
        inner_rect = None
        threshed = np.zeros((img.shape[0], img.shape[1]), np.uint8)

        if bground_aver[0] != -1:
            letter_aver, threshed = self.letter_calculator(img, mask, bground_aver, show_process=show_process)
            if letter_aver[0] != -1:
                mask = cv2.dilate(threshed, kernel, iterations=1)
                inner_rect = cv2.boundingRect(cv2.findNonZero(mask))
        else: letter_aver = [0, 0, 0]

        if sd != -1 and sd < inpaint_sdthresh:
            need_inpaint = False
        else:
            need_inpaint = True
        if show_process:
            pass
            # print(f"\nneed_inpaint: {need_inpaint}, sd: {sd}, {type(inner_rect)}")
            # show_img_by_dict({"outermask": ballon_mask, "detect": detected_edges, "mask": mask})

        if isinstance(inner_rect, tuple):
            inner_rect = [ii for ii in inner_rect]
        if inner_rect is None:
            inner_rect = [-1, -1, -1, -1]
        else:
            inner_rect.append(-1)

        bground_aver = bground_aver.astype(np.uint8)
        bub_dict = {"bgr": letter_aver,
                    "bground_bgr": bground_aver,
                    "inner_rect": inner_rect,
                    "need_inpaint": need_inpaint}
        # Expansión de la máscara
        expansion = round(self.oriw / 5)
        kernel = np.ones((expansion, expansion), np.uint8)
        mask_expanded = cv2.dilate(mask, kernel, iterations=2)
        return mask_expanded, ballon_mask, bub_dict

    def bground_calculator(self, buble_img, back_ground_mask, dilate=True):
        kernel = np.ones((3,3),np.uint8)
        if dilate:
            back_ground_mask = cv2.dilate(back_ground_mask, kernel, iterations = 1)
        bground_region = np.where(back_ground_mask==0)
        sd = -1
        if len(bground_region[0]) != 0:
            pix_array = buble_img[bground_region]
            bground_aver = np.mean(pix_array, axis=0).astype(int)
            pix_array - bground_aver
            gray = cv2.cvtColor(buble_img, cv2.COLOR_BGR2GRAY)
            gray_pixarray = gray[bground_region]
            gray_aver = np.mean(gray_pixarray)
            gray_pixarray = gray_pixarray - gray_aver
            gray_pixarray = np.power(gray_pixarray, 2)
            # gray_pixarray = np.sqrt(gray_pixarray)
            sd = np.mean(gray_pixarray)
        else: bground_aver = np.array([-1, -1, -1])

        return bground_aver, bground_region, sd

    def letter_calculator(self, img, mask, bground_bgr, show_process=False):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # bgr to grey
        aver_bground_bgr = 0.114 * bground_bgr[0] + 0.587 * bground_bgr[1] + 0.299 * bground_bgr[2]
        thresh_low = 127
        retval, threshed = cv2.threshold(gray, 127, 255, cv2.THRESH_OTSU)

        if aver_bground_bgr < thresh_low:
            threshed = 255 - threshed
        threshed = 255 - threshed


        threshed = cv2.bitwise_and(threshed, mask)
        le_region = np.where(threshed==255)
        mat_region = img[le_region]

        if mat_region.shape[0] == 0:
            return [-1, -1, -1], threshed

        letter_bgr = np.mean(mat_region, axis=0).astype(int).tolist()

        if show_process:
            cv2.imshow("thresh", threshed)
            imgcp = np.copy(img)
            imgcp *= 0
            imgcp += 127
            imgcp[le_region] = letter_bgr
            cv2.imshow("letter_img", imgcp)
        return letter_bgr, threshed