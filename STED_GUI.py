import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic
from CoolProp.CoolProp import PropsSI
from VCHP_layout import VCHP, VCHP_cascade
from HP_dataclass import ProcessFluid, Settings, Outputs

form_class = uic.loadUiType("STED_VCHP.ui")[0]

class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        
        self.ref_list = ['','1-Butene','Acetone','Air','Ammonia','Argon','Benzene','CO2','CarbonMonoxide','CarbonylSulfide','CycloHexane','CycloPropane','Cyclopentane','D4','D5','D6',
            'Deuterium','Dichloroethane','DiethylEther','DimethylCarbonate','DimethylEther','Ethane','Ethanol','EthylBenzene','Ethylene','EthyleneOxide','Fluorine','HFE143m','HeavyWater','Helium',
            'Hydrogen','HydrogenChloride','HydrogenSulfide','IsoButane','IsoButene','Isohexane','Isopentane','Krypton','MD2M','MD3M','MD4M','MDM','MM','Methane','Methanol','MethylLinoleate','MethylLinolenate',
            'MethylOleate','MethylPalmitate','MethylStearate','Neon','Neopentane','Nitrogen','NitrousOxide','Novec649','OrthoDeuterium','OrthoHydrogen','Oxygen','ParaDeuterium','ParaHydrogen','Propylene',
            'Propyne','R11','R113','R114','R115','R116','R12','R123','R1233zd(E)','R1234yf','R1234ze(E)','R1234ze(Z)','R124','R1243zf','R125','R13','R134a','R13I1','R14','R141b','R142b','R143a','R152A',
            'R161','R21','R218','R22','R227EA','R23','R236EA','R236FA','R245ca','R245fa','R32','R365MFC','R40','R404A','R407C','R41','R410A','R507A','RC318','SES36','SulfurDioxide','SulfurHexafluorid','Toluene',
            'Water','Xenon','cis-2-Butene','m-Xylene','n-Butane','n-Decane','n-Dodecane','n-Heptane','n-Hexane','n-Nonane','n-Octane','n-Pentane','n-Propane','n-Undecane','o-Xylene','p-Xylene','trans-2-Butene']
        
        self.setupUi(self)
        self.setWindowTitle("STED_VCHP")
        self.setWindowIcon(QIcon(".\Figs\icon.jpg"))
        
        self.bas_fig.setPixmap(QPixmap(".\Figs\Basic.png").scaledToHeight(300))
        self.ihx_fig.setPixmap(QPixmap(".\Figs\IHX.png").scaledToHeight(300))
        self.inj_fig.setPixmap(QPixmap(".\Figs\Injection.png").scaledToHeight(300))
        self.cas_fig.setPixmap(QPixmap(".\Figs\Cascade.png").scaledToHeight(300))
        
        self.process_fig.setPixmap(QPixmap(".\Figs\Process.png").scaledToWidth(300))
        self.steam_fig.setPixmap(QPixmap(".\Figs\Steam.png").scaledToWidth(300))
        self.hot_fig.setPixmap(QPixmap(".\Figs\Hotwater.png").scaledToWidth(300))
                
        for i in self.ref_list:
            self.ref_list_b.addItem(i)
            self.cond_fluid_list.addItem(i)
            self.evap_fluid_list.addItem(i)
        
        # 초기화
        self.layoutGroupRad()
        self.processGroupRad()
        self.cycleGroupRad()
        self.AllHidden_ProTab()
        self.phe_fthe_judge()
        
        # 레이아웃 선택
        self.bas_radio.clicked.connect(self.layoutGroupRad)
        self.ihx_radio.clicked.connect(self.layoutGroupRad)
        self.inj_radio.clicked.connect(self.layoutGroupRad)
        self.cas_radio.clicked.connect(self.layoutGroupRad)
        
        # 공정 선택
        self.process_radio.clicked.connect(self.processGroupRad)
        self.steam_radio.clicked.connect(self.processGroupRad)
        self.hot_radio.clicked.connect(self.processGroupRad)
        
        # 사이클 선택
        self.vcc_radio.clicked.connect(self.cycleGroupRad)
        self.scc_radio.clicked.connect(self.cycleGroupRad)
        
        # 탭간 이동 버튼
        self.LaytoPro_btn.clicked.connect(self.MoveToProcessTab)
        self.ProtoLay_btn.clicked.connect(self.MoveToLayoutTab)
        self.Calcstart_btn.clicked.connect(self.MoveToResultsTab)
        
        # 냉매 선택
        self.ref_list_b.currentIndexChanged.connect(self.ref_b_Select)
        self.ref_list_t.currentIndexChanged.connect(self.ref_t_Select)
        
        # 저온/고온 유체 선택
        self.evap_row_add_btn.clicked.connect(self.EvapRowAdd)
        self.evap_row_delete_btn.clicked.connect(self.EvapDeleteAdd)
        #self.evap_fluid_table.setColumnWidth(0, 0.08*self.width())
        #self.evap_fluid_table.setColumnWidth(1, 0.08*self.width())
        self.evap_fluid_list.currentIndexChanged.connect(self.EvapFluidAdd)
        
        self.cond_row_add_btn.clicked.connect(self.CondRowAdd)
        self.cond_row_delete_btn.clicked.connect(self.CondDeleteAdd)
        #self.cond_fluid_table.setColumnWidth(0, 0.08*self.width())
        #self.cond_fluid_table.setColumnWidth(1, 0.08*self.width())
        self.cond_fluid_list.currentIndexChanged.connect(self.CondFluidAdd)
        
        # 열교환기 타입 선택
        self.cond_phe_radio.clicked.connect(self.phe_fthe_judge)
        self.cond_fthe_radio.clicked.connect(self.phe_fthe_judge)
        self.evap_phe_radio.clicked.connect(self.phe_fthe_judge)
        self.evap_fthe_radio.clicked.connect(self.phe_fthe_judge)
        self.cas_phe_radio.clicked.connect(self.phe_fthe_judge)
        self.cas_fthe_radio.clicked.connect(self.phe_fthe_judge)
        
        # QEditLine 입력 완료시 행동
        self.DSH_edit.returnPressed.connect(self.EditEnteredAction)
        self.m_load_edit.returnPressed.connect(self.m_steam_copy)
        
    def MoveToLayoutTab(self):
        self.STED_tab.setCurrentWidget(self.layout_tab)
        self.AllHidden_ProTab()
        
    def MoveToProcessTab(self):
        self.STED_tab.setCurrentWidget(self.process_tab)
        self.ref_list_Indication()
        self.processGroupRad()
        self.layoutGroupRad()
        
    def MoveToResultsTab(self):
        self.STED_tab.setCurrentWidget(self.results_tab)
    
    def processGroupRad(self):
        if self.process_radio.isChecked():
            self.process_fig_tab2.setPixmap(QPixmap(".\Figs\Process.png").scaledToWidth(300))
            self.process_type = 'process'
            self.steam_hot_group.setHidden(True)
            self.cond_in_T_edit.setEnabled(True)
            self.cond_in_p_edit.setEnabled(True)
            self.cond_in_m_edit.setEnabled(True)
            self.cond_out_T_edit.setEnabled(True)
            self.cond_out_p_edit.setEnabled(True)
        elif self.steam_radio.isChecked():
            self.process_fig_tab2.setPixmap(QPixmap(".\Figs\Steam.png").scaledToWidth(300))            
            self.process_type = 'steam'
            self.Steam_batch()
        elif self.hot_radio.isChecked():
            self.process_fig_tab2.setPixmap(QPixmap(".\Figs\Hotwater.png").scaledToWidth(300))            
            self.process_type = 'hotwater'
            self.Hotwater_batch()
    
    def layoutGroupRad(self):
        if self.bas_radio.isChecked():
            self.layout_fig_tab2.setPixmap(QPixmap(".\Figs\Basic.png").scaledToHeight(500))
            self.layout_type = 'bas'
            self.Bas_batch()
        elif self.ihx_radio.isChecked():
            self.layout_fig_tab2.setPixmap(QPixmap(".\Figs\IHX.png").scaledToHeight(500))    
            self.layout_type = 'ihx'
            self.IHX_batch()
        elif self.inj_radio.isChecked():
            self.layout_fig_tab2.setPixmap(QPixmap(".\Figs\Injection.png").scaledToHeight(500))    
            self.layout_type = 'inj'
            self.Inj_batch()
        elif self.cas_radio.isChecked():
            self.layout_fig_tab2.setPixmap(QPixmap(".\Figs\Cascade.png").scaledToHeight(500))
            self.layout_type = 'cas'
            self.Cas_batch()
            
    def cycleGroupRad(self):
        if self.vcc_radio.isChecked():
            self.cycle_type = 'vcc'
        elif self.scc_radio.isChecked():
            self.cycle_type = 'scc'
        
    def ref_list_Indication(self):
        if self.layout_type == 'cas':
            self.ref_label_b.setText("냉매 (Bot)")
            self.ref_label_t.setText("냉매 (Top)")
            for i in self.ref_list:
                self.ref_list_t.addItem(i)
        else:
            self.ref_label_b.setText("냉매")
            self.ref_label_t.setText("")
            self.Tcrit_t.setText("")
            self.nbp_t.setText("")
            self.Tcrit_t_val.setText("")
            self.nbp_t_val.setText("") 
            self.ref_list_t.clear()
    
    def ref_b_Select(self):
        self.Y_b = self.ref_list_b.currentText()
        if self.Y_b != "":
            Tcrit_bottom = PropsSI('TCRIT','',0,'',0,self.Y_b)
            try: 
                nbp_bottom = PropsSI('T','P',101300,'Q',1.0,self.Y_b)
            except:
                nbp_bottom = PropsSI('TTRIPLE','',0,'',0,self.Y_b)
                self.nbp_b.setText("삼중점[℃]")
                
            self.Tcrit_b_val.setText(str(round(Tcrit_bottom-273.15,1)))
            self.nbp_b_val.setText(str(round(nbp_bottom-273.15,1)))
            
    def ref_t_Select(self):
        self.Y_t = self.ref_list_t.currentText()
        if self.Y_t != "":
            Tcrit_top = PropsSI('TCRIT','',0,'',0,self.Y_t)
            self.Tcrit_t.setText("임계점[℃]")
            try: 
                nbp_top = PropsSI('T','P',101300,'Q',1.0,self.Y_t)
                self.nbp_t.setText("NBP[℃]")
            except:
                nbp_top = PropsSI('TTRIPLE','',0,'',0,self.Y_t)
                self.nbp_t.setText("삼중점[℃]")
            self.Tcrit_t_val.setText(str(round(Tcrit_top-273.15,1)))
            self.nbp_t_val.setText(str(round(nbp_top-273.15,1))) 
        
    def EvapRowAdd(self):
        self.evap_fluid_table.insertRow(self.evap_fluid_table.rowCount())
        
    def EvapDeleteAdd(self):
        self.evap_fluid_table.removeRow(self.evap_fluid_table.rowCount()-1)
    
    def EvapFluidAdd(self):
        self.evap_fluid_table.setItem(self.evap_fluid_table.rowCount()-1, 0, QTableWidgetItem(self.evap_fluid_list.currentText()))
        self.evap_fluid_table.setItem(self.evap_fluid_table.rowCount()-1, 1, QTableWidgetItem('1.0'))
    
    def EvapFluidRatio(self): 
        self.evapY = {}
        for i in range(self.evap_fluid_table.rowCount()):
            self.condY[self.evap_fluid_table.item(i, 0).text()]=float(self.evap_fluid_table.item(i, 1).text())
    
    
    def CondRowAdd(self):
        self.cond_fluid_table.insertRow(self.cond_fluid_table.rowCount())
        
    def CondDeleteAdd(self):
        self.cond_fluid_table.removeRow(self.cond_fluid_table.rowCount()-1)
    
    def CondFluidAdd(self):
        self.cond_fluid_table.setItem(self.cond_fluid_table.rowCount()-1, 0, QTableWidgetItem(self.cond_fluid_list.currentText()))
        self.cond_fluid_table.setItem(self.cond_fluid_table.rowCount()-1, 1, QTableWidgetItem('1.0'))
        
    def CondFluidRatio(self): 
        self.condY = {}
        for i in range(self.cond_fluid_table.rowCount()):
            self.condY[self.cond_fluid_table.item(i, 0).text()]=float(self.cond_fluid_table.item(i, 1).text())
    
            
    
    def AllHidden_ProTab(self):
        self.expand_group.setHidden(True)
        self.expand_top_group.setHidden(True)
        self.expand_bot_group.setHidden(True)
        self.comp_group.setHidden(True)
        self.comp_top_group.setHidden(True)
        self.comp_bot_group.setHidden(True)
        self.cond_group.setHidden(True)
        self.cond_in_group.setHidden(True)
        self.cond_out_group.setHidden(True)
        self.evap_group.setHidden(True)
        self.evap_in_group.setHidden(True)
        self.evap_out_group.setHidden(True)
        self.cas_group.setHidden(True)
        self.IHX_group.setHidden(True)
        self.steam_hot_group.setHidden(True)
        self.DSH_group.setHidden(True)
        self.DSC_group.setHidden(True)
        
    def Bas_batch(self):
        self.comp_group.setHidden(False)
        self.expand_group.setHidden(False)
        self.cond_group.setHidden(False)
        self.cond_in_group.setHidden(False)
        self.cond_out_group.setHidden(False)
        self.evap_group.setHidden(False)
        self.evap_in_group.setHidden(False)
        self.evap_out_group.setHidden(False)
        self.DSH_group.setHidden(False)
        self.DSC_group.setHidden(False)
        
    def IHX_batch(self):
        self.comp_top_group.setHidden(False)
        self.expand_bot_group.setHidden(False)
        self.cond_group.setHidden(False)
        self.cond_in_group.setHidden(False)
        self.cond_out_group.setHidden(False)
        self.evap_group.setHidden(False)
        self.evap_in_group.setHidden(False)
        self.evap_out_group.setHidden(False)
        self.DSH_group.setHidden(False)
        self.DSC_group.setHidden(False)
        self.IHX_group.setHidden(False)
        
    def Inj_batch(self):
        self.comp_group.setHidden(False)
        self.expand_top_group.setHidden(False)
        self.expand_bot_group.setHidden(False)
        self.cond_group.setHidden(False)
        self.cond_in_group.setHidden(False)
        self.cond_out_group.setHidden(False)
        self.evap_group.setHidden(False)
        self.evap_in_group.setHidden(False)
        self.evap_out_group.setHidden(False)
        self.DSH_group.setHidden(False)
        self.DSC_group.setHidden(False)
        
        
    def Cas_batch(self):
        self.comp_top_group.setHidden(False)
        self.comp_bot_group.setHidden(False)
        self.expand_top_group.setHidden(False)
        self.expand_bot_group.setHidden(False)
        self.cond_group.setHidden(False)
        self.cond_in_group.setHidden(False)
        self.cond_out_group.setHidden(False)
        self.evap_group.setHidden(False)
        self.evap_in_group.setHidden(False)
        self.evap_out_group.setHidden(False)
        self.DSH_group.setHidden(False)
        self.DSC_group.setHidden(False)
        self.cas_group.setHidden(False)
        
    def Steam_batch(self):
        self.steam_hot_group.setHidden(False)
        self.Thot_target_label.setHidden(True)
        self.Thot_target_edit.setHidden(True)
        self.time_target_label.setHidden(True)
        self.time_target_edit.setHidden(True)
        self.mmakeup_label.setHidden(False)
        self.mmakeup_edit.setHidden(False)
        self.dT_lift_label.setText("증기온도 [℃]")
        self.m_load_label.setText("증기유량 [kg/s]")
        self.cond_in_T_edit.setEnabled(False)
        self.cond_in_p_edit.setEnabled(False)
        self.cond_in_m_edit.setEnabled(False)
        self.cond_out_T_edit.setEnabled(False)
        self.cond_out_p_edit.setEnabled(False)
        
    def Hotwater_batch(self):
        self.steam_hot_group.setHidden(False)
        self.steam_hot_group.setHidden(False)
        self.Thot_target_label.setHidden(False)
        self.Thot_target_edit.setHidden(False)
        self.time_target_label.setHidden(False)
        self.time_target_edit.setHidden(False)
        self.mmakeup_label.setHidden(True)
        self.mmakeup_edit.setHidden(True)
        self.dT_lift_label.setText("응축기 가열능력 [℃]")
        self.m_load_label.setText("급탕조용량 [kg]")
        self.cond_in_T_edit.setEnabled(False)
        self.cond_in_p_edit.setEnabled(False)
        self.cond_in_m_edit.setEnabled(False)
        self.cond_out_T_edit.setEnabled(False)
        self.cond_out_p_edit.setEnabled(False)
        
    def m_steam_copy(self):
        self.mmakeup_edit.setText(self.m_load_edit.text())
    
    def phe_fthe_judge(self):
        if self.cond_phe_radio.isChecked():
            self.cond_N_row_label.setHidden(True)
            self.cond_N_row_edit.setHidden(True)
            self.cond_T_pp_label.setText('접근온도차 [℃]')
        elif self.cond_fthe_radio.isChecked():
            self.cond_N_row_label.setHidden(False)
            self.cond_N_row_edit.setHidden(False)
            self.cond_T_pp_label.setText('LMTD [℃]')
            
        if self.evap_phe_radio.isChecked():
            self.evap_N_row_label.setHidden(True)
            self.evap_N_row_edit.setHidden(True)
            self.evap_T_pp_label.setText('접근온도차 [℃]')
        elif self.evap_fthe_radio.isChecked():
            self.evap_N_row_label.setHidden(False)
            self.evap_N_row_edit.setHidden(False)
            self.evap_T_pp_label.setText('LMTD [℃]')
            
        if self.cas_phe_radio.isChecked():
            self.cas_N_row_label.setHidden(True)
            self.cas_N_row_edit.setHidden(True)
            self.cas_T_pp_label.setText('접근온도차 [℃]')
        elif self.cas_fthe_radio.isChecked():
            self.cas_N_row_label.setHidden(False)
            self.cas_N_row_edit.setHidden(False)
            self.cas_T_pp_label.setText('LMTD [℃]')
    
    def EditEnteredAction(self):
        if self.layout_type == 'cas':
            self.inputs_t = Settings()
            self.inputs_b = Settings()
            self.outputs_t = Settings()
            self.outputs_b = Settings()
        else:
            self.inputs = Settings()
            self.outputs = Settings()
            self.inputs.DSH = float(self.DSH_edit.text())
            self.inputs.DSC = float(self.DSC_edit.text())
            self.inputs.cond_N_element = float(self.cond_N_row_edit.text())
            
            if self.cond_phe_radio.isChecked():
                self.inputs.cond_N_row = float(self.cond_N_row_edit.text())
            elif self.cond_fthe_radio.isChecked():
                
            if self.layout_type == 'bas':
                self.inputs.comp_eff = float(self.comp_eff_edit.text())    
            elif self.layout_type == 'ihx':
                self.inputs.comp_eff = float(self.comp_eff_top_edit.text())
            elif self.layout_type == 'inj':
                self.inputs.comp_eff = float(self.comp_eff_edit.text())    
        
    
    
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
        
        return (InCond, OutCond)
        
    def Hotwater_module(self, InCond, OutCond, inputs):
        rho_water = PropsSI('D','T',0.5*(inputs.T_makeup+inputs.T_target),'P',101300, InCond.fluidmixture)
        self.V_tank = inputs.M_load/rho_water
        
        h_target = PropsSI('H','T',inputs.T_target,'P',101300.0,InCond.fluidmixture)
        h_makeup = PropsSI('H','T',inputs.T_makeup,'P',101300.0,InCond.fluidmixture)
        InCond.h = 0.5*(h_target + h_makeup)
        InCond.T = PropsSI('T','H',InCond.h,'P',101300, InCond.fluidmixture)
        Cp_water = PropsSI('C','T',InCond.T,'P',101300, InCond.fluidmixture)
        OutCond.q = 0.5*inputs.M_load*Cp_water*(inputs.T_target - InCond.T)/inputs.time_target
        OutCond.m = OutCond.q/(Cp_water*inputs.dT_lift)
        OutCond.T = InCond.T + inputs.dT_lift
        
        return (InCond, OutCond)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    myWindow = WindowClass()
    myWindow.show()
    
    app.exec_()