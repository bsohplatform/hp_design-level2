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
    def __init__(self, Qbot, maxdP_bot, maxP_bot, maxT_bot, minT_bot, Kv_bot, Qtop, maxdP_top, maxP_top, maxT_top, minT_top, Kv_top, layout_type):
        super().__init__()
        loader = QUiLoader()
        ui_file = QFile(resource_path('VALVE.ui'))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()
        
        self.setCentralWidget(self.ui)
        self.ui.show()
        
        self.setWindowTitle("VALVE_RECOMMANDATION")
        
        margin = 1.15
        
        maxdP_bot = maxdP_bot*margin/1.0e5
        maxP_bot = maxP_bot*margin/1.0e5
        maxT_bot = maxT_bot*margin - 273.15
        minT_bot = minT_bot/margin - 273.15
        minQ_bot = Qbot/1.0e3*0.15
        maxQ_bot = 2*Qbot/1.0e3-minQ_bot
        Kv_bot = Kv_bot*margin
        maxdP_top = maxdP_top*margin/1.0e5
        maxP_top = maxP_top*margin/1.0e5
        maxT_top = maxT_top*margin - 273.15
        minT_top = minT_top/margin - 273.15
        minQ_top = Qtop/1.0e3*0.15
        maxQ_top = 2*Qtop/1.0e3-minQ_top
        Kv_top = Kv_top*margin
        
        valve_data = pd.read_csv(resource_path('DBs/valves/Danfoss_Valve.csv'),encoding='cp949')
        bb = valve_data[(valve_data['minQ'] < minQ_bot) & (valve_data['maxQ'] > maxQ_bot) & (valve_data['maxdP'] > maxdP_bot) & (valve_data['maxP'] > maxP_bot) & (valve_data['maxT'] > maxT_bot) & (valve_data['minT'] < minT_bot)]
        bb['valve_score'] = ((valve_data['minQ']-minQ_bot)/valve_data['minQ'])**2+((valve_data['maxQ']-maxQ_bot)/valve_data['maxQ'])**2+((bb['maxdP']-maxdP_bot)/bb['maxdP'])**2+((bb['maxP']-maxP_bot)/bb['maxP'])**2+((bb['maxT']-maxT_bot)/bb['maxT'])**2+((minT_bot-bb['minT'])/bb['minT'])**2
        
        kv_min_idx = bb['valve_score'].idxmin()
        self.ui.valve_bot_fig.setPixmap(QPixmap(resource_path("DBs/valves/Figs/"+valve_data.iloc[kv_min_idx]['Fig']+".png")).scaledToHeight(220))
        self.ui.model.setText(valve_data.iloc[kv_min_idx]['Brand']+' '+valve_data.iloc[kv_min_idx]['Model'])
        self.ui.NS.setText(str(valve_data.iloc[kv_min_idx]['minQ']))
        self.ui.Kv.setText(str(valve_data.iloc[kv_min_idx]['maxQ']))
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
            tt = valve_data[(valve_data['minQ'] < minQ_top) & (valve_data['maxQ'] > maxQ_top) & (valve_data['maxdP'] > maxdP_top) & (valve_data['maxP'] > maxP_top) & (valve_data['maxT'] > maxT_top) & (valve_data['minT'] < minT_top)]
            tt['valve_score'] = ((valve_data['minQ']-minQ_top)/valve_data['minQ'])**2+((valve_data['maxQ']-maxQ_top)/valve_data['maxQ'])**2+((tt['maxdP']-maxdP_top)/tt['maxdP'])**2+((tt['maxP']-maxP_top)/tt['maxP'])**2+((tt['maxT']-maxT_top)/tt['maxT'])**2+((minT_top-tt['minT'])/tt['minT'])**2
            
            kv_min_idx = tt['valve_score'].idxmin()
            self.ui.bot_top_tab.setTabText(0, '밸브스펙(Bot)')
            self.ui.bot_top_tab.setTabText(1, '밸브스펙(Top)')
            self.ui.valve_top_fig.setPixmap(QPixmap(resource_path("DBs/valves/Figs/"+valve_data.iloc[kv_min_idx]['Fig']+".png")).scaledToHeight(220))
            self.ui.model_2.setText(valve_data.iloc[kv_min_idx]['Brand']+' '+valve_data.iloc[kv_min_idx]['Model'])
            self.ui.NS_2.setText(str(valve_data.iloc[kv_min_idx]['minQ [kW]']))
            self.ui.Kv_2.setText(str(valve_data.iloc[kv_min_idx]['maxQ [kW]']))
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
            
        