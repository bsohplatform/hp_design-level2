from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic
from CoolProp.CoolProp import PropsSI
import pandas as pd
import math
import matplotlib.pyplot as PLT

import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

form = resource_path("COMPRESSOR.ui")
form_class = uic.loadUiType(form)[0]

class compressorWindow(QMainWindow, form_class):
    def __init__(self, Pevap, Pcond, Wcomp, Refrigerant, Pevap_2, Pcond_2, Wcomp_2, Refrigerant_2, layout_type):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("COMPRESSOR_RECOMMANDATION")
        comp_data = pd.read_excel('.\DBs\\compressors\Compressor.xlsx', sheet_name=None, engine='openpyxl')
        
        (model_name, min_row_idx) = self.compressor_recommand(Pevap, Pcond, Wcomp, Refrigerant, comp_data, 'Operation_boundary')
            
        self.comp_picture.setPixmap(QPixmap(".\DBs\compressors\Figs\\"+model_name[:2]+".png").scaledToHeight(180))
        self.operation_boundary.setPixmap(QPixmap(".\DBs\compressors\Figs\Operation_boundary.png").scaledToWidth(300))
        if model_name[:2] == 'CS' or model_name[:2] == 'HS' or model_name[:2] == 'OS':
            brand_name = 'Bitzer-'
        else:
            brand_name = 'Danfoss-'
        
        self.model_text.setText(brand_name+model_name)
        if pd.isna(comp_data[model_name].iloc[min_row_idx]['volumetric flow [m3/h]']):
            self.volumeflow_text.setText('-')
        else:
            self.volumeflow_text.setText(str(comp_data[model_name].iloc[min_row_idx]['volumetric flow [m3/h]']))
        if pd.isna(comp_data[model_name].iloc[min_row_idx]['weight [kg]']):
            self.weight_text.setText('-')
        else:
            self.weight_text.setText(str(comp_data[model_name].iloc[min_row_idx]['weight [kg]']))
        if pd.isna(comp_data[model_name].iloc[min_row_idx]['suction [in]']):
            self.suction_text.setText('-')
        else:
            self.suction_text.setText(str(comp_data[model_name].iloc[min_row_idx]['suction [in]']))        
        if pd.isna(comp_data[model_name].iloc[min_row_idx]['discharge [in]']):
            self.discharge_text.setText('-')
        else:
            self.discharge_text.setText(str(comp_data[model_name].iloc[min_row_idx]['discharge [in]']))
        if pd.isna(comp_data[model_name].iloc[min_row_idx]['voltage_low [V]']):
            self.voltage_low_text.setText('-')
        else:
            self.voltage_low_text.setText(str(comp_data[model_name].iloc[min_row_idx]['voltage_low [V]']))    
        if pd.isna(comp_data[model_name].iloc[min_row_idx]['voltage_high [V]']):
            self.voltage_high_text.setText('-')
        else:
            self.voltage_high_text.setText(str(comp_data[model_name].iloc[min_row_idx]['voltage_high [V]']))
        
        if pd.isna(comp_data[model_name].iloc[min_row_idx]['RPM']):
            self.rotation_text.setText('-')
        else:
            self.rotation_text.setText(str(comp_data[model_name].iloc[min_row_idx]['RPM']))
        if pd.isna(comp_data[model_name].iloc[min_row_idx]['IP class']):
            self.IPclass_text.setText('-')
        else:
            self.IPclass_text.setText(str(comp_data[model_name].iloc[min_row_idx]['IP class']))
        if pd.isna(comp_data[model_name].iloc[min_row_idx]['Oil']):
            self.oil_text.setText('-')
        else:
            self.oil_text.setText(str(comp_data[model_name].iloc[min_row_idx]['Oil']))
            
        if layout_type == 'cas' or layout_type == 'inj':
            self.comp_tab.setTabText(0, '압축기 스펙(Bot)')
            self.comp_tab.setTabText(1, '압축기 스펙(Top)')
            (model_name_2, min_row_idx_2) = self.compressor_recommand(Pevap_2, Pcond_2, Wcomp_2, Refrigerant_2, comp_data, 'Operation_boundary_2')            
            self.comp_picture_2.setPixmap(QPixmap(".\DBs\compressors\Figs\\"+model_name_2[:2]+".png").scaledToHeight(180))
            self.operation_boundary_2.setPixmap(QPixmap(".\DBs\compressors\Figs\Operation_boundary_2.png").scaledToWidth(300))
            if model_name_2[:2] == 'CS' or model_name_2[:2] == 'HS' or model_name_2[:2] == 'OS':
                brand_name_2 = 'Bitzer-'
            else:
                brand_name_2 = 'Danfoss-'
            
            self.model_text_2.setText(brand_name_2+model_name_2)
            if pd.isna(comp_data[model_name_2].iloc[min_row_idx_2]['volumetric flow [m3/h]']):
                self.volumeflow_text_2.setText('-')
            else:
                self.volumeflow_text_2.setText(str(comp_data[model_name_2].iloc[min_row_idx_2]['volumetric flow [m3/h]']))
            if pd.isna(comp_data[model_name_2].iloc[min_row_idx_2]['weight [kg]']):
                self.weight_text_2.setText('-')
            else:
                self.weight_text_2.setText(str(comp_data[model_name_2].iloc[min_row_idx_2]['weight [kg]']))
            if pd.isna(comp_data[model_name_2].iloc[min_row_idx_2]['suction [in]']):
                self.suction_text_2.setText('-')
            else:
                self.suction_text_2.setText(str(comp_data[model_name_2].iloc[min_row_idx_2]['suction [in]']))        
            if pd.isna(comp_data[model_name_2].iloc[min_row_idx_2]['discharge [in]']):
                self.discharge_text_2.setText('-')
            else:
                self.discharge_text_2.setText(str(comp_data[model_name_2].iloc[min_row_idx_2]['discharge [in]']))
            if pd.isna(comp_data[model_name_2].iloc[min_row_idx_2]['voltage_low [V]']):
                self.voltage_low_text_2.setText('-')
            else:
                self.voltage_low_text_2.setText(str(comp_data[model_name_2].iloc[min_row_idx_2]['voltage_low [V]']))    
            if pd.isna(comp_data[model_name_2].iloc[min_row_idx_2]['voltage_high [V]']):
                self.voltage_high_text_2.setText('-')
            else:
                self.voltage_high_text_2.setText(str(comp_data[model_name_2].iloc[min_row_idx_2]['voltage_high [V]']))
            
            if pd.isna(comp_data[model_name_2].iloc[min_row_idx_2]['RPM']):
                self.rotation_text_2.setText('-')
            else:
                self.rotation_text_2.setText(str(comp_data[model_name_2].iloc[min_row_idx_2]['RPM']))
            if pd.isna(comp_data[model_name_2].iloc[min_row_idx_2]['IP class']):
                self.IPclass_text_2.setText('-')
            else:
                self.IPclass_text_2.setText(str(comp_data[model_name_2].iloc[min_row_idx_2]['IP class']))
            if pd.isna(comp_data[model_name_2].iloc[min_row_idx_2]['Oil']):
                self.oil_text_2.setText('-')
            else:
                self.oil_text_2.setText(str(comp_data[model_name_2].iloc[min_row_idx_2]['Oil']))
            
    def compressor_recommand(self, Pevap, Pcond, Wcomp, Refrigerant, comp_data, fig_name):
        Tevap = PropsSI('T','P',Pevap,'Q',1.0,Refrigerant)
        Tevap = Tevap - 273.15
        Tcond = PropsSI('T','P',Pcond,'Q',1.0,Refrigerant)
        Tcond = Tcond - 273.15
        
        model_list = comp_data.keys()
        minidx_list = []
        min_list = []
        for m in model_list:
            distance_list = []
            Wcomp_list = []
            ref_list = []
            tot_list = []
            
            for idx, l in comp_data[m].iterrows():
                limit_coeff = l[['LIMIT1','LIMIT2','LIMIT3','LIMIT4','LIMIT5','LIMIT6','LIMIT7','LIMIT8','LIMIT9','LIMIT10']] 
                distance = 0.0
                for coeff in range(limit_coeff.notnull().sum()):
                    x_lim = float(limit_coeff.iloc[coeff][1:limit_coeff.iloc[coeff].find(',')])
                    y_lim = float(limit_coeff.iloc[coeff][limit_coeff.iloc[coeff].find(',')+1:-1])
                    distance = distance + math.sqrt((x_lim-Tevap)**2+(y_lim-Tcond)**2)
                
                distance = distance/math.sqrt(Tevap**2+Tcond**2)               
                distance_list.append(distance)
                
                Wcomp_db_coeff = l[['PC0','PC1','PC2','PC3','PC4','PC5','PC6','PC7','PC8','PC9']]
                Wcomp_db = float(Wcomp_db_coeff.iloc[0])
                Wcomp_db = Wcomp_db+float(Wcomp_db_coeff.iloc[1])*Tevap
                Wcomp_db = Wcomp_db+float(Wcomp_db_coeff.iloc[2])*Tcond
                Wcomp_db = Wcomp_db+float(Wcomp_db_coeff.iloc[3])*Tevap**2
                Wcomp_db = Wcomp_db+float(Wcomp_db_coeff.iloc[4])*Tevap*Tcond
                Wcomp_db = Wcomp_db+float(Wcomp_db_coeff.iloc[5])*Tcond**2
                Wcomp_db = Wcomp_db+float(Wcomp_db_coeff.iloc[6])*math.pow(Tevap,3)
                Wcomp_db = Wcomp_db+float(Wcomp_db_coeff.iloc[7])*Tcond*Tevap**2
                Wcomp_db = Wcomp_db+float(Wcomp_db_coeff.iloc[8])*Tcond**2*Tevap
                Wcomp_db = Wcomp_db+float(Wcomp_db_coeff.iloc[9])*math.pow(Tcond,3)
                
                dWcomp = abs(Wcomp_db-Wcomp)/Wcomp
                Wcomp_list.append(dWcomp)
                
                ref_db = str(l['REF_types'])
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
                        
                    dref = math.sqrt((Tcrit_db-Tcrit)**2+(Tnbp_db-Tnbp)**2)/math.sqrt((Tcrit-273.15)**2+(Tnbp-273.15)**2)
                                        
                ref_list.append(dref)
                tot_list.append(distance+dWcomp+dref)
            
            comp_data[m]['distance'] = distance_list
            comp_data[m]['dWcomp'] = Wcomp_list
            comp_data[m]['dref'] = ref_list
            
            comp_data[m]['Total_score'] = tot_list
            min_list.append(min(tot_list))
            minidx_list.append(tot_list.index(min(tot_list)))
        
        min_sheet_idx = min_list.index(min(min_list))
        min_row_idx = minidx_list[min_sheet_idx]
        
        model_name = list(model_list)[min_sheet_idx]
        selected_model = comp_data[model_name].iloc[min_row_idx]
        
        limit_coeff = selected_model[['LIMIT1','LIMIT2','LIMIT3','LIMIT4','LIMIT5','LIMIT6','LIMIT7','LIMIT8','LIMIT9','LIMIT10']] 
        x_list = []
        y_list = []
        for coeff in range(limit_coeff.notnull().sum()):
            x_lim = float(limit_coeff.iloc[coeff][1:limit_coeff.iloc[coeff].find(',')])
            y_lim = float(limit_coeff.iloc[coeff][limit_coeff.iloc[coeff].find(',')+1:-1])
            x_list.append(x_lim)
            y_list.append(y_lim)
        
        x_list.append(x_list[0])
        y_list.append(y_list[0])
        
        fig_ph, ax_ph = PLT.subplots()
        ax_ph.plot([i for i in x_list], [i for i in y_list],'k')
        ax_ph.scatter(Tevap, Tcond, color = 'red', s = 50, marker = '*', label='Operation Point')
        ax_ph.set_xlabel('Evaporation Temperature [℃]',fontsize = 15)
        ax_ph.set_ylabel('Condensation Temperature [℃]',fontsize = 15)
        ax_ph.set_title('Compressor Operation Boundary',fontsize = 18)
        ax_ph.tick_params(axis = 'x', labelsize = 13)
        ax_ph.tick_params(axis = 'y', labelsize = 13)
        fig_ph.savefig('.\DBs\compressors\Figs\\'+fig_name+'.png',dpi=300)
        
        return (model_name, min_row_idx)