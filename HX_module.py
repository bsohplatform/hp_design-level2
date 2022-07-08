import copy
from dataclasses import dataclass
import numpy as np
from CoolProp.CoolProp import PropsSI
# test 용 import
from STED_types import WireObjectFluid



class Heatexchanger_module:
        
    def __init__(self, primary_in, primary_out, secondary_in, secondary_out, N_element: int= 30, N_row: int = 5):
        self.primary_in = primary_in
        self.primary_out = primary_out
        self.secondary_in = secondary_in
        self.secondary_out = secondary_out
        self.N_element = N_element
        self.N_row = N_row
        
    def FTHE(self):
        
        x_primary = np.ones(shape=(self.N_element+1, self.N_row+1))
        h_primary = np.zeros(shape=(self.N_element+1, self.N_row+1))
        T_primary = copy.deepcopy(h_primary)
        p_primary = copy.deepcopy(h_primary)
        x_secondary = copy.deepcopy(x_primary)
        T_secondary = copy.deepcopy(h_primary)
        p_secondary = copy.deepcopy(h_primary)
        h_secondary = copy.deepcopy(h_primary)
        LMTD = np.zeros(shape=(self.N_element, self.N_row))
        UA_element = copy.deepcopy(LMTD)
        
        p_secondary[:,0] = self.secondary_out.p
        T_secondary[:,0] = self.secondary_out.T
        h_secondary[:,0] = self.secondary_out.h
        
        p_primary[0,0] = self.primary_in.p
        T_primary[0,0] = self.primary_in.T
        h_primary[0,0] = self.primary_in.h
        
        if p_primary[0,0] < self.primary_in.p_crit:
            h_primaryl = PropsSI('H','P',p_primary[0,0],'Q',0.0,self.primary_in.fluidmixture)
            h_primaryg = PropsSI('H','P',p_primary[0,0],'Q',1.0,self.primary_in.fluidmixture)
            x_primary[0,0] = (h_primary[0,0]-h_primaryl)/(h_primaryg-h_primaryl)
            
        if p_secondary[0,0] < self.secondary_in.p_crit:
            h_secondaryl = PropsSI('H','P',p_secondary[0,0],'Q',0.0,self.secondary_in.fluidmixture)
            h_secondaryg = PropsSI('H','P',p_secondary[0,0],'Q',1.0,self.secondary_in.fluidmixture)
            x_secondary[0,0] = (h_secondary[0,0]-h_secondaryl)/(h_secondaryg-h_secondaryl)
        
        for j in range(self.N_row):
            for jj in range(self.N_element):
                if round(j/2) == j/2: # 짝수
                    h_primary[jj+1,j] = h_primary[jj,j] - (self.primary_in.q/self.N_element/self.N_row)/self.primary_in.m
                    p_primary[jj+1,j] = p_primary[jj,j] - (self.primary_in.p - self.primary_out.p)/self.N_element/self.N_row
                    T_primary[jj+1,j] = PropsSI('T','P',p_primary[jj+1,j],'H',h_primary[jj+1,j],self.primary_in.fluidmixture)
                    
                    if p_primary[jj+1,j] < self.primary_in.p_crit:
                        h_primaryl = PropsSI('H','P',p_primary[jj+1,j],'Q',0.0,self.primary_in.fluidmixture)
                        h_primaryg = PropsSI('H','P',p_primary[jj+1,j],'Q',1.0,self.primary_in.fluidmixture)
                        x_primary[jj+1,j] = (h_primary[jj+1,j]-h_primaryl)/(h_primaryg-h_primaryl)
                        
                    h_secondary[jj,j+1] = h_secondary[jj,j] - self.primary_in.q/self.N_row/self.secondary_in.m
                    p_secondary[jj,j+1] = p_secondary[jj,j] + (self.secondary_in.p - self.secondary_out.p)/self.N_row
                    T_secondary[jj,j+1] = PropsSI('T','H',h_secondary[jj,j+1],'P',p_secondary[jj,j+1],self.secondary_in.fluidmixture)
                    
                    if p_secondary[jj,j+1] < self.secondary_in.p_crit:
                        h_secondaryl = PropsSI('H','P',p_secondary[jj,j+1],'Q',0.0,self.secondary_in.fluidmixture)
                        h_secondaryg = PropsSI('H','P',p_secondary[jj,j+1],'Q',1.0,self.secondary_in.fluidmixture)
                        x_secondary[jj,j+1] = (h_secondary[jj,j+1]-h_secondaryl)/(h_secondaryg-h_secondaryl)
                    if (T_primary[jj+1,j] - T_secondary[jj,j+1] < 0 and self.primary_in.q > 0) or (T_primary[jj+1,j] - T_secondary[jj,j+1] > 0 and self.primary_in.q < 0):
                        self.T_rvs = 1
                        break
                    else:
                        self.T_rvs = 0
                        LMTD[jj,j] = ((T_primary[jj+1,j]-T_secondary[jj,j+1]) - (T_primary[jj,j]-T_secondary[jj,j]))\
                            /np.log((T_primary[jj+1,j]-T_secondary[jj,j+1])/(T_primary[jj,j]-T_secondary[jj,j]))
                        UA_element[jj,j] = (self.primary_in.q/self.N_element/self.N_row) / LMTD[jj,j]
                        
                        if jj == self.N_element-1:
                            h_primary[self.N_element,j+1] = h_primary[self.N_element,j]
                            T_primary[self.N_element,j+1] = T_primary[self.N_element,j]
                            p_primary[self.N_element,j+1] = p_primary[self.N_element,j]
                            x_primary[self.N_element,j+1] = x_primary[self.N_element,j]
                            
                else: # 홀수
                    h_primary[self.N_element-jj-1,j] = h_primary[self.N_element-jj,j] - (self.primary_in.q/self.N_element/self.N_row)/self.primary_in.m
                    p_primary[self.N_element-jj-1,j] = p_primary[self.N_element-jj,j] - (self.primary_in.p - self.primary_out.p)/self.N_element/self.N_row
                    T_primary[self.N_element-jj-1,j] = PropsSI('T','P',p_primary[self.N_element-jj-1,j],'H',h_primary[self.N_element-jj-1,j],self.primary_in.fluidmixture)
                    
                    if p_primary[self.N_element-jj-1,j] < self.primary_in.p_crit:
                        h_primaryl = PropsSI('H','P',p_primary[self.N_element-jj-1,j],'Q',0.0,self.primary_in.fluidmixture)
                        h_primaryg = PropsSI('H','P',p_primary[self.N_element-jj-1,j],'Q',1.0,self.primary_in.fluidmixture)
                        x_primary[self.N_element-jj-1,j] = (h_primary[self.N_element-jj-1,j]-h_primaryl)/(h_primaryg-h_primaryl)
                        
                    h_secondary[self.N_element-jj-1,j+1] = h_secondary[self.N_element-jj-1,j] - self.primary_in.q/self.N_row/self.secondary_in.m
                    p_secondary[self.N_element-jj-1,j+1] = p_secondary[self.N_element-jj-1,j] + (self.secondary_in.p - self.secondary_in.p)/self.N_row
                    T_secondary[self.N_element-jj-1,j+1] = PropsSI('T','H',h_secondary[self.N_element-jj-1,j+1],'P',p_secondary[self.N_element-jj-1,j+1],self.secondary_in.fluidmixture)
                    
                    if p_secondary[self.N_element-jj-1,j+1] < self.secondary_in.p_crit:
                        h_secondaryl = PropsSI('H','P',p_secondary[self.N_element-jj-1,j+1],'Q',0.0,self.secondary_in.fluidmixture)
                        h_secondaryg = PropsSI('H','P',p_secondary[self.N_element-jj-1,j+1],'Q',1.0,self.secondary_in.fluidmixture)
                        x_secondary[self.N_element-jj-1,j+1] = (h_secondary[self.N_element-jj-1,j+1]-h_secondaryl)/(h_secondaryg-h_secondaryl)
                    
                    if (T_primary[self.N_element-jj-1,j] - T_secondary[self.N_element-jj-1,j+1] < 0 and self.primary_in.q > 0) or (T_primary[self.N_element-jj-1,j] - T_secondary[self.N_element-jj-1,j+1] > 0 and self.primary_in.q < 0):
                        self.T_rvs = 1
                        break
                    else:
                        self.T_rvs = 0
                        LMTD[self.N_element-jj-1,j] = ((T_primary[self.N_element-jj-1,j]-T_secondary[self.N_element-jj-1,j+1]) - (T_primary[self.N_element-jj,j]-T_secondary[self.N_element-jj-1,j]))\
                            /np.log((T_primary[self.N_element-jj-1,j]-T_secondary[self.N_element-jj-1,j+1])/(T_primary[self.N_element-jj,j]-T_secondary[self.N_element-jj-1,j]))
                        UA_element[self.N_element-jj-1,j] = (self.primary_in.q/self.N_element/self.N_row) / LMTD[self.N_element-jj-1,j]
                        
                        if jj == self.N_element-1:
                            h_primary[0,j+1] = h_primary[0,j]
                            T_primary[0,j+1] = T_primary[0,j]
                            p_primary[0,j+1] = p_primary[0,j]
                            x_primary[0,j+1] = x_primary[0,j]
                
                if self.T_rvs == 1:
                    break
        self.UA = np.sum(np.sum(UA_element))
        self.T_lm = self.primary_in.q/self.UA
        
        self.primary_in.x = x_primary[0,0]
        
        if np.round(self.N_row/2) != self.N_row/2: # 짝수
            self.primary_out.T = T_primary[self.N_element,self.N_row]
            self.primary_out.h = h_primary[self.N_element,self.N_row]
            self.primary_out.x = x_primary[self.N_element,self.N_row]
        else: # 홀수
            self.primary_out.T = T_primary[0,self.N_row]
            self.primary_out.h = h_primary[0,self.N_row]
            self.primary_out.x = x_primary[0,self.N_row]
        
        self.secondary_in.T = T_secondary[0,self.N_row]
        self.secondary_in.h = h_secondary[0,self.N_row]
        self.secondary_in.x = x_secondary[0,self.N_row]
            
        self.secondary_out.x = x_secondary[0,0]
        
    def PHE(self):
        x_primary = np.ones(shape=(self.N_element+1))
        h_primary = np.zeros(shape=(self.N_element+1))
        T_primary = copy.deepcopy(h_primary)
        p_primary = copy.deepcopy(h_primary)
        x_secondary = copy.deepcopy(x_primary)
        T_secondary = copy.deepcopy(h_primary)
        p_secondary = copy.deepcopy(h_primary)
        h_secondary = copy.deepcopy(h_primary)
        dT = copy.deepcopy(h_primary)
        LMTD = np.zeros(shape=(self.N_element))
        UA_element = copy.deepcopy(LMTD)
        
        p_secondary[0] = self.secondary_out.p
        T_secondary[0] = self.secondary_out.T
        h_secondary[0] = self.secondary_out.h
        
        p_primary[0] = self.primary_in.p
        T_primary[0] = self.primary_in.T
        h_primary[0] = self.primary_in.h
        
        if p_primary[0] < self.primary_in.p_crit:
            h_primaryl = PropsSI('H','P',p_primary[0],'Q',0.0,self.primary_in.fluidmixture)
            h_primaryg = PropsSI('H','P',p_primary[0],'Q',1.0,self.primary_in.fluidmixture)
            x_primary[0] = (h_primary[0]-h_primaryl)/(h_primaryg-h_primaryl)
        
        if p_secondary[0] < self.secondary_in.p_crit:
            h_secondaryl = PropsSI('H','P',p_secondary[0],'Q',0.0,self.secondary_in.fluidmixture)
            h_secondaryg = PropsSI('H','P',p_secondary[0],'Q',1.0,self.secondary_in.fluidmixture)
            x_secondary[0] = (h_secondary[0]-h_secondaryl)/(h_secondaryg-h_secondaryl)
        
        dT[0] = T_primary[0] - T_secondary[0]
        
        if (dT[0] < 0.0 and self.primary_in.q > 0.0) or (dT[0] > 0.0 and self.primary_in.q < 0.0):
            self.T_rvs = 1
        else:
            self.T_rvs = 0
    
        for i in range(self.N_element):
            h_primary[i+1] = h_primary[i] - self.primary_in.q/self.N_element/self.primary_in.m
            p_primary[i+1] = p_primary[i] - (self.primary_in.p - self.primary_out.p)/self.N_element
            T_primary[i+1] = PropsSI('T','H',h_primary[i+1],'P',p_primary[i+1],self.primary_in.fluidmixture)
            
            if p_primary[i+1] < self.primary_in.p_crit:
                h_primaryl = PropsSI('H','P',p_primary[i+1],'Q',0.0,self.primary_in.fluidmixture)
                h_primaryg = PropsSI('H','P',p_primary[i+1],'Q',1.0,self.primary_in.fluidmixture)
                x_primary[i+1] = (h_primary[i+1]-h_primaryl)/(h_primaryg-h_primaryl)
            
            h_secondary[i+1] = h_secondary[i] - self.primary_in.q/self.N_element/self.secondary_in.m
            p_secondary[i+1] = p_secondary[i] + (self.secondary_in.p - self.secondary_out.p)/self.N_element
            T_secondary[i+1] = PropsSI('T','H',h_secondary[i+1],'P',p_secondary[i+1],self.secondary_in.fluidmixture)
            
            if p_secondary[i+1] < self.secondary_in.p_crit:
                h_secondaryl = PropsSI('H','P',p_secondary[i+1],'Q',0.0,self.secondary_in.fluidmixture)
                h_secondaryg = PropsSI('H','P',p_secondary[i+1],'Q',1.0,self.secondary_in.fluidmixture)
                x_secondary[i+1] = (h_secondary[i+1]-h_secondaryl)/(h_secondaryg-h_secondaryl)
            
            dT[i+1] = T_primary[i+1] - T_secondary[i+1]
            if (dT[i+1] < 0.0 and self.primary_in.q > 0.0) or (dT[i+1] > 0.0 and self.primary_in.q < 0.0):
                self.T_rvs = 1
                break
            else:
                self.T_rvs = 0
                LMTD[i] = ((T_primary[i+1]-T_secondary[i+1]) - (T_primary[i]-T_secondary[i]))\
                            /np.log((T_primary[i+1]-T_secondary[i+1])/(T_primary[i]-T_secondary[i]))
                            
                UA_element[i] = (self.primary_in.q/self.N_element) / LMTD[i]    
        
        self.UA = np.sum(UA_element)
        self.T_pp = min(dT)
        
        self.primary_in.x = x_primary[0]
        
        self.primary_out.T = T_primary[self.N_element]
        self.primary_out.h = h_primary[self.N_element]
        self.primary_out.x = x_primary[self.N_element]
        
        self.secondary_out.x = x_secondary[0]
        
        self.secondary_in.T = T_secondary[self.N_element]
        self.secondary_in.h = h_secondary[self.N_element]
        self.secondary_in.x = x_secondary[self.N_element]
        
            

if __name__ == "__main__":
        # Condensor input
        '''
        secondary_in = WireObjectFluid({'water':1})
        secondary_in.T = 370
        secondary_in.p = 301300
        secondary_in.m = 1.0
        secondary_in.h = PropsSI('H','T',secondary_in.T,'P',secondary_in.p,secondary_in.fluidmixture)
        
        secondary_out = copy.deepcopy(secondary_in)
        secondary_out.T = 380
        secondary_out.p = 301300
        secondary_out.h = PropsSI('H','T',secondary_out.T,'P',secondary_out.p,secondary_out.fluidmixture)
        
        primary_in = WireObjectFluid({'R134a':1})
        primary_in.q = (secondary_out.h - secondary_in.h)*secondary_in.m
        primary_in.T = 400
        primary_in.p = 5000000
        primary_in.m = 1.0
        primary_in.h = PropsSI('H','T',primary_in.T,'P',primary_in.p,primary_in.fluidmixture)
        
        primary_out = copy.deepcopy(primary_in)
        primary_out.p = 4990000
        
        condensor = Heatexchanger_module(primary_in, primary_out, secondary_in, secondary_out)
        condensor.FTHE()
        
        print(primary_out.h)
        print(condensor.T_rvs)
        print(condensor.UA)
        '''
        # Evaporate input
        
        
        secondary_in = WireObjectFluid({'water':1})
        secondary_in.T = 320
        secondary_in.p = 101300
        secondary_in.m = 1.0
        secondary_in.h = PropsSI('H','T',secondary_in.T,'P',secondary_in.p,secondary_in.fluidmixture)
        
        secondary_out = copy.deepcopy(secondary_in)
        secondary_out.T = 310
        secondary_out.p = 101300
        secondary_out.h = PropsSI('H','T',secondary_out.T,'P',secondary_out.p,secondary_out.fluidmixture)
        
        primary_in = WireObjectFluid({'R134A':1})
        primary_in.q = (secondary_out.h - secondary_in.h)*secondary_in.m
        primary_in.p = 400000
        primary_in.m = 1.0
        primary_in.h = PropsSI('H','P',primary_in.p,'Q',0.8,primary_in.fluidmixture)
        primary_in.T = PropsSI('T','P',primary_in.p,'Q',0.8,primary_in.fluidmixture)
        primary_out = copy.deepcopy(primary_in)
        primary_out.p = 399000
        primary_out.T = PropsSI('T','P',primary_out.p,'Q',1.0,primary_out.fluidmixture)+5.0
        primary_out.h = PropsSI('H','P',primary_out.p,'T',primary_out.T,primary_out.fluidmixture)
        
        evaporator = Heatexchanger_module(primary_in, primary_out, secondary_in, secondary_out)
        evaporator.FTHE()
        
        print(primary_out.h)
        print(evaporator.T_rvs)
        print(evaporator.UA)
        
        '''
        # Cascade input
        secondary_in = WireObjectFluid({'R134A':1})
        secondary_in.p = 3000000
        secondary_in.m = 1.0
        secondary_in.T = PropsSI('T','P',secondary_in.p,'Q',1.0,secondary_in.fluidmixture)+5
        secondary_in.h = PropsSI('H','T',secondary_in.T,'P',secondary_in.p,secondary_in.fluidmixture)
        
        
        secondary_out = copy.deepcopy(secondary_in)
        secondary_out.p = 2999000
        secondary_out.T = PropsSI('T','P',secondary_out.p,'Q',0.0,secondary_in.fluidmixture)-1
        secondary_out.h = PropsSI('H','T',secondary_out.T,'P',secondary_out.p,secondary_out.fluidmixture)
        
        
        primary_in = WireObjectFluid({'R134A':1})
        primary_in.q = (secondary_out.h - secondary_in.h)*secondary_in.m
        primary_in.p = 400000
        primary_in.m = 1.0
        primary_in.h = PropsSI('H','P',primary_in.p,'Q',0.0,primary_in.fluidmixture)
        primary_in.T = PropsSI('T','P',primary_in.p,'Q',0.0,primary_in.fluidmixture)
        primary_out = copy.deepcopy(primary_in)
        primary_out.p = 399000
        primary_out.T = PropsSI('T','P',primary_out.p,'Q',1.0,primary_out.fluidmixture)+10.0
        primary_out.h = PropsSI('H','P',primary_out.p,'T',primary_out.T,primary_out.fluidmixture)
        
        cascadeHX = Heatexchanger_module(primary_in, primary_out, secondary_in, secondary_out)
        cascadeHX.PHE()
        
        print(primary_out.h)
        print(cascadeHX.T_rvs)
        print(cascadeHX.UA)
        '''