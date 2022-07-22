from enum import Enum
from dataclasses import dataclass, field
from re import T
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

    
    
    def __init__(self,  Y: dict = field(default_factory=dict),  m: float = 0.0,  T: float = 0.0, p: float = 0.0, q: float = 0.0, h: float = 0.0, s: float = 0.0):
        self.fluidmixture: str = ''
        for fluids, ratio in Y.items():         
            if fluids == list(Y.keys())[-1]:
                self.fluidmixture = self.fluidmixture+fluids+'['+str(ratio)+']'
            else:
                self.fluidmixture = self.fluidmixture+fluids+'['+str(ratio)+']'+'&'
                    
        self.m = m
        self.T = T
        self.p = p
        self.q = q
        self.h = h
        self.s = s
        self.p_crit: float = PropsSI('PCRIT','',0,'',0,self.fluidmixture)
        self.T_crit: float = PropsSI('TCRIT','',0,'',0,self.fluidmixture)

        
@dataclass
class Settings:
    # 냉매 입력
    Y = {'R410A':1.0}
    
    # 공정 정보
    second: str = 'process'
    
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
    
    # 증기 공정 조건 입력
    T_steam: float = 120.0
    T_steam = T_steam + 273.15
    m_steam: float = 0.1
    T_makeup: float = 30.0
    T_makeup = T_makeup + 273.15
    m_makeup = 1.0
    
    # 급탕 공정 조건 입력
    M_load: float = 100.0
    T_target: float = 60
    T_target = T_target + 273.15
    dT_lift: float = 10.0
    time_target: float = 600.0
    # 수렴오차
    tol: float = 1.0-3
        
@dataclass
class Bound:
    # 압축기 하한 경계 조건
    p_lb: float = 0.0
    p_ub: float = 0.0
    
    # 공정 정보
    second: str = 'process'
    
    # 응축기 스펙
    cond_T_pp: float = 5.0
    cond_T_lm: float = 15

if __name__ == "__main__":
    
    print("...")
    vchp_input_1 = WireObjectFluid(Y={'Ethane': 0.3, 'Propane':0.7},T=300, p=1.0e5)
    fluids = vchp_input_1.fluidmixture
    print(fluids)
    h = PropsSI('H','T',vchp_input_1.T,'P',vchp_input_1.p,fluids)
    print(h)
    print(vchp_input_1.p_crit)