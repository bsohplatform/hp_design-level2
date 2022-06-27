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
        
        def __init__(self):
            self.x_cond_ref = np.ones(shape=(self.setting.N_element_cond+1, self.setting.N_row_cond+1))
            self.h_cond_ref = np.zeors(shape=(self.setting.N_element_cond+1, self.setting.N_row_cond+1))
            self.T_cond_ref = copy.deepcopy(self.h_cond_ref)
            self.P_cond_ref = copy.deepcopy(self.h_cond_ref)
            self.T_cond_sec = copy.deepcopy(self.h_cond_ref)
            self.P_cond_sec = copy.deepcopy(self.h_cond_ref)
            self.h_cond_sec = copy.deepcopy(self.h_cond_ref)
            self.LMTD_cond = np.zeros(shape=(self.setting.N_element_cond, self.setting.N_row_cond))
            self.cond_UA_cond_element = copy.deepcopy(self.LMTD_cond)
            
        