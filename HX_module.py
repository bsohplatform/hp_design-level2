import copy
import numpy as np
from CoolProp.CoolProp import PropsSI

class Heatexchanger_module:
        
    def __init__(self, primary_in, primary_out, secondary_in, secondary_out):
        self.primary_in = primary_in
        self.primary_out = primary_out
        self.secondary_in = secondary_in
        self.secondary_out = secondary_out
        
    def FTHE(self, N_element: int = 30, N_row: int = 5):
        self.T_rvs = 0
        x_primary = np.ones(shape=(N_element, N_row))
        h_primary = np.zeros(shape=(N_element, N_row))
        T_primary = copy.deepcopy(h_primary)
        p_primary = copy.deepcopy(h_primary)
        x_secondary = copy.deepcopy(x_primary)
        T_secondary = copy.deepcopy(h_primary)
        p_secondary = copy.deepcopy(h_primary)
        h_secondary = copy.deepcopy(h_primary)
        LMTD = copy.deepcopy(h_primary)
        UA_element = copy.deepcopy(h_primary)
        
        p_secondary_out = self.secondary_out.p
        T_secondary_out = self.secondary_out.T
        h_secondary_out = self.secondary_out.h
        x_secondary_out = 1.0
        
        p_primary_in = self.primary_in.p
        T_primary_in = self.primary_in.T
        h_primary_in = self.primary_in.h
        x_primary_in = 1.0
        
        if p_primary_in < self.primary_in.p_crit:
            h_primaryl = PropsSI('H','P',p_primary_in,'Q',0.0,self.primary_in.fluidmixture)
            h_primaryg = PropsSI('H','P',p_primary_in,'Q',1.0,self.primary_in.fluidmixture)
            x_primary_in = (h_primary_in-h_primaryl)/(h_primaryg-h_primaryl)
            
        if p_secondary_out < self.secondary_in.p_crit:
            h_secondaryl = PropsSI('H','P',p_secondary_out,'Q',0.0,self.secondary_in.fluidmixture)
            h_secondaryg = PropsSI('H','P',p_secondary_out,'Q',1.0,self.secondary_in.fluidmixture)
            x_secondary_out = (h_secondary_out-h_secondaryl)/(h_secondaryg-h_secondaryl)
        
        for j in range(N_row):
            if self.T_rvs == 1:
                break
            for jj in range(N_element):
                if j == 0: # 첫번째 Row
                    h_secondary[jj,j] = h_secondary_out - self.secondary_in.q/N_row/self.secondary_in.m
                    p_secondary[jj,j] = p_secondary_out + (self.secondary_in.p - self.secondary_out.p)/N_row
                    T_secondary[jj,j] = PropsSI('T','H',h_secondary[jj,j],'P',p_secondary[jj,j], self.secondary_in.fluidmixture)
                    
                    if p_secondary[jj,j] < self.secondary_in.p_crit:
                        h_secondaryl = PropsSI('H','P',p_secondary[jj,j],'Q',0.0,self.secondary_in.fluidmixture)
                        h_secondaryg = PropsSI('H','P',p_secondary[jj,j],'Q',1.0,self.secondary_in.fluidmixture)
                        x_secondary[jj,j] = (h_secondary[jj,j]-h_secondaryl)/(h_secondaryg-h_secondaryl)
                        
                    if jj == 0: # 첫번째 tube:
                        h_primary[jj,j] = h_primary_in + (self.primary_in.q/N_element/N_row)/self.primary_in.m
                        p_primary[jj,j] = p_primary_in - (self.primary_in.p - self.primary_out.p)/N_element/N_row
                        T_primary[jj,j] = PropsSI('T','P',p_primary[jj,j],'H',h_primary[jj,j],self.primary_in.fluidmixture)
                        
                        if ((T_primary[jj,j] - T_secondary_out < 0 or T_primary_in - T_secondary[jj,j] < 0) and self.primary_in.q < 0) or\
                            ((T_primary[jj,j] - T_secondary_out > 0 or T_primary_in - T_secondary[jj,j] > 0) and self.primary_in.q > 0):
                            self.T_rvs = 1
                            break
                        else:
                            self.T_rvs = 0
                            LMTD[jj,j] = ((T_primary[jj,j]-T_secondary_out) - (T_primary_in-T_secondary[jj,j]))\
                                /np.log((T_primary[jj,j]-T_secondary_out)/(T_primary_in-T_secondary[jj,j]))
                            
                            UA_element[jj,j] = abs((self.primary_in.q/N_element/N_row) / LMTD[jj,j])
                    else:    
                        h_primary[jj,j] = h_primary[jj-1,j] + (self.primary_in.q/N_element/N_row)/self.primary_in.m
                        p_primary[jj,j] = p_primary[jj-1,j] - (self.primary_in.p - self.primary_out.p)/N_element/N_row
                        T_primary[jj,j] = PropsSI('T','P',p_primary[jj,j],'H',h_primary[jj,j],self.primary_in.fluidmixture)
                        
                        if ((T_primary[jj,j] - T_secondary_out < 0 or T_primary[jj-1,j] - T_secondary[jj,j] < 0) and self.primary_in.q < 0) or\
                            ((T_primary[jj,j] - T_secondary_out > 0 or T_primary[jj-1,j] - T_secondary[jj,j] > 0) and self.primary_in.q > 0):
                            self.T_rvs = 1
                            break
                        else:
                            self.T_rvs = 0
                            LMTD[jj,j] = ((T_primary[jj,j] - T_secondary_out) - (T_primary[jj-1,j] - T_secondary[jj,j]))\
                                /np.log((T_primary[jj,j] - T_secondary_out)/(T_primary[jj-1,j] - T_secondary[jj,j]))
                            
                            UA_element[jj,j] = abs((self.primary_in.q/N_element/N_row) / LMTD[jj,j])
                            
                    
                    if p_primary[jj,j] < self.primary_in.p_crit:
                        h_primaryl = PropsSI('H','P',p_primary[jj,j],'Q',0.0,self.primary_in.fluidmixture)
                        h_primaryg = PropsSI('H','P',p_primary[jj,j],'Q',1.0,self.primary_in.fluidmixture)
                        x_primary[jj,j] = (h_primary[jj,j]-h_primaryl)/(h_primaryg-h_primaryl)
                        
                elif round(j/2) == j/2 and j != 0: # 짝수
                    h_secondary[jj,j] = h_secondary[jj,j-1] - self.secondary_in.q/N_row/self.secondary_in.m
                    p_secondary[jj,j] = h_secondary[jj,j-1] + (self.secondary_in.p - self.secondary_out.p)/N_row
                    T_secondary[jj,j] = PropsSI('T','H',h_secondary[jj,j],'P',p_secondary[jj,j], self.secondary_in.fluidmixture)
                    
                    if p_secondary[jj,j] < self.secondary_in.p_crit:
                        h_secondaryl = PropsSI('H','P',p_secondary[jj,j],'Q',0.0,self.secondary_in.fluidmixture)
                        h_secondaryg = PropsSI('H','P',p_secondary[jj,j],'Q',1.0,self.secondary_in.fluidmixture)
                        x_secondary[jj,j] = (h_secondary[jj,j]-h_secondaryl)/(h_secondaryg-h_secondaryl)
                    
                    if jj == 0: # 첫번째 tube:
                        h_primary[jj,j] = h_primary[0,j-1] + (self.primary_in.q/N_element/N_row)/self.primary_in.m
                        p_primary[jj,j] = p_primary[0,j-1] - (self.primary_in.p - self.primary_out.p)/N_element/N_row
                        T_primary[jj,j] = PropsSI('T','P',p_primary[jj,j],'H',h_primary[jj,j],self.primary_in.fluidmixture)
                        
                        if ((T_primary[jj,j] - T_secondary[jj,j-1] < 0 or T_primary[0,j-1] - T_secondary[jj,j] < 0) and self.primary_in.q < 0) or\
                            ((T_primary[jj,j] - T_secondary[jj,j-1] > 0 or T_primary[0,j-1] - T_secondary[jj,j] > 0) and self.primary_in.q > 0):
                            self.T_rvs = 1
                            break
                        else:
                            self.T_rvs = 0
                            LMTD[jj,j] = ((T_primary[jj,j] - T_secondary[jj,j-1]) - (T_primary[0,j-1] - T_secondary[jj,j]))\
                                /np.log((T_primary[jj,j] - T_secondary[jj,j-1])/(T_primary[0,j-1] - T_secondary[jj,j]))
     
                            UA_element[jj,j] = abs((self.primary_in.q/N_element/N_row) / LMTD[jj,j])
                    else:
                        h_primary[jj,j] = h_primary[jj-1,j] + (self.primary_in.q/N_element/N_row)/self.primary_in.m
                        p_primary[jj,j] = p_primary[jj-1,j] - (self.primary_in.p - self.primary_out.p)/N_element/N_row
                        T_primary[jj,j] = PropsSI('T','P',p_primary[jj,j],'H',h_primary[jj,j],self.primary_in.fluidmixture)
                        
                        if ((T_primary[jj,j] - T_secondary[jj,j-1] < 0 or T_primary[jj-1,j] - T_secondary[jj,j] < 0) and self.primary_in.q < 0) or\
                            ((T_primary[jj,j] - T_secondary[jj,j-1] > 0 or T_primary[jj-1,j] - T_secondary[jj,j] > 0) and self.primary_in.q > 0):
                            self.T_rvs = 1
                            break
                        else:
                            self.T_rvs = 0
                            LMTD[jj,j] = ((T_primary[jj,j] - T_secondary[jj,j-1]) - (T_primary[jj-1,j] - T_secondary[jj,j]))\
                                /np.log((T_primary[jj,j] - T_secondary[jj,j-1])/(T_primary[jj-1,j] - T_secondary[jj,j]))
                            
                            UA_element[jj,j] = abs((self.primary_in.q/N_element/N_row) / LMTD[jj,j])
                            
                    if p_primary[jj,j] < self.primary_in.p_crit:
                        h_primaryl = PropsSI('H','P',p_primary[jj,j],'Q',0.0,self.primary_in.fluidmixture)
                        h_primaryg = PropsSI('H','P',p_primary[jj,j],'Q',1.0,self.primary_in.fluidmixture)
                        x_primary[jj,j] = (h_primary[jj,j]-h_primaryl)/(h_primaryg-h_primaryl)
                        
                else: # 홀수
                    h_secondary[N_element-jj-1,j] = h_secondary[N_element-jj-1,j-1] - self.secondary_in.q/N_row/self.secondary_in.m
                    p_secondary[N_element-jj-1,j] = p_secondary[N_element-jj-1,j-1] + (self.secondary_in.p - self.secondary_in.p)/N_row
                    T_secondary[N_element-jj-1,j] = PropsSI('T','H',h_secondary[N_element-jj-1,j],'P',p_secondary[N_element-jj-1,j],self.secondary_in.fluidmixture)
                    
                    if p_secondary[N_element-jj-1,j] < self.secondary_in.p_crit:
                        h_secondaryl = PropsSI('H','P',p_secondary[N_element-jj-1,j],'Q',0.0,self.secondary_in.fluidmixture)
                        h_secondaryg = PropsSI('H','P',p_secondary[N_element-jj-1,j],'Q',1.0,self.secondary_in.fluidmixture)
                        x_secondary[N_element-jj-1,j+1] = (h_secondary[N_element-jj-1,j]-h_secondaryl)/(h_secondaryg-h_secondaryl)
                    
                    if jj == 0: # Return 튜브
                        h_primary[N_element-jj-1,j] = h_primary[N_element-1,j-1] + (self.primary_in.q/N_element/N_row)/self.primary_in.m
                        p_primary[N_element-jj-1,j] = p_primary[N_element-1,j-1] - (self.primary_in.p - self.primary_out.p)/N_element/N_row
                        T_primary[N_element-jj-1,j] = PropsSI('T','P',p_primary[N_element-jj-1,j],'H',h_primary[N_element-jj-1,j],self.primary_in.fluidmixture)
                        
                        if ((T_primary[N_element-jj-1,j] - T_secondary[N_element-jj-1,j-1] < 0 or T_primary[N_element-1,j-1] - T_secondary[N_element-jj-1,j] < 0) and self.primary_in.q < 0) or\
                            ((T_primary[N_element-jj-1,j] - T_secondary[N_element-jj-1,j-1] > 0 or T_primary[N_element-1,j-1] - T_secondary[N_element-jj-1,j] > 0) and self.primary_in.q > 0):
                            self.T_rvs = 1
                            break
                        else:
                            self.T_rvs = 0
                            LMTD[N_element-jj-1,j] = ((T_primary[N_element-jj-1,j] - T_secondary[N_element-jj-1,j-1]) - (T_primary[N_element-1,j-1] - T_secondary[N_element-jj-1,j]))\
                                /np.log((T_primary[N_element-jj-1,j] - T_secondary[N_element-jj-1,j-1])/(T_primary[N_element-1,j-1] - T_secondary[N_element-jj-1,j]))
                            
                            UA_element[N_element-jj-1,j] = abs((self.primary_in.q/N_element/N_row) / LMTD[N_element-jj-1,j])
                    
                    else:
                        h_primary[N_element-jj-1,j] = h_primary[N_element-jj,j] + (self.primary_in.q/N_element/N_row)/self.primary_in.m
                        p_primary[N_element-jj-1,j] = p_primary[N_element-jj,j] - (self.primary_in.p - self.primary_out.p)/N_element/N_row
                        T_primary[N_element-jj-1,j] = PropsSI('T','P',p_primary[N_element-jj-1,j],'H',h_primary[N_element-jj-1,j],self.primary_in.fluidmixture)
                        
                        if ((T_primary[N_element-jj-1,j] - T_secondary[N_element-jj-1,j-1] < 0 or T_primary[N_element-jj,j] - T_secondary[N_element-jj-1,j] < 0) and self.primary_in.q < 0) or\
                            ((T_primary[N_element-jj-1,j] - T_secondary[N_element-jj-1,j-1] > 0 or T_primary[N_element-jj,j] - T_secondary[N_element-jj-1,j] > 0) and self.primary_in.q > 0):
                            self.T_rvs = 1
                            break
                        else:
                            self.T_rvs = 0
                            LMTD[N_element-jj-1,j] = ((T_primary[N_element-jj-1,j] - T_secondary[N_element-jj-1,j-1]) - (T_primary[N_element-jj,j] - T_secondary[N_element-jj-1,j]))\
                                /np.log((T_primary[N_element-jj-1,j] - T_secondary[N_element-jj-1,j-1])/(T_primary[N_element-jj,j] - T_secondary[N_element-jj-1,j]))
                            
                            UA_element[N_element-jj-1,j] = abs((self.primary_in.q/N_element/N_row) / LMTD[N_element-jj-1,j])           

                    if p_primary[N_element-jj-1,j] < self.primary_in.p_crit:
                        h_primaryl = PropsSI('H','P',p_primary[N_element-jj-1,j],'Q',0.0,self.primary_in.fluidmixture)
                        h_primaryg = PropsSI('H','P',p_primary[N_element-jj-1,j],'Q',1.0,self.primary_in.fluidmixture)
                        x_primary[N_element-jj-1,j] = (h_primary[N_element-jj-1,j]-h_primaryl)/(h_primaryg-h_primaryl)

        
        self.UA = np.sum(np.sum(UA_element))
        self.T_lm = abs(self.primary_in.q)/self.UA
        self.primary_in.x = x_primary_in
        
        if np.round(N_row/2) != N_row/2: # 짝수
            self.primary_out.T = T_primary[N_element-1,N_row-1]
            self.primary_out.h = h_primary[N_element-1,N_row-1]
            self.primary_out.x = x_primary[N_element-1,N_row-1]
        else: # 홀수
            self.primary_out.T = T_primary[0,N_row-1]
            self.primary_out.h = h_primary[0,N_row-1]
            self.primary_out.x = x_primary[0,N_row-1]

        self.secondary_in.x = x_secondary[0,N_row-1]
        self.secondary_out.x = x_secondary_out
        
    def PHE(self, N_element: int = 30):
        x_primary = np.ones(shape=(N_element+1))
        h_primary = np.zeros(shape=(N_element+1))
        T_primary = copy.deepcopy(h_primary)
        p_primary = copy.deepcopy(h_primary)
        x_secondary = copy.deepcopy(x_primary)
        T_secondary = copy.deepcopy(h_primary)
        p_secondary = copy.deepcopy(h_primary)
        h_secondary = copy.deepcopy(h_primary)
        dT = copy.deepcopy(h_primary)
        LMTD = np.zeros(shape=(N_element))
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
        
        if (dT[0] < 0.0 and self.primary_in.q < 0.0) or (dT[0] > 0.0 and self.primary_in.q > 0.0):
            self.T_rvs = 1
        else:
            self.T_rvs = 0
    
        for i in range(N_element):
            h_primary[i+1] = h_primary[i] + self.primary_in.q/N_element/self.primary_in.m
            p_primary[i+1] = p_primary[i] - (self.primary_in.p - self.primary_out.p)/N_element
            T_primary[i+1] = PropsSI('T','H',h_primary[i+1],'P',p_primary[i+1],self.primary_in.fluidmixture)
            
            if p_primary[i+1] < self.primary_in.p_crit:
                h_primaryl = PropsSI('H','P',p_primary[i+1],'Q',0.0,self.primary_in.fluidmixture)
                h_primaryg = PropsSI('H','P',p_primary[i+1],'Q',1.0,self.primary_in.fluidmixture)
                x_primary[i+1] = (h_primary[i+1]-h_primaryl)/(h_primaryg-h_primaryl)
            
            h_secondary[i+1] = h_secondary[i] - self.secondary_in.q/N_element/self.secondary_in.m
            p_secondary[i+1] = p_secondary[i] + (self.secondary_in.p - self.secondary_out.p)/N_element
            T_secondary[i+1] = PropsSI('T','H',h_secondary[i+1],'P',p_secondary[i+1],self.secondary_in.fluidmixture)
            
            if p_secondary[i+1] < self.secondary_in.p_crit:
                h_secondaryl = PropsSI('H','P',p_secondary[i+1],'Q',0.0,self.secondary_in.fluidmixture)
                h_secondaryg = PropsSI('H','P',p_secondary[i+1],'Q',1.0,self.secondary_in.fluidmixture)
                x_secondary[i+1] = (h_secondary[i+1]-h_secondaryl)/(h_secondaryg-h_secondaryl)
            
            dT[i+1] = T_primary[i+1] - T_secondary[i+1]
            if (dT[i+1] < 0.0 and self.primary_in.q < 0.0) or (dT[i+1] > 0.0 and self.primary_in.q > 0.0):
                self.T_rvs = 1
                break
            else:
                self.T_rvs = 0
                LMTD[i] = ((T_primary[i+1]-T_secondary[i+1]) - (T_primary[i]-T_secondary[i]))\
                            /np.log((T_primary[i+1]-T_secondary[i+1])/(T_primary[i]-T_secondary[i]))
                            
                UA_element[i] = abs((self.primary_in.q/N_element) / LMTD[i])  
        
        self.UA = np.sum(UA_element)
        self.T_pp = min(abs(dT))
        
        self.primary_in.x = x_primary[0]
        
        self.primary_out.T = T_primary[N_element]
        self.primary_out.h = h_primary[N_element]
        self.primary_out.x = x_primary[N_element]
        
        self.secondary_out.x = x_secondary[0]
        
    def SIMPHX(self, eff_HX:float = 0.9):
        h_secondary_out_ideal = PropsSI('H','T',self.primary_in.T,'P',self.secondary_out.p,self.secondary_in.fluidmixture)
        h_primary_out_ideal = PropsSI('H','T',self.secondary_in.T,'P',self.primary_out.p,self.primary_in.fluidmixture)
        
        q_ideal = min(abs(h_primary_out_ideal-self.primary_in.h),abs(h_secondary_out_ideal - self.secondary_in.h))
        if self.primary_in.T > self.secondary_in.T:
            self.primary_in.q = -q_ideal*eff_HX
        else:
            self.primary_in.q = q_ideal*eff_HX
            
        self.secondary_in.q = -self.primary_in.q
        
        self.primary_out.h = self.primary_in.h + self.primary_in.q
        self.secondary_out.h = self.secondary_in.h + self.secondary_in.q
        
        self.primary_out.T = PropsSI('T','H',self.primary_out.h,'P',self.primary_out.p,self.primary_out.fluidmixture)
        self.secondary_out.T = PropsSI('T','H',self.secondary_out.h,'P',self.secondary_out.p,self.secondary_out.fluidmixture)
        
        self.primary_out.s = PropsSI('S','T',self.primary_out.T,'P',self.primary_out.p, self.primary_out.fluidmixture)
        self.secondary_out.s = PropsSI('S','T',self.secondary_out.T,'P',self.secondary_out.p,self.secondary_out.fluidmixture)
        
        