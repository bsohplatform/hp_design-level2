import copy
import numpy as np
from CoolProp.CoolProp import PropsSI

class COND:
    
    def __init__(self, primary, second, heat, setting):
        self.primary = primary
        self.second = second
        self.heat = heat
        self.setting = setting
        
    def Condensor_FTHE(self):
        
        self.x_cond_ref = np.ones(shape=(self.setting.N_element_cond+1, self.setting.N_row_cond+1))
        self.h_cond_ref = np.zeors(shape=(self.setting.N_element_cond+1, self.setting.N_row_cond+1))
        self.T_cond_ref = copy.deepcopy(self.h_cond_ref)
        self.P_cond_ref = copy.deepcopy(self.h_cond_ref)
        self.T_cond_sec = copy.deepcopy(self.h_cond_ref)
        self.P_cond_sec = copy.deepcopy(self.h_cond_ref)
        self.h_cond_sec = copy.deepcopy(self.h_cond_ref)
        self.LMTD_cond = np.zeros(shape=(self.setting.N_element_cond, self.setting.N_row_cond))
        self.cond_UA_cond_element = copy.deepcopy(self.LMTD_cond)
        
        self.P_cond_sec[:,0] = self.second.cond_P_out
        self.T_cond_sec[:,0] = self.second.cond_T_out
        self.h_cond_sec[:,0] = self.second.cond_h_out
        
        self.P_cond_ref[0,0] = self.primary.cond_P_out
        self.T_cond_ref[0,0] = self.primary.cond_T_out
        self.h_cond_ref[0,0] = self.primary.cond_h_out
        
        if self.P_cond_ref[0,0] < self.primary.P_crit:
            self.h_cond_refl = PropsSI('H','P',self.P_cond_ref[0,0],'Q',0.0,self.primary.fluid)
            self.h_cond_refg = PropsSI('H','P',self.P_cond_ref[0,0],'Q',1.0,self.primary.fluid)
            self.x_cond_ref[0,0] = (self.h_cond_ref[0,0]-self.h_cond_refl)/(self.h_cond_refg-self.h_cond_refl)
        
        for j in self.setting.N_row_cond:
            for jj in self.setting.N_row_cond:
                if round(j/2) == j/2: # 짝수
                    self.h_cond_ref[jj+1,j] = self.h_cond_ref[jj,j] - (self.heat.cond/self.setting.N_element_cond/self.setting.N_row_cond)/self.primary.mdot
                    self.P_cond_ref[jj+1,j] = self.P_cond_ref[jj,j] - (self.primary.cond_P_in - self.primary.cond_P_out)/self.setting.N_element_cond/self.setting.N_row_cond
                    self.T_cond_ref[jj+1,j] = PropsSI('T','P',self.P_cond_ref,'H',self.h_cond_ref,self.primary.fluid)
                    
                    if self.P_cond_ref[jj+1,j] < self.primary.P_crit:
                        self.h_cond_refl = PropsSI('H','P',self.P_cond_ref[jj+1,j],'Q',0.0,self.primary.fluid)
                        self.h_cond_refg = PropsSI('H','P',self.P_cond_ref[jj+1,j],'Q',1.0,self.primary.fluid)
                        self.x_cond_ref[0,0] = (self.h_cond_ref[jj+1,j]-self.h_cond_refl)/(self.h_cond_refg-self.h_cond_refl)
                        
                    self.h_cond_sec[jj,j+1] = self.h_cond_sec[jj,j] - self.heat.cond/self.setting.N_row_cond/self.second.mdot
                    self.P_cond_sec[jj,j+1] = self.P_cond_sec[jj,j] + (self.second.cond_P_in - self.second.cond_P_out)/self.setting.N_row_cond
                    self.T_cond_sec[jj,j+1] = PropsSI('T','H',self.h_cond_sec[jj,j+1],'P',self.P_cond_sec[jj,j+1],self.second.fluid)
                    
                    if self.T_cond_ref[jj+1,j] - self.T_cond_sec[jj,j+1] < 0:
                        self.primary.cond_T_rvs = 1
                        break
                    else:
                        self.primary.cond_T_rvs = 0
                        self.LMTD_cond[jj,j] = ((self.T_cond_ref[jj+1,j]-self.T_cond_sec[jj,j+1]) - (self.T_cond_ref[jj,j]-self.T_cond_sec[jj,j]))\
                            /np.log((self.T_cond_ref[jj+1,j]-self.T_cond_sec[jj,j+1]) - (self.T_cond_ref[jj,j]-self.T_cond_sec[jj,j]))
                        self.cond_UA_cond_element[jj,j] = (self.heat.cond/self.setting.N_element_cond/self.setting.N_row_cond) / self.LMTD_cond[jj,j]
                        
                        if jj == self.setting.N_element_cond:
                            self.h_cond_ref[self.setting.N_element_cond+1,j] = self.h_cond_ref[self.setting.N_element_cond+1,j]
                            self.T_cond_ref[self.setting.N_element_cond+1,j] = self.T_cond_ref[self.setting.N_element_cond+1,j]
                            self.P_cond_ref[self.setting.N_element_cond+1,j] = self.P_cond_ref[self.setting.N_element_cond+1,j]
                            self.x_cond_ref[self.setting.N_element_cond+1,j] = self.x_cond_ref[self.setting.N_element_cond+1,j]
                            
                else: # 홀수
                    self.h_cond_ref[self.setting.N_element_cond+1-jj,j] = self.h_cond_ref[jj,j] - (self.heat.cond/self.setting.N_element_cond/self.setting.N_row_cond)/self.primary.mdot
                    self.P_cond_ref[self.setting.N_element_cond+1-jj,j] = self.P_cond_ref[jj,j] - (self.primary.cond_P_in - self.primary.cond_P_out)/self.setting.N_element_cond/self.setting.N_row_cond
                    self.T_cond_ref[self.setting.N_element_cond+1-jj,j] = PropsSI('T','P',self.P_cond_ref,'H',self.h_cond_ref,self.primary.fluid)
                    
                    if self.P_cond_ref[self.setting.N_element_cond+1-jj,j] < self.primary.P_crit:
                        self.h_cond_refl = PropsSI('H','P',self.P_cond_ref[self.setting.N_element_cond+1-jj,j],'Q',0.0,self.primary.fluid)
                        self.h_cond_refg = PropsSI('H','P',self.P_cond_ref[self.setting.N_element_cond+1-jj,j],'Q',1.0,self.primary.fluid)
                        self.x_cond_ref[0,0] = (self.h_cond_ref[self.setting.N_element_cond+1-jj,j]-self.h_cond_refl)/(self.h_cond_refg-self.h_cond_refl)
                        
                    self.h_cond_sec[jj,j] = self.h_cond_sec[jj,j] - self.heat.cond/self.setting.N_row_cond/self.second.mdot
                    self.P_cond_sec[jj,j] = self.P_cond_sec[jj,j] + (self.second.cond_P_in - self.second.cond_P_out)/self.setting.N_row_cond
                    self.T_cond_sec[jj,j] = PropsSI('T','H',self.h_cond_sec[jj,j],'P',self.P_cond_sec[jj,j],self.second.fluid)
                    
                    if self.T_cond_ref[self.setting.N_element_cond+1-jj,j] - self.T_cond_sec[jj,j] < 0:
                        self.primary.cond_T_rvs = 1
                        break
                    else:
                        self.primary.cond_T_rvs = 0
                        self.LMTD_cond[jj,j] = ((self.T_cond_ref[self.setting.N_element_cond+1-jj,j]-self.T_cond_sec[jj,j+1]) - (self.T_cond_ref[jj,j]-self.T_cond_sec[jj,j]))\
                            /np.log((self.T_cond_ref[self.setting.N_element_cond+1-jj,j]-self.T_cond_sec[jj,j+1]) - (self.T_cond_ref[jj,j]-self.T_cond_sec[jj,j]))
                        self.cond_UA_cond_element[jj,j] = (self.heat.cond/self.setting.N_element_cond/self.setting.N_row_cond) / self.LMTD_cond[jj,j]
                        
                        if jj == self.setting.N_element_cond:
                            self.h_cond_ref[self.setting.N_element_cond+1,j+1] = self.h_cond_ref[self.setting.N_element_cond+1,j]
                            self.T_cond_ref[self.setting.N_element_cond+1,j+1] = self.T_cond_ref[self.setting.N_element_cond+1,j]
                            self.P_cond_ref[self.setting.N_element_cond+1,j+1] = self.P_cond_ref[self.setting.N_element_cond+1,j]
                            self.x_cond_ref[self.setting.N_element_cond+1,j+1] = self.x_cond_ref[self.setting.N_element_cond+1,j]