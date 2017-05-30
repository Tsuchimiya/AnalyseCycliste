import numpy as np
import matplotlib.pyplot as plt
def tracer(path="resu.txt"):
    f = open(path, "a+")
    
    nb_lignes=0
    for l in f :
        nb_lignes=nb_lignes+1
    
    f.seek(0)
    
    x = np.linspace(0,nb_lignes/20.0,num = nb_lignes,endpoint=False)
    y = np.zeros(nb_lignes)
    
    i = 0
    for l in f :
        y[i] = float(l)
        i += 1

    plt.xlabel('Time(s)')
    plt.ylabel('Surface(cm2)')
    plt.plot(x,y,lw=2)
    plt.savefig('resu.png')
    print ("[graph]La graphe est enregistrer sous nom 'resu.png'")
    print ("[graph]Vous pouvez recevoir un waning mais c'est normale")
    plt.draw()
    plt.pause(1)

