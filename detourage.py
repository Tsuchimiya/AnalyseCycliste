#!/usr/bin/python2
import numpy as np
import cv2
import surface
import version
if version.is_cv2():
    import cv2.cv as cv

# input: image rgb
#        2 point (x1,y1), (x2,y2)
# output: /template.jpg
def createTemplate(image,x1,y1,x2,y2):
    if (x1>x2):
        xmax = x1
        xmin = x2
    else:
        xmax = x2
        xmin = x1
    if (y1>y2):
        ymax = y1
        ymin = y2
    else:
        ymax = y2
        ymin = y1
    
    # inverse x et y car image et matrix sont traites differament
    template = image[ymin:ymax,xmin:xmax]
    cv2.imwrite('template.png', template)
    return template


#methods = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR',
#            'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']
def findBodyPosition(img, template):
    h, w = template.shape[:2]
    
    # Apply template Matching
    res = cv2.matchTemplate(img,template,cv2.TM_CCOEFF)
    _, _, _, max_loc = cv2.minMaxLoc(res)

    top_left = max_loc
    #bottom_right = (top_left[0] + w, top_left[1] + h)
    
    matX = top_left[0]
    matY = top_left[1]
    matW = w
    matH = h

    return (matX, matY, matW, matH)

# input: 
#        h, w = image.shape[:2]
#        x,y,w,h = detourage.findBodyPosition(image, template)
# output:
#        maskbody: pour canny, maskbody=255 quand le body peut etre dedans
#        marker: mask pour watershed, surefg=255, surebg=50, others=0
#        marker32 = np.int32(marker)
#        cv2.watershed(frame,marker32)
#        m = cv2.convertScaleAbs(marker32)
def createMask(imageH, imageW, matX, matY, matW, matH):
    marker = np.zeros((imageH, imageW), np.uint8)
    maskbody = np.zeros((imageH, imageW), np.uint8) #i.e bg
    
    # mask body
    # dessiner body position
    cv2.rectangle(maskbody, (matX, matY), (matX+matW, matY+matH*2), (255, 255, 255), -2)
    # n'utilise pas le contour pour eviter le mal fonctionnement de watershed
    cv2.rectangle(maskbody, (0,0), (imageW-1,imageH-1), (0,0,0), 5)
    
    # sure fg
    # ligne centrale, milieu du ligne basse
    cv2.rectangle(marker, (matX+matW*7/16, matY+matH/4), (matX+matW*9/16, matY+matH), (255, 255, 255), -2)
    cv2.rectangle(marker, (matX+matW*5/16, matY+matH-3), (matX+matW*11/16, matY+matH+3), (255, 255, 255), -2) 
    # haut de jambe gauche, haut de jambe droite
    cv2.rectangle(marker, (matX+matW*3/8, matY+matH), (matX+matW*5/16, matY+matH*5/4), (255, 255, 255), -2)
    cv2.rectangle(marker, (matX+matW*5/8, matY+matH), (matX+matW*11/16, matY+matH*5/4), (255, 255, 255), -2)
    
    # sure bg
    marker[maskbody<125] = 50
    
    return marker, maskbody
    
# input:
#       gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
# output:
#       canny: enleve shadow
def edgeCanny(gray):
    # edge canny
    gray = cv2.GaussianBlur(gray,(7,7),0)
    # hist adapdative
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    cl1 = clahe.apply(gray)
    cl1 = cv2.GaussianBlur(cl1,(11,11),0)
    canny = cv2.Canny(cl1,40,160)
    
    return canny

# input:
#       image = color
#       marker = int8
def edgeWatershed(image, marker):
    # marker 32SC1 (32 bit signed single channel).
    marker32 = np.int32(marker)

    # watershed
    cv2.watershed(image,marker32)
    # convert to uinit8 image
    imWatershed = cv2.convertScaleAbs(marker32)
    
    # fill the edge of watershed
    h, w = image.shape[:2]
    edgec = np.zeros((h, w, 3), np.uint8)
    edgec[marker32 == -1] = [255,255,255]
    edgec[0:h-1,0] = [0,0,0]
    edgec[0:h-1,w-1] = [0,0,0]
    edgec[0,0:w-1] = [0,0,0]
    edgec[h-1,0:w-1] = [0,0,0]
    edge = cv2.cvtColor(edgec, cv2.COLOR_BGR2GRAY)
  
    return edge, imWatershed
    
# input:
#       edge = edge pour floodfill
# output:
#       result image
# kernel pour dilate
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7))

def edgeFloodfill(edge):
    # floodfill
    im_floodfill = edge.copy()
    h, w = edge.shape[:2]
    mask = np.zeros((h+2, w+2), np.uint8)
     
    # Floodfill from point (0, 0)
    cv2.floodFill(im_floodfill, mask, (0,0), 255);
    im_floodfill_inv = cv2.bitwise_not(im_floodfill)
 
    # dilate the inv floodfill
    #im_out = edged_img | im_floodfill_inv
    im_floodfill_inv = cv2.medianBlur(im_floodfill_inv,5)
    #im_open = cv2.morphologyEx(im_floodfill_inv,cv2.MORPH_OPEN,kernel)
    im_out = cv2.dilate(im_floodfill_inv,kernel,iterations = 1)
    im_out = edge | im_out
    
    return im_out
    
# input: 
#        frame: color
#        (matX, matY, matW, matH): bodyPosition
# output:
#        sihouette: grayscale image with 255 or 0, zone sihouette detected
#        edgeMarked: visualiser edge utilise et mark watershed
#                   il faut assurer que marker sont a l'interieur du sportif
def detourageFrame(frame, matX, matY, matW, matH):
    # gray pour canny
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = frame.shape[:2]
    
    # marker pour watershed, maskbody pour canny
    marker, maskbody = createMask(h, w, matX, matY, matW, matH)
    
    # edge watershed
    edgeWater, imWater = edgeWatershed(frame, marker)

    # edge canny, seulement pour la partie qui peut etre body, i.e dans maskbody
    canny = edgeCanny(gray)
    canny = cv2.bitwise_and(canny,maskbody)
    canny = cv2.dilate(canny,kernel,iterations = 1)
    
    # edge total
    edge = canny | edgeWater

    # floodfill
    silhouette = edgeFloodfill(edge)
    
    # debug info
    edgeMarked = edge|marker
    
    return silhouette, edgeMarked


# input :
#        path: frame: color
#        rate: int, parmi combien de frame on fera un templateMatch
#              si sampleRate=0, alors un seul template Matching est execute au debut du video
# output :
#        output.avi: cette fonction generent un video resultant, ecraser l'autre video qui ont le meme nom
#        compteur: combien de frame que cette fonction a traite
def detourageVideo(path, template, sampleRate=10, affichage=False):
    cap = cv2.VideoCapture(path)
    
    # info ecriture fichier
    fps = 20.0
    if version.is_cv2():
        fourcc = cv2.cv.CV_FOURCC(*'DIVX')
    elif version.is_cv3():
        fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    
    compteur = 0

    while(True):
        ret, frame = cap.read()
        
        # detection la fin du video
        if ret == 0:
            break
        
        # configuration pour output video
        if compteur == 0:
            h, w = frame.shape[:2]
            video = cv2.VideoWriter('silhouette.avi',fourcc, fps, (w,h), False)
    
        # find body position rectangle with template matching
        image = frame
        if sampleRate == 0:
            if compteur == 0:
                (matX, matY, matW, matH) = findBodyPosition(image,template)
        else:
            if compteur%sampleRate == 0 :
                (matX, matY, matW, matH) = findBodyPosition(image,template)
        
        silhouette, edgeMarked = detourageFrame(frame, matX, matY, matW, matH)
        
        
        if affichage == True:
            output = np.hstack((silhouette,edgeMarked))
            output = cv2.resize(output,None,fx=.3,fy=.3)
            cv2.imshow("silhouette|edgeMarked", output)
        
        compteur +=1
        video.write(silhouette)
        
        k = cv2.waitKey(30) & 0xff
        if k == 27:
            break

    video.release()
    cap.release()
    cv2.destroyAllWindows()
    
    return compteur

# interface avec ihm
# path = path du video a traiter
# appel la fonction pour traiter min max
def traitementSilhouette(path,x1,y1,x2,y2,x3,y3,x4,y4,echelle,sampleRate=10):

    print "[detourage]CALLING traitement silhouette"

    cap = cv2.VideoCapture(path)
    ret, frame = cap.read()
    template = createTemplate(frame,x1,y1,x2,y2)
    cap.release()
    
    detourageVideo(path, template, sampleRate)
    
    print "[detourage]END of traitement silhouette, CALLING calcul surface"
    
    # call fonction de traitement surface avec 2 points, echelle, et path
    path2 = 'silhouette.avi'
    surface.calcul_surface(path2,x3,y3,x4,y4,echelle)
    
    print "[detourage]END of calcul surface"
    
