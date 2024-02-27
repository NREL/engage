import pandas as pd

from geophires_x_client import GeophiresXClient
from geophires_x_client.geophires_input_parameters import GeophiresInputParameters


class geophires_parametrization_analysis:
    def __init__(self, plant, prod_temp_min, prod_temp_max):
        self.client = GeophiresXClient()
        self.df_results = []
        self.parameter_list = []
        self.plant = plant
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

        # Attempt to extract efficiency directly
        # try:
        #     if 'POWER GENERATION PROFILE' in all_results:
        #         header_index = all_results['POWER GENERATION PROFILE'][0].index('FIRST LAW EFFICIENCY (%)')
        #         first_law_eff = all_results['POWER GENERATION PROFILE'][1][header_index]
        #         data_row['Efficiency (%)'] = first_law_eff
        #     else:
        #         data_row['Efficiency (%)'] = "N/A"
        # except (KeyError, ValueError, IndexError) as e:
        #     data_row['Efficiency (%)'] = "N/A"

        # # Attempt to extract reservoir heat content consideration
        # heat_content_key = 'HEAT AND/OR ELECTRICITY EXTRACTION AND GENERATION PROFILE'
        # if heat_content_key in all_results:
        #     negative_content_year = None
        #     for year_data in all_results[heat_content_key][1:]:  # Skip the header row
        #         year, *_, reservoir_heat_content = year_data
        #         if reservoir_heat_content < 0:
        #             negative_content_year = year
        #             break

        #     if negative_content_year:
        #         data_row['Year Reservoir Heat Content Turns Negative'] = negative_content_year
        #     else:
        #         data_row['Reservoir Heat Content Status'] = f"Does not run out"
        # else:
        #     data_row['Reservoir Heat Content Status'] = "N/A"

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
            avg_prod_temp = data_row.get('Average Production Temperature (degC)', None)
            if avg_prod_temp is not None and self.prod_min <= avg_prod_temp <= self.prod_max:
                self.df_results.append(data_row)
            elif avg_prod_temp is not None and avg_prod_temp > self.prod_max:
                break  # Stop processing once the maximum temperature is reached

    def prepare_parameters(self, new_params_list):
        self.parameter_list = new_params_list

    def get_final_dataframe(self):
        return pd.DataFrame(self.df_results)
    

inputer = {
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


obj = geophires_parametrization_analysis(1,400,1000)
obj.prepare_parameters(inputer)
t = obj.process_multiple(inputer)
obj.df_results

