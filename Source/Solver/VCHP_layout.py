from copy import deepcopy
import HX_module as HX
import COMPAND_module as CP
from CoolProp.CoolProp import PropsSI
from CoolProp.HumidAirProp import HAPropsSI
import matplotlib.pyplot as PLT
# test 용 import
from HP_dataclass import ProcessFluid, Settings, Outputs

PI = 3.1415926535

# ── 상용 배관 규격 테이블 ──────────────────────────────────────────────────

class VCHP():
    def __init__(self, InCond, OutCond, InEvap, OutEvap, inputs):
        self.InCond = InCond
        self.OutCond = OutCond
        self.InEvap = InEvap
        self.OutEvap = OutEvap
        self.inputs = inputs
        self.amb_P = 101300.0
    
    def __call__(self, inj_opt_flag=1):
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
        if inj_opt_flag == 1:
            (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, outputs) = self.Injection_Optimizer(self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, self.inputs, outputs, no_input, cond_ph, evap_ph)
        elif self.inputs.layout == '2comp':
            (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, outputs) = self.Comp_2stage_Solver(self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, self.inputs, outputs, no_input, cond_ph, evap_ph)
        else:
            (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, outputs) = self.Cycle_Solver(self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, self.inputs, outputs, no_input, cond_ph, evap_ph)
        
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
        OutCond.p = PropsSI('P','T',OutCond.T+inputs.steam_subcool, 'Q', 0.0, InCond.fluidmixture)
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

    def Injection_Optimizer(self, InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, no_input, cond_ph, evap_ph):
        dfrac = 0.005
        inter_frac_lb = 0.0
        inter_frac_ub = 1.0
        results_array = []
        frac_a = 1
        while frac_a:
            for iii in range(2):
                if iii == 0:
                    inputs.inter_frac = 0.5*(inter_frac_lb+inter_frac_ub)*(1-dfrac)
                else:
                    inputs.inter_frac = 0.5*(inter_frac_lb+inter_frac_ub)*(1+dfrac)
                
                (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs) = self.Cycle_Solver(InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, no_input, cond_ph, evap_ph)
                
                if self.evap_conv_err == 1:
                    if self.evap_err > 0:
                        inter_frac_lb = inputs.inter_frac
                    else:
                        inter_frac_ub = inputs.inter_frac
                    inputs.tol += 0.001
                    break
                else:
                    if iii == 0:
                        COP_o = outputs.COP_heating
                        frac_o = inputs.inter_frac
                    else:
                        dCOP = ((outputs.COP_heating - COP_o)/outputs.COP_heating)/((inputs.inter_frac - frac_o)/inputs.inter_frac)
                        if dCOP > 0:
                            inter_frac_lb = inputs.inter_frac
                        else:
                            inter_frac_ub = inputs.inter_frac

                        results_array.append([0.5*(COP_o + outputs.COP_heating), 0.5*(frac_o + inputs.inter_frac), dCOP])

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
            
            outputs.d_evap = evap.d_avg
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
        outputs.COP_cooling = abs(OutEvap.q)/(outputs.Wcomp - outputs.Wexpand)
        outputs.DSH = inputs.DSH
        outputs.evap_UA = evap.UA
        outputs.evap_T_pp = evap.T_pp if inputs.evap_type == 'phe' else evap.T_lm
        
        return (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs)

    def _solve_cycle_states(self, cond_p_lb, cond_p_ub, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs):
        """주어진 압력 구간에서 압축기·팽창기 열역학 상태 계산. Pspecific을 outputs._Psp_*에 저장."""
        InCond_REF.p = 0.5*(cond_p_ub + cond_p_lb)
        OutCond_REF.p = InCond_REF.p - inputs.cond_dp
        
        if isinstance(inputs.comp_eff, (list, tuple)):
            # comp_eff = ['T' 또는 'P', c0, ..., c9]
            #   'P': 압력[bar] 기준 계수, 'T': 포화온도(dew)[°C] 기준 계수
            #   기준 문자 없이 10계수만 입력하면 압력 기준(기존 호환)
            if isinstance(inputs.comp_eff[0], str):
                basis = inputs.comp_eff[0].strip().upper()
                c = inputs.comp_eff[1:]
            else:
                basis = 'P'
                c = inputs.comp_eff
            if basis not in ('T', 'P') or len(c) != 10:
                raise ValueError(f"comp_eff는 ['T' 또는 'P', 10계수] 형식이어야 합니다: {inputs.comp_eff}")
            if basis == 'T':
                pe = PropsSI('T','P',OutEvap_REF.p,'Q',1.0,OutEvap_REF.fluidmixture) - 273.15
                pc = PropsSI('T','P',InCond_REF.p,'Q',1.0,InCond_REF.fluidmixture) - 273.15
            else:
                pe = OutEvap_REF.p/1.0e5
                pc = InCond_REF.p/1.0e5
            outputs.comp_eff = c[0]+c[1]*pe+c[2]*pc+c[3]*pe**2+c[4]*pe*pc+c[5]*pc**2+c[6]*pe**3+c[7]*pc*pe**2+c[8]*pe*pc**2+c[9]*pc**3
        else:
            outputs.comp_eff = inputs.comp_eff

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
                return (InCond_REF, OutCond_REF, InEvap_REF, outputs, 0)
            else:
                self.cond_p_err = 0

        cond_a = 1

        if inputs.layout == 'inj-flash':
            inter_p = InEvap_REF.p*(OutCond_REF.p/InEvap_REF.p)**inputs.inter_frac
            inter_h_vap = PropsSI('H','P',inter_p,'Q',1.0, OutCond_REF.fluidmixture)
            outputs.inter_h_vap = inter_h_vap
            inter_h_liq = PropsSI('H','P',inter_p,'Q',0.0, OutCond_REF.fluidmixture)
            outputs.inter_x = (OutCond_REF.h - inter_h_liq)/(inter_h_vap - inter_h_liq)

            OutComp_low = deepcopy(OutEvap_REF)
            OutComp_low.p = inter_p
            comp_low = CP.Compander_module(OutEvap_REF, OutComp_low)
            (inputs.DSH, cond_a) = comp_low.COMP(eff_isen=outputs.comp_eff, DSH=inputs.DSH)
            OutComp_low = comp_low.primary_out

            InComp_high = deepcopy(OutComp_low)
            InComp_high.h = OutComp_low.h*((1.0-outputs.inter_x)*(1-inputs.liq_frac)+outputs.inter_x*(1-inputs.vap_frac))+(inter_h_liq*(1.0-outputs.inter_x)*inputs.liq_frac+inter_h_vap*outputs.inter_x*inputs.vap_frac)
            InComp_high.T = PropsSI('T','P',InComp_high.p,'H',InComp_high.h, InComp_high.fluidmixture)
            InComp_high.s = PropsSI('S','T',InComp_high.T,'P',InComp_high.p, InComp_high.fluidmixture)
            comp_high = CP.Compander_module(InComp_high, InCond_REF)
            (inputs.DSH, cond_a) = comp_high.COMP(eff_isen=outputs.comp_eff, DSH=inputs.DSH)
            InCond_REF = comp_high.primary_out

            OutExpand_high = deepcopy(OutCond_REF)
            OutExpand_high.p = inter_p
            expand_high = CP.Compander_module(OutCond_REF, OutExpand_high)
            expand_high.EXPAND(eff_isen=inputs.expand_eff)
            OutExpand_high = expand_high.primary_out

            Flash_liq = deepcopy(OutExpand_high)
            Flash_liq.h = (inter_h_liq*(1.0-outputs.inter_x)*(1-inputs.liq_frac)+inter_h_vap*outputs.inter_x*(1-inputs.vap_frac))/((1.0-outputs.inter_x)*(1-inputs.liq_frac)+outputs.inter_x*(1-inputs.vap_frac))
            Flash_liq.T = PropsSI('T','P',OutExpand_high.p,'Q',0.0, OutExpand_high.fluidmixture)
            if inputs.expand_bot_eff > 0.0:
                Flash_liq.s = PropsSI('S','P',OutExpand_high.p,'Q',0.0, OutExpand_high.fluidmixture)
            expand_low = CP.Compander_module(Flash_liq, InEvap_REF)
            expand_low.EXPAND(eff_isen=inputs.expand_bot_eff)
            InEvap_REF = expand_low.primary_out

            outputs._Psp_comp_low    = comp_low.Pspecific
            outputs._Psp_comp_high   = comp_high.Pspecific
            outputs._Psp_expand_high = expand_high.Pspecific
            outputs._Psp_expand_low  = expand_low.Pspecific
            outputs.outcomp_low_T    = OutComp_low.T
            outputs.outcomp_low_p    = OutComp_low.p
            outputs.outcomp_low_h    = OutComp_low.h
            outputs.outcomp_low_s    = OutComp_low.s
            outputs.incomp_high_T    = InComp_high.T
            outputs.incomp_high_p    = InComp_high.p
            outputs.incomp_high_h    = InComp_high.h
            outputs.incomp_high_s    = InComp_high.s
            outputs.outexpand_high_T = OutExpand_high.T
            outputs.outexpand_high_p = OutExpand_high.p
            outputs.outexpand_high_h = OutExpand_high.h
            outputs.outexpand_high_s = OutExpand_high.s
            outputs.flash_liq_T      = Flash_liq.T
            outputs.flash_liq_p      = Flash_liq.p
            outputs.flash_liq_h      = Flash_liq.h
            outputs.flash_liq_s      = Flash_liq.s
            outputs.flash_gas_T      = outputs.flash_liq_T
            outputs.flash_gas_p      = outputs.flash_liq_p
            outputs.flash_gas_h      = PropsSI("H","P",outputs.flash_gas_p,"Q",1.0,OutCond_REF.fluidmixture)
            outputs.flash_gas_s      = PropsSI("S","P",outputs.flash_gas_p,"Q",1.0,OutCond_REF.fluidmixture)
            
        elif inputs.layout == 'inj-eco':
            inter_p = InEvap_REF.p*(OutCond_REF.p/InEvap_REF.p)**inputs.inter_frac
            
            InEco_cold = deepcopy(OutCond_REF)
            OutEco_cold = deepcopy(OutCond_REF)
            InEco_hot = deepcopy(OutCond_REF)
            OutEco_hot = deepcopy(OutCond_REF)
            OutComp_low = deepcopy(OutEvap_REF)
            
            
            OutEco_cold.p = inter_p
            OutEco_cold_T = PropsSI("T","P",OutEco_cold.p,"Q",1.0,OutEco_cold.fluidmixture)+inputs.eco_dsh
            OutEco_cold.T = OutEco_cold_T
            OutEco_cold_h = PropsSI("H","P",OutEco_cold.p,"T",OutEco_cold.T,OutEco_cold.fluidmixture)
            OutEco_cold.h = OutEco_cold_h
                
            InEco_cold.p = OutEco_cold.p + inputs.eco_cold_dp
            InEco_cold.T = PropsSI("T","H",InEco_cold.h,"P",InEco_cold.p,InEco_cold.fluidmixture)
            
            eco_frac_lb = 0.0
            eco_frac_ub = 1.0
            a_eco = 1
            while a_eco:
                eco_frac = 0.5*(eco_frac_lb+eco_frac_ub)
                OutEco_cold.m = eco_frac    
                InEco_cold.m = eco_frac
                InEco_hot.m = 1-eco_frac
                OutEco_hot.m = 1-eco_frac
                
                InEco_cold.q = (OutEco_cold.h - InEco_cold.h)*InEco_cold.m
                OutEco_cold.q = (OutEco_cold.h - InEco_cold.h)*InEco_cold.m
                InEco_hot.q = -InEco_cold.q
                OutEco_hot.q = -InEco_cold.q
                
                OutEco_hot.p = OutCond_REF.p - inputs.eco_hot_dp
                OutEco_hot.h = InEco_hot.h + InEco_hot.q/InEco_hot.m
                OutEco_hot.T = PropsSI("T","H",OutEco_hot.h,"P",OutEco_hot.p,OutEco_hot.fluidmixture)
                eco = HX.Heatexchanger_module(InEco_cold, OutEco_cold, 1, InEco_hot, OutEco_hot, 1)
                eco.PHE(N_element=inputs.eco_N_element)
                if eco.T_rvs == 1:
                    OutEco_cold.T = OutEco_cold_T
                    OutEco_cold.h = OutEco_cold_h
                    eco_frac_ub = eco_frac
                else:    
                    eco_add_dsc = eco.secondary_in.T - eco.secondary_out.T
                    eco_err = (eco_add_dsc - inputs.eco_add_dsc)/inputs.eco_add_dsc
                    
                    if eco_err < 0:
                        eco_frac_lb = eco_frac
                    else:
                        eco_frac_ub = eco_frac
                        
                    if abs(eco_err) < inputs.tol:
                        outputs.eco_T_pp = eco.T_pp
                        a_eco = 0
                    elif eco_frac_ub - eco_frac_lb < inputs.tol:
                        outputs.eco_T_pp = eco.T_pp
                        a_eco = 0
            
            outputs.eco_frac = eco_frac
            OutComp_low.p = inter_p
            comp_low = CP.Compander_module(OutEvap_REF, OutComp_low)
            (inputs.DSH, _) = comp_low.COMP(eff_isen=outputs.comp_eff, DSH=inputs.DSH)
            OutComp_low = comp_low.primary_out
            
            InComp_high = deepcopy(OutComp_low)
            InComp_high.h = OutComp_low.h*(1-eco_frac)+OutEco_cold.h*eco_frac
            InComp_high.T = PropsSI("T","H",InComp_high.h,"P",InComp_high.p,InComp_high.fluidmixture)
            InComp_high.s = PropsSI("S","T",InComp_high.T,"P",InComp_high.p,InComp_high.fluidmixture)
            
            comp_high = CP.Compander_module(InComp_high, InCond_REF)
            (_, _) = comp_high.COMP(eff_isen=outputs.comp_eff, DSH=inputs.DSH)
            InCond_REF = comp_high.primary_out
            
            expand_hot = CP.Compander_module(OutEco_hot, InEvap_REF)
            expand_hot.EXPAND(eff_isen = 0.0)
            InEvap_REF = expand_hot.primary_out
            
            outputs._Psp_comp_low = comp_low.Pspecific
            outputs._Psp_comp_high = comp_high.Pspecific
            outputs._Psp_expand_hot = expand_hot.Pspecific
            outputs.outcomp_low_T = OutComp_low.T
            outputs.outcomp_low_p = OutComp_low.p
            outputs.outcomp_low_h = OutComp_low.h
            outputs.outcomp_low_s = OutComp_low.s
            outputs.incomp_high_T = InComp_high.T
            outputs.incomp_high_p = InComp_high.p
            outputs.incomp_high_h = InComp_high.h
            outputs.incomp_high_s = InComp_high.s
            outputs.ineco_cold_T = InEco_cold.T
            outputs.ineco_cold_p = InEco_cold.p
            outputs.ineco_cold_h = InEco_cold.h
            outputs.outeco_cold_T = OutEco_cold.T
            outputs.outeco_cold_p = OutEco_cold.p
            outputs.outeco_cold_h = OutEco_cold.h
            outputs.ineco_hot_T = InEco_hot.T
            outputs.ineco_hot_p = InEco_hot.p
            outputs.ineco_hot_h = InEco_hot.h
            outputs.outeco_hot_T = OutEco_hot.T
            outputs.outeco_hot_p = OutEco_hot.p
            outputs.outeco_hot_h = OutEco_hot.h
            outputs.eco_UA = eco.UA
            outputs.eco_T_pp = eco.T_pp
            
            
        elif inputs.layout == '2comp':
            inter_p = InEvap_REF.p*(OutCond_REF.p/InEvap_REF.p)**inputs.inter_frac
            OutComp_low = deepcopy(OutEvap_REF)
            OutComp_low.p = inter_p
            comp_low = CP.Compander_module(OutEvap_REF, OutComp_low)
            (inputs.DSH, cond_a) = comp_low.COMP(eff_isen=outputs.comp_eff, DSH=inputs.DSH)
            OutComp_low = comp_low.primary_out

            InComp_high = deepcopy(OutComp_low)
            InComp_high.h = OutComp_low.h
            InComp_high.T = PropsSI('T','P',InComp_high.p,'H',InComp_high.h, InComp_high.fluidmixture)
            InComp_high.s = PropsSI('S','T',InComp_high.T,'P',InComp_high.p, InComp_high.fluidmixture)
            comp_high = CP.Compander_module(InComp_high, InCond_REF)
            (inputs.DSH, cond_a) = comp_high.COMP(eff_isen=outputs.comp_eff, DSH=inputs.DSH)
            InCond_REF = comp_high.primary_out

            InExpand = OutCond_REF
            expand_high = CP.Compander_module(InExpand, InEvap_REF)
            expand_high.EXPAND(eff_isen=inputs.expand_eff)
            InEvap_REF = expand_high.primary_out

            outputs._Psp_comp_low    = comp_low.Pspecific
            outputs._Psp_comp_high   = comp_high.Pspecific
            outputs._Psp_expand_high = expand_high.Pspecific
            outputs.outcomp_low_T    = OutComp_low.T
            outputs.outcomp_low_p    = OutComp_low.p
            outputs.outcomp_low_h    = OutComp_low.h
            outputs.outcomp_low_s    = OutComp_low.s
            outputs.incomp_high_T    = InComp_high.T
            outputs.incomp_high_p    = InComp_high.p
            outputs.incomp_high_h    = InComp_high.h
            outputs.incomp_high_s    = InComp_high.s

        elif inputs.layout == 'part_cool':
            pcx_cold_in = deepcopy(InEvap_REF)
            OutPCX_hot  = deepcopy(InEvap_REF)
            OutPCX_cold = deepcopy(InEvap_REF)

            pcx_cold_in.p = InEvap_REF.p + inputs.pcx_cold_dp
            cold_expand = CP.Compander_module(OutCond_REF, pcx_cold_in)
            cold_expand.EXPAND(eff_isen=0.0)
            pcx_cold_in = cold_expand.primary_out

            OutPCX_hot.p = OutCond_REF.p - inputs.pcx_hot_dp
            pcx_hot_out_hideal  = PropsSI("H","T",pcx_cold_in.T,"P",OutPCX_hot.p, OutPCX_hot.fluidmixture)
            pcx_cold_out_hideal = PropsSI("H","T",OutCond_REF.T,"P",OutPCX_cold.p,OutPCX_cold.fluidmixture)

            if (OutCond_REF.h-pcx_hot_out_hideal)*(1-inputs.pcx_frac) > (pcx_cold_out_hideal-pcx_cold_in.h)*inputs.pcx_frac:
                OutPCX_cold.T = OutCond_REF.T - inputs.pcx_T_pp
                OutPCX_cold.h = PropsSI("H","T",OutPCX_cold.T,"P",OutPCX_cold.p,OutPCX_cold.fluidmixture)
                OutPCX_hot.h  = OutCond_REF.h - (OutPCX_cold.h - pcx_cold_in.h)*inputs.pcx_frac/(1-inputs.pcx_frac)
                OutPCX_hot.T  = PropsSI("T","H",OutPCX_hot.h,"P",OutPCX_hot.p,OutPCX_hot.fluidmixture)
            else:
                OutPCX_hot.T  = pcx_cold_in.T + inputs.pcx_T_pp
                OutPCX_hot.h  = PropsSI("H","T",OutPCX_hot.T,"P",OutPCX_hot.p,OutPCX_hot.fluidmixture)
                OutPCX_cold.h = OutCond_REF.h + (OutCond_REF.h-OutPCX_hot.h)*(1-inputs.pcx_frac)/inputs.pcx_frac
                OutPCX_cold.T = PropsSI("T","H",OutPCX_cold.h,"P",OutPCX_cold.p,OutPCX_cold.fluidmixture)

            expand = CP.Compander_module(OutPCX_hot, InEvap_REF)
            expand.EXPAND(eff_isen=0.0)
            InEvap_REF = expand.primary_out

            InComp = deepcopy(OutEvap_REF)
            InComp.h = OutEvap_REF.h*(1-inputs.pcx_frac) + OutPCX_cold.h*inputs.pcx_frac
            InComp.T = PropsSI("T","H",InComp.h,"P",InComp.p,InComp.fluidmixture)
            comp = CP.Compander_module(InComp, InCond_REF)
            (inputs.DSH, cond_a) = comp.COMP(eff_isen=outputs.comp_eff, DSH=inputs.DSH)
            InCond_REF = comp.primary_out

            outputs._Psp_comp        = comp.Pspecific
            outputs._Psp_cold_expand = cold_expand.Pspecific
            outputs._Psp_expand      = expand.Pspecific
            outputs.pcx_cold_in_T    = pcx_cold_in.T
            outputs.pcx_cold_in_p    = pcx_cold_in.p
            outputs.pcx_cold_in_h    = pcx_cold_in.h
            outputs.pcx_hot_out_T    = OutPCX_hot.T
            outputs.pcx_hot_out_p    = OutPCX_hot.p
            outputs.pcx_hot_out_h    = OutPCX_hot.h
            outputs.pcx_cold_out_T   = OutPCX_cold.T
            outputs.pcx_cold_out_p   = OutPCX_cold.p
            outputs.pcx_cold_out_h   = OutPCX_cold.h
            outputs.incomp_T         = InComp.T
            outputs.incomp_p         = InComp.p
            outputs.incomp_h         = InComp.h

        else:  # basic / ihx
            if inputs.layout == 'ihx':
                InComp   = deepcopy(OutEvap_REF)
                InComp.p = InComp.p - inputs.ihx_cold_dp
                InExpand   = deepcopy(OutCond_REF)
                InExpand.p = InExpand.p - inputs.ihx_hot_dp
                IHX = HX.Heatexchanger_module(OutCond_REF, InExpand, 0, OutEvap_REF, InComp, 0)
                IHX.SIMPHX(eff_HX=inputs.ihx_eff)
                InExpand = IHX.primary_out
                InComp   = IHX.secondary_out
                outputs.ihx_hot_out_T = InExpand.T
                outputs.ihx_hot_out_p = InExpand.p
                outputs.ihx_hot_out_h = InExpand.h
                outputs.ihx_hot_out_s = InExpand.s
                outputs.ihx_cold_out_T = InComp.T
                outputs.ihx_cold_out_p = InComp.p
                outputs.ihx_cold_out_h = InComp.h
                outputs.ihx_cold_out_s = InComp.s
            else:
                InComp   = OutEvap_REF
                InExpand = OutCond_REF

            comp = CP.Compander_module(InComp, InCond_REF)
            (inputs.DSH, cond_a) = comp.COMP(eff_isen=outputs.comp_eff, DSH=inputs.DSH)
            InCond_REF = comp.primary_out

            expand = CP.Compander_module(InExpand, InEvap_REF)
            expand.EXPAND(eff_isen=inputs.expand_eff)
            InEvap_REF = expand.primary_out

            outputs._Psp_comp   = comp.Pspecific
            outputs._Psp_expand = expand.Pspecific

        return (InCond_REF, OutCond_REF, InEvap_REF, outputs, cond_a)

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
            (InCond_REF, OutCond_REF, InEvap_REF, outputs, cond_a) = \
                self._solve_cycle_states(cond_p_lb, cond_p_ub, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs)
            if self.cond_p_err:
                break

            if (no_input == 'InCondT') or (no_input == 'OutCondT') or (no_input == 'Condm'):
                InEvap_REF.m = InEvap.q/(InEvap_REF.h - OutEvap_REF.h)
                OutEvap_REF.m = InEvap_REF.m
                if inputs.layout == 'inj-flash':
                    InCond_REF.m = InEvap_REF.m/((1.0-outputs.inter_x)*(1-inputs.liq_frac)+outputs.inter_x*(1-inputs.vap_frac))
                    OutCond_REF.m = InCond_REF.m
                    outputs.Wcomp_top = outputs._Psp_comp_high*InCond_REF.m/inputs.mech_eff
                    outputs.Wcomp_bot = outputs._Psp_comp_low*OutEvap_REF.m/inputs.mech_eff
                    outputs.Wcomp     = outputs.Wcomp_bot + outputs.Wcomp_top
                    outputs.Wexpand_top = outputs._Psp_expand_high*OutCond_REF.m*inputs.mech_eff
                    outputs.Wexpand_bot = outputs._Psp_expand_low*InEvap_REF.m*inputs.mech_eff
                    outputs.Wexpand     = outputs.Wexpand_bot + outputs.Wexpand_top
                elif inputs.layout == 'inj-eco':
                    InCond_REF.m = InEvap_REF.m/(1-outputs.eco_frac)
                    OutCond_REF.m = InCond_REF.m
                    outputs.Wcomp_top = outputs._Psp_comp_high*InCond_REF.m/inputs.mech_eff
                    outputs.Wcomp_bot = outputs._Psp_comp_low*OutEvap_REF.m/inputs.mech_eff
                    outputs.Wcomp     = outputs.Wcomp_bot + outputs.Wcomp_top
                    outputs.Wexpand_hot = outputs._Psp_expand_hot*OutCond_REF.m*(1-outputs.eco_frac)*inputs.mech_eff
                    outputs.Wexpand   = outputs.Wexpand_hot
                elif inputs.layout == '2comp':
                    InCond_REF.m = InEvap_REF.m
                    OutCond_REF.m = InEvap_REF.m
                    outputs.Wcomp_top = outputs._Psp_comp_high*InCond_REF.m/inputs.mech_eff
                    outputs.Wcomp_bot = outputs._Psp_comp_low*OutEvap_REF.m/inputs.mech_eff
                    outputs.Wcomp     = outputs.Wcomp_bot + outputs.Wcomp_top
                    outputs.Wexpand   = outputs._Psp_expand_high*OutCond_REF.m*inputs.mech_eff
                elif inputs.layout == 'part_cool':
                    InCond_REF.m = InEvap_REF.m/(1-inputs.pcx_frac)
                    OutCond_REF.m = InCond_REF.m
                    outputs.Wcomp   = outputs._Psp_comp*InCond_REF.m/inputs.mech_eff
                    outputs.Wexpand = (outputs._Psp_cold_expand*inputs.pcx_frac + outputs._Psp_expand*(1-inputs.pcx_frac))*InCond_REF.m*inputs.mech_eff
                else:
                    InCond_REF.m = InEvap_REF.m
                    OutCond_REF.m = InEvap_REF.m
                    outputs.Wcomp   = outputs._Psp_comp*InCond_REF.m/inputs.mech_eff
                    outputs.Wexpand = outputs._Psp_expand*InEvap_REF.m*inputs.mech_eff

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
                if inputs.layout == 'inj-flash':
                    InEvap_REF.m = InCond_REF.m*((1.0-outputs.inter_x)*(1-inputs.liq_frac)+outputs.inter_x*(1-inputs.vap_frac))
                    OutEvap_REF.m = InEvap_REF.m
                    outputs.Wcomp_top = outputs._Psp_comp_high*InCond_REF.m/inputs.mech_eff
                    outputs.Wcomp_bot = outputs._Psp_comp_low*OutEvap_REF.m/inputs.mech_eff
                    outputs.Wcomp     = outputs.Wcomp_bot + outputs.Wcomp_top                    
                    outputs.Wexpand_top = outputs._Psp_expand_high*OutCond_REF.m*inputs.mech_eff
                    outputs.Wexpand_bot = outputs._Psp_expand_low*InEvap_REF.m*inputs.mech_eff
                    outputs.Wexpand     = outputs.Wexpand_bot + outputs.Wexpand_top
                elif inputs.layout == 'inj-eco':
                    InEvap_REF.m = InCond_REF.m*(1-outputs.eco_frac)
                    OutEvap_REF.m = InEvap_REF.m
                    outputs.Wcomp_top = outputs._Psp_comp_high*InCond_REF.m/inputs.mech_eff
                    outputs.Wcomp_bot = outputs._Psp_comp_low*OutEvap_REF.m/inputs.mech_eff
                    outputs.Wcomp     = outputs.Wcomp_bot + outputs.Wcomp_top
                    outputs.Wexpand_hot = outputs._Psp_expand_hot*OutCond_REF.m*(1-outputs.eco_frac)*inputs.mech_eff
                    outputs.Wexpand   = outputs.Wexpand_hot
                elif inputs.layout == '2comp':
                    InEvap_REF.m = InCond_REF.m
                    OutEvap_REF.m = InCond_REF.m
                    outputs.Wcomp_top = outputs._Psp_comp_high*InCond_REF.m/inputs.mech_eff
                    outputs.Wcomp_bot = outputs._Psp_comp_low*OutEvap_REF.m/inputs.mech_eff
                    outputs.Wcomp     = outputs.Wcomp_bot + outputs.Wcomp_top
                    outputs.Wexpand   = outputs._Psp_expand_high*OutCond_REF.m*inputs.mech_eff
                elif inputs.layout == 'part_cool':
                    InEvap_REF.m = InCond_REF.m*(1-inputs.pcx_frac)
                    OutEvap_REF.m = InEvap_REF.m
                    outputs.Wcomp   = outputs._Psp_comp*InCond_REF.m/inputs.mech_eff
                    outputs.Wexpand = (outputs._Psp_cold_expand*inputs.pcx_frac + outputs._Psp_expand*(1-inputs.pcx_frac))*InCond_REF.m*inputs.mech_eff
                else:
                    InEvap_REF.m = InCond_REF.m
                    OutEvap_REF.m = InCond_REF.m
                    outputs.Wcomp   = outputs._Psp_comp*InCond_REF.m/inputs.mech_eff
                    outputs.Wexpand = outputs._Psp_expand*InEvap_REF.m*inputs.mech_eff

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
                (outputs.cond_Tarray, outputs.cond_parray) = cond.FTHE(N_element=inputs.cond_N_element, N_turn=inputs.cond_N_turn, N_row=inputs.cond_N_row)
                self.cond_err = (inputs.cond_T_lm - cond.T_lm)/inputs.cond_T_lm
            elif inputs.cond_type == 'phe':
                (outputs.cond_Tarray, outputs.cond_parray) = cond.PHE(N_element=inputs.cond_N_element)
                self.cond_err = (inputs.cond_T_pp - cond.T_pp)/inputs.cond_T_pp

            outputs.d_cond = cond.d_avg
            if cond_ph != 0:
                outputs.d_cond_sec = cond.d_avg_sec
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
        outputs.cond_T_pp = cond.T_pp if inputs.cond_type == 'phe' else cond.T_lm
        if inputs.layout == 'ihx':
            outputs.qihx = (outputs.ihx_cold_out_h - OutEvap_REF.h)*OutEvap_REF.m
        elif inputs.layout == 'inj-eco':
            outputs.qeco = (outputs.ineco_hot_h - outputs.outeco_hot_h)*InEvap_REF.m
        elif inputs.layout == 'part_cool':
            outputs.qpcx = (outputs.pcx_cold_out_h - outputs.pcx_cold_in_h)*(OutCond_REF.m*inputs.pcx_frac)
            
        return (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs)

    
    def _find_std_pipe(self, D_calc_m: float, pipe_mat: str) -> dict:
        """계산 직경(m) 이상인 가장 작은 상용 배관을 반환."""
        # 동관 ACR (ASTM B280 / KS D 5507): (호칭, OD_mm, ID_mm, wall_mm)
        COPPER_ACR_TABLE = [
            ('1/4"',    6.35,  4.83, 0.76),
            ('3/8"',    9.53,  7.75, 0.89),
            ('1/2"',   12.70, 10.66, 1.02),
            ('5/8"',   15.88, 13.84, 1.02),
            ('3/4"',   19.05, 16.92, 1.07),
            ('7/8"',   22.22, 19.94, 1.14),
            ('1-1/8"', 28.58, 26.04, 1.27),
            ('1-3/8"', 34.93, 32.13, 1.40),
            ('1-5/8"', 41.28, 38.23, 1.52),
            ('2-1/8"', 53.98, 50.42, 1.78),
            ('2-5/8"', 66.68, 62.61, 2.03),
            ('3-1/8"', 79.38, 75.31, 2.03),
            ('3-5/8"', 92.08, 87.86, 2.11),
            ('4-1/8"',104.78, 99.95, 2.41),
            ('5-1/8"',130.18,124.64, 2.77),
            ('6-1/8"',155.58,149.38, 3.10),
        ]
        # 강관 Sch40 (KS D 3562 / ASTM A53): (호칭경mm, OD_mm, ID_mm, wall_mm)
        STEEL_SCH40_TABLE = [
            ( 15,  21.3,  15.8, 2.77),
            ( 20,  26.7,  20.9, 2.87),
            ( 25,  33.4,  26.6, 3.38),
            ( 32,  42.2,  35.1, 3.56),
            ( 40,  48.3,  40.9, 3.68),
            ( 50,  60.3,  52.5, 3.91),
            ( 65,  73.0,  62.7, 5.16),
            ( 80,  88.9,  77.9, 5.49),
            (100, 114.3, 102.3, 6.02),
            (125, 141.3, 128.2, 6.55),
            (150, 168.3, 154.1, 7.11),
            (200, 219.1, 202.7, 8.18),
            (250, 273.1, 254.5, 9.27),
            (300, 323.9, 303.2,10.31),
        ]
        D_mm = D_calc_m * 1000.0
        if pipe_mat == 'copper':
            for label, OD_mm, ID_mm, wall_mm in COPPER_ACR_TABLE:
                if ID_mm >= D_mm:
                    return {'label': label, 'OD_mm': OD_mm, 'ID_mm': ID_mm, 'wall_mm': wall_mm}
            r = COPPER_ACR_TABLE[-1]
            return {'label': r[0]+'↑', 'OD_mm': r[1], 'ID_mm': r[2], 'wall_mm': r[3]}
        else:  # steel
            for nom_mm, OD_mm, ID_mm, wall_mm in STEEL_SCH40_TABLE:
                if ID_mm >= D_mm:
                    return {'label': f'DN{nom_mm}', 'OD_mm': OD_mm, 'ID_mm': ID_mm, 'wall_mm': wall_mm}
            r = STEEL_SCH40_TABLE[-1]
            return {'label': f'DN{r[0]}↑', 'OD_mm': r[1], 'ID_mm': r[2], 'wall_mm': r[3]}


    def Pipe_Dia_Calc(self, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, vg_s=5.0, vg_d=10.0, vl=1.0, pipe_mat='copper'):
        OutEvap_REF.rho = PropsSI("D","T",OutEvap_REF.T,"P",OutEvap_REF.p, OutEvap_REF.fluidmixture)
        InCond_REF.rho  = PropsSI("D","T",InCond_REF.T, "P",InCond_REF.p,  InCond_REF.fluidmixture)
        OutCond_REF.rho = PropsSI("D","T",OutCond_REF.T,"P",OutCond_REF.p, OutCond_REF.fluidmixture)
        InEvap_REF.rhog = PropsSI("D","P",InEvap_REF.p, "Q", 1.0, OutEvap_REF.fluidmixture)
        InEvap_REF.rhol = PropsSI("D","P",InEvap_REF.p, "Q", 0.0, OutEvap_REF.fluidmixture)
        x = PropsSI("Q","P",InEvap_REF.p,"H",InEvap_REF.h,InEvap_REF.fluidmixture)
        InEvap_REF.rho  = 1/(x/InEvap_REF.rhog+(1-x)/InEvap_REF.rhol)

        OutEvap_REF.D = (4/PI*OutEvap_REF.m/vg_s/OutEvap_REF.rho)**0.5
        InCond_REF.D  = (4/PI*InCond_REF.m /vg_d/InCond_REF.rho )**0.5
        OutCond_REF.D = (4/PI*OutCond_REF.m/vl /OutCond_REF.rho)**0.5
        InEvap_REF.D  = (4/PI*InEvap_REF.m /vg_s/InEvap_REF.rho )**0.5

        pipe_suction   = self._find_std_pipe(OutEvap_REF.D, pipe_mat)
        pipe_discharge = self._find_std_pipe(InCond_REF.D,  pipe_mat)
        pipe_liquid    = self._find_std_pipe(OutCond_REF.D, pipe_mat)
        pipe_expansion = self._find_std_pipe(InEvap_REF.D,  pipe_mat)

        OutEvap_REF.D_std = pipe_suction['ID_mm']   / 1000.0
        InCond_REF.D_std  = pipe_discharge['ID_mm'] / 1000.0
        OutCond_REF.D_std = pipe_liquid['ID_mm']    / 1000.0
        InEvap_REF.D_std  = pipe_expansion['ID_mm'] / 1000.0

        mat_label = '동관 ACR' if pipe_mat == 'copper' else '강관 Sch40'
        print(f'\n{"─"*65}')
        print(f'  [배관 직경 계산 결과]  (규격: {mat_label})')
        print(f'{"─"*65}')
        print(f'  {"라인":<22}  {"계산값":>8}   {"추천 규격":<9}  ID(mm)  OD(mm)')
        print(f'  {"─"*60}')
        print(f'  {"흡입관 (증발기→압축기)":<22}  {OutEvap_REF.D*1000:>7.1f}mm'
            f'   {pipe_suction["label"]:<9}  {pipe_suction["ID_mm"]:>5.2f}   {pipe_suction["OD_mm"]:>5.2f}')
        print(f'  {"토출관 (압축기→응축기)":<22}  {InCond_REF.D*1000:>7.1f}mm'
            f'   {pipe_discharge["label"]:<9}  {pipe_discharge["ID_mm"]:>5.2f}   {pipe_discharge["OD_mm"]:>5.2f}')
        print(f'  {"액관   (응축기→팽창밸브)":<22}  {OutCond_REF.D*1000:>7.1f}mm'
            f'   {pipe_liquid["label"]:<9}  {pipe_liquid["ID_mm"]:>5.2f}   {pipe_liquid["OD_mm"]:>5.2f}')
        print(f'  {"팽창관 (팽창밸브→증발기)":<22}  {InEvap_REF.D*1000:>7.1f}mm'
            f'   {pipe_expansion["label"]:<9}  {pipe_expansion["ID_mm"]:>5.2f}   {pipe_expansion["OD_mm"]:>5.2f}')

        if inputs.layout == 'inj-flash':
            outputs.outexpand_high_rhog = PropsSI("D","P",outputs.outexpand_high_p,"Q",1.0,OutEvap_REF.fluidmixture)
            outputs.outexpand_high_rhol = PropsSI("D","P",outputs.outexpand_high_p,"Q",0.0,OutEvap_REF.fluidmixture)
            x = PropsSI("Q","P",outputs.outexpand_high_p,"H",outputs.outexpand_high_h,OutCond_REF.fluidmixture)
            outputs.outexpand_high_rho  = 1/(x/outputs.outexpand_high_rhog+(1-x)/outputs.outexpand_high_rhol)
            outputs.outexpand_high_D    = (4/PI*OutCond_REF.m/vg_s/outputs.outexpand_high_rho)**0.5
            outputs.flash_liq_rho       = PropsSI("D","P",outputs.flash_liq_p,"Q",0.0,OutCond_REF.fluidmixture)
            outputs.flash_liq_D         = (4/PI*InEvap_REF.m/vl/outputs.flash_liq_rho)**0.5
            outputs.flash_gas_rho       = PropsSI("D","P",outputs.flash_liq_p,"Q",1.0,OutCond_REF.fluidmixture)
            outputs.flash_gas_D         = (4/PI*(OutCond_REF.m-InEvap_REF.m)/vg_s/outputs.flash_gas_rho)**0.5

            pipe_exp_high  = self._find_std_pipe(outputs.outexpand_high_D, pipe_mat)
            pipe_flash_liq = self._find_std_pipe(outputs.flash_liq_D,      pipe_mat)
            pipe_flash_gas = self._find_std_pipe(outputs.flash_gas_D,      pipe_mat)
            outputs.outexpand_high_D_std = pipe_exp_high['ID_mm']  / 1000.0
            outputs.flash_liq_D_std      = pipe_flash_liq['ID_mm'] / 1000.0
            outputs.flash_gas_D_std      = pipe_flash_gas['ID_mm'] / 1000.0

            print(f'  {"인젝션 팽창출구관":<22}  {outputs.outexpand_high_D*1000:>7.1f}mm'
                f'   {pipe_exp_high["label"]:<9}  {pipe_exp_high["ID_mm"]:>5.2f}   {pipe_exp_high["OD_mm"]:>5.2f}')
            print(f'  {"플래시탱크 액관":<22}  {outputs.flash_liq_D*1000:>7.1f}mm'
                f'   {pipe_flash_liq["label"]:<9}  {pipe_flash_liq["ID_mm"]:>5.2f}   {pipe_flash_liq["OD_mm"]:>5.2f}')
            print(f'  {"플래시탱크 가스관":<22}  {outputs.flash_gas_D*1000:>7.1f}mm'
                f'   {pipe_flash_gas["label"]:<9}  {pipe_flash_gas["ID_mm"]:>5.2f}   {pipe_flash_gas["OD_mm"]:>5.2f}')
            
        elif inputs.layout == 'inj-eco':
            outputs.ineco_cold_rhog = PropsSI("D","P",outputs.ineco_cold_p, "Q", 1.0, OutCond_REF.fluidmixture)
            outputs.ineco_cold_rhol = PropsSI("D","P",outputs.ineco_cold_p, "Q", 0.0, OutCond_REF.fluidmixture)
            x = PropsSI("Q","P",outputs.ineco_cold_p,"H",outputs.ineco_cold_h, OutCond_REF.fluidmixture)
            outputs.ineco_cold_rho = 1/(x/outputs.ineco_cold_rhog+(1-x)/outputs.ineco_cold_rhol)
            outputs.outeco_cold_rho = PropsSI("D","P",outputs.outeco_cold_p,"T",outputs.outeco_cold_T,OutCond_REF.fluidmixture)
            outputs.outeco_hot_rho = PropsSI("D","P",outputs.outeco_hot_p,"T",outputs.outeco_hot_T,OutCond_REF.fluidmixture)
            outputs.ineco_hot_D   = (4/PI*InEvap_REF.m/vl/OutCond_REF.rho)**0.5
            outputs.ineev_cold_D  = (4/PI*(OutCond_REF.m - InEvap_REF.m)/vl/OutCond_REF.rho)**0.5
            outputs.ineco_cold_D  = (4/PI*(OutCond_REF.m - InEvap_REF.m)/vg_s/outputs.ineco_cold_rho)**0.5
            outputs.outeco_cold_D = (4/PI*(OutCond_REF.m - InEvap_REF.m)/vg_s/outputs.outeco_cold_rho)**0.5
            outputs.outeco_hot_D  = (4/PI*InEvap_REF.m/vl/outputs.outeco_hot_rho)**0.5

            pipe_ineco_hot   = self._find_std_pipe(outputs.ineco_hot_D,   pipe_mat)
            pipe_ineev_cold  = self._find_std_pipe(outputs.ineev_cold_D,  pipe_mat)
            pipe_ineco_cold  = self._find_std_pipe(outputs.ineco_cold_D,  pipe_mat)
            pipe_outeco_cold = self._find_std_pipe(outputs.outeco_cold_D, pipe_mat)
            pipe_outeco_hot  = self._find_std_pipe(outputs.outeco_hot_D,  pipe_mat)
            outputs.ineco_hot_D_std   = pipe_ineco_hot['ID_mm']   / 1000.0
            outputs.ineev_cold_D_std  = pipe_ineev_cold['ID_mm']  / 1000.0
            outputs.ineco_cold_D_std  = pipe_ineco_cold['ID_mm']  / 1000.0
            outputs.outeco_cold_D_std = pipe_outeco_cold['ID_mm'] / 1000.0
            outputs.outeco_hot_D_std  = pipe_outeco_hot['ID_mm']  / 1000.0

            print(f'  {"ECO 고온측 입구관(액관)":<22}  {outputs.ineco_hot_D*1000:>7.1f}mm'
                f'   {pipe_ineco_hot["label"]:<9}  {pipe_ineco_hot["ID_mm"]:>5.2f}   {pipe_ineco_hot["OD_mm"]:>5.2f}')
            print(f'  {"ECO 냉각측 팽창전관(액관)":<22}  {outputs.ineev_cold_D*1000:>7.1f}mm'
                f'   {pipe_ineev_cold["label"]:<9}  {pipe_ineev_cold["ID_mm"]:>5.2f}   {pipe_ineev_cold["OD_mm"]:>5.2f}')
            print(f'  {"ECO 냉각측 입구관(2상)":<22}  {outputs.ineco_cold_D*1000:>7.1f}mm'
                f'   {pipe_ineco_cold["label"]:<9}  {pipe_ineco_cold["ID_mm"]:>5.2f}   {pipe_ineco_cold["OD_mm"]:>5.2f}')
            print(f'  {"ECO 냉각측 출구(인젝션)관":<22}  {outputs.outeco_cold_D*1000:>7.1f}mm'
                f'   {pipe_outeco_cold["label"]:<9}  {pipe_outeco_cold["ID_mm"]:>5.2f}   {pipe_outeco_cold["OD_mm"]:>5.2f}')
            print(f'  {"ECO 고온측 출구관(액관)":<22}  {outputs.outeco_hot_D*1000:>7.1f}mm'
                f'   {pipe_outeco_hot["label"]:<9}  {pipe_outeco_hot["ID_mm"]:>5.2f}   {pipe_outeco_hot["OD_mm"]:>5.2f}')

            
        elif inputs.layout == 'ihx':
            outputs.ihx_hot_rho  = PropsSI("D","T",outputs.ihx_hot_out_T, "P",outputs.ihx_hot_out_p, OutCond_REF.fluidmixture)
            outputs.ihx_hot_D    = (4/PI*OutCond_REF.m/vl/outputs.ihx_hot_rho)**0.5
            outputs.ihx_cold_rho = PropsSI("D","T",outputs.ihx_cold_out_T,"P",outputs.ihx_cold_out_p,OutEvap_REF.fluidmixture)
            outputs.ihx_cold_D   = (4/PI*OutCond_REF.m/vg_s/outputs.ihx_hot_rho)**0.5

            pipe_ihx_hot  = self._find_std_pipe(outputs.ihx_hot_D,  pipe_mat)
            pipe_ihx_cold = self._find_std_pipe(outputs.ihx_cold_D, pipe_mat)
            outputs.ihx_hot_D_std  = pipe_ihx_hot['ID_mm']  / 1000.0
            outputs.ihx_cold_D_std = pipe_ihx_cold['ID_mm'] / 1000.0

            print(f'  {"IHX 고온측 (액관)":<22}  {outputs.ihx_hot_D*1000:>7.1f}mm'
                f'   {pipe_ihx_hot["label"]:<9}  {pipe_ihx_hot["ID_mm"]:>5.2f}   {pipe_ihx_hot["OD_mm"]:>5.2f}')
            print(f'  {"IHX 저온측 (흡입관)":<22}  {outputs.ihx_cold_D*1000:>7.1f}mm'
                f'   {pipe_ihx_cold["label"]:<9}  {pipe_ihx_cold["ID_mm"]:>5.2f}   {pipe_ihx_cold["OD_mm"]:>5.2f}')

        print(f'{"─"*65}')


    def Ref_Charge_Calc(self, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, vg=5.0, vl=1.0, pipe_mat='copper'):
        self.Pipe_Dia_Calc(InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, vg, vl, pipe_mat)

        M_evap      = inputs.evap_V    * outputs.d_evap
        M_evap2comp = inputs.outevap_L * OutEvap_REF.D**2 * PI/4 * OutEvap_REF.rho
        M_comp2cond = inputs.incond_L  * InCond_REF.D**2  * PI/4 * InCond_REF.rho
        M_cond      = inputs.cond_V    * outputs.d_cond
        M_cond2eev  = inputs.outcond_L * OutCond_REF.D**2 * PI/4 * OutCond_REF.rho
        M_eev2evap  = inputs.inevap_L  * InEvap_REF.D**2  * PI/4 * InEvap_REF.rho
        M_total     = M_evap + M_evap2comp + M_comp2cond + M_cond + M_cond2eev + M_eev2evap

        print(f'\n{"─"*55}')
        print(f'  [냉매 충전량 계산 결과]')
        print(f'{"─"*55}')
        print(f'  증발기                            : {M_evap:7.3f} kg')
        print(f'  흡입관 (증발기출구→압축기입구)    : {M_evap2comp:7.3f} kg')
        print(f'  토출관 (압축기출구→응축기입구)    : {M_comp2cond:7.3f} kg')
        print(f'  응축기                            : {M_cond:7.3f} kg')
        print(f'  액관   (응축기출구→팽창밸브)      : {M_cond2eev:7.3f} kg')
        print(f'  팽창관 (팽창밸브→증발기입구)      : {M_eev2evap:7.3f} kg')

        if inputs.layout == 'inj-flash':
            M_flash_tank = inputs.flash_V      * outputs.outexpand_high_rho
            M_flash2comp = inputs.flash2comp_L * outputs.flash_gas_D**2 * PI/4 * outputs.flash_gas_rho
            M_flash2eev  = inputs.flash2eev_L  * outputs.flash_liq_D**2  * PI/4 * outputs.flash_liq_rho
            M_total += M_flash_tank + M_flash2comp + M_flash2eev
            print(f'  플래시탱크                        : {M_flash_tank:7.3f} kg')
            print(f'  인젝션관 (플래시탱크→압축기)      : {M_flash2comp:7.3f} kg')
            print(f'  액관     (플래시탱크→EEV)          : {M_flash2eev:7.3f} kg')
        
        elif inputs.layout == 'inj-eco':
            a = 1
        
        elif inputs.layout == 'ihx':
            M_ihx_hot  = inputs.ihx_hot_L  * outputs.ihx_hot_D**2  * PI/4 * outputs.ihx_hot_rho
            M_ihx_cold = inputs.ihx_cold_L * outputs.ihx_cold_D**2 * PI/4 * outputs.ihx_cold_rho
            M_total += M_ihx_hot + M_ihx_cold
            print(f'  IHX 고온측 (액관)                 : {M_ihx_hot:7.3f} kg')
            print(f'  IHX 저온측 (흡입관)               : {M_ihx_cold:7.3f} kg')

        print(f'{"─"*55}')
        print(f'  총 냉매 충전량                    : {M_total:7.3f} kg')
        print(f'{"─"*55}')


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
        
        fig_ph.savefig(ph_file+'.png',dpi=300)
        fig_ts.savefig(ts_file+'.png',dpi=300)
        
        
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
            
        elif inputs.layout == 'inj-flash':
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
        
        elif inputs.layout == 'inj-eco':
            outeco_hot_s = PropsSI('S','T',outputs.outeco_hot_T,'P',outputs.outeco_hot_p,InCond_REF.fluidmixture)
            ineco_cold_s = PropsSI('S','H',outputs.ineco_cold_h,'P',outputs.ineco_cold_p,InCond_REF.fluidmixture)
            incomp_high_svap = PropsSI('S','P',outputs.incomp_high_p,'Q',1.0,InCond_REF.fluidmixture)
            incomp_high_Tvap = PropsSI('T','P',outputs.incomp_high_p,'Q',1.0,InCond_REF.fluidmixture)
            if inputs.cycle == 'vcc':    
                s_points = [OutCond_REF.s, outeco_hot_s, InEvap_REF.s, OutEvap_REF_svap, OutEvap_REF.s, outputs.outcomp_low_s, outputs.incomp_high_s, incomp_high_svap, ineco_cold_s, OutCond_REF.s, OutCond_REF_sliq, InCond_REF_svap, InCond_REF.s, outputs.incomp_high_s] 
                T_points = [OutCond_REF.T, outputs.outeco_hot_T, InEvap_REF.T, OutEvap_REF_Tvap, OutEvap_REF.T, outputs.outcomp_low_T, outputs.incomp_high_T, incomp_high_Tvap, outputs.ineco_cold_T, OutCond_REF.T, OutCond_REF_Tliq, InCond_REF_Tvap, InCond_REF.T, outputs.incomp_high_T] 
                h_points = [OutCond_REF.h, outputs.outeco_hot_h, InEvap_REF.h, OutEvap_REF.h, outputs.outcomp_low_h, outputs.incomp_high_h, outputs.ineco_cold_h, OutCond_REF.h, InCond_REF.h, outputs.incomp_high_h]
                p_points = [OutCond_REF.p, outputs.outeco_hot_p, InEvap_REF.p, OutEvap_REF.p, outputs.outcomp_low_p, outputs.incomp_high_p, outputs.ineco_cold_p, OutCond_REF.p, InCond_REF.p, outputs.incomp_high_p]
        
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
        print(f'Heating COP:{outputs.COP_heating:.3f}, Cooling COP:{outputs.COP_cooling:.3f}')
        print(f'Refrigerant:{OutCond_REF.fluidmixture}')
        print(f'Q heating: {OutCond.q/1000:.3f} [kW] ({OutCond.q/3516.8525:.3f} [usRT])')
        print(f'Q cooling: {OutEvap_REF.q/1000:.3f} [kW] ({OutEvap_REF.q/3516.8525:.3f} [usRT])')
        print(f'Q comp: {outputs.Wcomp/1000:.3f} [kW]')
        if inputs.layout == 'ihx':
            print(f'Q IHX: {outputs.qihx/1000:.3f} [kW]')
        if inputs.layout == 'part_cool':
            print(f'Q PCX: {outputs.qpcx/1000:.3f} [kW]')
        if inputs.layout == 'inj-eco':
            print(f'Q ECO: {outputs.qeco/1000:.3f} [kW]')
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
        elif inputs.layout == 'inj-flash':
            print(f'Toutcomp_s1: {outputs.outcomp_low_T-273.15:.3f} [℃], Poutcomp_s1: {outputs.outcomp_low_p/1.0e5:.3f} [bar], mcomp_s1: {OutEvap_REF.m:.3f} [kg/s]')
            print(f'Tincomp_s2: {outputs.incomp_high_T-273.15:.3f} [℃], Pincomp_s2: {outputs.incomp_high_p/1.0e5:.3f} [bar], mcomp_s2: {InCond_REF.m:.3f} [kg/s]')
        elif inputs.layout == 'inj-eco':
            print(f'Toutcomp_s1: {outputs.outcomp_low_T-273.15:.3f} [℃], Poutcomp_s1: {outputs.outcomp_low_p/1.0e5:.3f} [bar], mcomp_s1: {OutEvap_REF.m:.3f} [kg/s]')
            print(f'Tincomp_s2: {outputs.incomp_high_T-273.15:.3f} [℃], Pincomp_s2: {outputs.incomp_high_p/1.0e5:.3f} [bar], mcomp_s2: {InCond_REF.m:.3f} [kg/s]')
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
        elif inputs.layout == 'inj-flash':
            print(f'Tflash: {outputs.flash_liq_T-273.15:.3f} [℃], Pflash: {outputs.flash_liq_p/1.0e5:.3f} [bar], mflash: {OutCond_REF.m-OutEvap_REF.m:.3f} [kg/s]')
        elif inputs.layout == 'inj-eco':
            print(f'Teco_cold_in: {outputs.ineco_cold_T-273.15:.3f} [℃] (xeco_cold_in: {PropsSI("Q","P",outputs.ineco_cold_p,"H",outputs.ineco_cold_h,OutCond_REF.fluidmixture):.3f}), Peco_cold_in: {outputs.ineco_cold_p/1.0e5:.3f} [bar], meco_cold: {OutCond_REF.m-OutEvap_REF.m:.3f} [kg/s]')
            print(f'Teco_cold_out: {outputs.outeco_cold_T-273.15:.3f} [℃], Peco_cold_in: {outputs.outeco_cold_p/1.0e5:.3f} [bar]')
            print(f'Teco_hot_in: {outputs.ineco_hot_T-273.15:.3f} [℃], Peco_cold_in: {outputs.ineco_hot_p/1.0e5:.3f} [bar], meco_hot: {OutEvap_REF.m:.3f} [kg/s]')
            print(f'Teco_hot_out: {outputs.outeco_hot_T-273.15:.3f} [℃], Peco_cold_in: {outputs.outeco_hot_p/1.0e5:.3f} [bar]')
            print(f'DSH_inj: {outputs.outeco_cold_T-PropsSI("T","P",outputs.outeco_cold_p,"Q",1.0,OutCond_REF.fluidmixture):.3f} [℃], DSC_add_eco: {outputs.ineco_hot_T-outputs.outeco_hot_T:.3f} [℃]')
        
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
        print(f'Ts_low: {Tlow-273.15:.3f} [℃], Ts_high: {Thigh-273.15:.3f}')
        print('---------------------------------------------------------------------------')
        label = 'T_pp' if inputs.cond_type == 'phe' else 'T_lm'
        print(f'Cond_UA: {outputs.cond_UA:.3f} [W/℃], Cond_{label}: {outputs.cond_T_pp:.3f} [℃]')
        label = 'T_pp' if inputs.evap_type == 'phe' else 'T_lm'
        print(f'Evap_UA: {outputs.evap_UA:.3f} [W/℃], Evap_{label}: {outputs.evap_T_pp:.3f} [℃]')
        if inputs.layout == 'inj-eco':
            print(f'Eco_UA: {outputs.eco_UA:.3f} [W/℃], Eco_T_pp: {outputs.eco_T_pp:.3f} [℃]')
        comp_in_d = PropsSI("D","T",OutEvap_REF.T,"P",OutEvap_REF.p,OutEvap_REF.fluidmixture)
        print(f'Vdis comp @60hz: {OutEvap_REF.m/comp_in_d*1.0e6/60:.3f}[cc/rev] / Qflow comp: {OutEvap_REF.m/comp_in_d*3600:.2f}[m3/h]')
        print(f'Comp_eff: {outputs.comp_eff*100:.3f}[%]')
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
    
    def __call__(self, opt_flag=1, evap_t_T_input=0):
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
            evap_t_p_input = PropsSI("P","T",evap_t_T_input,"Q",0.5,OutEvap_REF_t.fluidmixture)
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
                
                outputs_t.COP_heating = abs(OutCond.q)/(outputs_t.Wcomp - outputs_t.Wexpand)
                outputs_t.COP_cooling = abs(OutEvap.q)/(outputs_t.Wcomp - outputs_t.Wexpand)
                
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
            outputs_t.d_evap = outputs_b.d_cond_sec
            outputs_t.evap_T_pp = outputs_b.cond_T_pp
            outputs_t.evap_UA = outputs_b.cond_UA
            
            
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
                (InCond_REF_t, OutCond_REF_t, InEvap_REF_t, outputs_t, _) = \
                    self._solve_cycle_states(cond_p_lb, cond_p_ub, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, inputs_t, outputs_t)
                if self.cond_p_err:
                    break
                (InEvap_REF_t, OutEvap_REF_t, InEvap, OutEvap, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, outputs_b) = super().Cycle_Solver(InEvap_REF_t, OutEvap_REF_t, InEvap, OutEvap, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, inputs_b, outputs_b, 'Condm', cond_b_ph, evap_b_ph)
                outputs_t.d_evap = outputs_b.d_cond_sec

                OutEvap_REF_t.m = InEvap_REF_t.m
                if inputs_t.layout == 'inj-flash':
                    InCond_REF_t.m = InEvap_REF_t.m/((1.0-outputs_t.inter_x)*(1-inputs_t.liq_frac)+outputs_t.inter_x*(1-inputs_t.vap_frac))
                    OutCond_REF_t.m = InCond_REF_t.m
                    outputs_t.Wcomp_top = outputs_t._Psp_comp_high*InCond_REF_t.m/inputs_t.mech_eff
                    outputs_t.Wcomp_bot = outputs_t._Psp_comp_low*OutEvap_REF_t.m/inputs_t.mech_eff
                    outputs_t.Wcomp     = outputs_t.Wcomp_bot + outputs_t.Wcomp_top
                    outputs_t.Wexpand_top = outputs_t._Psp_expand_high*OutCond_REF_t.m*inputs_t.mech_eff
                    outputs_t.Wexpand_bot = outputs_t._Psp_expand_low*InEvap_REF_t.m*inputs_t.mech_eff
                    outputs_t.Wexpand     = outputs_t.Wexpand_bot + outputs_t.Wexpand_top
                elif inputs_t.layout == 'inj-eco':
                    InCond_REF_t.m = InEvap_REF_t.m/(1.0-outputs_t.eco_frac)
                    OutCond_REF_t.m = InCond_REF_t.m
                    outputs_t.Wcomp_top = outputs_t._Psp_comp_high*InCond_REF_t.m/inputs_t.mech_eff
                    outputs_t.Wcomp_bot = outputs_t._Psp_comp_low*OutEvap_REF_t.m/inputs_t.mech_eff
                    outputs_t.Wcomp     = outputs_t.Wcomp_bot + outputs_t.Wcomp_top
                    outputs_t.Wexpand_hot = outputs_t._Psp_expand_hot*OutCond_REF_t.m*(1-outputs_t.eco_frac)*inputs_t.mech_eff
                    outputs_t.Wexpand   = outputs_t.Wexpand_hot
                elif inputs_t.layout == '2comp':
                    InCond_REF_t.m = InEvap_REF_t.m
                    OutCond_REF_t.m = InEvap_REF_t.m                    
                    outputs_t.Wcomp_top = outputs_t._Psp_comp_high*InCond_REF_t.m/inputs_t.mech_eff
                    outputs_t.Wcomp_bot = outputs_t._Psp_comp_low*OutEvap_REF_t.m/inputs_t.mech_eff
                    outputs_t.Wcomp     = outputs_t.Wcomp_bot + outputs_t.Wcomp_top
                    outputs_t.Wexpand   = outputs_t._Psp_expand_high*OutCond_REF_t.m*inputs_t.mech_eff
                elif inputs_t.layout == 'part_cool':
                    InCond_REF_t.m = InEvap_REF_t.m/(1-inputs_t.pcx_frac)
                    OutCond_REF_t.m = InCond_REF_t.m
                    outputs_t.Wcomp   = outputs_t._Psp_comp*InCond_REF_t.m/inputs_t.mech_eff
                    outputs_t.Wexpand = (outputs_t._Psp_cold_expand*inputs_t.pcx_frac + outputs_t._Psp_expand*(1-inputs_t.pcx_frac))*InCond_REF_t.m*inputs_t.mech_eff
                else:
                    InCond_REF_t.m = InEvap_REF_t.m
                    OutCond_REF_t.m = InEvap_REF_t.m
                    outputs_t.Wcomp   = outputs_t._Psp_comp*InCond_REF_t.m/inputs_t.mech_eff
                    outputs_t.Wexpand = outputs_t._Psp_expand*InEvap_REF_t.m*inputs_t.mech_eff
                if inputs_t.layout == 'ihx':
                    outputs_t.qihx = (outputs_t._ihx_InComp_h - OutEvap_REF_t.h)*OutEvap_REF_t.m
                elif inputs_t.layout == 'inj-eco':
                    outputs_t.qeco = (outputs_t.ineco_hot_h - outputs_t.outeco_hot_h)*InEvap_REF_t.m
                elif inputs_t.layout == 'part_cool':
                    outputs_t.qpcx = (outputs_t.pcx_cold_out_h - outputs_t.pcx_cold_in_h)*(OutCond_REF_t.m*inputs_t.pcx_frac)

                OutCond_REF_t.q = (OutCond_REF_t.h - InCond_REF_t.h)*OutCond_REF_t.m
                InCond_REF_t.q = OutCond_REF_t.q
                OutCond.q = -OutCond_REF_t.q
                InCond.q = -OutCond_REF_t.q
                
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
                
                outputs_t.d_cond = cond_t.d_avg        
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
            
            
            outputs_t.cond_UA = cond_t.UA
            outputs_t.cond_T_pp = cond_t.T_pp if inputs_t.cond_type == 'phe' else cond_t.T_lm
            
        outputs_t.COP_heating = abs(OutCond.q)/(outputs_t.Wcomp - outputs_t.Wexpand)
        outputs_t.COP_cooling = abs(OutEvap.q)/(outputs_t.Wcomp - outputs_t.Wexpand)
        outputs_t.DSH = OutEvap_REF_t.T - OutEvap_REF_t_Tvap
        
        return(InCond, OutCond, InEvap, OutEvap, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, outputs_t, outputs_b)
    
    def Pipe_Dia_Calc(self, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, inputs_t, outputs_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, inputs_b, outputs_b, vg_s_t=5.0, vg_d_t=10.0, vl_t=1.0, vg_s_b=5.0, vg_d_b=10.0, vl_b=1.0, pipe_mat="copper"):
        print('----------Top Cycle Charge----------')
        super().Pipe_Dia_Calc(InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, inputs_t, outputs_t, vg_s_t, vg_d_t, vl_t, pipe_mat)
        print(' ')
        print('----------Bot Cycle Charge----------')
        super().Pipe_Dia_Calc(InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, inputs_b, outputs_b, vg_s_b, vg_d_b, vl_b, pipe_mat)
    
    def Ref_Charge_Calc(self, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, inputs_t, outputs_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, inputs_b, outputs_b, vg=5.0, vl=1.0, pipe_mat="copper"):
        print('----------Top Cycle Charge----------')
        super().Ref_Charge_Calc(InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, inputs_t, outputs_t, vg, vl, pipe_mat)
        print(' ')
        print('----------Bot Cycle Charge----------')
        super().Ref_Charge_Calc(InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, inputs_b, outputs_b, vg, vl, pipe_mat)
        
        
        
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
        print('Cascade Heating COP:{:.3f}'.format(COP_cascade))
        print('')

