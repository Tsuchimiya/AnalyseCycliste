# -*- coding: cp1252 -*-
#import des bibliothèques nécessaires


from tkinter import *
#import filedialog # pour exe,Matplotlib
import numpy as np

from functools import partial
import os
from PIL import Image, ImageTk # tkinter pour exeutable
import cv2
import detourage
import surface
import Profil
from tkinter import filedialog as tkFileDialog
import graph



##############DE FACE##################
def lemin(): 
    print("Calcul du min") 
    val=surface.calcul_min()
    info = Label(root,text="La surface min est "+str(val)+" cm2")
    info.grid(column=1,row=8)

def lemax():
    print("Calcul du max")
    val=surface.calcul_max()
    info = Label(root,text="La surface maximale est "+str(val)+" cm2")
    info.grid(column=1,row=9)
    
def lamoy():
    print("Calcul de la moyenne")
    val = surface.calcul_moy()
    info = Label(root,text="La moyenne des surfaces est "+str(val)+" cm2")
    info.grid(column=1,row=10)

def analyse_de_face_option(label,path,x1,y1,x2,y2,x3,y3,x4,y4,echelle,sampleRate=10): 
    for suppr in root.grid_slaves():
        if int(suppr.grid_info()["row"]) > 6 and int(suppr.grid_info()["row"]) < 15:
            suppr.grid_forget()
    label.config(text="Analyse en cours, cela risque de prendre du temps")
    
    # traitement de video a silhouette
    print("lancement de l'analyse de face avec x1="+str(x1)+" y1="+str(y1)+" x2="+str(x2)+" y2="+str(y2)+" a l'echelle "+str(echelle)+" metres et un nombre de frames : "+str(sampleRate))
    detourage.traitementSilhouette(path,x1,y1,x2,y2,x3,y3,x4,y4,echelle,sampleRate)
    
    # affichage graph
    graph.tracer()

    # affichage speciale pour les valeurs min max moyenne
    info = Label(root,text="Que voulez-vous faire maintenant ?")
    mini = Button(root,text="Calcul du min", command=lemin)
    maxi = Button(root,text="Calcul du max", command=lemax)
    moy = Button(root,text="Calcul de la moyenne", command=lamoy)
    info.grid(column=0,row=7)
    mini.grid(column=0,row=8)
    maxi.grid(column=0,row=9)
    moy.grid(column=0,row=10)
    label.config(text="Analyse terminee")
    
    
def choix_option(label,path,x1,y1,x2,y2,x3,y3,x4,y4,echelle):
    for suppr in root.grid_slaves():
        if int(suppr.grid_info()["row"]) > 6 and int(suppr.grid_info()["row"]) < 14:
            suppr.grid_forget()
    label.config(text="Choisissez le nombre de frames par secondes \n parmi la liste ci-dessous")
    choix = IntVar(root) 
    bouton1 = Radiobutton(root, text="5", variable=choix, value=5)
    bouton2 = Radiobutton(root, text="10", variable=choix, value=10)
    bouton3 = Radiobutton(root, text="20", variable=choix, value=20)
    bouton4 = Radiobutton(root, text="50", variable=choix, value=50)
    bouton5 = Radiobutton(root, text="100", variable=choix, value=100)
    bouton6 = Radiobutton(root, text="0", variable=choix, value=0)
    ok = Button(root,text="ok",command=partial(analyse_de_face_option,label,path,x1,y1,x2,y2,x3,y3,x4,y4,echelle,choix.get()))
    bouton1.grid(column=0,row=7)
    bouton2.grid(column=0,row=8)
    bouton3.grid(column=0,row=9)
    bouton4.grid(column=0,row=10)
    bouton5.grid(column=0,row=11)
    bouton6.grid(column=0,row=12)
    ok.grid(column=0,row=13)
    
def option(x1,y1,x2,y2,x3,y3,x4,y4,echelle,label,path):
    for suppr in root.grid_slaves():
        if int(suppr.grid_info()["row"]) > 6 and int(suppr.grid_info()["row"]) < 14:
            suppr.grid_forget()
    label.config(text = "Souhaitez-vous choisir le nombre \n de frames par secondes \n (cela reduira le temps de calcul)")
    oui = Button(root,text="oui",command=partial(choix_option,label,path,x1,y1,x2,y2,x3,y3,x4,y4,echelle.get()))
    non = Button(root,text="non",command=partial(analyse_de_face_option,label,path,x1,y1,x2,y2,x3,y3,x4,y4,echelle.get()))
    oui.grid(column=0,row=7)
    non.grid(column=0,row=8)
    
def onClick_face_4(label,x1,y1,x2,y2,x3,y3,path,event):
    print(event.x,event.y)
    label.config(text="A combien de centimetres correspond la distance entre \n ces deux points de maniere reelle")
    echelle = IntVar(root)
    entry = Entry(root,textvariable=echelle)
    echellebutton = Button (root, text="soumettre", command=partial(option,x1*2,y1*2,x2*2,y2*2,x3*2,y3*2,event.x*2,event.y*2,echelle,label,path))
    entry.grid(column=0,row=7)
    echellebutton.grid(column=0,row=8)
    
def onClick_face_3(label,img,x1,y1,x2,y2,path,event):
	print(event.x,event.y)
	label.config(text="Cliquez sur le deuxieme \n point de l'echelle")
	img.bind('<Button-1>', partial(onClick_face_4,label,x1,y1,x2,y2,event.x,event.y,path))
	
def onClick_face_2(label,img,x1,y1,path,event):
	print(event.x,event.y)
	label.config(text="Cliquez maintenant sur le premier \n point de l'echelle")
	img.bind('<Button-1>', partial(onClick_face_3,label,img,x1,y1,event.x,event.y,path))

def onClick_face_1(label,img,path,event):
    #ce sont les coordonnées en pixels
    print(event.x,event.y)
    label.config(text="Cliquez sur le second coin \n du cadre")
    img.bind('<Button-1>', partial(onClick_face_2,label,img,event.x,event.y,path))
    
    

#fonction de sélection de la vidéo dans l'ordinateur
def select_video_face():   
    path = tkFileDialog.askopenfilename(title="Choix de la video",filetypes=[('MOV files','.MOV'),('mp4 files','.mp4'),('avi files','.avi'),('all files','.*')])
    frame = Frame(root)
    frame.grid(column=0, row=14, padx=100,pady=100)
    
	# prise du premier frame
    cap = cv2.VideoCapture(path)
    ret, frame = cap.read()
    frame = cv2.resize(frame,None,fx=.5,fy=.5)
    cv2.imwrite('1frame.jpg', frame)
    cap.release()
    
    # affiche premier frame
    image = Image.open("1frame.jpg") 
    photo = ImageTk.PhotoImage(image) 
    video = Label(image=photo)
    video.image = photo
	
    video.grid(column=0,row=14)
    info = Label(root,text="Vous devez sélectionner deux points aux extremites \n du cadre a conserver \nCliquez sur le premier coin")
    info.grid(column=0,row=6)
    video.bind('<Button-1>', partial(onClick_face_1,info,video,path))

    
def face():
    info = Label(root,text = "Vous avez choisi l'analyse de face, \n maintenant, choisissez votre vidéo")
    info.grid(column = 0, row =4)
    button1 = Button(root, text="Sélectionnez la vidéo", command=select_video_face)
    button1.grid(column=0, row=5)
    
##################DE PROFIL###################

def analyse_de_profil(x,y,label,path): ###################REMPLIR#################
    for suppr in root.grid_slaves():
        if int(suppr.grid_info()["row"]) > 5:
            suppr.grid_forget()

    label.config(text="Analyse en cours")
    print("Analyse de profil avec la couleur situee aux coordonnees ("+str(x)+","+str(y)+")")
    save = Profil.video(path,x,y)
    if save==None: ## a changer fait de la merde
        label.config(text="Erreur dans l'analyse: nombre de points de tracking insuffisants\n Conseil: Changez d'endroit lors du clic sur la couleur à tracker")
    else:
        label.config(text="Analyse terminee ! \n Résultat stocké dans "+str(save))
        image = Image.open('calcul_profil//'+save+'//fenetres.jpg')
        photo = ImageTk.PhotoImage(image) 
        video = Label(image=photo)
        video.image = photo
        video.grid(column=0,row=14)

def onClick_profil(label,path,event):
    print(event.x,event.y)
    label.config(text="Vous pouvez maintenant lancer l'analyse \n avec le bouton ci-dessous")
    analyse = Button(root,text="analyse", command=partial(analyse_de_profil,event.x*2,event.y*2,label,path))
   
    analyse.grid(column=0,row=6)



#fonction de sélection de la vidéo dans l'ordinateur
def select_video_prof():
     for suppr in root.grid_slaves():
        if int(suppr.grid_info()["row"]) >= 5:
            suppr.grid_forget()
     path = tkFileDialog.askopenfilename(title="Choix de la video",filetypes=[('MOV files','.MOV'),('mp4 files','.mp4'),('avi files','.avi'),('all files','.*')])
     frame = Frame(root)
     
     cap = cv2.VideoCapture(path)
     ret, frame = cap.read()
     frame = cv2.resize(frame,None,fx=.5,fy=.5)
     cv2.imwrite('1frame.jpg', frame)
    
     image = Image.open("1frame.jpg") 
     photo = ImageTk.PhotoImage(image) 
     video = Label(image=photo)
     video.image = photo
    
     video.grid(column=0,row=14)
     info = Label(root,text="Cliquez au milieu de la couleur à analyser")
     info.grid(column=0,row=5)
     video.bind('<Button-1>', partial(onClick_profil,info,path))
    



    
    
def profil():
    info = Label(root,text = "Vous avez choisi l'analyse de profil, \n maintenant, choisissez votre vidéo")
    info.grid(column = 0, row =4)
    button1 = Button(root, text='Sélectionnez la vidéo', command=select_video_prof)
    button1.grid(column=0, row=5)



#########MAIN IHM#####################
# Création de la fenêtre racine
root = Tk() 
root.title("Analyse des performances d'un cycliste")


#Les textes explicatifs
welcome = Label(root, text='Bienvenue dans le le gestionnaire d\'analyse de vos performances')
#f = font.Font(welcome, welcome.cget("font"))
#f.configure(underline = True)
welcome.grid(column=0, row=0)
step1 = Label(root, text='Pour commencer, choisissez votre mode d\'analyse')
step1.grid(column=0, row=1)
deface = Button(root,text="De face", command=face)
deprofil = Button(root,text="De profil", command=profil)
deface.grid (column = 0, row =2)
deprofil.grid (column = 0, row =3)


#le main
root.mainloop() # Lancement de la boucle principale
