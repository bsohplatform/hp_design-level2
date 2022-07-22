import copy
import numpy as np
from CoolProp.CoolProp import PropsSI
# test 용 import
from STED_types import WireObjectFluid, Settings

class Preprocess_module:
    def __init__(self, InCond, OutCond, InEvap, OutEvap, inputs):
        self.InCond = InCond
        self.OutCond = OutCond
        self.InEvap = InEvap
        self.OutEvap = OutEvap
        self.inputs = inputs
        if self.inputs.second == 'steam':
            self.Steam_module()
        elif self.inputs.second == 'hotwater':
            self.Hotwater_module()
        else:
            print('일반공정')
        
    
    def Steam_module(self):
        p_flash = PropsSI('P','T',self.inputs.T_steam,'Q',1.0, self.InCond.fluidmixture)
        self.OutCond.p = PropsSI('P','T',self.OutCond.T+0.1, 'Q', 0.0, self.InCond.fluidmixture)
        self.OutCond.h = PropsSI('H','T',self.OutCond.T+0.1, 'Q', 0.0, self.InCond.fluidmixture)
        X_flash = PropsSI('Q','H',self.OutCond.h,'P',p_flash, self.InCond.fluidmixture)
        self.OutCond.m = self.inputs.m_steam / X_flash
        self.InCond.m = self.OutCond.m
        m_sat_liq = (1-X_flash)*self.OutCond.m
        h_sat_liq = PropsSI('H','P',p_flash,'Q',0.0, self.InCond.fluidmixture)
        h_makeup = PropsSI('H','T',self.inputs.T_makeup,'P',p_flash, self.InCond.fluidmixture)
        
        self.InCond.h = (m_sat_liq*h_sat_liq + self.inputs.m_makeup*h_makeup)/self.OutCond.m
        self.InCond.T = PropsSI('T','H',self.InCond.h,'P',p_flash, self.InCond.fluidmixture)
        
    def Hotwater_module(self):
        rho_water = PropsSI('D','T',0.5*(self.inputs.T_makeup+self.inputs.T_target),'P',101300, self.InCond.fluidmixture)
        self.V_tank = self.inputs.M_load/rho_water
        
        h_target = PropsSI('H','T',self.inputs.T_target,'P',101300.0,self.InCond.fluidmixture)
        h_makeup = PropsSI('H','T',self.inputs.T_makeup,'P',101300.0,self.InCond.fluidmixture)
        self.InCond.h = 0.5*(h_target + h_makeup)
        self.InCond.T = PropsSI('T','H',self.InCond.h,'P',101300, self.InCond.fluidmixture)
        Cp_water = PropsSI('C','T',self.InCond.T,'P',101300, self.InCond.fluidmixture)
        self.OutCond.q = 0.5*self.inputs.M_load*Cp_water*(self.inputs.T_target - self.InCond.T)/self.inputs.time_target
        self.OutCond.m = self.OutCond.q/(Cp_water*self.inputs.dT_lift)
        self.OutCond.T = self.InCond.T + self.inputs.dT_lift


if __name__ == "__main__":
    inputs = Settings(second='hotwater')
    OutCond = WireObjectFluid(Y={'water': 1.0},T=430, p=1.0e5)
    Preprocess = Preprocess_module(OutCond, OutCond, OutCond, OutCond, inputs)
    print(OutCond.T)
    print(Preprocess.V_tank)