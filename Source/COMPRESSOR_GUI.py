from PySide6.QtCore import QSize, Qt, QFile
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QTableWidgetItem, QMessageBox
from PySide6.QtUiTools import loadUiType
from CoolProp.CoolProp import PropsSI
import pandas as pd
import math
import matplotlib.pyplot as PLT

import sys
import os
import subprocess

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

form = resource_path("COMPRESSOR.ui")
form_class = loadUiType(form)[0]

class compressorWindow(QMainWindow, form_class):
    def __init__(self, Pevap, Pcond, Tcomp_in, mdot, Refrigerant, Pevap_2, Pcond_2, Tcomp_in_2, mdot_2, Refrigerant_2, layout_type):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("COMPRESSOR_RECOMMANDATION")        
        comp_data = pd.read_csv('.\\DBs\\Compressor_DB\\Comp_DB.csv')
        self.point_list = ['Point1','Point2','Point3','Point4','Point5','Point6','Point7','Point8','Point9','Point10','Point11','Point12']
        min_row_idx = self.compressor_recommand(Pevap, Pcond, Tcomp_in, mdot, Refrigerant, comp_data, 'Operation_boundary')
        company = str(comp_data['Company'].loc[min_row_idx])
        model_name = str(comp_data['Model'].loc[min_row_idx])
        
        self.pdf_path=".\\DBs\\Compressor_DB\\"+company[0]+"_"+model_name+".pdf"
        self.operation_boundary.setPixmap(QPixmap(".\\DBs\\Compressor_DB\\Figs\\Operation_boundary.png").scaledToHeight(300))
        
        self.model_text.setText(company+'  '+model_name)
        self.rotation_text.setText('3600')
        if pd.isna(comp_data['Discharge'].iloc[min_row_idx]):
            self.volumeflow_text.setText('-')
        else:
            self.volumeflow_text.setText(str(comp_data['Discharge'].iloc[min_row_idx]))
        if pd.isna(comp_data['Diameter_Suction'].iloc[min_row_idx]):
            self.suction_text.setText('-')
        else:
            self.suction_text.setText(str(comp_data['Diameter_Suction'].iloc[min_row_idx]))        
        if pd.isna(comp_data['Diameter_Discharge'].iloc[min_row_idx]):
            self.discharge_text.setText('-')
        else:
            self.discharge_text.setText(str(comp_data['Diameter_Discharge'].iloc[min_row_idx]))
        if pd.isna(comp_data['Voltage'].iloc[min_row_idx]):
            self.voltage_text.setText('-')
        else:
            self.voltage_text.setText(str(comp_data['Voltage'].iloc[min_row_idx]))    
        if pd.isna(comp_data['Enclosure_class'].iloc[min_row_idx]):
            self.IPclass_text.setText('-')
        else:
            self.IPclass_text.setText(str(comp_data['Enclosure_class'].iloc[min_row_idx]))
        if pd.isna(comp_data['Oil_type'].iloc[min_row_idx]):
            self.oil_text.setText('-')
        else:
            self.oil_text.setText(str(comp_data['Oil_type'].iloc[min_row_idx]))
        
        self.comp_spec_btn.clicked.connect(self.open_specification)
        
        if layout_type == 'cas' or layout_type == 'inj':
            self.comp_tab.setTabText(0, '압축기 스펙(Bot)')
            self.comp_tab.setTabText(1, '압축기 스펙(Top)')
            min_row_idx_2 = self.compressor_recommand(Pevap_2, Pcond_2, Tcomp_in_2, mdot_2, Refrigerant_2, comp_data, 'Operation_boundary_2')
            company_2 = str(comp_data['Company'].loc[min_row_idx_2])
            model_name_2 = str(comp_data['Model'].loc[min_row_idx_2])
            self.comp_picture.setPixmap(QPixmap(".\\DBs\\Compressor_DB\\"+company_2[0]+"_"+model_name_2+".pdf").scaledToHeight(180))
            self.operation_boundary.setPixmap(QPixmap(".\\DBs\\Compressor_DB\\Figs\\Operation_boundary_2.png").scaledToWidth(431))
            
            self.model_text_2.setText(company_2+'  '+model_name_2)
            self.rotation_text_2.setText('3600')
            if pd.isna(comp_data['Discharge'].iloc[min_row_idx_2]):
                self.volumeflow_text_2.setText('-')
            else:
                self.volumeflow_text_2.setText(str(comp_data['Discharge'].iloc[min_row_idx_2]))
            if pd.isna(comp_data['Diameter_Suction'].iloc[min_row_idx_2]):
                self.suction_text_2.setText('-')
            else:
                self.suction_text_2.setText(str(comp_data['Diameter_Suction'].iloc[min_row_idx_2]))        
            if pd.isna(comp_data['Diameter_Discharge'].iloc[min_row_idx_2]):
                self.discharge_text_2.setText('-')
            else:
                self.discharge_text_2.setText(str(comp_data['Diameter_Discharge'].iloc[min_row_idx_2]))
            if pd.isna(comp_data['Voltage'].iloc[min_row_idx_2]):
                self.voltage_text_2.setText('-')
            else:
                self.voltage_text_2.setText(str(comp_data['Voltage'].iloc[min_row_idx_2]))    
            if pd.isna(comp_data['Enclosure_class'].iloc[min_row_idx_2]):
                self.IPclass_text_2.setText('-')
            else:
                self.IPclass_text_2.setText(str(comp_data['Enclosure_class'].iloc[min_row_idx_2]))
            if pd.isna(comp_data['Oil_type'].iloc[min_row_idx_2]):
                self.oil_text_2.setText('-')
            else:
                self.oil_text_2.setText(str(comp_data['Oil_type'].iloc[min_row_idx_2]))
    
    def open_specification(self):
        try:
            subprocess.run(["start", self.pdf_path], shell=True)
        except Exception as e:
            print(f"Failed to open PDF: {e}")
           
    def compressor_recommand(self, Pevap, Pcond, Tcomp_in, mdot, Refrigerant, comp_data, fig_name):
        Tevap = PropsSI('T','P',Pevap,'Q',1.0,Refrigerant)
        Tevap = Tevap - 273.15
        Tcond = PropsSI('T','P',Pcond,'Q',1.0,Refrigerant)
        Tcond = Tcond - 273.15
        tot_list = []
        ref_list = []
        flow_list = []
        limit_list = []
        for idx in range(len(comp_data)):
            limit_coeff = comp_data[self.point_list].loc[idx]
            distance = 0.0
            notnull = (limit_coeff.notnull().sum())
            for point in range(notnull):
                xy = str(limit_coeff[self.point_list[point]])
                x_lim = float(xy[xy.find('(')+1:xy.find(',')])
                y_lim = float(xy[xy.find(',')+1:xy.find(')')])
                distance = distance + math.sqrt((x_lim-Tevap)**2+(y_lim-Tcond)**2)
            
            distance = distance/math.sqrt(Tevap**2+Tcond**2)               
            
            vol_flow_db = float(comp_data['Discharge'].loc[idx])
            Dcomp_in = PropsSI("D","T",Tcomp_in,"P",Pevap,Refrigerant)
            vol_flow = mdot/Dcomp_in*3600
            
            dvol_flow = abs(vol_flow_db-vol_flow)/vol_flow
            ref_db = str(comp_data['Refrigerant'].loc[idx])
            if ref_db == Refrigerant:
                dref = 0.0
            else:
                Tcrit = PropsSI('Tcrit','',0,'',0,Refrigerant)
                try:
                    Tnbp = PropsSI('T','P',101300.0,'Q',0.0,Refrigerant)
                except:
                    Tnbp = PropsSI('TTRIPLE','',0,'',0,Refrigerant)
                
                try:
                    Tcrit_db = PropsSI('Tcrit','',0,'',0,ref_db)
                    try:
                        Tnbp_db = PropsSI('T','P',101300.0,'Q',0.0,ref_db)
                    except:
                        Tnbp_db = PropsSI('TTRIPLE','',0,'',0,ref_db)
                except:
                    Tcrit_db = 0.0
                    Tnbp_db = 0.0
                
                dref = math.sqrt((Tcrit_db-Tcrit)**2+(Tnbp_db-Tnbp)**2)/math.sqrt((Tcrit-273.15)**2+(Tnbp-273.15)**2)*10
                
            limit_list.append(distance)
            flow_list.append(dvol_flow)
            ref_list.append(dref)
            tot_score =  distance+dvol_flow+dref
            tot_list.append(tot_score)
        
        comp_data['Limit_score'] = limit_list
        comp_data['flow_score'] = flow_list
        comp_data['Ref_score'] = ref_list
        comp_data['Tot_score'] = tot_list
        min_row_idx = comp_data['Tot_score'].idxmin()
        selected_model = comp_data[self.point_list].loc[min_row_idx]
        x_list = []
        y_list = []
        notnull = (selected_model.notnull().sum())
        for point in range(notnull):
            xy = str(selected_model[self.point_list[point]])
            x_lim = float(xy[xy.find('(')+1:xy.find(',')])
            y_lim = float(xy[xy.find(',')+1:xy.find(')')])    
            x_list.append(x_lim)
            y_list.append(y_lim)
        
        x_list.append(x_list[0])
        y_list.append(y_list[0])
        
        fig_ph, ax_ph = PLT.subplots()
        ax_ph.plot([i for i in x_list], [i for i in y_list],'b--')
        ax_ph.scatter(Tevap, Tcond, color = 'red', s = 100, marker = '*', label='Operation Point')
        ax_ph.set_xlabel('Evaporation Temperature [℃]',fontsize = 15)
        ax_ph.set_ylabel('Condensation Temperature [℃]',fontsize = 15)
        ax_ph.set_title('Compressor Operation Boundary',fontsize = 18)
        ax_ph.tick_params(axis = 'x', labelsize = 13)
        ax_ph.tick_params(axis = 'y', labelsize = 13)
        fig_ph.savefig('.\\DBs\Compressor_DB\\Figs\\'+fig_name+'.png',dpi=500)
        
        return (min_row_idx)