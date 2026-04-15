from copy import deepcopy
import matplotlib.pyplot as PLT
from dataclasses import dataclass
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary
import os, numpy as np
RP = REFPROPFunctionLibrary(os.environ['RPPREFIX'])
RP.SETPATHdll(os.environ['RPPREFIX'])
iUnit = RP.GETENUMdll(0,"MOLAR BASE SI").iEnum

@dataclass
class ProcessFluid:
    m: float = 0.0
    T: float = 0.0
    p: float = 0.0
    h: float = 0.0
    s: float = 0.0
    Cp: float = 0.0
    q: float = 0.0
        

@dataclass
class Settings:
    # 냉매 입력    
    DSC = 5.0
    DSH = 10.0
    
    # 응축기 스펙
    cond_type = 'phe'
    cond_T_pp: float = 2.0
    cond_T_lm: float = 10.0
    cond_dp: float = 0.01
    cond_N_element: int = 20
    cond_N_row: int = 2
    cond_N_turn: int = 3
    cond_UA = 0.0
        
    # 증발기 스펙
    evap_type = 'phe'
    evap_T_pp: float = 2.0
    evap_T_lm: float = 10.0
    evap_dp: float = 0.01
    evap_N_element: int = 20
    evap_N_row: int = 3
    evap_N_turn: int = 3
    evap_UA = 0.0

    comp_eff: float = 0.7
    mech_eff: float = 1.0
    # 수렴오차
    tol: float = 1.0e-3
    
    
@dataclass
class Outputs:
    COP_heating: float = 0.0
    Wcomp: float = 0.0
    DSH:float = 0.0
    cond_UA:float = 0.0
    evap_UA:float = 0.0    

class VCHP():
    def __init__(self, ref_dict):
        ref_name = ''
        M_list = []
        w_frac = []
        
        tot_frac= sum(ref_dict.values())
        N_tot = 0
        for k, v in zip(ref_dict.keys(),ref_dict.values()):
            ref_name = ref_name+k+';'
            m_value = RP.REFPROPdll(k,'','M',iUnit,0,0,0,0,[1.0]).Output[0]
            w_value = v/tot_frac
            M_list.append(m_value)
            w_frac.append(w_value)
            N_tot = N_tot+w_value/m_value
        
        x_frac = []
        for w, m in zip(w_frac, M_list):
            x_frac.append(w/m/N_tot)
        
        self.ref_dict = ref_dict
        self.w_frac = w_frac
        self.x_frac = x_frac
        self.N_tot = N_tot
        self.M_tot = 1/N_tot
        self.ref_fluid = ref_name
        
    def __call__(self, cond_fluid, evap_fluid, InCond, OutCond, InEvap, OutEvap, Inputs):
        self.cond_fluid = cond_fluid
        self.evap_fluid = evap_fluid
        
        self.M_cond = RP.REFPROPdll(self.cond_fluid,'','M',iUnit,0,0,0,0,[1.0]).Output[0]
        self.M_evap = RP.REFPROPdll(self.evap_fluid,'','M',iUnit,0,0,0,0,[1.0]).Output[0]
        
        self.InCond = InCond
        self.OutCond = OutCond
        self.InEvap = InEvap
        self.OutEvap = OutEvap
        self.inputs = Inputs
        
        outputs = Outputs()
        
        InCond_REF = ProcessFluid()
        OutCond_REF = ProcessFluid()
        InEvap_REF = ProcessFluid()
        OutEvap_REF = ProcessFluid()
        
        [p_crit, T_crit] = RP.REFPROPdll(self.ref_fluid,'CRIT','P;T',iUnit,0,0,0,0,self.x_frac).Output[:2]
        
        InCond_REF.p_crit = p_crit
        OutCond_REF.p_crit = p_crit
        InEvap_REF.p_crit = p_crit
        OutEvap_REF.p_crit = p_crit
        
        InCond_REF.T_crit = T_crit
        OutCond_REF.T_crit = T_crit
        InEvap_REF.T_crit = T_crit
        OutEvap_REF.T_crit = T_crit
        
        (self.InCond, self.OutCond, self.InEvap, self.OutEvap, no_input) = self.Input_Processing(self.InCond, self.OutCond, self.InEvap, self.OutEvap)
        evap_ph = 0
        cond_ph = 0
        
        (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, outputs) = self.Cycle_Solver(self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, self.inputs, outputs, no_input, cond_ph, evap_ph)
        
        #self.Post_Processing(outputs)
        #self.Plot_diagram(self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, self.inputs, outputs)
        
        return (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, outputs)
        
    def Input_Processing(self, InCond, OutCond, InEvap, OutEvap):
        no_InCondT = 0
        no_Condm = 0
        no_OutCondT = 0
        no_InEvapT = 0
        no_Evapm = 0
        no_OutEvapT = 0
        
        
        
        if InCond.p <= 0.0:
            InCond.p = 101300.0
    
        if OutCond.p <= 0.0:
            OutCond.p = 101300.0
            
        if InCond.T <= 0.0:
            no_InCondT = 1
    
        if InCond.m <= 0 and OutCond.m <= 0 :
            no_Condm = 1
        else:
            if InCond.m == 0:
                OutCond.m = OutCond.m/self.M_cond
                InCond.m = OutCond.m # shallow copy
            else:
                InCond.m = InCond.m/self.M_cond
                OutCond.m = InCond.m
            
        if OutCond.T <= 0.0:
            no_OutCondT = 1
            
            
        if InEvap.p <= 0.0:
            InEvap.p = 101300.0
        
        if OutEvap.p <= 0.0:
            OutEvap.p = 101300.0
        
        
        if InEvap.T <= 0.0:
            no_InEvapT = 1
        
        if InEvap.m <= 0 and OutEvap.m <= 0 :
            no_Evapm = 1
        else:
            if InEvap.m == 0:
                OutEvap.m = OutEvap.m/self.M_evap
                InEvap.m = OutEvap.m
            else:
                InEvap.m = InEvap.m/self.M_evap
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
                [OutCond.h, OutCond.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,OutCond.T,OutCond.p,[1.0]).Output[:2]
                [InEvap.h, InEvap.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,InEvap.T,InEvap.p,[1.0]).Output[:2]
                [OutEvap.h, OutEvap.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,OutEvap.T,OutEvap.p,[1.0]).Output[:2]
                
                InEvap.q = (OutEvap.h - InEvap.h)*InEvap.m
                OutEvap.q = InEvap.q 
                no_input = 'InCondT'
            elif no_OutCondT == 1:
                [InCond.h, InCond.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,InCond.T,InCond.p,[1.0]).Output[:2]
                [InEvap.h, InEvap.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,InEvap.T,InEvap.p,[1.0]).Output[:2]
                [OutEvap.h, OutEvap.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,OutEvap.T,OutEvap.p,[1.0]).Output[:2]
                InEvap.q = (OutEvap.h - InEvap.h)*InEvap.m
                OutEvap.q = InEvap.q 
                no_input = 'OutCondT'
            elif no_Condm == 1:
                [InCond.h, InCond.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,InCond.T,InCond.p,[1.0]).Output[:2]
                [OutCond.h, OutCond.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,OutCond.T,OutCond.p,[1.0]).Output[:2]
                [InEvap.h, InEvap.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,InEvap.T,InEvap.p,[1.0]).Output[:2]
                [OutEvap.h, OutEvap.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,OutEvap.T,OutEvap.p,[1.0]).Output[:2]
                InEvap.q = (OutEvap.h - InEvap.h)*InEvap.m
                OutEvap.q = InEvap.q 
                no_input = 'Condm'
            
            elif no_InEvapT == 1:
                [InCond.h, InCond.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,InCond.T,InCond.p,[1.0]).Output[:2]
                [OutCond.h, OutCond.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,OutCond.T,OutCond.p,[1.0]).Output[:2]
                [OutEvap.h, OutEvap.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,OutEvap.T,OutEvap.p,[1.0]).Output[:2]
                InCond.q = (OutCond.h - InCond.h)*InCond.m
                OutCond.q = InCond.q
                no_input = 'InEvapT'
            elif no_OutEvapT == 1:
                [InCond.h, InCond.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,InCond.T,InCond.p,[1.0]).Output[:2]
                [OutCond.h, OutCond.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,OutCond.T,OutCond.p,[1.0]).Output[:2]
                [InEvap.h, InEvap.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,InEvap.T,InEvap.p,[1.0]).Output[:2]
                InCond.q = (OutCond.h - InCond.h)*InCond.m
                OutCond.q = InCond.q
                no_input = 'OutEvapT'
            elif no_Evapm == 1:
                [InCond.h, InCond.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,InCond.T,InCond.p,[1.0]).Output[:2]
                [OutCond.h, OutCond.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,OutCond.T,OutCond.p,[1.0]).Output[:2]
                [InEvap.h, InEvap.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,InEvap.T,InEvap.p,[1.0]).Output[:2]
                [OutEvap.h, OutEvap.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;CP',iUnit,0,0,OutEvap.T,OutEvap.p,[1.0]).Output[:2]
                InCond.q = (OutCond.h - InCond.h)*InCond.m
                OutCond.q = InCond.q
                no_input = 'Evapm'
                
        return (InCond, OutCond, InEvap, OutEvap, no_input)
    
    def Cycle_Solver(self,InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, no_input, cond_ph, evap_ph):
        if no_input == 'InEvapT':
            evap_p_ub = RP.REFPROPdll(self.ref_fluid,'TQ','P',iUnit,0,0,InCond.T,1.0,self.x_frac).Output[0]
        else:
            evap_p_ub = RP.REFPROPdll(self.ref_fluid,'TQ','P',iUnit,0,0,InEvap.T,1.0,self.x_frac).Output[0]
            
        evap_p_lb = 101300.0
        evap_a = 1
        
        while evap_a: 
            OutEvap_REF.p = 0.5*(evap_p_lb+evap_p_ub)
            InEvap_REF.p = OutEvap_REF.p+inputs.evap_dp
            OutEvap_REF_Tvap = RP.REFPROPdll(self.ref_fluid,'PQ','T',iUnit,0,0,OutEvap_REF.p,1.0,self.x_frac).Output[0]
            OutEvap_REF.T = OutEvap_REF_Tvap + inputs.DSH
            if inputs.DSH == 0:
                [OutEvap_REF.h, OutEvap_REF.s] = RP.REFPROPdll(self.ref_fluid,'PQ','H;S',iUnit,0,0,OutEvap_REF.p,1.0,self.x_frac).Output[:2]
            else:
                [OutEvap_REF.h, OutEvap_REF.s] = RP.REFPROPdll(self.ref_fluid,'PT','H;S',iUnit,0,0,OutEvap_REF.p,OutEvap_REF.T,self.x_frac).Output[:2]
            
            (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs) = self.HighPressure_Solver(InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, no_input, cond_ph)
            
            evap = Heatexchanger_module(InEvap_REF, OutEvap_REF, self.ref_fluid, self.x_frac, 1, InEvap, OutEvap, self.evap_fluid, [1.0], evap_ph)
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
            elif (evap_p_ub - evap_p_lb)/101300 < inputs.tol:
                self.evap_conv_err = 1
                evap_a = 0
                
            outputs.COP_heating = abs(OutCond.q)/outputs.Wcomp
        
        outputs.DSH = inputs.DSH
        outputs.evap_UA = evap.UA
        
        return (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs)
        
    def HighPressure_Solver(self, InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, no_input, cond_ph):
        
        cond_p_ub = InCond_REF.p_crit
        if no_input == 'InCondT':
            cond_p_lb = RP.REFPROPdll(self.ref_fluid,'TQ','P',iUnit,0,0,OutCond.T,1.0,self.x_frac).Output[0]
        else:
            cond_p_lb = RP.REFPROPdll(self.ref_fluid,'TQ','P',iUnit,0,0,InCond.T,1.0,self.x_frac).Output[0]

        cond_a = 1
        while cond_a:
            InCond_REF.p = 0.5*(cond_p_ub+cond_p_lb)
            OutCond_REF.p = InCond_REF.p-inputs.cond_dp
            OutCond_REF.T = RP.REFPROPdll(self.ref_fluid,'PQ','T',iUnit,0,0,OutCond_REF.p,0.0,self.x_frac).Output[0]-inputs.DSC
            if inputs.DSC == 0:                
                OutCond_REF.h = RP.REFPROPdll(self.ref_fluid,'PQ','H',iUnit,0,0,OutCond_REF.p,inputs.DSC_x,self.x_frac).Output[0]
            else:
                OutCond_REF.h = RP.REFPROPdll(self.ref_fluid,'PT','H',iUnit,0,0,OutCond_REF.p,OutCond_REF.T,self.x_frac).Output[0]
            
            if InCond_REF.p > InCond_REF.p_crit*0.98:
                    self.cond_p_err = 1
                    break
            else:
                self.cond_p_err = 0
                
                comp = Compander_module(OutEvap_REF, InCond_REF, self.ref_fluid, self.x_frac)
                (inputs.DSH, cond_a) = comp.COMP(eff_isen = inputs.comp_eff, eff_mech = inputs.mech_eff, DSH = inputs.DSH)
                InCond_REF = comp.primary_out
                
                InEvap_REF.h = OutCond_REF.h
                InEvap_REF.T = RP.REFPROPdll(self.ref_fluid,'PH','T',iUnit,0,0,InEvap_REF.p,InEvap_REF.h,self.x_frac).Output[0]
                
            if (no_input == 'InCondT') or (no_input == 'OutCondT') or (no_input == 'Condm'):
                InEvap_REF.m =  InEvap.q/(InEvap_REF.h - OutEvap_REF.h)
                OutEvap_REF.m = InEvap_REF.m
                
                InCond_REF.m = InEvap_REF.m
                OutCond_REF.m = InEvap_REF.m
                outputs.Wcomp = comp.Pspecific*InCond_REF.m
                    
                InEvap_REF.q = -InEvap.q
                OutEvap_REF.q = -OutEvap.q
                
                InCond_REF.q = (OutCond_REF.h - InCond_REF.h)*InCond_REF.m
                OutCond_REF.q = InCond_REF.q
                InCond.q = -InCond_REF.q
                OutCond.q = -InCond_REF.q
                if no_input == 'InCondT':
                    InCond.h = OutCond.h - OutCond.q/OutCond.m
                    try:
                        [InCond.T, InCond.Cp] = RP.REFPROPdll(self.cond_fluid,'PH','T;C',iUnit,0,0,InCond.p,InCond.h,[1.0]).Output[:2]
                    except:    
                        InCond.T = OutCond.T
                        while 1:
                            [H_virtual, InCond.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;C',iUnit,0,0,InCond.p,InCond.T,[1.0]).Output[:2]
                            err_h = H_virtual - InCond.h
                            InCond.T = InCond.T - err_h/InCond.Cp
                            if err_h/InCond.h < 1.0e-5:
                                break
                elif no_input == 'OutCondT':
                    OutCond.h = InCond.h + InCond.q/InCond.m
                    try:
                        [OutCond.T, OutCond.Cp] = RP.REFPROPdll(self.cond_fluid,'PH','T;C',iUnit,0,0,OutCond.p,OutCond.h,[1.0]).Output[:2]
                    except:
                        OutCond.T = InCond.T
                        while 1:
                            [H_virtual, OutCond.Cp] = RP.REFPROPdll(self.cond_fluid,'TP','H;C',iUnit,0,0,OutCond.p,OutCond.T,[1.0]).Output[:2]
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
                
                InEvap_REF.m = InCond_REF.m
                OutEvap_REF.m = InCond_REF.m
                outputs.Wcomp = comp.Pspecific*InCond_REF.m
                
                InCond_REF.q = -InCond.q
                OutCond_REF.q = -InCond.q
                
                InEvap_REF.q = (OutEvap_REF.h - InEvap_REF.h)*InEvap_REF.m
                OutEvap_REF.q = InEvap_REF.q
                InEvap.q = -InEvap_REF.q
                OutEvap.q = -InEvap_REF.q
                
                if no_input == 'InEvapT':
                    InEvap.h = OutEvap.h - OutEvap.q/OutEvap.m
                    try:    
                        [InEvap.T, InEvap.Cp] = RP.REFPROPdll(self.evap_fluid,'PH','T;C',iUnit,0,0,InEvap.p,InEvap.h,[1.0]).Output[:2]
                    except:    
                        InEvap.T = OutEvap.T
                        while 1:
                            [H_virtual, InEvap.Cp] = RP.REFPROPdll(self.evap_fluid,'TP','H;C',iUnit,0,0,InEvap.p,InEvap.T,[1.0]).Output[:2]
                            err_h = H_virtual - InEvap.h
                            InEvap.T = InEvap.T - err_h/InEvap.Cp
                            if err_h/InEvap.h < 1.0e-5:
                                break
                            
                elif no_input == 'OutEvapT':
                    OutEvap.h = InEvap.h + InEvap.q/InEvap.m
                    try:
                        [OutEvap.T, OutEvap.Cp] = RP.REFPROPdll(self.evap_fluid,'PH','T;C',iUnit,0,0,OutEvap.p,OutEvap.h,[1.0]).Output[:2]
                    except:
                        OutEvap.T = InEvap.T
                        while 1:
                            [H_virtual, OutEvap.Cp] = RP.REFPROPdll(self.evap_fluid,'TP','H;C',iUnit,0,0,OutEvap.p,OutEvap.T,[1.0]).Output[:2]
                            err_h = H_virtual - OutEvap.h
                            OutEvap.T = OutEvap.T - err_h/OutEvap.Cp
                            if err_h/OutEvap.h < 1.0e-5:
                                break
                    
                elif no_input == 'Evapm':
                    InEvap.m = InEvap.q/(OutEvap.h - InEvap.h)
                    OutEvap.m = InEvap.m
                
            cond = Heatexchanger_module(InCond_REF, OutCond_REF, self.ref_fluid, self.x_frac, 1, InCond, OutCond, self.cond_fluid, [1.0], cond_ph)
        
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
            elif (cond_p_ub - cond_p_lb)/101300 < inputs.tol:
                self.cond_conv_err = 1
                cond_a = 0
        
        outputs.cond_UA = cond.UA 
        
        return (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs)
    
    def Plot_diagram(self, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, ts_file, ph_file, coeff):
        (p_array, h_array, T_array, s_array) = self.Dome_Draw(self.ref_fluid, self.x_frac, coeff)
        (p_points, h_points, T_points, s_points) = self.Diagram_Draw(InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF)
        
        ts_title = ''
        for k,w in self.ref_dict.items():
            ts_title = ts_title+k+':'+str(round(w*100))+'[w%];'
        
        fig_ph, ax_ph = PLT.subplots()
        ax_ph.plot([i/1.0e3/self.M_tot for i in h_array], [i/1.0e5 for i in p_array],'b--')
        ax_ph.set_xlabel('Enthalpy [kJ/kg]',fontsize = 15)
        ax_ph.set_ylabel('Pressure [bar]',fontsize = 15)
        ax_ph.set_title('Pressure-Enthalpy Diagram\nRefrigerant:{}'.format(ts_title),fontsize = 18)
        ax_ph.tick_params(axis = 'x', labelsize = 13)
        ax_ph.tick_params(axis = 'y', labelsize = 13)
        
        fig_ts, ax_ts = PLT.subplots()
        ax_ts.plot([i/1.0e3/self.M_tot for i in s_array], [i-273.15 for i in T_array],'r--')
        ax_ts.set_xlabel('Entropy [kJ/kg-K]',fontsize = 15)
        ax_ts.set_ylabel('Temperature [℃]',fontsize = 15)
        ax_ts.set_xlim([0 ,2])
        ax_ts.set_title('Temperature-Entropy Diagram\nRefrigerant:{}'.format(ts_title),fontsize = 18)
        ax_ts.tick_params(axis = 'x', labelsize = 13)
        ax_ts.tick_params(axis = 'y', labelsize = 13)
        
        ax_ts.plot([i/1.0e3/self.M_tot for i in s_points], [i-273.15 for i in T_points],'ro-')
        ax_ph.plot([i/1.0e3/self.M_tot for i in h_points], [i/1.0e5 for i in p_points],'bo-')
        
        fig_ph.savefig('.\\'+ph_file+'.png',dpi=300)
        fig_ts.savefig('.\\'+ts_file+'.png',dpi=300)
        
    def Dome_Draw(self, fluid, frac, coeff=0.999):
        [P_crit, T_crit] = RP.REFPROPdll(fluid,'CRIT','P;T',iUnit,0,0,0,0,frac).Output[:2]
        [H_crit_liq, S_crit_liq] = RP.REFPROPdll(fluid,'PQ','H;S',iUnit,0,0,P_crit*coeff,0,frac).Output[:2]
        [H_crit_vap, S_crit_vap] = RP.REFPROPdll(fluid,'PQ','H;S',iUnit,0,0,P_crit*coeff,1,frac).Output[:2]
        H_crit = 0.5*(H_crit_liq+H_crit_vap)
        S_crit = 0.5*(S_crit_liq+S_crit_vap)
        
        try:
            Pliq_array = [101300.0+(P_crit*coeff - 101300.0)*i/49 for i in range(50)]
            Pvap_array = [P_crit*coeff - (P_crit*coeff - 101300.0)*i/49 for i in range(50)]
            Tliq_array, hliq_array, sliq_array= [[RP.REFPROPdll(fluid,'PQ','T;H;S',iUnit,0,0,pl,0,frac).Output[j] for pl in Pliq_array] for j in range(3)]
            hliq_array_new = [(H_crit-hliq_array[i-1])/(P_crit-Pliq_array[i-1])*(Pliq_array[i]-Pliq_array[i-1])+hliq_array[i-1] if hliq_array[i] < 0 or hliq_array[i]/hliq_array[i-1] > 1.2 else hliq_array[i] for i in range(len(hliq_array))]
            sliq_array_new = [(H_crit-sliq_array[i-1])/(T_crit-Tliq_array[i-1])*(Tliq_array[i]-Tliq_array[i-1])+sliq_array[i-1] if sliq_array[i] < 0 or sliq_array[i]/sliq_array[i-1] > 1.2 else sliq_array[i] for i in range(len(sliq_array))]
            Tvap_array, hvap_array, svap_array= [[RP.REFPROPdll(fluid,'PQ','T;H;S',iUnit,0,0,pv,1,frac).Output[j] for pv in Pvap_array] for j in range(3)]
            hvap_array_new = [(H_crit-hvap_array[i-1])/(P_crit-Pvap_array[i-1])*(Pvap_array[i]-Pvap_array[i-1])+hvap_array[i-1] if hvap_array[i] < 0 or hvap_array[i-1]/hvap_array[i] > 1.2 else hvap_array[i] for i in range(len(hvap_array))]
            svap_array_new = [(H_crit-svap_array[i-1])/(T_crit-Tvap_array[i-1])*(Tvap_array[i]-Tvap_array[i-1])+svap_array[i-1] if svap_array[i] < 0 or svap_array[i-1]/svap_array[i] > 1.2 else svap_array[i] for i in range(len(svap_array))]
        except:
            P_trp = RP.REFPROPdll(fluid,'TRIPLE','P',iUnit,0,0,0,0,frac).Output[0]
            Pliq_array = [P_trp*(2-coeff)+(P_crit*coeff - P_trp*(2-coeff))*i/49 for i in range(50)]
            Pvap_array = [P_crit*coeff - (P_crit*coeff - P_trp*(2-coeff))*i/49 for i in range(50)]
            Tliq_array, hliq_array, sliq_array= [[RP.REFPROPdll(fluid,'PQ','T;H;S',iUnit,0,0,pl,0,frac).Output[j] for pl in Pliq_array] for j in range(3)]
            Tvap_array, hvap_array, svap_array= [[RP.REFPROPdll(fluid,'PQ','T;H;S',iUnit,0,0,pv,1,frac).Output[j] for pv in Pvap_array] for j in range(3)]
            
        p_array = Pliq_array+[P_crit]+Pvap_array
        T_array = Tliq_array+[T_crit]+Tvap_array
        h_array = hliq_array_new+[H_crit]+hvap_array_new
        s_array = sliq_array_new+[S_crit]+svap_array_new
        
        return (p_array, h_array, T_array, s_array)
    
    def Diagram_Draw(self, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF):
    
        OutEvap_REF_Tvap, OutEvap_REF_svap = RP.REFPROPdll(self.ref_fluid,'PQ','T;S',iUnit,0,0,OutEvap_REF.p,1,self.x_frac).Output[:2]
        InCond_REF_Tvap, InCond_REF_svap = RP.REFPROPdll(self.ref_fluid,'PQ','T;S',iUnit,0,0,InCond_REF.p,1,self.x_frac).Output[:2]
        OutCond_REF_Tliq, OutCond_REF_sliq = RP.REFPROPdll(self.ref_fluid,'PQ','T;S',iUnit,0,0,OutCond_REF.p,0,self.x_frac).Output[:2]
                
        OutCond_REF.s = RP.REFPROPdll(self.ref_fluid,'TP','S',iUnit,0,0,OutCond_REF.T,OutCond_REF.p,self.x_frac).Output[0]
        InEvap_REF.s = RP.REFPROPdll(self.ref_fluid,'HP','S',iUnit,0,0,InEvap_REF.h,InEvap_REF.p,self.x_frac).Output[0]
        
        s_points = [OutEvap_REF_svap, OutEvap_REF.s, InCond_REF.s, InCond_REF_svap, OutCond_REF_sliq, OutCond_REF.s, InEvap_REF.s, OutEvap_REF_svap]
        T_points = [OutEvap_REF_Tvap, OutEvap_REF.T, InCond_REF.T, InCond_REF_Tvap, OutCond_REF_Tliq, OutCond_REF.T, InEvap_REF.T, OutEvap_REF_Tvap]
        h_points = [OutEvap_REF.h, InCond_REF.h, OutCond_REF.h, InEvap_REF.h, OutEvap_REF.h]
        p_points = [OutEvap_REF.p, InCond_REF.p, OutCond_REF.p, InEvap_REF.p, OutEvap_REF.p]
        
        
        return (p_points, h_points, T_points, s_points)
            
            
    def Post_Processing(self, outputs):
        print('Heating COP:{:.3f}, Cooling COP:{:.3f}'.format(outputs.COP_heating, outputs.COP_heating-1))
        print('Refrigerant:{}, mass_fraction: {}, mole_fraction: {}'.format(self.ref_fluid, self.w_frac, self.x_frac))
        print('Q heating: {:.3f} [kW] ({:.3f} [usRT])'.format(self.OutCond.q/1000, self.OutCond.q/3516.8525))
        print('Q cooling: {:.3f} [kW] ({:.3f} [usRT])'.format(self.OutEvap_REF.q/1000, self.OutEvap_REF.q/3516.8525))
        print('Q comp: {:.3f} [kW]'.format(outputs.Wcomp/1000))
        print('Hot fluid Inlet T:{:.3f}[℃]/P:{:.3f}[bar]/m:{:.3f}[kg/s]:   -------> Hot fluid Outlet T:{:.3f}[℃]/P:{:.3f}[bar]/m:{:.3f}[kg/s]'.format(self.InCond.T-273.15, self.InCond.p/1.0e5, self.InCond.m*self.M_cond, self.OutCond.T-273.15, self.OutCond.p/1.0e5, self.OutCond.m*self.M_cond))
        print('Cold fluid Outlet T:{:.3f}[℃]/P:{:.3f}[bar]/m:{:.3f}[kg/s]: <------- Cold fluid Inlet T:{:.3f}[℃]/P:{:.3f}[bar]/m:{:.3f}[kg/s]'.format(self.OutEvap.T-273.15, self.OutEvap.p/1.0e5, self.OutEvap.m*self.M_evap, self.InEvap.T-273.15, self.InEvap.p/1.0e5, self.InEvap.m*self.M_evap))
        print('Pcomp_in: {:.3f} [bar], Pcomp_out: {:.3f} [bar]'.format(self.OutEvap_REF.p/1.0e5, self.InCond_REF.p/1.0e5))
        print('Pvalve_in: {:.3f} [bar], Pvalve_out: {:.3f} [bar]'.format(self.OutCond_REF.p/1.0e5, self.InEvap_REF.p/1.0e5))
        print('Tcomp_in: {:.3f} [℃], Tcomp_out: {:.3f} [℃]'.format(self.OutEvap_REF.T-273.15,self.InCond_REF.T-273.15))
        print('Tvalve_in: {:.3f} [℃], Tvalve_out: {:.3f} [℃]'.format(self.OutCond_REF.T-273.15,self.InEvap_REF.T-273.15))
        Tlow = RP.REFPROPdll(self.ref_fluid,'PQ','T',iUnit,0,0,0.5*(self.OutEvap_REF.p+self.InEvap_REF.p),0.5,self.x_frac).Output[0]
        try:
            Thigh = RP.REFPROPdll(self.ref_fluid,'PQ','T',iUnit,0,0,0.5*(self.OutCond_REF.p+self.InCond_REF.p),0.5,self.x_frac).Output[0]
        except:
            Thigh = 0
        print('Ts_low: {:.3f} [℃], Ts_high: {:.3f} [℃], mdot: {:.3f}[kg/s]'.format(Tlow-273.15,Thigh-273.15, self.OutEvap_REF.m*self.M_tot))
        print('Cond_UA: {:.3f} [W/℃], Evap_UA: {:.3f} [W/℃]'.format(outputs.cond_UA, outputs.evap_UA))


class Heatexchanger_module:
        
    def __init__(self, primary_in, primary_out, primary_fluid, primary_fraction, pph, secondary_in, secondary_out, secondary_fluid, secondary_fraction, sph):
        self.primary_in = primary_in
        self.primary_out = primary_out
        self.primary_fluid = primary_fluid
        self.primary_fraction = primary_fraction
        self.pph = pph
        self.secondary_in = secondary_in
        self.secondary_out = secondary_out
        self.secondary_fluid = secondary_fluid
        self.secondary_fraction = secondary_fraction
        self.sph = sph
        
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
                T_primary[i+1] = RP.REFPROPdll(self.primary_fluid,'HP','T',iUnit,0,0,h_primary[i+1],p_primary[i+1],self.primary_fraction).Output[0]
                if T_primary[i+1] < 0 or T_primary[i+1] > 1000:
                    h_primary_liq = RP.REFPROPdll(self.primary_fluid,'PQ','H',iUnit,0,0,p_primary[i+1],0.0,self.primary_fraction).Output[0]
                    T_primary_liq = RP.REFPROPdll(self.primary_fluid,'PQ','T',iUnit,0,0,p_primary[i+1],0.0,self.primary_fraction).Output[0]
                    h_primary_gas = RP.REFPROPdll(self.primary_fluid,'PQ','H',iUnit,0,0,p_primary[i+1],1.0,self.primary_fraction).Output[0]
                    T_primary_gas = RP.REFPROPdll(self.primary_fluid,'PQ','T',iUnit,0,0,p_primary[i+1],1.0,self.primary_fraction).Output[0]
                    T_primary[i+1] = (T_primary_gas*h_primary_gas+T_primary_liq*h_primary_liq)/(h_primary_gas + h_primary_liq)
            if self.sph == 0:
                T_secondary[i+1] = T_secondary[i] - self.secondary_in.q/N_element/self.secondary_in.m/0.5/(self.secondary_in.Cp + self.secondary_out.Cp)
            else: 
                h_secondary[i+1] = h_secondary[i] - self.secondary_in.q/N_element/self.secondary_in.m
                p_secondary[i+1] = p_secondary[i] + (self.secondary_in.p - self.secondary_out.p)/N_element
                T_secondary[i+1] = RP.REFPROPdll(self.secondary_fluid,'HP','T',iUnit,0,0,h_secondary[i+1],p_secondary[i+1],self.secondary_fraction).Output[0]
            
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


class Compander_module:
    
    def __init__(self, primary_in, primary_out, gas, x_frac):
        self.primary_in = primary_in
        self.primary_out = primary_out
        self.gas = gas
        self.x_frac = x_frac
        
    def COMP(self, eff_isen: float, eff_mech: float, DSH):
        h_comp_out_isen = RP.REFPROPdll(self.gas,'PS','H',iUnit,0,0,self.primary_out.p,self.primary_in.s, self.x_frac).Output[0]
        self.primary_out.h = (h_comp_out_isen - self.primary_in.h)/eff_isen + self.primary_in.h
        self.primary_out.T = RP.REFPROPdll(self.gas,'PH','T',iUnit,0,0,self.primary_out.p,self.primary_out.h,self.x_frac).Output[0]
        self.primary_out.s = RP.REFPROPdll(self.gas,'PT','S',iUnit,0,0,self.primary_out.p,self.primary_out.T,self.x_frac).Output[0]
        try:
            T_comp_out_sat = RP.REFPROPdll(self.gas,'PQ','T',iUnit,0,0,self.primary_out.p,1,self.x_frac).Output[0]
        except:
            T_comp_out_sat = self.primary_out.T_crit
        if abs(self.primary_out.T - T_comp_out_sat) < 1: # Overhanging problem protection
            DSH = DSH + 1.0
            cond_a = 0
        else:
            cond_a = 1
            
        self.Pspecific = (self.primary_out.h - self.primary_in.h)/eff_mech
        
        return (DSH, cond_a)
    
    
if __name__ == '__main__':   
    
    evapfluid = 'water'
    inevapT = 20+273.15
    inevapp = 110000.0
    evapm = 1.2/3600.0*RP.REFPROPdll(evapfluid,'TP','D',iUnit,0,0,inevapT,inevapp,[1.0]).Output[0]*RP.REFPROPdll(evapfluid,'','M',iUnit,0,0,0,0,[1.0]).Output[0]
    InEvap = ProcessFluid(m = evapm, T = inevapT, p = inevapp)
    
    outevapT = 15 + 273.15
    outevapp = 110000.0
    OutEvap = ProcessFluid(m = evapm, T = outevapT, p = outevapp)
    
    condfluid = 'water'
    incondT = 55.0 + 273.15
    incondp = 210000.0
    #condm = 1.89*RP.REFPROPdll(condfluid,'TP','D',iUnit,0,0,incondT,incondp,[1.0]).Output[0]/3600.0
    condm = 0
    InCond = ProcessFluid(m = condm, T = incondT, p = incondp)
    
    outcondT = 59.5 + 273.15
    outcondp = 101300.0
    OutCond = ProcessFluid(m = condm, T = outcondT, p = outcondp)
    
    
    inputs = Settings()
    
    inputs.DSH = 0.01
    inputs.DSC = 0.01
    inputs.cond_dp = 400.0e3
    inputs.evap_dp = 10.0e3
    inputs.cond_type = 'phe'
    inputs.evap_type = 'phe'
    inputs.cond_T_pp = 1.0
    inputs.evap_T_pp = 1.0
    inputs.comp_eff = 0.6
    inputs.mech_eff = 0.9
    
    
    ref_list = {'R32':0.191,'R1234yf':0.567,'R13I1':0.242}
    mix_cycle = VCHP(ref_list)
    (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs) = mix_cycle('water', 'water', InCond, OutCond, InEvap, OutEvap, inputs)
    
    mix_cycle.Post_Processing(outputs) 
    print(' ')
    print(' ')
    mix_cycle.Plot_diagram(InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, "TS_diagram_40bar", "PH_diagram_40bar", 0.92)