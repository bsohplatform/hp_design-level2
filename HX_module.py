from cmath import log
import numpy as np
from CoolProp.CoolProp import PropsSI

class Heatexchanger_module:
        
    def __init__(self, primary_in, primary_out, pph, secondary_in, secondary_out, sph):
        self.primary_in = primary_in
        self.primary_out = primary_out
        self.pph = pph
        self.secondary_in = secondary_in
        self.secondary_out = secondary_out
        self.sph = sph
        
    def FTHE(self, N_element: int, N_turn: int, N_row: int):
        self.T_rvs = 0
        h_primary = np.zeros(shape=(N_element*N_turn, N_row))
        T_primary = np.zeros(shape=(N_element*N_turn, N_row))
        p_primary = np.zeros(shape=(N_element*N_turn, N_row))
        T_secondary = np.zeros(shape=(N_element*N_turn, N_row))
        p_secondary = np.zeros(shape=(N_element*N_turn, N_row))
        h_secondary = np.zeros(shape=(N_element*N_turn, N_row))
        LMTD = np.zeros(shape=(N_element*N_turn, N_row))
        UA_element = np.zeros(shape=(N_element*N_turn, N_row))
        
        p_secondary_in = self.secondary_in.p
        T_secondary_in = self.secondary_in.T
        h_secondary_in = self.secondary_in.h
        
        p_primary_in = self.primary_in.p
        T_primary_in = self.primary_in.T
        h_primary_in = self.primary_in.h
        
        for j in range(N_row):
            for tt in range(N_turn):
                for jj in range(N_element):
                    if j == 0: # 첫번째 Row
                        if self.sph == 0:
                            T_secondary[N_element*tt+jj,j] = T_secondary_in + self.secondary_in.q/N_row/self.secondary_in.m/0.5/(self.secondary_in.Cp + self.secondary_out.Cp)
                        else:
                            h_secondary[N_element*tt+jj,j] = h_secondary_in + self.secondary_in.q/N_row/self.secondary_in.m
                            p_secondary[N_element*tt+jj,j] = p_secondary_in - (self.secondary_in.p - self.secondary_out.p)/N_row
                            T_secondary[N_element*tt+jj,j] = PropsSI('T','H',h_secondary[N_element*tt+jj,j],'P',p_secondary[N_element*tt+jj,j], self.secondary_in.fluidmixture)
                        
                        if jj == 0: #Turn 입구
                            if self.pph == 0:
                                T_primary[N_element*tt+jj,j] = T_primary_in + self.primary_in.q/N_element/N_turn/N_row/self.primary_in.m/0.5/(self.primary_in.Cp + self.primary_out.Cp)
                            else:    
                                h_primary[N_element*tt+jj,j] = h_primary_in + (self.primary_in.q/N_element/N_turn/N_row)/self.primary_in.m
                                p_primary[N_element*tt+jj,j] = p_primary_in - (self.primary_in.p - self.primary_out.p)/N_element/N_turn/N_row
                                T_primary[N_element*tt+jj,j] = PropsSI('T','P',p_primary[N_element*tt+jj,j],'H',h_primary[N_element*tt+jj,j],self.primary_in.fluidmixture)
                            
                            if (T_primary_in - T_secondary_in < 0 and self.primary_in.q < 0) or (T_primary_in - T_secondary_in > 0 and self.primary_in.q > 0):
                                self.T_rvs = 1
                                break
                            else:
                                self.T_rvs = 0
                                LMTD[N_element*tt+jj,j] = ((T_primary_in-T_secondary_in) - (T_primary[N_element*tt+jj,j]-T_secondary[N_element*tt+jj,j]))\
                                    /np.log((T_primary_in-T_secondary_in)/(T_primary[N_element*tt+jj,j]-T_secondary[N_element*tt+jj,j]))
                                
                                UA_element[N_element*tt+jj,j] = abs((self.primary_in.q/N_element/N_turn/N_row) / LMTD[N_element*tt+jj,j])
                        else:
                            if self.pph == 0:
                                T_primary[N_element*tt+jj,j] = T_primary[N_element*tt+jj-1,j] + (self.primary_in.q/N_element/N_turn/N_row)/self.primary_in.m/0.5/(self.primary_in.Cp + self.primary_out.Cp)
                            else:    
                                h_primary[N_element*tt+jj,j] = h_primary[N_element*tt+jj-1,j] + (self.primary_in.q/N_element/N_turn/N_row)/self.primary_in.m
                                p_primary[N_element*tt+jj,j] = p_primary[N_element*tt+jj-1,j] - (self.primary_in.p - self.primary_out.p)/N_element/N_turn/N_row
                                T_primary[N_element*tt+jj,j] = PropsSI('T','P',p_primary[N_element*tt+jj,j],'H',h_primary[N_element*tt+jj,j],self.primary_in.fluidmixture)
                            
                            if jj == N_element-1:
                                T_primary_in = T_primary[N_element*tt+jj,j]
                                h_primary_in = h_primary[N_element*tt+jj,j]
                                p_primary_in = p_primary[N_element*tt+jj,j]
                            
                            if (T_primary[N_element*tt+jj-1,j] - T_secondary_in < 0 and self.primary_in.q < 0) or (T_primary[N_element*tt+jj-1,j] - T_secondary_in > 0 and self.primary_in.q > 0):
                                self.T_rvs = 1
                                break
                            else:
                                self.T_rvs = 0
                                LMTD[N_element*tt+jj,j] = ((T_primary[N_element*tt+jj-1,j] - T_secondary_in) - (T_primary[N_element*tt+jj,j] - T_secondary[N_element*tt+jj,j]))\
                                    /np.log((T_primary[N_element*tt+jj-1,j] - T_secondary_in)/(T_primary[N_element*tt+jj,j] - T_secondary[N_element*tt+jj,j]))
                                
                                UA_element[N_element*tt+jj,j] = abs((self.primary_in.q/N_element/N_turn/N_row) / LMTD[N_element*tt+jj,j])
                            
                    elif round(j/2) == j/2 and j != 0: # 짝수
                        if self.sph == 0:
                            T_secondary[N_element*tt+jj,j] = T_secondary[N_element*tt+jj,j-1] + self.secondary_in.q/N_row/self.secondary_in.m/0.5/(self.secondary_in.Cp + self.secondary_out.Cp)
                        else:
                            h_secondary[N_element*tt+jj,j] = h_secondary[N_element*tt+jj,j-1] + self.secondary_in.q/N_row/self.secondary_in.m
                            p_secondary[N_element*tt+jj,j] = h_secondary[N_element*tt+jj,j-1] - (self.secondary_in.p - self.secondary_out.p)/N_row
                            T_secondary[N_element*tt+jj,j] = PropsSI('T','H',h_secondary[N_element*tt+jj,j],'P',p_secondary[N_element*tt+jj,j], self.secondary_in.fluidmixture)
                        
                        if jj == 0: #Turn 입구
                            if self.pph == 0:
                                T_primary[N_element*tt+jj,j] = T_primary_in + (self.primary_in.q/N_element/N_turn/N_row)/self.primary_in.m/0.5/(self.primary_in.Cp + self.primary_out.Cp)
                            else:
                                h_primary[N_element*tt+jj,j] = h_primary_in + (self.primary_in.q/N_element/N_turn/N_row)/self.primary_in.m
                                p_primary[N_element*tt+jj,j] = p_primary_in - (self.primary_in.p - self.primary_out.p)/N_element/N_turn/N_row
                                T_primary[N_element*tt+jj,j] = PropsSI('T','P',p_primary[N_element*tt+jj,j],'H',h_primary[N_element*tt+jj,j],self.primary_in.fluidmixture)
                            
                            if (T_primary_in - T_secondary[N_element*tt+jj,j-1] < 0 and self.primary_in.q < 0) or (T_primary_in - T_secondary[N_element*tt+jj,j-1] > 0 and self.primary_in.q > 0):
                                self.T_rvs = 1
                                break
                            else:
                                self.T_rvs = 0
                                LMTD[N_element*tt+jj,j] = ((T_primary_in - T_secondary[N_element*tt+jj,j-1]) - (T_primary[N_element*tt+jj,j] - T_secondary[N_element*tt+jj,j]))\
                                    /np.log((T_primary_in - T_secondary[N_element*tt+jj,j-1])/(T_primary[N_element*tt+jj,j] - T_secondary[N_element*tt+jj,j]))
        
                                UA_element[N_element*tt+jj,j] = abs((self.primary_in.q/N_element/N_turn/N_row) / LMTD[N_element*tt+jj,j])
                        else:
                            if self.pph == 0:
                                T_primary[N_element*tt+jj,j] = T_primary[N_element*tt+jj-1,j] + (self.primary_in.q/N_element/N_turn/N_row)/self.primary_in.m/0.5/(self.primary_in.Cp + self.primary_out.Cp)
                            else:
                                h_primary[N_element*tt+jj,j] = h_primary[N_element*tt+jj-1,j] + (self.primary_in.q/N_element/N_turn/N_row)/self.primary_in.m
                                p_primary[N_element*tt+jj,j] = p_primary[N_element*tt+jj-1,j] - (self.primary_in.p - self.primary_out.p)/N_element/N_turn/N_row
                                T_primary[N_element*tt+jj,j] = PropsSI('T','P',p_primary[N_element*tt+jj,j],'H',h_primary[N_element*tt+jj,j],self.primary_in.fluidmixture)
                            
                            if jj == N_element-1:
                                T_primary_in = T_primary[N_element*tt+jj,j]
                                h_primary_in = h_primary[N_element*tt+jj,j]
                                p_primary_in = p_primary[N_element*tt+jj,j]
                            
                            if (T_primary[N_element*tt+jj-1,j] - T_secondary[N_element*tt+jj,j-1] < 0 and self.primary_in.q < 0) or (T_primary[N_element*tt+jj-1,j] - T_secondary[N_element*tt+jj,j-1] > 0 and self.primary_in.q > 0):
                                self.T_rvs = 1
                                break
                            else:
                                self.T_rvs = 0
                                LMTD[N_element*tt+jj,j] = ((T_primary[N_element*tt+jj-1,j] - T_secondary[N_element*tt+jj,j-1]) - (T_primary[N_element*tt+jj,j] - T_secondary[N_element*tt+jj,j]))\
                                    /np.log((T_primary[N_element*tt+jj-1,j] - T_secondary[N_element*tt+jj,j-1])/(T_primary[N_element*tt+jj,j] - T_secondary[N_element*tt+jj,j]))
        
                                UA_element[N_element*tt+jj,j] = abs((self.primary_in.q/N_element/N_turn/N_row) / LMTD[N_element*tt+jj,j])  
                    else: # 홀수
                        if self.sph == 0:
                            T_secondary[N_element*N_turn-1-N_element*tt-jj,j] = T_secondary[N_element*N_turn-1-N_element*tt-jj,j-1] + self.secondary_in.q/N_row/self.secondary_in.m/0.5/(self.secondary_in.Cp + self.secondary_out.Cp)
                        else:
                            h_secondary[N_element*N_turn-1-N_element*tt-jj,j] = h_secondary[N_element*N_turn-1-N_element*tt-jj,j-1] + self.secondary_in.q/N_row/self.secondary_in.m
                            p_secondary[N_element*N_turn-1-N_element*tt-jj,j] = h_secondary[N_element*N_turn-1-N_element*tt-jj,j-1] - (self.secondary_in.p - self.secondary_out.p)/N_row
                            T_secondary[N_element*N_turn-1-N_element*tt-jj,j] = PropsSI('T','H',h_secondary[N_element*N_turn-1-N_element*tt-jj,j],'P',p_secondary[N_element*N_turn-1-N_element*tt-jj,j], self.secondary_in.fluidmixture)
                        
                        if jj == 0: #Turn 입구
                            if self.pph == 0:
                                T_primary[N_element*N_turn-1-N_element*tt-jj,j] = T_primary_in + (self.primary_in.q/N_element/N_turn/N_row)/self.primary_in.m/0.5/(self.primary_in.Cp + self.primary_out.Cp)
                            else:
                                h_primary[N_element*N_turn-1-N_element*tt-jj,j] = h_primary_in + (self.primary_in.q/N_element/N_turn/N_row)/self.primary_in.m
                                p_primary[N_element*N_turn-1-N_element*tt-jj,j] = p_primary_in - (self.primary_in.p - self.primary_out.p)/N_element/N_turn/N_row
                                T_primary[N_element*N_turn-1-N_element*tt-jj,j] = PropsSI('T','P',p_primary[N_element*N_turn-1-N_element*tt-jj,j],'H',h_primary[N_element*N_turn-1-N_element*tt-jj,j],self.primary_in.fluidmixture)
                            
                            if (T_primary_in - T_secondary[N_element*N_turn-1-N_element*tt-jj,j-1] < 0 and self.primary_in.q < 0) or (T_primary_in - T_secondary[N_element*N_turn-1-N_element*tt-jj,j-1] > 0 and self.primary_in.q > 0):
                                self.T_rvs = 1
                                break
                            else:
                                self.T_rvs = 0
                                LMTD[N_element*N_turn-1-N_element*tt-jj,j] = ((T_primary_in - T_secondary[N_element*N_turn-1-N_element*tt-jj,j-1]) - (T_primary[N_element*N_turn-1-N_element*tt-jj,j] - T_secondary[N_element*N_turn-1-N_element*tt-jj,j]))\
                                    /np.log((T_primary_in - T_secondary[N_element*N_turn-1-N_element*tt-jj,j-1])/(T_primary[N_element*N_turn-1-N_element*tt-jj,j] - T_secondary[N_element*N_turn-1-N_element*tt-jj,j]))
        
                                UA_element[N_element*N_turn-1-N_element*tt-jj,j] = abs((self.primary_in.q/N_element/N_turn/N_row) / LMTD[N_element*N_turn-1-N_element*tt-jj,j])
                        else:
                            if self.pph == 0:
                                T_primary[N_element*N_turn-1-N_element*tt-jj,j] = T_primary[N_element*N_turn-N_element*tt-jj,j] + (self.primary_in.q/N_element/N_turn/N_row)/self.primary_in.m/0.5/(self.primary_in.Cp + self.primary_out.Cp)
                            else:
                                h_primary[N_element*N_turn-1-N_element*tt-jj,j] = h_primary[N_element*N_turn-N_element*tt-jj,j] + (self.primary_in.q/N_element/N_turn/N_row)/self.primary_in.m
                                p_primary[N_element*N_turn-1-N_element*tt-jj,j] = p_primary[N_element*N_turn-N_element*tt-jj,j] - (self.primary_in.p - self.primary_out.p)/N_element/N_turn/N_row
                                T_primary[N_element*N_turn-1-N_element*tt-jj,j] = PropsSI('T','P',p_primary[N_element*N_turn-1-N_element*tt-jj,j],'H',h_primary[N_element*N_turn-1-N_element*tt-jj,j],self.primary_in.fluidmixture)
                            
                            if jj == N_element-1:
                                T_primary_in = T_primary[N_element*N_turn-1-N_element*tt-jj,j]
                                h_primary_in = h_primary[N_element*N_turn-1-N_element*tt-jj,j]
                                p_primary_in = p_primary[N_element*N_turn-1-N_element*tt-jj,j]
                            
                            if (T_primary[N_element*N_turn-N_element*tt-jj,j] - T_secondary[N_element*N_turn-1-N_element*tt-jj,j-1] < 0 and self.primary_in.q < 0) or (T_primary[N_element*N_turn-N_element*tt-jj,j] - T_secondary[N_element*N_turn-1-N_element*tt-jj,j-1] > 0 and self.primary_in.q > 0):
                                self.T_rvs = 1
                                break
                            else:
                                self.T_rvs = 0
                                LMTD[N_element*N_turn-1-N_element*tt-jj,j] = ((T_primary[N_element*N_turn-N_element*tt-jj,j] - T_secondary[N_element*N_turn-1-N_element*tt-jj,j-1]) - (T_primary[N_element*N_turn-1-N_element*tt-jj,j] - T_secondary[N_element*N_turn-1-N_element*tt-jj,j]))\
                                    /np.log((T_primary[N_element*N_turn-N_element*tt-jj,j] - T_secondary[N_element*N_turn-1-N_element*tt-jj,j-1])/(T_primary[N_element*N_turn-1-N_element*tt-jj,j] - T_secondary[N_element*N_turn-1-N_element*tt-jj,j]))
        
                                UA_element[N_element*N_turn-1-N_element*tt-jj,j] = abs((self.primary_in.q/N_element/N_turn/N_row) / LMTD[N_element*N_turn-1-N_element*tt-jj,j])        
        
        self.UA = np.sum(np.sum(UA_element))
        self.T_lm = abs(self.primary_in.q)/self.UA
        
        if np.round(N_row/2) != N_row/2:
            self.primary_out.T = T_primary[-1,N_row-1]
            self.primary_out.h = h_primary[-1,N_row-1]
        else:
            self.primary_out.T = T_primary[0,N_row-1]
            self.primary_out.h = h_primary[0,N_row-1]
        
        T_array = []
        p_array = []
        for i in np.arange(N_row):
            if np.round(i/2) == i/2:
                np.append(T_array, T_primary[N_element-1,i])
                np.append(p_array, p_primary[N_element-1,i])
            else:
                np.append(T_array, T_primary[0,i])
                np.append(p_array, p_primary[0,i])
                        
        return(T_array, p_array)
        
    def PHE(self, N_element: int):
        h_primary = np.zeros(shape=(N_element+1))
        T_primary = np.zeros(shape=(N_element+1))
        p_primary = np.zeros(shape=(N_element+1))
        T_secondary = np.zeros(shape=(N_element+1))
        p_secondary = np.zeros(shape=(N_element+1))
        h_secondary = np.zeros(shape=(N_element+1))
        dT = np.zeros(shape=(N_element+1))
        LMTD = np.zeros(shape=(N_element))
        UA_element = np.zeros(shape=(N_element+1))
        
        p_secondary[0] = self.secondary_out.p
        T_secondary[0] = self.secondary_out.T
        h_secondary[0] = self.secondary_out.h
        
        p_primary[0] = self.primary_in.p
        T_primary[0] = self.primary_in.T
        h_primary[0] = self.primary_in.h
         
        dT[0] = T_primary[0] - T_secondary[0]
        
        if (dT[0] < 0.0 and self.primary_in.q < 0.0) or (dT[0] > 0.0 and self.primary_in.q > 0.0):
            self.T_rvs = 1
        else:
            self.T_rvs = 0
    
        for i in range(N_element):
            if self.T_rvs == 1:
                break
            
            if self.pph == 0:
                T_primary[i+1] = T_primary[i] + self.primary_in.q/N_element/self.primary_in.m/0.5/(self.primary_in.Cp + self.primary_out.Cp)
            else:    
                h_primary[i+1] = h_primary[i] + self.primary_in.q/N_element/self.primary_in.m
                p_primary[i+1] = p_primary[i] - (self.primary_in.p - self.primary_out.p)/N_element
                T_primary[i+1] = PropsSI('T','H',h_primary[i+1],'P',p_primary[i+1],self.primary_in.fluidmixture)
                
            if self.sph == 0:
                T_secondary[i+1] = T_secondary[i] + self.secondary_in.q/N_element/self.secondary_in.m/0.5/(self.secondary_in.Cp + self.secondary_out.Cp)
            else: 
                h_secondary[i+1] = h_secondary[i] + self.secondary_in.q/N_element/self.secondary_in.m
                p_secondary[i+1] = p_secondary[i] + (self.secondary_in.p - self.secondary_out.p)/N_element
                T_secondary[i+1] = PropsSI('T','H',h_secondary[i+1],'P',p_secondary[i+1],self.secondary_in.fluidmixture)
            
            dT[i+1] = T_primary[i+1] - T_secondary[i+1]
            if (dT[i+1] < 0.0 and self.primary_in.q < 0.0) or (dT[i+1] > 0.0 and self.primary_in.q > 0.0):
                self.T_rvs = 1
            else:
                self.T_rvs = 0
                LMTD[i] = ((T_primary[i+1]-T_secondary[i+1]) - (T_primary[i]-T_secondary[i]))\
                            /np.log((T_primary[i+1]-T_secondary[i+1])/(T_primary[i]-T_secondary[i]))
                            
                UA_element[i] = abs((self.primary_in.q/N_element)/LMTD[i])  
      
        self.T_pp = min(abs(dT))
        self.UA = sum(UA_element) 
        self.primary_out.T = T_primary[N_element]
        self.primary_out.h = h_primary[N_element]
        
        T_array = [T_primary[round(N_element/6)], T_primary[round(N_element/3)], T_primary[round(N_element/2)], T_primary[round(N_element*2/3)], T_primary[round(N_element*5/6)]]
        p_array = [p_primary[round(N_element/6)], p_primary[round(N_element/3)], p_primary[round(N_element/2)], p_primary[round(N_element*2/3)], p_primary[round(N_element*5/6)]]
        return(T_array, p_array)
        
    def SIMPHX(self, eff_HX:float):
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
        
        