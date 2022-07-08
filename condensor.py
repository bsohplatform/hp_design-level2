import copy
from dataclasses import dataclass
import numpy as np
from CoolProp.CoolProp import PropsSI
# test 용 import
from STED_types import WireObjectFluid, Settings, Errormsg



class Condensor_module:
        
    def __init__(self, primary_in, primary_out, second_in, second_out, setting, errmsg):
        self.primary_in = primary_in
        self.primary_out = primary_out
        self.second_in = second_in
        self.second_out = second_out
        self.setting = setting
        self.errmsg = errmsg

        
        
    def Condensor_FTHE(self):
        
        x_cond_ref = np.ones(shape=(self.setting.cond_N_element+1, self.setting.cond_N_row+1))
        h_cond_ref = np.zeros(shape=(self.setting.cond_N_element+1, self.setting.cond_N_row+1))
        T_cond_ref = copy.deepcopy(h_cond_ref)
        P_cond_ref = copy.deepcopy(h_cond_ref)
        T_cond_sec = copy.deepcopy(h_cond_ref)
        P_cond_sec = copy.deepcopy(h_cond_ref)
        h_cond_sec = copy.deepcopy(h_cond_ref)
        LMTD_cond = np.zeros(shape=(self.setting.cond_N_element, setting.cond_N_row))
        cond_UA_cond_element = copy.deepcopy(LMTD_cond)
        
        P_cond_sec[:,0] = self.second_out.p
        T_cond_sec[:,0] = self.second_out.T
        h_cond_sec[:,0] = self.second_out.h
        
        P_cond_ref[0,0] = self.primary_out.p
        T_cond_ref[0,0] = self.primary_out.T
        h_cond_ref[0,0] = self.primary_out.h
        
        if P_cond_ref[0,0] < self.primary_in.p_crit:
            h_cond_refl = PropsSI('H','P',P_cond_ref[0,0],'Q',0.0,self.primary_in.fluidmixture)
            h_cond_refg = PropsSI('H','P',P_cond_ref[0,0],'Q',1.0,self.primary_in.fluidmixture)
            x_cond_ref[0,0] = (h_cond_ref[0,0]-h_cond_refl)/(h_cond_refg-h_cond_refl)
        
        for j in range(self.setting.cond_N_row):
            for jj in range(self.setting.cond_N_element):
                if round(j/2) == j/2: # 짝수
                    h_cond_ref[jj+1,j] = h_cond_ref[jj,j] - (self.primary_in.q/self.setting.cond_N_element/self.setting.cond_N_row)/self.primary_in.m
                    P_cond_ref[jj+1,j] = P_cond_ref[jj,j] - (self.primary_in.p - self.primary_out.p)/self.setting.cond_N_element/self.setting.cond_N_row
                    T_cond_ref[jj+1,j] = PropsSI('T','P',P_cond_ref[jj+1,j],'H',h_cond_ref[jj+1,j],self.primary_in.fluidmixture)
                    
                    if P_cond_ref[jj+1,j] < self.primary_in.p_crit:
                        h_cond_refl = PropsSI('H','P',P_cond_ref[jj+1,j],'Q',0.0,self.primary_in.fluidmixture)
                        h_cond_refg = PropsSI('H','P',P_cond_ref[jj+1,j],'Q',1.0,self.primary_in.fluidmixture)
                        x_cond_ref[0,0] = (h_cond_ref[jj+1,j]-h_cond_refl)/(h_cond_refg-h_cond_refl)
                        
                    h_cond_sec[jj,j+1] = h_cond_sec[jj,j] - self.primary_in.q/self.setting.cond_N_row/self.second_in.m
                    P_cond_sec[jj,j+1] = P_cond_sec[jj,j] + (self.second_in.p - self.second_out.p)/self.setting.cond_N_row
                    T_cond_sec[jj,j+1] = PropsSI('T','H',h_cond_sec[jj,j+1],'P',P_cond_sec[jj,j+1],self.second_in.fluidmixture)
                    
                    if T_cond_ref[jj+1,j] - T_cond_sec[jj,j+1] < 0:
                        self.errmsg.cond_T_rvs = 1
                        break
                    else:
                        self.errmsg.cond_T_rvs = 0
                        LMTD_cond[jj,j] = ((T_cond_ref[jj+1,j]-T_cond_sec[jj,j+1]) - (T_cond_ref[jj,j]-T_cond_sec[jj,j]))\
                            /np.log((T_cond_ref[jj+1,j]-T_cond_sec[jj,j+1]) - (T_cond_ref[jj,j]-T_cond_sec[jj,j]))
                        cond_UA_cond_element[jj,j] = (self.primary_in.q/self.setting.cond_N_element/self.setting.cond_N_row) / LMTD_cond[jj,j]
                        
                        if jj == self.setting.cond_N_element-1:
                            h_cond_ref[self.setting.cond_N_element,j+1] = h_cond_ref[self.setting.cond_N_element,j]
                            T_cond_ref[self.setting.cond_N_element,j+1] = T_cond_ref[self.setting.cond_N_element,j]
                            P_cond_ref[self.setting.cond_N_element,j+1] = P_cond_ref[self.setting.cond_N_element,j]
                            x_cond_ref[self.setting.cond_N_element,j+1] = x_cond_ref[self.setting.cond_N_element,j]
                            
                else: # 홀수
                    h_cond_ref[self.setting.cond_N_element-jj-1,j] = h_cond_ref[self.setting.cond_N_element-jj,j] - (self.primary_in.q/self.setting.cond_N_element/self.setting.cond_N_row)/self.primary_in.m
                    P_cond_ref[self.setting.cond_N_element-jj-1,j] = P_cond_ref[self.setting.cond_N_element-jj,j] - (self.primary_in.p - self.primary_out.p)/self.setting.cond_N_element/self.setting.cond_N_row
                    T_cond_ref[self.setting.cond_N_element-jj-1,j] = PropsSI('T','P',P_cond_ref[self.setting.cond_N_element-jj-1,j],'H',h_cond_ref[self.setting.cond_N_element-jj-1,j],self.primary_in.fluidmixture)
                    
                    if P_cond_ref[self.setting.cond_N_element-jj-1,j] < self.primary_in.p_crit:
                        h_cond_refl = PropsSI('H','P',P_cond_ref[self.setting.cond_N_element-jj-1,j],'Q',0.0,self.primary_in.fluidmixture)
                        h_cond_refg = PropsSI('H','P',P_cond_ref[self.setting.cond_N_element-jj-1,j],'Q',1.0,self.primary_in.fluidmixture)
                        x_cond_ref[self.setting.cond_N_element-jj-1,j] = (h_cond_ref[self.setting.cond_N_element-jj-1,j]-h_cond_refl)/(h_cond_refg-h_cond_refl)
                        
                    h_cond_sec[self.setting.cond_N_element-jj-1,j+1] = h_cond_sec[self.setting.cond_N_element-jj-1,j] - self.primary_in.q/self.setting.cond_N_row/self.second_in.m
                    P_cond_sec[self.setting.cond_N_element-jj-1,j+1] = P_cond_sec[self.setting.cond_N_element-jj-1,j] + (self.second_in.p - self.second_in.p)/self.setting.cond_N_row
                    T_cond_sec[self.setting.cond_N_element-jj-1,j+1] = PropsSI('T','H',h_cond_sec[self.setting.cond_N_element-jj-1,j+1],'P',P_cond_sec[self.setting.cond_N_element-jj-1,j+1],self.second_in.fluidmixture)
                    
                    if T_cond_ref[self.setting.cond_N_element-jj-1,j] - T_cond_sec[self.setting.cond_N_element-jj-1,j+1] < 0:
                        self.errmsg.cond_T_rvs = 1
                        break
                    else:
                        self.errmsg.cond_T_rvs = 0
                        LMTD_cond[self.setting.cond_N_element-jj-1,j] = ((T_cond_ref[self.setting.cond_N_element-jj-1,j]-T_cond_sec[self.setting.cond_N_element-jj-1,j+1]) - (T_cond_ref[self.setting.cond_N_element-jj,j]-T_cond_sec[self.setting.cond_N_element-jj-1,j]))\
                            /np.log((T_cond_ref[self.setting.cond_N_element-jj-1,j]-T_cond_sec[self.setting.cond_N_element-jj-1,j+1]) - (T_cond_ref[self.setting.cond_N_element-jj,j]-T_cond_sec[self.setting.cond_N_element-jj-1,j]))
                        cond_UA_cond_element[self.setting.cond_N_element-jj-1,j] = (self.primary_in.q/self.setting.cond_N_element/self.setting.cond_N_row) / LMTD_cond[self.setting.cond_N_element-jj-1,j]
                        
                        if jj == self.setting.cond_N_element-1:
                            h_cond_ref[0,j+1] = h_cond_ref[0,j]
                            T_cond_ref[0,j+1] = T_cond_ref[0,j]
                            P_cond_ref[0,j+1] = P_cond_ref[0,j]
                            x_cond_ref[0,j+1] = x_cond_ref[0,j]
                
                if self.errmsg.cond_T_rvs == 1:
                    break
        self.setting.cond_UA = np.sum(np.sum(cond_UA_cond_element))
        self.setting.cond_T_lm = self.primary_in.q/self.setting.cond_UA
        if np.round(self.setting.cond_N_row/2) != self.setting.cond_N_row/2: # 짝수
            self.primary_out.T = T_cond_ref[self.setting.cond_N_element,self.setting.cond_N_row-1]
            self.primary_out.h = h_cond_ref[self.setting.cond_N_element,self.setting.cond_N_row-1]
            self.primary_out.x = x_cond_ref[self.setting.cond_N_element,self.setting.cond_N_row-1]
        else: # 홀수
            self.primary_out.T = T_cond_ref[0,self.setting.cond_N_row-1]
            self.primary_out.h = h_cond_ref[0,self.setting.cond_N_row-1]
            self.primary_out.x = x_cond_ref[0,self.setting.cond_N_row-1]
            
            
    def Condensor_PHE(self):
        x_cond_ref = np.ones(shape=(self.setting.cond_N_element+1))
        h_cond_ref = np.zeros(shape=(self.setting.cond_N_element+1))
        T_cond_ref = copy.deepcopy(h_cond_ref)
        P_cond_ref = copy.deepcopy(h_cond_ref)
        T_cond_sec = copy.deepcopy(h_cond_ref)
        P_cond_sec = copy.deepcopy(h_cond_ref)
        h_cond_sec = copy.deepcopy(h_cond_ref)
        dT_cond = copy.deepcopy(h_cond_ref)
        LMTD_cond = np.zeros(shape=(self.setting.cond_N_element))
        cond_UA_cond_element = copy.deepcopy(LMTD_cond)
        
        P_cond_sec[0] = self.second_out.p
        T_cond_sec[0] = self.second_out.T
        h_cond_sec[0] = self.second_out.h
        
        P_cond_ref[0] = self.primary_in.p
        T_cond_ref[0] = self.primary_in.T
        h_cond_ref[0] = self.primary_in.h
        
        if P_cond_ref[0] < self.primary_in.p_crit:
            h_cond_refl = PropsSI('H','P',P_cond_ref[0],'Q',0.0,self.primary_in.fluidmixture)
            h_cond_refg = PropsSI('H','P',P_cond_ref[0],'Q',1.0,self.primary_in.fluidmixture)
            x_cond_ref[0] = (h_cond_ref[0]-h_cond_refl)/(h_cond_refg-h_cond_refl)
        
        dT_cond[0] = T_cond_ref[0] - T_cond_sec[0]
        
        if dT_cond[0] < 0.0:
            self.errmsg.cond_T_rvs = 1
        else:
            self.errmsg.cond_T_rvs = 0
    
        for i in range(self.setting.cond_N_element):
            h_cond_ref[i+1] = h_cond_ref[i] - self.primary_in.q/self.setting.cond_N_element/self.primary_in.m
            P_cond_ref[i+1] = P_cond_ref[i] - (self.primary_in.p - self.primary_out.p)/self.setting.cond_N_element
            T_cond_ref[i+1] = PropsSI('T','H',h_cond_ref[i+1],'P',P_cond_ref[i+1],self.primary_in.fluidmixture)
            
            if P_cond_ref[i+1] < self.primary_in.p_crit:
                h_cond_refl = PropsSI('H','P',P_cond_ref[i+1],'Q',0.0,self.primary_in.fluidmixture)
                h_cond_refg = PropsSI('H','P',P_cond_ref[i+1],'Q',1.0,self.primary_in.fluidmixture)
                x_cond_ref[i+1] = (h_cond_ref[i+1]-h_cond_refl)/(h_cond_refg-h_cond_refl)
            
            h_cond_sec[i+1] = h_cond_sec[i] - self.primary_in.q/self.setting.cond_N_row/self.second_in.m
            P_cond_sec[i+1] = P_cond_sec[i] + (self.second_in.p - self.second_out.p)/self.setting.cond_N_row
            T_cond_sec[i+1] = PropsSI('T','H',h_cond_sec[i+1],'P',P_cond_sec[i+1],self.second_in.fluidmixture)
            
            dT_cond[i+1] = T_cond_ref[i+1] - T_cond_sec[i+1]
            if dT_cond[i+1] < 0.0:
                self.errmsg.cond_T_rvs = 1
                break
            else:
                self.errmsg.cond_T_rvs = 0
                LMTD_cond[i] = ((T_cond_ref[i+1]-T_cond_sec[i+1]) - (T_cond_ref[i]-T_cond_sec[i]))\
                            /np.log((T_cond_ref[i+1]-T_cond_sec[i+1]) - (T_cond_ref[i]-T_cond_sec[i]))
                            
                cond_UA_cond_element[i] = (self.primary_in.q/self.setting.cond_N_element/self.setting.cond_N_row) / LMTD_cond[i]    
        
        self.setting.cond_UA = np.sum(cond_UA_cond_element)
        self.setting.cond_T_pp = min(dT_cond)
        self.primary_out.T = T_cond_ref[self.setting.cond_N_element]
        self.primary_out.h = h_cond_ref[self.setting.cond_N_element]
        self.primary_out.x = x_cond_ref[self.setting.cond_N_element]
        
            

if __name__ == "__main__":
        
        second_in = WireObjectFluid({'water':1})
        second_in.T = 370
        second_in.p = 301300
        second_in.m = 1.0
        second_in.h = PropsSI('H','T',second_in.T,'P',second_in.p,second_in.fluidmixture)
        
        second_out = copy.deepcopy(second_in)
        second_out.T = 380
        second_out.p = 301300
        second_out.h = PropsSI('H','T',second_out.T,'P',second_out.p,second_out.fluidmixture)
        
        primary_in = WireObjectFluid({'R134a':1})
        primary_in.q = (second_out.h - second_in.h)*second_in.m
        primary_in.T = 400
        primary_in.p = 5000000
        primary_in.m = 1.0
        primary_in.h = PropsSI('H','T',primary_in.T,'P',primary_in.p,primary_in.fluidmixture)
        
        primary_out = copy.deepcopy(primary_in)
        primary_out.p = 4990000
        
        
        setting = Settings(cond_N_row = 3)
        errmsg = Errormsg()
        cond_basic = Condensor_module(primary_in, primary_out, second_in, second_out, setting, errmsg)
        cond_basic.Condensor_PHE()
        
        print(primary_out.h)