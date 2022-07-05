from enum import Enum
from dataclasses import dataclass, field
from CoolProp.CoolProp import PropsSI

"""
Common Data Types

"""
@dataclass
class WireObjectFluid:
    """
    * Wire Object - Fluid
        - Y: 조성 질량비(Dictionary)
        ex)     {
                    "H2O": 0.43,
                    "O2": 0.13
                }
        - m: 질량 유량 (kg/s)
        - T: 온도 (K)
        - p: 절대 압력 (Pa)
        - q: 공정열
        - h: 비 엔탈피 (J/kg)
        - s: 비 엔트로피 (J/kg/K)
    """

    """
    TODO
    1. fluid_type이 문서 상에는 없지만, vchp 모듈에서는 입력 파라미터에 fluid_type이 존재해서 우선 추가. 확인 필요
    2. 공정열(q)는 기본 사양에는 없지만 VCHP의 output이 공정열이라는 값을 반환. 확인 필요
    """

    Y: dict = field(default_factory=dict) # Default_factory는 배열 형태 자료형을 미리 할당함 (default_factory=list, default_factory=tuple, ...)
    m: float = 0.0
    T: float = 0.0
    p: float = 0.0
    q: float = 0.0
    h: float = 0.0
    s: float = 0.0
    fluidmixture: str = ''
    p_crit: float = 0.0
    T_crit: float = 0.0
    
    def __init__(self, Y):
        
        for fluids, ratio in Y.items():
            print(type(fluids))
            
            if fluids == list(Y.keys())[-1]:
                self.fluidmixture = self.fluidmixture+fluids+'['+str(ratio)+']'
            else:
                self.fluidmixture = self.fluidmixture+fluids+'['+str(ratio)+']'+'&'
                
        self.p_crit: float = PropsSI('PCRIT','',0,'',0,self.fluidmixture)
        self.T_crit: float = PropsSI('TCRIT','',0,'',0,self.fluidmixture)
        
        
@dataclass
class Settings:
    # 응축기 스펙
    cond_T_pp: float = 5.0
    cond_T_lm: float = 15.0
    cond_dP: float = 0.01
    cond_N_element: int = 30
    cond_N_row: int = 5
    cond_UA = 0.0
    
    # 증발기 스펙
    evap_T_pp: float = 5.0
    evap_T_lm: float = 15.0
    evap_dP: float = 0.01
    evap_N_element: int = 30
    evap_N_row: int = 5
    evap_UA = 0.0
    
    # 터보기기 스펙
    comp_eff: float = 0.7
    expand_eff: float = 0.8
    
    # 중간열교환기 스펙
    ihx_eff: float = 0.9
    ihx_cold_dP: float = 0.01
    ihx_hot_dP: float = 0.01
    
    # 케스케이드 열교환기 스펙
    cas_T_pp: float = 5.0
    cas_T_lm: float = 15.0
    cas_cold_dP: float = 0.01
    cas_hot_dP: float = 0.01
    cas_N_element: int = 30
    
    P_crit: float = 0.0
    T_crit: float = 0.0
    h_crit: float = 0.0
    s_crit: float = 0.0
    
    
    # 수렴오차
    tol: float = 1.0-3

@dataclass
class Errormsg:
    cond_T_rvs: int = 1
    evap_T_rvs: int = 1
    cas_T_rvs: int = 1
    P_high: int = 1
    P_low: int = 1

'''
class Auxfunction:
    def __init__(self):
        self.fluidmixture = 
    
    def YtoFluidmix(self, Y:dict):
        for fluids, ratio in Y.items():
            print(type(fluids))
            
            if fluids == list(Y.keys())[-1]:
                self.fluidmixture = self.fluidmixture+fluids+'['+str(ratio)+']'
            else:
                self.fluidmixture = self.fluidmixture+fluids+'['+str(ratio)+']'+'&'
            
        return(self.fluidmixture)'''

    
    

if __name__ == "__main__":
    
    print("...")
    vchp_input_1 = WireObjectFluid(Y={'Ethane': 0.3, 'Propane':0.7})
    fluids = vchp_input_1.fluidmixture
    print(fluids)
    h = PropsSI('H','T',300,'P',1.0e5,fluids)
    print(h)
    print(vchp_input_1.p_crit)