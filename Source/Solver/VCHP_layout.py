from copy import deepcopy
import HX_module as HX
import COMPAND_module as CP
from CoolProp.CoolProp import PropsSI
from CoolProp.HumidAirProp import HAPropsSI
import matplotlib.pyplot as PLT
# test 용 import
from HP_dataclass import ProcessFluid, Settings, Outputs


class VCHP():
    def __init__(self, InCond, OutCond, InEvap, OutEvap, inputs):
        self.InCond = InCond
        self.OutCond = OutCond
        self.InEvap = InEvap
        self.OutEvap = OutEvap
        self.inputs = inputs
        self.amb_P = 101300.0
    
    def __call__(self):
        outputs = Outputs()
        
        InCond_REF = ProcessFluid(Y=self.inputs.Y)
        OutCond_REF = ProcessFluid(Y=self.inputs.Y)
        InEvap_REF = ProcessFluid(Y=self.inputs.Y)
        OutEvap_REF = ProcessFluid(Y=self.inputs.Y)
        
        p_crit = PropsSI('PCRIT','',0,'',0, list(self.inputs.Y.keys())[0])
        T_crit = PropsSI('TCRIT','',0,'',0, list(self.inputs.Y.keys())[0])
        
        InCond_REF.p_crit = p_crit
        OutCond_REF.p_crit = p_crit
        InEvap_REF.p_crit = p_crit
        OutEvap_REF.p_crit = p_crit
        
        InCond_REF.T_crit = T_crit
        OutCond_REF.T_crit = T_crit
        InEvap_REF.T_crit = T_crit
        OutEvap_REF.T_crit = T_crit
        
        (self.InCond, self.OutCond, self.InEvap, self.OutEvap, no_input) = self.Input_Processing(self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.inputs)
        evap_ph = 0
        cond_ph = 0
        if self.inputs.layout == 'inj':
            (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, outputs) = self.Injection_Solver(self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, self.inputs, outputs, no_input, cond_ph, evap_ph)
        elif self.inputs.layout == '2comp':
            (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, outputs) = self.Comp_2stage_Solver(self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, self.inputs, outputs, no_input, cond_ph, evap_ph)
        else:
            (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, outputs) = self.Cycle_Solver(self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, self.inputs, outputs, no_input, cond_ph, evap_ph)
        
        #self.Post_Processing(outputs)
        #self.Plot_diagram(self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, self.inputs, outputs)
        
        return (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, outputs)
        
    def Input_Processing(self, InCond, OutCond, InEvap, OutEvap, inputs):
        no_InCondT = 0
        no_Condm = 0
        no_OutCondT = 0
        no_InEvapT = 0
        no_Evapm = 0
        no_OutEvapT = 0
        
        if inputs.second == 'steam':
            (InCond, OutCond) = self.Steam_module(InCond, OutCond, inputs)
            
        elif inputs.second == 'hotwater':
            (InCond, OutCond) = self.Hotwater_module(InCond, OutCond, inputs)
        
        else: # 일반 공정
            if InCond.p <= 0.0:
                InCond.p = self.amb_P
        
            if OutCond.p <= 0.0:
             OutCond.p = self.amb_P
             
            if InCond.T <= 0.0:
                no_InCondT = 1
        
            if InCond.m <= 0 and OutCond.m <= 0 :
                no_Condm = 1
            else:
                if InCond.m == 0:
                    InCond.m = OutCond.m # shallow copy
                else:
                    OutCond.m = InCond.m 
                
            if OutCond.T <= 0.0:
                no_OutCondT = 1
            
            
        if InEvap.p <= 0.0:
            InEvap.p = self.amb_P
        
        if OutEvap.p <= 0.0:
            OutEvap.p = self.amb_P
        
        
        if InEvap.T <= 0.0:
            no_InEvapT = 1
        
        if InEvap.m <= 0 and OutEvap.m <= 0 :
            no_Evapm = 1
        else:
            if InEvap.m == 0:
                InEvap.m = OutEvap.m
            else:
                OutEvap.m = InEvap.m
                
        if OutEvap.T <= 0.0:
            no_OutEvapT = 1
            
        no_inputs_sum = no_InCondT + no_Condm + no_OutCondT + no_InEvapT + no_Evapm + no_OutEvapT
        
        if no_inputs_sum == 0:
            no_input = 'Overdefine'
            return (InCond, OutCond, InEvap, OutEvap, no_input)
        elif no_inputs_sum > 1:
            no_input = 'Underdefine'
            return (InCond, OutCond, InEvap, OutEvap, no_input)
        else:    
            if no_InCondT == 1:
                if OutCond.fluidmixture == ('air' or 'Air'):
                    OutCond.h = HAPropsSI('H','T',OutCond.T, 'P',OutCond.p, 'W', OutCond.ahum)
                    OutCond.Cp = HAPropsSI('C','T',OutCond.T, 'P',OutCond.p, 'W', OutCond.ahum)
                else:
                    OutCond.h = PropsSI('H','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                    OutCond.Cp = PropsSI('C','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                    
                if InEvap.fluidmixture == ('air' or 'Air') or OutEvap.fluidmixture == ('air' or 'Air'):
                    InEvap.h = HAPropsSI('H','T',InEvap.T, 'P',InEvap.p, 'W',InEvap.ahum)
                    InEvap.Cp = HAPropsSI('C','T',InEvap.T, 'P',InEvap.p, 'W',InEvap.ahum)
                    OutEvap.h = HAPropsSI('H','T',OutEvap.T, 'P',OutEvap.p, 'W',OutEvap.ahum)
                    OutEvap.Cp = HAPropsSI('C','T',OutEvap.T, 'P',OutEvap.p, 'W',OutEvap.ahum)
                else:
                    InEvap.h = PropsSI('H','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                    InEvap.Cp = PropsSI('C','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                    OutEvap.h = PropsSI('H','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                    OutEvap.Cp = PropsSI('C','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                InEvap.q = (OutEvap.h - InEvap.h)*InEvap.m
                OutEvap.q = InEvap.q 
                no_input = 'InCondT'
            elif no_OutCondT == 1:
                if InCond.fluidmixture == ('air' or 'Air'):
                    InCond.h = HAPropsSI('H','T',InCond.T, 'P',InCond.p, 'W', InCond.ahum)
                    InCond.Cp = HAPropsSI('C','T',InCond.T, 'P',InCond.p, 'W', InCond.ahum)
                else:    
                    InCond.h = PropsSI('H','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                    InCond.Cp = PropsSI('C','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                if InEvap.fluidmixture == ('air' or 'Air') or OutEvap.fluidmixture == ('air' or 'Air'):
                    InEvap.h = HAPropsSI('H','T',InEvap.T, 'P',InEvap.p, 'W',InEvap.ahum)
                    InEvap.Cp = HAPropsSI('C','T',InEvap.T, 'P',InEvap.p, 'W',InEvap.ahum)
                    OutEvap.h = HAPropsSI('H','T',OutEvap.T, 'P',OutEvap.p, 'W',OutEvap.ahum)
                    OutEvap.Cp = HAPropsSI('C','T',OutEvap.T, 'P',OutEvap.p, 'W',OutEvap.ahum)
                else:
                    InEvap.h = PropsSI('H','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                    InEvap.Cp = PropsSI('C','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                    OutEvap.h = PropsSI('H','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                    OutEvap.Cp = PropsSI('C','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                InEvap.q = (OutEvap.h - InEvap.h)*InEvap.m
                OutEvap.q = InEvap.q 
                no_input = 'OutCondT'
            elif no_Condm == 1:
                if InCond.fluidmixture == ('air' or 'Air') or OutCond.fluidmixture == ('air' or 'Air'):
                    InCond.h = HAPropsSI('H','T',InCond.T, 'P',InCond.p, 'W', InCond.ahum)
                    InCond.Cp = HAPropsSI('C','T',InCond.T, 'P',InCond.p, 'W', InCond.ahum)
                    OutCond.h = HAPropsSI('H','T',OutCond.T, 'P',OutCond.p, 'W', OutCond.ahum)
                    OutCond.Cp = HAPropsSI('C','T',OutCond.T, 'P',OutCond.p, 'W', OutCond.ahum)
                else:
                    InCond.h = PropsSI('H','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                    InCond.Cp = PropsSI('C','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                    OutCond.h = PropsSI('H','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                    OutCond.Cp = PropsSI('C','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                if InEvap.fluidmixture == ('air' or 'Air') or OutEvap.fluidmixture == ('air' or 'Air'):
                    InEvap.h = HAPropsSI('H','T',InEvap.T, 'P',InEvap.p, 'W',InEvap.ahum)
                    InEvap.Cp = HAPropsSI('C','T',InEvap.T, 'P',InEvap.p, 'W',InEvap.ahum)
                    OutEvap.h = HAPropsSI('H','T',OutEvap.T, 'P',OutEvap.p, 'W',OutEvap.ahum)
                    OutEvap.Cp = HAPropsSI('C','T',OutEvap.T, 'P',OutEvap.p, 'W',OutEvap.ahum)
                else:    
                    InEvap.h = PropsSI('H','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                    InEvap.Cp = PropsSI('C','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                    OutEvap.h = PropsSI('H','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                    OutEvap.Cp = PropsSI('C','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                InEvap.q = (OutEvap.h - InEvap.h)*InEvap.m
                OutEvap.q = InEvap.q 
                no_input = 'Condm'
            elif no_InEvapT == 1:
                if InCond.fluidmixture == ('air' or 'Air') or OutCond.fluidmixture == ('air' or 'Air'):
                    InCond.h = HAPropsSI('H','T',InCond.T, 'P',InCond.p, 'W', InCond.ahum)
                    InCond.Cp = HAPropsSI('C','T',InCond.T, 'P',InCond.p, 'W', InCond.ahum)
                    OutCond.h = HAPropsSI('H','T',OutCond.T, 'P',OutCond.p, 'W', OutCond.ahum)
                    OutCond.Cp = HAPropsSI('C','T',OutCond.T, 'P',OutCond.p, 'W', OutCond.ahum)
                else:
                    InCond.h = PropsSI('H','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                    InCond.Cp = PropsSI('C','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                    OutCond.h = PropsSI('H','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                    OutCond.Cp = PropsSI('C','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                if OutEvap.fluidmixture == ('air' or 'Air'):
                    OutEvap.h = HAPropsSI('H','T',OutEvap.T, 'P',OutEvap.p, 'W',OutEvap.ahum)
                    OutEvap.Cp = HAPropsSI('C','T',OutEvap.T, 'P',OutEvap.p, 'W',OutEvap.ahum)
                else:
                    OutEvap.h = PropsSI('H','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                    OutEvap.Cp = PropsSI('C','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                InCond.q = (OutCond.h - InCond.h)*InCond.m
                OutCond.q = InCond.q
                no_input = 'InEvapT'
            elif no_OutEvapT == 1:
                if InCond.fluidmixture == ('air' or 'Air') or OutCond.fluidmixture == ('air' or 'Air'):
                    InCond.h = HAPropsSI('H','T',InCond.T, 'P',InCond.p, 'W', InCond.ahum)
                    InCond.Cp = HAPropsSI('C','T',InCond.T, 'P',InCond.p, 'W', InCond.ahum)
                    OutCond.h = HAPropsSI('H','T',OutCond.T, 'P',OutCond.p, 'W', OutCond.ahum)
                    OutCond.Cp = HAPropsSI('C','T',OutCond.T, 'P',OutCond.p, 'W', OutCond.ahum)
                else:    
                    InCond.h = PropsSI('H','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                    InCond.Cp = PropsSI('C','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                    OutCond.h = PropsSI('H','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                    OutCond.Cp = PropsSI('C','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                if InEvap.fluidmixture == ('air' or 'Air'):
                    InEvap.h = HAPropsSI('H','T',InEvap.T, 'P',InEvap.p, 'W',InEvap.ahum)
                    InEvap.Cp = HAPropsSI('C','T',InEvap.T, 'P',InEvap.p, 'W',InEvap.ahum)
                else:    
                    InEvap.h = PropsSI('H','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                    InEvap.Cp = PropsSI('C','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                InCond.q = (OutCond.h - InCond.h)*InCond.m
                OutCond.q = InCond.q
                no_input = 'OutEvapT'
            elif no_Evapm == 1:
                if InCond.fluidmixture == ('air' or 'Air') or OutCond.fluidmixture == ('air' or 'Air'):
                    InCond.h = HAPropsSI('H','T',InCond.T, 'P',InCond.p, 'W', InCond.ahum)
                    InCond.Cp = HAPropsSI('C','T',InCond.T, 'P',InCond.p, 'W', InCond.ahum)
                    OutCond.h = HAPropsSI('H','T',OutCond.T, 'P',OutCond.p, 'W', OutCond.ahum)
                    OutCond.Cp = HAPropsSI('C','T',OutCond.T, 'P',OutCond.p, 'W', OutCond.ahum)
                else:
                    InCond.h = PropsSI('H','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                    InCond.Cp = PropsSI('C','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                    OutCond.h = PropsSI('H','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                    OutCond.Cp = PropsSI('C','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                if InEvap.fluidmixture == ('air' or 'Air') or OutEvap.fluidmixture == ('air' or 'Air'):
                    InEvap.h = HAPropsSI('H','T',InEvap.T, 'P',InEvap.p, 'W',InEvap.ahum)
                    InEvap.Cp = HAPropsSI('C','T',InEvap.T, 'P',InEvap.p, 'W',InEvap.ahum)
                    OutEvap.h = HAPropsSI('H','T',OutEvap.T, 'P',OutEvap.p, 'W',OutEvap.ahum)
                    OutEvap.Cp = HAPropsSI('C','T',OutEvap.T, 'P',OutEvap.p, 'W',OutEvap.ahum)
                else:    
                    InEvap.h = PropsSI('H','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                    InEvap.Cp = PropsSI('C','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                    OutEvap.h = PropsSI('H','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                    OutEvap.Cp = PropsSI('C','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                InCond.q = (OutCond.h - InCond.h)*InCond.m
                OutCond.q = InCond.q
                no_input = 'Evapm'
                
        return (InCond, OutCond, InEvap, OutEvap, no_input)
    

    def Steam_module(self, InCond, OutCond, inputs):
        p_flash = PropsSI('P','T',inputs.T_steam,'Q',1.0, InCond.fluidmixture)
        OutCond.p = PropsSI('P','T',OutCond.T+2.0, 'Q', 0.0, InCond.fluidmixture)
        OutCond.h = PropsSI('H','T',OutCond.T, 'P', OutCond.p, InCond.fluidmixture)
        X_flash = PropsSI('Q','H',OutCond.h,'P',p_flash, InCond.fluidmixture)
        OutCond.m = inputs.m_steam / X_flash
        InCond.m = OutCond.m
        m_sat_liq = (1-X_flash)*OutCond.m
        h_sat_liq = PropsSI('H','P',p_flash,'Q',0.0, InCond.fluidmixture)
        h_makeup = PropsSI('H','T',inputs.T_makeup,'P',p_flash, InCond.fluidmixture)
        
        InCond.h = (m_sat_liq*h_sat_liq + inputs.m_makeup*h_makeup)/OutCond.m
        InCond.T = PropsSI('T','H',InCond.h,'P',p_flash, InCond.fluidmixture)
        InCond.p = OutCond.p
            
        return (InCond, OutCond)
        
    def Hotwater_module(self, InCond, OutCond, inputs):
        rho_water = PropsSI('D','T',0.5*(inputs.T_makeup+inputs.T_target),'P',self.amb_P, InCond.fluidmixture)
        self.V_tank = inputs.M_load/rho_water
        InCond.p = self.amb_P
        OutCond.p = self.amb_P
        h_target = PropsSI('H','T',inputs.T_target,'P',self.amb_P,InCond.fluidmixture)
        h_makeup = PropsSI('H','T',inputs.T_makeup,'P',self.amb_P,InCond.fluidmixture)
        InCond.h = 0.5*(h_target + h_makeup)
        InCond.T = PropsSI('T','H',InCond.h,'P',InCond.p, InCond.fluidmixture)
        Cp_water = PropsSI('C','T',InCond.T,'P',InCond.p, InCond.fluidmixture)
        OutCond.q = 0.5*inputs.M_load*Cp_water*(inputs.T_target - InCond.T)/inputs.time_target
        OutCond.m = OutCond.q/(Cp_water*inputs.dT_lift)
        InCond.m = OutCond.m
        OutCond.T = InCond.T + inputs.dT_lift
        
        return (InCond, OutCond)

    def Injection_Solver(self, InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, no_input, cond_ph, evap_ph):
        dfrac = 0.005
        inter_frac_lb = 0.0
        inter_frac_ub = 1.0
        results_array = []
        frac_a = 1
        while frac_a:
            for iii in range(2):
                if iii == 0:
                    self.inter_frac = 0.5*(inter_frac_lb+inter_frac_ub)*(1-dfrac)
                else:
                    self.inter_frac = 0.5*(inter_frac_lb+inter_frac_ub)*(1+dfrac)
                
                (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs) = self.Cycle_Solver(InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, no_input, cond_ph, evap_ph)
                
                if self.evap_conv_err == 1:
                    if self.evap_err > 0:
                        inter_frac_lb = self.inter_frac
                    else:
                        inter_frac_ub = self.inter_frac
                    inputs.tol += 0.001
                    break
                else:
                    if iii == 0:
                        COP_o = outputs.COP_heating
                        frac_o = self.inter_frac
                    else:
                        dCOP = ((outputs.COP_heating - COP_o)/outputs.COP_heating)/((self.inter_frac - frac_o)/self.inter_frac)
                        if dCOP > 0:
                            inter_frac_lb = self.inter_frac
                        else:
                            inter_frac_ub = self.inter_frac
                           
                        results_array.append([0.5*(COP_o + outputs.COP_heating), 0.5*(frac_o + self.inter_frac), dCOP])
                        
                        if len(results_array) > 2:
                            if results_array[-2][0] > results_array[-1][0] and results_array[-2][0] > results_array[-3][0]:
                                outputs.COP_heating = results_array[-2][0]
                                outputs.inter_frac = results_array[-2][0]
                                frac_a = 0
                            elif abs(results_array[-1][2]) < inputs.tol:
                                outputs.COP_heating = results_array[-1][0]
                                outputs.inter_frac = results_array[-1][1]
                                frac_a = 0
                        
                        if (inter_frac_ub - inter_frac_lb) < inputs.tol: 
                            outputs.COP_heating = results_array[-1][0]
                            outputs.inter_frac = results_array[-1][1]
                            frac_a = 0
        
        return (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs)
    
    def Comp_2stage_Solver(self, InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, no_input, cond_ph, evap_ph):
        self.inter_frac = inputs.frac
        (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs) = self.Cycle_Solver(InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, no_input, cond_ph, evap_ph)
        
        return (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs)
    
    def Cycle_Solver(self,InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, no_input, cond_ph, evap_ph):
        if no_input == 'InEvapT':
            evap_p_ub = PropsSI('P','T',OutEvap.T, 'Q', 0.0, InEvap_REF.fluidmixture)        
        else:
            evap_p_ub = PropsSI('P','T',InEvap.T, 'Q', 0.0, InEvap_REF.fluidmixture)
            
        evap_p_lb = self.amb_P
        evap_a = 1
        
        while evap_a: 
            OutEvap_REF.p = 0.5*(evap_p_lb+evap_p_ub)
            InEvap_REF.p = OutEvap_REF.p+inputs.evap_dp
            
            OutEvap_REF_Tvap = PropsSI('T','P',OutEvap_REF.p, 'Q', 1.0, OutEvap_REF.fluidmixture)
            OutEvap_REF.T = OutEvap_REF_Tvap + inputs.DSH
            if inputs.DSH == 0:
                OutEvap_REF.h = PropsSI('H','P',OutEvap_REF.p, 'Q', 1.0, OutEvap_REF.fluidmixture)
                OutEvap_REF.s = PropsSI('S','P',OutEvap_REF.p, 'Q', 1.0, OutEvap_REF.fluidmixture)
            else:
                OutEvap_REF.h = PropsSI('H','T',OutEvap_REF.T, 'P', OutEvap_REF.p ,OutEvap_REF.fluidmixture)
                OutEvap_REF.s = PropsSI('S','T',OutEvap_REF.T, 'P', OutEvap_REF.p ,OutEvap_REF.fluidmixture)
            
            (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs) = self.HighPressure_Solver(InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, no_input, cond_ph)
            
            evap = HX.Heatexchanger_module(InEvap_REF, OutEvap_REF, 1, InEvap, OutEvap, evap_ph)
            
            if inputs.evap_type == 'fthe':
                evap.FTHE(N_element = inputs.evap_N_element, N_turn = inputs.evap_N_turn, N_row = inputs.evap_N_row)
                self.evap_err = (inputs.evap_T_lm - evap.T_lm)/inputs.evap_T_lm
            elif inputs.evap_type == 'phe':
                evap.PHE(N_element= inputs.evap_N_element)
                self.evap_err = (inputs.evap_T_pp - evap.T_pp)/inputs.evap_T_pp
            
            OutEvap_REF = evap.primary_out
            
            if evap.T_rvs == 1:
                evap_p_ub = OutEvap_REF.p                    
            else:
                if self.evap_err < 0:
                    evap_p_lb = OutEvap_REF.p
                else:
                    evap_p_ub = OutEvap_REF.p
                    
            if abs(self.evap_err) < inputs.tol:
                self.evap_conv_err = 0
                evap_a = 0
            elif (evap_p_ub - evap_p_lb)/self.amb_P < inputs.tol:
                self.evap_conv_err = 1
                evap_a = 0
                
        outputs.COP_heating = abs(OutCond.q)/(outputs.Wcomp - outputs.Wexpand)
        outputs.DSH = inputs.DSH
        outputs.evap_UA = evap.UA
        
        return (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs)
        
    def HighPressure_Solver(self, InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, no_input, cond_ph):
        if inputs.cycle == 'scc':
            cond_p_ub = min(5*InCond_REF.p_crit, 1.0e8)
            cond_p_lb = InCond_REF.p_crit
        else:
            cond_p_ub = InCond_REF.p_crit
            if no_input == 'InCondT':
                cond_p_lb = PropsSI('P','T',OutCond.T,'Q',1.0,OutCond_REF.fluidmixture)
            else:
                cond_p_lb = PropsSI('P','T',InCond.T,'Q',1.0,OutCond_REF.fluidmixture)

        cond_a = 1
        while cond_a:
            InCond_REF.p = 0.5*(cond_p_ub+cond_p_lb)
            OutCond_REF.p = InCond_REF.p-inputs.cond_dp
            
            if OutCond_REF.p > OutCond_REF.p_crit:
                OutCond_REF.T = 0.10753154*((OutCond_REF.p - OutCond_REF.p_crit)/OutCond_REF.p_crit) + 0.004627621995008088
                OutCond_REF.T = OutCond_REF.T*OutCond_REF.T_crit + OutCond_REF.T_crit - inputs.DSC
                OutCond_REF.h = PropsSI('H','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
                if inputs.expand_eff > 0.0:
                    OutCond_REF.s = PropsSI('S','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
            else:
                OutCond_REF.T = PropsSI('T','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture) - inputs.DSC
                if inputs.DSC == 0:
                    OutCond_REF.h = PropsSI('H','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture)
                    if inputs.expand_eff > 0.0:
                        OutCond_REF.s = PropsSI('S','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture)
                else:
                    OutCond_REF.h = PropsSI('H','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
                    if inputs.expand_eff > 0.0:
                        OutCond_REF.s = PropsSI('S','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
            
            if inputs.cycle != 'scc':
                if InCond_REF.p > InCond_REF.p_crit*0.98:
                    self.cond_p_err = 1
                    break
                else:
                    self.cond_p_err = 0 
    
            if inputs.layout == 'inj':
                inter_p = InEvap_REF.p + self.inter_frac*(OutCond_REF.p - InEvap_REF.p)
                inter_h_vap = PropsSI('H','P',inter_p,'Q',1.0, OutCond_REF.fluidmixture)
                outputs.inter_h_vap = inter_h_vap
                inter_h_liq = PropsSI('H','P',inter_p,'Q',0.0, OutCond_REF.fluidmixture)
                outputs.inter_x = (OutCond_REF.h - inter_h_liq)/(inter_h_vap - inter_h_liq)
                
                OutComp_low = deepcopy(OutEvap_REF)
                OutComp_low.p = inter_p
                
                comp_low = CP.Compander_module(OutEvap_REF, OutComp_low)
                (inputs.DSH, cond_a) = comp_low.COMP(eff_isen = inputs.comp_eff, DSH = inputs.DSH)
                OutComp_low = comp_low.primary_out
                
                InComp_high = deepcopy(OutComp_low)
                
                InComp_high.h = OutComp_low.h*((1.0-outputs.inter_x)*(1-inputs.liq_frac)+outputs.inter_x*(1-inputs.vap_frac))+inter_h_vap*outputs.inter_x*inputs.vap_frac+inter_h_liq*(1-outputs.inter_x)*inputs.liq_frac
                InComp_high.T = PropsSI('T','P',InComp_high.p,'H',InComp_high.h, InComp_high.fluidmixture)
                InComp_high.s = PropsSI('S','T',InComp_high.T, 'P', InComp_high.p, InComp_high.fluidmixture)
                
                comp_high = CP.Compander_module(InComp_high, InCond_REF)
                (inputs.DSH, cond_a)= comp_high.COMP(eff_isen = inputs.comp_top_eff, DSH = inputs.DSH)
                InCond_REF = comp_high.primary_out
                
                OutExpand_high = deepcopy(OutCond_REF)
                OutExpand_high.p = inter_p
                expand_high = CP.Compander_module(OutCond_REF, OutExpand_high)
                expand_high.EXPAND(eff_isen=inputs.expand_eff)
                OutExpand_high = expand_high.primary_out
                
                Flash_liq = deepcopy(OutExpand_high) # 팽창 후 2-phase 중 liq 상만 두번째 팽창기 입구로
                Flash_liq.h = (inter_h_liq*(1-inputs.liq_frac)*(1-outputs.inter_x)+inter_h_vap*(1-inputs.vap_frac)*outputs.inter_x)/((1-inputs.liq_frac)*(1-outputs.inter_x)+(1-inputs.vap_frac)*outputs.inter_x)
                Flash_liq.T = PropsSI('T','P',OutExpand_high.p,'Q',0.0, OutExpand_high.fluidmixture)
                if inputs.expand_bot_eff > 0.0:
                    Flash_liq.s = PropsSI('S','P',OutExpand_high.p,'Q',0.0, OutExpand_high.fluidmixture) 

                expand_low = CP.Compander_module(Flash_liq, InEvap_REF)
                expand_low.EXPAND(eff_isen=inputs.expand_bot_eff)
                InEvap_REF = expand_low.primary_out
                
            elif inputs.layout == '2comp':
                inter_p = InEvap_REF.p + self.inter_frac*(OutCond_REF.p - InEvap_REF.p)
                OutComp_low = deepcopy(OutEvap_REF)
                OutComp_low.p = inter_p
                
                comp_low = CP.Compander_module(OutEvap_REF, OutComp_low)
                (inputs.DSH, cond_a) = comp_low.COMP(eff_isen = inputs.comp_eff, DSH = inputs.DSH)
                OutComp_low = comp_low.primary_out
                
                InComp_high = deepcopy(OutComp_low)
                
                InComp_high.h = OutComp_low.h
                InComp_high.T = PropsSI('T','P',InComp_high.p,'H',InComp_high.h, InComp_high.fluidmixture)
                InComp_high.s = PropsSI('S','T',InComp_high.T, 'P', InComp_high.p, InComp_high.fluidmixture)
                
                comp_high = CP.Compander_module(InComp_high, InCond_REF)
                (inputs.DSH, cond_a) = comp_high.COMP(eff_isen = inputs.comp_top_eff, DSH = inputs.DSH)
                InCond_REF = comp_high.primary_out
                
                InExpand = OutCond_REF
                expand_high = CP.Compander_module(InExpand, InEvap_REF)
                expand_high.EXPAND(eff_isen = inputs.expand_eff)
                InEvap_REF = expand_high.primary_out
            elif inputs.layout == 'part_cool':
                
                pcx_cold_in = deepcopy(InEvap_REF)
                OutPCX_hot = deepcopy(InEvap_REF)
                OutPCX_cold = deepcopy(InEvap_REF)
                
                pcx_cold_in.p = InEvap_REF.p+inputs.pcx_cold_dp
                cold_expand = CP.Compander_module(OutCond_REF, pcx_cold_in)
                cold_expand.EXPAND(eff_isen = 0.0)
                pcx_cold_in = cold_expand.primary_out
                
                OutPCX_hot.p = OutCond_REF.p-inputs.pcx_hot_dp
                pcx_hot_out_hideal = PropsSI("H","T",pcx_cold_in.T,"P",OutPCX_hot.p,OutPCX_hot.fluidmixture)
                pcx_cold_out_hideal = PropsSI("H","T",OutCond_REF.T,"P",OutPCX_cold.p,OutPCX_cold.fluidmixture)
                
                if (OutCond_REF.h-pcx_hot_out_hideal)*(1-inputs.pcx_frac) > (pcx_cold_out_hideal-pcx_cold_in.h)*inputs.pcx_frac:
                    # hot 측 열용량이 더 큰 경우
                    OutPCX_cold.T = OutCond_REF.T-inputs.pcx_T_pp
                    OutPCX_cold.h = PropsSI("H","T",OutPCX_cold.T,"P",OutPCX_cold.p,OutPCX_cold.fluidmixture)
                    OutPCX_hot.h = OutCond_REF.h - (OutPCX_cold.h - pcx_cold_in.h)*inputs.pcx_frac/(1-inputs.pcx_frac)
                    OutPCX_hot.T = PropsSI("T","H",OutPCX_hot.h,"P",OutPCX_hot.p,OutPCX_hot.fluidmixture)
                else:
                    # cold 측 열용량이 더 큰 경우
                    OutPCX_hot.T = pcx_cold_in.T+inputs.pcx_T_pp
                    OutPCX_hot.h = PropsSI("H","T",OutPCX_hot.T,"P",OutPCX_hot.p,OutPCX_hot.fluidmixture)
                    OutPCX_cold.h = OutCond_REF.h+(OutCond_REF.h-OutPCX_hot.h)*(1-inputs.pcx_frac)/inputs.pcx_frac
                    OutPCX_cold.T = PropsSI("T","H",OutPCX_cold.h,"P",OutPCX_cold.p,OutPCX_cold.fluidmixture)
                
                expand = CP.Compander_module(OutPCX_hot, InEvap_REF)
                expand.EXPAND(eff_isen = 0.0)
                InEvap_REF = expand.primary_out
                
                InComp = deepcopy(OutEvap_REF)
                InComp.h = OutEvap_REF.h*(1-inputs.pcx_frac)+OutPCX_cold.h*inputs.pcx_frac
                InComp.T = PropsSI("T","H",InComp.h,"P",InComp.p,InComp.fluidmixture)               
                comp = CP.Compander_module(InComp, InCond_REF)
                (inputs.DSH, cond_a) = comp.COMP(eff_isen = inputs.comp_eff, DSH = inputs.DSH)
                InCond_REF = comp.primary_out
                
            else:
                if inputs.layout == 'ihx':
                    InComp = deepcopy(OutEvap_REF)
                    InComp.p = InComp.p-inputs.ihx_cold_dp
                    InExpand = deepcopy(OutCond_REF)
                    InExpand.p = InExpand.p-inputs.ihx_hot_dp
                    IHX = HX.Heatexchanger_module(OutCond_REF, InExpand, 0, OutEvap_REF, InComp, 0)
                    IHX.SIMPHX(eff_HX = inputs.ihx_eff)
                
                    InExpand = IHX.primary_out
                    InComp = IHX.secondary_out
                else:    
                    InComp = OutEvap_REF
                    InExpand = OutCond_REF
                
                comp = CP.Compander_module(InComp, InCond_REF)
                (inputs.DSH, cond_a) = comp.COMP(eff_isen = inputs.comp_eff, DSH = inputs.DSH)
                InCond_REF = comp.primary_out
                
                
                expand = CP.Compander_module(InExpand, InEvap_REF)
                expand.EXPAND(eff_isen = inputs.expand_eff)
                InEvap_REF = expand.primary_out
                
            if (no_input == 'InCondT') or (no_input == 'OutCondT') or (no_input == 'Condm'):
                InEvap_REF.m = InEvap.q/(InEvap_REF.h - OutEvap_REF.h)
                OutEvap_REF.m = InEvap_REF.m
                if inputs.layout == 'inj':
                    InCond_REF.m = InEvap_REF.m/(1.0-outputs.inter_x)
                    OutCond_REF.m = InCond_REF.m
                    outputs.Wcomp = comp_low.Pspecific*OutEvap_REF.m + comp_high.Pspecific*InCond_REF.m
                    outputs.Wcomp /= inputs.mech_eff
                    outputs.Wcomp_top = comp_high.Pspecific*InCond_REF.m
                    outputs.Wcomp_top /= inputs.mech_eff
                    outputs.Wexpand = expand_high.Pspecific*OutCond_REF.m + expand_low.Pspecific*InEvap_REF.m
                    outputs.Wexpand *= inputs.mech_eff
                    outputs.Wexpand_bot = expand_low.Pspecific*InEvap_REF.m
                    outputs.Wexpand_bot *= inputs.mech_eff
                elif inputs.layout == '2comp':
                    InCond_REF.m = InEvap_REF.m
                    OutCond_REF.m = InEvap_REF.m
                    outputs.Wcomp = comp_low.Pspecific*OutEvap_REF.m + comp_high.Pspecific*InCond_REF.m
                    outputs.Wcomp /= inputs.mech_eff
                    outputs.Wcomp_top = comp_high.Pspecific*InCond_REF.m
                    outputs.Wcomp_top /= inputs.mech_eff
                    outputs.Wexpand = expand_high.Pspecific*OutCond_REF.m
                    outputs.Wexpand *= inputs.mech_eff
                elif inputs.layout == 'part_cool':
                    InCond_REF.m  = InEvap_REF.m/(1-inputs.pcx_frac)
                    OutCond_REF.m = InEvap_REF.m/(1-inputs.pcx_frac)
                    pcx_cold_in.m = OutCond_REF.m*inputs.pcx_frac
                    OutPCX_hot.m = OutCond_REF.m*(1-inputs.pcx_frac)
                    OutPCX_cold.m = OutCond_REF.m*inputs.pcx_frac
                    InComp.m = InCond_REF.m
                    
                    outputs.Wcomp = comp.Pspecific*InCond_REF.m
                    outputs.Wcomp /= inputs.mech_eff
                    outputs.Wexpand = (cold_expand.Pspecific*inputs.pcx_frac + expand.Pspecific*(1-inputs.pcx_frac))*InCond_REF.m
                    outputs.Wexpand *= inputs.mech_eff
                else:
                    InCond_REF.m = InEvap_REF.m
                    OutCond_REF.m = InEvap_REF.m
                    outputs.Wcomp = comp.Pspecific*InCond_REF.m
                    outputs.Wcomp /= inputs.mech_eff
                    outputs.Wexpand = expand.Pspecific*InEvap_REF.m
                    outputs.Wexpand *= inputs.mech_eff
                    
                InEvap_REF.q = -InEvap.q
                OutEvap_REF.q = -OutEvap.q
                
                InCond_REF.q = (OutCond_REF.h - InCond_REF.h)*InCond_REF.m
                OutCond_REF.q = InCond_REF.q
                InCond.q = -InCond_REF.q
                OutCond.q = -InCond_REF.q
                if no_input == 'InCondT':
                    InCond.h = OutCond.h - OutCond.q/OutCond.m
                    try:
                        if InCond.fluidmixture == ('air' or 'Air'):
                            InCond.T = HAPropsSI('T','P',InCond.p, 'H', InCond.h, 'W', InCond.ahum)
                            InCond.Cp = HAPropsSI('C','T',InCond.T, 'P', InCond.p, 'W', InCond.ahum)
                        else:
                            InCond.T = PropsSI('T','P',InCond.p, 'H', InCond.h, InCond.fluidmixture)
                            InCond.Cp = PropsSI('C','T',InCond.T, 'P', InCond.p, InCond.fluidmixture)
                    except:    
                        InCond.T = OutCond.T
                        while 1:
                            if InCond.fluidmixture == ('air' or 'Air'):
                                H_virtual = HAPropsSI('H','T', InCond.T, 'P', InCond.p, 'W', InCond.ahum)
                                InCond.Cp = HAPropsSI('C','T',InCond.T, 'P', InCond.p, 'W', InCond.ahum)
                            else:
                                H_virtual = PropsSI('H','T', InCond.T, 'P', InCond.p, InCond.fluidmixture)
                                InCond.Cp = PropsSI('C','T',InCond.T, 'P', InCond.p, InCond.fluidmixture)
                            err_h = H_virtual - InCond.h
                            InCond.T = InCond.T - err_h/InCond.Cp
                            if err_h/InCond.h < 1.0e-5:
                                break
                elif no_input == 'OutCondT':
                    OutCond.h = InCond.h + InCond.q/InCond.m
                    try:
                        if OutCond.fluidmixture == ('air' or 'Air'):
                            OutCond.T = HAPropsSI('T','P',OutCond.p, 'H', OutCond.h, 'W', OutCond.ahum)
                            OutCond.Cp = HAPropsSI('C','T',OutCond.T, 'P', OutCond.p, 'W', OutCond.ahum)
                        else:    
                            OutCond.T = PropsSI('T','P',OutCond.p, 'H', OutCond.h, OutCond.fluidmixture)
                            OutCond.Cp = PropsSI('C','T',OutCond.T, 'P', OutCond.p, OutCond.fluidmixture)
                    except:
                        OutCond.T = InCond.T
                        while 1:
                            if OutCond.fluidmixture == ('air' or 'Air'):
                                H_virtual = HAPropsSI('H','T', OutCond.T, 'P', OutCond.p, 'W', OutCond.ahum)
                                OutCond.Cp = HAPropsSI('C','T',OutCond.T, 'P', OutCond.p, 'W', OutCond.ahum)
                            else:    
                                H_virtual = PropsSI('H','T', OutCond.T, 'P', OutCond.p, OutCond.fluidmixture)
                                OutCond.Cp = PropsSI('C','T',OutCond.T, 'P', OutCond.p, OutCond.fluidmixture)
                            err_h = H_virtual - OutCond.h
                            OutCond.T = OutCond.T - err_h/OutCond.Cp
                            if err_h/OutCond.h < 1.0e-5:
                                break
                elif no_input == 'Condm':
                    InCond.m = InCond.q/(OutCond.h - InCond.h)
                    OutCond.m = InCond.m
                
            elif (no_input == 'InEvapT') or (no_input == 'OutEvapT') or (no_input == 'Evapm'):
                InCond_REF.m = InCond.q/(InCond_REF.h - OutCond_REF.h)
                OutCond_REF.m = InCond_REF.m
                if inputs.layout == 'inj':
                    InEvap_REF.m = InCond_REF.m*(1.0 - outputs.inter_x)
                    OutEvap_REF.m = InCond_REF.m*(1.0 - outputs.inter_x)
                    outputs.Wcomp = comp_low.Pspecific*OutEvap_REF.m + comp_high.Pspecific*InCond_REF.m
                    outputs.Wcomp /= inputs.mech_eff
                    outputs.Wcomp_top = comp_high.Pspecific*InCond_REF.m
                    outputs.Wcomp_top /= inputs.mech_eff
                    outputs.Wexpand = expand_high.Pspecific*OutCond_REF.m + expand_low.Pspecific*InEvap_REF.m
                    outputs.Wexpand *= inputs.mech_eff
                    outputs.Wexpand_bot = expand_low.Pspecific*InEvap_REF.m
                    outputs.Wexpand_bot *= inputs.mech_eff
                elif inputs.layout == '2comp':
                    InEvap_REF.m = InCond_REF.m
                    OutEvap_REF.m = InCond_REF.m
                    outputs.Wcomp = comp_low.Pspecific*OutEvap_REF.m + comp_high.Pspecific*InCond_REF.m
                    outputs.Wcomp /= inputs.mech_eff
                    outputs.Wcomp_top = comp_high.Pspecific*InCond_REF.m
                    outputs.Wcomp_top /= inputs.mech_eff
                    outputs.Wexpand = expand_high.Pspecific*OutCond_REF.m
                    outputs.Wexpand *= inputs.mech_eff
                elif inputs.layout == 'part_cool':
                    InEvap_REF.m = InCond_REF.m*(1-inputs.pcx_frac)
                    OutEvap_REF.m = InCond_REF.m*(1-inputs.pcx_frac)
                    pcx_cold_in.m = OutCond_REF.m*inputs.pcx_frac
                    OutPCX_hot.m = OutCond_REF.m*(1-inputs.pcx_frac)
                    OutPCX_cold.m = OutCond_REF.m*inputs.pcx_frac
                    InComp.m = InCond_REF.m
                    
                    outputs.Wcomp = comp.Pspecific*InCond_REF.m
                    outputs.Wcomp /= inputs.mech_eff
                    outputs.Wexpand = (cold_expand.Pspecific*inputs.pcx_frac + expand.Pspecific*(1-inputs.pcx_frac))*InCond_REF.m
                    outputs.Wexpand *= inputs.mech_eff
                else:
                    InEvap_REF.m = InCond_REF.m
                    OutEvap_REF.m = InCond_REF.m
                    outputs.Wcomp = comp.Pspecific*InCond_REF.m
                    outputs.Wcomp /= inputs.mech_eff
                    outputs.Wexpand = expand.Pspecific*InEvap_REF.m
                    outputs.Wexpand *= inputs.mech_eff
                
                InCond_REF.q = -InCond.q
                OutCond_REF.q = -InCond.q
                
                InEvap_REF.q = (OutEvap_REF.h - InEvap_REF.h)*InEvap_REF.m
                OutEvap_REF.q = InEvap_REF.q
                InEvap.q = -InEvap_REF.q
                OutEvap.q = -InEvap_REF.q
                
                if no_input == 'InEvapT':
                    InEvap.h = OutEvap.h - OutEvap.q/OutEvap.m
                    try:
                        if InEvap.fluidmixture == ('air' or 'Air'):
                            InEvap.T = HAPropsSI('T','P',InEvap.p, 'H', InEvap.h, 'W', InEvap.ahum)
                            InEvap.Cp = HAPropsSI('C','T',InEvap.T, 'P', InEvap.p, 'W', InEvap.ahum)
                        else:
                            InEvap.T = PropsSI('T','P',InEvap.p, 'H', InEvap.h, InEvap.fluidmixture)
                            InEvap.Cp = PropsSI('C','T',InEvap.T, 'P', InEvap.p, InEvap.fluidmixture)
                    except:    
                        InEvap.T = OutEvap.T
                        while 1:
                            if InEvap.fluidmixture == ('air' or 'Air'):
                                H_virtual = HAPropsSI('H','T', InEvap.T, 'P', InEvap.p, 'W', InEvap.ahum)
                                InEvap.Cp = HAPropsSI('C','T',InEvap.T, 'P', InEvap.p, 'W', InEvap.ahum)
                            else:
                                H_virtual = PropsSI('H','T', InEvap.T, 'P', InEvap.p, InEvap.fluidmixture)
                                InEvap.Cp = PropsSI('C','T',InEvap.T, 'P', InEvap.p, InEvap.fluidmixture)
                            err_h = H_virtual - InEvap.h
                            InEvap.T = InEvap.T - err_h/InEvap.Cp
                            if err_h/InEvap.h < 1.0e-5:
                                break
                            
                elif no_input == 'OutEvapT':
                    OutEvap.h = InEvap.h + InEvap.q/InEvap.m
                    try:
                        if OutEvap.fluidmixture == ('air' or 'Air'):
                            OutEvap.T = HAPropsSI('T','P',OutEvap.p, 'H', OutEvap.h, 'W', OutEvap.ahum)
                            OutEvap.Cp = HAPropsSI('C','T',OutEvap.T, 'P', OutEvap.p, 'W', OutEvap.ahum)
                        else:    
                            OutEvap.T = PropsSI('T','P',OutEvap.p, 'H', OutEvap.h, OutEvap.fluidmixture)
                            OutEvap.Cp = PropsSI('C','T',OutEvap.T, 'P', OutEvap.p, OutEvap.fluidmixture)
                    except:
                        OutEvap.T = InEvap.T
                        while 1:
                            if OutEvap.fluidmixture == ('air' or 'Air'):
                                H_virtual = HAPropsSI('H','T', OutEvap.T, 'P', OutEvap.p, 'W', OutEvap.ahum)
                                OutEvap.Cp = HAPropsSI('C','T',OutEvap.T, 'P', OutEvap.p, 'W', OutEvap.ahum)
                            else:    
                                H_virtual = PropsSI('H','T', OutEvap.T, 'P', OutEvap.p, OutEvap.fluidmixture)
                                OutEvap.Cp = PropsSI('C','T',OutEvap.T, 'P', OutEvap.p, OutEvap.fluidmixture)
                            err_h = H_virtual - OutEvap.h
                            OutEvap.T = OutEvap.T - err_h/OutEvap.Cp
                            if err_h/OutEvap.h < 1.0e-5:
                                break
                    
                elif no_input == 'Evapm':
                    InEvap.m = InEvap.q/(OutEvap.h - InEvap.h)
                    OutEvap.m = InEvap.m
                
            cond = HX.Heatexchanger_module(InCond_REF, OutCond_REF, 1, InCond, OutCond, cond_ph)
        
            if inputs.cond_type == 'fthe':
                (outputs.cond_Tarray, outputs.cond_parray) = cond.FTHE(N_element=inputs.cond_N_element, N_turn = inputs.cond_N_turn, N_row = inputs.cond_N_row)
                self.cond_err = (inputs.cond_T_lm - cond.T_lm)/inputs.cond_T_lm
                
            elif inputs.cond_type == 'phe':
                (outputs.cond_Tarray, outputs.cond_parray) = cond.PHE(N_element=inputs.cond_N_element)
                self.cond_err = (inputs.cond_T_pp - cond.T_pp)/inputs.cond_T_pp
            
            OutCond_REF = cond.primary_out
            
            if cond.T_rvs == 1:
                cond_p_lb = InCond_REF.p
            else:
                if self.cond_err < 0:
                    cond_p_ub = InCond_REF.p
                else:
                    cond_p_lb = InCond_REF.p
            
            if abs(self.cond_err) < inputs.tol:
                self.cond_conv_err = 0
                cond_a = 0
            elif (cond_p_ub - cond_p_lb)/self.amb_P < inputs.tol:
                self.cond_conv_err = 1
                cond_a = 0
        
        outputs.cond_UA = cond.UA
        if inputs.layout == 'ihx':
            outputs.qihx = (InComp.h - OutEvap_REF.h)*OutEvap_REF.m
            outputs.ihx_hot_out_T = InExpand.T
            outputs.ihx_hot_out_p = InExpand.p
            outputs.ihx_hot_out_h = InExpand.h
            outputs.ihx_hot_out_s = InExpand.s
            outputs.ihx_cold_out_T = InComp.T
            outputs.ihx_cold_out_p = InComp.p
            outputs.ihx_cold_out_h = InComp.h
            outputs.ihx_cold_out_s = InComp.s
        elif inputs.layout == 'inj':
            outputs.outcomp_low_T = OutComp_low.T
            outputs.outcomp_low_p = OutComp_low.p
            outputs.outcomp_low_h = OutComp_low.h
            outputs.outcomp_low_s = OutComp_low.s
            outputs.incomp_high_T = InComp_high.T
            outputs.incomp_high_p = InComp_high.p
            outputs.incomp_high_h = InComp_high.h
            outputs.incomp_high_s = InComp_high.s
            outputs.outexpand_high_T = OutExpand_high.T
            outputs.outexpand_high_p = OutExpand_high.p
            outputs.outexpand_high_h = OutExpand_high.h
            outputs.outexpand_high_s = OutExpand_high.s
            outputs.flash_liq_T = Flash_liq.T
            outputs.flash_liq_p = Flash_liq.p
            outputs.flash_liq_h = Flash_liq.h
            outputs.flash_liq_s = Flash_liq.s
        elif inputs.layout == '2comp':
            outputs.outcomp_low_T = OutComp_low.T
            outputs.outcomp_low_p = OutComp_low.p
            outputs.outcomp_low_h = OutComp_low.h
            outputs.outcomp_low_s = OutComp_low.s
            outputs.incomp_high_T = InComp_high.T
            outputs.incomp_high_p = InComp_high.p
            outputs.incomp_high_h = InComp_high.h
            outputs.incomp_high_s = InComp_high.s
        elif inputs.layout == 'part_cool':
            outputs.pcx_cold_in_T = pcx_cold_in.T
            outputs.pcx_cold_in_p = pcx_cold_in.p
            outputs.pcx_cold_in_h = pcx_cold_in.h
            outputs.pcx_hot_out_T = OutPCX_hot.T
            outputs.pcx_hot_out_p = OutPCX_hot.p
            outputs.pcx_hot_out_h = OutPCX_hot.h
            outputs.pcx_cold_out_T = OutPCX_cold.T
            outputs.pcx_cold_out_p = OutPCX_cold.p
            outputs.pcx_cold_out_h = OutPCX_cold.h
            outputs.incomp_T = InComp.T
            outputs.incomp_p = InComp.p
            outputs.incomp_h = InComp.h
            outputs.qpcx = (OutPCX_cold.h - pcx_cold_in.h)*pcx_cold_in.m
            
        return (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs)
    
    def Plot_diagram(self, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, ts_file, ph_file, coeff):
        (p_array, h_array, T_array, s_array) = self.Dome_Draw(list(inputs.Y.keys())[0], coeff)
        (p_points, h_points, T_points, s_points) = self.Diagram_Draw(InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs)
        fig_ph, ax_ph = PLT.subplots()
        ax_ph.plot([i/1.0e3 for i in h_array], [i/1.0e5 for i in p_array],'b--')
        ax_ph.set_xlabel('Enthalpy [kJ/kg]',fontsize = 15)
        ax_ph.set_ylabel('Pressure [bar]',fontsize = 15)
        ax_ph.set_title('Pressure-Enthalpy Diagram\nRefrigerant:{}'.format(list(inputs.Y.keys())[0]),fontsize = 18)
        ax_ph.tick_params(axis = 'x', labelsize = 13)
        ax_ph.tick_params(axis = 'y', labelsize = 13)
        
        fig_ts, ax_ts = PLT.subplots()
        ax_ts.plot([i/1.0e3 for i in s_array], [i-273.15 for i in T_array],'b--')
        ax_ts.set_xlabel('Entropy [kJ/kg-K]',fontsize = 15)
        ax_ts.set_ylabel('Temperature [℃]',fontsize = 15)
        ax_ts.set_title('Temperature-Entropy Diagram\nRefrigerant:{}'.format(list(inputs.Y.keys())[0]),fontsize = 18)
        ax_ts.tick_params(axis = 'x', labelsize = 13)
        ax_ts.tick_params(axis = 'y', labelsize = 13)
        
        ax_ts.plot([i/1.0e3 for i in s_points], [i-273.15 for i in T_points],'bo-')
        ax_ph.plot([i/1.0e3 for i in h_points], [i/1.0e5 for i in p_points],'bo-')
        
        fig_ph.savefig('./Figs/'+ph_file+'.png',dpi=300)
        fig_ts.savefig('./Figs/'+ts_file+'.png',dpi=300)
        
        
        
    def Dome_Draw(self, fluid, coeff=0.999):
        P_crit = PropsSI('PCRIT','',0,'',0,fluid)
        T_crit = PropsSI('TCRIT','',0,'',0,fluid)
        H_crit_liq = PropsSI('H','P',P_crit*coeff,'Q',0.0,fluid)
        H_crit_vap = PropsSI('H','P',P_crit*coeff,'Q',1.0,fluid)
        S_crit_liq = PropsSI('S','P',P_crit*coeff,'Q',0.0,fluid)
        S_crit_vap = PropsSI('S','P',P_crit*coeff,'Q',1.0,fluid)
        H_crit = 0.5*(H_crit_liq+H_crit_vap)
        S_crit = 0.5*(S_crit_liq+S_crit_vap)
        
        try:
            Pliq_array = [self.amb_P+(P_crit*coeff - self.amb_P)*i/49 for i in range(50)]
            Pvap_array = [P_crit*coeff - (P_crit*coeff - self.amb_P)*i/49 for i in range(50)]
            Tliq_array = [PropsSI('T','P',i,'Q',0.0,fluid) for i in Pliq_array]
            Tvap_array = [PropsSI('T','P',i,'Q',1.0,fluid) for i in Pvap_array]
            hliq_array = [PropsSI('H','P',i,'Q',0.0,fluid) for i in Pliq_array]
            hliq_array_new = [(H_crit-hliq_array[i-1])/(P_crit-Pliq_array[i-1])*(Pliq_array[i]-Pliq_array[i-1])+hliq_array[i-1] if hliq_array[i] < 0 or hliq_array[i]/hliq_array[i-1] > 1.2 else hliq_array[i] for i in range(len(hliq_array))]
            hvap_array = [PropsSI('H','P',i,'Q',1.0,fluid) for i in Pvap_array]
            hvap_array_new = [(H_crit-hvap_array[i-1])/(P_crit-Pvap_array[i-1])*(Pvap_array[i]-Pvap_array[i-1])+hvap_array[i-1] if hvap_array[i] < 0 or hvap_array[i-1]/hvap_array[i] > 1.2 else hvap_array[i] for i in range(len(hvap_array))]
            sliq_array = [PropsSI('S','P',i,'Q',0.0,fluid) for i in Pliq_array]
            sliq_array_new = [(S_crit-sliq_array[i-1])/(T_crit-Tliq_array[i-1])*(Tliq_array[i]-Tliq_array[i-1])+sliq_array[i-1] if sliq_array[i] < 0 or sliq_array[i]/sliq_array[i-1] > 1.2 else sliq_array[i] for i in range(len(sliq_array))]
            svap_array = [PropsSI('S','T',i,'Q',1.0,fluid) for i in Tvap_array]
            svap_array_new = [(S_crit-svap_array[i-1])/(T_crit-Tvap_array[i-1])*(Tvap_array[i]-Tvap_array[i-1])+svap_array[i-1] if svap_array[i] < 0 or svap_array[i-1]/svap_array[i] > 1.2 else svap_array[i] for i in range(len(svap_array))]
            
        except:
            P_trp = PropsSI('PTRIPLE','',0,'',0,fluid)
            Pliq_array = [P_trp*(2-coeff)+(P_crit*coeff - P_trp*(2-coeff))*i/49 for i in range(50)]
            Pvap_array = [P_crit*coeff - (P_crit*coeff - P_trp*(2-coeff))*i/49 for i in range(50)]
            Tliq_array = [PropsSI('T','P',i,'Q',0.0,fluid) for i in Pliq_array]
            Tvap_array = [PropsSI('T','P',i,'Q',1.0,fluid) for i in Pvap_array]
            hliq_array = [PropsSI('H','P',i,'Q',0.0,fluid) for i in Pliq_array]
            hvap_array = [PropsSI('H','P',i,'Q',1.0,fluid) for i in Pvap_array]
            sliq_array = [PropsSI('S','P',i,'Q',0.0,fluid) for i in Pliq_array]
            svap_array = [PropsSI('S','P',i,'Q',1.0,fluid) for i in Pvap_array]
            
        p_array = Pliq_array+[P_crit]+Pvap_array
        T_array = Tliq_array+[T_crit]+Tvap_array
        h_array = hliq_array_new+[H_crit]+hvap_array_new
        s_array = sliq_array_new+[S_crit]+svap_array_new
        
        return (p_array, h_array, T_array, s_array)
    
    def Diagram_Draw(self, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs):
    
        OutEvap_REF_Tvap = PropsSI('T','P',OutEvap_REF.p,'Q',1.0,OutCond_REF.fluidmixture)
        OutEvap_REF_svap = PropsSI('S','P',OutEvap_REF.p,'Q',1.0,OutCond_REF.fluidmixture)
        
        if inputs.cycle == 'vcc':
            InCond_REF_Tvap = PropsSI('T','P',InCond_REF.p,'Q',1.0,OutCond_REF.fluidmixture)
            InCond_REF_svap = PropsSI('S','P',InCond_REF.p,'Q',1.0,OutCond_REF.fluidmixture)
            OutCond_REF_Tliq = PropsSI('T','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture)
            OutCond_REF_sliq = PropsSI('S','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture)
        else:
            outputs.cond_Tarray
            outputs.cond_parray
            cond_harray = [PropsSI('H','T',i,'P',j,OutCond_REF.fluidmixture) for i,j in zip(outputs.cond_Tarray, outputs.cond_parray)]
            cond_sarray = [PropsSI('S','T',i,'P',j,OutCond_REF.fluidmixture) for i,j in zip(outputs.cond_Tarray, outputs.cond_parray)]
            
        OutCond_REF.s = PropsSI('S','T',OutCond_REF.T,'P',OutCond_REF.p,OutCond_REF.fluidmixture)
        InEvap_REF.s = PropsSI('S','H',InEvap_REF.h,'P',InEvap_REF.p,InEvap_REF.fluidmixture)
        
        if inputs.layout == 'ihx':
            if inputs.cycle == 'vcc':
                s_points = [OutEvap_REF_svap, OutEvap_REF.s, outputs.ihx_cold_out_s, InCond_REF.s, InCond_REF_svap, OutCond_REF_sliq, OutCond_REF.s, outputs.ihx_hot_out_s, InEvap_REF.s, OutEvap_REF_svap]
                T_points = [OutEvap_REF_Tvap, OutEvap_REF.T, outputs.ihx_cold_out_T, InCond_REF.T, InCond_REF_Tvap, OutCond_REF_Tliq, OutCond_REF.T, outputs.ihx_hot_out_T, InEvap_REF.T, OutEvap_REF_Tvap]
                h_points = [OutEvap_REF.h, outputs.ihx_cold_out_h, InCond_REF.h, OutCond_REF.h, outputs.ihx_hot_out_h, InEvap_REF.h, OutEvap_REF.h]
                p_points = [OutEvap_REF.p, outputs.ihx_cold_out_p, InCond_REF.p, OutCond_REF.p, outputs.ihx_hot_out_p, InEvap_REF.p, OutEvap_REF.p]
            else:
                s_points = [OutEvap_REF_svap, OutEvap_REF.s, outputs.ihx_cold_out_s, InCond_REF.s]+cond_sarray+[OutCond_REF.s, outputs.ihx_hot_out_s, InEvap_REF.s, OutEvap_REF_svap]
                T_points = [OutEvap_REF_Tvap, OutEvap_REF.T, outputs.ihx_cold_out_T, InCond_REF.T]+outputs.cond_Tarray+[OutCond_REF.T, outputs.ihx_hot_out_T, InEvap_REF.T, OutEvap_REF_Tvap]
                h_points = [OutEvap_REF.h, outputs.ihx_cold_out_h, InCond_REF.h]+cond_harray+[OutCond_REF.h, outputs.ihx_hot_out_h, InEvap_REF.h, OutEvap_REF.h]
                p_points = [OutEvap_REF.p, outputs.ihx_cold_out_p, InCond_REF.p]+outputs.cond_parray+[OutCond_REF.p, outputs.ihx_hot_out_p, InEvap_REF.p, OutEvap_REF.p]
            
        elif inputs.layout == 'inj':
            outcomp_low_svap = PropsSI('S','P',outputs.outcomp_low_p,'Q',1.0,InCond_REF.fluidmixture)
            outcomp_low_Tvap = PropsSI('T','P',outputs.outcomp_low_p,'Q',1.0,InCond_REF.fluidmixture)
            outputs.flash_liq_s = PropsSI('S','P',outputs.flash_liq_p,'Q',0.0,InCond_REF.fluidmixture)
            outputs.outexpand_high_s = PropsSI('S','P',outputs.outexpand_high_p,'H',outputs.outexpand_high_h,InCond_REF.fluidmixture)
            if inputs.cycle == 'vcc':    
                s_points = [outputs.flash_liq_s, InEvap_REF.s, OutEvap_REF_svap, OutEvap_REF.s, outputs.outcomp_low_s, outcomp_low_svap, outputs.flash_liq_s, outputs.outexpand_high_s, outcomp_low_svap, outputs.incomp_high_s, InCond_REF.s, InCond_REF_svap, OutCond_REF_sliq, OutCond_REF.s, outputs.outexpand_high_s] 
                T_points = [outputs.flash_liq_T, InEvap_REF.T, OutEvap_REF_Tvap, OutEvap_REF.T, outputs.outcomp_low_T, outcomp_low_Tvap, outputs.flash_liq_T, outputs.outexpand_high_T, outcomp_low_Tvap, outputs.incomp_high_T, InCond_REF.T, InCond_REF_Tvap, OutCond_REF_Tliq, OutCond_REF.T, outputs.outexpand_high_T] 
                h_points = [outputs.flash_liq_h, InEvap_REF.h, OutEvap_REF.h, outputs.outcomp_low_h, outputs.flash_liq_h, outputs.outexpand_high_h, outputs.incomp_high_h, InCond_REF.h, OutCond_REF.h, outputs.outexpand_high_h]
                p_points = [outputs.flash_liq_p, InEvap_REF.p, OutEvap_REF.p, outputs.outcomp_low_p, outputs.flash_liq_p, outputs.outexpand_high_p, outputs.incomp_high_p, InCond_REF.p, OutCond_REF.p, outputs.outexpand_high_p]
            else:
                s_points = [outputs.flash_liq_s, InEvap_REF.s, OutEvap_REF_svap, OutEvap_REF.s, outputs.outcomp_low_s, outcomp_low_svap, outputs.flash_liq_s, outputs.outexpand_high_s, outcomp_low_svap, outputs.incomp_high_s, InCond_REF.s]+cond_sarray+[OutCond_REF.s, outputs.outexpand_high_s] 
                T_points = [outputs.flash_liq_T, InEvap_REF.T, OutEvap_REF_Tvap, OutEvap_REF.T, outputs.outcomp_low_T, outcomp_low_Tvap, outputs.flash_liq_T, outputs.outexpand_high_T, outcomp_low_Tvap, outputs.incomp_high_T, InCond_REF.T]+outputs.cond_Tarray+[OutCond_REF.T, outputs.outexpand_high_T] 
                h_points = [outputs.flash_liq_h, InEvap_REF.h, OutEvap_REF.h, outputs.outcomp_low_h, outputs.flash_liq_h, outputs.outexpand_high_h, outputs.incomp_high_h, InCond_REF.h]+cond_harray+[OutCond_REF.h, outputs.outexpand_high_h]
                p_points = [outputs.flash_liq_p, InEvap_REF.p, OutEvap_REF.p, outputs.outcomp_low_p, outputs.flash_liq_p, outputs.outexpand_high_p, outputs.incomp_high_p, InCond_REF.p]+outputs.cond_parray+[OutCond_REF.p, outputs.outexpand_high_p]
        
        elif inputs.layout == 'part_cool':
            if inputs.cycle == 'vcc':
                pcx_cold_in_s = PropsSI("S","H",outputs.pcx_cold_in_h,"P",outputs.pcx_cold_in_p,OutCond_REF.fluidmixture)
                pcx_hot_out_s = PropsSI("S","H",outputs.pcx_hot_out_h,"P",outputs.pcx_hot_out_p,OutCond_REF.fluidmixture)
                incomp_s = PropsSI("S","H",outputs.incomp_h,"P",outputs.incomp_p,OutCond_REF.fluidmixture)
                
                s_points = [OutEvap_REF_svap, OutEvap_REF.s, InCond_REF.s, InCond_REF_svap, OutCond_REF_sliq, OutCond_REF.s, pcx_cold_in_s, OutCond_REF.s, pcx_hot_out_s, InEvap_REF.s, OutEvap_REF_svap, OutEvap_REF.s, incomp_s]
                T_points = [OutEvap_REF_Tvap, OutEvap_REF.T, InCond_REF.T, InCond_REF_Tvap, OutCond_REF_Tliq, OutCond_REF.T, outputs.pcx_cold_in_T, OutCond_REF.T, outputs.pcx_hot_out_T, InEvap_REF.T, OutEvap_REF_Tvap, OutEvap_REF.T, outputs.incomp_T]
                h_points = [OutEvap_REF.h, InCond_REF.h, OutCond_REF.h, outputs.pcx_cold_in_h, OutCond_REF.h, outputs.pcx_hot_out_h, InEvap_REF.h, OutEvap_REF.h, outputs.incomp_h]
                p_points = [OutEvap_REF.p, InCond_REF.p, OutCond_REF.p, outputs.pcx_cold_in_p, OutCond_REF.p, outputs.pcx_hot_out_p, InEvap_REF.p, OutEvap_REF.p, outputs.incomp_p]
        
        else:
            if inputs.cycle == 'vcc':
                s_points = [OutEvap_REF_svap, OutEvap_REF.s, InCond_REF.s, InCond_REF_svap, OutCond_REF_sliq, OutCond_REF.s, InEvap_REF.s, OutEvap_REF_svap]
                T_points = [OutEvap_REF_Tvap, OutEvap_REF.T, InCond_REF.T, InCond_REF_Tvap, OutCond_REF_Tliq, OutCond_REF.T, InEvap_REF.T, OutEvap_REF_Tvap]
                h_points = [OutEvap_REF.h, InCond_REF.h, OutCond_REF.h, InEvap_REF.h, OutEvap_REF.h]
                p_points = [OutEvap_REF.p, InCond_REF.p, OutCond_REF.p, InEvap_REF.p, OutEvap_REF.p]
            else:
                s_points = [OutEvap_REF_svap, OutEvap_REF.s, InCond_REF.s]+cond_sarray+[OutCond_REF.s, InEvap_REF.s, OutEvap_REF_svap]
                T_points = [OutEvap_REF_Tvap, OutEvap_REF.T, InCond_REF.T]+outputs.cond_Tarray+[OutCond_REF.T, InEvap_REF.T, OutEvap_REF_Tvap]
                h_points = [OutEvap_REF.h, InCond_REF.h]+cond_harray+[OutCond_REF.h, InEvap_REF.h, OutEvap_REF.h]
                p_points = [OutEvap_REF.p, InCond_REF.p]+outputs.cond_parray+[OutCond_REF.p, InEvap_REF.p, OutEvap_REF.p]
            
        
        
        return (p_points, h_points, T_points, s_points)
            
            
    def Post_Processing(self, InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs):
        print('---------------------------------------------------------------------------')
        print(f'Heating COP:{outputs.COP_heating:.3f}, Cooling COP:{outputs.COP_heating-1:.3f}')
        print(f'Refrigerant:{OutCond_REF.fluidmixture}')
        print(f'Q heating: {OutCond.q/1000:.3f} [kW] ({OutCond.q/3516.8525:.3f} [usRT])')
        print(f'Q cooling: {OutEvap_REF.q/1000:.3f} [kW] ({OutEvap_REF.q/3516.8525:.3f} [usRT])')
        print(f'Q comp: {outputs.Wcomp/1000:.3f} [kW]')
        if inputs.layout == 'ihx':
            print(f'Q IHX: {outputs.qihx/1000:.3f} [kW]')
        if inputs.layout == 'part_cool':
            print(f'Q PCX: {outputs.qpcx/1000:.3f} [kW]')
        print('---------------------------------------------------------------------------')
        if inputs.second == 'steam':
            print(f'Steam mass flow: {inputs.m_steam:.4f} [kg/s] ({inputs.m_steam*3.6:.2f} [ton/hr])')
        print('<Cond fluid:'+InCond.fluidmixture+'>')
        print(f'Tin:{InCond.T-273.15:.3f}[℃], Pin:{InCond.p/1.0e5:.3f}[bar], mdot:{InCond.m:.3f}[kg/s] -> Tout:{OutCond.T-273.15:.3f}[℃], Pout:{OutCond.p/1.0e5:.3f}[bar]')
        if InCond.fluidmixture == ('air' or 'Air'):
            InCond_rhum = HAPropsSI("R","T",InCond.T,"P",InCond.p,"W",InCond.ahum)
            InCond_Tdew = HAPropsSI("Tdp","T",InCond.T,"P",InCond.p,"W",InCond.ahum)
            InCond_Twet = HAPropsSI("B","T",InCond.T,"P",InCond.p,"W",InCond.ahum)
            OutCond_rhum = HAPropsSI("R","T",OutCond.T,"P",OutCond.p,"W",OutCond.ahum)
            OutCond_Tdew = HAPropsSI("Tdp","T",OutCond.T,"P",OutCond.p,"W",OutCond.ahum)
            OutCond_Twet = HAPropsSI("B","T",OutCond.T,"P",OutCond.p,"W",OutCond.ahum)
            print(f'Ahum:{InCond.ahum:.3e}[kg/kg], Rhum_in:{InCond_rhum*100:.3f}[%], Tdew_in:{InCond_Tdew-273.15:.3f}[℃], Twet_in:{InCond_Twet-273.15:.3f}[℃] -> R_Humid_out:{OutCond_rhum*100:.3f}[%], Tdew_out:{OutCond_Tdew-273.15:.3f}[℃], Twet_out:{OutCond_Twet-273.15:.3f}[℃]')
        print(' ')
        print('<Evap fluid:'+InEvap.fluidmixture+'>')
        print(f'Tin:{InEvap.T-273.15:.3f}[℃], Pin:{InEvap.p/1.0e5:.3f}[bar], mdot:{InEvap.m:.3f}[kg/s] -> Tout:{OutEvap.T-273.15:.3f}[℃], Pout:{OutEvap.p/1.0e5:.3f}[bar]')
        if InEvap.fluidmixture == ('air' or 'Air'):
            InEvap_rhum = HAPropsSI("R","T",InEvap.T,"P",InEvap.p,"W",InEvap.ahum)
            InEvap_Tdew = HAPropsSI("Tdp","T",InEvap.T,"P",InEvap.p,"W",InEvap.ahum)
            InEvap_Twet = HAPropsSI("B","T",InEvap.T,"P",InEvap.p,"W",InEvap.ahum)
            OutEvap_rhum = HAPropsSI("R","T",OutEvap.T,"P",OutEvap.p,"W",OutEvap.ahum)
            OutEvap_Tdew = HAPropsSI("Tdp","T",OutEvap.T,"P",OutEvap.p,"W",OutEvap.ahum)
            OutEvap_Twet = HAPropsSI("B","T",OutEvap.T,"P",OutEvap.p,"W",OutEvap.ahum)
            print(f'Ahum:{InEvap.ahum:.3e}[kg/kg], Rhum_in:{InEvap_rhum*100:.3f}[%], Tdew_in:{InEvap_Tdew-273.15:.3f}[℃], Twet_in:{InEvap_Twet-273.15:.3f}[℃] -> Rhum_out:{OutEvap_rhum*100:.3f}[%], Tdew_out:{OutEvap_Tdew-273.15:.3f}[℃], Twet_out:{OutEvap_Twet-273.15:.3f}[℃]')
        print('---------------------------------------------------------------------------')
        
        print(f'Tevap_out: {OutEvap_REF.T-273.15:.3f} [℃], Pevap_out: {OutEvap_REF.p/1.0e5:.3f} [bar], mevap_out {OutEvap_REF.m:.3f} [kg/s]')
        if inputs.layout == 'ihx':
            print(f'Tihx_cold_out: {outputs.ihx_cold_out_T-273.15:.3f} [℃], Pihx_cold_out: {outputs.ihx_cold_out_p/1.0e5:.3f} [bar], mihx_cold_out: {OutEvap_REF.m:.3f} [kg/s]')
        elif inputs.layout == 'part_cool':
            print(f'Tcomp_in: {outputs.incomp_T-273.15:.3f} [℃], Pcomp_in: {outputs.incomp_p/1.0e5:.3f} [bar], mcomp_in: {InCond_REF.m:.3f} [kg/s]')
        print(f'Tcond_in: {InCond_REF.T-273.15:.3f} [℃], Pcond_in: {InCond_REF.p/1.0e5:.3f} [bar], mcond_in {InCond_REF.m:.3f} [kg/s]')
        print(f'Tcond_out: {OutCond_REF.T-273.15:.3f} [℃], Pcond_out: {OutCond_REF.p/1.0e5:.3f} [bar], mcond_out {OutCond_REF.m:.3f} [kg/s]')
        if inputs.layout == 'ihx':
            print(f'Tihx_hot_out: {outputs.ihx_hot_out_T-273.15:.3f} [℃], Pihx_hot_out: {outputs.ihx_hot_out_p/1.0e5:.3f} [bar], mihx_hot_out: {OutCond_REF.m:.3f} [kg/s]')
        elif inputs.layout == 'part_cool':
            x_pcx_cold_in = PropsSI("Q","P",outputs.pcx_cold_in_p,"H",outputs.pcx_cold_in_h,OutCond_REF.fluidmixture)
            x_pcx_cold_out = PropsSI("Q","P",outputs.pcx_cold_out_p,"H",outputs.pcx_cold_out_h,OutCond_REF.fluidmixture)
            print(f'Tpcx_cold_in: {outputs.pcx_cold_in_T-273.15:.3f} [℃] (xpcx_cold_in: {x_pcx_cold_in:.3f}), Ppcx_cold_in: {outputs.pcx_cold_in_p/1.0e5:.3f} [bar], mpcx_cold_in: {OutCond_REF.m*inputs.pcx_frac:.3f} [kg/s]')
            print(f'Tpcx_cold_out: {outputs.pcx_cold_out_T-273.15:.3f} [℃] (xpcx_cold_out: {x_pcx_cold_out:.3f}), Ppcx_cold_out: {outputs.pcx_cold_out_p/1.0e5:.3f} [bar], mpcx_cold_out: {OutCond_REF.m*inputs.pcx_frac:.3f} [kg/s]')
            print(f'Tpcx_hot_out: {outputs.pcx_hot_out_T-273.15:.3f} [℃], Ppcx_hot_out: {outputs.pcx_hot_out_p/1.0e5:.3f} [bar], mpcx_hot_out: {OutCond_REF.m*(1-inputs.pcx_frac):.3f} [kg/s]')
            
        x_evap_in = PropsSI("Q","P",InEvap_REF.p,"H",InEvap_REF.h,InEvap_REF.fluidmixture)
        print(f'Tevap_in: {InEvap_REF.T-273.15:.3f} [℃] (xevap_in: {x_evap_in:.3f}), Pvalve_out: {InEvap_REF.p/1.0e5:.3f} [bar], mevap_in {InEvap_REF.m:.3f} [kg/s]')
        print(f'DSH_evap_out: {OutEvap_REF.T-PropsSI("T","Q",1.0,"P",OutEvap_REF.p,OutEvap_REF.fluidmixture):.3f} [℃], DSC_cond_out: {PropsSI("T","Q",0.0,"P",OutCond_REF.p,OutCond_REF.fluidmixture)-OutCond_REF.T:.3f} [℃]')
        if inputs.layout == 'ihx':
            print(f'DSH_ihx_cold_side: {outputs.ihx_cold_out_T-PropsSI("T","Q",1.0,"P",outputs.ihx_cold_out_p,OutEvap_REF.fluidmixture):.3f} [℃]')
            print(f'DSC_ihx_hot_side: {PropsSI("T","Q",0.0,"P",outputs.ihx_hot_out_p,OutCond_REF.fluidmixture)-outputs.ihx_hot_out_T:.3f} [℃]')
        elif inputs.layout == 'part_cool':
            print(f'DSC_pcx_hot_side: {PropsSI("T","Q",0.0,"P",outputs.pcx_hot_out_p,OutCond_REF.fluidmixture)-outputs.pcx_hot_out_T:.3f} [℃]')
            print(f'DSH_comp_in: {outputs.incomp_T-PropsSI("T","Q",1.0,"P",OutEvap_REF.p,OutEvap_REF.fluidmixture):.3f} [℃]')
        
        Tlow = PropsSI('T','P',0.5*(OutEvap_REF.p+InEvap_REF.p),'Q',0.5,OutEvap_REF.fluidmixture)
        try:
            Thigh = PropsSI('T','P',0.5*(OutCond_REF.p+InCond_REF.p),'Q',0.5,OutCond_REF.fluidmixture)
        except:
            Thigh = 0
        print(f'Ts_low: {Tlow-273.15:.3f} [℃], Ts_high: {Thigh-273.15:.3f} [℃], mdot: {OutEvap_REF.m:.3f}[kg/s]')
        if inputs.layout == 'inj' or inputs.layout == '2comp':
            print(f'T_inter: {outputs.incomp_high_T-273.15:.3f} [℃] / P_inter: {outputs.incomp_high_p/1.0e5:.3f} [bar]')
        print('---------------------------------------------------------------------------')
        print(f'Cond_UA: {outputs.cond_UA:.3f} [W/℃], Evap_UA: {outputs.evap_UA:.3f} [W/℃]')
        comp_in_d = PropsSI("D","T",OutEvap_REF.T,"P",OutEvap_REF.p,OutEvap_REF.fluidmixture)
        print(f'Vdis comp: {OutEvap_REF.m/comp_in_d*1.0e6/60:.3f}[cc/rev]')
        print('---------------------------------------------------------------------------')
        print(' ')
class VCHP_cascade(VCHP):
    def __init__(self, InCond, OutCond, InEvap, OutEvap, inputs_t, inputs_b):
        self.InCond = InCond
        self.OutCond = OutCond
        self.InEvap = InEvap
        self.OutEvap = OutEvap
        self.inputs_t = inputs_t
        self.inputs_b = inputs_b
        self.amb_P = 50000.0
    
    def __call__(self, opt_flag=1, evap_t_p_input=0):
        outputs_t = Outputs()
        outputs_b = Outputs()
        
        InCond_REF_t = ProcessFluid(Y=self.inputs_t.Y)
        OutCond_REF_t = ProcessFluid(Y=self.inputs_t.Y)
        InEvap_REF_t = ProcessFluid(Y=self.inputs_t.Y)
        OutEvap_REF_t = ProcessFluid(Y=self.inputs_t.Y)
        InCond_REF_b = ProcessFluid(Y=self.inputs_b.Y)
        OutCond_REF_b = ProcessFluid(Y=self.inputs_b.Y)
        InEvap_REF_b = ProcessFluid(Y=self.inputs_b.Y)
        OutEvap_REF_b = ProcessFluid(Y=self.inputs_b.Y)
        
        p_crit_t = PropsSI('PCRIT','',0,'',0,list(self.inputs_t.Y.keys())[0])
        T_crit_t = PropsSI('TCRIT','',0,'',0,list(self.inputs_t.Y.keys())[0])
        p_crit_b = PropsSI('PCRIT','',0,'',0,list(self.inputs_b.Y.keys())[0])
        T_crit_b = PropsSI('TCRIT','',0,'',0,list(self.inputs_b.Y.keys())[0])
        
        InCond_REF_t.p_crit = p_crit_t
        OutCond_REF_t.p_crit = p_crit_t
        InEvap_REF_t.p_crit = p_crit_t
        OutEvap_REF_t.p_crit = p_crit_t
        
        InCond_REF_t.T_crit = T_crit_t
        OutCond_REF_t.T_crit = T_crit_t
        InEvap_REF_t.T_crit = T_crit_t
        OutEvap_REF_t.T_crit = T_crit_t
        
        InCond_REF_b.p_crit = p_crit_b
        OutCond_REF_b.p_crit = p_crit_b
        InEvap_REF_b.p_crit = p_crit_b
        OutEvap_REF_b.p_crit = p_crit_b
        
        InCond_REF_b.T_crit = T_crit_b
        OutCond_REF_b.T_crit = T_crit_b
        InEvap_REF_b.T_crit = T_crit_b
        OutEvap_REF_b.T_crit = T_crit_b
        
        cond_t_ph = 0
        evap_b_ph = 0
        
        (self.InCond, self.OutCond, self.InEvap, self.OutEvap, no_input) = super().Input_Processing(self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.inputs_t)
        if opt_flag == 1:
            (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF_t, self.OutCond_REF_t, self.InEvap_REF_t, self.OutEvap_REF_t, self.InCond_REF_b, self.OutCond_REF_b, self.InEvap_REF_b, self.OutEvap_REF_b, outputs_t, outputs_b) = self.Cascade_opt(self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, self.inputs_t, self.inputs_b, outputs_t, outputs_b, no_input, cond_t_ph, evap_b_ph)    
        else:
            (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF_t, self.OutCond_REF_t, self.InEvap_REF_t, self.OutEvap_REF_t, self.InCond_REF_b, self.OutCond_REF_b, self.InEvap_REF_b, self.OutEvap_REF_b, outputs_t, outputs_b) = self.Cascade_solver(self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, self.inputs_t, self.inputs_b, outputs_t, outputs_b, no_input, cond_t_ph, evap_b_ph, evap_t_p_input)
        
        return (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF_t, self.OutCond_REF_t, self.InEvap_REF_t, self.OutEvap_REF_t, self.InCond_REF_b, self.OutCond_REF_b, self.InEvap_REF_b, self.OutEvap_REF_b, outputs_t, outputs_b)
        
        
    def Cascade_opt(self, InCond, OutCond, InEvap, OutEvap, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, inputs_t, inputs_b, outputs_t, outputs_b, no_input, cond_t_ph, evap_b_ph):
        
        evap_t_p_ub = PropsSI('P','T',OutCond_REF_b.T_crit,'Q',0.0, OutEvap_REF_t.fluidmixture)
        evap_t_p_lb = self.amb_P
        
        cascade_a = 1
        results_array = []
        devap = 0.005
        while cascade_a:
            for ii in range(2):
                if ii == 0:
                    evap_t_p_input = 0.5*(evap_t_p_ub+evap_t_p_lb)*(1-devap)
                else:
                    evap_t_p_input = 0.5*(evap_t_p_ub+evap_t_p_lb)*(1+devap)
                    
                (InCond, OutCond, InEvap, OutEvap, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, outputs_t, outputs_b) = self.Cascade_solver(InCond, OutCond, InEvap, OutEvap, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, inputs_t, inputs_b, outputs_t, outputs_b, no_input, cond_t_ph, evap_b_ph, evap_t_p_input)
                
                outputs_t.COP_heating = OutCond.q/(outputs_t.Wcomp - outputs_t.Wexpand)
                
                COP_cascade = OutCond.q/(outputs_t.Wcomp - outputs_t.Wexpand + outputs_b.Wcomp - outputs_b.Wexpand)
                
                if ii == 0:
                    COP_o = COP_cascade
                    OutEvap_REF_t_po = OutEvap_REF_t.p
                else:
                    dCOP = ((COP_cascade - COP_o)/COP_cascade)/((OutEvap_REF_t.p - OutEvap_REF_t_po)/OutEvap_REF_t.p)
                    if dCOP > 0:
                        evap_t_p_lb = OutEvap_REF_t.p
                    else:
                        evap_t_p_ub = OutEvap_REF_t.p
                        
                    results_array.append([0.5*(COP_o + COP_cascade), 0.5*(OutEvap_REF_t_po + OutEvap_REF_t.p), dCOP])
                    
                    if len(results_array) > 2:
                        if results_array[-2][0] > results_array[-1][0] and results_array[-2][0] > results_array[-3][0]:
                            COP_cascade = results_array[-2][0]
                            OutEvap_REF_t.p = results_array[-1][1]
                            cascade_a = 0
                        elif abs(results_array[-1][2]) < inputs_t.tol:
                            COP_cascade = results_array[-1][0]
                            OutEvap_REF_t.p = results_array[-1][1]
                            cascade_a = 0
                        elif abs(results_array[-1][1] - results_array[-2][1]) < 1.0:
                            OutEvap_REF_t.p = results_array[-1][1]
                            cascade_a = 0
                    
                    if evap_t_p_ub - evap_t_p_lb < 1.0e3: 
                        COP_cascade = results_array[-1][0]
                        OutEvap_REF_t.p = results_array[-1][1]
                        cascade_a = 0
                    
                    InEvap_REF_t.p = OutEvap_REF_t.p+inputs_t.evap_dp
        
        return(InCond, OutCond, InEvap, OutEvap, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, outputs_t, outputs_b)
    
    def Cascade_solver(self, InCond, OutCond, InEvap, OutEvap, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, inputs_t, inputs_b, outputs_t, outputs_b, no_input, cond_t_ph, evap_b_ph, evap_t_p_input):
        cond_b_ph = 1
        
        OutEvap_REF_t.p = evap_t_p_input
        InEvap_REF_t.p = OutEvap_REF_t.p+inputs_t.evap_dp
        
        OutEvap_REF_t_Tvap = PropsSI('T','P',OutEvap_REF_t.p, 'Q', 1.0, OutEvap_REF_t.fluidmixture)
        OutEvap_REF_t.T = OutEvap_REF_t_Tvap + inputs_t.DSH
        if inputs_t.DSH == 0:
            OutEvap_REF_t.h = PropsSI('H','P',OutEvap_REF_t.p, 'Q', 1.0, OutEvap_REF_t.fluidmixture)
            OutEvap_REF_t.s = PropsSI('S','P',OutEvap_REF_t.p, 'Q', 1.0, OutEvap_REF_t.fluidmixture)
        else:
            OutEvap_REF_t.h = PropsSI('H','T',OutEvap_REF_t.T, 'P', OutEvap_REF_t.p ,OutEvap_REF_t.fluidmixture)
            OutEvap_REF_t.s = PropsSI('S','T',OutEvap_REF_t.T, 'P', OutEvap_REF_t.p ,OutEvap_REF_t.fluidmixture)
            
        if (no_input == 'InEvapT') or (no_input == 'OutEvapT') or (no_input == 'Evapm'):
            (InCond, OutCond, InEvap_dummy, OutEvap_dummy, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, outputs_t) = super().HighPressure_Solver(InCond, OutCond, InEvap, OutEvap, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, inputs_t, outputs_t, no_input, cond_t_ph)
            (InEvap_REF_t, OutEvap_REF_t, InEvap, OutEvap, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, outputs_b) = super().Cycle_Solver(InEvap_REF_t, OutEvap_REF_t, InEvap, OutEvap, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, inputs_b, outputs_b, no_input, cond_b_ph, evap_b_ph)
                
        elif (no_input == 'InCondT') or (no_input == 'OutCondT') or (no_input == 'Condm'):
            if inputs_t.cycle == 'scc':
                cond_p_ub = min(5*InCond_REF_t.p_crit, 1.0e8)
                cond_p_lb = InCond_REF_t.p_crit
            else:
                cond_p_ub = InCond_REF_t.p_crit
                if no_input == 'InCondT':
                    cond_p_lb = PropsSI('P','T',OutCond.T,'Q',1.0,OutCond_REF_t.fluidmixture)
                else:
                    cond_p_lb = PropsSI('P','T',InCond.T,'Q',1.0,OutCond_REF_t.fluidmixture)
            
            cond_a_t = 1
            while cond_a_t:
                (InCond_REF_t, OutCond_REF_t, InEvap_REF_t, outputs_t) = self.TopCycle_HighPressure_solver(cond_p_lb, cond_p_ub, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, inputs_t, outputs_t)
                (InEvap_REF_t, OutEvap_REF_t, InEvap, OutEvap, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, outputs_b) = super().Cycle_Solver(InEvap_REF_t, OutEvap_REF_t, InEvap, OutEvap, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, inputs_b, outputs_b, 'Condm', cond_b_ph, evap_b_ph)
                
                InCond_REF_t.m = InEvap_REF_t.m
                OutCond_REF_t.m = InEvap_REF_t.m
                OutCond_REF_t.q = (OutCond_REF_t.h - InCond_REF_t.h)*OutCond_REF_t.m
                InCond_REF_t.q = OutCond_REF_t.q
                OutCond.q = -OutCond_REF_t.q
                InCond.q = -OutCond_REF_t.q
                
                outputs_t.Wcomp = outputs_t.Wcomp*InCond_REF_t.m
                outputs_t.Wexpand = outputs_t.Wexpand*InEvap_REF_t.m
                
                if no_input == 'InCondT':
                    InCond.h = OutCond.h - OutCond.q/OutCond.m
                    if InCond.fluidmixture == ('air' or 'Air'):
                        InCond.T = HAPropsSI('T','P',InCond.p, 'H', InCond.h, 'W', InCond.ahum)
                        InCond.Cp = HAPropsSI('C','T',InCond.T, 'P', InCond.p, 'W', InCond.ahum)
                    else:    
                        InCond.T = PropsSI('T','P',InCond.p, 'H', InCond.h, InCond.fluidmixture)
                        InCond.Cp = PropsSI('C','T',InCond.T, 'P', InCond.p, InCond.fluidmixture)
                elif no_input == 'OutCondT':
                    OutCond.h = InCond.h + InCond.q/InCond.m
                    if OutCond.fluidmixture == ('air' or 'Air'):
                        OutCond.T = HAPropsSI('T','P',OutCond.p, 'H', OutCond.h, 'W', OutCond.ahum)
                        OutCond.Cp = HAPropsSI('C','T',OutCond.T, 'P', OutCond.p, 'W', OutCond.ahum)
                    else:
                        OutCond.T = PropsSI('T','P',OutCond.p, 'H', OutCond.h, OutCond.fluidmixture)
                        OutCond.Cp = PropsSI('C','T',OutCond.T, 'P', OutCond.p, OutCond.fluidmixture)
                elif no_input == 'Condm':
                    InCond.m = InCond.q/(OutCond.h - InCond.h)
                    OutCond.m = InCond.m

                cond_t = HX.Heatexchanger_module(InCond_REF_t, OutCond_REF_t, 1, InCond, OutCond, cond_t_ph)
                
                if inputs_t.cond_type == 'fthe':
                    (outputs_t.cond_Tarray, outputs_t.cond_parray) = cond_t.FTHE(N_element=inputs_t.cond_N_element, N_turn = inputs_t.cond_N_turn, N_row = inputs_t.cond_N_row)
                    cond_err = (inputs_t.cond_T_lm - cond_t.T_lm)/inputs_t.cond_T_lm
                    
                elif inputs_t.cond_type == 'phe':
                    (outputs_t.cond_Tarray, outputs_t.cond_parray) = cond_t.PHE(N_element=inputs_t.cond_N_element)
                    cond_err = (inputs_t.cond_T_pp - cond_t.T_pp)/inputs_t.cond_T_pp
                
                OutCond_REF_t = cond_t.primary_out
                
                if cond_t.T_rvs == 1:
                    cond_p_lb = InCond_REF_t.p
                else:
                    if cond_err < 0:
                        cond_p_ub = InCond_REF_t.p
                    else:
                        cond_p_lb = InCond_REF_t.p
                
                if abs(cond_err) < inputs_t.tol:
                    cond_conv_err = 0
                    cond_a_t = 0
                elif cond_p_ub - cond_p_lb < inputs_t.tol:
                    cond_conv_err = 1
                    cond_a_t = 0
            
        outputs_t.COP_heating = OutCond.q/(outputs_t.Wcomp - outputs_t.Wexpand)
        outputs_t.DSH = OutEvap_REF_t.T - OutEvap_REF_t_Tvap
        
        return(InCond, OutCond, InEvap, OutEvap, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, outputs_t, outputs_b)
    
    
    def TopCycle_HighPressure_solver(self, cond_p_lb, cond_p_ub, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs):
        
        InCond_REF.p = 0.5*(cond_p_ub+cond_p_lb)
        OutCond_REF.p = InCond_REF.p-inputs.cond_dp
        
        if OutCond_REF.p > OutCond_REF.p_crit:
            OutCond_REF.T = 0.10753154*((OutCond_REF.p - OutCond_REF.p_crit)/OutCond_REF.p_crit) + 0.004627621995008088
            OutCond_REF.T = OutCond_REF.T*OutCond_REF.T_crit + OutCond_REF.T_crit - inputs.DSC
            OutCond_REF.h = PropsSI('H','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
            if inputs.expand_eff > 0.0:
                OutCond_REF.s = PropsSI('S','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
        else:
            OutCond_REF.T = PropsSI('T','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture) - inputs.DSC
            if inputs.DSC == 0:
                OutCond_REF.h = PropsSI('H','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture)
                if inputs.expand_eff > 0.0:
                    OutCond_REF.s = PropsSI('S','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture)
            else:
                OutCond_REF.h = PropsSI('H','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
                if inputs.expand_eff > 0.0:
                    OutCond_REF.s = PropsSI('S','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
        
        if inputs.layout == 'ihx':
            InComp = deepcopy(OutEvap_REF)
            InComp.p = InComp.p-inputs.ihx_cold_dp
            InExpand = deepcopy(OutCond_REF)
            InExpand.p = InExpand.p-inputs.ihx_hot_dp
            IHX = HX.Heatexchanger_module(OutCond_REF, InExpand, 0, OutEvap_REF, InComp, 0)
            IHX.SIMPHX(eff_HX = inputs.ihx_eff)
        
            InExpand = IHX.primary_out
            InComp = IHX.secondary_out
        else:    
            InComp = OutEvap_REF
            InExpand = OutCond_REF
            
        comp = CP.Compander_module(InComp, InCond_REF)
        (inputs.DSH, cond_a) = comp.COMP(eff_isen = inputs.comp_eff, DSH = inputs.DSH)
        InCond_REF = comp.primary_out
        
        
        expand = CP.Compander_module(InExpand, InEvap_REF)
        expand.EXPAND(eff_isen = inputs.expand_eff)
        InEvap_REF = expand.primary_out
            
        if inputs.layout == 'ihx':
            outputs.qihx = (InComp.h - OutEvap_REF.h)*OutEvap_REF.m
            outputs.ihx_hot_out_T = InExpand.T
            outputs.ihx_hot_out_p = InExpand.p
            outputs.ihx_hot_out_h = InExpand.h
            outputs.ihx_hot_out_s = InExpand.s
            outputs.ihx_cold_out_T = InComp.T
            outputs.ihx_cold_out_p = InComp.p
            outputs.ihx_cold_out_h = InComp.h
            outputs.ihx_cold_out_s = InComp.s
            
        outputs.Wcomp = comp.Pspecific
        outputs.Wcomp /= inputs.mech_eff
        outputs.Wexpand = expand.Pspecific
        outputs.Wexpand *= inputs.mech_eff
        
        return (InCond_REF, OutCond_REF, InEvap_REF, outputs)
    
    def Plot_diagram(self, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, inputs_t, outputs_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, inputs_b, outputs_b, ts_file, ph_file, coeff = 1.0):
        (p_array_t, h_array_t, T_array_t, s_array_t) = super().Dome_Draw(InCond_REF_t.fluidmixture, coeff)
        (p_array_b, h_array_b, T_array_b, s_array_b) = super().Dome_Draw(InCond_REF_b.fluidmixture, coeff)
        (p_points_t, h_points_t, T_points_t, s_points_t) = super().Diagram_Draw(InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, inputs_t, outputs_t)
        (p_points_b, h_points_b, T_points_b, s_points_b) = super().Diagram_Draw(InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, inputs_b, outputs_b)
        
        fig_ph, ax_ph = PLT.subplots()
        ax_ph.plot([i/1.0e3 for i in h_array_t], [i/1.0e5 for i in p_array_t],'r--')
        ax_ph.plot([i/1.0e3 for i in h_array_b], [i/1.0e5 for i in p_array_b],'b--')
        ax_ph.set_xlabel('Enthalpy [kJ/kg]',fontsize = 15)
        ax_ph.set_ylabel('Pressure [bar]',fontsize = 15)
        ax_ph.set_title('Pressure-Enthalpy Diagram\nRefrigerant [Top:{} / Bot:{}] )'.format(list(inputs_t.Y.keys())[0], list(inputs_b.Y.keys())[0]),fontsize = 18)
        ax_ph.tick_params(axis = 'x', labelsize = 13)
        ax_ph.tick_params(axis = 'y', labelsize = 13)
        
        fig_ts, ax_ts = PLT.subplots()
        ax_ts.plot([i/1.0e3 for i in s_array_t], [i-273.15 for i in T_array_t])
        ax_ts.plot([i/1.0e3 for i in s_array_b], [i-273.15 for i in T_array_b])
        ax_ts.set_xlabel('Entropy [kJ/kg-K]',fontsize = 15)
        ax_ts.set_ylabel('Temperature [℃]',fontsize = 15)
        ax_ts.set_title('Temperature-Entropy Diagram\nRefrigerant [Top:{} / Bot:{}]'.format(list(inputs_t.Y.keys())[0], list(inputs_b.Y.keys())[0],),fontsize = 18)
        ax_ts.tick_params(axis = 'x', labelsize = 13)
        ax_ts.tick_params(axis = 'y', labelsize = 13)
        
        ax_ts.plot([i/1.0e3 for i in s_points_t], [i-273.15 for i in T_points_t],'ro-')
        ax_ts.plot([i/1.0e3 for i in s_points_b], [i-273.15 for i in T_points_b],'bo-')
        ax_ph.plot([i/1.0e3 for i in h_points_t], [i/1.0e5 for i in p_points_t],'ro-')
        ax_ph.plot([i/1.0e3 for i in h_points_b], [i/1.0e5 for i in p_points_b],'bo-')
        
        fig_ph.savefig(ph_file+'.png',dpi=300)
        fig_ts.savefig(ts_file+'.png',dpi=300)
        
    def Post_Processing(self, InCond, OutCond, InEvap, OutEvap, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, inputs_t, outputs_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, inputs_b, outputs_b):
        print('')
        print('<<<<<  Top Cycle  >>>>>>')
        super().Post_Processing(InCond, OutCond, InCond_REF_b, OutCond_REF_b, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, inputs_t, outputs_t)
        
        print('<<<<<  Bottom Cycle  >>>>>')
        super().Post_Processing(InEvap_REF_t, OutEvap_REF_t, InEvap, OutEvap, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, inputs_b, outputs_b)
        COP_cascade = (self.OutCond.q)/(outputs_t.Wcomp - outputs_t.Wexpand + outputs_b.Wcomp - outputs_b.Wexpand)
        print('Combination COP:{:.3f}'.format(COP_cascade))
        print('')

if __name__ == '__main__':
    
    evapfluid = 'water'
    inevap_T = 12.0+273.15
    inevap_p = 167000

    outevap_T = 0
    outevap_p = 165000
    
    #evap_v = 339.844
    #evap_m = evap_v*PropsSI("D","T",inevap_T,"P",inevap_p,evapfluid)/1000/60
    evap_m = 1.0
    
    InEvap = ProcessFluid(Y={evapfluid:1.0,},m = evap_m, T = inevap_T, p = inevap_p)
    OutEvap = ProcessFluid(Y={evapfluid:1.0,},m = evap_m, T = outevap_T, p = outevap_p)
    
    condfluid = 'Water'

    incond_T = 45.0 + 273.15
    incond_p = 236000
    
    outcond_T = 50.0 + 273.15
    outcond_p = 215000
    
    #cond_v = 429.641
    #cond_m = cond_v*PropsSI("D","T",incond_T,"P",incond_p,condfluid)/1000/60
    cond_m = 1.0
    
    InCond = ProcessFluid(Y={condfluid:1.0,},m = cond_m, T = incond_T, p = incond_p)
    OutCond = ProcessFluid(Y={condfluid:1.0,},m = cond_m, T = outcond_T, p = outcond_p)
    
    inputs = Settings()
    inputs.Y = {'R134a':1.0,}
    inputs.second = 'process'
    inputs.cycle = 'vcc'
    inputs.DSC = 1.0
    inputs.DSH = 10.0
    inputs.cond_type = 'phe'
    inputs.cond_dp = 30.0e3
    inputs.cond_T_pp = 2.0
    inputs.cond_N_element = 30
    inputs.evap_type = 'phe'
    inputs.evap_dp = 15.0e3
    inputs.evap_T_pp = 2.0
    inputs.evap_N_element = 30
    inputs.layout = 'inj'
    
    inputs.comp_eff = 0.7
    inputs.mech_eff = 0.95
    
    vchp_basic = VCHP(InCond, OutCond, InEvap, OutEvap, inputs)    
    (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs)=vchp_basic()
    vchp_basic.Post_Processing(InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs)
    '''
    evapfluid = 'water'
    inevapT = 70.0+273.15
    inevapp = 101300
    evapm = 0
    InEvap = ProcessFluid(Y={evapfluid:1.0,},m = evapm, T = inevapT, p = inevapp)
    
    outevapT = 65.0+273.15
    outevapp = 101300
    OutEvap = ProcessFluid(Y={evapfluid:1.0,},m = evapm, T = outevapT, p = outevapp)
    
    condfluid = 'air'

    incond_T = 59.4+273.15
    incond_p = 101300
    incond_hum = 0.068
    incond_ahum = HAPropsSI("W","T",incond_T,"P",incond_p,"R",incond_hum)
    
    outcond_T = 120+273.15
    outcond_p = 101300
    outcond_hum = 0.007
    outcond_ahum = incond_ahum
    
    cond_cmh = 36000
    
    d_hum_cond = HAPropsSI("Vha","T",incond_T, "P", incond_p, "W", incond_ahum)
    cond_m = cond_cmh/3600*d_hum_cond
    
    InCond = ProcessFluid(Y={condfluid:1.0,},m = cond_m, T = incond_T, p = incond_p, ahum=incond_ahum)
    OutCond = ProcessFluid(Y={condfluid:1.0,},m = cond_m, T = outcond_T, p = outcond_p, ahum=outcond_ahum)
    
    inputs = Settings()
    inputs.Y = {'REFPROP::R1233zd(E)':1.0,}
    inputs.second = 'process'
    inputs.cycle = 'vcc' 
    
    inputs.DSH = 8.0
    inputs.DSC = 1.0
    inputs.cond_dp = 0.01
    inputs.evap_dp = 0.01
    inputs.evap_type = 'phe'
    inputs.cond_type = 'fthe'
    inputs.evap_T_pp = 0.1
    inputs.cond_T_lm = 25.0
    inputs.cond_N_row = 5
    inputs.cond_N_turn = 5
    inputs.layout = 'bas'
    inputs.comp_eff = 0.75
    
    bas = VCHP(InCond, OutCond, InEvap, OutEvap, inputs)
    (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs) = bas()
    bas.Post_Processing(InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs)
    a = 0
    
    
    evapfluid = 'air'
    inevap_T = 25.1+273.15
    inevap_p = 103000
    inevap_hum = 0.024
    inevap_ahum = HAPropsSI("W","T",inevap_T,"P",inevap_p,"R",inevap_hum)

    outevap_T = 0
    outevap_p = 101300
    outevap_ahum = inevap_ahum
    
    evap_cmh = 36000

    d_hum_evap = HAPropsSI("Vha","T",inevap_T, "P", inevap_p, "R", inevap_hum)
    evap_m = evap_cmh/3600*d_hum_evap

    InEvap = ProcessFluid(Y={evapfluid:1.0,},m = evap_m, T = inevap_T, p = inevap_p, ahum = inevap_ahum)
    OutEvap = ProcessFluid(Y={evapfluid:1.0,},m = evap_m, T = outevap_T, p = outevap_p, ahum = outevap_ahum)
    
    condfluid = 'water'
    incondT = 65.0+273.15
    incondp = 101300
    condm = InEvap.m
    InCond = ProcessFluid(Y={condfluid:1.0,},m = condm, T = incondT, p = incondp)
    
    outcondT = 70.0+273.15
    outcondp = 101300
    OutCond = ProcessFluid(Y={condfluid:1.0,},m = condm, T = outcondT, p = outcondp)
    
    inputs = Settings()
    inputs.Y = {'REFPROP::R513a.mix':1.0,}
    inputs.second = 'process'
    inputs.cycle = 'vcc' 
    
    inputs.DSH = 5.0    
    inputs.DSC = 1.0
    inputs.evap_dp = 0.01
    inputs.evap_type = 'fthe'
    inputs.evap_T_lm = 10.0
    inputs.evap_N_row = 5
    inputs.evap_N_turn = 5
    inputs.cond_dp = 0.01
    inputs.cond_type = 'phe'
    inputs.cond_T_pp = 0.1
    
    inputs.layout = 'bas'
    inputs.comp_eff = 0.75
    
    bas = VCHP(InCond, OutCond, InEvap, OutEvap, inputs)
    (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs) = bas()
    bas.Post_Processing(InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs)
    a = 0
    '''

    '''
    evapfluid = 'water'
    inevapT = 70.0+273.15
    inevapp = 101300.0
    evapm = 10.345
    InEvap = ProcessFluid(Y={evapfluid:1.0,},m = evapm, T = inevapT, p = inevapp)
    
    outevapT = 0.0
    outevapp = 101300.0
    OutEvap = ProcessFluid(Y={evapfluid:1.0,},m = evapm, T = outevapT, p = outevapp)
    
    condfluid = 'water'
    incondT = 0.0
    incondp = 0.0
    condm = 0.0
    InCond = ProcessFluid(Y={condfluid:1.0,},m = condm, T = incondT, p = incondp)
    
    outcondT = 125.0 + 273.15
    outcondp = 0.0
    OutCond = ProcessFluid(Y={condfluid:1.0,},m = condm, T = outcondT, p = outcondp)
    
    
    inputs = Settings()
    inputs.Y = {'R245fa':1.0,}
    inputs.second = 'steam'
    inputs.T_steam = 120.0 + 273.15
    inputs.m_steam = 0.1153
    inputs.T_makeup = 25.0 + 273.15
    inputs.m_makeup = inputs.m_steam
    inputs.cycle = 'vcc'
    inputs.DSC = 6.0
    inputs.DSH = 1.0    
    inputs.cond_dp = 0.0
    inputs.evap_dp = 0.0
    inputs.cond_type = 'phe'
    inputs.evap_type = 'phe'
    inputs.layout = 'ihx'
    inputs.cond_T_pp = 5.0
    inputs.evap_T_pp = 5.0
    inputs.ihx_eff = 0.61617
    inputs.ihx_cold_dp = 0.0
    inputs.ihx_hot_dp = 0.0
    
    inputs.comp_eff = 0.8
    
    steam_ihx = VCHP(InCond, OutCond, InEvap, OutEvap, inputs)
    steam_ihx()
    a = 0
    '''
    '''
    COP_list = []
    evapUA_list = []
    condUA_list = []
    comp_list = [0.7, 0.71, 0.72, 0.73, 0.74, 0.75]
    cond_list = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    evap_list = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    for comp in comp_list:
        COP_list_c = []
        evapUA_list_c = []
        condUA_list_c = []
        for cond in cond_list:
            COP_list_e = []
            evapUA_list_e = []
            condUA_list_e = []
            for evap in evap_list:
                try:
                    inputs.comp_eff = comp
                    inputs.cond_T_pp = cond
                    inputs.evap_T_pp = evap
                    OutCond = ProcessFluid(Y={condfluid:1.0,},m = 0.195, p = outcondp)
                    vchp_basic = VCHP(InCond, OutCond, InEvap, OutEvap, inputs)
                    (a, b, c, d, outputs) = vchp_basic()
                    COP = outputs.COP_heating - 1
                except:
                    COP = 0.0
                    outputs.evap_UA = 0.0
                    outputs.cond_UA = 0.0
                
                COP_list_e.append(COP)
                evapUA_list_e.append(outputs.evap_UA)
                condUA_list_e.append(outputs.cond_UA)
                
            COP_list_c.append(COP_list_e)
            evapUA_list_c.append(evapUA_list_e)
            condUA_list_c.append(condUA_list_e)
        
        COP_list.append(COP_list_c)
        evapUA_list.append(evapUA_list_c)
        condUA_list.append(condUA_list_c)


    print(COP_list)
    print(evapUA_list)
    print(condUA_list)
    
    
    evapfluid = 'water'
    inevapT = 285.15
    inevapp = 101300.0
    InEvap = ProcessFluid(Y={evapfluid:1.0,},m = 1.0, T = inevapT, p = inevapp)
    
    outevapT = 280.15
    outevapp = 101300.0
    OutEvap = ProcessFluid(Y={evapfluid:1.0,},p = outevapp)
    
    condfluid = 'water'
    incondT = 305.15
    incondp = 101300.0
    InCond = ProcessFluid(Y={condfluid:1.0,},m = 1.0, T = incondT, p = incondp)
    
    outcondT = 311.15
    outcondp = 101300.0
    OutCond = ProcessFluid(Y={condfluid:1.0,},m = 1.0, T =outcondT, p = outcondp)
    
    inputs = Settings()
    inputs.Y = {'R410A':1.0,}
    inputs.second = 'process'
    inputs.cycle = 'vcc'
    inputs.DSC = 5.0
    inputs.cond_type = 'phe'
    inputs.evap_type = 'phe'
    inputs.layout = 'inj'
    
    
    vchp_basic = VCHP(InCond, OutCond, InEvap, OutEvap, inputs)
    vchp_basic()
    
    evapfluid = 'water'
    inevapT = 280.15
    inevapp = 101300.0
    InEvap = ProcessFluid(Y={evapfluid:1.0,},m = 0.0, T = inevapT, p = inevapp)
    
    outevapT = 275.15
    outevapp = 101300.0
    OutEvap = ProcessFluid(Y={evapfluid:1.0,})
    
    condfluid = 'water'
    incondT = 313.15
    incondp = 101300.0
    InCond = ProcessFluid(Y={condfluid:1.0,},m = 1.0, T = incondT, p = incondp)
    
    outcondT = 318.15
    outcondp = 101300.0
    OutCond = ProcessFluid(Y={condfluid:1.0,},T=outcondT)
    
    inputs_t = Settings()
    inputs_t.Y = {'R245FA':1.0,}
    inputs_t.second = 'process'
    inputs_t.cycle = 'vcc'
    inputs_t.cond_type = 'phe'
    inputs_t.evap_type = 'phe'
    inputs_t.layout = 'bas'
    
    inputs_b = Settings()
    inputs_b.Y = {'R32':1.0,}
    inputs_b.second = 'process'
    inputs_b.cycle = 'scc'
    inputs_b.cond_type = 'phe'
    inputs_b.evap_type = 'phe'
    inputs_b.layout = 'bas'
    
    vchp_cascade = VCHP_cascade(InCond, OutCond, InEvap, OutEvap, inputs_t, inputs_b)

    from cProfile import Profile
    
    profiler = Profile()
    profiler.run('vchp_basic()')
    
    from pstats import Stats
    
    stats = Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats('cumulative')
    stats.print_stats()
    '''
    
    '''
    # 한도외 사이클 입력
    
    purpose = 'summer'
    
    inputs_t = Settings()
    inputs_t.Y = {'R1234ze(E)':1.0,}
    inputs_t.second = 'process'
    inputs_t.cycle = 'vcc'
    inputs_t.cond_type = 'phe'
    inputs_t.evap_type = 'phe'
    inputs_t.layout = 'bas'
    
    inputs_b = Settings()
    inputs_b.Y = {'R1234yf':1.0,}
    inputs_b.second = 'process'
    inputs_b.cycle = 'vcc'
    inputs_b.cond_type = 'phe'
    inputs_b.evap_type = 'phe'
    inputs_b.layout = 'bas'
    inputs_b.comp_eff = 0.72
        
    if purpose == 'winter':
            
        evapfluid = 'water'
        inevapT = 298.15
        inevapp = 101300.0
        evapm = 0.0
        InEvap = ProcessFluid(Y={evapfluid:1.0,},m=evapm, T = inevapT, p = inevapp)
        
        outevapT = 293.15
        outevapp = 101300.0
        OutEvap = ProcessFluid(Y={evapfluid:1.0,},m=evapm, T = outevapT, p = outevapp)
        
        condfluid = 'water'
        incondT_space = 313.15
        incondp_space = 101300.0
        m_space = 0.169
        InCond_space = ProcessFluid(Y={condfluid:1.0,},m = m_space, T = incondT_space, p = incondp_space)
        
        outcondT_space = 318.15
        outcondp_space = 101300.0
        OutCond_space = ProcessFluid(Y={condfluid:1.0,},m = m_space, T=outcondT_space, p=outcondp_space)
        
        incondT_water = 338.15
        incondp_water = 101300.0
        m_water = 0.069922077
        InCond_water = ProcessFluid(Y={condfluid:1.0,},m = m_water, T = incondT_water, p = incondp_water)
        
        outcondT_water = 343.15
        outcondp_water = 101300.0
        OutCond_water = ProcessFluid(Y={condfluid:1.0,},m = m_water, T=outcondT_water, p=outcondp_water)
        inputs_t.comp_eff = 0.74
        inputs_b.comp_eff = 0.74
        
    elif purpose == 'hotwater':
        evapfluid = 'water'
        inevapT = 298.15
        inevapp = 101300.0
        evapm = 0.0
        InEvap = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = inevapT, p = inevapp)
        
        outevapT = 293.15
        outevapp = 101300.0
        OutEvap = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = outevapT, p = outevapp)
        
        condfluid = 'water'
        
        incondT = 338.15
        incondp = 101300.0
        condm = 0.069922077
        InCond = ProcessFluid(Y={condfluid:1.0,},m = condm, T = incondT, p = incondp)
        
        outcondT = 343.15
        outcondp = 101300.0
        OutCond = ProcessFluid(Y={condfluid:1.0,},m = condm, T=outcondT, p=outcondp)
        inputs_t.comp_eff = 0.8
        inputs_b.comp_eff = 0.74
    else:
        evapfluid = 'water'
        inevapT = 285.15
        inevapp = 101300.0
        evapm = 0.0
        InEvap = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = inevapT, p = inevapp)
        
        outevapT = 280.15
        outevapp = 101300.0
        OutEvap = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = outevapT, p = outevapp)
        
        condfluid = 'water'
        incondT_space = 298.15
        incondp_space = 101300.0
        condm = 0.154
        InCond_space = ProcessFluid(Y={condfluid:1.0,},m = condm, T = incondT_space, p = incondp_space)
        
        outcondT_space = 303.15
        outcondp_space = 101300.0
        OutCond_space = ProcessFluid(Y={condfluid:1.0,},m = condm, T=outcondT_space, p=outcondp_space)
        
        incondT_water = 338.15
        incondp_water = 101300.0
        m_water = 0.069922077
        InCond_water = ProcessFluid(Y={condfluid:1.0,},m = m_water, T = incondT_water, p = incondp_water)
        
        outcondT_water = 343.15
        outcondp_water = 101300.0
        OutCond_water = ProcessFluid(Y={condfluid:1.0,},m = m_water, T=outcondT_water, p=outcondp_water)
        
        inputs_t.comp_eff = 0.8
        inputs_b.comp_eff = 0.63
    
        
    vchp_hando = VCHP_cascade(InCond, OutCond, InEvap, OutEvap, inputs_t, inputs_b)
    vchp_hando()
    
   
    
    weather_list = [308.15, 293.15, 280.15, 253.15]
    #cond_list = [299.65, 297.655, 296.234, 296.234]
    m_list = [0.154, 0.051, 0.193, 0.193]
    eff_list = [0.87, 0.78, 0.75, 0.7]
    
    inputs = Settings()
    inputs.Y = {'n-Propane':1.0,}
    inputs.second = 'process'
    inputs.cycle = 'vcc'
    inputs.DSC = 5.0
    inputs.DSH = 10.0
    inputs.layout = 'bas'
        
    results_array = []
    
    for i,m,e in zip(weather_list, m_list, eff_list):
        if i <= 293.15: # 간절기 및 동절기
            evapfluid = 'air'
            inevapT = i
            inevapp = 101300.0
            inevapm = 0.0
            InEvap = ProcessFluid(Y={evapfluid:1.0,}, m = inevapm, T = inevapT, p = inevapp)
            
            outevapT = inevapT - 5.0
            outevapp = 101300.0
            OutEvap = ProcessFluid(Y={evapfluid:1.0,}, m = inevapm, T = outevapT, p = outevapp)
            
            inputs.evap_type = 'fthe'
            
            
            condfluid = 'water'
            incondT = 293.15
            incondp = 101300.0
            incondm = m # 분산 히트펌프 증발유량이 메인 히트펌프 응축 유량이 됨
            InCond = ProcessFluid(Y={condfluid:1.0,}, m = incondm, T = incondT, p = incondp)
            
            outcondT = 298.15
            outcondp = 101300.0
            OutCond = ProcessFluid(Y={condfluid:1.0,}, m = incondm, T =outcondT, p = outcondp)
            
            inputs.cond_type = 'phe'
            inputs.comp_eff = e
            vchp_basic = VCHP(InCond, OutCond, InEvap, OutEvap, inputs)
            (InCond, OutCond, InEvap, OutEvap, outputs) = vchp_basic()
        
            
        elif i > 293.15: # 하절기
            evapfluid = 'water'
            inevapT = 303.15
            inevapm = m # 분산 히트펌프 응축유량이 메인 히트펌프 증발 유량이 됨
            inevapp = 101300.0
            InEvap = ProcessFluid(Y={evapfluid:1.0,},m = inevapm, T = inevapT, p = inevapp)
            
            outevapT = 298.15
            outevapp = 101300.0
            OutEvap = ProcessFluid(Y={evapfluid:1.0,},m = inevapm, T = outevapT, p = outevapp)
            
            inputs.evap_type = 'phe'
                
            condfluid = 'air'
            incondT = i
            incondp = 101300.0
            incondm = 0.0
            InCond = ProcessFluid(Y={condfluid:1.0,}, m = incondm, T = incondT, p = incondp)
            
            outcondT = incondT+5.0
            outcondp = 101300.0
            OutCond = ProcessFluid(Y={condfluid:1.0,}, T =outcondT, p = outcondp)
            
            inputs.cond_type = 'fthe'
            inputs.comp_eff = e
            
            vchp_basic = VCHP(InCond, OutCond, InEvap, OutEvap, inputs)
            (InCond, OutCond, InEvap, OutEvap, outputs) = vchp_basic()
        
        results_array.append([InCond.q/1000.0, -InEvap.q/1000.0, outputs.Wcomp/1000.0, outputs.COP_heating])
    
    import pandas as pd
    
    df = pd.DataFrame(results_array)
    print(df)
    '''
    '''
    # 2단 캐스케이드 입력
    
    
    purpose = 'winter'
    
    inputs_t = Settings()
    inputs_t.Y = {'R1234yf':1.0,}
    inputs_t.second = 'process'
    inputs_t.cycle = 'vcc'
    inputs_t.cond_type = 'phe'
    inputs_t.evap_type = 'phe'
    inputs_t.layout = 'bas'
    
    inputs_b = Settings()
    inputs_b.Y = {'R32':1.0,}
    inputs_b.second = 'process'
    inputs_b.cycle = 'vcc'
    inputs_b.layout = 'bas'
    
    if purpose == 'winter':
            
        evapfluid = 'air'
        inevapT = 253.15
        inevapp = 101300.0
        evapm = 0.0
        InEvap = ProcessFluid(Y={evapfluid:1.0,}, m=evapm, T = inevapT, p = inevapp)
        
        outevapT = 248.15
        outevapp = 101300.0
        OutEvap = ProcessFluid(Y={evapfluid:1.0,}, m=evapm, T = outevapT, p = outevapp)
        
        condfluid = 'water'
        incondT_space = 313.15
        incondp_space = 101300.0
        m_space = 0.169
        InCond_space = ProcessFluid(Y={condfluid:1.0,},m = m_space, T = incondT_space, p = incondp_space)
        
        outcondT_space = 318.15
        outcondp_space = 101300.0
        OutCond_space = ProcessFluid(Y={condfluid:1.0,},m = m_space, T=outcondT_space, p=outcondp_space)
        
        incondT_water = 338.15
        incondp_water = 101300.0
        m_water = 0.069922077
        InCond_water = ProcessFluid(Y={condfluid:1.0,},m = m_water, T = incondT_water, p = incondp_water)
        
        outcondT_water = 343.15
        outcondp_water = 101300.0
        OutCond_water = ProcessFluid(Y={condfluid:1.0,},m = m_water, T=outcondT_water, p=outcondp_water)
        
        inputs_b.cond_type = 'phe'
        inputs_b.evap_type = 'fthe'
        
        inputs_t.comp_eff = 0.2
        inputs_b.comp_eff = 0.55
        
        vchp_hando = HandoCycle(InCond_water, OutCond_water, InCond_space, OutCond_space, 'phe', InEvap, OutEvap, inputs_t, inputs_b, purpose)
        
    elif purpose == 'hotwater':
        evapfluid = 'air'
        inevapT = 293.15
        inevapp = 101300.0
        InEvap = ProcessFluid(Y={evapfluid:1.0,}, T = inevapT, p = inevapp)
        
        outevapT = 288.15
        outevapp = 101300.0
        OutEvap = ProcessFluid(Y={evapfluid:1.0,}, T = outevapT, p = outevapp)
        
        condfluid = 'water'
        
        incondT = 338.15
        incondp = 101300.0
        condm = 0.069922077
        InCond = ProcessFluid(Y={condfluid:1.0,},m = condm, T = incondT, p = incondp)
        
        outcondT = 343.15
        outcondp = 101300.0
        OutCond = ProcessFluid(Y={condfluid:1.0,},m = condm, T=outcondT, p=outcondp)
        
        inputs_b.cond_type = 'phe'
        inputs_b.evap_type = 'fthe'
        
        inputs_t.comp_eff = 0.6
        inputs_b.comp_eff = 0.82
        
        vchp_hando = VCHP_cascade(InCond, OutCond, InEvap, OutEvap, inputs_t, inputs_b)
    else:
        evapfluid = 'water'
        inevapT = 285.15
        inevapp = 101300.0
        inevapm = 0.0
        InEvap = ProcessFluid(Y={evapfluid:1.0,},m = inevapm, T = inevapT, p = inevapp)
        
        outevapT = 280.15
        outevapp = 101300.0
        OutEvap = ProcessFluid(Y={evapfluid:1.0,},m = inevapm, T = outevapT, p = outevapp)
        
        cond_space_fluid = 'air'
        incondT_space = 308.15
        incondp_space = 101300.0
        m_space = 0.68
        InCond_space = ProcessFluid(Y={cond_space_fluid:1.0,},m = m_space, T = incondT_space, p = incondp_space)
        
        outcondT_space = 313.15
        outcondp_space = 101300.0
        OutCond_space = ProcessFluid(Y={cond_space_fluid:1.0,},m = m_space, T=outcondT_space, p=outcondp_space)
        
        cond_water_fluid = 'water'
        incondT_water = 338.15
        incondp_water = 101300.0
        m_water = 0.069922077
        InCond_water = ProcessFluid(Y={cond_water_fluid:1.0,},m = m_water, T = incondT_water, p = incondp_water)
        
        outcondT_water = 343.15
        outcondp_water = 101300.0
        OutCond_water = ProcessFluid(Y={cond_water_fluid:1.0,},m = m_water, T=outcondT_water, p=outcondp_water)
        
        inputs_b.cond_type = 'phe'
        inputs_b.evap_type = 'phe'
        
        inputs_t.comp_eff = 0.6
        inputs_b.comp_eff = 0.75
        
        vchp_hando = HandoCycle(InCond_water, OutCond_water, InCond_space, OutCond_space, 'fthe', InEvap, OutEvap, inputs_t, inputs_b, purpose)
    vchp_hando()
    '''
    '''
    # 한도외 사이클 CO2-R290
    # CO2-R290: eff_b = 0.65, eff_t = 0.68
    # CO2-R1234yf: eff_b = 0.65, eff_t = 0.65
    
    
    inputs_b = Settings()
    inputs_t = Settings()
    m_cond_fix = 0.0
    # m_evap_fix = 0.742 (1세대 기준)
    m_evap_fix = 27.825
    m_TES = 0.0
    T_amb = [258.15, 266.15, 275.15, 280.15]
    eff_comp_b = [0.745, 0.77, 0.786, 0.786]
    eff_comp_t = [0.77, 0.766, 0.75, 0.735]
    T_mid = [284.95, 288.95, 293.35, 295.85]
    for T, Tm, eff_b, eff_t in zip(T_amb, T_mid, eff_comp_b, eff_comp_t):
        inputs_b.Y = {'CO2':1.0,}
        inputs_b.comp_eff = eff_b
        inputs_b.second = 'process'
        inputs_b.cycle = 'vcc'
        inputs_b.cond_type = 'phe'
        inputs_b.evap_type = 'fthe'
        inputs_b.layout = 'bas'
        inputs_b.DSC = 1
        inputs_b.DSH = 3
        inputs_b.cond_T_pp = 2
        inputs_b.evap_T_lm = 5

        evapfluid = 'air'
        inevapT = T
        inevapp = 101300.0
        evapm = m_evap_fix
        InEvap_b = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = inevapT, p = inevapp)
        
        outevapT = T-5
        outevapp = 101300.0
        OutEvap_b = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = outevapT, p = outevapp)
        
        condfluid = 'water'
        incondT = Tm
        incondp = 101300.0
        condm = m_TES
        InCond_b = ProcessFluid(Y={condfluid:1.0,},m = condm, T = incondT, p = incondp)
        
        outcondT = Tm+2.0
        outcondp = 101300.0
        OutCond_b = ProcessFluid(Y={condfluid:1.0,},m = condm, T=outcondT, p=outcondp)
        
        print('------------------------------------------------------------------------')
        vchp_hando_bot = VCHP(InCond_b, OutCond_b, InEvap_b, OutEvap_b, inputs_b)
        vchp_hando_bot()
        
        inputs_t.Y = {'R290':1.0,}
        inputs_t.comp_eff = eff_t
        inputs_t.second = 'process'
        inputs_t.cycle = 'vcc'
        inputs_t.cond_type = 'phe'
        inputs_t.evap_type = 'phe'
        inputs_t.layout = 'bas'
        inputs_t.DSC = 1
        inputs_t.DSH = 3
        inputs_t.cond_T_pp = 2
        inputs_t.evap_T_pp = 2
        
        evapfluid = 'water'
        inevapT = Tm
        inevapp = 101300.0
        evapm = OutCond_b.m
        InEvap_t = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = inevapT, p = inevapp)
        
        outevapT = Tm-2
        outevapp = 101300.0
        OutEvap_t = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = outevapT, p = outevapp)
        
        condfluid = 'water'
        incondT = 313.15
        incondp = 101300.0
        condm = m_cond_fix
        InCond_t = ProcessFluid(Y={condfluid:1.0,},m = condm, T = incondT, p = incondp)
        
        outcondT = 318.15
        outcondp = 101300.0
        OutCond_t = ProcessFluid(Y={condfluid:1.0,},m = condm, T=outcondT, p=outcondp)
        
        
        vchp_hando_top = VCHP(InCond_t, OutCond_t, InEvap_t, OutEvap_t, inputs_t)
        vchp_hando_top()
        print('------------------------------------------------------------------------')
    '''
    '''
    # CO2-CO2 급탕
    inputs_b = Settings()
    inputs_t = Settings()
    m_cond_fix = 0.0
    m_evap_fix = 77.525
    m_TES = 0.0
    T_amb = [258.15, 266.15, 275.15, 280.15]
    eff_comp_b = [0.745, 0.77, 0.786, 0.786]
    eff_comp_t = [0.73, 0.77, 0.78, 0.784]
    T_mid = [284.95, 288.95, 293.35, 295.85]
    for T, Tm, eff_b, eff_t in zip(T_amb, T_mid, eff_comp_b, eff_comp_t):
        inputs_b.Y = {'CO2':1.0,}
        inputs_b.comp_eff = eff_b
        inputs_b.second = 'process'
        inputs_b.cycle = 'vcc'
        inputs_b.cond_type = 'phe'
        inputs_b.evap_type = 'fthe'
        inputs_b.layout = 'bas'
        inputs_b.DSC = 1
        inputs_b.DSH = 3
        inputs_b.cond_T_pp = 2
        inputs_b.evap_T_lm = 5

        evapfluid = 'air'
        inevapT = T
        inevapp = 101300.0
        evapm = m_evap_fix
        InEvap_b = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = inevapT, p = inevapp)
        
        outevapT = T-5
        outevapp = 101300.0
        OutEvap_b = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = outevapT, p = outevapp)
        
        condfluid = 'water'
        incondT = Tm
        incondp = 101300.0
        condm = m_TES
        InCond_b = ProcessFluid(Y={condfluid:1.0,},m = condm, T = incondT, p = incondp)
        
        outcondT = Tm+2.0
        outcondp = 101300.0
        OutCond_b = ProcessFluid(Y={condfluid:1.0,},m = condm, T=outcondT, p=outcondp)
        
        print('------------------------------------------------------------------------')
        vchp_hando_bot = VCHP(InCond_b, OutCond_b, InEvap_b, OutEvap_b, inputs_b)
        vchp_hando_bot()
        
        inputs_t.Y = {'CO2':1.0,}
        inputs_t.comp_eff = eff_t
        inputs_t.second = 'process'
        inputs_t.cycle = 'scc'
        inputs_t.cond_type = 'phe'
        inputs_t.evap_type = 'phe'
        inputs_t.layout = 'bas'
        inputs_t.DSC = 5
        inputs_t.DSH = 3
        inputs_t.cond_T_pp = 2
        inputs_t.evap_T_pp = 2
        
        evapfluid = 'water'
        inevapT = Tm
        inevapp = 101300.0
        evapm = OutCond_b.m
        InEvap_t = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = inevapT, p = inevapp)
        
        outevapT = Tm-2
        outevapp = 101300.0
        OutEvap_t = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = outevapT, p = outevapp)
        
        condfluid = 'water'
        incondT = 323.15
        incondp = 101300.0
        condm = m_cond_fix
        InCond_t = ProcessFluid(Y={condfluid:1.0,},m = condm, T = incondT, p = incondp)
        
        outcondT = 333.15
        outcondp = 101300.0
        OutCond_t = ProcessFluid(Y={condfluid:1.0,},m = condm, T=outcondT, p=outcondp)
        
        
        vchp_hando_top = VCHP(InCond_t, OutCond_t, InEvap_t, OutEvap_t, inputs_t)
        vchp_hando_top()
        print('------------------------------------------------------------------------')
    
    
    
    # CO2 단독 난방
    # T_amb = [258.15, 266.15, 275.15, 280.15]
    # eff_comp_b = [0.573, 0.687, 0.76, 0.796]
    
    inputs_b = Settings()
    m_cond_fix = 0.0
    m_evap_fix = 163.3
    m_TES = 0.0
    T_amb = [258.15, 266.15, 275.15, 280.15]
    eff_comp_b = [0.573, 0.687, 0.76, 0.796]
    DSH_list = [5.0, 5.0, 5.0, 5.0]
    
    for T, eff_b, dsh in zip(T_amb, eff_comp_b, DSH_list):
        inputs_b.Y = {'CO2':1.0,}
        inputs_b.comp_eff = eff_b
        inputs_b.second = 'process'
        inputs_b.cycle = 'scc'
        inputs_b.cond_type = 'phe'
        inputs_b.evap_type = 'fthe'
        inputs_b.layout = 'bas'
        inputs_b.DSC = dsh
        inputs_b.DSH = 3
        inputs_b.cond_T_pp = 2
        inputs_b.evap_T_lm = 5

        evapfluid = 'air'
        inevapT = T
        inevapp = 101300.0
        evapm = m_evap_fix
        InEvap_b = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = inevapT, p = inevapp)
        
        outevapT = T-5
        outevapp = 101300.0
        OutEvap_b = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = outevapT, p = outevapp)
        
        condfluid = 'water'
        incondT = 313.15
        incondp = 101300.0
        condm = m_TES
        InCond_b = ProcessFluid(Y={condfluid:1.0,},m = condm, T = incondT, p = incondp)
        
        outcondT = 318.15
        outcondp = 101300.0
        OutCond_b = ProcessFluid(Y={condfluid:1.0,},m = condm, T=outcondT, p=outcondp)
        
        print('------------------------------------------------------------------------')
        vchp_hando_bot = VCHP(InCond_b, OutCond_b, InEvap_b, OutEvap_b, inputs_b)
        vchp_hando_bot()
    
    
     # R1234ze(E) 단독급탕
    
    inputs_b = Settings()
    m_cond_fix = 0.0
    m_evap_fix = 3.561
    m_TES = 0.0
    T_amb = [258.15, 266.15, 275.15, 280.15]
    eff_comp_b = [0.43, 0.5, 0.6, 0.65]
    
    for T, eff_b in zip(T_amb, eff_comp_b):
        inputs_b.Y = {'R1234ze(E)':1.0,}
        inputs_b.comp_eff = eff_b
        inputs_b.second = 'process'
        inputs_b.cycle = 'vcc'
        inputs_b.cond_type = 'phe'
        inputs_b.evap_type = 'fthe'
        inputs_b.layout = 'inj'
        inputs_b.DSC = 1
        inputs_b.DSH = 3
        inputs_b.cond_T_pp = 2
        inputs_b.evap_T_lm = 5

        evapfluid = 'air'
        inevapT = T
        inevapp = 101300.0
        evapm = m_evap_fix
        InEvap_b = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = inevapT, p = inevapp)
        
        outevapT = T-5
        outevapp = 101300.0
        OutEvap_b = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = outevapT, p = outevapp)
        
        condfluid = 'water'
        incondT = 313.15
        incondp = 101300.0
        condm = m_TES
        InCond_b = ProcessFluid(Y={condfluid:1.0,},m = condm, T = incondT, p = incondp)
        
        outcondT = 333.15
        outcondp = 101300.0
        OutCond_b = ProcessFluid(Y={condfluid:1.0,},m = condm, T=outcondT, p=outcondp)
        
        print('------------------------------------------------------------------------')
        vchp_hando_bot = VCHP(InCond_b, OutCond_b, InEvap_b, OutEvap_b, inputs_b)
        vchp_hando_bot()
    
    
    '''
    '''
    # 한도외 사이클 CO2-R290 (-15℃ 조건 밸런스 계산용)
    # CO2-R290: eff_b = 0.65, eff_t = 0.68
    # CO2-R1234yf: eff_b = 0.65, eff_t = 0.65
    
    
    inputs_b = Settings()
    inputs_t = Settings()
    m_cond_fix = 0.0
    m_evap_fix = 2.13
    m_TES = 0.0
    T_amb = 263.15
    eff_comp_b = 0.65
    eff_comp_t = 0.68
    T_mid = 280.15
    
    inputs_b.Y = {'CO2':1.0,}
    inputs_b.comp_eff = eff_comp_b
    inputs_b.second = 'process'
    inputs_b.cycle = 'vcc'
    inputs_b.cond_type = 'phe'
    inputs_b.evap_type = 'fthe'
    inputs_b.layout = 'bas'
    inputs_b.DSC = 1
    inputs_b.DSH = 3
    inputs_b.cond_T_pp = 2
    inputs_b.evap_T_lm = 5

    evapfluid = 'air'
    inevapT = T_amb
    inevapp = 101300.0
    evapm = m_evap_fix
    InEvap_b = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = inevapT, p = inevapp)
    
    outevapT = T_amb-5
    outevapp = 101300.0
    OutEvap_b = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = outevapT, p = outevapp)
    
    condfluid = 'water'
    incondT = T_mid
    incondp = 101300.0
    condm = m_TES
    InCond_b = ProcessFluid(Y={condfluid:1.0,},m = condm, T = incondT, p = incondp)
    
    outcondT = T_mid+2.0
    outcondp = 101300.0
    OutCond_b = ProcessFluid(Y={condfluid:1.0,},m = condm, T=outcondT, p=outcondp)
    
    print('------------------------------------------------------------------------')
    vchp_hando_bot = VCHP(InCond_b, OutCond_b, InEvap_b, OutEvap_b, inputs_b)
    vchp_hando_bot()
    
    inputs_t.Y = {'R290':1.0,}
    inputs_t.comp_eff = eff_comp_t
    inputs_t.second = 'process'
    inputs_t.cycle = 'vcc'
    inputs_t.cond_type = 'phe'
    inputs_t.evap_type = 'phe'
    inputs_t.layout = 'bas'
    inputs_t.DSC = 1
    inputs_t.DSH = 3
    inputs_t.cond_T_pp = 2
    inputs_t.evap_T_pp = 2
    
    evapfluid = 'water'
    inevapT = T_mid
    inevapp = 101300.0
    evapm = OutCond_b.m
    InEvap_t = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = inevapT, p = inevapp)
    
    outevapT = T_mid-2
    outevapp = 101300.0
    OutEvap_t = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = outevapT, p = outevapp)
    
    condfluid = 'water'
    incondT = 313.15
    incondp = 101300.0
    condm = m_cond_fix
    InCond_t = ProcessFluid(Y={condfluid:1.0,},m = condm, T = incondT, p = incondp)
    
    outcondT = 318.15
    outcondp = 101300.0
    OutCond_t = ProcessFluid(Y={condfluid:1.0,},m = condm, T=outcondT, p=outcondp)
    
    
    vchp_hando_top = VCHP(InCond_t, OutCond_t, InEvap_t, OutEvap_t, inputs_t)
    vchp_hando_top()
    print('------------------------------------------------------------------------')
    '''
    
    '''
    # CO2 단독 난방 2단 (-15℃ 급탕 밸런스 계산용) 
    # T_amb = [258.15, 266.15, 275.15, 280.15]
    # eff_comp_b = [0.573, 0.687, 0.76, 0.796]
    
    inputs_b = Settings()
    m_cond_fix = 0.0
    m_evap_fix = 0.742
    m_TES = 0.0
    T_amb = 258.15
    eff_comp_b = 0.745
    eff_comp_t = 0.73
    dsh = 5
    
    
    inputs_b.Y = {'CO2':1.0,}
    inputs_b.comp_eff = eff_comp_b
    inputs_b.comp_top_eff = eff_comp_t
    inputs_b.second = 'process'
    inputs_b.cycle = 'scc'
    inputs_b.cond_type = 'phe'
    inputs_b.evap_type = 'fthe'
    inputs_b.layout = '2comp'
    inputs_b.frac = 0.3
    inputs_b.DSC = dsh
    inputs_b.DSH = 3
    inputs_b.cond_T_pp = 2
    inputs_b.evap_T_lm = 5.0

    evapfluid = 'air'
    inevapT = T_amb
    inevapp = 101300.0
    evapm = m_evap_fix
    InEvap_b = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = inevapT, p = inevapp)
    
    outevapT = T_amb-5
    outevapp = 101300.0
    OutEvap_b = ProcessFluid(Y={evapfluid:1.0,}, m = evapm, T = outevapT, p = outevapp)
    
    condfluid = 'water'
    incondT = 313.15
    incondp = 101300.0
    condm = m_TES
    InCond_b = ProcessFluid(Y={condfluid:1.0,},m = condm, T = incondT, p = incondp)
    
    outcondT = 333.15
    outcondp = 101300.0
    OutCond_b = ProcessFluid(Y={condfluid:1.0,},m = condm, T=outcondT, p=outcondp)
    
    print('------------------------------------------------------------------------')
    vchp_hando_bot = VCHP(InCond_b, OutCond_b, InEvap_b, OutEvap_b, inputs_b)
    vchp_hando_bot()
    '''