   # -*- coding: utf-8 -*-
import numpy as np
import cv2
import version
if version.is_cv2():
    import cv2.cv as cv
import math
import pickle
import csv
import re
import os
import platform


ix,iy=460,258
decalX= [[10,300],[300,550],[600,800]]
 ## Calcule l'angle entre 3 points
def calcul_angle(P1,P2,P3):
    x1,y1=P1
    x2,y2=P2
    x3,y3=P3

    dist_12=math.sqrt((x2-x1)**2+(y2-y1)**2) #b
    dist_23=math.sqrt((x3-x2)**2+(y3-y2)**2) #a
    dist_13=math.sqrt((x3-x1)**2+(y3-y1)**2) #c
    a=dist_23
    b=dist_12
    c=dist_13

    rad=math.acos((a**2+b**2-c**2)/(2*a*b))
    angle=rad*180/math.pi

    return angle
    
def write_angle(angle,fichier):
        fichier.write(str(angle))
        fichier.write("\n")
def find_color_BGR(frame,couleur):
    global ix,iy
    tr =25
    tg = 25
    tb= 25
    [b,g,r]=couleur
    mask = np.zeros_like(frame)
    mask=cv2.inRange(frame, (b-tb, g-tg,r-tr), (b+tb, g+tg,r+tr))
    return mask

def fusion(rect):
    rectF=np.zeros((50,4))
    nbRect=0
    ecart=0
    print (np.shape(rect)[0])
    for i in range(np.shape(rect)[0]):
        j=0
        ecart=0
        x,y,z,h=rect[i]

        
        
        if not(x==0 and y==0 and z==0 and h==0) and not (z<20 or h<20):
            #print 'rect'
            while j<nbRect and not (ecart==1):
                ecartX=rectF[j][0]-rect[i][0]
                ecartY=rectF[j][1]-rect[i][1]
                if abs(ecartX)<70 and abs(ecartY)<70:
                    ecart=1
                   # print 'ecart inf'
                    rectF[j]=min(rectF[j][0],rect[i][0]),min(rectF[j][1],rect[i][1]),max(rectF[j][2],rect[i][2]), max(rectF[j][3],rect[i][3])
                j+=1
            if ecart==0:
                #print 'ajout nouveau rect'
                #print x,y,z,h
                rectF[nbRect]=rect[i]
                nbRect+=1
                ecart=1
        ## IL NE PEUT PAS Y AVOIR 2 RECTANGLES A LA MEME ORDONNEE
    
                    
    return rectF[:nbRect]
        

def find_tracking_window(frame,couleur,save,path):
    global ix,iy
    frame = cv2.blur(frame,(4,4))
    gray= cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hsv= cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    _,t=cv2.threshold(gray,100,255,cv2.THRESH_BINARY)
    output_image = cv2.bitwise_and(frame, frame, mask = t)

    
    
    #output_image1 = cv2.bitwise_and(hsv, hsv, mask = t)
   # cv2.imshow('bgr',output_image)
    #cv2.imshow('hsv',output_image1)
   #[111,21,176]
  # [174 158 255]
    print( "Determination de fenetres de tracking candidates")
    print (str(couleur))
    test=find_color_BGR(output_image,couleur)
    
   # cv2.circle(output_image,(ix,iy),2,(255,0,0),-1)
    #cv2.imshow('thresh',output_image)

  
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(6,6))
    dilated= cv2.dilate(test,kernel)
    eroded= cv2.erode(dilated,kernel)
   

   # cv2.line(frame,(y+100,decalxmin),(y,decalxmin),(0,0,255),2)
    #cv2.imshow('test',test)

    ## TENTATIVE POUR TROUVER TOUS  LES POINTS A TRACKER ##
    if version.is_cv2():
        edges,h=cv2.findContours(eroded,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    elif version.is_cv3():
        _,edges,h=cv2.findContours(eroded,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    #cv2.drawContours(frame,edges,-1,(255,0,0))

    #hull=np.zeros(np.shape(edges)[0])
    rect=np.zeros((np.shape(edges)[0],4))
    for i in range(np.shape(edges)[0]):
      
        if np.shape(edges[i])[0]>1:

            x,y,w,h=cv2.boundingRect(edges[i])
            rect[i]=x,y,w,h
            cv2.rectangle(frame, (int(x),int(y)), (int(x+w),int(y+h)), 255,2)
    #print rect
    rectFinal=fusion(rect)
    print(str(rectFinal))
    for i in range(np.shape(rectFinal)[0]):
        x,y,w,h=rectFinal[i]
        cv2.rectangle(frame, (int(x),int(y)), (int(x+w),int(y+h)), (0,255,0),2)

    #cv2.circle(frame,(int(x),int(y)),5,(255,0,0),-1)
    save[250:1050,550:1350]=frame
    save = cv2.resize(save,None,fx=.5,fy=.5)
    import re
    
    
    if (platform.system() == 'Linux'):
        results = re.search('/(.*/)*(.*)[.](.+)',path)
    else: #elif (platform.system() == 'Windows')
        results = re.search('.:(.*/)*(.*)[.](.+)',path)


    ## preparation des directorys :
    if not os.path.isdir('calcul_profil'):
        os.mkdir('calcul_profil')
    if not os.path.isdir('calcul_profil//'+results.group(2)):
        os.mkdir('calcul_profil//'+results.group(2))
    else:
        print ("Attention, suppression d'un dossier existant car même titre de video")
    cv2.imwrite('calcul_profil//'+results.group(2)+'//fenetres.jpg',save)
    #cv2.imshow('contours',frame)
  
    return rectFinal

def recalibration(frame,couleur,save,path):
    Ws=find_tracking_window(frame,couleur,save,path)
    track_w=np.zeros((np.shape(Ws)[0],4))
    test=np.zeros((180,1))
    roi_hist=[test]*np.shape(Ws)[0]
    
    
    for i in range(np.shape(Ws)[0]):
        c,r,w,h=Ws[i]
        track_w[i]=(c,r,w,h)
        roi = frame[int(r):int(r+h),int(c):int(c+w)]
        hsv_roi=cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask=cv2.inRange(hsv_roi,np.array((0.,60.,32.)), np.array((180.,255.,255.)))
       # print np.shape(cv2.calcHist([hsv_roi],[0],mask,[180],[0,180]))
      #  print "suivant"
        roi_hist[i] = cv2.calcHist([hsv_roi],[0],mask,[180],[0,180])
        cv2.normalize(roi_hist[i],roi_hist[i],0,255,cv2.NORM_MINMAX)

    recal = 0
    if np.shape(Ws)[0]<1:
        recal=0
    else:
        recal=1
    return track_w,roi_hist,recal




def mean_shifts(Ws,path,couleur): #pas mal mais dur de tracker genoux ou quoi

    if (np.shape(Ws)[0]<3):
        print ("Impossible de calculer des angles, nombre de points de tracking inférieurs à 3")
        return None
    else : 
        cap = cv2.VideoCapture(path)
        ret, frame = cap.read()
        savedFrame= frame
        frame=frame[250:1050,550:1350]
        ## préparation du systeme de fichiers
        angles = np.zeros((np.shape(Ws)[0]-2) )
        
        init = np.array(range(np.shape(Ws)[0]-2))
        print(init)
        fint=open("test1.csv", "wb")
        fich = csv.writer(fint)
        tabfich= [fich]*(np.shape(Ws)[0]-2)
        fint.close()
        os.remove("test1.csv")
        if (platform.system() == 'Linux'):
            regexp = re.search('/(.*/)*(.*)[.](.+)',path)
        else: #elif (platform.system() == 'Windows')
            regexp = re.search('.:(.*/)*(.*)[.](.+)',path)
        fAngles = open ("calcul_profil//"+regexp.group(2)+"//Angles.txt","w")
    
        
        for i in range(np.shape(tabfich)[0]):
           
            fAngles.write("Angles liés à "+str(i)+".jpg\t")
            f=open("calcul_profil//"+regexp.group(2)+"//"+str(i)+".csv", "w")
            f.write("Angles liés à "+str(i)+".jpg\n")
            tabfich[i]=f
        
        fAngles.write("\n")

        
       # writer = csv.DictWriter(fichier, fieldnames=init)

        #writer.writeheader()
        #    #tabfich[i]= fichier

        ## préparation des images correspondantes
        cv2.imwrite("calcul_profil//"+regexp.group(2)+"//frame.jpg",frame)
        for i in range(np.shape(Ws)[0]-2):
            interm = cv2.imread("calcul_profil//"+regexp.group(2)+"//frame.jpg")
            x,y,w,h=Ws[i]
            x1,y1,w1,h1=Ws[i+1]
            x2,y2,w2,h2=Ws[i+2]
            cv2.line(interm, (int(x+w),int(y+h)), (int(x1+w1),int(y1+h1)), (0, 0, 255), 2)
            cv2.line(interm, (int(x1+w1),int(y1+h1)), (int(x2+w2),int(y2+h2)), (0, 0, 255), 2)
            cv2.rectangle(interm, (int(x),int(y)), (int(x+w),int(y+h)), (0,255,0),2)
            cv2.rectangle(interm, (int(x1),int(y1)), (int(x1+w1),int(y1+h1)), (0,255,0),2)
            cv2.rectangle(interm, (int(x2),int(y2)), (int(x2+w2),int(y2+h2)), (0,255,0),2)
            cv2.imwrite("calcul_profil//"+regexp.group(2)+"//"+str(i)+".jpg",interm)

        
        os.remove("calcul_profil//"+regexp.group(2)+"//frame.jpg")
        
        nbAngles = 0
        track_w=np.zeros((np.shape(Ws)[0],4))
        test=np.zeros((180,1))
        roi_hist=[test]*np.shape(Ws)[0]
        
        
        for i in range(np.shape(Ws)[0]):
            c,r,w,h=Ws[i]
            track_w[i]=(c,r,w,h)
            roi = frame[int(r):int(r+h),int(c):int(c+w)]
            hsv_roi=cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            mask=cv2.inRange(hsv_roi,np.array((0.,60.,32.)), np.array((180.,255.,255.)))
           # print np.shape(cv2.calcHist([hsv_roi],[0],mask,[180],[0,180]))
          #  print "suivant"
            roi_hist[i] = cv2.calcHist([hsv_roi],[0],mask,[180],[0,180])
            cv2.normalize(roi_hist[i],roi_hist[i],0,255,cv2.NORM_MINMAX)
           
        precPositions= np.zeros((np.shape(Ws)[0],2))
        
      
        term_crit=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,10,1)
        trackingPoints=np.zeros((np.shape(Ws)[0],2))
        print("Calcul en cours ... ")
        
        recal= 0
        resu= 1
        nb_recal = 0


        
        while(1):
            ret , original =cap.read()
            
            if nb_recal>5 :
                print ("erreur trop de pertes calibration")
                return -1
            
             #tentative d'amélioration du rendu en floutant
           
            #frame=BG_substr(frame,fgbg)
            
            if ret == True:
                original=original[250:1050,550:1350]
                frame = cv2.blur(original,(5,5))
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                
                if recal == 1 :
                    track_w,roi_hist,resu=recalibration(original,couleur,savedFrame,path)
                    recal=0
                    nb_recal+=1
                else:
                    nb_recal=0
                    
                if resu == 1:
                    for i in range(np.shape(Ws)[0]):
                        
                        (c,r,w,h)=track_w[i]
                        dst= cv2.calcBackProject([hsv],[0],roi_hist[i],[0,180],1)
                        ret, track_w[i] = cv2.meanShift(dst, (int(c),int(r),int(w),int(h)), term_crit)
                        x,y,w,h = track_w[i]

                        xprec,yprec= precPositions[i]
                        deltY = y - yprec
                        deltX = x - xprec
                        # si la fenetre a sauté d'un coup, on demande la recalibration
                        if (xprec>0 and yprec >0 and (abs(deltY)>50 or abs(deltX)>50) and nb_recal>0):
                            print ("fenetre a saute")
                            precPositions[i]=0,0
                            recal=1
                        else:
                            precPositions[i]=x,y
                        
                        trackingPoints[i]=(x+w,y+h)
                        cv2.rectangle(frame, (int(x),int(y)), (int(x+w),int(y+h)), 255,2)

                    for i in range(np.shape(trackingPoints)[0]-2):
                        x,y=trackingPoints[i]
                        x1,y1=trackingPoints[i+1]
                        x2,y2=trackingPoints[i+2]
                        cv2.line(frame, (int(x),int(y)), (int(x1),int(y1)), (0, 0, 255), 2)
                        a= calcul_angle((int(x),int(y)),(int(x1),int(y1)),(int(x2),int(y2)))
                        if a>170 or a<50 or recal==1:
                            print( "recalibration necessaire")
                            print (str(a))
                            recal=1
                        else:
                            #print "Angle : "
                            #print a
                            angles[i]=a
                            fAngles.write(str(a)+"\t")
                            fAngles.write("test")
                            ## ecriture dans le fichier
                            write_angle(int(a),tabfich[i])
                          
                    #cv2.imshow('img2',frame)
                    #cv2.waitKey(0)
                    if (recal == 0 ):
                        nbAngles += 1
                        fAngles.write("\n")
                        #fichier.writerow(angles)

             #   print(str(calcul_angle((x2,y2+h2),(x1+w1,y1+h1),(x,y+h))))
                    

                
                

            else:
                print ("Termine !! ")
                cv2.destroyAllWindows()
                fAngles.close()
                print (str(range(np.shape(tabfich)[0])))
                for i in range(np.shape(tabfich)[0]):
                     tabfich[i].close()
               # fichier.write=SOMME(A3:A11)/2
                 ## préparation des datas à afficher
                results = np.zeros((np.shape(tabfich)[0],3))
                
                
                for i in range(np.shape(tabfich)[0]):
                    print( 'calcul_profil//'+regexp.group(2)+'//'+str(i)+'.csv')
                    results[i]=calculCsv('calcul_profil//'+regexp.group(2)+'//'+str(i)+'.csv')
                print (str(results))
                
                return str(regexp.group(2))
                break

def moyenne(x,y,frame):
    tol = 8
    lx= x-tol
    hx= x+tol
    ly=y-tol
    hy=y+tol
    Bsom = 0
    Gsom = 0
    Rsom = 0
    total= 0

    for ix in range(lx,hx):
        for iy in range (ly,hy):
            b,g,r= frame[ix,iy]
            Bsom+=b
            Gsom+=g
            Rsom+=r
            total+=1
    print (str(total))
    return Bsom/total,Gsom/total,Rsom/total

## faire le décalage x et y de façon automatique
def video(path,x,y):
    print ("start Lecture")
    #'logiciel//Video//MOV_0007.mp4'
    cap = cv2.VideoCapture(path)
    global ix,iy,decalX
   
    #[111,21,176]
    ret, frame = cap.read()
    frame = cv2.blur(frame,(5,5))
    couleur = frame[y,x]
    
    
    print (str(couleur))
    moyCoul= moyenne(y,x,frame)
    save = frame
    print ("Moyenne : " + str(moyCoul))
    frame=frame[250:1050,550:1350]
    
    hsv= cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    w1=find_tracking_window(frame,moyCoul,save,path)
    
   # w2=find_tracking_window(frame,(60,80),(decalX[1][0],decalX[1][1],0))
    #w1=find_tracking_window(frame,(60,80),(decalX[0][0],decalX[0][1],0))
    #cv2.circle(frame,(ix,iy),5,(255,0,0),-1)
   
    #cv2.circle(save,(x,y),5,(255,0,0),-1)
    #cv2.imshow('test',frame)
    #w2=600,80,210,100
    #w3=280,80,230,100
    #w4=90,20,250,150
    #print np.shape([w1,w2,w2])
    
    return mean_shifts(w1,path,moyCoul)
#926,720 hanches



## pour tester le programme avec une image et vérifier qu'il distingue bien les angles 
def test4points():
     frame = cv2.imread("test.jpg")
     frame = cv2.blur(frame,(5,5))
     couleur = 188,19,236
     frame=frame[250:1050,550:1350]
     Ws=find_tracking_window(frame,couleur)
     fich= open("test.txt","a")
     tabfich= [fich]*(np.shape(Ws)[0]-2)
     fich.close()
     for i in range(np.shape(tabfich)[0]):
        fichier= open("calcul_profil//"+str(i)+".txt","w")
        tabfich[i]= fichier

    ## préparation des images correspondantes
     cv2.imwrite('calcul_profil/template.jpg',frame)
     time.sleep(1)
     
     for i in range(np.shape(Ws)[0]-2):
        interm = cv2.imread('calcul_profil/template.jpg')
        x,y,w,h=Ws[i]
        x1,y1,w1,h1=Ws[i+1]
        x2,y2,w2,h2=Ws[i+2]
        cv2.line(interm, (int(x+w),int(y+h)), (int(x1+w1),int(y1+h1)), (0,0,255), 2)
        cv2.line(interm, (int(x1+w1),int(y1+h1)), (int(x2+w2),int(y2+h2)), (0,0,255), 2)
        cv2.rectangle(interm, (int(x),int(y)), (int(x+w),int(y+h)), (255,255,0),2)
        cv2.rectangle(interm, (int(x1),int(y1)), (int(x1+w1),int(y1+h1)), (255,255,0),2)
        cv2.rectangle(interm, (int(x2),int(y2)), (int(x2+w2),int(y2+h2)), (255,255,0),2)
        cv2.imwrite("calcul_profil//"+str(i)+".jpg",interm)
def calculCsv(path):
    fichier = open(path, "r")
    reader = csv.reader(fichier)
    nbAngles = 0
    minAngle = 360
    maxAngle = 0
    sumAngles = 0.0
    sauter = 1
    for row in reader:
        #print row
        if sauter == 1 :
            sauter =0
        else :
            nbAngles+=1
            sumAngles+=float(row[0])
            if (minAngle>float(row[0])):
                minAngle=float(row[0])

            if maxAngle<float(row[0]):
                maxAngle=float(row[0])
    if nbAngles == 0 :
        return 0,0,0
    else :
        return sumAngles/nbAngles,minAngle,maxAngle

#print calculCsv('calcul_profil//0.csv')
#print video('logiciel//Video//MOV_0007.mp4',926,720)
#test4points()

cv2.waitKey(0)
cv2.destroyAllWindows()
