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
        
        self.Input_Processing()
        evap_ph = 0
        cond_ph = 0
        if self.inputs.layout == 'inj':    
            (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF) = self.InterPressure_opt(self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, evap_ph, cond_ph)
        else:
            (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF) = self.Cycle_Solver(self.InCond, self.OutCond, self.InEvap, self.OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, evap_ph, cond_ph)
        
        self.Post_Processing()
            
    def Input_Processing(self):
        no_InCondT = 0
        no_Condm = 0
        no_OutCondT = 0
        no_InEvapT = 0
        no_Evapm = 0
        no_OutEvapT = 0
        
        
        if self.inputs.second == 'steam':
            self.Steam_module()
            
        elif self.inputs.second == 'hotwater':
            self.Hotwater_module()
        
        else: # 일반 공정
            if self.InCond.p <= 0.0:
                self.InCond.p = 101300.0
        
            if self.OutCond.p <= 0.0:
             self.OutCond.p = 101300.0
             
            if self.InCond.T <= 0.0:
                no_InCondT = 1
        
            if self.InCond.m <= 0 and self.OutCond.m <= 0 :
                no_Condm = 1
            else:
                if self.InCond.m == 0:
                    self.InCond.m = self.OutCond.m # shallow copy
                else:
                    self.OutCond.m = self.InCond.m 
                
            if self.OutCond.T <= 0.0:
                no_OutCondT = 1
            
            
        if self.InEvap.p <= 0.0:
            self.InEvap.p = 101300.0
        
        if self.OutEvap.p <= 0.0:
            self.OutEvap.p = 101300.0
        
        
        if self.InEvap.T <= 0.0:
            no_InEvapT = 1
        
        if self.InEvap.m <= 0 and self.OutEvap.m <= 0 :
            no_Evapm = 1
        else:
            if self.InEvap.m == 0:
                self.InEvap.m = self.OutEvap.m
            else:
                self.OutEvap.m = self.InEvap.m
                
        if self.OutEvap.T <= 0.0:
            no_OutEvapT = 1
            
        no_inputs_sum = no_InCondT + no_Condm + no_OutCondT + no_InEvapT + no_Evapm + no_OutEvapT
        
        if no_inputs_sum == 0:
            return print('입력 변수가 Overdefine 됐습니다.')
        elif no_inputs_sum > 1:
            return print('입력 변수가 Underdefine 됐습니다.')
        else:    
            if no_InCondT == 1:
                self.OutCond.h = PropsSI('H','T',self.OutCond.T, 'P',self.OutCond.p, self.OutCond.fluidmixture)
                self.OutCond.Cp = PropsSI('C','T',self.OutCond.T, 'P',self.OutCond.p, self.OutCond.fluidmixture)
                self.InEvap.h = PropsSI('H','T',self.InEvap.T, 'P',self.InEvap.p, self.InEvap.fluidmixture)
                self.InEvap.Cp = PropsSI('C','T',self.InEvap.T, 'P',self.InEvap.p, self.InEvap.fluidmixture)
                self.OutEvap.h = PropsSI('H','T',self.OutEvap.T, 'P',self.OutEvap.p, self.OutEvap.fluidmixture)
                self.OutEvap.Cp = PropsSI('C','T',self.OutEvap.T, 'P',self.OutEvap.p, self.OutEvap.fluidmixture)
                self.InEvap.q = (self.OutEvap.h - self.InEvap.h)*self.InEvap.m
                self.OutEvap.q = self.InEvap.q 
                self.no_input = 'InCondT'
            elif no_OutCondT == 1:
                self.InCond.h = PropsSI('H','T',self.InCond.T, 'P',self.InCond.p, self.InCond.fluidmixture)
                self.InCond.Cp = PropsSI('C','T',self.InCond.T, 'P',self.InCond.p, self.InCond.fluidmixture)
                self.InEvap.h = PropsSI('H','T',self.InEvap.T, 'P',self.InEvap.p, self.InEvap.fluidmixture)
                self.InEvap.Cp = PropsSI('C','T',self.InEvap.T, 'P',self.InEvap.p, self.InEvap.fluidmixture)
                self.OutEvap.h = PropsSI('H','T',self.OutEvap.T, 'P',self.OutEvap.p, self.OutEvap.fluidmixture)
                self.OutEvap.Cp = PropsSI('C','T',self.OutEvap.T, 'P',self.OutEvap.p, self.OutEvap.fluidmixture)
                self.InEvap.q = (self.OutEvap.h - self.InEvap.h)*self.InEvap.m
                self.OutEvap.q = self.InEvap.q 
                self.no_input = 'OutCondT'
            elif no_Condm == 1:
                self.InCond.h = PropsSI('H','T',self.InCond.T, 'P',self.InCond.p, self.InCond.fluidmixture)
                self.InCond.Cp = PropsSI('C','T',self.InCond.T, 'P',self.InCond.p, self.InCond.fluidmixture)
                self.OutCond.h = PropsSI('H','T',self.OutCond.T, 'P',self.OutCond.p, self.OutCond.fluidmixture)
                self.OutCond.Cp = PropsSI('C','T',self.OutCond.T, 'P',self.OutCond.p, self.OutCond.fluidmixture)
                self.InEvap.h = PropsSI('H','T',self.InEvap.T, 'P',self.InEvap.p, self.InEvap.fluidmixture)
                self.InEvap.Cp = PropsSI('C','T',self.InEvap.T, 'P',self.InEvap.p, self.InEvap.fluidmixture)
                self.OutEvap.h = PropsSI('H','T',self.OutEvap.T, 'P',self.OutEvap.p, self.OutEvap.fluidmixture)
                self.OutEvap.Cp = PropsSI('C','T',self.OutEvap.T, 'P',self.OutEvap.p, self.OutEvap.fluidmixture)
                self.InEvap.q = (self.OutEvap.h - self.InEvap.h)*self.InEvap.m
                self.OutEvap.q = self.InEvap.q 
                self.no_input = 'Condm'
            
            elif no_InEvapT == 1:
                self.InCond.h = PropsSI('H','T',self.InCond.T, 'P',self.InCond.p, self.InCond.fluidmixture)
                self.InCond.Cp = PropsSI('C','T',self.InCond.T, 'P',self.InCond.p, self.InCond.fluidmixture)
                self.OutCond.h = PropsSI('H','T',self.OutCond.T, 'P',self.OutCond.p, self.OutCond.fluidmixture)
                self.OutCond.Cp = PropsSI('C','T',self.OutCond.T, 'P',self.OutCond.p, self.OutCond.fluidmixture)
                self.OutEvap.h = PropsSI('H','T',self.OutEvap.T, 'P',self.OutEvap.p, self.OutEvap.fluidmixture)
                self.OutEvap.Cp = PropsSI('C','T',self.OutEvap.T, 'P',self.OutEvap.p, self.OutEvap.fluidmixture)
                self.InCond.q = (self.OutCond.h - self.InCond.h)*self.InCond.m
                self.OutCond.q = self.InCond.q
                self.no_input = 'InEvapT'
            elif no_OutEvapT == 1:
                self.InCond.h = PropsSI('H','T',self.InCond.T, 'P',self.InCond.p, self.InCond.fluidmixture)
                self.InCond.Cp = PropsSI('C','T',self.InCond.T, 'P',self.InCond.p, self.InCond.fluidmixture)
                self.OutCond.h = PropsSI('H','T',self.OutCond.T, 'P',self.OutCond.p, self.OutCond.fluidmixture)
                self.OutCond.Cp = PropsSI('C','T',self.OutCond.T, 'P',self.OutCond.p, self.OutCond.fluidmixture)
                self.InEvap.h = PropsSI('H','T',self.InEvap.T, 'P',self.InEvap.p, self.InEvap.fluidmixture)
                self.InEvap.Cp = PropsSI('C','T',self.InEvap.T, 'P',self.InEvap.p, self.InEvap.fluidmixture)
                self.InCond.q = (self.OutCond.h - self.InCond.h)*self.InCond.m
                self.OutCond.q = self.InCond.q
                self.no_input = 'OutEvapT'
            elif no_Evapm == 1:
                self.InCond.h = PropsSI('H','T',self.InCond.T, 'P',self.InCond.p, self.InCond.fluidmixture)
                self.InCond.Cp = PropsSI('C','T',self.InCond.T, 'P',self.InCond.p, self.InCond.fluidmixture)
                self.OutCond.h = PropsSI('H','T',self.OutCond.T, 'P',self.OutCond.p, self.OutCond.fluidmixture)
                self.OutCond.Cp = PropsSI('C','T',self.OutCond.T, 'P',self.OutCond.p, self.OutCond.fluidmixture)
                self.InEvap.h = PropsSI('H','T',self.InEvap.T, 'P',self.InEvap.p, self.InEvap.fluidmixture)
                self.InEvap.Cp = PropsSI('C','T',self.InEvap.T, 'P',self.InEvap.p, self.InEvap.fluidmixture)
                self.OutEvap.h = PropsSI('H','T',self.OutEvap.T, 'P',self.OutEvap.p, self.OutEvap.fluidmixture)
                self.OutEvap.Cp = PropsSI('C','T',self.OutEvap.T, 'P',self.OutEvap.p, self.OutEvap.fluidmixture)
                self.InCond.q = (self.OutCond.h - self.InCond.h)*self.InCond.m
                self.OutCond.q = self.InCond.q
                self.no_input = 'Evapm'
            
            if self.no_input == 'InEvapT':
                if self.inputs.evap_type == 'fthe':
                    if self.nbp > self.OutEvap.T - self.inputs.cond_T_lm:
                        return print('냉매 NBP가 공정 저온 온도 보다 높습니다.')
                elif self.inputs.evap_type == 'phe':
                    if self.nbp > self.OutEvap.T - self.inputs.cond_T_pp:
                        return print('냉매 NBP가 공정 저온 온도 보다 높습니다.')
                else: 
                    print('정의되지 않은 열교환기 타입입니다.')
                
            else:
                if self.inputs.evap_type == 'fthe':
                    if self.nbp > self.InEvap.T - self.inputs.evap_T_lm:
                        return print('냉매 NBP가 공정 저온 온도 보다 높습니다.')
                elif self.inputs.evap_type == 'phe':
                    if self.nbp > self.InEvap.T - self.inputs.evap_T_pp:
                        return print('냉매 NBP가 공정 저온 온도 보다 높습니다.')
                else: 
                    print('정의되지 않은 열교환기 타입입니다.')
                
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
    
    def InterPressure_opt(self, InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, evap_ph, cond_ph):
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
                
                (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF) = self.Cycle_Solver(InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, evap_ph, cond_ph)
                
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
                            elif abs(results_array[-1][2]) < self.inputs.tol:
                                self.COP_heating = results_array[-1][0]
                                self.inter_frac = results_array[-1][1]
                                frac_a = 0
<<<<<<< HEAD
                        
                        if inter_frac_ub - inter_frac_lb < self.inputs.tol:
                            self.COP_heating = results_array[-1][0]
                            self.inter_frac = results_array[-1][1]
                            frac_a = 0
        
        return (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF)                
            
    def Cycle_Solver(self,InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, evap_ph, cond_ph):
        if self.no_input == 'InEvapT':
            evap_p_ub = PropsSI('P','T',OutEvap.T, 'Q', 1.0, InEvap_REF.fluidmixture)        
=======
                        elif inter_frac_ub - inter_frac_lb < self.inputs.tol:
                            frac_a = 0

    def Cycle_Solver(self):
            if self.no_input == 'InEvapT':
                evap_p_ub = PropsSI('P','T',self.OutEvap.T, 'Q', 1.0, self.InEvap_REF.fluidmixture)        
            else:
                evap_p_ub = PropsSI('P','T',self.InEvap.T, 'Q', 1.0, self.InEvap_REF.fluidmixture)
                
            evap_p_lb = 101300.0
            evap_a = 1
            
            while evap_a: 
                self.OutEvap_REF.p = 0.5*(evap_p_lb+evap_p_ub)
                self.InEvap_REF.p = self.OutEvap_REF.p/(1.0-self.inputs.evap_dp)
                
                self.OutEvap_REF.T = PropsSI('T','P',self.OutEvap_REF.p, 'Q', 1.0, self.OutEvap_REF.fluidmixture) + self.inputs.DSH
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
                    evap_p_ub = self.OutEvap_REF.p                    
                else:
                    if self.evap_err < 0:
                        evap_p_lb = self.OutEvap_REF.p
                    else:
                        evap_p_ub = self.OutEvap_REF.p
                        
                if abs(self.evap_err) < self.inputs.tol:
                    self.evap_conv_err = 0
                    self.COP_heating = abs(self.OutCond.q)/(self.compPower - self.expandPower)
                    self.COP_cooling = abs(self.OutEvap.q)/(self.compPower - self.expandPower)
                    evap_a = 0
                elif evap_p_ub - evap_p_lb < self.inputs.tol:
                    self.evap_conv_err = 1
                    evap_a = 0
                
    def HighPressure_Solver(self):
        if self.inputs.cycle == 'scc':
            self.cond_p_ub = min(2*self.InCond_REF.p_crit, 3.0e7)
            self.cond_p_lb = self.InCond_REF.p_crit
>>>>>>> main
        else:
            evap_p_ub = PropsSI('P','T',InEvap.T, 'Q', 1.0, InEvap_REF.fluidmixture)
            
        evap_p_lb = 101300.0
        evap_a = 1
        
        while evap_a: 
            OutEvap_REF.p = 0.5*(evap_p_lb+evap_p_ub)
            InEvap_REF.p = OutEvap_REF.p/(1.0-self.inputs.evap_dp)
            
            OutEvap_REF.T = PropsSI('T','P',OutEvap_REF.p, 'Q', 1.0, OutEvap_REF.fluidmixture) + self.inputs.DSH
            if self.inputs.DSH == 0:
                OutEvap_REF.h = PropsSI('H','P',OutEvap_REF.p, 'Q', 1.0, OutEvap_REF.fluidmixture)
                OutEvap_REF.s = PropsSI('S','P',OutEvap_REF.p, 'Q', 1.0, OutEvap_REF.fluidmixture)
            else:
                OutEvap_REF.h = PropsSI('H','T',OutEvap_REF.T, 'P', OutEvap_REF.p ,OutEvap_REF.fluidmixture)
                OutEvap_REF.s = PropsSI('S','T',OutEvap_REF.T, 'P', OutEvap_REF.p ,OutEvap_REF.fluidmixture)
            
            self.HighPressure_Solver(InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, cond_ph)
            
            evap = HX.Heatexchanger_module(InEvap_REF, OutEvap_REF, 1, InEvap, OutEvap, evap_ph)
            
            if self.inputs.evap_type == 'fthe':
                evap.FTHE(N_element = self.inputs.evap_N_element, N_row = self.inputs.evap_N_row)
                self.evap_err = (self.inputs.evap_T_lm - evap.T_lm)/self.inputs.evap_T_lm
            elif self.inputs.evap_type == 'phe':
                evap.PHE(N_element= self.inputs.evap_N_element)
                self.evap_err = (self.inputs.evap_T_pp - evap.T_pp)/self.inputs.evap_T_pp
            
            OutEvap_REF = evap.primary_out
            
            if evap.T_rvs == 1:
                evap_p_ub = OutEvap_REF.p                    
            else:
                if self.evap_err < 0:
                    evap_p_lb = OutEvap_REF.p
                else:
                    evap_p_ub = OutEvap_REF.p
                    
            if abs(self.evap_err) < self.inputs.tol:
                self.evap_conv_err = 0
                self.COP_heating = abs(OutCond.q)/(self.compPower - self.expandPower)
                self.COP_cooling = abs(OutEvap.q)/(self.compPower - self.expandPower)
                evap_a = 0
            elif evap_p_ub - evap_p_lb < self.inputs.tol:
                self.evap_conv_err = 1
                evap_a = 0
        
        return (InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF)
        
    def HighPressure_Solver(self, InCond, OutCond, InEvap, OutEvap, InCond_REF, OutCond_REF, InEvap_REF, OutEvap_REF, cond_ph):
        if self.inputs.cycle == 'scc':
            cond_p_ub = min(2*InCond_REF.p_crit, 3.0e7)
            cond_p_lb = InCond_REF.p_crit
        else:
            cond_p_ub = InCond_REF.p_crit
            if self.no_input == 'InCondT':
                cond_p_lb = PropsSI('P','T',OutCond.T,'Q',1.0,OutCond_REF.fluidmixture)
            else:
                cond_p_lb = PropsSI('P','T',InCond.T,'Q',1.0,OutCond_REF.fluidmixture)

        cond_a = 1
        while cond_a:
            InCond_REF.p = 0.5*(cond_p_ub+cond_p_lb)
            OutCond_REF.p = InCond_REF.p*(1-self.inputs.cond_dp)
            
            if OutCond_REF.p > OutCond_REF.p_crit:
                OutCond_REF.T = 0.10753154*((OutCond_REF.p - OutCond_REF.p_crit)/OutCond_REF.p_crit) + 0.004627621995008088
                OutCond_REF.T = OutCond_REF.T*OutCond_REF.T_crit + OutCond_REF.T_crit - self.inputs.DSC
                OutCond_REF.h = PropsSI('H','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
                OutCond_REF.s = PropsSI('S','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
            else:
                OutCond_REF.T = PropsSI('T','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture) - self.inputs.DSC
                if self.inputs.DSC == 0:
                    OutCond_REF.h = PropsSI('H','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture)
                    OutCond_REF.s = PropsSI('S','P',OutCond_REF.p,'Q',0.0,OutCond_REF.fluidmixture)
                else:
                    OutCond_REF.h = PropsSI('H','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
                    OutCond_REF.s = PropsSI('S','T',OutCond_REF.T,'P',OutCond_REF.p, OutCond_REF.fluidmixture)
            
            if self.inputs.cycle != 'scc':
                if InCond_REF.p > InCond_REF.p_crit*0.98:
                    self.cond_p_err = 1
                    break
                else:
                    self.cond_p_err = 0 
    
            if self.inputs.layout == 'inj':
                self.inter_p = InEvap_REF.p + self.inter_frac*(OutCond_REF.p - InEvap_REF.p)
                
                self.inter_h_vap = PropsSI('H','P',self.inter_p,'Q',1.0, OutCond_REF.fluidmixture)
                self.inter_h_liq = PropsSI('H','P',self.inter_p,'Q',0.0, OutCond_REF.fluidmixture)
                self.inter_x = (OutCond_REF.h - self.inter_h_liq)/(self.inter_h_vap - self.inter_h_liq)
                
                self.OutComp_low = deepcopy(OutEvap_REF)
                self.OutComp_low.p = self.inter_p
                
                comp_low = CP.Compander_module(OutEvap_REF, self.OutComp_low)
                comp_low.COMP(eff_isen = self.inputs.comp_eff, eff_mech = self.inputs.mech_eff)
                self.OutComp_low = comp_low.primary_out
                
                self.InComp_high = deepcopy(self.OutComp_low)
                
                self.InComp_high.h = self.OutComp_low.h*(1.0-self.inter_x)+self.inter_h_vap*self.inter_x
                self.InComp_high.T = PropsSI('T','P',self.InComp_high.p,'H',self.InComp_high.h, self.InComp_high.fluidmixture)
                self.InComp_high.s = PropsSI('S','T',self.InComp_high.T, 'P', self.InComp_high.p, self.InComp_high.fluidmixture)
                
                comp_high = CP.Compander_module(self.InComp_high, InCond_REF)
                comp_high.COMP(eff_isen = self.inputs.comp_eff, eff_mech = self.inputs.mech_eff)
                InCond_REF = comp_high.primary_out
                
                self.OutExpand_high = deepcopy(OutCond_REF)
                self.OutExpand_high.p = self.inter_p
                expand_high = CP.Compander_module(OutCond_REF, self.OutExpand_high)
                expand_high.EXPAND(eff_isen=self.inputs.expand_eff, eff_mech = self.inputs.mech_eff)
                self.OutExpand_high = expand_high.primary_out
                
                self.Flash_liq = deepcopy(self.OutExpand_high) # 팽창 후 2-phase 중 liq 상만 두번째 팽창기 입구로
                self.Flash_liq.h = self.inter_h_liq
                self.Flash_liq.T = PropsSI('T','P',self.OutExpand_high.p,'Q',0.0, self.OutExpand_high.fluidmixture)
                self.Flash_liq.s = PropsSI('S','P',self.OutExpand_high.p,'Q',0.0, self.OutExpand_high.fluidmixture) 

                expand_low = CP.Compander_module(self.Flash_liq, InEvap_REF)
                expand_low.EXPAND(eff_isen=self.inputs.expand_eff, eff_mech = self.inputs.mech_eff)
                InEvap_REF = expand_low.primary_out
            else:
                if self.inputs.layout == 'ihx':
                    InComp = deepcopy(OutEvap_REF)
                    InComp.p = InComp.p*(1.0-self.inputs.ihx_cold_dp)
                    InExpand = deepcopy(OutCond_REF)
                    InExpand.p = InExpand.p*(1.0-self.inputs.ihx_hot_dp)
                    IHX = HX.Heatexchanger_module(OutCond_REF, InExpand, 0, OutEvap_REF, InComp, 0)
                    IHX.SIMPHX(eff_HX = self.inputs.ihx_eff)
                
                    InExpand = IHX.primary_out
                    InComp = IHX.secondary_out
                else:    
                    InComp = OutEvap_REF
                    InExpand = OutCond_REF
                
                comp = CP.Compander_module(InComp, InCond_REF)
                comp.COMP(eff_isen = self.inputs.comp_eff, eff_mech = self.inputs.mech_eff)
                InCond_REF = comp.primary_out
                
                
                expand = CP.Compander_module(InExpand, InEvap_REF)
                expand.EXPAND(eff_isen = self.inputs.expand_eff, eff_mech = self.inputs.mech_eff)
                InEvap_REF = expand.primary_out
                
            if (self.no_input == 'InCondT') or (self.no_input == 'OutCondT') or (self.no_input == 'Condm'):
                InEvap_REF.m = InEvap.q/(InEvap_REF.h - OutEvap_REF.h)
                OutEvap_REF.m = InEvap_REF.m
                if self.inputs.layout == 'inj':
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
                if self.no_input == 'InCondT':
                    InCond.h = OutCond.h - OutCond.q/OutCond.m
                    InCond.T = PropsSI('T','P',InCond.p, 'H', InCond.h, InCond.fluidmixture)
                    InCond.Cp = PropsSI('C','T',InCond.T, 'P', InCond.p, InCond.fluidmixture)
                elif self.no_input == 'OutCondT':
                    OutCond.h = InCond.h + InCond.q/InCond.m
                    OutCond.T = PropsSI('T','P',OutCond.p, 'H', OutCond.h, OutCond.fluidmixture)
                    OutCond.Cp = PropsSI('C','T',OutCond.T, 'P', OutCond.p, OutCond.fluidmixture)
                elif self.no_input == 'Condm':
                    InCond.m = InCond.q/(OutCond.h - InCond.h)
                    OutCond.m = InCond.m
                
            elif (self.no_input == 'InEvapT') or (self.no_input == 'OutEvapT') or (self.no_input == 'Evapm'):
                InCond_REF.m = InCond.q/(InCond_REF.h - OutCond_REF.h)
                OutCond_REF.m = InCond_REF.m
                if self.inputs.layout == 'inj':
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
                
                if self.no_input == 'InEvapT':
                    InEvap.h = OutEvap.h - OutEvap.q/OutEvap.m
                    InEvap.T = PropsSI('T','P',InEvap.p, 'H', InEvap.h, InEvap.fluidmixture)
                    InEvap.Cp = PropsSI('C','T',InEvap.T, 'P', InEvap.p, InEvap.fluidmixture)
                elif self.no_input == 'OutEvapT':
                    OutEvap.h = InEvap.h + InEvap.q/InEvap.m
                    OutEvap.T = PropsSI('T','P',OutEvap.p, 'H', OutEvap.h, OutEvap.fluidmixture)
                    OutEvap.Cp = PropsSI('C','T',OutEvap.T, 'P', OutEvap.p, OutEvap.fluidmixture)
                elif self.no_input == 'Evapm':
                    InEvap.m = InEvap.q/(OutEvap.h - InEvap.h)
                    OutEvap.m = InEvap.m
                
            cond = HX.Heatexchanger_module(InCond_REF, OutCond_REF, 1, InCond, OutCond, cond_ph)
        
            if self.inputs.cond_type == 'fthe':
                cond.FTHE(N_element=self.inputs.cond_N_element, N_row = self.inputs.cond_N_row)
                self.cond_err = (self.inputs.cond_T_lm - cond.T_lm)/self.inputs.cond_T_lm
                
            elif self.inputs.cond_type == 'phe':
                cond.PHE(N_element=self.inputs.cond_N_element)
                self.cond_err = (self.inputs.cond_T_pp - cond.T_pp)/self.inputs.cond_T_pp
            
            OutCond_REF = cond.primary_out
            
            if cond.T_rvs == 1:
                cond_p_lb = InCond_REF.p
            else:
                if self.cond_err < 0:
                    cond_p_ub = InCond_REF.p
                else:
                    cond_p_lb = InCond_REF.p
            
            if abs(self.cond_err) < self.inputs.tol:
                self.cond_conv_err = 0
                cond_a = 0
            elif cond_p_ub - cond_p_lb < self.inputs.tol:
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
        
class VCHP_injection(VCHP):
    def __init__(self, InCond, OutCond, InEvap, OutEvap, inputs):
        super().__init__(InCond, OutCond, InEvap, OutEvap, inputs)
    
    def InterPressure_Opt(self):
        dfrac = 0.005
        inter_frac_lb = 0.0
        inter_frac_ub = 1.0
        
        while 1:
            for iii in range(2):
                self.inter_frac = 0.5*(inter_frac_lb+inter_frac_ub)*(1-dfrac)
            else:
                self.inter_frac = 0.5*(inter_frac_lb+inter_frac_ub)*(1+dfrac)
                
            super().Cycle_Solver()
            
            super().Post_Processing()

if __name__ == '__main__':
    
    evapfluid = 'water'
    inevapT = 323.15
    inevapp = 101300.0
    InEvap = ProcessFluid(Y={evapfluid:1.0,},m = 1.0, T = inevapT, p = inevapp)
    
    outevapp = 101300.0
    OutEvap = ProcessFluid(Y={evapfluid:1.0,},p = outevapp)
    '''
    outevapT = 295.15
    outevapp = 101300.0
    OutEvap = ProcessFluid(Y={evapfluid:1.0,},m = 1.0, T = outevapT, p = outevapp)'''
    
    
    condfluid = 'water'
    incondT = 333.15
    incondp = 101300.0
    InCond = ProcessFluid(Y={condfluid:1.0,},m = 1.0, T = incondT, p = incondp)
    
    outcondT = 343.15
    outcondp = 101300.0
    outcondh = PropsSI('H','T',outcondT, 'P', outcondp, condfluid)
    outconds = PropsSI('S','T',outcondT, 'P', outcondp, condfluid)
    OutCond = ProcessFluid(Y={condfluid:1.0,},m = 1.0, T = outcondT, p = outcondp, q = 0.0, h = outcondh, s = outconds)
    
    '''
    outcondp = 101300.0
    OutCond = ProcessFluid(Y={condfluid:1.0,},p = outcondp, q = 0.0)'''
    
    inputs = Settings()
    inputs.Y = {'R134A':1.0,}
    inputs.second = 'process'
    inputs.cycle = 'vcc'
<<<<<<< HEAD
    inputs.cond_type = 'phe'
    inputs.evap_type = 'phe'
    inputs.layout = 'inj'
=======
    inputs.cond_type = 'fthe'
    inputs.evap_type = 'fthe'
    inputs.layout = 'ihx'

    #vchp_basic = VCHP(InCond, OutCond, InEvap, OutEvap, inputs)
    #vchp_basic()
>>>>>>> main
    
    
    vchp_basic = VCHP(InCond, OutCond, InEvap, OutEvap, inputs)    
    
    from cProfile import Profile
    
    profiler = Profile()
    profiler.run('vchp_basic()')
    
    from pstats import Stats
    
    stats = Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats('cumulative')
    stats.print_stats()