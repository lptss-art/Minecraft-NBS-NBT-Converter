import numpy as np
from customNBT import customNBT
from random import randint

class Data:

    # Class équivalante aux données utiles d'un NBT
    
    # On sauvegarde 3 données
    # l'indice du block souhaité
    # la direction que regarde le block (sera utile pour 'tourner' le block)
    # Le tick ou celui ci sera posé (utile pour la génération au fur a mesure)
      
    pos = [0,0,0]
    
    maxShape = [0,0,0]
    
    nbData = 6
    # 0 : Vide ou pas
    # 1 : Index
    # 2 : tick
    # 3 : random delay of tick
    # 4 : Layer : where to put the block
    # 5 : bottom block needed
    # 6 : Top block needed
    
    shape = [4,1,4]
    
    #data = np.ones(shape = shape)*-1  # Index of the blocks

    
    def __init__(self, x=0, y=0, z = 0, nbt = None, facing = 'south', direction = -1):
        #self.data = np.ones(shape = self.shape)*-1  # Index of the blocks
        
        self.pos = [0,0,0]
        self.dt = np.dtype("bool, uint8, int16, uint8, int16, bool, bool")
        self.data = np.zeros(shape = self.shape, dtype = self.dt)
        #self.direction = np.ones(shape = shape)*-1 # direction they are facing

        #self.ticks = np.ones(shape = shape)*-1 # Tick they were placed

    
    def Reshape(self, x,y,z):
        # Agrandir les array si necessaire (x2)

        newShape = [0,0,0]
        self.maxShape = [0,0,0]
        
        r = True
        
        if(abs(x)+2>self.shape[0]/2):
            newShape[0] = abs(x*2)+10
            r=False
        else:
            newShape[0] = self.shape[0]
        if(abs(y)+2>self.shape[1]/2):
            newShape[1] = abs(y*2)+4
            r=False
        else:
            newShape[1] = self.shape[1]
        if(abs(z)+2>self.shape[2]/2):
            newShape[2] = abs(z*2)+8
            r=False
        else:
            newShape[2] = self.shape[2]
             
                
        if(r):
            return

            
        sX = self.shape[0]
        sY = self.shape[1]
        sZ = self.shape[2]
            
        self.data = np.roll(self.data, [sX//2, sY//2, sZ//2], [0,1,2])    
        
        newData = np.zeros(shape = newShape, dtype = self.dt)
        newData[:sX,:sY,:sZ]=self.data
        
        self.data = np.roll(newData, [-sX//2, -sY//2, -sZ//2], [0,1,2])   

        self.shape = newShape
        
    def Maxshape(self):
        sX = self.shape[0]
        sY = self.shape[1]
        sZ = self.shape[2]
        for i in range(sX):
            for j in range(sY):
                for k in range(sZ):
                    if(self.data[i-sX//2,j-sY//2,k-sZ//2][0]):
                        if(abs(i-sX//2)>self.maxShape[0]):
                            self.maxShape[0] = abs(i-sX//2)
                        if(abs(j-sY//2)>self.maxShape[1]):
                            self.maxShape[1] = abs(j-sY//2)                       
                        if(abs(k-sZ//2)>self.maxShape[0]):
                            self.maxShape[2] = abs(k-sZ//2)
    
    def AddData(self,dataB):
        dataB.Maxshape()
        maxX = dataB.maxShape[0] + abs(dataB.pos[0])
        maxY = dataB.maxShape[1] + abs(dataB.pos[1])
        maxZ = dataB.maxShape[2] + abs(dataB.pos[2])
        
        self.Reshape(maxX,maxY,maxZ)
        
        
        
        
        newDataB = np.roll(dataB.data,[dataB.shape[0]//2,dataB.shape[1]//2,dataB.shape[2]//2],axis = [0,1,2])
        
        
        for i in range(dataB.shape[0]):
            for j in range(dataB.shape[1]):
                for k in range(dataB.shape[2]):
                    if(newDataB[i,j,k][0]):
                        self.data[dataB.pos[0] + i - dataB.shape[0]//2,
                                  dataB.pos[1] + j - dataB.shape[1]//2,
                                  dataB.pos[2] + k - dataB.shape[2]//2] = newDataB[i,j,k]

  
    def AddBlock(self, x,y,z, index, tick = 0, randomAmount = -1, needsDown = False,needsUp = False):
        self.Reshape(x,y,z)
        self.data[x,y,z][0] = True
        self.data[x,y,z][1] = index
        self.data[x,y,z][2] = tick
        self.data[x,y,z][3] = randomAmount
        self.data[x,y,z][5] = needsDown
        self.data[x,y,z][6] = needsUp
        
        return
        
        if(abs(x) > self.maxShape[0]):
            self.maxShape[0]=abs(x)
        if(abs(y) > self.maxShape[1]):
            self.maxShape[1]=abs(y)
        if(abs(z) > self.maxShape[2]):
            self.maxShape[2]=abs(z)            
            

    def Rotate(self, i, nbt=None):
        i=i%4

        if(i==1):
            axis = 0
            mvt = 1
            self.shape = [self.shape[2],self.shape[1],self.shape[0]]
        elif(i==2):
            axis = [0,2]
            mvt = [1,1]
        elif(i==3):
            axis = 2
            mvt = 1
            self.shape = [self.shape[2],self.shape[1],self.shape[0]]
        else:
            axis = 0
            mvt = 0

        self.data = np.roll(np.rot90(self.data, k=i,axes = (0,2)),mvt,axis = axis)
        
        if(nbt == None):
            return
        corresondance = nbt.GetRotationIndex(i)
        
        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                for k in range(self.shape[2]):
                    if(self.data[i,j,k][1] in corresondance.keys() ):
                        self.data[i,j,k][1] = corresondance[self.data[i,j,k][1]]
                        
                        
                        
    def Flip(self, nbt):
        self.data = np.roll(np.flip(self.data, axis=2),1,axis=2)
        
        if(nbt == None):
            return
        
        corresondance = nbt.GetRotationIndex(2,True)
        
        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                for k in range(self.shape[2]):
                    if(self.data[i,j,k][1] in corresondance.keys() ):
                        self.data[i,j,k][1] = corresondance[self.data[i,j,k][1]]
                        
                        
        
    def WriteNBT(self, nbt):

        sX = self.shape[0]
        sY = self.shape[1]
        sZ = self.shape[2]
        for i in range(sX):
            for j in range(sY):
                for k in range(sZ):
                    if(self.data[i-sX//2,j-sY//2,k-sZ//2][0]):
                        #print('successful print')
                        nbt.AddBloc([i-sX//2 + self.pos[0],j-sY//2+ self.pos[1],k-sZ//2+ self.pos[2]], self.data[i-sX//2,j-sY//2,k-sZ//2][1])
        
        
     
    def SetLayers(self, randomAmount = 5):
# On indique a quel tick charger quoi

        sX = self.shape[0]
        sY = self.shape[1]
        sZ = self.shape[2]

        for i in range(sX):
            for j in range(sY):
                for k in range(sZ):
                    i2 = i-sX//2
                    j2 = j-sY//2
                    k2 = k-sZ//2

                    if(self.data[i2,j2,k2][0]):
                        if(self.data[i2,j2,k2][3] == 255):
                            r = randomAmount
                        else:
                            r = self.data[i2,j2,k2][3]

                        tickNecessaire = self.data[i2,j2,k2][2] - randint(0,r)

                        self.data[i2,j2,k2][4] = max(0,int(tickNecessaire))
                                                
                        if(self.data[i2,j2,k2][5]):
                            self.data[i2,j2-1,k2][4] = self.data[i2,j2,k2][4]
                        if(self.data[i2,j2-1,k2][6]):
                            self.data[i2,j2,k2][4] = self.data[i2,j2-1,k2][4]                            

                            
                            
                            
                            
                            
                            
                            