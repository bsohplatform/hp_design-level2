from copy import deepcopy
import HX_module as HX
import COMPAND_module as CP
from CoolProp.CoolProp import PropsSI
# test 용 import
from HP_dataclass import ProcessFluid, Settings


class VCHP():
    def __init__(self, InCond, OutCond, InEvap, OutEvap, inputs):
        self.InCond = InCond
        self.OutCond = OutCond
        self.InEvap = InEvap
        self.OutEvap = OutEvap
        self.inputs = inputs
    
    def __call__(self):
        
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
            (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF) = self.Injection_Solver(self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, self.inputs, no_input, cond_ph, evap_ph)
        else:
            (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF) = self.Cycle_Solver(self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, self.inputs, no_input, cond_ph, evap_ph)
        
        self.Post_Processing()
            
    def Input_Processing(self, InCond, OutCond, InEvap, OutEvap, Inputs):
        no_InCondT = 0
        no_Condm = 0
        no_OutCondT = 0
        no_InEvapT = 0
        no_Evapm = 0
        no_OutEvapT = 0
        
        
        if Inputs.second == 'steam':
            (InCond, OutCond) = self.Steam_module(InCond, OutCond, Inputs)
            
        elif Inputs.second == 'hotwater':
            (InCond, OutCond) = self.Hotwater_module(InCond, OutCond, Inputs)
        
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
            return print('입력 변수가 Overdefine 됐습니다.')
        elif no_inputs_sum > 1:
            return print('입력 변수가 Underdefine 됐습니다.')
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
            
            if no_input == 'InEvapT':
                if Inputs.evap_type == 'fthe':
                    if self.nbp > OutEvap.T - Inputs.cond_T_lm:
                        return print('냉매 NBP가 공정 저온 온도 보다 높습니다.')
                elif Inputs.evap_type == 'phe':
                    if self.nbp > OutEvap.T - Inputs.cond_T_pp:
                        return print('냉매 NBP가 공정 저온 온도 보다 높습니다.')
                else: 
                    print('정의되지 않은 열교환기 타입입니다.')
                
            else:
                if Inputs.evap_type == 'fthe':
                    if self.nbp > InEvap.T - Inputs.evap_T_lm:
                        return print('냉매 NBP가 공정 저온 온도 보다 높습니다.')
                elif Inputs.evap_type == 'phe':
                    if self.nbp > InEvap.T - Inputs.evap_T_pp:
                        return print('냉매 NBP가 공정 저온 온도 보다 높습니다.')
                else: 
                    print('정의되지 않은 열교환기 타입입니다.')
        return (InCond, OutCond, InEvap, OutEvap, no_input)
                
    def Steam_module(self, InCond, OutCond, Inputs):
        p_flash = PropsSI('P','T',Inputs.T_steam,'Q',1.0, InCond.fluidmixture)
        OutCond.p = PropsSI('P','T',OutCond.T+0.1, 'Q', 0.0, InCond.fluidmixture)
        OutCond.h = PropsSI('H','T',OutCond.T+0.1, 'Q', 0.0, InCond.fluidmixture)
        X_flash = PropsSI('Q','H',OutCond.h,'P',p_flash, InCond.fluidmixture)
        OutCond.m = Inputs.m_steam / X_flash
        InCond.m = OutCond.m
        m_sat_liq = (1-X_flash)*OutCond.m
        h_sat_liq = PropsSI('H','P',p_flash,'Q',0.0, InCond.fluidmixture)
        h_makeup = PropsSI('H','T',Inputs.T_makeup,'P',p_flash, InCond.fluidmixture)
        
        InCond.h = (m_sat_liq*h_sat_liq + Inputs.m_makeup*h_makeup)/OutCond.m
        InCond.T = PropsSI('T','H',InCond.h,'P',p_flash, InCond.fluidmixture)
        
        return (InCond, OutCond)
        
    def Hotwater_module(self, InCond, OutCond, Inputs):
        rho_water = PropsSI('D','T',0.5*(Inputs.T_makeup+Inputs.T_target),'P',101300, InCond.fluidmixture)
        self.V_tank = Inputs.M_load/rho_water
        
        h_target = PropsSI('H','T',Inputs.T_target,'P',101300.0,InCond.fluidmixture)
        h_makeup = PropsSI('H','T',Inputs.T_makeup,'P',101300.0,InCond.fluidmixture)
        InCond.h = 0.5*(h_target + h_makeup)
        InCond.T = PropsSI('T','H',InCond.h,'P',101300, InCond.fluidmixture)
        Cp_water = PropsSI('C','T',InCond.T,'P',101300, InCond.fluidmixture)
        OutCond.q = 0.5*Inputs.M_load*Cp_water*(Inputs.T_target - InCond.T)/Inputs.time_target
        OutCond.m = OutCond.q/(Cp_water*Inputs.dT_lift)
        OutCond.T = InCond.T + Inputs.dT_lift
        
        return (InCond, OutCond)
    
    def Injection_Solver(self, InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, Inputs, no_input, cond_ph, evap_ph):
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
                
                (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF) = self.Cycle_Solver(InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, Inputs, no_input, cond_ph, evap_ph)
                
                if self.evap_conv_err == 1:
                    if self.evap_err > 0:
                        inter_frac_lb = self.inter_frac
                        break
                else:
                    if iii == 0:
                        COP_o = self.COP_heating
                        frac_o = self.inter_frac
                    else:
                        dCOP = ((self.COP_heating - COP_o)/self.COP_heating)/((self.inter_frac - frac_o)/self.inter_frac)
                        if dCOP > 0:
                            inter_frac_lb = self.inter_frac
                        else:
                            inter_frac_ub = self.inter_frac
                           
                        results_array.append([0.5*(COP_o + self.COP_heating), 0.5*(frac_o + self.inter_frac), dCOP])
                        
                        if len(results_array) > 2:
                            if results_array[-2][0] > results_array[-1][0] and results_array[-2][0] > results_array[-3][0]:
                                self.COP_heating = results_array[-2][0]
                                self.inter_frac = results_array[-2][0]
                                frac_a = 0
                            elif abs(results_array[-1][2]) < Inputs.tol:
                                self.COP_heating = results_array[-1][0]
                                self.inter_frac = results_array[-1][1]
                                frac_a = 0
                        
                        if inter_frac_ub - inter_frac_lb < Inputs.tol:
                            self.COP_heating = results_array[-1][0]
                            self.inter_frac = results_array[-1][1]
                            frac_a = 0
        
        return (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF)                
            
    def Cycle_Solver(self,InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, Inputs, no_input, cond_ph, evap_ph):
        if no_input == 'InEvapT':
            evap_p_ub = PropsSI('P','T',OutEvap.T, 'Q', 1.0, InEvap_REF.fluidmixture)        
        else:
            evap_p_ub = PropsSI('P','T',InEvap.T, 'Q', 1.0, InEvap_REF.fluidmixture)
            
        evap_p_lb = 101300.0
        evap_a = 1
        
        while evap_a: 
            OutEvap_REF.p = 0.5*(evap_p_lb+evap_p_ub)
            InEvap_REF.p = OutEvap_REF.p/(1.0-Inputs.evap_dp)
            
            OutEvap_REF.T = PropsSI('T','P',OutEvap_REF.p, 'Q', 1.0, OutEvap_REF.fluidmixture) + Inputs.DSH
            if Inputs.DSH == 0:
                OutEvap_REF.h = PropsSI('H','P',OutEvap_REF.p, 'Q', 1.0, OutEvap_REF.fluidmixture)
                OutEvap_REF.s = PropsSI('S','P',OutEvap_REF.p, 'Q', 1.0, OutEvap_REF.fluidmixture)
            else:
                OutEvap_REF.h = PropsSI('H','T',OutEvap_REF.T, 'P', OutEvap_REF.p ,OutEvap_REF.fluidmixture)
                OutEvap_REF.s = PropsSI('S','T',OutEvap_REF.T, 'P', OutEvap_REF.p ,OutEvap_REF.fluidmixture)
            
            (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF) = self.HighPressure_Solver(InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, Inputs, no_input, cond_ph)
            
            evap = HX.Heatexchanger_module(InEvap_REF, OutEvap_REF, 1, InEvap, OutEvap, evap_ph)
            
            if Inputs.evap_type == 'fthe':
                evap.FTHE(N_element = Inputs.evap_N_element, N_row = Inputs.evap_N_row)
                self.evap_err = (Inputs.evap_T_lm - evap.T_lm)/Inputs.evap_T_lm
            elif Inputs.evap_type == 'phe':
                evap.PHE(N_element= Inputs.evap_N_element)
                self.evap_err = (Inputs.evap_T_pp - evap.T_pp)/Inputs.evap_T_pp
            
            OutEvap_REF = evap.primary_out
            
            if evap.T_rvs == 1:
                evap_p_ub = OutEvap_REF.p                    
            else:
                if self.evap_err < 0:
                    evap_p_lb = OutEvap_REF.p
                else:
                    evap_p_ub = OutEvap_REF.p
                    
            if abs(self.evap_err) < Inputs.tol:
                self.evap_conv_err = 0
                self.COP_heating = abs(OutCond.q)/(self.compPower - self.expandPower)
                self.COP_cooling = abs(OutEvap.q)/(self.compPower - self.expandPower)
                evap_a = 0
            elif evap_p_ub - evap_p_lb < Inputs.tol:
                self.evap_conv_err = 1
                evap_a = 0
        
        return (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF)
        
    def HighPressure_Solver(self, InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, Inputs, no_input, cond_ph):
        if Inputs.cycle == 'scc':
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
            OutCond_REF.p = InCond_REF.p*(1-Inputs.cond_dp)
            
            if OutCond_REF.p > OutCond_REF.p_crit:
                OutCond_REF.T = 0.10753154*((OutCond_REF.p - OutCond_REF.p_crit)/OutCond_REF.p_crit) + 0.004627621995008088
                OutCond_REF.T = OutCond_REF.T*OutCond_REF.T_crit + OutCond_REF.T_crit - Inputs.DSC
                OutCond_REF.h = PropsSI('H','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
                OutCond_REF.s = PropsSI('S','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
            else:
                OutCond_REF.T = PropsSI('T','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture) - Inputs.DSC
                if Inputs.DSC == 0:
                    OutCond_REF.h = PropsSI('H','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture)
                    OutCond_REF.s = PropsSI('S','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture)
                else:
                    OutCond_REF.h = PropsSI('H','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
                    OutCond_REF.s = PropsSI('S','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
            
            if Inputs.cycle != 'scc':
                if InCond_REF.p > InCond_REF.p_crit*0.98:
                    self.cond_p_err = 1
                    break
                else:
                    self.cond_p_err = 0 
    
            if Inputs.layout == 'inj':
                self.inter_p = InEvap_REF.p + self.inter_frac*(OutCond_REF.p - InEvap_REF.p)
                
                self.inter_h_vap = PropsSI('H','P',self.inter_p,'Q',1.0, OutCond_REF.fluidmixture)
                self.inter_h_liq = PropsSI('H','P',self.inter_p,'Q',0.0, OutCond_REF.fluidmixture)
                self.inter_x = (OutCond_REF.h - self.inter_h_liq)/(self.inter_h_vap - self.inter_h_liq)
                
                self.OutComp_low = deepcopy(OutEvap_REF)
                self.OutComp_low.p = self.inter_p
                
                comp_low = CP.Compander_module(OutEvap_REF, self.OutComp_low)
                comp_low.COMP(eff_isen = Inputs.comp_eff, eff_mech = Inputs.mech_eff)
                self.OutComp_low = comp_low.primary_out
                
                self.InComp_high = deepcopy(self.OutComp_low)
                
                self.InComp_high.h = self.OutComp_low.h*(1.0-self.inter_x)+self.inter_h_vap*self.inter_x
                self.InComp_high.T = PropsSI('T','P',self.InComp_high.p,'H',self.InComp_high.h, self.InComp_high.fluidmixture)
                self.InComp_high.s = PropsSI('S','T',self.InComp_high.T, 'P', self.InComp_high.p, self.InComp_high.fluidmixture)
                
                comp_high = CP.Compander_module(self.InComp_high, InCond_REF)
                comp_high.COMP(eff_isen = Inputs.comp_eff, eff_mech = Inputs.mech_eff)
                InCond_REF = comp_high.primary_out
                
                self.OutExpand_high = deepcopy(OutCond_REF)
                self.OutExpand_high.p = self.inter_p
                expand_high = CP.Compander_module(OutCond_REF, self.OutExpand_high)
                expand_high.EXPAND(eff_isen=Inputs.expand_eff, eff_mech = Inputs.mech_eff)
                self.OutExpand_high = expand_high.primary_out
                
                self.Flash_liq = deepcopy(self.OutExpand_high) # 팽창 후 2-phase 중 liq 상만 두번째 팽창기 입구로
                self.Flash_liq.h = self.inter_h_liq
                self.Flash_liq.T = PropsSI('T','P',self.OutExpand_high.p,'Q',0.0, self.OutExpand_high.fluidmixture)
                self.Flash_liq.s = PropsSI('S','P',self.OutExpand_high.p,'Q',0.0, self.OutExpand_high.fluidmixture) 

                expand_low = CP.Compander_module(self.Flash_liq, InEvap_REF)
                expand_low.EXPAND(eff_isen=Inputs.expand_eff, eff_mech = Inputs.mech_eff)
                InEvap_REF = expand_low.primary_out
            else:
                if Inputs.layout == 'ihx':
                    InComp = deepcopy(OutEvap_REF)
                    InComp.p = InComp.p*(1.0-Inputs.ihx_cold_dp)
                    InExpand = deepcopy(OutCond_REF)
                    InExpand.p = InExpand.p*(1.0-Inputs.ihx_hot_dp)
                    IHX = HX.Heatexchanger_module(OutCond_REF, InExpand, 0, OutEvap_REF, InComp, 0)
                    IHX.SIMPHX(eff_HX = Inputs.ihx_eff)
                
                    InExpand = IHX.primary_out
                    InComp = IHX.secondary_out
                else:    
                    InComp = OutEvap_REF
                    InExpand = OutCond_REF
                
                comp = CP.Compander_module(InComp, InCond_REF)
                comp.COMP(eff_isen = Inputs.comp_eff, eff_mech = Inputs.mech_eff)
                InCond_REF = comp.primary_out
                
                
                expand = CP.Compander_module(InExpand, InEvap_REF)
                expand.EXPAND(eff_isen = Inputs.expand_eff, eff_mech = Inputs.mech_eff)
                InEvap_REF = expand.primary_out
                
            if (no_input == 'InCondT') or (no_input == 'OutCondT') or (no_input == 'Condm'):
                InEvap_REF.m = InEvap.q/(InEvap_REF.h - OutEvap_REF.h)
                OutEvap_REF.m = InEvap_REF.m
                if Inputs.layout == 'inj':
                    InCond_REF.m = InEvap_REF.m/(1.0-self.inter_x)
                    OutCond_REF.m = InCond_REF.m
                    self.compPower = comp_low.Pspecific*OutEvap_REF.m + comp_high.Pspecific*InCond_REF.m
                    self.expandPower = expand_high.Pspecific*OutCond_REF.m + expand_low.Pspecific*InEvap_REF.m
                else:
                    InCond_REF.m = InEvap_REF.m
                    OutCond_REF.m = InEvap_REF.m
                    self.compPower = comp.Pspecific*InCond_REF.m
                    self.expandPower = expand.Pspecific*InEvap_REF.m
                    
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
                if Inputs.layout == 'inj':
                    InEvap_REF.m = InCond_REF.m*(1.0 - self.inter_x)
                    OutEvap_REF.m = InCond_REF.m*(1.0 - self.inter_x)
                    self.compPower = comp_low.Pspecific*OutEvap_REF.m + comp_high.Pspecific*InCond_REF.m
                    self.expandPower = expand_high.Pspecific*OutCond_REF.m + expand_low.Pspecific*InEvap_REF.m
                else:
                    InEvap_REF.m = InCond_REF.m
                    OutEvap_REF.m = InCond_REF.m
                    self.compPower = comp.Pspecific*InCond_REF.m
                    self.expandPower = expand.Pspecific*InEvap_REF.m
                
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
        
            if Inputs.cond_type == 'fthe':
                cond.FTHE(N_element=Inputs.cond_N_element, N_row = Inputs.cond_N_row)
                self.cond_err = (Inputs.cond_T_lm - cond.T_lm)/Inputs.cond_T_lm
                
            elif Inputs.cond_type == 'phe':
                cond.PHE(N_element=Inputs.cond_N_element)
                self.cond_err = (Inputs.cond_T_pp - cond.T_pp)/Inputs.cond_T_pp
            
            OutCond_REF = cond.primary_out
            
            if cond.T_rvs == 1:
                cond_p_lb = InCond_REF.p
            else:
                if self.cond_err < 0:
                    cond_p_ub = InCond_REF.p
                else:
                    cond_p_lb = InCond_REF.p
            
            if abs(self.cond_err) < Inputs.tol:
                self.cond_conv_err = 0
                cond_a = 0
            elif cond_p_ub - cond_p_lb < Inputs.tol:
                self.cond_conv_err = 1
                cond_a = 0
        
        return (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF)
    
    def Post_Processing(self):
        print('Heating COP:{:.3f}, Cooling COP:{:.3f}'.format(self.COP_heating, self.COP_cooling))
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
        InCond_REF_t = ProcessFluid(Y=self.inputs_t.Y)
        OutCond_REF_t = ProcessFluid(Y=self.inputs_t.Y)
        InEvap_REF_t = ProcessFluid(Y=self.inputs_t.Y)
        OutEvap_REF_t = ProcessFluid(Y=self.inputs_t.Y)
        InCond_REF_b = ProcessFluid(Y=self.inputs_b.Y)
        OutCond_REF_b = ProcessFluid(Y=self.inputs_b.Y)
        InEvap_REF_b = ProcessFluid(Y=self.inputs_b.Y)
        OutEvap_REF_b = ProcessFluid(Y=self.inputs_b.Y)
        
        self.nbp = 0.0
        
        (self.InCond, self.OutCond, self.InEvap, self.OutEvap, no_input) = super().Input_Processing(self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.inputs_t)
        
        devap = 0.005
        cascade_a = 1
        evap_t_p_lb = 101300.0
        cond_t_ph = 0
        cond_b_ph = 1
        evap_b_ph = 0
        
        
        if no_input == 'InCondT':
            evap_t_p_ub = PropsSI('P','T',self.OutCond.T,'Q',1.0, OutEvap_REF_t.fluidmixture) 
        else:
            evap_t_p_ub = PropsSI('P','T',self.InCond.T,'Q',1.0, OutEvap_REF_t.fluidmixture)
        
        evap_t_p_ub = min(evap_t_p_ub, OutEvap_REF_t.p_crit)
        
        while cascade_a:
            for ii in range(2):
                if ii == 0:
                    OutEvap_REF_t.p = 0.5*(evap_t_p_lb + evap_t_p_ub)*(1+devap)
                else:
                    OutEvap_REF_t.p = 0.5*(evap_t_p_lb + evap_t_p_ub)*(1-devap)
                    
                InEvap_REF_t.p = OutEvap_REF_t.p/(1.0 - self.inputs_t.evap_dp)
                
                OutEvap_REF_t.T = PropsSI('T','P',OutEvap_REF_t.p, 'Q', 1.0, OutEvap_REF_t.fluidmixture) + self.inputs_t.DSH
                if self.inputs_t.DSH == 0:
                    OutEvap_REF_t.h = PropsSI('H','P',OutEvap_REF_t.p, 'Q', 1.0, OutEvap_REF_t.fluidmixture)
                    OutEvap_REF_t.s = PropsSI('S','P',OutEvap_REF_t.p, 'Q', 1.0, OutEvap_REF_t.fluidmixture)
                else:
                    OutEvap_REF_t.h = PropsSI('H','T',OutEvap_REF_t.T, 'P', OutEvap_REF_t.p ,OutEvap_REF_t.fluidmixture)
                    OutEvap_REF_t.s = PropsSI('S','T',OutEvap_REF_t.T, 'P', OutEvap_REF_t.p ,OutEvap_REF_t.fluidmixture)
                    
                if (no_input == 'InEvapT') or (no_input == 'OutEvapT') or (no_input == 'Evapm'):
                    (self.InCond, self.OutCond, InEvap_dummy, OutEvap_dummy, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t) = super().HighPressure_Solver(self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, self.inputs_t, no_input, cond_t_ph)
                    if self.inputs_b.layout == 'inj':    
                        (InEvap_REF_t, OutEvap_REF_t, self.InEvap, self.OutEvap, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b) = super().Injection_Solver(InEvap_REF_t, OutEvap_REF_t, self.InEvap, self.OutEvap, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, self.inputs_b, no_input, cond_b_ph, evap_b_ph)
                    else:
                        (InEvap_REF_t, OutEvap_REF_t, self.InEvap, self.OutEvap, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b) = super().Cycle_Solver(InEvap_REF_t, OutEvap_REF_t, self.InEvap, self.OutEvap, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, self.inputs_b, no_input, cond_b_ph, evap_b_ph)
                        
                elif (no_input == 'InCondT') or (no_input == 'OutCondT') or (no_input == 'Condm'):
                    if self.inputs_t.cycle == 'scc':
                        cond_p_ub = min(2*InCond_REF_t.p_crit, 3.0e7)
                        cond_p_lb = InCond_REF_t.p_crit
                    else:
                        cond_p_ub = InCond_REF_t.p_crit
                        if no_input == 'InCondT':
                            cond_p_lb = PropsSI('P','T',self.OutCond.T,'Q',1.0,OutCond_REF_t.fluidmixture)
                        else:
                            cond_p_lb = PropsSI('P','T',self.InCond.T,'Q',1.0,OutCond_REF_t.fluidmixture)
                    
                    cond_a_t = 1
                    while cond_a_t:
                        (InCond_REF_t, OutCond_REF_t, InEvap_REF_t) = self.HighPressure_for_Evap(cond_p_lb, cond_p_ub, InCond_REF_t, OutCond_REF_t, InEvap_REF_t, OutEvap_REF_t, inputs_t)
                    ## 여기서 부터 잘 짜보자
                    if self.inputs_b.layout == 'inj':    
                        (InEvap_REF_t, OutEvap_REF_t, self.InEvap, self.OutEvap, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b) = super().Injection_Solver(InEvap_REF_t, OutEvap_REF_t, self.InEvap, self.OutEvap, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, self.inputs_b, 'Condm', cond_b_ph, evap_b_ph)
                    else:
                        (InEvap_REF_t, OutEvap_REF_t, self.InEvap, self.OutEvap, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b) = super().Cycle_Solver(InEvap_REF_t, OutEvap_REF_t, self.InEvap, self.OutEvap, InCond_REF_b, OutCond_REF_b, InEvap_REF_b, OutEvap_REF_b, self.inputs_b, 'Condm', cond_b_ph, evap_b_ph)
    
    def HighPressure_for_Evap(self, cond_p_lb, cond_p_ub, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, Inputs):
        
        InCond_REF.p = 0.5*(cond_p_ub+cond_p_lb)
        OutCond_REF.p = InCond_REF.p*(1-Inputs.cond_dp)
        
        if OutCond_REF.p > OutCond_REF.p_crit:
            OutCond_REF.T = 0.10753154*((OutCond_REF.p - OutCond_REF.p_crit)/OutCond_REF.p_crit) + 0.004627621995008088
            OutCond_REF.T = OutCond_REF.T*OutCond_REF.T_crit + OutCond_REF.T_crit - Inputs.DSC
            OutCond_REF.h = PropsSI('H','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
            OutCond_REF.s = PropsSI('S','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
        else:
            OutCond_REF.T = PropsSI('T','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture) - Inputs.DSC
            if Inputs.DSC == 0:
                OutCond_REF.h = PropsSI('H','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture)
                OutCond_REF.s = PropsSI('S','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture)
            else:
                OutCond_REF.h = PropsSI('H','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
                OutCond_REF.s = PropsSI('S','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
        
        if Inputs.layout == 'inj':
            self.inter_p = InEvap_REF.p + self.inter_frac*(OutCond_REF.p - InEvap_REF.p)
            
            self.inter_h_vap = PropsSI('H','P',self.inter_p,'Q',1.0, OutCond_REF.fluidmixture)
            self.inter_h_liq = PropsSI('H','P',self.inter_p,'Q',0.0, OutCond_REF.fluidmixture)
            self.inter_x = (OutCond_REF.h - self.inter_h_liq)/(self.inter_h_vap - self.inter_h_liq)
            
            self.OutComp_low = deepcopy(OutEvap_REF)
            self.OutComp_low.p = self.inter_p
            
            comp_low = CP.Compander_module(OutEvap_REF, self.OutComp_low)
            comp_low.COMP(eff_isen = Inputs.comp_eff, eff_mech = Inputs.mech_eff)
            self.OutComp_low = comp_low.primary_out
            
            self.InComp_high = deepcopy(self.OutComp_low)
            
            self.InComp_high.h = self.OutComp_low.h*(1.0-self.inter_x)+self.inter_h_vap*self.inter_x
            self.InComp_high.T = PropsSI('T','P',self.InComp_high.p,'H',self.InComp_high.h, self.InComp_high.fluidmixture)
            self.InComp_high.s = PropsSI('S','T',self.InComp_high.T, 'P', self.InComp_high.p, self.InComp_high.fluidmixture)
            
            comp_high = CP.Compander_module(self.InComp_high, InCond_REF)
            comp_high.COMP(eff_isen = Inputs.comp_eff, eff_mech = Inputs.mech_eff)
            InCond_REF = comp_high.primary_out
            
            self.OutExpand_high = deepcopy(OutCond_REF)
            self.OutExpand_high.p = self.inter_p
            expand_high = CP.Compander_module(OutCond_REF, self.OutExpand_high)
            expand_high.EXPAND(eff_isen=Inputs.expand_eff, eff_mech = Inputs.mech_eff)
            self.OutExpand_high = expand_high.primary_out
            
            self.Flash_liq = deepcopy(self.OutExpand_high) # 팽창 후 2-phase 중 liq 상만 두번째 팽창기 입구로
            self.Flash_liq.h = self.inter_h_liq
            self.Flash_liq.T = PropsSI('T','P',self.OutExpand_high.p,'Q',0.0, self.OutExpand_high.fluidmixture)
            self.Flash_liq.s = PropsSI('S','P',self.OutExpand_high.p,'Q',0.0, self.OutExpand_high.fluidmixture) 

            expand_low = CP.Compander_module(self.Flash_liq, InEvap_REF)
            expand_low.EXPAND(eff_isen=Inputs.expand_eff, eff_mech = Inputs.mech_eff)
            InEvap_REF = expand_low.primary_out
        else:
            if Inputs.layout == 'ihx':
                InComp = deepcopy(OutEvap_REF)
                InComp.p = InComp.p*(1.0-Inputs.ihx_cold_dp)
                InExpand = deepcopy(OutCond_REF)
                InExpand.p = InExpand.p*(1.0-Inputs.ihx_hot_dp)
                IHX = HX.Heatexchanger_module(OutCond_REF, InExpand, 0, OutEvap_REF, InComp, 0)
                IHX.SIMPHX(eff_HX = Inputs.ihx_eff)
            
                InExpand = IHX.primary_out
                InComp = IHX.secondary_out
            else:    
                InComp = OutEvap_REF
                InExpand = OutCond_REF
            
            comp = CP.Compander_module(InComp, InCond_REF)
            comp.COMP(eff_isen = Inputs.comp_eff, eff_mech = Inputs.mech_eff)
            InCond_REF = comp.primary_out
            
            
            expand = CP.Compander_module(InExpand, InEvap_REF)
            expand.EXPAND(eff_isen = Inputs.expand_eff, eff_mech = Inputs.mech_eff)
            InEvap_REF = expand.primary_out
            
            return (InCond_REF, OutCond_REF, InEvap_REF)
     
                    
                        
                    
                                    
if __name__ == '__main__':
    '''
    evapfluid = 'water'
    inevapT = 323.15
    inevapp = 101300.0
    InEvap = ProcessFluid(Y={evapfluid:1.0,},m = 1.0, T = inevapT, p = inevapp)
    
    outevapp = 101300.0
    OutEvap = ProcessFluid(Y={evapfluid:1.0,},p = outevapp)
    
    condfluid = 'water'
    incondT = 333.15
    incondp = 101300.0
    InCond = ProcessFluid(Y={condfluid:1.0,},m = 1.0, T = incondT, p = incondp)
    
    outcondT = 343.15
    outcondp = 101300.0
    outcondh = PropsSI('H','T',outcondT, 'P', outcondp, condfluid)
    outconds = PropsSI('S','T',outcondT, 'P', outcondp, condfluid)
    OutCond = ProcessFluid(Y={condfluid:1.0,},m = 1.0, T = outcondT, p = outcondp, q = 0.0, h = outcondh, s = outconds)
    
    inputs = Settings()
    inputs.Y = {'R134A':1.0,}
    inputs.second = 'process'
    inputs.cycle = 'vcc'
    inputs.cond_type = 'phe'
    inputs.evap_type = 'phe'
    inputs.layout = 'inj'
    
    vchp_basic = VCHP(InCond, OutCond, InEvap, OutEvap, inputs)'''
    
    evapfluid = 'water'
    inevapT = 323.15
    inevapp = 101300.0
    InEvap = ProcessFluid(Y={evapfluid:1.0,},m = 1.0, T = inevapT, p = inevapp)
    
    outevapT = 313.15
    outevapp = 101300.0
    OutEvap = ProcessFluid(Y={evapfluid:1.0,}, T = outevapT)
    
    condfluid = 'water'
    incondT = 343.15
    incondp = 101300.0
    InCond = ProcessFluid(Y={condfluid:1.0,},m = 1.0, T = incondT, p = incondp)
    
    outcondT = 353.15
    outcondp = 101300.0
    OutCond = ProcessFluid(Y={condfluid:1.0,})
    
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