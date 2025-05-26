from PySide6.QtCore import QSize, Qt, QFile
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QTableWidgetItem, QMessageBox
from PySide6.QtUiTools import QUiLoader
import pandas as pd


import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class valveWindow(QMainWindow):
    def __init__(self, maxdP_bot, maxP_bot, maxT_bot, minT_bot, Kv_bot, maxdP_top, maxP_top, maxT_top, minT_top, Kv_top, layout_type):
        super().__init__()
        loader = QUiLoader()
        ui_file = QFile(resource_path('VALVE.ui'))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()
        
        self.setCentralWidget(self.ui)
        self.ui.show()
        
        
        self.setWindowTitle("VALVE_RECOMMANDATION")
        
        maxdP_bot = maxdP_bot/1.0e5
        maxP_bot = maxP_bot/1.0e5
        maxT_bot = maxT_bot - 273.15
        minT_bot = minT_bot - 273.15
        maxdP_top = maxdP_top/1.0e5
        maxP_top = maxP_top/1.0e5
        maxT_top = maxT_top - 273.15
        minT_top = minT_top - 273.15
        
        valve_data = pd.read_csv(resource_path('DBs/valves/Danfoss_Valve.csv'),encoding='cp949')
        valve_data['Kv_diff'] = abs(valve_data['Kv']*0.6-Kv_bot)
        valve_data_b = valve_data[(valve_data['maxdP'] > maxdP_bot) & (valve_data['maxP'] > maxP_bot) & (valve_data['maxT'] > maxT_bot) & (valve_data['minT'] < minT_bot)]
        kv_min_idx = valve_data_b['Kv_diff'].idxmin()
        self.ui.valve_bot_fig.setPixmap(QPixmap(resource_path("DBs/valves/Figs/"+valve_data.iloc[kv_min_idx]['Fig']+".png")).scaledToHeight(220))
        self.ui.model.setText(valve_data.iloc[kv_min_idx]['Brand']+' '+valve_data.iloc[kv_min_idx]['Model'])
        self.ui.NS.setText(str(valve_data.iloc[kv_min_idx]['NS']))
        self.ui.Kv.setText(str(valve_data.iloc[kv_min_idx]['Kv']))
        self.ui.max_dp.setText(str(valve_data.iloc[kv_min_idx]['maxdP']))
        self.ui.max_p.setText(str(valve_data.iloc[kv_min_idx]['maxP']))
        self.ui.max_T.setText(str(valve_data.iloc[kv_min_idx]['maxT']))
        self.ui.min_T.setText(str(valve_data.iloc[kv_min_idx]['minT']))
        self.ui.inlet_size_mm.setText(str(valve_data.iloc[kv_min_idx]['inlet_size_mm']))
        self.ui.inlet_size_inch.setText(str(valve_data.iloc[kv_min_idx]['inlet_size_inch']))
        self.ui.inlet_dia.setText(str(valve_data.iloc[kv_min_idx]['inlet_dia']))
        self.ui.outlet_size_mm.setText(str(valve_data.iloc[kv_min_idx]['outlet_size_mm']))
        self.ui.outlet_size_inch.setText(str(valve_data.iloc[kv_min_idx]['outlet_size_inch']))
        self.ui.outlet_dia.setText(str(valve_data.iloc[kv_min_idx]['outlet_dia']))
        self.ui.connect_recommand.setText(valve_data.iloc[kv_min_idx]['connect_recommand'])
        self.ui.connect_possible.setText(valve_data.iloc[kv_min_idx]['connect_possible'])
        
        if layout_type == 'cas' or layout_type == 'inj':
            valve_data.drop(['Kv_diff'],axis = 1)
            valve_data['Kv_diff'] = abs(valve_data['Kv']*0.6-Kv_top)
            valve_data_t = valve_data[(valve_data['maxdP'] > maxdP_top) & (valve_data['maxP'] > maxP_top) & (valve_data['maxT'] > maxT_top) & (valve_data['minT'] < minT_top)]
            kv_min_idx = valve_data_t['Kv_diff'].idxmin()
            self.ui.bot_top_tab.setTabText(0, '밸브스펙(Bot)')
            self.ui.bot_top_tab.setTabText(1, '밸브스펙(Top)')
            self.ui.valve_top_fig.setPixmap(QPixmap(resource_path("DBs/valves/Figs/"+valve_data.iloc[kv_min_idx]['Fig']+".png")).scaledToHeight(220))
            self.ui.model_2.setText(valve_data.iloc[kv_min_idx]['Brand']+' '+valve_data.iloc[kv_min_idx]['Model'])
            self.ui.NS_2.setText(str(valve_data.iloc[kv_min_idx]['NS']))
            self.ui.Kv_2.setText(str(valve_data.iloc[kv_min_idx]['Kv']))
            self.ui.max_dp_2.setText(str(valve_data.iloc[kv_min_idx]['maxdP']))
            self.ui.max_p_2.setText(str(valve_data.iloc[kv_min_idx]['maxP']))
            self.ui.max_T_2.setText(str(valve_data.iloc[kv_min_idx]['maxT']))
            self.ui.min_T_2.setText(str(valve_data.iloc[kv_min_idx]['minT']))
            self.ui.inlet_size_mm_2.setText(str(valve_data.iloc[kv_min_idx]['inlet_size_mm']))
            self.ui.inlet_size_inch_2.setText(str(valve_data.iloc[kv_min_idx]['inlet_size_inch']))
            self.ui.inlet_dia_2.setText(str(valve_data.iloc[kv_min_idx]['inlet_dia']))
            self.ui.outlet_size_mm_2.setText(str(valve_data.iloc[kv_min_idx]['outlet_size_mm']))
            self.ui.outlet_size_inch_2.setText(str(valve_data.iloc[kv_min_idx]['outlet_size_inch']))
            self.ui.outlet_dia_2.setText(str(valve_data.iloc[kv_min_idx]['outlet_dia']))
            self.ui.connect_recommand_2.setText(valve_data.iloc[kv_min_idx]['connect_recommand'])
            self.ui.connect_possible_2.setText(valve_data.iloc[kv_min_idx]['connect_possible'])
            
        