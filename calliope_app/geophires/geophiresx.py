# -*- coding: utf-8 -*-
"""
@source: https://github.com/NREL/GEOPHIRES-X
@license: https://github.com/NREL/GEOPHIRES-X/blob/main/LICENSE

"""
import matplotlib.pyplot as plt
import numpy as np
import pprint
import os
from dataclasses import dataclass
from scipy.optimize import curve_fit
# import engage_geophires_client
# import engage_parametrization_visualization

import importlib
# importlib.reload(engage_geophires_client)
# importlib.reload(engage_parametrization_visualization)

# from engage_geophires_client import *
# from engage_parametrization_visualization import *
import logging

# Get an instance of a logger
logger = logging.getLogger('myapp')

################################## Added #################################
import pandas as pd
from geophires_x_client import GeophiresXClient
from geophires_x_client.geophires_input_parameters import GeophiresInputParameters




class geophires_parametrization_analysis:
    def __init__(self, prod_temp_min, prod_temp_max):
        self.client = GeophiresXClient()
        self.df_results = []
        self.parameter_list = []
        # self.plant = plant
        self.prod_min = prod_temp_min
        self.prod_max = prod_temp_max  # Corrected this line to properly set prod_max
        self.results_cache = {}  # Cache for storing results

    def get_value(self, results, keys):
        for key in keys:
            results = results.get(key, {})
            if not isinstance(results, dict):
                return None
        return results.get('value', None)

    def process_multiple(self, input_params):
        # Initialize data_row at the beginning of the method
        data_row = {}

        param_key = str(input_params)
        if param_key in self.results_cache:
            return self.results_cache[param_key]

        result = self.client.get_geophires_result(GeophiresInputParameters(input_params))
        all_results = result.result

        # Define paths for the values we're interested in
        paths = {
            'Depth (m)': ['ENGINEERING PARAMETERS', 'Well depth (or total length, if not vertical)'],
            'Number of Prod Wells': ['ENGINEERING PARAMETERS', 'Number of Production Wells'],
            'Number of Inj Wells': ['ENGINEERING PARAMETERS', 'Number of Injection Wells'],
            'Flow Rate per Prod Well (kg/sec)': ['ENGINEERING PARAMETERS', 'Flowrate per production well'],
            'Maximum Reservoir Temperature (deg.C)': ['RESOURCE CHARACTERISTICS', 'Maximum reservoir temperature'],
            'Surface Plant Cost ($M)': ['CAPITAL COSTS (M$)', 'Total surface equipment costs'],
            'Exploration Cost ($M)': ['CAPITAL COSTS (M$)', 'Exploration costs'],
            'Drilling and completion cost ($MUSD)': ['CAPITAL COSTS (M$)', 'Drilling and completion costs'],
            'Wellfield maintenance costs ($MUSD/yr)': [
                'OPERATING AND MAINTENANCE COSTS (M$/yr)',
                'Wellfield maintenance costs',
            ],
            'Make-Up Water O&M Cost ($MUSD/year)': ['OPERATING AND MAINTENANCE COSTS (M$/yr)', 'Water costs'],
            'Average Reservoir Heat Extraction (MWth)': [
                'RESERVOIR SIMULATION RESULTS',
                'Average Reservoir Heat Extraction',
            ],
            'Average Heat Production (MWth)': ['SURFACE EQUIPMENT SIMULATION RESULTS', 'Average Net Heat Production'],
            'Average Cool Production (MW)': ['SURFACE EQUIPMENT SIMULATION RESULTS', 'Average Cooling Production'],
            'Average Electricity Production (MWe)': [
                'SURFACE EQUIPMENT SIMULATION RESULTS',
                'Average Net Electricity Generation',
            ],
            'Lifetime': ['ECONOMIC PARAMETERS', 'Project lifetime'],
            'Total capital costs ($MUSD/yr)': ['CAPITAL COSTS (M$)', 'Total capital costs'],
            'Surface maintenance costs ($MUSD/yr)': [
                'OPERATING AND MAINTENANCE COSTS (M$/yr)',
                'Power plant maintenance costs',
            ],
            'Average Production Temperature (degC)': ['RESERVOIR SIMULATION RESULTS', 'Average Production Temperature'],
            'Maximum Total Electricity Generation (MWe)': [
                'SURFACE EQUIPMENT SIMULATION RESULTS',
                'Maximum Total Electricity Generation',
            ],
            'Maximum Cooling Production (MW)': ['SURFACE EQUIPMENT SIMULATION RESULTS', 'Maximum Cooling Production'],
            'Maximum Net Heat Production (MWth)': [
                'SURFACE EQUIPMENT SIMULATION RESULTS',
                'Maximum Net Heat Production',
            ],
        }

        # Extract values using the defined paths and update data_row
        for label, path in paths.items():
            value = self.get_value(all_results, path)
            print('============================================================')
            print(f'Extracting {label}: Found value {value}')
            print('============================================================')
            if value is not None:
                data_row[label] = value

        data_row = {k: v for k, v in data_row.items() if v is not None}
        self.results_cache[param_key] = data_row
        return data_row

    def run_iterations(self):
        for params in self.parameter_list:
            data_row = self.process_multiple(params)
            # Check if Average Production Temperature is within the specified range
            # avg_prod_temp = data_row.get('Average Production Temperature (degC)', None)
            # if avg_prod_temp is not None and self.prod_min <= avg_prod_temp <= self.prod_max:
                # self.df_results.append(data_row)
            # elif avg_prod_temp is not None and avg_prod_temp > self.prod_max:
            #     break  # Stop processing once the maximum temperature is reached
            self.df_results.append(data_row)

    def prepare_parameters(self, new_params_list):
        self.parameter_list = new_params_list

    def get_final_dataframe(self):
        return pd.DataFrame(self.df_results)


params = {
    "Reservoir Model": 1,
    "Reservoir Depth": 3,
    "Number of Segments": 1,
    "Gradient 1": 50,
    "Number of Production Wells": 2,
    "Number of Injection Wells": 2,
    "Production Well Diameter": 7,
    "Injection Well Diameter": 7,
    "Ramey Production Wellbore Model": 1,
    "Production Wellbore Temperature Drop": .5,
    "Injection Wellbore Temperature Gain": 0,
    "Production Flow Rate per Well": 55,
    "Fracture Shape": 3,
    "Fracture Height": 900,
    "Reservoir Volume Option": 3,
    "Number of Fractures": 20,
    "Reservoir Volume": 1000000000,
    "Water Loss Fraction": .02,
    "Productivity Index": 5,
    "Injectivity Index": 5,
    "Injection Temperature": 50,
    "Maximum Drawdown": 1,
    "Reservoir Heat Capacity": 1000,
    "Reservoir Density": 2700,
    "Reservoir Thermal Conductivity": 2.7,
    "End-Use Option": 1,
    "Power Plant Type": 2,
    "Circulation Pump Efficiency": .8,
    "Utilization Factor": .9,
    "Surface Temperature": 20,
    "Ambient Temperature": 20,
    "Plant Lifetime": 30,
    "Economic Model": 1,
    "Fixed Charge Rate": .05,
    "Inflation Rate During Construction": 0,
    "Well Drilling and Completion Capital Cost Adjustment Factor": 1,
    "Well Drilling Cost Correlation": 1,
    "Reservoir Stimulation Capital Cost Adjustment Factor": 1,
    "Surface Plant Capital Cost Adjustment Factor": 1,
    "Field Gathering System Capital Cost Adjustment Factor": 1,
    "Exploration Capital Cost Adjustment Factor": 1,
    "Wellfield O&M Cost Adjustment Factor": 1,
    "Surface Plant O&M Cost Adjustment Factor": 1,
    "Water Cost Adjustment Factor": 1,
    "Print Output to Console": 1,
    "Time steps per year": 6
}


base_params = {'HYDRO_chp': {
        'Reservoir Model': 4,
        'Drawdown Parameter': 0.003,
        'Number of Segments': 1,
        'Gradient 1': 55,
        'Maximum Temperature': 400,
        'Production Well Diameter': 8.5,
        'Injection Well Diameter': 8.5,
        'Ramey Production Wellbore Model': 0,
        'Production Wellbore Temperature Drop': 5,
        'Injection Wellbore Temperature Gain': 3,
        'Reservoir Volume Option': 1,
        'Injectivity Index': 5,
        'Injection Temperature': 70,
        'Maximum Drawdown': 1,
        'Reservoir Heat Capacity': 1000,
        'Reservoir Density': 3000,
        'Reservoir Thermal Conductivity': 3,
        'Water Loss Fraction': 0.02,
        'End-Use Option': 31,
        'Power Plant Type': 1,
        'Circulation Pump Efficiency': 0.80,
        'Plant Lifetime': 30,
        'Well Drilling Cost Correlation': 10,               
        'Print Output to Console': 0
    },
}
############################################################################

from django.conf import settings

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "configs")

def objective(x, a, b):
    """A simple objective function"""
    return a * x + b

@dataclass
class GeophiresParams:
    reservoir_heat_capacity: float
    reservoir_density: float
    reservoir_thermal_conductivity: float
    gradient: float

    # max temperature
    min_temperature: int
    max_temperature: int
    temperature_step: float

    # reservoir depth
    min_reservoir_depth: float
    max_reservoir_depth: float
    reservoir_depth_step: float

    # production wells should
    min_production_wells: int
    max_production_wells: int
    production_wells_step: int

    # Injection wells
    min_injection_wells: int
    max_injection_wells: int
    injection_wells_step: int


class Geophires(object):

    def __init__(self, plant):
        if plant not in GEO_TEMPLATE_FILES:
            names = GEO_TEMPLATE_FILES.keys()
            raise Exception(
                f"Plant '{plant}' is not supported, available plant types are: {names}"
            )
        self.plant = plant
        self.template_file = GEO_TEMPLATE_FILES[self.plant]
        self.template_data = self.get_template_data(self.template_file)
        self.results = {"data": [], "params": {}}

    def get_template_data(self, template_file):
        """Read template into dictionary."""
        with open(template_file, "r") as f:
            template_data = f.readlines()
        return template_data

    def run(self, input_params, output_file):
        logger.info("_______________Stuff______________")
        logger.info(input_params)
        config_files = self.generate_config_files(input_params)
        for filelike in config_files:
            self._perform_run(filelike)

        # Export xlsx result file
        if self.plant == 'direct_use':
            df_final = pd.DataFrame(self.results["data"], columns = [
                'Depth (m)',
                'Number of Prod/Inj Wells',
                'Wellfield Cost ($M)',
                'Surface Plant Cost ($M)',
                'Exploration Cost ($M)',
                'Field Gathering System Cost ($M)',
                'Wellfield O&M Cost ($M/year)',
                'Surface Plant O&M Cost ($M/year)',
                'Make-Up Water O&M Cost ($M/year)',
                'Average Reservoir Heat Extraction (MWth)',
                'Maximum reservoir temperature (deg.C)',
                # 'Average Total Electricity Generation (MWe)',
                "Efficiency",                                   ####ADDEDD
                "Interest Rate",                                ####ADDEDD
                "Lifetime"                                      ####ADDEDD
            ])

            df_final = df_final.sort_values(by=[
                'Depth (m)',
                'Number of Prod/Inj Wells'
            ], ascending=[True, True])

            df_final.to_csv(output_file, index=False, encoding='utf-8')

        else:
            df_final = pd.DataFrame(self.results["data"], columns = [
                'Depth (m)',
                'Number of Prod Wells',
                'Number of Inj Wells',
                'Maximum Reservoir Temperature (deg.C)',
                'Wellfield Cost ($M)',
                'Surface Plant Cost ($M)',
                'Exploration Cost ($M)',
                'Field Gathering System Cost ($M)',
                'Wellfield O&M Cost ($M/year)',
                'Surface Plant O&M Cost ($M/year)',
                'Make-Up Water O&M Cost ($M/year)',
                'Average Reservoir Heat Extraction (MWth)',
                'Average Total Electricity Generation (MWe)',
                "Efficiency",                                   ####ADDEDD
                "Interest Rate",                                ####ADDEDD
                "Lifetime"                                      ####ADDEDD
            ])

            df_final = df_final.sort_values(by=[
                'Depth (m)',
                'Number of Prod Wells'
            ], ascending=[True, True])

            df_final.to_csv(output_file, index=False, encoding='utf-8')

        ########################################
        ######### Mapping of Variable ##########
        ########################################
        df_line = df_final
        df_line = df_line.append(pd.Series(0, index=df_line.columns), ignore_index=True)

        max_e_cap               = np.max(df_line['Average Total Electricity Generation (MWe)'])     ####ADDEDD
        max_h_cap               = np.max(df_line['Average Reservoir Heat Extraction (MWth)'])       ####ADDEDD
        plant_efficiency        = float(np.average(df_line['Efficiency']))                          ####ADDEDD
        lifecycle               = int(df_line['Lifetime'][1])                                       ####ADDEDD
        rate                    = float(df_line['Interest Rate'][1])                                ####ADDEDD

        thermal_capacity         = np.array(df_line['Average Reservoir Heat Extraction (MWth)'])
        electric_capacity        =  np.array(df_line['Average Total Electricity Generation (MWe)'])
        subsurface_cost          = np.add(np.array(df_line['Wellfield Cost ($M)']), np.array(df_line['Field Gathering System Cost ($M)']))
        surface_cost             = np.array(df_line['Surface Plant Cost ($M)'])
        subsurface_o_m_cost      = np.add(np.array(df_line['Wellfield O&M Cost ($M/year)']), np.array(df_line['Make-Up Water O&M Cost ($M/year)']))
        surface_o_m_cost         = np.array(df_line['Surface Plant O&M Cost ($M/year)'])

        x1              = thermal_capacity
        y1              = subsurface_cost
        popt, _         = curve_fit(objective, x1, y1)
        a1, b1          = popt  #slope of line

        x2              = electric_capacity
        y2              = surface_cost
        popt, _         = curve_fit(objective, x2, y2)
        a2, b2          = popt #a2 slope of the line

        x3              = thermal_capacity
        y3              = subsurface_o_m_cost
        popt, _         = curve_fit(objective, x3, y3)
        a3, b3         = popt

        x4              = electric_capacity #Raw
        y4              = surface_o_m_cost  #raw
        popt, _         = curve_fit(objective, x4, y4)
        a4, b4         = popt

        ####    Supply(Subsurface) + Conversion (Surface)
        ####    Supply Carrier (Thermal)
        ####    Conversion Input Carrier (Thermal) -> Output Carrier (Power)

        output_params = dict(
            max_electricity_cap                     = max_e_cap,                       ### [MW] Conversion (Surface)                   ->     Maximum production capacity
            surface_plant_efficiency                = plant_efficiency,                ### [%] Conversion (Surface)                    ->     Conversion Efficiency (instead of c-rate)
            surface_cost_to_electric_slope          = a2,                              ### [$/MW] Conversion (Surface)                   ->     Cost of Production Capacity
            surface_om_cost_to_electric_slope       = a3,                              ### [$/MW] Conversion (Surface)                   ->     Annual Fixed O&M Cost

            max_heat_cap                            = max_h_cap,                       ### [MW] Supply     (Subsurface)                ->     Maximum production capacity
            subsurface_cost_to_thermal_slope        = a1,                              ### [$/MW] Supply     (Subsurface)                ->     Cost of Production Capacity
            subsurface_om_cost_to_thermal_slope     = a4,                              ### [$/MW] Supply     (Subsurface)                ->     Annual Fixed O&M Cost
            interest_rate                           = rate*100,                        ### [%] maps to both conversion and supply      ->     Interest rate
            lifetime                                = lifecycle                        ### [years] maps to both conversion and supply  ->     Lifetime and amortization period
        )

        ########################################
        ########################################
        print(output_params, output_file)
        return output_params, output_file
