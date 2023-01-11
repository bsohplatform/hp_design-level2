from random import *
import pandas as pd
import os
from VCHP_layout import VCHP
from HP_dataclass import ProcessFluid, Settings, Outputs
from CoolProp.CoolProp import PropsSI

ref_list = ['Ammonia','CO2','Ethane','Ethylene','IsoButane','Isopentane','Propylene','R11','R113','R114','R115','R116','R12','R123','R1233zd(E)','R1234yf','R1234ze(E)','R1234ze(Z)','R124','R1243zf','R125','R13','R134a','R13I1','R14','R141b','R142b','R143a','R152A','R161','R21','R218','R22','R227EA','R23','R236EA','R236FA','R245ca','R245fa','R32','R365MFC','R40','R404A','R407C','R41','R410A','R507A','RC318','Water','n-Butane','n-Pentane','n-Propane']
Tcrt_list = [405.4, 304.1282, 305.322, 282.35, 407.817, 460.35, 364.211, 471.06, 487.21, 418.83, 353.1, 293.03, 385.12, 456.831, 439.6, 367.85, 382.52, 423.27, 395.425, 376.93, 339.173, 301.88, 374.21, 396.44, 227.51, 477.5, 410.26, 345.857, 386.411, 375.25, 451.48, 345.02, 369.295, 374.9, 299.293, 412.44, 398.07, 447.57, 427.01, 351.255, 460.0, 416.3, 345.27, 359.345, 317.28, 344.494, 343.765, 388.38, 647.096, 425.125, 469.7, 369.89]
Tnbp_list = [239.83431861980574, 216.592, 184.56858783245625, 169.37864843190997, 261.40097716144936, 300.97633181438664, 225.5308389820667, 296.85807236462267, 320.73517445831334, 276.74149036992037, 233.93183409414397, 195.05837337845716, 243.3977126672084, 300.97304760982433, 291.41300673628854, 243.6648737793625, 254.1817060635814, 282.8777863341162, 261.187129145237, 247.72635000907877, 225.0613923699324, 191.73815855630235, 247.07616894214513,
             251.29063349165594, 145.10484437128846, 305.19535070063444, 264.0267308938689, 225.90943385012372, 249.1279497615346, 235.59668768466616, 282.0119266440489, 236.36108741137815, 232.33952525912977, 256.80907279175136, 191.13213619322852, 279.32325411141977, 271.661627105418, 298.41219978647297, 288.1983205854856, 221.49865601382044, 313.34306890893464, 249.1726857448825, 227.30321032197264, 233.02189246544975, 194.79411644275066, 221.74709913892272, 226.408980824306, 267.1753253354927, 373.1242958476844, 272.6598619089341, 309.20934582034374, 231.03621464431768]

Tho_ub = 423.15
Tho_lb = 293.15
Thi_lb = 283.15
Tci_lb = 293.15
Tco_lb = 273.16

inputs = Settings()
inputs.second = 'process'
inputs.cycle = 'vcc'
inputs.layout = 'bas'
inputs.cond_N_row = 1
inputs.evap_N_row = 1
inputs.cond_N_element = 20
inputs.evap_N_element = 20
inputs.expand_eff = 0.0
inputs.mech_eff = 1.0

for i in range(50000):
    fluid_h = random()
    fluid_c = random()

    Tho = uniform(Tho_lb, Tho_ub)
    dTh = 19*random()+1
    Thi = max(Tho - dTh,Thi_lb)

    Tci = uniform(Tci_lb, Thi)
    dTc = (1.5*random()-0.5)*dTh
    Tco = max(Tci-dTc, Tco_lb)

    m_cond = 1.0


    ref_list_screen = []

    for ref, Tcrt, Tnbp in zip(ref_list, Tcrt_list, Tnbp_list):
            
        if fluid_h <= 0.5:
            Y_h = "Water"
            Ph = PropsSI("P","T",Tho,"Q",1.0,Y_h)
            Ph = max(Ph+100, 101300)
            inputs.cond_type = 'phe'
            inputs.cond_T_pp = 9.9*random()+0.1
            dTh = inputs.cond_T_pp
        else:
            Y_h = "Air"
            Ph = 101300
            inputs.cond_type = 'fthe'
            inputs.cond_T_lm = 17.0*random()+3.0
            dTh = inputs.cond_T_lm
        if fluid_c <= 0.5:
            Y_c = "Water"
            Pc = PropsSI("P","T",Tci,"Q",1.0,Y_c)
            Pc = max(Pc+100, 101300)
            inputs.evap_type = 'phe'
            inputs.evap_T_pp = 9.9*random()+0.1
            dTc = inputs.evap_T_pp
        else:
            Y_c = "Air"
            Pc = 101300
            inputs.evap_type = 'fthe'
            inputs.evap_T_lm = 17*random()+3.0
            dTc = inputs.evap_T_lm
        
        if Tcrt > 0.5*(Thi+Tho)+dTh and Tnbp < 0.5*(Tci+Tco)-dTc:
            ref_list_screen.append(ref)
        
        
    inputs.DSC = 9.9*random()+0.1
    inputs.DSH = 14.9*random()+0.1
    inputs.comp_eff = 0.6*random()+0.25
    
    results_mat = []
    for r in ref_list_screen:
        inputs.Y = {r:1.0,}
        InCond = ProcessFluid(Y={Y_h:1.0,}, m = m_cond, T = Thi, p = Ph)
        OutCond = ProcessFluid(Y={Y_h:1.0,}, m = m_cond, T = Tho, p = Ph)
        InEvap = ProcessFluid(Y={Y_c:1.0,}, m = 0.0, T = Tci, p = Pc)
        OutEvap = ProcessFluid(Y={Y_c:1.0,}, m = 0.0, T = Tco, p = Pc)
        vchp = VCHP(InCond, OutCond, InEvap, OutEvap, inputs)
        
        try:    
            (InCond, OutCond, InEvap, OutEvap, outputs) = vchp()
            if InEvap.m > 0.0:
                results = [outputs.COP_heating, Y_h, InCond.T, OutCond.T, InCond.p, InCond.m, dTh, Y_c, InEvap.T, OutEvap.T, InEvap.p, InEvap.m, dTc, outputs.DSH, inputs.DSC, inputs.comp_eff, r]
                results_mat.append(results)
        except:
            a = 0
        
    print('반복계산회수: %d'%(i))
    if not os.path.exists('Basic_DB.csv'):
        column_list = ['COP','fluid_h','Thi','Tho','Ph','mh','dTh','fluid_c','Tci','Tco','Pc','mc','dTc','DSH','DSC','comp_eff','Refrigerant']
        df = pd.DataFrame(results_mat, columns=column_list)
        df.to_csv('Basic_DB.csv', index=False, mode='w', encoding='utf-8-sig')
    else:
        df = pd.DataFrame(results_mat)
        df.to_csv('Basic_DB.csv', index=False, mode='a', encoding='utf-8-sig', header=False)