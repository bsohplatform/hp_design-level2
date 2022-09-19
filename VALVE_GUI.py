import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic
import pandas as pd

form_class = uic.loadUiType("VALVE.ui")[0]


class valveWindow(QMainWindow, form_class):
    def __init__(self, maxdP_bot, maxP_bot, maxT_bot, minT_bot, Kv_bot, maxdP_top, maxP_top, maxT_top, minT_top, Kv_top, layout_type):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("VALVE_RECOMMANDATION")
        
        maxdP_bot = maxdP_bot/1.0e5
        maxP_bot = maxP_bot/1.0e5
        maxT_bot = maxT_bot - 273.15
        minT_bot = minT_bot - 273.15
        maxdP_top = maxdP_top/1.0e5
        maxP_top = maxP_top/1.0e5
        maxT_top = maxT_top - 273.15
        minT_top = minT_top - 273.15
        
        valve_data = pd.read_csv('.\DBs\\valves\Danfoss_Valve.csv',encoding='cp949')
        valve_data['Kv_diff'] = abs(valve_data['Kv']*0.6-Kv_bot)
        valve_data_b = valve_data[(valve_data['maxdP'] > maxdP_bot) & (valve_data['maxP'] > maxP_bot) & (valve_data['maxT'] > maxT_bot) & (valve_data['minT'] < minT_bot)]
        kv_min_idx = valve_data_b['Kv_diff'].idxmin()
        self.valve_bot_fig.setPixmap(QPixmap(".\DBs\\valves\Figs\\"+valve_data.iloc[kv_min_idx]['Fig']+".png").scaledToHeight(220))
        self.model.setText(valve_data.iloc[kv_min_idx]['Brand']+' '+valve_data.iloc[kv_min_idx]['Model'])
        self.NS.setText(str(valve_data.iloc[kv_min_idx]['NS']))
        self.Kv.setText(str(valve_data.iloc[kv_min_idx]['Kv']))
        self.max_dp.setText(str(valve_data.iloc[kv_min_idx]['maxdP']))
        self.max_p.setText(str(valve_data.iloc[kv_min_idx]['maxP']))
        self.max_T.setText(str(valve_data.iloc[kv_min_idx]['maxT']))
        self.min_T.setText(str(valve_data.iloc[kv_min_idx]['minT']))
        self.inlet_size_mm.setText(str(valve_data.iloc[kv_min_idx]['inlet_size_mm']))
        self.inlet_size_inch.setText(str(valve_data.iloc[kv_min_idx]['inlet_size_inch']))
        self.inlet_dia.setText(str(valve_data.iloc[kv_min_idx]['inlet_dia']))
        self.outlet_size_mm.setText(str(valve_data.iloc[kv_min_idx]['outlet_size_mm']))
        self.outlet_size_inch.setText(str(valve_data.iloc[kv_min_idx]['outlet_size_inch']))
        self.outlet_dia.setText(str(valve_data.iloc[kv_min_idx]['outlet_dia']))
        self.connect_recommand.setText(valve_data.iloc[kv_min_idx]['connect_recommand'])
        self.connect_possible.setText(valve_data.iloc[kv_min_idx]['connect_possible'])
        
        if layout_type == 'cas' or layout_type == 'inj':
            valve_data.drop(['Kv_diff'],axis = 1)
            valve_data['Kv_diff'] = abs(valve_data['Kv']*0.6-Kv_top)
            valve_data_t = valve_data[(valve_data['maxdP'] > maxdP_top) & (valve_data['maxP'] > maxP_top) & (valve_data['maxT'] > maxT_top) & (valve_data['minT'] < minT_top)]
            kv_min_idx = valve_data_t['Kv_diff'].idxmin()
            self.bot_top_tab.setTabText(0, '밸브스펙(Bot)')
            self.bot_top_tab.setTabText(1, '밸브스펙(Top)')
            self.valve_top_fig.setPixmap(QPixmap(".\DBs\\valves\Figs\\"+valve_data.iloc[kv_min_idx]['Fig']+".png").scaledToHeight(220))
            self.model_2.setText(valve_data.iloc[kv_min_idx]['Brand']+' '+valve_data.iloc[kv_min_idx]['Model'])
            self.NS_2.setText(str(valve_data.iloc[kv_min_idx]['NS']))
            self.Kv_2.setText(str(valve_data.iloc[kv_min_idx]['Kv']))
            self.max_dp_2.setText(str(valve_data.iloc[kv_min_idx]['maxdP']))
            self.max_p_2.setText(str(valve_data.iloc[kv_min_idx]['maxP']))
            self.max_T_2.setText(str(valve_data.iloc[kv_min_idx]['maxT']))
            self.min_T_2.setText(str(valve_data.iloc[kv_min_idx]['minT']))
            self.inlet_size_mm_2.setText(str(valve_data.iloc[kv_min_idx]['inlet_size_mm']))
            self.inlet_size_inch_2.setText(str(valve_data.iloc[kv_min_idx]['inlet_size_inch']))
            self.inlet_dia_2.setText(str(valve_data.iloc[kv_min_idx]['inlet_dia']))
            self.outlet_size_mm_2.setText(str(valve_data.iloc[kv_min_idx]['outlet_size_mm']))
            self.outlet_size_inch_2.setText(str(valve_data.iloc[kv_min_idx]['outlet_size_inch']))
            self.outlet_dia_2.setText(str(valve_data.iloc[kv_min_idx]['outlet_dia']))
            self.connect_recommand_2.setText(valve_data.iloc[kv_min_idx]['connect_recommand'])
            self.connect_possible_2.setText(valve_data.iloc[kv_min_idx]['connect_possible'])
            
        