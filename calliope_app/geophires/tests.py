import os
import datetime
import uuid
import numpy as np

from django.conf import settings
from django.test import TestCase

from geophires.v2 import Geophires, GeophiresParams


class GeophiresTestCase(TestCase):
    
    def test_geophires_run(self):
        start_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        plant = 'binary_subcritical'

        reservoir_heat_capacity: float
        reservoir_density: float
        reservoir_thermal_conductivity: float
        gradient: float
        min_temperature: int
        max_temperature: int
        min_reservoir_depth: float
        max_reservoir_depth: float
        min_production_wells: int
        max_production_wells: int
        min_injection_wells: int
        max_injection_wells: int
        
        ##depths
        depths = np.arange(1.0,5.0,0.1)
        depths = np.around(depths, decimals=1)

        ##wells
        wells_prod = np.arange(1.0,7.0,1)
        wells_prod = np.around(wells_prod, decimals=0)

        wells_inj = np.arange(1.0,7.0,1)
        wells_inj = np.around(wells_inj, decimals=0)

        ##Maximum Temperature
        temps = [200]
        temps = np.around(temps, decimals=0)

        ## Run
        input_params = GeophiresParams(
            reservoir_depths=depths,
            number_of_injection_wells=wells_prod,
            number_of_production_wells=wells_inj,
            max_temperatures=temps
        )

        template_id = '456'
        result_file = os.path.join(settings.DATA_STORAGE, f"{template_id}__{plant}__final_result__{start_time}.csv")
        
        geophiers = Geophires(plant)
        geophiers.run(input_params=input_params, output_file=result_file)
