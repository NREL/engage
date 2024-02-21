# -*- coding: utf-8 -*-
"""
@source: https://github.com/NREL/GEOPHIRES-X
@license: https://github.com/NREL/GEOPHIRES-X/blob/main/LICENSE

"""
import matplotlib.pyplot as plt
import numpy as np
import pprint

import engage_geophires_client
import engage_parametrization_visualization

import importlib
importlib.reload(engage_geophires_client)
importlib.reload(engage_parametrization_visualization)

from engage_geophires_client import *
from engage_parametrization_visualization import *


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
