from cmath import sqrt
import sys
import os
from CoolProp.CoolProp import PropsSI

from PySide6.QtCore import QSize, Qt, QFile
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QTableWidgetItem, QMessageBox
from PySide6.QtUiTools import QUiLoader

def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))    
    return os.path.join(base_path, relative_path)

sys.path.append(resource_path('Solver'))
from VCHP_layout import VCHP, VCHP_cascade
from HP_dataclass import ProcessFluid, Settings, Outputs

class WindowClass(QMainWindow):
    def __init__(self):
        super().__init__()
        loader = QUiLoader()
        ui_file = QFile(resource_path('STED_VCHP.ui'))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()
        
        self.setCentralWidget(self.ui)
        self.ui.show()
        
        self.ref_list = ['','1-Butene','Acetone','Air','Ammonia','Argon','Benzene','CO2','CarbonMonoxide','CarbonylSulfide','CycloHexane','CycloPropane','Cyclopentane','D4','D5','D6',
            'Deuterium','Dichloroethane','DiethylEther','DimethylCarbonate','DimethylEther','Ethane','Ethanol','EthylBenzene','Ethylene','EthyleneOxide','Fluorine','HFE143m','HeavyWater','Helium',
            'Hydrogen','HydrogenChloride','HydrogenSulfide','IsoButane','IsoButene','Isohexane','Isopentane','Krypton','MD2M','MD3M','MD4M','MDM','MM','Methane','Methanol','MethylLinoleate','MethylLinolenate',
            'MethylOleate','MethylPalmitate','MethylStearate','Neon','Neopentane','Nitrogen','NitrousOxide','Novec649','OrthoDeuterium','OrthoHydrogen','Oxygen','ParaDeuterium','ParaHydrogen','Propylene',
            'Propyne','R11','R113','R114','R115','R116','R12','R123','R1233zd(E)','R1234yf','R1234ze(E)','R1234ze(Z)','R124','R1243zf','R125','R13','R134a','R13I1','R14','R141b','R142b','R143a','R152A',
            'R161','R21','R218','R22','R227EA','R23','R236EA','R236FA','R245ca','R245fa','R32','R365MFC','R40','R404A','R407C','R41','R410A','R507A','RC318','SES36','SulfurDioxide','SulfurHexafluorid','Toluene',
            'Water','Xenon','cis-2-Butene','m-Xylene','n-Butane','n-Decane','n-Dodecane','n-Heptane','n-Hexane','n-Nonane','n-Octane','n-Pentane','n-Propane','n-Undecane','o-Xylene','p-Xylene','trans-2-Butene']
        
        
        self.setWindowTitle("STED_VCHP")
        self.setWindowIcon(QIcon(resource_path("Figs/icon.jpg")))
        
        self.ui.bas_fig.setPixmap(QPixmap(resource_path("Figs/Basic.png")).scaledToHeight(300))
        self.ui.ihx_fig.setPixmap(QPixmap(resource_path("Figs/IHX.png")).scaledToHeight(300))
        self.ui.inj_fig.setPixmap(QPixmap(resource_path("Figs/Injection.png")).scaledToHeight(300))
        self.ui.cas_fig.setPixmap(QPixmap(resource_path("Figs/Cascade.png")).scaledToHeight(300))
        
        self.ui.process_fig.setPixmap(QPixmap(resource_path("Figs/Process.png")).scaledToWidth(300))
        self.ui.steam_fig.setPixmap(QPixmap(resource_path("Figs/Steam.png")).scaledToWidth(300))
        self.ui.hot_fig.setPixmap(QPixmap(resource_path("Figs/Hotwater.png")).scaledToWidth(300))
                
        for i in self.ref_list:
            self.ui.ref_list_b.addItem(i)
            self.ui.cond_fluid_list.addItem(i)
            self.ui.evap_fluid_list.addItem(i)
        
        # 초기화
        self.cycleGroupRad()
        self.layoutGroupRad()
        self.processGroupRad()
        self.AllHidden_ProTab()
        self.phe_fthe_judge()
        
        # 사이클 선택
        self.ui.vcc_radio.clicked.connect(self.cycleGroupRad)
        self.ui.scc_radio.clicked.connect(self.cycleGroupRad)
        
        # 레이아웃 선택
        self.ui.bas_radio.clicked.connect(self.layoutGroupRad)
        self.ui.ihx_radio.clicked.connect(self.layoutGroupRad)
        self.ui.inj_radio.clicked.connect(self.layoutGroupRad)
        self.ui.cas_radio.clicked.connect(self.layoutGroupRad)
        
        # 공정 선택
        self.ui.process_radio.clicked.connect(self.processGroupRad)
        self.ui.steam_radio.clicked.connect(self.processGroupRad)
        self.ui.hot_radio.clicked.connect(self.processGroupRad)
        
        # 탭간 이동 버튼
        self.ui.LaytoPro_btn.clicked.connect(self.MoveToProcessTab)
        self.ui.ProtoLay_btn.clicked.connect(self.MoveToLayoutTab)
        
        # 냉매 선택
        self.ui.ref_list_b.currentIndexChanged.connect(self.ref_b_Select)
        self.ui.ref_list_t.currentIndexChanged.connect(self.ref_t_Select)
        
        # 저온/고온 유체 선택
        self.ui.evap_row_add_btn.clicked.connect(self.EvapRowAdd)
        self.ui.evap_row_delete_btn.clicked.connect(self.EvapDeleteAdd)
        #self.ui.evap_fluid_table.setColumnWidth(0, 0.08*self.ui.width())
        #self.ui.evap_fluid_table.setColumnWidth(1, 0.08*self.ui.width())
        self.ui.evap_fluid_list.currentIndexChanged.connect(self.EvapFluidAdd)
        
        self.ui.cond_row_add_btn.clicked.connect(self.CondRowAdd)
        self.ui.cond_row_delete_btn.clicked.connect(self.CondDeleteAdd)
        #self.ui.cond_fluid_table.setColumnWidth(0, 0.08*self.ui.width())
        #self.ui.cond_fluid_table.setColumnWidth(1, 0.08*self.ui.width())
        self.ui.cond_fluid_list.currentIndexChanged.connect(self.CondFluidAdd)
        
        # 열교환기 타입 선택
        self.ui.cond_phe_radio.clicked.connect(self.phe_fthe_judge)
        self.ui.cond_fthe_radio.clicked.connect(self.phe_fthe_judge)
        self.ui.evap_phe_radio.clicked.connect(self.phe_fthe_judge)
        self.ui.evap_fthe_radio.clicked.connect(self.phe_fthe_judge)
        self.ui.cas_phe_radio.clicked.connect(self.phe_fthe_judge)
        self.ui.cas_fthe_radio.clicked.connect(self.phe_fthe_judge)
        
        # 공정 입력 했을 때 행동
        self.ui.cond_in_T_edit.textChanged.connect(self.LimitProcessInput)
        self.ui.cond_out_T_edit.textChanged.connect(self.LimitProcessInput)
        self.ui.cond_in_m_edit.textChanged.connect(self.LimitProcessInput)
        self.ui.evap_in_T_edit.textChanged.connect(self.LimitProcessInput)
        self.ui.evap_out_T_edit.textChanged.connect(self.LimitProcessInput)
        self.ui.evap_in_m_edit.textChanged.connect(self.LimitProcessInput)
        
        # 입력검사시 행동
        self.ui.Inspection_btn.clicked.connect(self.Inspection_action)
        
        # 계산시작시 행동
        self.ui.Calcstart_btn.clicked.connect(self.Calcstart_action)
        
        # 입력문 예시 버튼
        self.ui.Example_btn.clicked.connect(self.InputExample)
        self.ui.Input_delete_btn.clicked.connect(self.InputClear)
        
        # 밸브 추천 버튼
        self.ui.valve_recommand.clicked.connect(self.Valve_Recommand)
        
        # 압축기 추천 버튼
        self.ui.compressor_recommand.clicked.connect(self.Compressor_Recommand)
    def MoveToLayoutTab(self):
        self.ui.STED_tab.setCurrentWidget(self.ui.layout_tab)
        self.ui.Calcstart_btn.setEnabled(False)
        self.ui.valve_recommand.setEnabled(False)
        self.ui.compressor_recommand.setEnabled(False)
        self.InputClear()
        
    def MoveToProcessTab(self):
        self.ui.STED_tab.setCurrentWidget(self.ui.process_tab)
        self.ref_list_Indication()
        self.AllHidden_ProTab()
        self.processGroupRad()
        self.layoutGroupRad()
        self.cycleGroupRad()
        self.ui.Calcstart_btn.setEnabled(False)
        self.ui.valve_recommand.setEnabled(False)
        self.ui.compressor_recommand.setEnabled(False)
        
    def MoveToResultsTab(self):
        self.ui.STED_tab.setCurrentWidget(self.ui.results_tab)
    
    def processGroupRad(self):
        if self.ui.process_radio.isChecked():
            self.ui.process_fig_tab2.setPixmap(QPixmap(resource_path("Figs/Process.png")).scaledToWidth(300))
            self.process_type = 'process'
            self.Process_batch()
        elif self.ui.steam_radio.isChecked():
            self.ui.process_fig_tab2.setPixmap(QPixmap(resource_path("Figs/Steam.png")).scaledToWidth(300))
            self.process_type = 'steam'
            self.ui.cond_fluid_table.setItem(0, 0, QTableWidgetItem('Water'))
            self.ui.cond_fluid_table.setItem(0, 1, QTableWidgetItem('1.0'))
            self.Steam_batch()
        elif self.ui.hot_radio.isChecked():
            self.ui.process_fig_tab2.setPixmap(QPixmap(resource_path("Figs/Hotwater.png")).scaledToWidth(300))
            self.process_type = 'hotwater'
            self.ui.cond_fluid_table.setItem(0, 0, QTableWidgetItem('Water'))
            self.ui.cond_fluid_table.setItem(0, 1, QTableWidgetItem('1.0'))
            self.Hotwater_batch()
        
        
        
    def layoutGroupRad(self):
        if self.ui.bas_radio.isChecked():
            self.ui.layout_fig_tab2.setPixmap(QPixmap(resource_path("Figs/Basic.png")).scaledToHeight(500))
            self.layout_type = 'bas'
            self.Bas_batch()
        elif self.ihx_radio.isChecked():
            self.layout_fig_tab2.setPixmap(QPixmap(resource_path("Figs/IHX.png")).scaledToHeight(500))
            self.layout_type = 'ihx'
            self.IHX_batch()
        elif self.inj_radio.isChecked():
            self.layout_fig_tab2.setPixmap(QPixmap(resource_path("Figs/Injection.png")).scaledToHeight(500))
            self.layout_type = 'inj'
            self.Inj_batch()
        elif self.cas_radio.isChecked():
            self.layout_fig_tab2.setPixmap(QPixmap(resource_path("Figs/Cascade.png")).scaledToHeight(500))
            self.layout_type = 'cas'
            self.Cas_batch()
            
    def cycleGroupRad(self):
        if self.ui.vcc_radio.isChecked():
            self.cycle_type = 'vcc'
        elif self.ui.scc_radio.isChecked():
            self.cycle_type = 'scc'
        
        
    def ref_list_Indication(self):
        if self.layout_type == 'cas':
            self.ui.ref_label_b.setText("냉매 (Bot)")
            self.ui.ref_label_t.setText("냉매 (Top)")
            for i in self.ref_list:
                self.ui.ref_list_t.addItem(i)
        else:
            self.ui.ref_label_b.setText("냉매")
            self.ui.ref_label_t.setText("")
            self.ui.Tcrit_t.setText("")
            self.ui.nbp_t.setText("")
            self.ui.Tcrit_t_val.setText("")
            self.ui.nbp_t_val.setText("") 
            self.ui.ref_list_t.clear()
    
    def ref_b_Select(self):
        self.Y_b = self.ui.ref_list_b.currentText()
        if self.Y_b != "":
            self.Tcrit_bottom = PropsSI('TCRIT','',0,'',0,self.Y_b)
            try: 
                self.nbp_bottom = PropsSI('T','P',101300,'Q',1.0,self.Y_b)
            except:
                self.nbp_bottom = PropsSI('TTRIPLE','',0,'',0,self.Y_b)
                self.nbp_b.setText("삼중점[℃]")
                
            self.ui.Tcrit_b_val.setText(str(round(self.Tcrit_bottom-273.15,1)))
            self.ui.nbp_b_val.setText(str(round(self.nbp_bottom-273.15,1)))
                
            
    def ref_t_Select(self):
        self.Y_t = self.ui.ref_list_t.currentText()
        if self.Y_t != "":
            self.Tcrit_top = PropsSI('TCRIT','',0,'',0,self.Y_t)
            self.ui.Tcrit_t.setText("임계점[℃]")
            try: 
                self.nbp_top = PropsSI('T','P',101300,'Q',1.0,self.Y_t)
                self.ui.nbp_t.setText("NBP[℃]")
            except:
                self.nbp_top = PropsSI('TTRIPLE','',0,'',0,self.Y_t)
                self.ui.nbp_t.setText("삼중점[℃]")
            self.ui.Tcrit_t_val.setText(str(round(self.Tcrit_top-273.15,1)))
            self.ui.nbp_t_val.setText(str(round(self.nbp_top-273.15,1))) 
            
    def EvapRowAdd(self):
        self.ui.evap_fluid_table.insertRow(self.ui.evap_fluid_table.rowCount())
        
    def EvapDeleteAdd(self):
        self.ui.evap_fluid_table.removeRow(self.ui.evap_fluid_table.rowCount()-1)
    
    def EvapFluidAdd(self):
        self.ui.evap_fluid_table.setItem(self.ui.evap_fluid_table.rowCount()-1, 0, QTableWidgetItem(self.ui.evap_fluid_list.currentText()))
        self.ui.evap_fluid_table.setItem(self.ui.evap_fluid_table.rowCount()-1, 1, QTableWidgetItem('1.0'))
        if self.ui.evap_fluid_list.currentText() == 'Air':
            self.ui.evap_row_add_btn.setEnabled(False)
        else:
            self.ui.evap_row_add_btn.setEnabled(True)
            
    
    def EvapFluidRatio(self):
        self.evapY = {}
        frac_total = 0.0
        
        if self.ui.evap_fluid_table.rowCount() == 0:
            QMessageBox.warning(self, '입력문 검토', '저온 유체 행을 추가하세요.', QMessageBox.Yes)
            self.message_chk = self.message_chk+1
        else:
            for i in range(self.ui.evap_fluid_table.rowCount()):
                if self.ui.evap_fluid_table.item(i,1) is not None:
                    if self.ui.evap_fluid_table.item(i,1).text() != '':
                        frac_total = frac_total + float(self.ui.evap_fluid_table.item(i, 1).text())
                    else:
                        QMessageBox.warning(self, '입력문 검토', '저온 유체 조성비를 정의하세요.', QMessageBox.Yes)
                        self.message_chk = self.message_chk+1    
                else:
                    QMessageBox.warning(self, '입력문 검토', '저온 유체 조성비를 정의하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1    

            if frac_total != 0:
                for i in range(self.ui.evap_fluid_table.rowCount()):
                    if self.ui.evap_fluid_table.item(i,0) is not None:
                        if self.ui.evap_fluid_table.item(i,0).text() != '':        
                            if self.ui.evap_fluid_table.item(i,0).text() == 'Air' and self.ui.evap_fluid_table.rowCount() != 1:
                                QMessageBox.warning(self, '입력문 검토', '저온 유체에 Air Mixture는 계산할 수 없습니다.', QMessageBox.Yes)
                                self.message_chk = self.message_chk+1
                            else:
                                self.evapY[self.ui.evap_fluid_table.item(i, 0).text()]=float(self.ui.evap_fluid_table.item(i, 1).text())/frac_total
                        else:
                            QMessageBox.warning(self, '입력문 검토', '저온 유체 종류를 정의하세요.', QMessageBox.Yes)
                            self.message_chk = self.message_chk+1
                    else:
                        QMessageBox.warning(self, '입력문 검토', '저온 유체 종류를 정의하세요.', QMessageBox.Yes)
                        self.message_chk = self.message_chk+1
                    

    def CondRowAdd(self):
        self.ui.cond_fluid_table.insertRow(self.ui.cond_fluid_table.rowCount())
        
    def CondDeleteAdd(self):
        self.ui.cond_fluid_table.removeRow(self.ui.cond_fluid_table.rowCount()-1)
    
    def CondFluidAdd(self):
        self.ui.cond_fluid_table.setItem(self.ui.cond_fluid_table.rowCount()-1, 0, QTableWidgetItem(self.ui.cond_fluid_list.currentText()))
        self.ui.cond_fluid_table.setItem(self.ui.cond_fluid_table.rowCount()-1, 1, QTableWidgetItem('1.0'))
        if self.ui.cond_fluid_list.currentText() == 'Air':
            self.ui.cond_row_add_btn.setEnabled(False)
        else:
            self.ui.cond_row_add_btn.setEnabled(True)

    def CondFluidRatio(self):
        self.condY = {}
        frac_total = 0.0
        if self.ui.cond_fluid_table.rowCount() == 0:
            QMessageBox.warning(self, '입력문 검토', '고온 유체 행을 추가하세요.', QMessageBox.Yes)
            self.message_chk = self.message_chk+1
        else:
            for i in range(self.ui.cond_fluid_table.rowCount()):
                if self.ui.cond_fluid_table.item(i,1) is not None:
                    if self.ui.cond_fluid_table.item(i,1).text() != '':                        
                        frac_total = frac_total + float(self.ui.cond_fluid_table.item(i, 1).text())
                    else:
                        QMessageBox.warning(self, '입력문 검토', '고온 유체 조성비를 정의하세요.', QMessageBox.Yes)
                        self.message_chk = self.message_chk+1
                else:
                    QMessageBox.warning(self, '입력문 검토', '고온 유체 조성비를 정의하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
            
            if frac_total != 0:
                for i in range(self.ui.cond_fluid_table.rowCount()):
                    if self.ui.cond_fluid_table.item(i,0) is not None:
                        if self.ui.cond_fluid_table.item(i,0).text() != '':
                            if self.ui.cond_fluid_table.item(i,0).text() == 'Air' and self.ui.cond_fluid_table.rowCount() != 1:
                                QMessageBox.warning(self, '입력문 검토', '고온 유체에 Air Mixture는 계산할 수 없습니다.', QMessageBox.Yes)
                                self.message_chk = self.message_chk+1
                            else:
                                self.condY[self.ui.cond_fluid_table.item(i, 0).text()]=float(self.ui.cond_fluid_table.item(i, 1).text())/frac_total
                        else:
                            QMessageBox.warning(self, '입력문 검토', '고온 유체 종류를 정의하세요.', QMessageBox.Yes)
                            self.message_chk = self.message_chk+1
                    else:
                        QMessageBox.warning(self, '입력문 검토', '고온 유체 종류를 정의하세요.', QMessageBox.Yes)
                        self.message_chk = self.message_chk+1
        
    def Inspection_action(self):
        self.message_chk = 0
        self.InputsEnteredAction()
        self.ProcessEnteredAction()
    
    def AllHidden_ProTab(self):
        self.ui.expand_group.setHidden(True)
        self.ui.expand_top_group.setHidden(True)
        self.ui.expand_bot_group.setHidden(True)
        self.ui.comp_group.setHidden(True)
        self.ui.comp_top_group.setHidden(True)
        self.ui.comp_bot_group.setHidden(True)
        self.ui.cond_group.setHidden(True)
        self.ui.cond_in_group.setHidden(True)
        self.ui.cond_out_group.setHidden(True)
        self.ui.evap_group.setHidden(True)
        self.ui.evap_in_group.setHidden(True)
        self.ui.evap_out_group.setHidden(True)
        self.ui.cas_group.setHidden(True)
        self.ui.IHX_group.setHidden(True)
        self.ui.steam_hot_group.setHidden(True)
        self.ui.DSH_group.setHidden(True)
        self.ui.DSC_group.setHidden(True)
        self.ui.DSH_top_group.setHidden(True)
        self.ui.DSC_bot_group.setHidden(True)
        self.ui.comp_top_eff_label.setText('압축기 효율 [%]')
        self.ui.comp_bot_eff_label.setText('압축기 효율 [%]')
        self.ui.expand_top_eff_label.setText('팽창기 효율 [%]')
        self.ui.expand_bot_eff_label.setText('팽창기 효율 [%]')
        self.ui.DSH_top_label.setText('과열도 [℃]')
        self.ui.DSC_label.setText('과냉도 [℃]')
        self.ui.DSH_label.setText('과열도 [℃]')
        self.ui.DSC_bot_label.setText('과냉도 [℃]')
        
    def Bas_batch(self):
        self.ui.comp_group.setHidden(False)
        self.ui.expand_group.setHidden(False)
        self.ui.cond_group.setHidden(False)
        self.ui.cond_in_group.setHidden(False)
        self.ui.cond_out_group.setHidden(False)
        self.ui.evap_group.setHidden(False)
        self.ui.evap_in_group.setHidden(False)
        self.ui.evap_out_group.setHidden(False)
        self.ui.DSH_group.setHidden(False)
        if self.cycle_type == 'vcc':
            self.ui.DSC_group.setHidden(False)
        
        
    def IHX_batch(self):
        self.ui.comp_top_group.setHidden(False)
        self.ui.expand_bot_group.setHidden(False)
        self.ui.cond_group.setHidden(False)
        self.ui.cond_in_group.setHidden(False)
        self.ui.cond_out_group.setHidden(False)
        self.ui.evap_group.setHidden(False)
        self.ui.evap_in_group.setHidden(False)
        self.ui.evap_out_group.setHidden(False)
        self.ui.DSH_group.setHidden(False)
        if self.cycle_type == 'vcc':
            self.ui.DSC_group.setHidden(False)
        self.ui.IHX_group.setHidden(False)
        
    def Inj_batch(self):
        self.ui.comp_top_group.setHidden(False)
        self.ui.comp_bot_group.setHidden(False)
        self.ui.expand_top_group.setHidden(False)
        self.ui.expand_bot_group.setHidden(False)
        self.ui.cond_group.setHidden(False)
        self.ui.cond_in_group.setHidden(False)
        self.ui.cond_out_group.setHidden(False)
        self.ui.evap_group.setHidden(False)
        self.ui.evap_in_group.setHidden(False)
        self.ui.evap_out_group.setHidden(False)
        self.ui.DSH_group.setHidden(False)
        if self.cycle_type == 'vcc':
            self.ui.DSC_group.setHidden(False)
        self.ui.comp_top_eff_label.setText('압축기 효율 (Top) [%]')
        self.ui.comp_bot_eff_label.setText('압축기 효율 (Bot) [%]')
        self.ui.expand_top_eff_label.setText('팽창기 효율 (Top) [%]')
        self.ui.expand_bot_eff_label.setText('팽창기 효율 (Bot) [%]')
        
        
        
    def Cas_batch(self):
        self.ui.comp_top_group.setHidden(False)
        self.ui.comp_bot_group.setHidden(False)
        self.ui.expand_top_group.setHidden(False)
        self.ui.expand_bot_group.setHidden(False)
        self.ui.cond_group.setHidden(False)
        self.ui.cond_in_group.setHidden(False)
        self.ui.cond_out_group.setHidden(False)
        self.ui.evap_group.setHidden(False)
        self.ui.evap_in_group.setHidden(False)
        self.ui.evap_out_group.setHidden(False)
        self.ui.DSH_group.setHidden(False)
        if self.cycle_type == 'vcc':
            self.ui.DSC_group.setHidden(False)
        self.ui.DSH_top_group.setHidden(False)
        self.ui.DSC_bot_group.setHidden(False)
        self.ui.cas_group.setHidden(False)
        self.ui.comp_top_eff_label.setText('압축기 효율 (Top) [%]')
        self.ui.comp_bot_eff_label.setText('압축기 효율 (Bot) [%]')
        self.ui.expand_top_eff_label.setText('팽창기 효율 (Top) [%]')
        self.ui.expand_bot_eff_label.setText('팽창기 효율 (Bot) [%]')
        self.ui.DSH_top_label.setText('과열도 (Top) [℃]')
        self.ui.DSC_label.setText('과냉도 (Top) [℃]')
        self.ui.DSH_label.setText('과열도 (Bot) [℃]')
        self.ui.DSC_bot_label.setText('과냉도 (Bot) [℃]')
    
    def Process_batch(self):
        self.ui.steam_hot_group.setHidden(True)
        self.ui.cond_in_T_edit.setEnabled(True)
        self.ui.cond_in_p_edit.setEnabled(True)
        self.ui.cond_in_m_edit.setEnabled(True)
        self.ui.cond_out_T_edit.setEnabled(True)
        self.ui.cond_out_p_edit.setEnabled(True)
        self.ui.cond_fluid_list.setEnabled(True)
        self.ui.cond_row_add_btn.setEnabled(True)
        self.ui.cond_row_delete_btn.setEnabled(True)
        
    def Steam_batch(self):
        self.ui.steam_hot_group.setHidden(False)
        self.ui.Thot_target_label.setHidden(True)
        self.ui.Thot_target_edit.setHidden(True)
        self.ui.time_target_label.setHidden(True)
        self.ui.time_target_edit.setHidden(True)
        self.ui.mmakeup_label.setHidden(False)
        self.ui.mmakeup_edit.setHidden(False)
        self.ui.dT_lift_label.setText("증기온도 [℃]")
        self.ui.m_load_label.setText("증기유량 [kg/s]")
        self.ui.cond_in_T_edit.setEnabled(False)
        self.ui.cond_in_p_edit.setEnabled(False)
        self.ui.cond_in_m_edit.setEnabled(False)
        self.ui.cond_out_p_edit.setEnabled(False)
        self.ui.cond_fluid_list.setEnabled(False)
        self.ui.cond_row_add_btn.setEnabled(False)
        self.ui.cond_row_delete_btn.setEnabled(False)
        
    def Hotwater_batch(self):
        self.ui.steam_hot_group.setHidden(False)
        self.ui.Thot_target_label.setHidden(False)
        self.ui.Thot_target_edit.setHidden(False)
        self.ui.time_target_label.setHidden(False)
        self.ui.time_target_edit.setHidden(False)
        self.ui.mmakeup_label.setHidden(True)
        self.ui.mmakeup_edit.setHidden(True)
        self.ui.dT_lift_label.setText("응축기 가열능력 [℃]")
        self.ui.m_load_label.setText("급탕조용량 [kg]")
        self.ui.cond_in_T_edit.setEnabled(False)
        self.ui.cond_in_p_edit.setEnabled(False)
        self.ui.cond_in_m_edit.setEnabled(False)
        self.ui.cond_out_T_edit.setEnabled(False)
        self.ui.cond_out_p_edit.setEnabled(False)
        self.ui.cond_fluid_list.setEnabled(False)
        self.ui.cond_row_add_btn.setEnabled(False)
        self.ui.cond_row_delete_btn.setEnabled(False)
        
    def phe_fthe_judge(self):
        if self.ui.cond_phe_radio.isChecked():
            self.ui.cond_N_row_label.setHidden(True)
            self.ui.cond_N_row_edit.setHidden(True)
            self.ui.cond_T_pp_label.setText('접근온도차 [℃]')
        elif self.ui.cond_fthe_radio.isChecked():
            self.ui.cond_N_row_label.setHidden(False)
            self.ui.cond_N_row_edit.setHidden(False)
            self.ui.cond_T_pp_label.setText('LMTD [℃]')
            
        if self.ui.evap_phe_radio.isChecked():
            self.ui.evap_N_row_label.setHidden(True)
            self.ui.evap_N_row_edit.setHidden(True)
            self.ui.evap_T_pp_label.setText('접근온도차 [℃]')
        elif self.ui.evap_fthe_radio.isChecked():
            self.ui.evap_N_row_label.setHidden(False)
            self.ui.evap_N_row_edit.setHidden(False)
            self.ui.evap_T_pp_label.setText('LMTD [℃]')
            
        if self.ui.cas_phe_radio.isChecked():
            self.ui.cas_N_row_label.setHidden(True)
            self.ui.cas_N_row_edit.setHidden(True)
            self.ui.cas_T_pp_label.setText('접근온도차 [℃]')
        elif self.ui.cas_fthe_radio.isChecked():
            self.ui.cas_N_row_label.setHidden(False)
            self.ui.cas_N_row_edit.setHidden(False)
            self.ui.cas_T_pp_label.setText('LMTD [℃]')
    
    def LimitProcessInput(self):    
        if self.ui.cond_out_T_edit.text() != '' and self.ui.cond_in_m_edit.text() != '' and self.ui.evap_in_T_edit.text() != '' and self.ui.evap_out_T_edit.text() != '' and self.ui.evap_in_m_edit.text() != '':
            self.ui.cond_in_T_edit.setEnabled(False)
        elif self.ui.cond_in_T_edit.text() != '' and self.ui.cond_in_m_edit.text() != '' and self.ui.evap_in_T_edit.text() != '' and self.ui.evap_out_T_edit.text() != '' and self.ui.evap_in_m_edit.text() != '':
            self.ui.cond_out_T_edit.setEnabled(False)
        elif self.ui.cond_in_T_edit.text() != '' and self.ui.cond_out_T_edit.text() != '' and self.ui.evap_in_T_edit.text() != '' and self.ui.evap_out_T_edit.text() != '' and self.ui.evap_in_m_edit.text() != '':
            self.ui.cond_in_m_edit.setEnabled(False)
        elif self.ui.cond_in_T_edit.text() != '' and self.ui.cond_out_T_edit.text() != '' and self.ui.cond_in_m_edit.text() != '' and self.ui.evap_out_T_edit.text() != '' and self.ui.evap_in_m_edit.text() != '':
            self.ui.evap_in_T_edit.setEnabled(False)
        elif self.ui.cond_in_T_edit.text() != '' and self.ui.cond_out_T_edit.text() != '' and self.ui.cond_in_m_edit.text() != '' and self.ui.evap_in_T_edit.text() != '' and self.ui.evap_in_m_edit.text() != '':            
            self.ui.evap_out_T_edit.setEnabled(False)
        elif self.ui.cond_in_T_edit.text() != '' and self.ui.cond_out_T_edit.text() != '' and self.ui.cond_in_m_edit.text() != '' and self.ui.evap_in_T_edit.text() != '' and self.ui.evap_out_T_edit.text() != '':
            self.ui.evap_in_m_edit.setEnabled(False)
        else:
            self.ui.cond_in_T_edit.setEnabled(True)
            self.ui.cond_out_T_edit.setEnabled(True)
            self.ui.cond_in_m_edit.setEnabled(True)
            self.ui.evap_in_T_edit.setEnabled(True)
            self.ui.evap_out_T_edit.setEnabled(True)
            self.ui.evap_in_m_edit.setEnabled(True)
    
    def InputsEnteredAction(self):
        
        if self.layout_type == 'cas':
            self.inputs_t = Settings()
            self.inputs_b = Settings()
            self.outputs_t = Settings()
            self.outputs_b = Settings()
            
            self.inputs_b.cycle = 'vcc'
            self.inputs_b.second = 'process'
            self.inputs_t.layout = 'bas'
            self.inputs_b.layout = 'bas'
            
            if self.process_type == 'steam':
                self.inputs_t.second = 'steam'
                self.ui.mmakeup_edit.setText(self.ui.m_load_edit.text())
                if self.ui.dT_lift_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '목표 증기 온도를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs_t.T_steam = float(self.ui.dT_lift_edit.text())+273.15
                if self.ui.m_load_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '증기 유량을 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs_t.m_steam = float(self.ui.m_load_edit.text())
                    
                self.inputs_t.m_makeup = self.inputs_t.m_steam
            elif self.process_type == 'hotwater':
                self.inputs_t.second = 'hotwater'
                if self.ui.Thot_target_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '목표 급탕 온도를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs_t.T_target = float(self.ui.Thot_target_edit.text())+273.15
                if self.time_target_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '급탕조 가열 시간을 입력하세요', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs_t.time_target = float(self.ui.time_target_edit.text())*60.0
                if self.dT_lift_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '응축기 내에서 가열하고자하는 상승온도를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs_t.dT_lift = float(self.ui.dT_lift_edit.text())
                if self.m_load_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '급탕조 용량을 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs_t.M_load = float(self.ui.m_load_edit.text())
            else:
                self.inputs_t.second = 'process'
                
            if self.cycle_type == 'scc':
                self.inputs_t.cycle = 'scc'
            else:
                self.inputs_t.cycle = 'vcc'
            
            if self.ui.DSH_top_edit.text() == '':
                QMessageBox.warning(self, '입력문 검토', '과열도를 입력하세요. (Top)', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                self.inputs_t.DSH = float(self.ui.DSH_top_edit.text())
            if self.ui.DSC_edit.text() == ''  and self.cycle_type == 'vcc':
                QMessageBox.warning(self, '입력문 검토', '과냉도를 입력하세요. (Top)', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                if self.cycle_type == 'scc':
                    self.inputs_t.DSC = (self.Tcrit_top - self.nbp_top)/5
                else:
                    self.inputs_t.DSC = float(self.ui.DSC_edit.text())
            if self.ui.DSH_edit.text() == '':
                QMessageBox.warning(self, '입력문 검토', '과열도를 입력하세요. (Bottom)', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                self.inputs_b.DSH = float(self.ui.DSH_edit.text())
            if self.ui.DSC_bot_edit.text() == '':
                QMessageBox.warning(self, '입력문 검토', '과냉도를 입력하세요 (Bottom).', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                self.inputs_b.DSC = float(self.ui.DSC_bot_edit.text())
                
            self.inputs_t.cond_N_element = 30
            self.inputs_t.evap_N_element = 30
            self.inputs_b.cond_N_element = 30
            self.inputs_b.evap_N_element = 30
            
            if self.ui.cond_dp_edit.text() == '':
                QMessageBox.warning(self, '입력문 검토', '응축기 압력강하를 입력하세요.', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                self.inputs_t.cond_dp = float(self.ui.cond_dp_edit.text())*1000.0
            if self.ui.cas_cold_dp_edit.text() == '':
                QMessageBox.warning(self, '입력문 검토', '캐스케이드 열교환기 저온측 압력강하를 입력하세요.', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                self.inputs_t.evap_dp = float(self.ui.cas_cold_dp_edit.text())*1000.0
            if self.ui.cas_hot_dp_edit.text() == '':
                QMessageBox.warning(self, '입력문 검토', '캐스케이드 열교환기 고온측 압력강하를 입력하세요.', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                self.inputs_b.cond_dp = float(self.ui.cas_hot_dp_edit.text())*1000.0
            if self.ui.evap_dp_edit.text() == '':
                QMessageBox.warning(self, '입력문 검토', '증발기 압력강하를 입력하세요.', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:                
                self.inputs_b.evap_dp = float(self.ui.evap_dp_edit.text())*1000.0
            
            if self.ui.cond_phe_radio.isChecked():
                if self.ui.cond_T_pp_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '판형 응축기 접근온도를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs_t.cond_T_pp = float(self.ui.cond_T_pp_edit.text())
            elif self.ui.cond_fthe_radio.isChecked():
                if self.ui.cond_T_pp_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '핀튜브형 응축기 LMTD를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs_t.cond_T_lm = float(self.ui.cond_T_pp_edit.text())
                if self.ui.cond_N_row_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '핀튜브형 응축기 전열관 열 개수를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs_t.cond_N_row = int(self.ui.cond_N_row_edit.text())
            
            if self.ui.cas_phe_radio.isChecked():
                if self.ui.cas_T_pp_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '판형 캐스케이드 열교환기 접근온도를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs_t.evap_T_pp = float(self.ui.cas_T_pp_edit.text())
                    self.inputs_b.cond_T_pp = float(self.ui.cas_T_pp_edit.text())
            elif self.ui.cond_fthe_radio.isChecked():
                if self.ui.cas_T_pp_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '핀튜브형 캐스케이드 열교환기 LMTD를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs_t.cond_T_lm = float(self.ui.cas_T_pp_edit.text())
                    self.inputs_b.evap_T_lm = float(self.ui.cas_T_pp_edit.text())
                if self.ui.cas_N_row_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '핀튜브형 캐스케이드 열교환기 전열관 열 개수를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:    
                    self.inputs_t.cond_N_row = int(self.ui.cas_N_row_edit.text())
                    self.inputs_b.evap_N_row = int(self.ui.cas_N_row_edit.text())
            
            if self.ui.evap_phe_radio.isChecked():
                if self.ui.evap_T_pp_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '판형 증발기 접근온도를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs_b.evap_T_pp = float(self.ui.evap_T_pp_edit.text())
            elif self.ui.evap_fthe_radio.isChecked():
                if self.ui.evap_T_pp_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '핀튜브형 증발기 LMTD를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs_b.evap_T_lm = float(self.ui.evap_T_pp_edit.text())
                if self.ui.evap_N_row_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '핀튜브형 증발기 전열관 열 개수를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs_b.evap_N_row = int(self.ui.evap_N_row_edit.text())
                    
            if self.ui.comp_top_eff_edit.text() == '':
                QMessageBox.warning(self, '입력문 검토', '압축기 등엔트로피 효율을 입력하세요 (Top).', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                self.inputs_t.comp_eff = float(self.ui.comp_top_eff_edit.text())/100.0
            if self.ui.comp_bot_eff_edit.text() == '':
                QMessageBox.warning(self, '입력문 검토', '압축기 등엔트로피 효율을 입력하세요 (Bottom).', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                self.inputs_b.comp_eff = float(self.ui.comp_bot_eff_edit.text())/100.0
            if self.ui.expand_top_eff_edit.text() == '':
                QMessageBox.warning(self, '입력문 검토', '팽창기 등엔트로피 효율을 입력하세요 (Top).', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                self.inputs_t.expand_eff = float(self.ui.expand_top_eff_edit.text())/100.0
            if self.ui.expand_bot_eff_edit.text() == '':
                QMessageBox.warning(self, '입력문 검토', '팽창기 등엔트로피 효율을 입력하세요 (Bottom).', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                self.inputs_b.expand_eff = float(self.ui.expand_bot_eff_edit.text())/100.0
        else:
            self.inputs = Settings()
            self.outputs = Settings()
            
            if self.process_type == 'steam':
                self.inputs.second = 'steam'
                self.mmakeup_edit.setText(self.ui.m_load_edit.text())
                self.inputs.T_steam = float(self.ui.dT_lift_edit.text())+273.15
                self.inputs.m_steam = float(self.ui.m_load_edit.text())
                self.inputs.m_makeup = self.inputs.m_steam
            elif self.process_type == 'hotwater':
                self.inputs.second = 'hotwater'
                self.inputs.T_target = float(self.ui.Thot_target_edit.text())+273.15
                self.inputs.time_target = float(self.ui.time_target_edit.text())
                self.inputs.dT_lift = float(self.ui.dT_lift_edit.text())
                self.inputs.M_load = float(self.ui.m_load_edit.text())
            else:
                self.inputs.second = 'process'
                
            if self.cycle_type == 'scc':
                self.inputs.cycle = 'scc'
            else:
                self.inputs.cycle = 'vcc'
            
            if self.ui.DSH_edit.text() == '':
                QMessageBox.warning(self, '입력문 검토', '과열도를 입력하세요.', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                self.inputs.DSH = float(self.ui.DSH_edit.text())
            if self.ui.DSC_edit.text() == '' and self.cycle_type == 'vcc':
                 QMessageBox.warning(self, '입력문 검토', '과냉도를 입력하세요.', QMessageBox.Yes)
                 self.message_chk = self.message_chk+1
            else:
                if self.cycle_type == 'scc':
                    self.inputs.DSC = (self.Tcrit_bottom - self.nbp_bottom)/5
                else:
                    self.inputs.DSC = float(self.ui.DSC_edit.text())
            if self.ui.cond_dp_edit.text() == '':
                QMessageBox.warning(self, '입력문 검토', '응축기 압력강하를 입력하세요.', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                self.inputs.cond_dp = float(self.ui.cond_dp_edit.text())*1000.0
            if self.ui.evap_dp_edit.text() == '':
                QMessageBox.warning(self, '입력문 검토', '증발기 압력강하를 입력하세요.', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                self.inputs.evap_dp = float(self.ui.evap_dp_edit.text())*1000.0
            
            self.inputs.cond_N_element = 30
            self.inputs.evap_N_element = 30
            if self.ui.cond_phe_radio.isChecked():
                if self.ui.cond_T_pp_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '판형 응축기 접근온도를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.cond_T_pp = float(self.ui.cond_T_pp_edit.text())
            elif self.ui.cond_fthe_radio.isChecked():
                if self.ui.cond_T_pp_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '핀튜브형 응축기 LMTD를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.cond_T_lm = float(self.ui.cond_T_pp_edit.text())
                if self.ui.cond_N_row_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '핀튜브형 응축기 전열관 열 개수를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.cond_N_row = int(self.ui.cond_N_row_edit.text())
            if self.ui.evap_phe_radio.isChecked():
                if self.ui.evap_T_pp_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '판형 증발기 접근온도를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.evap_T_pp = float(self.ui.evap_T_pp_edit.text())
            elif self.ui.evap_fthe_radio.isChecked():
                if self.ui.evap_T_pp_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '핀튜브형 증발기 LMTD를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.evap_T_lm = float(self.ui.evap_T_pp_edit.text())
                if self.ui.evap_N_row_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '핀튜브형 증발기 전열관 열 개수를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.evap_N_row = int(self.ui.evap_N_row_edit.text())
            
            if self.layout_type == 'bas':
                self.inputs.layout = 'bas'
                if self.ui.comp_eff_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '압축기 등엔트로피 효율을 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.comp_eff = float(self.ui.comp_eff_edit.text())/100.0
                if self.ui.motor_eff_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '모터 효율을 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.mech_eff = float(self.ui.motor_eff_edit.text())/100.0
                if self.ui.expand_eff_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '팽창기 등엔트로피 효율을 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.expand_eff = float(self.ui.expand_eff_edit.text())/100.0
            elif self.layout_type == 'ihx':
                self.inputs.layout = 'ihx'
                if self.ui.comp_top_eff_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '압축기 등엔트로피 효율을 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.comp_eff = float(self.ui.comp_top_eff_edit.text())/100.0
                if self.ui.expand_bot_eff_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '팽창기 등엔트로피 효율을 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.expand_eff = float(self.ui.expand_bot_eff_edit.text())/100.0
                if self.ui.IHX_eff_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '내부열교환기 유용도를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.ihx_eff = float(self.ui.IHX_eff_edit.text())/100.0
                if self.ui.IHX_hot_dp_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '내부열교환기 고온측 압력강하를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.ihx_hot_dp = float(self.ui.IHX_hot_dp_edit.text())*1000.0
                if self.ui.IHX_cold_dp_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '내부열교환기 저온측 압력강하를 입력하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.ihx_cold_dp = float(self.ui.IHX_cold_dp_edit.text())*1000.0
            elif self.layout_type == 'inj':
                self.inputs.layout = 'inj'
                if self.ui.comp_top_eff_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '압축기 등엔트로피 효율을 입력하세요. (Top)', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.comp_top_eff = float(self.ui.comp_top_eff_edit.text())/100.0
                if self.ui.comp_bot_eff_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '압축기 등엔트로피 효율을 입력하세요. (Bottom)', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.comp_eff = float(self.ui.comp_bot_eff_edit.text())/100.0
                if self.ui.expand_top_eff_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '팽창기 등엔트로피 효율을 입력하세요. (Top)', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.expand_eff = float(self.ui.expand_top_eff_edit.text())/100.0
                if self.ui.expand_bot_eff_edit.text() == '':
                    QMessageBox.warning(self, '입력문 검토', '팽창기 등엔트로피 효율을 입력하세요. (Bottom)', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.inputs.expand_bot_eff = float(self.ui.expand_bot_eff_edit.text())/100.0
            
    def ProcessEnteredAction(self):
        self.CondFluidRatio()
        self.EvapFluidRatio()
        
        self.InEvap = ProcessFluid(Y=self.evapY)
        self.OutEvap = ProcessFluid(Y=self.evapY)
        self.InCond = ProcessFluid(Y=self.condY)
        self.OutCond = ProcessFluid(Y=self.condY)
        
        if self.ui.evap_in_T_edit.text() == '':
            self.InEvap.T = 0.0
        else:
            self.InEvap.T = float(self.ui.evap_in_T_edit.text())+273.15    
        if self.ui.evap_in_p_edit.text() == '':
            self.InEvap.p = 0.0
        else:
            self.InEvap.p = float(self.ui.evap_in_p_edit.text())*1.0e5
        if self.ui.evap_in_m_edit.text() == '':
            self.InEvap.m = 0.0
        else:
            self.InEvap.m = float(self.ui.evap_in_m_edit.text())
        
        if self.ui.evap_out_T_edit.text() == '':
            self.OutEvap.T = 0.0
        else:
            self.OutEvap.T = float(self.ui.evap_out_T_edit.text())+273.15    
        if self.ui.evap_out_p_edit.text() == '':
            self.OutEvap.p = 0.0
        else:
            self.OutEvap.p = float(self.ui.evap_out_p_edit.text())*1.0e5
        
        self.OutEvap.m = self.InEvap.m
        
        if self.process_type == 'process':
            if self.ui.cond_in_T_edit.text() == '':
                self.InCond.T = 0.0
            else:    
                self.InCond.T = float(self.ui.cond_in_T_edit.text())+273.15
            if self.ui.cond_in_p_edit.text() == '':
                self.InCond.p = 0.0
            else:
                self.InCond.p = float(self.ui.cond_in_p_edit.text())*1.0e5
            if self.ui.cond_in_m_edit.text() == '':
                self.InCond.m = 0.0
            else:
                self.InCond.m = float(self.ui.cond_in_m_edit.text())    
            if self.ui.cond_out_T_edit.text() == '':
                self.OutCond.T = 0.0
            else:
                self.OutCond.T = float(self.ui.cond_out_T_edit.text())+273.15 
            if self.ui.cond_out_p_edit.text() == '':
                self.OutCond.p = 0.0
            else:
                self.OutCond.p = float(self.ui.cond_out_p_edit.text())*1.0e5
            
            self.OutCond.m = self.InCond.m
        elif self.process_type == 'steam':
            if self.ui.cond_out_T_edit.text() == '':
                QMessageBox.warning(self, '입력문 검토', '응축기 출구 온도를 입력하세요', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                if self.layout_type == 'cas':
                    steamT = self.inputs_t.T_steam
                else:
                    steamT = self.inputs.T_steam
                        
                if  steamT < float(self.ui.cond_out_T_edit.text()):
                    QMessageBox.warning(self, '입력문 검토', '응축기 출구 온도는 타겟 증기 온도보다 높게 설정해야합니다.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                elif steamT < 100.0:
                    QMessageBox.warning(self, '입력문 검토', '증기 온도는 100℃보다 높게 설정해야합니다.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
                else:
                    self.OutCond.T = float(self.ui.cond_out_T_edit.text())+273.15
        
        elif self.process_type == 'hotwater':
            if float(self.ui.Thot_target_edit.text()) > 100.0:
                QMessageBox.warning(self, '입력문 검토', '급탕온도는 100℃보다 낮게 설정해야합니다.', QMessageBox.Yes)
                self.message_chk = self.message_chk+1

        if self.layout_type == 'cas':
            if self.ui.ref_list_t.currentText() == '':
                QMessageBox.warning(self, '입력문 검토', '냉매 종류를 입력하세요 (Top)', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                self.inputs_t.Y = {self.Y_t:1.0,}
            if self.ref_list_b.currentText() == '':
                QMessageBox.warning(self, '입력문 검토', '냉매 종류를 입력하세요 (Bottom)', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                self.inputs_b.Y = {self.Y_b:1.0,}
            
            if self.message_chk == 0:
                self.vchp_cascade = VCHP_cascade(self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.inputs_t, self.inputs_b)
                (self.InCond, self.OutCond, self.InEvap, self.OutEvap, no_input) = self.vchp_cascade.Input_Processing(self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.inputs_t)

        else:
            if self.ui.ref_list_b.currentText() == '':
                QMessageBox.warning(self, '입력문 검토', '냉매 종류를 입력하세요', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                self.inputs.Y = {self.Y_b:1.0,}
            
            if self.message_chk == 0:
                self.vchp = VCHP(self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.inputs)
                (self.InCond, self.OutCond, self.InEvap, self.OutEvap, no_input) = self.vchp.Input_Processing(self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.inputs)
                
        if self.message_chk == 0:
            self.no_input = no_input
            if no_input == 'InEvapT':
                if self.nbp_bottom > self.OutEvap.T - float(self.ui.evap_T_pp_edit.text()):
                    QMessageBox.warning(self, '입력문 검토', '냉매의 NBP가 공정 온도 보다 높습니다. 다른 냉매를 선택하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
            else:
                if self.nbp_bottom > self.InEvap.T - float(self.ui.evap_T_pp_edit.text()):
                    QMessageBox.warning(self, '입력문 검토', '냉매의 NBP가 공정 온도 보다 높습니다. 다른 냉매를 선택하세요.', QMessageBox.Yes)
                    self.message_chk = self.message_chk+1
            
            if self.layout_type == 'cas':
                Tcrit = self.Tcrit_top
            else:
                Tcrit = self.Tcrit_bottom
            
            if self.cycle_type == 'vcc':                
                if no_input == 'OutCondT':
                    if Tcrit < self.InCond.T + float(self.ui.cond_T_pp_edit.text()):
                        QMessageBox.warning(self, '입력문 검토', '아임계 사이클은 공정 온도가 임계온도보다 낮아야합니다. 다른 냉매를 선택하세요.', QMessageBox.Yes)
                        self.message_chk = self.message_chk+1
                else:
                    if Tcrit < self.OutCond.T + float(self.ui.cond_T_pp_edit.text()):
                        QMessageBox.warning(self, '입력문 검토', '아임계 사이클은 공정 온도가 임계온도보다 낮아야합니다. 다른 냉매를 선택하세요.', QMessageBox.Yes)
                        self.message_chk = self.message_chk+1
            else:
                if no_input == 'OutCondT':
                    if Tcrit > self.InCond.T + float(self.ui.cond_T_pp_edit.text()):
                        QMessageBox.warning(self, '입력문 검토', '초월임계 사이클은 공정 온도가 임계온도보다 높아야합니다. 다른 냉매를 선택하세요.', QMessageBox.Yes)
                        self.message_chk = self.message_chk+1
                else:
                    if Tcrit > self.OutCond.T + float(self.ui.cond_T_pp_edit.text()):
                        QMessageBox.warning(self, '입력문 검토', '초월임계 사이클은 공정 온도가 임계온도보다 높아야합니다. 다른 냉매를 선택하세요.', QMessageBox.Yes)
                        self.message_chk = self.message_chk+1
        
        if self.message_chk == 0:
            if no_input == 'Overdefine':
                QMessageBox.warning(self, '입력문 검토', 'OverDefine: 고온 입구 온도, 고온 출구 온도, 고온 유량, 저온 입구 온도, 저온 출구 온도, 저온 유량 중 하나를 미지수로 설정하세요. (5개 입력)', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            elif no_input == 'Underdefine':
                QMessageBox.warning(self, '입력문 검토', 'UnderDefine: 미지수가 너무 적게 입력됐습니다. (5개 입력)', QMessageBox.Yes)
                self.message_chk = self.message_chk+1
            else:
                if no_input == 'OutCondT' or no_input == 'InCondT':
                    if self.InEvap.T - self.OutEvap.T < 0:
                        QMessageBox.warning(self, '입력문 검토', '증발기 출구 온도를 입구 온도보다 낮게 설정하세요.', QMessageBox.Yes)
                        self.message_chk = self.message_chk+1
                    else:
                        self.message_chk = 0
                                                
                elif no_input == 'Condm' or no_input == 'Evapm':
                    if self.OutCond.T - self.InCond.T > 0 and self.InEvap.T - self.OutEvap.T > 0:
                        self.message_chk = 0
                    else:
                        if self.OutCond.T - self.InCond.T < 0:
                            QMessageBox.warning(self, '입력문 검토', '응축기 출구 온도를 입구 온도보다 높게 설정하세요.', QMessageBox.Yes)
                        elif self.InEvap.T - self.OutEvap.T < 0:
                            QMessageBox.warning(self, '입력문 검토', '증발기 출구 온도를 입구 온도보다 낮게 설정하세요.', QMessageBox.Yes)
                        self.message_chk = self.message_chk+1
                            
                elif no_input == 'OutEvapT' or no_input == 'InEvapT':
                    if self.OutCond.T - self.InCond.T < 0:
                        QMessageBox.warning(self, '입력문 검토', '응축기 출구 온도를 입구 온도보다 높게 설정하세요.', QMessageBox.Yes)
                        self.message_chk = self.message_chk+1
                    else:
                        self.message_chk = 0
                        
                    
        if self.message_chk == 0:
            if self.process_type == 'steam':
                self.ui.cond_in_T_edit.setText(str(round(self.InCond.T-273.15,1)))
                self.ui.cond_in_p_edit.setText(str(round(self.InCond.p/1.0e5,1)))
                self.ui.cond_in_m_edit.setText(str(round(self.InCond.m,2)))
                self.ui.cond_out_p_edit.setText(str(round(self.OutCond.p/1.0e5,1)))
                self.ui.cond_in_T_edit.setEnabled(False)
                self.ui.cond_in_p_edit.setEnabled(False)
                self.ui.cond_in_m_edit.setEnabled(False)
                self.ui.cond_out_p_edit.setEnabled(False)
            elif self.process_type == 'hotwater':
                self.ui.cond_in_T_edit.setText(str(round(self.InCond.T-273.15,1)))
                self.ui.cond_in_p_edit.setText(str(round(self.InCond.p/1.0e5,1)))
                self.ui.cond_in_m_edit.setText(str(round(self.InCond.m,2)))
                self.ui.cond_out_T_edit.setText(str(round(self.OutCond.T-273.15,1)))
                self.ui.cond_out_p_edit.setText(str(round(self.OutCond.p/1.0e5,1)))
                self.ui.cond_in_T_edit.setEnabled(False)
                self.ui.cond_in_p_edit.setEnabled(False)
                self.ui.cond_in_m_edit.setEnabled(False)
                self.ui.cond_out_T_edit.setEnabled(False)
                self.ui.cond_out_p_edit.setEnabled(False)
                
            QMessageBox.information(self, '입력문 검토 완료!', '입력문이 적절하게 입력됐습니다.', QMessageBox.Yes)
            self.ui.Calcstart_btn.setEnabled(True)
            
    def Calcstart_action(self):
      ph_file = "Ph_diagram"
      ts_file = "Ts_diagram"
      try:
        if self.layout_type == 'cas':
          self.outputs_t = Outputs()
          self.outputs_b = Outputs()
          
          self.InCond_REF_t = ProcessFluid(Y=self.inputs_t.Y, m = 0.0, T = 0.0, p = 0.0, q = 0.0, h = 0.0, s = 0.0, Cp = 0.0)
          self.OutCond_REF_t = ProcessFluid(Y=self.inputs_t.Y, m = 0.0, T = 0.0, p = 0.0, q = 0.0, h = 0.0, s = 0.0, Cp = 0.0)
          self.InEvap_REF_t = ProcessFluid(Y=self.inputs_t.Y, m = 0.0, T = 0.0, p = 0.0, q = 0.0, h = 0.0, s = 0.0, Cp = 0.0)
          self.OutEvap_REF_t = ProcessFluid(Y=self.inputs_t.Y, m = 0.0, T = 0.0, p = 0.0, q = 0.0, h = 0.0, s = 0.0, Cp = 0.0)
          self.InCond_REF_b = ProcessFluid(Y=self.inputs_b.Y, m = 0.0, T = 0.0, p = 0.0, q = 0.0, h = 0.0, s = 0.0, Cp = 0.0)
          self.OutCond_REF_b = ProcessFluid(Y=self.inputs_b.Y, m = 0.0, T = 0.0, p = 0.0, q = 0.0, h = 0.0, s = 0.0, Cp = 0.0)
          self.InEvap_REF_b = ProcessFluid(Y=self.inputs_b.Y, m = 0.0, T = 0.0, p = 0.0, q = 0.0, h = 0.0, s = 0.0, Cp = 0.0)
          self.OutEvap_REF_b = ProcessFluid(Y=self.inputs_b.Y, m = 0.0, T = 0.0, p = 0.0, q = 0.0, h = 0.0, s = 0.0, Cp = 0.0)
          
          p_crit_t = PropsSI('PCRIT','',0,'',0,list(self.inputs_t.Y.keys())[0])
          T_crit_t = PropsSI('TCRIT','',0,'',0,list(self.inputs_t.Y.keys())[0])
          p_crit_b = PropsSI('PCRIT','',0,'',0,list(self.inputs_b.Y.keys())[0])
          T_crit_b = PropsSI('TCRIT','',0,'',0,list(self.inputs_b.Y.keys())[0])
          
          self.InCond_REF_t.p_crit = p_crit_t
          self.OutCond_REF_t.p_crit = p_crit_t
          self.InEvap_REF_t.p_crit = p_crit_t
          self.OutEvap_REF_t.p_crit = p_crit_t
          
          self.InCond_REF_t.T_crit = T_crit_t
          self.OutCond_REF_t.T_crit = T_crit_t
          self.InEvap_REF_t.T_crit = T_crit_t
          self.OutEvap_REF_t.T_crit = T_crit_t
          
          self.InCond_REF_b.p_crit = p_crit_b
          self.OutCond_REF_b.p_crit = p_crit_b
          self.InEvap_REF_b.p_crit = p_crit_b
          self.OutEvap_REF_b.p_crit = p_crit_b
          
          self.InCond_REF_b.T_crit = T_crit_b
          self.OutCond_REF_b.T_crit = T_crit_b
          self.InEvap_REF_b.T_crit = T_crit_b
          self.OutEvap_REF_b.T_crit = T_crit_b
          
          
          cond_t_ph = 0
          evap_b_ph = 0
          (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF_t, self.OutCond_REF_t, self.InEvap_REF_t, self.OutEvap_REF_t, self.InCond_REF_b, self.OutCond_REF_b, self.InEvap_REF_b, self.OutEvap_REF_b, self.outputs_t, self.outputs_b) = self.vchp_cascade.Cascade_solver(self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF_t, self.OutCond_REF_t, self.InEvap_REF_t, self.OutEvap_REF_t, self.InCond_REF_b, self.OutCond_REF_b, self.InEvap_REF_b, self.OutEvap_REF_b, self.inputs_t, self.inputs_b, self.outputs_t, self.outputs_b, self.no_input, cond_t_ph, evap_b_ph)
          self.vchp_cascade.Plot_diagram(self.InCond_REF_t, self.OutCond_REF_t, self.InEvap_REF_t, self.OutEvap_REF_t, self.inputs_t, self.outputs_t, self.InCond_REF_b, self.OutCond_REF_b, self.InEvap_REF_b, self.OutEvap_REF_b, self.inputs_b, self.outputs_b)
        else:
          self.outputs = Outputs()
          
          self.InCond_REF = ProcessFluid(Y=self.inputs.Y, m = 0.0, T = 0.0, p = 0.0, q = 0.0, h = 0.0, s = 0.0, Cp = 0.0)
          self.OutCond_REF = ProcessFluid(Y=self.inputs.Y, m = 0.0, T = 0.0, p = 0.0, q = 0.0, h = 0.0, s = 0.0, Cp = 0.0)
          self.InEvap_REF = ProcessFluid(Y=self.inputs.Y, m = 0.0, T = 0.0, p = 0.0, q = 0.0, h = 0.0, s = 0.0, Cp = 0.0)
          self.OutEvap_REF = ProcessFluid(Y=self.inputs.Y, m = 0.0, T = 0.0, p = 0.0, q = 0.0, h = 0.0, s = 0.0, Cp = 0.0)
          
          p_crit = PropsSI('PCRIT','',0,'',0, list(self.inputs.Y.keys())[0])
          T_crit = PropsSI('TCRIT','',0,'',0, list(self.inputs.Y.keys())[0])
          
          self.InCond_REF.p_crit = p_crit
          self.OutCond_REF.p_crit = p_crit
          self.InEvap_REF.p_crit = p_crit
          self.OutEvap_REF.p_crit = p_crit
          
          self.InCond_REF.T_crit = T_crit
          self.OutCond_REF.T_crit = T_crit
          self.InEvap_REF.T_crit = T_crit
          self.OutEvap_REF.T_crit = T_crit
          
          evap_ph = 0
          cond_ph = 0
          if self.layout_type == 'inj':    
              (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, self.outputs) = self.vchp.Injection_Solver(self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, self.inputs, self.outputs, self.no_input, cond_ph, evap_ph)
          else:
              (self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, self.outputs) = self.vchp.Cycle_Solver(self.InCond, self.OutCond, self.InEvap, self.OutEvap, self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, self.inputs, self.outputs, self.no_input, cond_ph, evap_ph)
      
          self.vchp.Plot_diagram(self.InCond_REF, self.OutCond_REF, self.InEvap_REF, self.OutEvap_REF, self.inputs, self.outputs, ts_file, ph_file, 0.999)
            
          self.MoveToResultsTab()
          self.ui.valve_recommand.setEnabled(True)
          self.ui.compressor_recommand.setEnabled(True)
          self.AllHidden_ResultTab()
          if self.layout_type == 'bas':
              self.Bas_batch_result()
              self.ui.layout_fig_tab3.setPixmap(QPixmap(resource_path("Figs/Basic_result.png")).scaledToHeight(500))
          elif self.layout_type == 'ihx':
              self.IHX_batch_result()
              self.ui.layout_fig_tab3.setPixmap(QPixmap(resource_path("Figs/IHX_result.png")).scaledToHeight(500))
          elif self.layout_type == 'inj':
              self.Inj_batch_result()
              self.ui.layout_fig_tab3.setPixmap(QPixmap(resource_path("Figs/Injection_result.png")).scaledToHeight(500))
          elif self.layout_type == 'cas':
              self.Cas_batch_result()
              self.ui.layout_fig_tab3.setPixmap(QPixmap(resource_path("Figs/Cascade_result.png")).scaledToHeight(500))
              
          if self.process_type == 'process':
              self.ui.process_fig_tab3.setPixmap(QPixmap(resource_path("Figs/Process.png")).scaledToWidth(300))
          elif self.process_type == 'steam':
              self.ui.process_fig_tab3.setPixmap(QPixmap(resource_path("Figs/Steam.png")).scaledToWidth(300))
          elif self.process_type == 'hotwater':
              self.ui.process_fig_tab3.setPixmap(QPixmap(resource_path("Figs/Hotwater.png")).scaledToWidth(300))
              
          self.ui.ph_diagram.setPixmap(QPixmap(resource_path("Figs/"+ph_file+".png")).scaledToWidth(400))
          self.ui.ts_diagram.setPixmap(QPixmap(resource_path("Figs/"+ts_file+".png")).scaledToWidth(400))
      except:
          import traceback
          QMessageBox.warning(self, '계산 error', '입력문을 재검토하세요.', QMessageBox.Yes)
          QMessageBox.warning(self, '계산 error', traceback.format_exc(), QMessageBox.Yes)
          self.message_chk = self.message_chk+1
    
    def AllHidden_ResultTab(self):
        self.ui.REF_table.clearContents()
        self.ui.expand_group_2.setHidden(True)
        self.ui.expand_top_group_2.setHidden(True)
        self.ui.expand_bot_group_2.setHidden(True)
        self.ui.comp_group_2.setHidden(True)
        self.ui.comp_top_group_2.setHidden(True)
        self.ui.comp_bot_group_2.setHidden(True)
        self.ui.cond_group_2.setHidden(True)
        self.ui.evap_group_2.setHidden(True)
        self.ui.cas_group_2.setHidden(True)
        self.ui.IHX_group_2.setHidden(True)
        self.ui.flash_tank_group.setHidden(True)
        self.ui.COP_bot_group.setHidden(True)
        self.ui.COP_top_group.setHidden(True)
        self.ui.cond_in_group_2.setHidden(True)
        self.ui.cond_out_group_2.setHidden(True)
        self.ui.evap_in_group_2.setHidden(True)
        self.ui.evap_out_group_2.setHidden(True)
        
        
        self.ui.comp_top_eff_label.setText('압축기 출력 [kW]')
        self.ui.comp_bot_eff_label.setText('압축기 출력 [kW]')
        self.ui.expand_top_eff_label.setText('팽창기 출력 [kW]')
        self.ui.expand_bot_eff_label.setText('팽창기 출력 [kW]')
        
        
    def Bas_batch_result(self):
        self.ui.comp_group_2.setHidden(False)
        self.ui.comp_eff_edit_2.setText(str(round(self.outputs.Wcomp/1000.0,2)))
        self.ui.expand_group_2.setHidden(False)
        self.ui.expand_eff_edit_2.setText(str(round(self.outputs.Wexpand/1000.0,2)))
        self.ui.cond_group_2.setHidden(False)
        self.ui.condQ_edit.setText(str(round(self.OutCond.q/1000.0,2)))
        self.ui.cond_in_group_2.setHidden(False)
        self.ui.cond_in_T_edit_2.setText(str(round(self.InCond.T-273.15,2)))
        self.ui.cond_in_p_edit_2.setText(str(round(self.InCond.p/1.0e5,2)))
        self.ui.cond_in_m_edit_2.setText(str(round(self.InCond.m,2)))
        self.ui.cond_out_group_2.setHidden(False)
        self.ui.cond_out_T_edit_2.setText(str(round(self.OutCond.T-273.15,2)))
        self.ui.cond_out_p_edit_2.setText(str(round(self.OutCond.p/1.0e5,2)))
        self.ui.evap_group_2.setHidden(False)
        self.ui.evapQ_edit.setText(str(round(-self.OutEvap.q/1000.0,2)))
        self.ui.evap_in_group_2.setHidden(False)
        self.ui.evap_in_T_edit_2.setText(str(round(self.InEvap.T-273.15,2)))
        self.ui.evap_in_p_edit_2.setText(str(round(self.InEvap.p/1.0e5,2)))
        self.ui.evap_in_m_edit_2.setText(str(round(self.InEvap.m,2)))
        self.ui.evap_out_group_2.setHidden(False)
        self.ui.evap_out_T_edit_2.setText(str(round(self.OutEvap.T-273.15,2)))
        self.ui.evap_out_p_edit_2.setText(str(round(self.OutEvap.p/1.0e5,2)))
        self.ui.COP_h_edit.setText(str(round(self.outputs.COP_heating,2)))
        COP_c = abs(self.OutEvap.q)/(self.outputs.Wcomp - self.outputs.Wexpand)
        self.ui.COP_c_edit.setText(str(round(COP_c,2)))
        kwusRT = (self.outputs.Wcomp - self.outputs.Wexpand)/1.0E3/abs(self.OutEvap.q/3516.8525)
        self.ui.kwusRT_edit.setText(str(round(kwusRT,2)))
        
        self.ui.REF_table.setItem(0, 0, QTableWidgetItem(str(round(self.OutEvap_REF.T-273.15,1))))
        self.ui.REF_table.setItem(0, 1, QTableWidgetItem(str(round(self.InCond_REF.T-273.15,1))))
        self.ui.REF_table.setItem(0, 2, QTableWidgetItem(str(round(self.OutCond_REF.T-273.15,1))))
        self.ui.REF_table.setItem(0, 3, QTableWidgetItem(str(round(self.InEvap_REF.T-273.15,1))))
        self.ui.REF_table.setItem(1, 0, QTableWidgetItem(str(round(self.OutEvap_REF.p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 1, QTableWidgetItem(str(round(self.InCond_REF.p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 2, QTableWidgetItem(str(round(self.OutCond_REF.p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 3, QTableWidgetItem(str(round(self.InEvap_REF.p/1.0e5,1))))
        self.ui.REF_table.setItem(2, 0, QTableWidgetItem(str(round(self.OutEvap_REF.h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 1, QTableWidgetItem(str(round(self.InCond_REF.h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 2, QTableWidgetItem(str(round(self.OutCond_REF.h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 3, QTableWidgetItem(str(round(self.InEvap_REF.h/1.0e3,1))))
        self.ui.REF_table.setItem(3, 0, QTableWidgetItem(str(round(self.OutEvap_REF.m*3600,2))))
        self.ui.REF_table.setItem(3, 1, QTableWidgetItem(str(round(self.InCond_REF.m*3600,2))))
        self.ui.REF_table.setItem(3, 2, QTableWidgetItem(str(round(self.OutCond_REF.m*3600,2))))
        self.ui.REF_table.setItem(3, 3, QTableWidgetItem(str(round(self.InEvap_REF.m*3600,2))))
        
    def IHX_batch_result(self):
        self.ui.comp_top_group_2.setHidden(False)
        self.ui.comp_top_eff_edit_2.setText(str(round(self.outputs.Wcomp/1000.0,2)))
        self.ui.expand_bot_group_2.setHidden(False)
        self.ui.expand_bot_eff_edit_2.setText(str(round(self.outputs.Wexpand/1000.0,2)))
        self.ui.cond_group_2.setHidden(False)
        self.ui.condQ_edit.setText(str(round(self.OutCond.q/1000.0,2)))
        self.ui.cond_in_group_2.setHidden(False)
        self.ui.cond_in_T_edit_2.setText(str(round(self.InCond.T-273.15,2)))
        self.ui.cond_in_p_edit_2.setText(str(round(self.InCond.p/1.0e5,2)))
        self.ui.cond_in_m_edit_2.setText(str(round(self.InCond.m,2)))
        self.ui.cond_out_group_2.setHidden(False)
        self.ui.cond_out_T_edit_2.setText(str(round(self.OutCond.T-273.15,2)))
        self.ui.cond_out_p_edit_2.setText(str(round(self.OutCond.p/1.0e5,2)))
        self.ui.evap_group_2.setHidden(False)
        self.ui.evapQ_edit.setText(str(round(-self.OutEvap.q/1000.0,2)))
        self.ui.evap_in_group_2.setHidden(False)
        self.ui.evap_in_T_edit_2.setText(str(round(self.InEvap.T-273.15,2)))
        self.ui.evap_in_p_edit_2.setText(str(round(self.InEvap.p/1.0e5,2)))
        self.ui.evap_in_m_edit_2.setText(str(round(self.InEvap.m,2)))
        self.ui.evap_out_group_2.setHidden(False)
        self.ui.evap_out_T_edit_2.setText(str(round(self.OutEvap.T-273.15,2)))
        self.ui.evap_out_p_edit_2.setText(str(round(self.OutEvap.p/1.0e5,2)))
        self.ui.IHX_group_2.setHidden(False)
        self.ui.IHXQ_edit.setText(str(round(self.outputs.qihx/1000.0,2)))
        self.ui.COP_h_edit.setText(str(round(self.outputs.COP_heating,2)))
        COP_c = abs(self.OutEvap.q)/(self.outputs.Wcomp - self.outputs.Wexpand)
        self.ui.COP_c_edit.setText(str(round(COP_c,2)))
        
        self.ui.REF_table.setItem(0, 0, QTableWidgetItem(str(round(self.OutEvap_REF.T-273.15,1))))
        self.ui.REF_table.setItem(0, 1, QTableWidgetItem(str(round(self.outputs.ihx_cold_out_T-273.15,1))))
        self.ui.REF_table.setItem(0, 2, QTableWidgetItem(str(round(self.InCond_REF.T-273.15,1))))
        self.ui.REF_table.setItem(0, 3, QTableWidgetItem(str(round(self.OutCond_REF.T-273.15,1))))
        self.ui.REF_table.setItem(0, 4, QTableWidgetItem(str(round(self.outputs.ihx_hot_out_T-273.15,1))))
        self.ui.REF_table.setItem(0, 5, QTableWidgetItem(str(round(self.InEvap_REF.T-273.15,1))))
        self.ui.REF_table.setItem(1, 0, QTableWidgetItem(str(round(self.OutEvap_REF.p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 1, QTableWidgetItem(str(round(self.outputs.ihx_cold_out_p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 2, QTableWidgetItem(str(round(self.InCond_REF.p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 3, QTableWidgetItem(str(round(self.OutCond_REF.p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 4, QTableWidgetItem(str(round(self.outputs.ihx_hot_out_p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 5, QTableWidgetItem(str(round(self.InEvap_REF.p/1.0e5,1))))
        self.ui.REF_table.setItem(2, 0, QTableWidgetItem(str(round(self.OutEvap_REF.h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 1, QTableWidgetItem(str(round(self.outputs.ihx_cold_out_h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 2, QTableWidgetItem(str(round(self.InCond_REF.h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 3, QTableWidgetItem(str(round(self.OutCond_REF.h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 4, QTableWidgetItem(str(round(self.outputs.ihx_hot_out_h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 5, QTableWidgetItem(str(round(self.InEvap_REF.h/1.0e3,1))))
        self.ui.REF_table.setItem(3, 0, QTableWidgetItem(str(round(self.OutEvap_REF.m,2))))
        self.ui.REF_table.setItem(3, 1, QTableWidgetItem(str(round(self.OutEvap_REF.m,2))))
        self.ui.REF_table.setItem(3, 2, QTableWidgetItem(str(round(self.InCond_REF.m,2))))
        self.ui.REF_table.setItem(3, 3, QTableWidgetItem(str(round(self.OutCond_REF.m,2))))
        self.ui.REF_table.setItem(3, 4, QTableWidgetItem(str(round(self.OutCond_REF.m,2))))
        self.ui.REF_table.setItem(3, 5, QTableWidgetItem(str(round(self.InEvap_REF.m,2))))
        
    def Inj_batch_result(self):
        self.ui.comp_top_group_2.setHidden(False)
        self.ui.comp_top_eff_edit_2.setText(str(round(self.outputs.Wcomp_top/1000.0,2)))
        self.ui.comp_bot_group_2.setHidden(False)
        self.ui.comp_bot_eff_edit_2.setText(str(round((self.outputs.Wcomp - self.outputs.Wcomp_top)/1000.0,2)))
        self.ui.expand_top_group_2.setHidden(False)
        self.ui.expand_top_eff_edit_2.setText(str(round((self.outputs.Wexpand-self.outputs.Wexpand_bot)/1000.0,2)))
        self.ui.expand_bot_group_2.setHidden(False)
        self.ui.expand_bot_eff_edit_2.setText(str(round(self.outputs.Wexpand_bot/1000.0,2)))
        self.ui.cond_group_2.setHidden(False)
        self.ui.condQ_edit.setText(str(round(self.OutCond.q/1000.0,2)))
        self.ui.cond_in_group_2.setHidden(False)
        self.ui.cond_in_T_edit_2.setText(str(round(self.InCond.T-273.15,2)))
        self.ui.cond_in_p_edit_2.setText(str(round(self.InCond.p/1.0e5,2)))
        self.ui.cond_in_m_edit_2.setText(str(round(self.InCond.m,2)))
        self.ui.cond_out_group_2.setHidden(False)
        self.ui.cond_out_T_edit_2.setText(str(round(self.OutCond.T-273.15,2)))
        self.ui.cond_out_p_edit_2.setText(str(round(self.OutCond.p/1.0e5,2)))
        self.ui.evap_group_2.setHidden(False)
        self.ui.evapQ_edit.setText(str(round(-self.OutEvap.q/1000.0,2)))
        self.ui.evap_in_group_2.setHidden(False)
        self.ui.evap_in_T_edit_2.setText(str(round(self.InEvap.T-273.15,2)))
        self.ui.evap_in_p_edit_2.setText(str(round(self.InEvap.p/1.0e5,2)))
        self.ui.evap_in_m_edit_2.setText(str(round(self.InEvap.m,2)))
        self.ui.evap_out_group_2.setHidden(False)
        self.ui.evap_out_T_edit_2.setText(str(round(self.OutEvap.T-273.15,2)))
        self.ui.evap_out_p_edit_2.setText(str(round(self.OutEvap.p/1.0e5,2)))
        self.ui.flash_tank_group.setHidden(False)
        self.ui.flash_tank_edit.setText(str(round(self.outputs.inter_x,2)))
        self.ui.comp_top_eff_label_2.setText('압축기 출력 (Top) [kW]')
        self.ui.comp_bot_eff_label_2.setText('압축기 출력 (Bot) [kW]')
        self.ui.expand_top_eff_label_2.setText('팽창기 출력 (Top) [kW]')
        self.ui.expand_bot_eff_label_2.setText('팽창기 출력 (Bot) [kW]')
        self.ui.COP_h_edit.setText(str(round(self.outputs.COP_heating,2)))
        COP_c = abs(self.OutEvap.q)/(self.outputs.Wcomp - self.outputs.Wexpand)
        self.ui.COP_c_edit.setText(str(round(COP_c,2)))
        
        self.ui.REF_table.setItem(0, 0, QTableWidgetItem(str(round(self.OutEvap_REF.T-273.15,1))))
        self.ui.REF_table.setItem(0, 1, QTableWidgetItem(str(round(self.outputs.outcomp_low_T-273.15,1))))
        self.ui.REF_table.setItem(0, 2, QTableWidgetItem(str(round(self.outputs.outexpand_high_T-273.15,1))))
        self.ui.REF_table.setItem(0, 3, QTableWidgetItem(str(round(self.outputs.incomp_high_T-273.15,1))))
        self.ui.REF_table.setItem(0, 4, QTableWidgetItem(str(round(self.InCond_REF.T-273.15,1))))
        self.ui.REF_table.setItem(0, 5, QTableWidgetItem(str(round(self.OutCond_REF.T-273.15,1))))
        self.ui.REF_table.setItem(0, 6, QTableWidgetItem(str(round(self.outputs.outexpand_high_T-273.15,1))))
        self.ui.REF_table.setItem(0, 7, QTableWidgetItem(str(round(self.outputs.flash_liq_T-273.15,1))))
        self.ui.REF_table.setItem(0, 8, QTableWidgetItem(str(round(self.InEvap_REF.T-273.15,1))))
        self.ui.REF_table.setItem(1, 0, QTableWidgetItem(str(round(self.OutEvap_REF.p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 1, QTableWidgetItem(str(round(self.outputs.outcomp_low_p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 2, QTableWidgetItem(str(round(self.outputs.outexpand_high_p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 3, QTableWidgetItem(str(round(self.outputs.incomp_high_p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 4, QTableWidgetItem(str(round(self.InCond_REF.p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 5, QTableWidgetItem(str(round(self.OutCond_REF.p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 6, QTableWidgetItem(str(round(self.outputs.outexpand_high_p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 7, QTableWidgetItem(str(round(self.outputs.flash_liq_p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 8, QTableWidgetItem(str(round(self.InEvap_REF.p/1.0e5,1))))
        self.ui.REF_table.setItem(2, 0, QTableWidgetItem(str(round(self.OutEvap_REF.h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 1, QTableWidgetItem(str(round(self.outputs.outcomp_low_h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 2, QTableWidgetItem(str(round(self.outputs.inter_h_vap/1.0e3,1))))
        self.ui.REF_table.setItem(2, 3, QTableWidgetItem(str(round(self.outputs.incomp_high_h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 4, QTableWidgetItem(str(round(self.InCond_REF.h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 5, QTableWidgetItem(str(round(self.OutCond_REF.h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 6, QTableWidgetItem(str(round(self.outputs.outexpand_high_h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 7, QTableWidgetItem(str(round(self.outputs.flash_liq_h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 8, QTableWidgetItem(str(round(self.InEvap_REF.h/1.0e3,1))))
        self.ui.REF_table.setItem(3, 0, QTableWidgetItem(str(round(self.OutEvap_REF.m,2))))
        self.ui.REF_table.setItem(3, 1, QTableWidgetItem(str(round(self.OutEvap_REF.m,2))))
        self.ui.REF_table.setItem(3, 2, QTableWidgetItem(str(round(self.InCond_REF.m,2))))
        self.ui.REF_table.setItem(3, 3, QTableWidgetItem(str(round(self.InCond_REF.m,2))))
        self.ui.REF_table.setItem(3, 4, QTableWidgetItem(str(round(self.InCond_REF.m,2))))
        self.ui.REF_table.setItem(3, 5, QTableWidgetItem(str(round(self.OutCond_REF.m,2))))
        self.ui.REF_table.setItem(3, 6, QTableWidgetItem(str(round(self.OutCond_REF.m,2))))
        self.ui.REF_table.setItem(3, 7, QTableWidgetItem(str(round(self.InEvap_REF.m,2))))
        self.ui.REF_table.setItem(3, 8, QTableWidgetItem(str(round(self.InEvap_REF.m,2))))
        
        
    def Cas_batch_result(self):
        self.ui.comp_top_group_2.setHidden(False)
        self.ui.comp_top_eff_edit_2.setText(str(round(self.outputs_t.Wcomp/1000.0,2)))
        self.ui.comp_bot_group_2.setHidden(False)
        self.ui.comp_bot_eff_edit_2.setText(str(round(self.outputs_b.Wcomp/1000.0,2)))
        self.ui.expand_top_group_2.setHidden(False)
        self.ui.expand_top_eff_edit_2.setText(str(round(self.outputs_t.Wexpand/1000.0,2)))
        self.ui.expand_bot_group_2.setHidden(False)
        self.ui.expand_bot_eff_edit_2.setText(str(round(self.outputs_b.Wexpand/1000.0,2)))
        self.ui.cond_group_2.setHidden(False)
        self.ui.condQ_edit.setText(str(round(self.OutCond.q/1000.0,2)))
        self.ui.cond_in_group_2.setHidden(False)
        self.ui.cond_in_T_edit_2.setText(str(round(self.InCond.T-273.15,2)))
        self.ui.cond_in_p_edit_2.setText(str(round(self.InCond.p/1.0e5,2)))
        self.ui.cond_in_m_edit_2.setText(str(round(self.InCond.m,2)))
        self.ui.cond_out_group_2.setHidden(False)
        self.ui.cond_out_T_edit_2.setText(str(round(self.OutCond.T-273.15,2)))
        self.ui.cond_out_p_edit_2.setText(str(round(self.OutCond.p/1.0e5,2)))
        self.ui.evap_group_2.setHidden(False)
        self.ui.evapQ_edit.setText(str(round(-self.OutEvap.q/1000.0,2)))
        self.ui.evap_in_group_2.setHidden(False)
        self.ui.evap_in_T_edit_2.setText(str(round(self.InEvap.T-273.15,2)))
        self.ui.evap_in_p_edit_2.setText(str(round(self.InEvap.p/1.0e5,2)))
        self.ui.evap_in_m_edit_2.setText(str(round(self.InEvap.m,2)))
        self.ui.evap_out_group_2.setHidden(False)
        self.ui.evap_out_T_edit_2.setText(str(round(self.OutEvap.T-273.15,2)))
        self.ui.evap_out_p_edit_2.setText(str(round(self.OutEvap.p/1.0e5,2)))
        self.ui.cas_group_2.setHidden(False)
        self.ui.casQ_edit.setText(str(round(self.OutEvap_REF_t.q/1000.0,2)))
        self.ui.COP_bot_group.setHidden(False)
        self.ui.COP_top_group.setHidden(False)
        self.ui.comp_top_eff_label_2.setText('압축기 출력 (Top) [kW]')
        self.ui.comp_bot_eff_label_2.setText('압축기 출력 (Bot) [kW]')
        self.ui.expand_top_eff_label_2.setText('팽창기 출력 (Top) [kW]')
        self.ui.expand_bot_eff_label_2.setText('팽창기 출력 (Bot) [kW]')
        COP_cascade_h = abs(self.OutCond.q)/(self.outputs_t.Wcomp - self.outputs_t.Wexpand + self.outputs_b.Wcomp - self.outputs_b.Wexpand)
        COP_cascade_c = abs(self.OutEvap.q)/(self.outputs_t.Wcomp - self.outputs_t.Wexpand + self.outputs_b.Wcomp - self.outputs_b.Wexpand)
        self.ui.COP_h_edit.setText(str(round(COP_cascade_h,2)))
        self.ui.COP_c_edit.setText(str(round(COP_cascade_c,2)))
        self.ui.COP_bot_edit.setText(str(round(self.outputs_b.COP_heating,2)))
        self.ui.COP_top_edit.setText(str(round(self.outputs_t.COP_heating,2)))
        
        self.ui.REF_table.setItem(0, 0, QTableWidgetItem(str(round(self.OutEvap_REF_b.T-273.15,1))))
        self.ui.REF_table.setItem(0, 1, QTableWidgetItem(str(round(self.InCond_REF_b.T-273.15,1))))
        self.ui.REF_table.setItem(0, 2, QTableWidgetItem(str(round(self.OutCond_REF_b.T-273.15,1))))
        self.ui.REF_table.setItem(0, 3, QTableWidgetItem(str(round(self.InEvap_REF_b.T-273.15,1))))
        self.ui.REF_table.setItem(0, 4, QTableWidgetItem(str(round(self.OutEvap_REF_t.T-273.15,1))))
        self.ui.REF_table.setItem(0, 5, QTableWidgetItem(str(round(self.InCond_REF_t.T-273.15,1))))
        self.ui.REF_table.setItem(0, 6, QTableWidgetItem(str(round(self.OutCond_REF_t.T-273.15,1))))
        self.ui.REF_table.setItem(0, 7, QTableWidgetItem(str(round(self.InEvap_REF_t.T-273.15,1))))
        self.ui.REF_table.setItem(1, 0, QTableWidgetItem(str(round(self.OutEvap_REF_b.p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 1, QTableWidgetItem(str(round(self.InCond_REF_b.p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 2, QTableWidgetItem(str(round(self.OutCond_REF_b.p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 3, QTableWidgetItem(str(round(self.InEvap_REF_b.p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 4, QTableWidgetItem(str(round(self.OutEvap_REF_t.p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 5, QTableWidgetItem(str(round(self.InCond_REF_t.p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 6, QTableWidgetItem(str(round(self.OutCond_REF_t.p/1.0e5,1))))
        self.ui.REF_table.setItem(1, 7, QTableWidgetItem(str(round(self.InEvap_REF_t.p/1.0e5,1))))
        self.ui.REF_table.setItem(2, 0, QTableWidgetItem(str(round(self.OutEvap_REF_b.h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 1, QTableWidgetItem(str(round(self.InCond_REF_b.h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 2, QTableWidgetItem(str(round(self.OutCond_REF_b.h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 3, QTableWidgetItem(str(round(self.InEvap_REF_b.h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 4, QTableWidgetItem(str(round(self.OutEvap_REF_t.h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 5, QTableWidgetItem(str(round(self.InCond_REF_t.h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 6, QTableWidgetItem(str(round(self.OutCond_REF_t.h/1.0e3,1))))
        self.ui.REF_table.setItem(2, 7, QTableWidgetItem(str(round(self.InEvap_REF_t.h/1.0e3,1))))
        self.ui.REF_table.setItem(3, 0, QTableWidgetItem(str(round(self.OutEvap_REF_b.m,2))))
        self.ui.REF_table.setItem(3, 1, QTableWidgetItem(str(round(self.InCond_REF_b.m,2))))
        self.ui.REF_table.setItem(3, 2, QTableWidgetItem(str(round(self.OutCond_REF_b.m,2))))
        self.ui.REF_table.setItem(3, 3, QTableWidgetItem(str(round(self.InEvap_REF_b.m,2))))
        self.ui.REF_table.setItem(3, 4, QTableWidgetItem(str(round(self.OutEvap_REF_t.m,2))))
        self.ui.REF_table.setItem(3, 5, QTableWidgetItem(str(round(self.InCond_REF_t.m,2))))
        self.ui.REF_table.setItem(3, 6, QTableWidgetItem(str(round(self.OutCond_REF_t.m,2))))
        self.ui.REF_table.setItem(3, 7, QTableWidgetItem(str(round(self.InEvap_REF_t.m,2))))
        
    def InputExample(self):
        self.ui.evap_fluid_table.setItem(0, 0, QTableWidgetItem('Water'))
        self.ui.evap_fluid_table.setItem(0, 1, QTableWidgetItem('1.0'))
        
        if self.process_type == 'steam':
            self.ui.evap_in_T_edit.setText('70.0')
        
            self.ui.evap_in_p_edit.setText('1.56')
            self.ui.evap_in_m_edit.setText('10.33')
            
            self.ui.evap_out_T_edit.setText('')
            self.ui.evap_out_p_edit.setText('1.39')
            
            if self.ui.cycle_type == 'vcc':
                self.ui.dT_lift_edit.setText('120.0')
                self.ui.cond_out_T_edit.setText('125.0')
            else:
                self.ui.dT_lift_edit.setText('140.0')
                self.ui.cond_out_T_edit.setText('150.0')
                
            self.ui.m_load_edit.setText('0.1153')
            self.ui.Tmakeup_edit.setText('25.0')
            self.ui.cond_in_T_edit.setEnabled(False)
            self.ui.cond_in_p_edit.setEnabled(False)
            self.ui.cond_in_m_edit.setEnabled(False)
            self.ui.cond_out_p_edit.setEnabled(False)
            
            self.ui.DSH_top_edit.setText('3.0')
            if self.cycle_type == 'vcc':
                self.ui.DSC_edit.setText('1.0')
            else:
                self.ui.DSC_edit.setText('')
                
            self.ui.ui.DSH_edit.setText('3.0')
            self.ui.ui.DSC_bot_edit.setText('1.0')
            
            self.ui.cond_dp_edit.setText('1.0')
            self.ui.cas_cold_dp_edit.setText('1.0')
            self.ui.cas_hot_dp_edit.setText('1.0')
            self.ui.evap_dp_edit.setText('1.0')
            
            if self.ui.cond_phe_radio.isChecked():
                self.ui.cond_T_pp_edit.setText('3.5')
            elif self.ui.cond_fthe_radio.isChecked():
                self.ui.cond_T_pp_edit.setText('15.0')
                self.ui.cond_N_row_edit.setText('10')
            
            if self.ui.cas_phe_radio.isChecked():
                self.ui.cas_T_pp_edit.setText('0.8')
            elif self.ui.cond_fthe_radio.isChecked():
                self.ui.cas_T_pp_edit.setText('15.0')
                self.ui.cas_N_row_edit.setText('5')
            
            if self.ui.evap_phe_radio.isChecked():
                self.ui.evap_T_pp_edit.setText('3.0')
            elif self.ui.evap_fthe_radio.isChecked():
                self.ui.evap_T_pp_edit.setText('15.0')
                self.ui.evap_N_row_edit.setText('5')
                    
            self.ui.comp_top_eff_edit.setText('80.0')
            self.ui.comp_eff_edit.setText('80.0')
            self.ui.comp_bot_eff_edit.setText('80.0')
            self.ui.expand_top_eff_edit.setText('0.0')
            self.ui.expand_eff_edit.setText('0.0')
            self.ui.expand_bot_eff_edit.setText('0.0')
            
            self.ui.IHX_eff_edit.setText('62.0')
            self.ui.IHX_hot_dp_edit.setText('1.0')
            self.ui.IHX_cold_dp_edit.setText('1.0')
            
            if self.layout_type == 'cas': 
                self.ui.ref_list_b.setCurrentIndex(1)
                self.ui.ref_list_t.setCurrentIndex(93)
            else:
                self.ui.ref_list_b.setCurrentIndex(93)       
            
            
        elif self.process_type == 'hotwater':
            self.ui.Thot_target_edit.setText('90.0')
            self.ui.time_target_edit.setText('10.0')
            self.ui.dT_lift_edit.setText('10.0')
            self.ui.m_load_edit.setText('10.0')
            self.ui.Tmakeup_edit.setText('25.0')
            self.ui.cond_in_T_edit.setEnabled(False)
            self.ui.cond_in_p_edit.setEnabled(False)
            self.ui.cond_in_m_edit.setEnabled(False)
            self.ui.cond_out_T_edit.setEnabled(False)
            self.ui.cond_out_p_edit.setEnabled(False)
        else:
            self.process_type = 'process'
            self.ui.evap_in_T_edit.setText('12.387')
        
            self.ui.evap_in_p_edit.setText('1.67')
            self.ui.evap_in_m_edit.setText('5.661')
            
            self.ui.evap_out_T_edit.setText('7.312')
            self.ui.evap_out_p_edit.setText('1.65')
            
            if self.cycle_type == 'vcc':
                self.ui.cond_fluid_table.setItem(0, 0, QTableWidgetItem('Water'))
                self.ui.cond_in_T_edit.setText('29.737')
                self.ui.cond_out_T_edit.setText('')
            else:
                self.ui.cond_fluid_table.setItem(0, 0, QTableWidgetItem('air'))
                self.ui.cond_in_T_edit.setText('120.0')
                self.ui.cond_out_T_edit.setText('160.0')
            
            self.ui.cond_fluid_table.setItem(0, 1, QTableWidgetItem('1.0'))
            self.ui.cond_in_p_edit.setText('2.36')
            self.ui.cond_in_m_edit.setText('7.131')
            self.ui.cond_out_p_edit.setText('2.15')
            
            self.ui.DSH_top_edit.setText('7.0')
            if self.cycle_type == 'vcc':
                self.ui.DSC_edit.setText('1.0')
            else:
                self.ui.DSC_edit.setText('')
                
            self.ui.DSH_edit.setText('7.0')
            self.ui.DSC_bot_edit.setText('1.0')
            
            self.ui.cond_dp_edit.setText('30.0')
            self.ui.cas_cold_dp_edit.setText('10.0')
            self.ui.cas_hot_dp_edit.setText('10.0')
            self.ui.evap_dp_edit.setText('15.0')
            
            if self.ui.cond_phe_radio.isChecked():
                self.ui.cond_T_pp_edit.setText('1.5')
            elif self.ui.cond_fthe_radio.isChecked():
                self.ui.cond_T_pp_edit.setText('15.0')
                self.ui.cond_N_row_edit.setText('10')
            
            if self.ui.cas_phe_radio.isChecked():
                self.ui.cas_T_pp_edit.setText('0.8')
            elif self.ui.cond_fthe_radio.isChecked():
                self.ui.cas_T_pp_edit.setText('15.0')
                self.ui.cas_N_row_edit.setText('5')
            
            if self.ui.evap_phe_radio.isChecked():
                self.ui.evap_T_pp_edit.setText('0.8')
            elif self.ui.evap_fthe_radio.isChecked():
                self.ui.evap_T_pp_edit.setText('15.0')
                self.ui.evap_N_row_edit.setText('5')
                    
            self.ui.comp_top_eff_edit.setText('70.0')
            self.ui.comp_eff_edit.setText('70.0')
            self.ui.motor_eff_edit.setText('95.0')
            self.ui.comp_bot_eff_edit.setText('70.0')
            self.ui.expand_top_eff_edit.setText('0.0')
            self.ui.expand_eff_edit.setText('0.0')
            self.ui.expand_bot_eff_edit.setText('0.0')
            
            
            self.ui.IHX_eff_edit.setText('90.0')
            self.ui.IHX_hot_dp_edit.setText('1.0')
            self.ui.IHX_cold_dp_edit.setText('1.0')
            
            if self.layout_type == 'cas': 
                self.ui.ref_list_b.setCurrentIndex(1)
                self.ui.ref_list_t.setCurrentIndex(77)
            else:
                self.ui.ref_list_b.setCurrentIndex(77)            
    
    def InputClear(self):
        self.ui.evap_fluid_table.clearContents()
        self.ui.evap_in_T_edit.setText('')
        self.ui.evap_in_p_edit.setText('')
        self.ui.evap_in_m_edit.setText('')
        self.ui.evap_out_p_edit.setText('')
        
        self.ui.Thot_target_edit.setText('')
        self.ui.time_target_edit.setText('')
        self.ui.dT_lift_edit.setText('')
        self.ui.m_load_edit.setText('')
        self.ui.Tmakeup_edit.setText('')
        
        self.ui.cond_fluid_table.clearContents()
        self.ui.cond_in_T_edit.setText('')
        self.ui.cond_in_p_edit.setText('')
        self.ui.cond_in_m_edit.setText('')
        self.ui.cond_out_T_edit.setText('')
        self.ui.cond_out_p_edit.setText('')
        
        self.ui.DSH_top_edit.setText('')
        self.ui.DSC_edit.setText('')
        self.ui.DSH_edit.setText('')
        self.ui.DSC_bot_edit.setText('')
        
        self.ui.cond_dp_edit.setText('')
        self.ui.cas_cold_dp_edit.setText('')
        self.ui.cas_hot_dp_edit.setText('')
        self.ui.evap_dp_edit.setText('')
        
        self.ui.cond_T_pp_edit.setText('')
        self.ui.cond_N_row_edit.setText('')
    
        self.ui.cas_T_pp_edit.setText('')
        self.ui.cas_N_row_edit.setText('')
        
        self.ui.IHX_eff_edit.setText('')
        self.ui.IHX_hot_dp_edit.setText('')
        self.ui.IHX_cold_dp_edit.setText('')
        
        self.ui.evap_T_pp_edit.setText('')
        self.ui.evap_N_row_edit.setText('')
                
        self.ui.comp_top_eff_edit.setText('')
        self.ui.comp_eff_edit.setText('')
        self.ui.comp_bot_eff_edit.setText('')
        self.ui.expand_top_eff_edit.setText('')
        self.ui.expand_eff_edit.setText('')
        self.ui.expand_bot_eff_edit.setText('')
    
        self.ui.ref_list_b.setCurrentIndex(0)
        self.ui.ref_list_t.setCurrentIndex(0)
            
    def Valve_Recommand(self):
        from VALVE_GUI import valveWindow
        if self.layout_type == 'cas':
            maxdP_bot = (self.OutCond_REF_b.p - self.InEvap_REF_b.p)
            maxP_bot = self.OutCond_REF_b.p
            maxT_bot = self.OutCond_REF_b.T
            minT_bot = self.InEvap_REF_b.T
            maxD_bot = PropsSI('D','T',maxT_bot,'P',maxP_bot,self.OutCond_REF_b.fluidmixture)
            V_bot = self.OutCond_REF_b.m/maxD_bot*3600.0
            Kv_bot = V_bot*sqrt(maxD_bot*10/maxdP_bot)
            Qbot = self.OutCond_b.q
            maxdP_top = self.OutCond_REF_t.p - self.InEvap_REF_t.p
            maxP_top = self.OutCond_REF_t.p
            maxT_top = self.OutCond_REF_t.T
            minT_top = self.InEvap_REF_t.T
            maxD_top = PropsSI('D','T',maxT_top,'P',maxP_top,self.OutCond_REF_t.fluidmixture)
            V_top = self.OutCond_REF_t.m/maxD_top*3600.0
            Kv_top = V_top*sqrt(maxD_top*10/maxdP_top)
            Qtop = self.OutCond_t.q
            self.valve = valveWindow(Qbot, maxdP_bot, maxP_bot, maxT_bot, minT_bot, Kv_bot, Qtop, maxdP_top, maxP_top, maxT_top, minT_top, Kv_top, self.layout_type)
        elif self.layout_type == 'inj':
            maxdP_bot = (self.outputs.flash_liq_p - self.InEvap_REF.p)
            maxP_bot = self.outputs.flash_liq_p
            maxT_bot = self.outputs.flash_liq_T
            minT_bot = self.InEvap_REF.p
            maxD_bot = PropsSI('D','T',maxT_bot,'Q',0.0, self.OutCond_REF.fluidmixture)
            V_bot = self.InEvap_REF.m/maxD_bot*3600.0
            Kv_bot = V_bot*sqrt(maxD_bot*10/maxdP_bot)
            Qbot = self.OutCond.q
            maxdP_top = (self.OutCond_REF.p - self.outputs.outexpand_high_p)
            maxP_top = self.OutCond_REF.p
            maxT_top = self.OutCond_REF.T
            minT_top = self.outputs.outexpand_high_T
            maxD_top = PropsSI('D','T',maxT_top,'P',maxP_top,self.OutCond_REF.fluidmixture)
            V_top = self.OutCond_REF.m/maxD_top*3600.0
            Kv_top = V_top*sqrt(maxD_top*10/maxdP_top)
            Qtop = self.OutCond.q
            self.valve = valveWindow(Qbot, maxdP_bot, maxP_bot, maxT_bot, minT_bot, Kv_bot, Qbot, maxdP_top, maxP_top, maxT_top, minT_top, Kv_top, self.layout_type)
        elif self.layout_type == 'ihx':
            maxdP_bot = (self.outputs.ihx_cold_out_p - self.InEvap_REF.p)
            maxP_bot = self.outputs.ihx_cold_out_p
            maxT_bot = self.outputs.ihx_cold_out_T
            minT_bot = self.InEvap_REF.T
            maxD_bot = PropsSI('D','T',maxT_bot,'P',maxP_bot, self.OutCond_REF.fluidmixture)
            V_bot = self.OutCond_REF.m/maxD_bot*3600.0
            Kv_bot = V_bot*sqrt(maxD_bot*10/maxdP_bot)
            Qbot = self.OutCond.q
            self.valve = valveWindow(Qbot, maxdP_bot, maxP_bot, maxT_bot, minT_bot, Kv_bot, Qbot, maxdP_bot, maxP_bot, maxT_bot, minT_bot, Kv_bot, self.layout_type)
        else:
            maxdP_bot = (self.OutCond_REF.p - self.InEvap_REF.p)
            maxP_bot = self.OutCond_REF.p
            maxT_bot = self.OutCond_REF.T
            minT_bot = self.InEvap_REF.T
            maxD_bot = PropsSI('D','T',maxT_bot,'P',maxP_bot, self.OutCond_REF.fluidmixture)
            V_bot = self.OutCond_REF.m/maxD_bot*3600.0
            Kv_bot = V_bot*sqrt(maxD_bot*10/maxdP_bot)
            Qbot = self.OutCond.q
            self.valve = valveWindow(Qbot, maxdP_bot, maxP_bot, maxT_bot, minT_bot, Kv_bot, Qbot, maxdP_bot, maxP_bot, maxT_bot, minT_bot, Kv_bot, self.layout_type)
                
        self.valve.show()
    
    def Compressor_Recommand(self):
        from COMPRESSOR_GUI import compressorWindow
        if self.layout_type == 'cas':
            Pevap = self.OutEvap_REF_b.p
            Pcond = self.InCond_REF_b.p
            Tcomp_in = self.OutEvap_REF_b.T
            mdot = self.OutEvap_REF_b.m
            Refrigerant = self.OutEvap_REF_b.fluidmixture
            Pevap_2 = self.OutEvap_REF_t.p
            Pcond_2 = self.InCond_REF_t.p
            Tcomp_in_2 = self.OutEvap_REF_t.T
            mdot_2 = self.OutEvap_REF_t.m
            Refrigerant_2 = self.OutEvap_REF_t.fluidmixture
            
        elif self.layout_type == 'inj':
            Pevap = self.OutEvap_REF.p
            Pcond = self.outputs.outcomp_low_p
            Tcomp_in = self.OutEvap_REF.T
            mdot = self.OutEvap_REF.m
            Refrigerant = self.OutEvap_REF.fluidmixture
            Pevap_2 = self.outputs.incomp_high_p
            Pcond_2 = self.InCond_REF.p
            Tcomp_in_2 = self.outputs.incomp_high_T
            mdot_2 = self.InCond_REF.m
            Refrigerant_2 = self.InCond_REF.fluidmixture
            
        elif self.layout_type == 'ihx':
            Pevap = self.outputs.ihx_cold_out_p
            Pcond = self.InCond_REF.p
            Tcomp_in = self.outputs.ihx_cold_out_T
            mdot = self.InCond_REF.m
            Refrigerant = self.OutEvap_REF.fluidmixture
            Pevap_2 = self.outputs.ihx_cold_out_p
            Pcond_2 = self.OutCond_REF.p
            Tcomp_in_2 = self.outputs.ihx_cold_out_T
            mdot_2 = self.OutCond_REF.m
            Refrigerant_2 = self.OutEvap_REF.fluidmixture
            
        else:
            Pevap = self.OutEvap_REF.p
            Pcond = self.InCond_REF.p
            Tcomp_in = self.OutEvap_REF.T
            mdot = self.InCond_REF.m
            Refrigerant = self.OutEvap_REF.fluidmixture
            Pevap_2 = self.OutEvap_REF.p
            Pcond_2 = self.InCond_REF.p
            Tcomp_in_2 = self.OutEvap_REF.T
            mdot_2 = self.InCond_REF.m
            Refrigerant_2 = self.OutEvap_REF.fluidmixture
        
        self.compressor = compressorWindow(Pevap, Pcond, Tcomp_in, mdot, Refrigerant, Pevap_2, Pcond_2, Tcomp_in_2, mdot_2, Refrigerant_2, self.layout_type)            
        self.compressor.show()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    myWindow = WindowClass()
    
    sys.exit(app.exec())