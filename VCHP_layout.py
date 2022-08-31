from copy import deepcopy
import HX_module as HX
import COMPAND_module as CP
from CoolProp.CoolProp import PropsSI
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
    
    def __call__(self):
        outputs = Outputs()
        
        InCond_REF = ProcessFluid(Y=self.inputs.Y)
        OutCond_REF = ProcessFluid(Y=self.inputs.Y)
        InEvap_REF = ProcessFluid(Y=self.inputs.Y)
        OutEvap_REF = ProcessFluid(Y=self.inputs.Y)
        
        try:
            self.nbp = PropsSI('T','P',101300,'Q',0.0, InEvap_REF.fluidmixture)
        except:
            return print('선택하신 냉매는 NBP를 구할 수 없습니다.')
        
        (self.InCond, self.OutCond, self.InEvap, self.OutEvap, no_input) = self.Input_Processing(self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.inputs)
        evap_ph = 0
        cond_ph = 0
        if self.inputs.layout == 'inj':    
            (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, outputs) = self.Injection_Solver(self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, self.inputs, outputs, no_input, cond_ph, evap_ph)
        else:
            (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, outputs) = self.Cycle_Solver(self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, self.inputs, outputs, no_input, cond_ph, evap_ph)
        
        self.Post_Processing(outputs)
        self.Plot_diagram(self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, self.inputs, outputs)
        
        
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
                InCond.p = 101300.0
        
            if OutCond.p <= 0.0:
             OutCond.p = 101300.0
             
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
            InEvap.p = 101300.0
        
        if OutEvap.p <= 0.0:
            OutEvap.p = 101300.0
        
        
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
                OutCond.h = PropsSI('H','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                OutCond.Cp = PropsSI('C','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                InEvap.h = PropsSI('H','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                InEvap.Cp = PropsSI('C','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                OutEvap.h = PropsSI('H','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                OutEvap.Cp = PropsSI('C','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                InEvap.q = (OutEvap.h - InEvap.h)*InEvap.m
                OutEvap.q = InEvap.q 
                no_input = 'InCondT'
            elif no_OutCondT == 1:
                InCond.h = PropsSI('H','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                InCond.Cp = PropsSI('C','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                InEvap.h = PropsSI('H','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                InEvap.Cp = PropsSI('C','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                OutEvap.h = PropsSI('H','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                OutEvap.Cp = PropsSI('C','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                InEvap.q = (OutEvap.h - InEvap.h)*InEvap.m
                OutEvap.q = InEvap.q 
                no_input = 'OutCondT'
            elif no_Condm == 1:
                InCond.h = PropsSI('H','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                InCond.Cp = PropsSI('C','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                OutCond.h = PropsSI('H','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                OutCond.Cp = PropsSI('C','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                InEvap.h = PropsSI('H','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                InEvap.Cp = PropsSI('C','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                OutEvap.h = PropsSI('H','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                OutEvap.Cp = PropsSI('C','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                InEvap.q = (OutEvap.h - InEvap.h)*InEvap.m
                OutEvap.q = InEvap.q 
                no_input = 'Condm'
            
            elif no_InEvapT == 1:
                InCond.h = PropsSI('H','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                InCond.Cp = PropsSI('C','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                OutCond.h = PropsSI('H','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                OutCond.Cp = PropsSI('C','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                OutEvap.h = PropsSI('H','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                OutEvap.Cp = PropsSI('C','T',OutEvap.T, 'P',OutEvap.p, OutEvap.fluidmixture)
                InCond.q = (OutCond.h - InCond.h)*InCond.m
                OutCond.q = InCond.q
                no_input = 'InEvapT'
            elif no_OutEvapT == 1:
                InCond.h = PropsSI('H','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                InCond.Cp = PropsSI('C','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                OutCond.h = PropsSI('H','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                OutCond.Cp = PropsSI('C','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                InEvap.h = PropsSI('H','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                InEvap.Cp = PropsSI('C','T',InEvap.T, 'P',InEvap.p, InEvap.fluidmixture)
                InCond.q = (OutCond.h - InCond.h)*InCond.m
                OutCond.q = InCond.q
                no_input = 'OutEvapT'
            elif no_Evapm == 1:
                InCond.h = PropsSI('H','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                InCond.Cp = PropsSI('C','T',InCond.T, 'P',InCond.p, InCond.fluidmixture)
                OutCond.h = PropsSI('H','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
                OutCond.Cp = PropsSI('C','T',OutCond.T, 'P',OutCond.p, OutCond.fluidmixture)
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
        OutCond.p = PropsSI('P','T',OutCond.T+0.1, 'Q', 0.0, InCond.fluidmixture)
        OutCond.h = PropsSI('H','T',OutCond.T+0.1, 'Q', 0.0, InCond.fluidmixture)
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
        rho_water = PropsSI('D','T',0.5*(inputs.T_makeup+inputs.T_target),'P',101300, InCond.fluidmixture)
        self.V_tank = inputs.M_load/rho_water
        InCond.p = 101300.0
        OutCond.p = 101300.0
        h_target = PropsSI('H','T',inputs.T_target,'P',101300.0,InCond.fluidmixture)
        h_makeup = PropsSI('H','T',inputs.T_makeup,'P',101300.0,InCond.fluidmixture)
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
                        
                        if inter_frac_ub - inter_frac_lb < inputs.tol: 
                            outputs.COP_heating = results_array[-1][0]
                            outputs.inter_frac = results_array[-1][1]
                            frac_a = 0
        
        return (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs)
    
    def Cycle_Solver(self,InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, no_input, cond_ph, evap_ph):
        if no_input == 'InEvapT':
            evap_p_ub = PropsSI('P','T',OutEvap.T, 'Q', 1.0, InEvap_REF.fluidmixture)        
        else:
            evap_p_ub = PropsSI('P','T',InEvap.T, 'Q', 1.0, InEvap_REF.fluidmixture)
            
        evap_p_lb = 101300.0
        evap_a = 1
        
        while evap_a: 
            OutEvap_REF.p = 0.5*(evap_p_lb+evap_p_ub)
            InEvap_REF.p = OutEvap_REF.p/(1.0-inputs.evap_dp)
            
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
                evap.FTHE(N_element = inputs.evap_N_element, N_row = inputs.evap_N_row)
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
                outputs.COP_heating = abs(OutCond.q)/(outputs.Wcomp - outputs.Wexpand)
                evap_a = 0
            elif evap_p_ub - evap_p_lb < inputs.tol:
                self.evap_conv_err = 1
                evap_a = 0
        
        outputs.DSH = OutEvap_REF.T - OutEvap_REF_Tvap
        
        return (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs)
        
    def HighPressure_Solver(self, InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs, no_input, cond_ph):
        if inputs.cycle == 'scc':
            cond_p_ub = min(2*InCond_REF.p_crit, 3.0e7)
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
            OutCond_REF.p = InCond_REF.p*(1-inputs.cond_dp)
            
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
                comp_low.COMP(eff_isen = inputs.comp_eff, eff_mech = inputs.mech_eff)
                OutComp_low = comp_low.primary_out
                
                InComp_high = deepcopy(OutComp_low)
                
                InComp_high.h = OutComp_low.h*(1.0-outputs.inter_x)+inter_h_vap*outputs.inter_x
                InComp_high.T = PropsSI('T','P',InComp_high.p,'H',InComp_high.h, InComp_high.fluidmixture)
                InComp_high.s = PropsSI('S','T',InComp_high.T, 'P', InComp_high.p, InComp_high.fluidmixture)
                
                comp_high = CP.Compander_module(InComp_high, InCond_REF)
                comp_high.COMP(eff_isen = inputs.comp_top_eff, eff_mech = inputs.mech_eff)
                InCond_REF = comp_high.primary_out
                
                OutExpand_high = deepcopy(OutCond_REF)
                OutExpand_high.p = inter_p
                expand_high = CP.Compander_module(OutCond_REF, OutExpand_high)
                expand_high.EXPAND(eff_isen=inputs.expand_eff, eff_mech = inputs.mech_eff)
                OutExpand_high = expand_high.primary_out
                
                Flash_liq = deepcopy(OutExpand_high) # 팽창 후 2-phase 중 liq 상만 두번째 팽창기 입구로
                Flash_liq.h = inter_h_liq
                Flash_liq.T = PropsSI('T','P',OutExpand_high.p,'Q',0.0, OutExpand_high.fluidmixture)
                if inputs.expand_bot_eff > 0.0:
                    Flash_liq.s = PropsSI('S','P',OutExpand_high.p,'Q',0.0, OutExpand_high.fluidmixture) 

                expand_low = CP.Compander_module(Flash_liq, InEvap_REF)
                expand_low.EXPAND(eff_isen=inputs.expand_bot_eff, eff_mech = inputs.mech_eff)
                InEvap_REF = expand_low.primary_out
            else:
                if inputs.layout == 'ihx':
                    InComp = deepcopy(OutEvap_REF)
                    InComp.p = InComp.p*(1.0-inputs.ihx_cold_dp)
                    InExpand = deepcopy(OutCond_REF)
                    InExpand.p = InExpand.p*(1.0-inputs.ihx_hot_dp)
                    IHX = HX.Heatexchanger_module(OutCond_REF, InExpand, 0, OutEvap_REF, InComp, 0)
                    IHX.SIMPHX(eff_HX = inputs.ihx_eff)
                
                    InExpand = IHX.primary_out
                    InComp = IHX.secondary_out
                else:    
                    InComp = OutEvap_REF
                    InExpand = OutCond_REF
                
                comp = CP.Compander_module(InComp, InCond_REF)
                comp.COMP(eff_isen = inputs.comp_eff, eff_mech = inputs.mech_eff)
                InCond_REF = comp.primary_out
                
                
                expand = CP.Compander_module(InExpand, InEvap_REF)
                expand.EXPAND(eff_isen = inputs.expand_eff, eff_mech = inputs.mech_eff)
                InEvap_REF = expand.primary_out
                
            if (no_input == 'InCondT') or (no_input == 'OutCondT') or (no_input == 'Condm'):
                InEvap_REF.m = InEvap.q/(InEvap_REF.h - OutEvap_REF.h)
                OutEvap_REF.m = InEvap_REF.m
                if inputs.layout == 'inj':
                    InCond_REF.m = InEvap_REF.m/(1.0-outputs.inter_x)
                    OutCond_REF.m = InCond_REF.m
                    outputs.Wcomp = comp_low.Pspecific*OutEvap_REF.m + comp_high.Pspecific*InCond_REF.m
                    outputs.Wcomp_top = comp_high.Pspecific*InCond_REF.m
                    outputs.Wexpand = expand_high.Pspecific*OutCond_REF.m + expand_low.Pspecific*InEvap_REF.m
                    outputs.Wexpand_bot = expand_low.Pspecific*InEvap_REF.m
                else:
                    InCond_REF.m = InEvap_REF.m
                    OutCond_REF.m = InEvap_REF.m
                    outputs.Wcomp = comp.Pspecific*InCond_REF.m
                    outputs.Wexpand = expand.Pspecific*InEvap_REF.m
                    
                InEvap_REF.q = -InEvap.q
                OutEvap_REF.q = -OutEvap.q
                
                InCond_REF.q = (OutCond_REF.h - InCond_REF.h)*InCond_REF.m
                OutCond_REF.q = InCond_REF.q
                InCond.q = -InCond_REF.q
                OutCond.q = -InCond_REF.q
                if no_input == 'InCondT':
                    InCond.h = OutCond.h - OutCond.q/OutCond.m
                    InCond.T = PropsSI('T','P',InCond.p, 'H', InCond.h, InCond.fluidmixture)
                    InCond.Cp = PropsSI('C','T',InCond.T, 'P', InCond.p, InCond.fluidmixture)
                elif no_input == 'OutCondT':
                    OutCond.h = InCond.h + InCond.q/InCond.m
                    OutCond.T = PropsSI('T','P',OutCond.p, 'H', OutCond.h, OutCond.fluidmixture)
                    OutCond.Cp = PropsSI('C','T',OutCond.T, 'P', OutCond.p, OutCond.fluidmixture)
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
                    outputs.Wcomp_top = comp_high.Pspecific*InCond_REF.m
                    outputs.Wexpand = expand_high.Pspecific*OutCond_REF.m + expand_low.Pspecific*InEvap_REF.m
                    outputs.Wexpand_bot = expand_low.Pspecific*InEvap_REF.m
                else:
                    InEvap_REF.m = InCond_REF.m
                    OutEvap_REF.m = InCond_REF.m
                    outputs.Wcomp = comp.Pspecific*InCond_REF.m
                    outputs.Wexpand = expand.Pspecific*InEvap_REF.m
                
                InCond_REF.q = -InCond.q
                OutCond_REF.q = -InCond.q
                
                InEvap_REF.q = (OutEvap_REF.h - InEvap_REF.h)*InEvap_REF.m
                OutEvap_REF.q = InEvap_REF.q
                InEvap.q = -InEvap_REF.q
                OutEvap.q = -InEvap_REF.q
                
                if no_input == 'InEvapT':
                    InEvap.h = OutEvap.h - OutEvap.q/OutEvap.m
                    InEvap.T = PropsSI('T','P',InEvap.p, 'H', InEvap.h, InEvap.fluidmixture)
                    InEvap.Cp = PropsSI('C','T',InEvap.T, 'P', InEvap.p, InEvap.fluidmixture)
                elif no_input == 'OutEvapT':
                    OutEvap.h = InEvap.h + InEvap.q/InEvap.m
                    OutEvap.T = PropsSI('T','P',OutEvap.p, 'H', OutEvap.h, OutEvap.fluidmixture)
                    OutEvap.Cp = PropsSI('C','T',OutEvap.T, 'P', OutEvap.p, OutEvap.fluidmixture)
                elif no_input == 'Evapm':
                    InEvap.m = InEvap.q/(OutEvap.h - InEvap.h)
                    OutEvap.m = InEvap.m
                
            cond = HX.Heatexchanger_module(InCond_REF, OutCond_REF, 1, InCond, OutCond, cond_ph)
        
            if inputs.cond_type == 'fthe':
                cond.FTHE(N_element=inputs.cond_N_element, N_row = inputs.cond_N_row)
                self.cond_err = (inputs.cond_T_lm - cond.T_lm)/inputs.cond_T_lm
                
            elif inputs.cond_type == 'phe':
                cond.PHE(N_element=inputs.cond_N_element)
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
            elif cond_p_ub - cond_p_lb < inputs.tol:
                self.cond_conv_err = 1
                cond_a = 0
        
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
        
        return (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, outputs)
    
    def Plot_diagram(self, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs):
        (p_array, h_array, T_array, s_array, p_points, h_points, s_points, T_points) = self.Dome_Draw(InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs)
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
        
        fig_ph.savefig('.\Figs\Ph_diagram.png',dpi=300)
        fig_ts.savefig('.\Figs\Ts_diagram.png',dpi=300)
        
    def Dome_Draw(self, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs):        
        P_crit = PropsSI('PCRIT','',0,'',0,InCond_REF.fluidmixture)
        P_trp = PropsSI('PTRIPLE','',0,'',0,InCond_REF.fluidmixture)
        T_crit = PropsSI('TCRIT','',0,'',0,InCond_REF.fluidmixture)
        H_crit = 0.5*(PropsSI('H','P',P_crit*0.999,'Q',0.0,InCond_REF.fluidmixture)+PropsSI('H','P',P_crit*0.999,'Q',1.0,InCond_REF.fluidmixture))
        S_crit = 0.5*(PropsSI('S','P',P_crit*0.999,'Q',0.0,InCond_REF.fluidmixture)+PropsSI('S','P',P_crit*0.999,'Q',1.0,InCond_REF.fluidmixture))
        
        try:
            Pliq_array = [101300.0+(P_crit*0.99 - 101300.0)*i/49 for i in range(50)]
            Pvap_array = [P_crit*0.99 - (P_crit*0.99 - 101300.0)*i/49 for i in range(50)]
            Tliq_array = [PropsSI('T','P',i,'Q',0.0,InCond_REF.fluidmixture) for i in Pliq_array]
            Tvap_array = [PropsSI('T','P',i,'Q',1.0,InCond_REF.fluidmixture) for i in Pvap_array]
            hliq_array = [PropsSI('H','P',i,'Q',0.0,InCond_REF.fluidmixture) for i in Pliq_array]
            hvap_array = [PropsSI('H','P',i,'Q',1.0,InCond_REF.fluidmixture) for i in Pvap_array]
            sliq_array = [PropsSI('S','P',i,'Q',0.0,InCond_REF.fluidmixture) for i in Pliq_array]
            svap_array = [PropsSI('S','P',i,'Q',1.0,InCond_REF.fluidmixture) for i in Pvap_array]
        except:
            Pliq_array = [P_trp*1.01+(P_crit*0.99 - P_trp*1.01)*i/49 for i in range(50)]
            Pvap_array = [P_crit*0.99 - (P_crit*0.99 - P_trp*1.01)*i/49 for i in range(50)]
            Tliq_array = [PropsSI('T','P',i,'Q',0.0,InCond_REF.fluidmixture) for i in Pliq_array]
            Tvap_array = [PropsSI('T','P',i,'Q',1.0,InCond_REF.fluidmixture) for i in Pvap_array]
            hliq_array = [PropsSI('H','P',i,'Q',0.0,InCond_REF.fluidmixture) for i in Pliq_array]
            hvap_array = [PropsSI('H','P',i,'Q',1.0,InCond_REF.fluidmixture) for i in Pvap_array]
            sliq_array = [PropsSI('S','P',i,'Q',0.0,InCond_REF.fluidmixture) for i in Pliq_array]
            svap_array = [PropsSI('S','P',i,'Q',1.0,InCond_REF.fluidmixture) for i in Pvap_array]
            
        p_array = Pliq_array+[P_crit]+Pvap_array
        T_array = Tliq_array+[T_crit]+Tvap_array
        h_array = hliq_array+[H_crit]+hvap_array
        s_array = sliq_array+[S_crit]+svap_array
        
        OutEvap_REF_Tvap = PropsSI('T','P',OutEvap_REF.p,'Q',1.0,OutCond_REF.fluidmixture)
        OutEvap_REF_svap = PropsSI('S','P',OutEvap_REF.p,'Q',1.0,OutCond_REF.fluidmixture)
        
        if inputs.cycle == 'vcc':
            InCond_REF_Tvap = PropsSI('T','P',InCond_REF.p,'Q',1.0,OutCond_REF.fluidmixture)
            InCond_REF_svap = PropsSI('S','P',InCond_REF.p,'Q',1.0,OutCond_REF.fluidmixture)
            OutCond_REF_Tliq = PropsSI('T','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture)
            OutCond_REF_sliq = PropsSI('S','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture)
        
        OutCond_REF.s = PropsSI('S','T',OutCond_REF.T,'P',OutCond_REF.p,OutCond_REF.fluidmixture)
        InEvap_REF.s = PropsSI('S','H',InEvap_REF.h,'P',InEvap_REF.p,InEvap_REF.fluidmixture)
        
        if inputs.layout == 'ihx':
            if inputs.cycle == 'vcc':
                s_points = [OutEvap_REF_svap, OutEvap_REF.s, outputs.ihx_cold_out_s, InCond_REF.s, InCond_REF_svap, OutCond_REF_sliq, OutCond_REF.s, outputs.ihx_hot_out_s, InEvap_REF.s, OutEvap_REF_svap]
                T_points = [OutEvap_REF_Tvap, OutEvap_REF.T, outputs.ihx_cold_out_T, InCond_REF.T, InCond_REF_Tvap, OutCond_REF_Tliq, OutCond_REF.T, outputs.ihx_hot_out_T, InEvap_REF.T, OutEvap_REF_Tvap]
            else:
                s_points = [OutEvap_REF_svap, OutEvap_REF.s, outputs.ihx_cold_out_s, InCond_REF.s, OutCond_REF.s, outputs.ihx_hot_out_s, InEvap_REF.s, OutEvap_REF_svap]
                T_points = [OutEvap_REF_Tvap, OutEvap_REF.T, outputs.ihx_cold_out_T, InCond_REF.T, OutCond_REF.T, outputs.ihx_hot_out_T, InEvap_REF.T, OutEvap_REF_Tvap]
            
            h_points = [OutEvap_REF.h, outputs.ihx_cold_out_h, InCond_REF.h, OutCond_REF.h, outputs.ihx_hot_out_h, InEvap_REF.h, OutEvap_REF.h]
            p_points = [OutEvap_REF.p, outputs.ihx_cold_out_p, InCond_REF.p, OutCond_REF.p, outputs.ihx_hot_out_p, InEvap_REF.p, OutEvap_REF.p]
        elif inputs.layout == 'inj':
            outcomp_low_svap = PropsSI('S','P',outputs.outcomp_low_p,'Q',1.0,InCond_REF.fluidmixture)
            outcomp_low_Tvap = PropsSI('T','P',outputs.outcomp_low_p,'Q',1.0,InCond_REF.fluidmixture)
            outputs.flash_liq_s = PropsSI('S','P',outputs.flash_liq_p,'Q',0.0,InCond_REF.fluidmixture)
            outputs.outexpand_high_s = PropsSI('S','P',outputs.outexpand_high_p,'H',outputs.outexpand_high_h,InCond_REF.fluidmixture)
            if inputs.cycle == 'vcc':    
                s_points = [outputs.flash_liq_s, InEvap_REF.s, OutEvap_REF_svap, OutEvap_REF.s, outputs.outcomp_low_s, outcomp_low_svap, outputs.flash_liq_s, outputs.outexpand_high_s, outcomp_low_svap, outputs.incomp_high_s, InCond_REF.s, InCond_REF_svap, OutCond_REF_sliq, OutCond_REF.s, outputs.outexpand_high_s] 
                T_points = [outputs.flash_liq_T, InEvap_REF.T, OutEvap_REF_Tvap, OutEvap_REF.T, outputs.outcomp_low_T, outcomp_low_Tvap, outputs.flash_liq_T, outputs.outexpand_high_T, outcomp_low_Tvap, outputs.incomp_high_T, InCond_REF.T, InCond_REF_Tvap, OutCond_REF_Tliq, OutCond_REF.T, outputs.outexpand_high_T] 
            else:
                s_points = [outputs.flash_liq_s, InEvap_REF.s, OutEvap_REF_svap, OutEvap_REF.s, outputs.outcomp_low_s, outcomp_low_svap, outputs.flash_liq_s, outputs.outexpand_high_s, outcomp_low_svap, outputs.incomp_high_s, InCond_REF.s, OutCond_REF.s, outputs.outexpand_high_s] 
                T_points = [outputs.flash_liq_T, InEvap_REF.T, OutEvap_REF_Tvap, OutEvap_REF.T, outputs.outcomp_low_T, outcomp_low_Tvap, outputs.flash_liq_T, outputs.outexpand_high_T, outcomp_low_Tvap, outputs.incomp_high_T, InCond_REF.T, OutCond_REF.T, outputs.outexpand_high_T] 
                
            h_points = [outputs.flash_liq_h, InEvap_REF.h, OutEvap_REF.h, outputs.outcomp_low_h, outputs.flash_liq_h, outputs.outexpand_high_h, outputs.incomp_high_h, InCond_REF.h, OutCond_REF.h, outputs.outexpand_high_h]
            p_points = [outputs.flash_liq_p, InEvap_REF.p, OutEvap_REF.p, outputs.outcomp_low_p, outputs.flash_liq_p, outputs.outexpand_high_p, outputs.incomp_high_p, InCond_REF.p, OutCond_REF.p, outputs.outexpand_high_p]
        else:
            if inputs.cycle == 'vcc':
                s_points = [OutEvap_REF_svap, OutEvap_REF.s, InCond_REF.s, InCond_REF_svap, OutCond_REF_sliq, OutCond_REF.s, InEvap_REF.s, OutEvap_REF_svap]
                T_points = [OutEvap_REF_Tvap, OutEvap_REF.T, InCond_REF.T, InCond_REF_Tvap, OutCond_REF_Tliq, OutCond_REF.T, InEvap_REF.T, OutEvap_REF_Tvap]
            else:
                s_points = [OutEvap_REF_svap, OutEvap_REF.s, InCond_REF.s, OutCond_REF.s, InEvap_REF.s, OutEvap_REF_svap]
                T_points = [OutEvap_REF_Tvap, OutEvap_REF.T, InCond_REF.T, OutCond_REF.T, InEvap_REF.T, OutEvap_REF_Tvap]
                
            h_points = [OutEvap_REF.h, InCond_REF.h, OutCond_REF.h, InEvap_REF.h, OutEvap_REF.h]
            p_points = [OutEvap_REF.p, InCond_REF.p, OutCond_REF.p, InEvap_REF.p, OutEvap_REF.p]
        
        
        return (p_array, h_array, T_array, s_array, p_points, h_points, s_points, T_points)
            
            
    def Post_Processing(self, outputs):
        print('Heating COP:{:.3f}, Cooling COP:{:.3f}'.format(outputs.COP_heating, outputs.COP_heating-1))
        print('Refrigerant:{}'.format(self.OutCond_REF.fluidmixture))
        print('Q heating: {:.2f} [kW] ({:.2f} [usRT])'.format(self.OutCond.q/1000, self.OutCond.q/3516.8525))
        print('Q cooling: {:.2f} [kW] ({:.2f} [usRT])'.format(self.OutEvap_REF.q/1000, self.OutEvap_REF.q/3516.8525))
        print('Hot fluid Inlet T:{:.2f}[℃]/P:{:.2f}[bar]/m:{:.2f}[kg/s]:   -------> Hot fluid Outlet T:{:.2f}[℃]/P:{:.2f}[bar]/m:{:.2f}[kg/s]'.format(self.InCond.T, self.InCond.p/1.0e5, self.InCond.m, self.OutCond.T, self.OutCond.p, self.OutCond.m))
        print('Cold fluid Outlet T:{:.2f}[℃]/P:{:.2f}[bar]/m:{:.2f}[kg/s]: <------- Cold fluid Inlet T:{:.2f}[℃]/P:{:.2f}[bar]/m:{:.2f}[kg/s]'.format(self.OutEvap.T, self.OutEvap.p/1.0e5, self.OutEvap.m, self.InEvap.T, self.InEvap.p, self.InEvap.m))
        print('Plow: {:.2f} [bar], Phigh: {:.2f} [bar], mdot: {:.2f}[kg/s]'.format(self.OutEvap_REF.p/1.0e5, self.InCond_REF.p/1.0e5, self.OutEvap_REF.m))
      
class VCHP_cascade(VCHP):
    def __init__(self, InCond, OutCond, InEvap, OutEvap, inputs_t, inputs_b):
        self.InCond = InCond
        self.OutCond = OutCond
        self.InEvap = InEvap
        self.OutEvap = OutEvap
        self.inputs_t = inputs_t
        self.inputs_b = inputs_b
    
    def __call__(self):
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
        
        self.nbp = 0.0
        cond_t_ph = 0
        evap_b_ph = 0
        
        (self.InCond, self.OutCond, self.InEvap, self.OutEvap, no_input) = self.Input_Processing(self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.inputs_t)
        (self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, outputs_t, outputs_b) = self.Cascade_solver(self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, self.inputs_t, self.inputs_b, outputs_t, outputs_b, no_input, cond_t_ph, evap_b_ph)
        self.Plot_diagram(InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, self.inputs_t, outputs_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, self.inputs_b, outputs_b)        
    
    def Input_Processing(self, InCond, OutCond, InEvap, OutEvap, inputs):
        return super().Input_Processing(InCond, OutCond, InEvap, OutEvap, inputs)
    
    def Cascade_solver(self, InCond, OutCond, InEvap, OutEvap, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, inputs_t, inputs_b, outputs_t, outputs_b, no_input, cond_t_ph, evap_b_ph):
        devap = 0.005
        cascade_a = 1
        evap_t_p_lb = 101300.0
        cond_b_ph = 1
        results_array = []
    
        if no_input == 'InCondT':
            evap_t_p_ub = PropsSI('P','T',OutCond.T,'Q',1.0, OutEvap_REF_t.fluidmixture) 
        else:
            evap_t_p_ub = PropsSI('P','T',InCond.T,'Q',1.0, OutEvap_REF_t.fluidmixture)
    
        evap_t_p_ub = min(evap_t_p_ub, OutEvap_REF_t.p_crit)
    
        while cascade_a:
            for ii in range(2):
                if ii == 0:
                    OutEvap_REF_t.p = 0.5*(evap_t_p_lb + evap_t_p_ub)*(1-devap)
                else:
                    OutEvap_REF_t.p = 0.5*(evap_t_p_lb + evap_t_p_ub)*(1+devap)
                    
                InEvap_REF_t.p = OutEvap_REF_t.p/(1.0 - inputs_t.evap_dp)
                
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
                        cond_p_ub = min(2*InCond_REF_t.p_crit, 3.0e7)
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
                            InCond.T = PropsSI('T','P',InCond.p, 'H', InCond.h, InCond.fluidmixture)
                            InCond.Cp = PropsSI('C','T',InCond.T, 'P', InCond.p, InCond.fluidmixture)
                        elif no_input == 'OutCondT':
                            OutCond.h = InCond.h + InCond.q/InCond.m
                            OutCond.T = PropsSI('T','P',OutCond.p, 'H', OutCond.h, OutCond.fluidmixture)
                            OutCond.Cp = PropsSI('C','T',OutCond.T, 'P', OutCond.p, OutCond.fluidmixture)
                        elif no_input == 'Condm':
                            InCond.m = InCond.q/(OutCond.h - InCond.h)
                            OutCond.m = InCond.m

                        cond_t = HX.Heatexchanger_module(InCond_REF_t, OutCond_REF_t, 1, InCond, OutCond, cond_t_ph)
                        
                        if inputs_t.cond_type == 'fthe':
                            cond_t.FTHE(N_element=inputs_t.cond_N_element, N_row = inputs_t.cond_N_row)
                            cond_err = (inputs_t.cond_T_lm - cond_t.T_lm)/inputs_t.cond_T_lm
                            
                        elif inputs_t.cond_type == 'phe':
                            cond_t.PHE(N_element=inputs_t.cond_N_element)
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
                                OutEvap_REF_t.p = results_array[-2][1]
                                cascade_a = 0
                            elif abs(results_array[-1][2]) < inputs_t.tol:
                                COP_cascade = results_array[-1][0]
                                OutEvap_REF_t.p = results_array[-1][1]
                                cascade_a = 0
                        
                        if evap_t_p_ub - evap_t_p_lb < inputs_t.tol: 
                            COP_cascade = results_array[-1][0]
                            OutEvap_REF_t.p = results_array[-1][1]
                            cascade_a = 0
        
        outputs_t.DSH = OutEvap_REF_t.T - OutEvap_REF_t_Tvap
        
        return(InCond, OutCond, InEvap, OutEvap, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, outputs_t, outputs_b)
    
    def TopCycle_HighPressure_solver(self, cond_p_lb, cond_p_ub, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, inputs, outputs):
        
        InCond_REF.p = 0.5*(cond_p_ub+cond_p_lb)
        OutCond_REF.p = InCond_REF.p*(1-inputs.cond_dp)
        
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
            InComp.p = InComp.p*(1.0-inputs.ihx_cold_dp)
            InExpand = deepcopy(OutCond_REF)
            InExpand.p = InExpand.p*(1.0-inputs.ihx_hot_dp)
            IHX = HX.Heatexchanger_module(OutCond_REF, InExpand, 0, OutEvap_REF, InComp, 0)
            IHX.SIMPHX(eff_HX = inputs.ihx_eff)
        
            InExpand = IHX.primary_out
            InComp = IHX.secondary_out
        else:    
            InComp = OutEvap_REF
            InExpand = OutCond_REF
            
        comp = CP.Compander_module(InComp, InCond_REF)
        comp.COMP(eff_isen = inputs.comp_eff, eff_mech = inputs.mech_eff)
        InCond_REF = comp.primary_out
        
        
        expand = CP.Compander_module(InExpand, InEvap_REF)
        expand.EXPAND(eff_isen = inputs.expand_eff, eff_mech = inputs.mech_eff)
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
        outputs.Wexpand = expand.Pspecific
        
        return (InCond_REF, OutCond_REF, InEvap_REF, outputs)
    
    def Plot_diagram(self, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, inputs_t, outputs_t, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, inputs_b, outputs_b):
        (p_array_t, h_array_t, T_array_t, s_array_t, p_points_t, h_points_t, s_points_t, T_points_t) = super().Dome_Draw(InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, inputs_t, outputs_t)
        (p_array_b, h_array_b, T_array_b, s_array_b, p_points_b, h_points_b, s_points_b, T_points_b) = super().Dome_Draw(InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, inputs_b, outputs_b)
        
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
        
        fig_ph.savefig('.\Figs\Ph_diagram.png',dpi=300)
        fig_ts.savefig('.\Figs\Ts_diagram.png',dpi=300)  
                    
                                    
if __name__ == '__main__':
    '''
    evapfluid = 'water'
    inevapT = 333.15
    inevapp = 101300.0
    InEvap = ProcessFluid(Y={evapfluid:1.0,},m = 1.0, T = inevapT, p = inevapp)
    
    outevapp = 101300.0
    OutEvap = ProcessFluid(Y={evapfluid:1.0,},p = outevapp)
    
    condfluid = 'water'
    incondT = 323.15
    incondp = 301300.0
    InCond = ProcessFluid(Y={condfluid:1.0,},m = 1.0, T = incondT, p = incondp)
    
    outcondT = 413.15
    outcondp = 301300.0
    outcondh = PropsSI('H','T',outcondT, 'P', outcondp, condfluid)
    outconds = PropsSI('S','T',outcondT, 'P', outcondp, condfluid)
    OutCond = ProcessFluid(Y={condfluid:1.0,},m = 1.0, T = outcondT, p = outcondp, q = 0.0, h = outcondh, s = outconds)
    
    inputs = Settings()
    inputs.Y = {'R245FA':1.0,}
    inputs.second = 'steam'
    inputs.cycle = 'vcc'
    inputs.cond_type = 'phe'
    inputs.evap_type = 'phe'
    inputs.layout = 'bas'
    
    vchp_basic = VCHP(InCond, OutCond, InEvap, OutEvap, inputs)
    '''
    
    evapfluid = 'water'
    inevapT = 323.15
    inevapp = 101300.0
    InEvap = ProcessFluid(Y={evapfluid:1.0,},m = 1.0, T = inevapT, p = inevapp)
    
    outevapT = 313.15
    outevapp = 101300.0
    OutEvap = ProcessFluid(Y={evapfluid:1.0,})
    
    condfluid = 'water'
    incondT = 343.15
    incondp = 101300.0
    InCond = ProcessFluid(Y={condfluid:1.0,},m = 1.0, T = incondT, p = incondp)
    
    outcondT = 353.15
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
    inputs_b.Y = {'R134A':1.0,}
    inputs_b.second = 'process'
    inputs_b.cycle = 'vcc'
    inputs_b.cond_type = 'phe'
    inputs_b.evap_type = 'phe'
    inputs_b.layout = 'bas'
    
    vchp_cascade = VCHP_cascade(InCond, OutCond, InEvap, OutEvap, inputs_t, inputs_b)
    
    from cProfile import Profile
    
    profiler = Profile()
    profiler.run('vchp_cascade()')
    
    from pstats import Stats
    
    stats = Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats('cumulative')
    stats.print_stats()
    