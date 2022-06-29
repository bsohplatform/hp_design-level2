import copy
from dataclasses import dataclass
import numpy as np
from CoolProp.CoolProp import PropsSI
# test 용 import
from STED_types import WireObjectFluid



class Condensor_module:
    
    def __init__(self, primary_in, primary_out, second_in, second_out, setting):
        self.primary_in = primary_in
        self.primary_out = primary_out
        self.second_in = second_in
        self.second_out = second_out
        self.setting = setting
        
    def Condensor_FTHE(self):
        
        self.x_cond_ref = np.ones(shape=(self.setting.cond_N_element+1, self.setting.cond_N_row+1))
        self.h_cond_ref = np.zeros(shape=(self.setting.cond_N_element+1, self.setting.cond_N_row+1))
        self.T_cond_ref = copy.deepcopy(self.h_cond_ref)
        self.P_cond_ref = copy.deepcopy(self.h_cond_ref)
        self.T_cond_sec = copy.deepcopy(self.h_cond_ref)
        self.P_cond_sec = copy.deepcopy(self.h_cond_ref)
        self.h_cond_sec = copy.deepcopy(self.h_cond_ref)
        self.LMTD_cond = np.zeros(shape=(self.setting.cond_N_element, self.setting.cond_N_row))
        self.cond_UA_cond_element = copy.deepcopy(self.LMTD_cond)
        
        self.P_cond_sec[:,0] = self.second_out.p
        self.T_cond_sec[:,0] = self.second_out.T
        self.h_cond_sec[:,0] = self.second_out.h
        
        self.P_cond_ref[0,0] = self.primary_out.p
        self.T_cond_ref[0,0] = self.primary_out.T
        self.h_cond_ref[0,0] = self.primary_out.h
        
        if self.P_cond_ref[0,0] < self.setting.P_crit:
            self.h_cond_refl = PropsSI('H','P',self.P_cond_ref[0,0],'Q',0.0,self.primary_in.Y[self.primary_in.refrigerant])
            self.h_cond_refg = PropsSI('H','P',self.P_cond_ref[0,0],'Q',1.0,self.primary_in.fluid)
            self.x_cond_ref[0,0] = (self.h_cond_ref[0,0]-self.h_cond_refl)/(self.h_cond_refg-self.h_cond_refl)
        
        for j in range(self.setting.cond_N_row-1):
            for jj in range(self.setting.cond_N_row-1):
                if round(j/2) == j/2: # 짝수
                    self.h_cond_ref[jj+1,j] = self.h_cond_ref[jj,j] - (self.heat.cond/self.setting.cond_N_element/self.setting.cond_N_row)/self.primary_in.mdot
                    self.P_cond_ref[jj+1,j] = self.P_cond_ref[jj,j] - (self.primary_in.P - self.primary.cond_P_out)/self.setting.cond_N_element/self.setting.cond_N_row
                    self.T_cond_ref[jj+1,j] = PropsSI('T','P',self.P_cond_ref,'H',self.h_cond_ref,self.primary.fluid)
                    
                    if self.P_cond_ref[jj+1,j] < self.primary.P_crit:
                        self.h_cond_refl = PropsSI('H','P',self.P_cond_ref[jj+1,j],'Q',0.0,self.primary.fluid)
                        self.h_cond_refg = PropsSI('H','P',self.P_cond_ref[jj+1,j],'Q',1.0,self.primary.fluid)
                        self.x_cond_ref[0,0] = (self.h_cond_ref[jj+1,j]-self.h_cond_refl)/(self.h_cond_refg-self.h_cond_refl)
                        
                    self.h_cond_sec[jj,j+1] = self.h_cond_sec[jj,j] - self.heat.cond/self.setting.cond_N_row/self.second.mdot
                    self.P_cond_sec[jj,j+1] = self.P_cond_sec[jj,j] + (self.second.cond_P_in - self.second.cond_P_out)/self.setting.cond_N_row
                    self.T_cond_sec[jj,j+1] = PropsSI('T','H',self.h_cond_sec[jj,j+1],'P',self.P_cond_sec[jj,j+1],self.second.fluid)
                    
                    if self.T_cond_ref[jj+1,j] - self.T_cond_sec[jj,j+1] < 0:
                        self.primary.cond_T_rvs = 1
                        break
                    else:
                        self.primary.cond_T_rvs = 0
                        self.LMTD_cond[jj,j] = ((self.T_cond_ref[jj+1,j]-self.T_cond_sec[jj,j+1]) - (self.T_cond_ref[jj,j]-self.T_cond_sec[jj,j]))\
                            /np.log((self.T_cond_ref[jj+1,j]-self.T_cond_sec[jj,j+1]) - (self.T_cond_ref[jj,j]-self.T_cond_sec[jj,j]))
                        self.cond_UA_cond_element[jj,j] = (self.heat.cond/self.setting.cond_N_element/self.setting.cond_N_row) / self.LMTD_cond[jj,j]
                        
                        if jj == self.setting.cond_N_element:
                            self.h_cond_ref[self.setting.cond_N_element,j+1] = self.h_cond_ref[self.setting.cond_N_element,j]
                            self.T_cond_ref[self.setting.cond_N_element,j+1] = self.T_cond_ref[self.setting.cond_N_element,j]
                            self.P_cond_ref[self.setting.cond_N_element,j+1] = self.P_cond_ref[self.setting.cond_N_element,j]
                            self.x_cond_ref[self.setting.cond_N_element,j+1] = self.x_cond_ref[self.setting.cond_N_element,j]
                            
                else: # 홀수
                    self.h_cond_ref[self.setting.cond_N_element-jj-1,j] = self.h_cond_ref[self.setting.cond_N_element-jj,j] - (self.heat.cond/self.setting.cond_N_element/self.setting.cond_N_row)/self.primary.mdot
                    self.P_cond_ref[self.setting.cond_N_element-jj-1,j] = self.P_cond_ref[self.setting.cond_N_element-jj,j] - (self.primary.cond_P_in - self.primary.cond_P_out)/self.setting.cond_N_element/self.setting.cond_N_row
                    self.T_cond_ref[self.setting.cond_N_element-jj-1,j] = PropsSI('T','P',self.P_cond_ref[self.setting.cond_N_element-jj-1,j],'H',self.h_cond_ref[self.setting.cond_N_element-jj-1,j],self.primary.fluid)
                    
                    if self.P_cond_ref[self.setting.cond_N_element-jj-1,j] < self.primary.P_crit:
                        self.h_cond_refl = PropsSI('H','P',self.P_cond_ref[self.setting.cond_N_element-jj-1,j],'Q',0.0,self.primary.fluid)
                        self.h_cond_refg = PropsSI('H','P',self.P_cond_ref[self.setting.cond_N_element-jj-1,j],'Q',1.0,self.primary.fluid)
                        self.x_cond_ref[self.setting.cond_N_element-jj-1,j] = (self.h_cond_ref[self.setting.cond_N_element-jj-1,j]-self.h_cond_refl)/(self.h_cond_refg-self.h_cond_refl)
                        
                    self.h_cond_sec[self.setting.cond_N_element-jj-1,j+1] = self.h_cond_sec[self.setting.cond_N_element-jj-1,j] - self.heat.cond/self.setting.cond_N_row/self.second.mdot
                    self.P_cond_sec[self.setting.cond_N_element-jj-1,j+1] = self.P_cond_sec[self.setting.cond_N_element-jj-1,j] + (self.second.cond_P_in - self.second.cond_P_out)/self.setting.cond_N_row
                    self.T_cond_sec[self.setting.cond_N_element-jj-1,j+1] = PropsSI('T','H',self.h_cond_sec[self.setting.cond_N_element-jj-1,j+1],'P',self.P_cond_sec[self.setting.cond_N_element-jj-1,j+1],self.second.fluid)
                    
                    if self.T_cond_ref[self.setting.cond_N_element-jj-1,j] - self.T_cond_sec[self.setting.cond_N_element-jj-1,j+1] < 0:
                        self.primary.cond_T_rvs = 1
                        break
                    else:
                        self.primary.cond_T_rvs = 0
                        self.LMTD_cond[self.setting.cond_N_element-jj-1,j] = ((self.T_cond_ref[self.setting.cond_N_element-jj-1,j]-self.T_cond_sec[self.setting.cond_N_element-jj-1,j+1]) - (self.T_cond_ref[self.setting.cond_N_element-jj,j]-self.T_cond_sec[self.setting.cond_N_element-jj-1,j]))\
                            /np.log((self.T_cond_ref[self.setting.cond_N_element-jj-1,j]-self.T_cond_sec[self.setting.cond_N_element-jj-1,j+1]) - (self.T_cond_ref[self.setting.cond_N_element-jj,j]-self.T_cond_sec[self.setting.cond_N_element-jj-1,j]))
                        self.cond_UA_cond_element[self.setting.cond_N_element-jj-1,j] = (self.heat.cond/self.setting.cond_N_element/self.setting.cond_N_row) / self.LMTD_cond[self.setting.cond_N_element-jj-1,j]
                        
                        if jj == self.setting.cond_N_element:
                            self.h_cond_ref[0,j+1] = self.h_cond_ref[0,j]
                            self.T_cond_ref[0,j+1] = self.T_cond_ref[0,j]
                            self.P_cond_ref[0,j+1] = self.P_cond_ref[0,j]
                            self.x_cond_ref[0,j+1] = self.x_cond_ref[0,j]
                
                if self.primary.cond_T_rvs == 1:
                    break
        self.primary.cond_UA = np.sum(np.sum(self.cond_UA_cond_element))
        self.cond_T_lm = self.heat.cond/self.primary.cond_UA
        if np.round(self.setting.cond_N_row/2) != self.setting.cond_N_row/2: # 짝수
            self.primary.cond_T_out = self.T_cond_ref[self.setting.cond_N_element,self.setting.cond_N_row-1]
            self.primary.cond_h_out = self.h_cond_ref[self.setting.cond_N_element,self.setting.cond_N_row-1]
            self.primary.cond_x_out = self.x_cond_ref[self.setting.cond_N_element,self.setting.cond_N_row-1]
        else: # 홀수
            self.primary.cond_T_out = self.T_cond_ref[0,self.setting.cond_N_row-1]
            self.primary.cond_h_out = self.h_cond_ref[0,self.setting.cond_N_row-1]
            self.primary.cond_x_out = self.x_cond_ref[0,self.setting.cond_N_row-1]


if __name__ == "__main__":
    Second = WireObjectFluid{"H2O": 1.0, }
    cond_basic = Condensor_module()
        