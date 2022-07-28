import copy
import numpy as np
from CoolProp.CoolProp import PropsSI
# test 용 import
from STED_types import WireObjectFluid

class Compander_module:
    
    def __init__(self, primary_in, primary_out):
        self.primary_in = primary_in
        self.primary_out = primary_out
    
    def COMP(self, eff_isen: float = 0.7, eff_mech: float = 1.0, cycle_index: str='vcc'):    
        while 1:
            h_comp_out_isen = PropsSI('H','P',self.primary_out.p,'S',self.primary_in.s,self.primary_in.fluidmixture)
            self.primary_out.h = (h_comp_out_isen - self.primary_in.h)/eff_isen + self.primary_in.h
            self.primary_out.T = PropsSI('T','H',self.primary_out.h,'P',self.primary_out.p,self.primary_in.fluidmixture)
            
            if cycle_index == 'scc':
                break
            else:
                T_comp_out_sat = PropsSI('T','P',self.primary_out.p,'Q',1.0,self.primary_in.fluidmixture)
                if (self.primary_out.T - T_comp_out_sat) > 0.01: # Overhanging problem protection
                    break
                    
            
        self.Pspecific = (self.primary_out.h - self.primary_in.h)/eff_mech
            
    def EXPAND(self, eff_isen: float = 0.8, eff_mech: float = 1.0):
        h_expand_out_isen = PropsSI('H','P',self.primary_out.p,'S', self.primary_in.s, self.primary_in.fluidmixture)
        self.primary_out.h = self.primary_in.h - (self.primary_in.h - h_expand_out_isen)*eff_isen
        self.primary_out.T = PropsSI('T','H',self.primary_out.h,'P',self.primary_out.p,self.primary_in.fluidmixture)
        
        self.Pspecific = (self.primary_in.h - self.primary_out.h)*eff_mech
        

if __name__ == "__main__":
    '''
    # Compressor input
    comp_in = WireObjectFluid({'R134A':1})
    comp_in.p = 301300
    comp_in.T = PropsSI('T','P',comp_in.p,'Q',1.0, comp_in.fluidmixture)+5.0
    comp_in.h = PropsSI('H','T',comp_in.T,'P',comp_in.p,comp_in.fluidmixture)
    comp_in.s = PropsSI('S','T',comp_in.T,'P',comp_in.p,comp_in.fluidmixture)
    comp_out = copy.deepcopy(comp_in)
    comp_out.p = 301300*3
    
    compressor = Compander_module(comp_in, comp_out)
    compressor.COMP(0.7)
    print(compressor.Pspecific)
    '''
    # Expander input
    expand_in = WireObjectFluid({'R134A':1})
    expand_in.p = 501300
    expand_in.T = PropsSI('T','P',expand_in.p,'Q',1.0, expand_in.fluidmixture)+30.0
    expand_in.h = PropsSI('H','T',expand_in.T,'P',expand_in.p,expand_in.fluidmixture)
    expand_in.s = PropsSI('S','T',expand_in.T,'P',expand_in.p,expand_in.fluidmixture)
    expand_out = copy.deepcopy(expand_in)
    expand_out.p = expand_in.p/3
    
    expander = Compander_module(expand_in, expand_out)
    expander.EXPAND(0.0)
    print(expander.Pspecific)
    