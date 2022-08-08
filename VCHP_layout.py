from copy import deepcopy
import HX_module as HX
import COMPAND_module as CP
from CoolProp.CoolProp import PropsSI
# test 용 import
from STED_types import WireObjectFluid, Settings


class VCHP():
    def __init__(self, InCond, OutCond, InEvap, OutEvap, inputs):
        self.InCond = InCond
        self.OutCond = OutCond
        self.InEvap = InEvap
        self.OutEvap = OutEvap
        self.inputs = inputs
        self.slope = 0.10753154
        self.intercept = 0.004627621995008088
        
        try:
            self.nbp = PropsSI('T','P',101300,'Q',0.0, self.InCond_REF.fluidmixture)
        except:
            return print('선택하신 냉매는 NBP를 구할 수 없습니다.')
    
    def __call__(self):
        
        (InCond, OutCond, InEvap, OutEvap, no_input) = self.Input_Processing()
        
        InCond_REF = WireObjectFluid(Y=self.inputs.Y)
        OutCond_REF = WireObjectFluid(Y=self.inputs.Y)
        InEvap_REF = WireObjectFluid(Y=self.inputs.Y)
        OutEvap_REF = WireObjectFluid(Y=self.inputs.Y)
        
        if self.inputs.layout == 'inj':
            (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, Output) = self.InterPressure_opt(InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, no_input)
        else:
            (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, Output) = self.Cycle_Solver(InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, no_input)
        
        self.Post_Processing()
            
    def Input_Processing(self):
        no_InCondT = 0
        no_Condm = 0
        no_OutCondT = 0
        no_InEvapT = 0
        no_Evapm = 0
        no_OutEvapT = 0
        
        InEvap = self.InEvap
        OutEvap = self.OutEvap
        
        if self.inputs.second == 'steam':
            (InCond, OutCond) = self.Steam_module(self.OutCond.T, self.inputs.T_steam, self.inputs.m_steam, self.inputs.T_makeup, self.inputs.m_makeup, self.OutCond.Y)
            
        elif self.inputs.second == 'hotwater':
            (InCond, OutCond) = self.Hotwater_module(self.inputs.T_target, self.inputs.M_load, self.inputs.time_target, self.inputs.dT_lift, self.inputs.T_makeup, self.OutCond.Y)
        
        else: # 일반 공정
            InCond = self.InCond
            OutCond = self.OutCond
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
                    InCond.m = OutCond.m
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
                InEvap.m = OutEvap.m # shallow copy
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
                InEvap.q = (OutEvap.h - InEvap.h)*InEvap.m
                OutEvap.q = InEvap.q 
                no_input = 'InCondT'    
            elif no_OutCondT == 1:
                InEvap.q = (OutEvap.h - InEvap.h)*InEvap.m
                OutEvap.q = InEvap.q 
                no_input = 'OutCondT'
            elif no_Condm == 1:   
                InEvap.q = (OutEvap.h - InEvap.h)*InEvap.m
                OutEvap.q = InEvap.q 
                no_input = 'Condm'
            
            elif no_InEvapT == 1:
                InCond.q = (OutCond.h - InCond.h)*InCond.m
                OutCond.q = InCond.q
                no_input = 'InEvapT'
            elif no_OutEvapT == 1:
                InCond.q = (OutCond.h - InCond.h)*InCond.m
                OutCond.q = InCond.q
                no_input = 'OutEvapT'
            elif no_Evapm == 1:   
                InCond.q = (OutCond.h - InCond.h)*InCond.m
                OutCond.q = InCond.q
                no_input = 'Evapm'
            
            if no_input == 'InEvapT':
                if self.inputs.evap_type == 'fthe':
                    if self.nbp > OutEvap.T - self.inputs.cond_T_lm:
                        return print('냉매 NBP가 공정 저온 온도 보다 높습니다.')
                elif self.inputs.evap_type == 'phe':
                    if self.nbp > OutEvap.T - self.inputs.cond_T_pp:
                        return print('냉매 NBP가 공정 저온 온도 보다 높습니다.')
                else: 
                    print('정의되지 않은 열교환기 타입입니다.')
                
            else:
                if self.inputs.evap_type == 'fthe':
                    if self.nbp > InEvap.T - self.inputs.evap_T_lm:
                        return print('냉매 NBP가 공정 저온 온도 보다 높습니다.')
                elif self.inputs.evap_type == 'phe':
                    if self.nbp > InEvap.T - self.inputs.evap_T_pp:
                        return print('냉매 NBP가 공정 저온 온도 보다 높습니다.')
                else: 
                    print('정의되지 않은 열교환기 타입입니다.')
                    
        return (InCond, OutCond, InEvap, OutEvap, no_input)
            
    def Steam_module(self, OutCondT, T_steam, m_steam, T_makeup, m_makeup, Ycond):
        OutCond = WireObjectFluid(Y = Ycond, T=OutCondT)
        InCond = WireObjectFluid(Y = Ycond)
        p_flash = PropsSI('P','T',T_steam,'Q',1.0, OutCond.fluidmixture)
        OutCond.p = PropsSI('P','T',OutCond.T+0.1, 'Q', 0.0, OutCond.fluidmixture)
        OutCond.h = PropsSI('H','T',OutCond.T+0.1, 'Q', 0.0, OutCond.fluidmixture)
        X_flash = PropsSI('Q','H',OutCond.h,'P',p_flash, OutCond.fluidmixture)
        OutCond.m = m_steam / X_flash
        InCond.m = OutCond.m
        m_sat_liq = (1-X_flash)*OutCond.m
        h_sat_liq = PropsSI('H','P',p_flash,'Q',0.0, InCond.fluidmixture)
        h_makeup = PropsSI('H','T',T_makeup,'P',p_flash, InCond.fluidmixture)
        
        InCond.h = (m_sat_liq*h_sat_liq + m_makeup*h_makeup)/OutCond.m
        InCond.T = PropsSI('T','H',InCond.h,'P',p_flash, InCond.fluidmixture)
        
        return (InCond, OutCond)
    
    def Hotwater_module(self, T_target, M_load, time_target, dT_lift, T_makeup, Ycond):
        OutCond = WireObjectFluid(Y = Ycond)
        InCond = WireObjectFluid(Y = Ycond)
        rho_water = PropsSI('D','T',0.5*(T_makeup+T_target),'P',101300, InCond.fluidmixture)
        V_tank = M_load/rho_water
        
        h_target = PropsSI('H','T',T_target,'P',101300.0,InCond.fluidmixture)
        h_makeup = PropsSI('H','T',T_makeup,'P',101300.0,InCond.fluidmixture)
        InCond.h = 0.5*(h_target + h_makeup)
        InCond.T = PropsSI('T','H',InCond.h,'P',101300, InCond.fluidmixture)
        Cp_water = PropsSI('C','T',InCond.T,'P',101300, InCond.fluidmixture)
        OutCond.q = 0.5*M_load*Cp_water*(T_target - InCond.T)/time_target
        OutCond.m = OutCond.q/(Cp_water*dT_lift)
        OutCond.T = InCond.T + dT_lift
        
        return (InCond, OutCond)
    
    def InterPressure_opt(self, InCond, OutCond, InEvap, OutEvap, no_input):
        dfrac = 0.005
        inter_frac_lb = 0.0
        inter_frac_ub = 1.0
        results_array = []
        frac_a = 1
        while frac_a:
            for iii in range(2):
                if iii == 0:
                    inter_frac = 0.5*(inter_frac_lb+inter_frac_ub)*(1-dfrac)
                else:
                    inter_frac = 0.5*(inter_frac_lb+inter_frac_ub)*(1+dfrac)
                
                (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, Output) = self.Cycle_Solver(InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, no_input)
                
                if Output.evap_conv_err == 1:
                    if Output.evap_err > 0:
                        inter_frac_lb = inter_frac
                        break
                else:
                    if iii == 0:
                        COP_o = Output.COP_heating
                        frac_o = inter_frac
                    else:
                        dCOP = ((Output.COP_heating - COP_o)/Output.COP_heating)/((inter_frac - frac_o)/inter_frac)
                        if dCOP > 0:
                            inter_frac_lb = inter_frac
                        else:
                            inter_frac_ub = inter_frac
                            
                        results_array.append([0.5*(Output.COP_heating+COP_o), 0.5*(inter_frac+frac_o), dCOP])
                        
                        if len(results_array) > 2:
                            if abs(results_array[2][-2]) < abs(results_array[2][-1]) and abs(results_array[2][-2]) < abs(results_array[2][-3]):
                                Output.COP_heating = results_array[0][-2]
                                Output.opt_frac = results_array[1][-2]
                                frac_a = 0
                            elif abs(results_array[2][-1]) < self.inputs.tol:
                                Output.COP_heating = results_array[0][-1]
                                Output.opt_frac = results_array[1][-1]
                                frac_a = 0
                        elif inter_frac_ub - inter_frac_lb < self.inputs.tol:
                            Output.COP_heating = results_array[0][-1]
                            Output.opt_frac = results_array[1][-1]
                            frac_a = 0
                              
        return (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, Output)

    def Cycle_Solver(self, InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, no_input):
            if no_input == 'InEvapT':
                evap_p_ub = PropsSI('P','T',OutEvap.T, 'Q', 1.0, InEvap_REF.fluidmixture)        
            else:
                evap_p_ub = PropsSI('P','T',InEvap.T, 'Q', 1.0, InEvap_REF.fluidmixture)
                
            evap_p_lb = 101300.0
            evap_a = 1
            
            while evap_a: 
                OutEvap_REF.p = 0.5*(evap_p_lb+evap_p_ub)
                InEvap_REF.p = OutEvap_REF.p/(1.0-inputs.evap_dp)
                
                OutEvap_REF.T = PropsSI('T','P',OutEvap_REF.p, 'Q', 1.0, OutEvap_REF.fluidmixture) + self.inputs.DSH
                if self.inputs.DSH == 0:
                    self.OutEvap_REF.h = PropsSI('H','P',self.OutEvap_REF.p, 'Q', 1.0, self.OutEvap_REF.fluidmixture)
                    self.OutEvap_REF.s = PropsSI('S','P',self.OutEvap_REF.p, 'Q', 1.0, self.OutEvap_REF.fluidmixture)
                else:
                    self.OutEvap_REF.h = PropsSI('H','T',self.OutEvap_REF.T, 'P', self.OutEvap_REF.p ,self.OutEvap_REF.fluidmixture)
                    self.OutEvap_REF.s = PropsSI('S','T',self.OutEvap_REF.T, 'P', self.OutEvap_REF.p ,self.OutEvap_REF.fluidmixture)
                
                self.HighPressure_Solver()
                
                evap = HX.Heatexchanger_module(self.InEvap_REF, self.OutEvap_REF, self.InEvap, self.OutEvap)
                
                if self.inputs.evap_type == 'fthe':
                    evap.FTHE(N_element = self.inputs.evap_N_element, N_row = self.inputs.evap_N_row)
                    self.evap_err = (self.inputs.evap_T_lm - evap.T_lm)/self.inputs.evap_T_lm
                elif self.inputs.evap_type == 'phe':
                    evap.PHE(N_element= self.inputs.evap_N_element)
                    self.evap_err = (self.inputs.evap_T_pp - evap.T_pp)/self.inputs.evap_T_pp
                
                self.OutEvap_REF = evap.primary_out
                
                if evap.T_rvs == 1:
                    self.evap_p_ub = self.OutEvap_REF.p                    
                else:
                    if self.evap_err < 0:
                        self.evap_p_lb = self.OutEvap_REF.p
                    else:
                        self.evap_p_ub = self.OutEvap_REF.p
                        
                if abs(self.evap_err) < self.inputs.tol:
                    self.evap_conv_err = 0
                    self.COP_heating = abs(self.OutCond.q)/(self.compPower - self.expandPower)
                    self.COP_cooling = abs(self.OutEvap.q)/(self.compPower - self.expandPower)
                    evap_a = 0
                elif self.evap_p_ub - self.evap_p_lb < self.inputs.tol:
                    self.evap_conv_err = 1
                    evap_a = 0
                
    def HighPressure_Solver(self):
        if self.inputs.cycle == 'scc':
            self.cond_p_ub = min(2*self.InCond_REF.p_crit, 3.0e7)
            self.cond_p_lb = self.InCond_REF.p_crit
        else:
            self.cond_p_ub = self.InCond_REF.p_crit
            if self.no_input == 'InCondT':
                self.cond_p_lb = PropsSI('P','T',self.OutCond.T,'Q',1.0,self.OutCond_REF.fluidmixture)
            else:
                self.cond_p_lb = PropsSI('P','T',self.InCond.T,'Q',1.0,self.OutCond_REF.fluidmixture)

        cond_a = 1
        while cond_a:
            self.InCond_REF.p = 0.5*(self.cond_p_ub+self.cond_p_lb)
            self.OutCond_REF.p = self.InCond_REF.p*(1-self.inputs.cond_dp)
            
            if self.OutCond_REF.p > self.OutCond_REF.p_crit:
                self.OutCond_REF.T = self.slope*((self.OutCond_REF.p - self.OutCond_REF.p_crit)/self.OutCond_REF.p_crit) + self.intercept
                self.OutCond_REF.T = self.OutCond_REF.T*self.OutCond_REF.T_crit + self.OutCond_REF.T_crit - self.inputs.DSC
                self.OutCond_REF.h = PropsSI('H','T',self.OutCond_REF.T,'P',self.OutCond_REF.p, self.OutCond_REF.fluidmixture)
                self.OutCond_REF.s = PropsSI('S','T',self.OutCond_REF.T,'P',self.OutCond_REF.p, self.OutCond_REF.fluidmixture)
            else:
                self.OutCond_REF.T = PropsSI('T','P',self.OutCond_REF.p,'Q',0.0,self.OutCond_REF.fluidmixture) - self.inputs.DSC
                if self.inputs.DSC == 0:
                    self.OutCond_REF.h = PropsSI('H','P',self.OutCond_REF.p,'Q',0.0,self.OutCond_REF.fluidmixture)
                    self.OutCond_REF.s = PropsSI('S','P',self.OutCond_REF.p,'Q',0.0,self.OutCond_REF.fluidmixture)
                else:
                    self.OutCond_REF.h = PropsSI('H','T',self.OutCond_REF.T,'P',self.OutCond_REF.p, self.OutCond_REF.fluidmixture)
                    self.OutCond_REF.s = PropsSI('S','T',self.OutCond_REF.T,'P',self.OutCond_REF.p, self.OutCond_REF.fluidmixture)
            
            if self.inputs.cycle != 'scc':
                if self.InCond_REF.p > self.InCond_REF.p_crit*0.98:
                    self.cond_p_err = 1
                    break
                else:
                    self.cond_p_err = 0 
    
            if self.inputs.layout == 'inj':
                self.inter_p = self.InEvap_REF.p + self.inter_frac*(self.OutCond_REF.p - self.InEvap_REF.p)
                
                self.inter_h_vap = PropsSI('H','P',self.inter_p,'Q',1.0, self.OutCond_REF.fluidmixture)
                self.inter_h_liq = PropsSI('H','P',self.inter_p,'Q',0.0, self.OutCond_REF.fluidmixture)
                self.inter_x = (self.OutCond_REF.h - self.inter_h_liq)/(self.inter_h_vap - self.inter_h_liq)
                
                self.OutComp_low = deepcopy(self.OutEvap_REF)
                self.InComp_high = deepcopy(self.OutComp_low)

                self.OutComp_low.p = self.inter_p
                
                comp_low = CP.Compander_module(self.OutEvap_REF, self.OutComp_low)
                comp_low.COMP(eff_isen = self.inputs.comp_eff, eff_mech = self.inputs.mech_eff)
                self.OutComp_low = comp_low.primary_out
                
                self.InComp_high.h = self.OutComp_low.h*(1.0-self.inter_x)+self.inter_h_vap*self.inter_x
                self.InComp_high.T = PropsSI('T','P',self.InComp_high.p,'H',self.InComp_high.h, self.InComp_high.fluidmixture)
                self.InComp_high.s = PropsSI('S','T',self.InComp_high.T, 'P', self.InComp_high.p, self.InComp_high.fluidmixture)
                
                comp_high = CP.Compander_module(self.InComp_high, self.InCond_REF)
                comp_high.COMP(eff_isen = self.inputs.comp_eff, eff_mech = self.inputs.mech_eff)
                self.InCond_REF = comp_high.primary_out
                
                self.OutExpand_high = deepcopy(self.OutCond_REF)
                self.OutExpand_high.p = self.inter_p
                expand_high = CP.Compander_module(self.OutCond_REF, self.OutExpand_high)
                expand_high.EXPAND(eff_isen=self.inputs.expand_eff, eff_mech = self.inputs.mech_eff)
                self.OutExpand_high = expand_high.primary_out
                
                self.Flash_liq = deepcopy(self.OutExpand_high) # 팽창 후 2-phase 중 liq 상만 두번째 팽창기 입구로
                self.Flash_liq.h = self.inter_h_liq
                self.Flash_liq.T = PropsSI('T','P',self.OutExpand_high.p,'Q',0.0, self.OutExpand_high.fluidmixture)
                self.Flash_liq.s = PropsSI('S','P',self.OutExpand_high.p,'Q',0.0, self.OutExpand_high.fluidmixture) 

                expand_low = CP.Compander_module(self.Flash_liq, self.InEvap_REF)
                expand_low.EXPAND(eff_isen=self.inputs.expand_eff, eff_mech = self.inputs.mech_eff)
                self.InEvap_REF = expand_low.primary_out
            else:
                if self.inputs.layout == 'ihx':
                    InComp = deepcopy(self.OutEvap_REF)
                    InComp.p = InComp.p*(1.0-self.inputs.ihx_cold_dp)
                    InExpand = deepcopy(self.OutCond_REF)
                    InExpand.p = InExpand.p*(1.0-self.inputs.ihx_hot_dp)
                    IHX = HX.Heatexchanger_module(self.OutCond_REF, InExpand, self.OutEvap_REF, InComp)
                    IHX.SIMPHX(eff_HX = self.inputs.ihx_eff)
                
                    InExpand = IHX.primary_out
                    InComp = IHX.secondary_out
                else:    
                    InComp = self.OutEvap_REF
                    InExpand = self.OutCond_REF
                
                comp = CP.Compander_module(InComp, self.InCond_REF)
                comp.COMP(eff_isen = self.inputs.comp_eff, eff_mech = self.inputs.mech_eff)
                self.InCond_REF = comp.primary_out
                
                
                expand = CP.Compander_module(InExpand, self.InEvap_REF)
                expand.EXPAND(eff_isen = self.inputs.expand_eff, eff_mech = self.inputs.mech_eff)
                self.InEvap_REF = expand.primary_out
                
            if (self.no_input == 'InCondT') or (self.no_input == 'OutCondT') or (self.no_input == 'Condm'):
                self.InEvap_REF.m = self.InEvap.q/(self.InEvap_REF.h - self.OutEvap_REF.h)
                self.OutEvap_REF.m = self.InEvap_REF.m
                if self.inputs.layout == 'inj':
                    self.InCond_REF.m = self.InEvap_REF.m/(1.0-self.inter_x)
                    self.OutCond_REF.m = self.InCond_REF.m
                    self.compPower = comp_low.Pspecific*self.OutEvap_REF.m + comp_high.Pspecific*self.InCond_REF.m
                    self.expandPower = expand_high.Pspecific*self.OutCond_REF.m + expand_low.Pspecific*self.InEvap_REF.m
                else:
                    self.InCond_REF.m = self.InEvap_REF.m
                    self.OutCond_REF.m = self.InEvap_REF.m
                    self.compPower = comp.Pspecific*self.InCond_REF.m
                    self.expandPower = expand.Pspecific*self.InEvap_REF.m
                    
                self.InEvap_REF.q = -self.InEvap.q
                self.OutEvap_REF.q = -self.OutEvap.q
                
                self.InCond_REF.q = (self.OutCond_REF.h - self.InCond_REF.h)*self.InCond_REF.m
                self.OutCond_REF.q = self.InCond_REF.q
                self.InCond.q = -self.InCond_REF.q
                self.OutCond.q = -self.InCond_REF.q
                if self.no_input == 'InCondT':
                    self.InCond.h = self.OutCond.h - self.OutCond.q/self.OutCond.m
                    self.InCond.T = PropsSI('T','P',self.InCond.p, 'H', self.InCond.h, self.InCond.fluidmixture)
                elif self.no_input == 'OutCondT':
                    self.OutCond.h = self.InCond.h + self.InCond.q/self.InCond.m
                    self.OutCond.T = PropsSI('T','P',self.OutCond.p, 'H', self.OutCond.h, self.OutCond.fluidmixture)
                elif self.no_input == 'Condm':
                    self.InCond.m = self.InCond.q/(self.OutCond.h - self.InCond.h)
                    self.OutCond.m = self.InCond.m
                
            elif (self.no_input == 'InEvapT') or (self.no_input == 'OutEvapT') or (self.no_input == 'Evapm'):
                self.InCond_REF.m = self.InCond.q/(self.InCond_REF.h - self.OutCond_REF.h)
                self.OutCond_REF.m = self.InCond_REF.m
                if self.inputs.layout == 'inj':
                    self.InEvap_REF.m = self.InCond_REF.m*(1.0 - self.inter_x)
                    self.OutEvap_REF.m = self.InCond_REF.m*(1.0 - self.inter_x)
                    self.compPower = comp_low.Pspecific*self.OutEvap_REF.m + comp_high.Pspecific*self.InCond_REF.m
                    self.expandPower = expand_high.Pspecific*self.OutCond_REF.m + expand_low.Pspecific*self.InEvap_REF.m
                else:
                    self.InEvap_REF.m = self.InCond_REF.m
                    self.OutEvap_REF.m = self.InCond_REF.m
                    self.compPower = comp.Pspecific*self.InCond_REF.m
                    self.expandPower = expand.Pspecific*self.InEvap_REF.m
                
                self.InCond_REF.q = -self.InCond.q
                self.OutCond_REF.q = -self.InCond.q
                
                self.InEvap_REF.q = (self.OutEvap_REF.h - self.InEvap_REF.h)*self.InEvap_REF.m
                self.OutEvap_REF.q = self.InEvap_REF.q
                self.InEvap.q = -self.InEvap_REF.q
                self.OutEvap.q = -self.InEvap_REF.q
                
                if self.no_input == 'InEvapT':
                    self.InEvap.h = self.OutEvap.h - self.OutEvap.q/self.OutEvap.m
                    self.InEvap.T = PropsSI('T','P',self.InEvap.p, 'H', self.InEvap.h, self.InEvap.fluidmixture)
                elif self.no_input == 'OutEvapT':
                    self.OutEvap.h = self.InEvap.h + self.InEvap.q/self.InEvap.m
                    self.OutEvap.T = PropsSI('T','P',self.OutEvap.p, 'H', self.OutEvap.h, self.OutEvap.fluidmixture)
                elif self.no_input == 'Evapm':
                    self.InEvap.m = self.InEvap.q/(self.OutEvap.h - self.InEvap.h)
                    self.OutEvap.m = self.InEvap.m
                
            cond = HX.Heatexchanger_module(self.InCond_REF, self.OutCond_REF, self.InCond, self.OutCond)
        
            if self.inputs.cond_type == 'fthe':
                cond.FTHE(N_element=self.inputs.cond_N_element, N_row = self.inputs.cond_N_row)
                self.cond_err = (self.inputs.cond_T_lm - cond.T_lm)/self.inputs.cond_T_lm
                
            elif self.inputs.cond_type == 'phe':
                cond.PHE(N_element=self.inputs.cond_N_element)
                self.cond_err = (self.inputs.cond_T_pp - cond.T_pp)/self.inputs.cond_T_pp
            
            self.OutCond_REF = cond.primary_out
            
            if cond.T_rvs == 1:
                self.cond_p_lb = self.InCond_REF.p
            else:
                if self.cond_err < 0:
                    self.cond_p_ub = self.InCond_REF.p
                else:
                    self.cond_p_lb = self.InCond_REF.p
            
            if abs(self.cond_err) < self.inputs.tol:
                self.cond_conv_err = 0
                cond_a = 0
            elif self.cond_p_ub - self.cond_p_lb < self.inputs.tol:
                self.cond_conv_err = 1
                cond_a = 0
    
    def Post_Processing(self):
        print('Heating COP:{:.3f}, Cooling COP:{:.3f}'.format(self.COP_heating, self.COP_cooling))
        print('Refrigerant:{}'.format(self.OutCond_REF.fluidmixture))
        print('Q heating: {:.2f} [kW] ({:.2f} [usRT])'.format(self.OutCond.q/1000, self.OutCond.q/3516.8525))
        print('Q cooling: {:.2f} [kW] ({:.2f} [usRT])'.format(self.OutEvap_REF.q/1000, self.OutEvap_REF.q/3516.8525))
        print('Hot fluid Inlet T:{:.2f}[℃]/P:{:.2f}[bar]/m:{:.2f}[kg/s]:   -------> Hot fluid Outlet T:{:.2f}[℃]/P:{:.2f}[bar]/m:{:.2f}[kg/s]'.format(self.InCond.T, self.InCond.p/1.0e5, self.InCond.m, self.OutCond.T, self.OutCond.p, self.OutCond.m))
        print('Cold fluid Outlet T:{:.2f}[℃]/P:{:.2f}[bar]/m:{:.2f}[kg/s]: <------- Cold fluid Inlet T:{:.2f}[℃]/P:{:.2f}[bar]/m:{:.2f}[kg/s]'.format(self.OutEvap.T, self.OutEvap.p/1.0e5, self.OutEvap.m, self.InEvap.T, self.InEvap.p, self.InEvap.m))
        print('Plow: {:.2f} [bar], Phigh: {:.2f} [bar], mdot: {:.2f}[kg/s]'.format(self.OutEvap_REF.p/1.0e5, self.InCond_REF.p/1.0e5, self.OutEvap_REF.m))

class VCHP_cascade(VCHP):
    def __init__(self, InCond, OutCond, InEvap, OutEvap, inputs, top_layout: str, bot_layout: str):        
        super().__init__(InCond, OutCond, InEvap, OutEvap, inputs)
        self.top_layout = top_layout
        self.bot_layout = bot_layout
    def Connection_Solver(self):
        if top_layout == 'bas':
            super().Cycle_Solver()
    
if __name__ == '__main__':
    
    evapfluid = 'AIR'
    inevapT = 313.15
    inevapp = 101300.0
    inevaph = PropsSI('H','T',inevapT, 'P', inevapp, evapfluid)
    inevaps = PropsSI('S','T',inevapT, 'P', inevapp, evapfluid)
    InEvap = WireObjectFluid(Y={evapfluid:1.0,},m = 1.0, T = inevapT, p = inevapp, q = 0.0, h = inevaph, s = inevaps)
    
    '''
    outevapp = 101300.0
    OutEvap = WireObjectFluid(Y={evapfluid:1.0,},p = outevapp)'''
    
    
    outevapT = 307.8
    outevapp = 101300.0
    outevaph = PropsSI('H','T',outevapT, 'P', outevapp, evapfluid)
    outevaps = PropsSI('S','T',outevapT, 'P', outevapp, evapfluid)
    OutEvap = WireObjectFluid(Y={evapfluid:1.0,},m = 1.0, T = outevapT, p = outevapp, q = 0.0, h = outevaph, s = outevaps)
    
    
    condfluid = 'AIR'
    incondT = 323.15
    incondp = 101300.0
    incondh = PropsSI('H','T',incondT, 'P', incondp, condfluid)
    inconds = PropsSI('S','T',incondT, 'P', incondp, condfluid)
    InCond = WireObjectFluid(Y={condfluid:1.0,},m = 1.0, T = incondT, p = incondp, q = 0.0, h = incondh, s = inconds)
    
    '''
    outcondT = 330.0
    outcondp = 101300.0
    outcondh = PropsSI('H','T',outcondT, 'P', outcondp, condfluid)
    outconds = PropsSI('S','T',outcondT, 'P', outcondp, condfluid)
    OutCond = WireObjectFluid(Y={condfluid:1.0,},m = 1.0, T = outcondT, p = outcondp, q = 0.0, h = outcondh, s = outconds)'''
    
    
    outcondp = 101300.0
    OutCond = WireObjectFluid(Y={condfluid:1.0,},p = outcondp, q = 0.0)
    
    inputs = Settings()
    inputs.Y = {'R134A':1.0,}
    inputs.second = 'process'
    inputs.cycle = 'vcc'
    inputs.cond_type = 'fthe'
    inputs.evap_type = 'fthe'
    inputs.layout = 'bas'

    #vchp_basic = VCHP(InCond, OutCond, InEvap, OutEvap, inputs)
    #vchp_basic()
    
    vchp_inject = VCHP(InCond, OutCond, InEvap, OutEvap, inputs)
    vchp_inject()