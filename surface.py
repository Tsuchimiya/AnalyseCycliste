# -*- coding: utf-8 -*-
import cv2
import numpy as np
import math

#le gars montre une règle de la taille de son guidon, il doit connaitre la longueur de la regle et la tenir le plus horizontalement possible
#Le cycliste doit rester immobile pendant cette phase

#entree: x,y=>coordonnees points cliques aux extremites de la regle, lg=>distance de la regle 
#fonction executee une seule fois qu debut donc ce n`est pas grave si le calcul est gros

def taille_pixel(x1,y1,x2,y2,lregle):

    l=math.sqrt((x2-x1)**2+(y2-y1)**2) #si pente de la regle
    taille=lregle/l
    return taille**2

# apres generation du fichier resu.txt, traitement des donnees dedans
#ouvre le fichier coontenant les surfaces en cm^2
#trouve le minimum et le maximum de surface
#calcule la moyenne
#vire les résultats aberrants

def calcul_moy(f="resu.txt"):
    mon_fichier = open(f, "a+")
    somme=0
    nb_lignes=0
    for l in mon_fichier :
        nb_lignes=nb_lignes+1
        somme=somme+float(l)

    moy=somme/nb_lignes
    return moy

def calcul_max(f="resu.txt"):
    mon_fichier = open(f, "a+")
    liste = []
    for l in mon_fichier.read().splitlines() :
        
        liste.append(float(l))
    
    high=max(liste)
    #print liste
    return high


def calcul_min(f="resu.txt"):
    mon_fichier = open(f, "a+")
    liste = []
    for l in mon_fichier :
        liste.append(float(l))

    low=min(liste)
    return low

def absurd(f,seuilmin,seuilmax):
    mon_fichier = open(f, "a+")
    liste = []
    for l in mon_fichier :
        
        if float(l)<=seuilmax:
            if float(l)>=seuilmin:
                liste.append(float(l))
    mon_fichier.close()

    #je le réecris avec juste les bonnes valeurs
    mon_fichier=open (f, 'a+')
    #je vide mon précédent fichier

    mon_fichier.truncate()
    for i in liste :
        mon_fichier.write(str(i)+"\n")
        
        
##
#la fonction principale
def calcul_surface(path,x1,y1,x2,y2,echelle):
    cap=cv2.VideoCapture(path)  

    #l'utilisateur clique sur les deux extremites de la regle et rentre la longueur de la reference
    #par exemple, p1=(1200,1300) p2=(400,350) et l=30cm

    taille_px=taille_pixel(x1,y1,x2,y2,echelle)

    mon_fichier = open("resu.txt", "a") #a=append
    #je vide le fichier avant 
    mon_fichier.seek(0)
    mon_fichier.truncate()

    while (1):
        ret,frame=cap.read()
        if ret==0 :
            break
    #calcul du nb de pixels noirs sur l'image du velo
        gray=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret1,thresh=cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY);
    #inversion image
        h,w=thresh.shape[:2]
        nzCountBlack = cv2.countNonZero(thresh)
        nWhite=nzCountBlack
    #calcul de la surface mec+velo
        surface=taille_px*nWhite
        #print ('surface finale=%.10f' %surface, 'cm2')
        mon_fichier.write(str(surface)+"\n")

        #cv2.imshow('frame', thresh)
        if cv2.waitKey(30) & 0xFF == ord('q'):
                break

    mon_fichier.close()
    
    valmax = calcul_max("resu.txt")
    valmin = calcul_min("resu.txt")
    valmoy = calcul_moy("resu.txt")
    
    if valmax>(1.1*valmin):
        absurd("resu.txt",0.9*valmoy,1.1*valmoy)

    cap.release()
    cv2.destroyAllWindows()
