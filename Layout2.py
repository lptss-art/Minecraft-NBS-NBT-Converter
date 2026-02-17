import numpy as np
from customNBT import customNBT
from data import Data

class Layout2:
    pos = [0,0,0]
    #direction = 'east'
    data = Data()
    
    tick = 0
    
    index = 0
    
    indexVide = 0
    indexPiston = 50
    indexRedstoneBlock = 60
    indexRepeter = [2,3,4,5]
    
    indexLampe = 6
    
    indexSol = -20
    
    offsetNotes = 100 #self.customNBT.indexNotes
    offsetInstr = 200 #self.customNBT.indexInstr
    
    def __init__(self, x=0, y=0, z = 0, nbt = None, facing = 'south', direction = -1):
        self.x0 = x
        self.y0 = y
        self.z0 = z
        
        self.pos = [0,0,0]
        
        
        if(nbt == None):
            return
        
        self.customNBT = nbt
        self.direction = direction
        self.facing = facing
        
        self.data = Data()
        
        self.indexRepeter = self.customNBT.indexRepeters["west"]
        
        self.indexPiston = self.customNBT.indexPistons["east"]
        
        self.indexRedstone= self.customNBT.GetIndex("minecraft:redstone_wire",{'east':'side', 'west':'side'})
        self.indexRedstoneBlock = self.customNBT.GetIndex("minecraft:redstone_block")
        self.indexLampe = self.customNBT.GetIndex("minecraft:redstone_lamp")
        self.indexVide = self.customNBT.GetIndex("minecraft:air")
        #self.indexSol = self.customNBT.GetIndex("minecraft:stone")
        self.indexSol = -1
        
        self.offsetNotes = self.customNBT.indexNotes
        self.offsetInstr = self.customNBT.indexInstr
        
        #self.facing = 'east'
        
    
    
    
    def Add(self, tick, notesEntier = None, notesDemi = None, sym = False):
        
        self.data.Reshape(10,0,4)
        
        nbEntier = 0
        nbDemi = 0
        
        if(notesEntier != None):
            nbEntier = len(notesEntier)
        if(notesDemi != None):
            nbDemi = len(notesDemi)
  

        #self.tick = tick

        
        # ON fait tout la partie qui est coté piston, et qui peut être tourné
        
        
        if(notesDemi != None):
            if(nbDemi >= 1):
                self.AddNote(1,0,0, notesDemi[0])
            if(nbDemi >= 2):
                self.AddNote(0,0,-1, notesDemi[1])
            if(nbDemi >= 3):
                self.AddNote(0,0,1, notesDemi[2])
            if(nbDemi >= 4):
                self.data.data = np.roll(self.data.data, 1, axis = 0)
                self.AddBlock(0,0,0, self.indexRedstone,needsDown=True)
                self.AddBlock(0,-1,0, self.indexSol)
                self.AddNote(1,0,0, notesDemi[3])
            if(nbDemi >= 5):
                self.AddNote(0,-1,1, notesDemi[4])
            if(nbDemi >= 6):
                self.AddNote(0,-1,-1, notesDemi[5])
            if(nbDemi >= 7):
                self.data.data = np.roll(self.data.data, 1, axis = 0)
                self.AddBlock(0,0,0, self.indexRedstone,needsDown=True)
                self.AddBlock(0,-1,0, self.indexSol)
                self.AddNote(0,-1,1, notesDemi[6])
            if(nbDemi >= 8):
                self.AddNote(0,-1,-1, notesDemi[7]) # Jusqu'a 8 notes demi a priori
                
            if(nbDemi >= 4):
                self.data.data = np.roll(self.data.data, 1, axis = 0)
            self.data.data = np.roll(self.data.data, 2, axis = 0)
            self.AddBlock(0,0,0, self.indexPiston)
            self.AddBlock(1,0,0, self.indexRedstoneBlock)
            

            
            self.data.data = np.roll(self.data.data, 1, axis = 0)
            
            
        # La partie des notes  entier qui vont être tourné
        # Il y en a si:
        # sans piston + de 5 notes
        # avec piston + de 4 notes            
        if(nbEntier > 5 or nbEntier > 4 and nbDemi != 0):

            # Si on est en symetrie on peut poser un block en plus ( le bloc n°4)
            if(sym):
                offsetNotesEntier=1
            else:
                offsetNotesEntier=0

            self.AddBlock(0,0,0, self.indexRedstone,needsDown=True)
            self.AddBlock(0,-1,0, self.indexSol)

            if(nbEntier >= 4+offsetNotesEntier):
                self.AddNote(0,-1,-1, notesEntier[3+offsetNotesEntier])
                    
            if(nbEntier >= 5+offsetNotesEntier):
                self.AddNote(0,-1, 1, notesEntier[4+offsetNotesEntier])

            if(nbEntier >= 6+offsetNotesEntier):
                self.data.data = np.roll(self.data.data, 1, axis = 0)
                self.AddBlock(0,0,0, self.indexRedstone,needsDown=True)
                self.AddBlock(0,-1,0, self.indexSol)
                self.AddNote(0,-1,-1, notesEntier[5+offsetNotesEntier])
            if(nbEntier >= 7+offsetNotesEntier):
                self.AddNote(0,-1, 1, notesEntier[6+offsetNotesEntier])
             
            if(nbEntier >= 8+offsetNotesEntier):
                self.data.data = np.roll(self.data.data, 1, axis = 0)
                self.AddBlock(0,0,0, self.indexRedstone,needsDown=True)
                self.AddBlock(0,-1,0, self.indexSol)
                self.AddNote(0,-1,-1, notesEntier[7+offsetNotesEntier])
            if(nbEntier >= 9+offsetNotesEntier):
                self.AddNote(0,-1, 1, notesEntier[8+offsetNotesEntier])
            
            self.data.data = np.roll(self.data.data, 1, axis = 0)

        
        # Une fois que la partie coté piston est faite, on tourne et on ajoute le reste
        
        if(sym):
            self.Rotate(1)
        self.data.data = np.roll(self.data.data, 1, axis = 0)
        
        
        # Le bloc central
        if(nbEntier == 0):
            self.AddBlock(1,0,0, self.indexLampe)
        if(nbEntier>=1):
            self.AddNote(1,0,0, notesEntier[0])
            
        # notes coté redstone
        if(nbDemi == 0 and nbEntier<=5):
            if(nbEntier>=2):
                self.AddNote(1,0,1, notesEntier[1])
            if(nbEntier>=3):
                self.AddNote(2,0,0, notesEntier[2])          
            if(nbEntier>=4):
                self.AddNote(0,-1,-1, notesEntier[3])
            if(nbEntier>=5):
                self.AddNote(2,-1,-1, notesEntier[4])            

        elif(nbDemi == 1 and nbEntier<=4):
            if(nbEntier>=2 and not sym):
                self.AddNote(1,0,1, notesEntier[1])
            if(nbEntier>=2 and sym):
                self.AddNote(2,0,0, notesEntier[1])
            if(nbEntier>=3):
                self.AddNote(0,-1,-1, notesEntier[2])
            if(nbEntier>=4):
                self.AddNote(2,-1,-1, notesEntier[3])            
        
        else:
            if(nbEntier>=2 and not sym):
                self.AddNote(1,0,1, notesEntier[1])
            if(nbEntier>=2 and sym):
                self.AddNote(2,0,0, notesEntier[1])
            if(nbEntier>=3):
                self.AddNote(0,-1,-1, notesEntier[2])
            if(nbEntier>=4 and sym):
                self.AddNote(2,-1,-1, notesEntier[3])                      

            
        # Redstone & sol
        self.AddBlock(0,0,0, self.indexRepeter+tick-1,needsDown=True)
        self.AddBlock(0,-1,0, self.indexSol)
        
        self.AddBlock(1,0,-1, self.indexRedstone,needsDown=True)
        self.AddBlock(1,-1,-1, self.indexSol)
        
            
        
        #tick = int(tick)
        
        self.index +=1
     
    
    def AddNote(self,x,y,z,note):
        
        # Ajout du bloc de musqiue
        self.data.AddBlock(x ,y , z, note.note + self.offsetNotes , self.tick) 

        # Ajout du bloc de note en dessous
        self.data.AddBlock(x, y-1, z,note.instr+self.offsetInstr, self.tick) 
        
        # Ajout du bloc de note au dessus
        self.data.AddBlock(x, y+1, z,self.indexVide, self.tick)
        

    
    def AddBlock(self, x,y,z, index, randomAmount = -1, needsDown = False, needsUp = False):
        # Fonction à faire pour poser les blocks
        if(index == -1):
            return
        self.data.AddBlock(x,y,z, index, self.tick, randomAmount = randomAmount, needsDown= needsDown,needsUp=needsUp)
    
    def Rotate(self, i):
        self.data.Rotate(i, self.customNBT)
    
    def Flip(self):
        self.data.Flip(self.customNBT)
    
    def WriteNBT(self):

        sX = self.data.shape[0]
        sY = self.data.shape[1]
        sZ = self.data.shape[2]
        for i in range(sX):
            for j in range(sY):
                for k in range(sZ):
                    if(self.data.data[i-sX//2,j-sY//2,k-sZ//2,0] != -1):
                        #print('successful print')
                        self.customNBT.AddBloc([i-sX//2,j-sY//2,k-sZ//2], self.data.data[i-sX//2,j-sY//2,k-sZ//2,0])

    