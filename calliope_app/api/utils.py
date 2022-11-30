"""
This module contains support functions and libraries used in views and tasks.
"""

import json
import logging
import os
import shutil
from datetime import datetime
from itertools import permutations

import yaml
import pandas as pd
import numpy as np
from django.db.models import Func, Value
from django.utils.timezone import make_aware
import pint


CALLIOPE = 18
logging.addLevelName(CALLIOPE, "CALLIOPE")
logger = logging.getLogger("calliope")


def get_model_logger(log_file):
    """
    Get logger for logging model run info or errors

    :param log_file:
    :return: logger
    """
    logging.basicConfig(level=logging.INFO,
                        format="[%(asctime)s] %(levelname)s: %(message)s")
    if logger.handlers:
        logger.removeHandler(logger.handlers[0])

    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s<br>",
        datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(CALLIOPE)

    return logger


def dateformats():
    """
    Yield common combinations of valid datetime formats.
    """

    years = ("%Y", "%y",)
    months = ("%m", "%b", "%B",)
    days = ("%d",)
    times = (
        "%H:%M", "%H:%M:%S", "%I:%M%p", "%I:%M:%S%p",
        "%I:%M %p", "%I:%M:%S %p", "%I%p")

    for year in years:
        for month in months:
            for day in days:
                date_orders = ((year, month, day), (month, day, year),
                               (day, month, year), (month, day), (day, month))
                for args in date_orders:
                    for sep in (" ", "/", "-"):
                        date = sep.join(args)
                        for time in times:
                            for combo in permutations([date, time]):
                                yield " ".join(combo).strip()


def get_date_format(string):
    """
    Detect datetime.strptime format or None from a string.
    from http://code.activestate.com/recipes/578245-flexible-datetime-parsing/
    """

    for fmt in dateformats():
        try:
            datetime.strptime(string, fmt)
            return fmt
        except ValueError:
            pass

    return None


def zip_folder(path, keep_folder=True):
    """
    Zip contents of folder

    Parameters
    ----------
    path : str
        folder path to be zipped
    """
    zip_file = path + ".zip"
    if not os.path.exists(zip_file):
        root_dir = os.path.dirname(path)
        base_dir = "./" + os.path.basename(path)
        shutil.make_archive(path, "zip", root_dir, base_dir=base_dir)

    if not keep_folder:
        shutil.rmtree(path)

    return zip_file


def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict
    """

    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def list_to_yaml(table_list, filename):
    """
    Convert a list of strings to YAML file format
    DEPRECATED: The YAML creation code was refactored to write directly to a dict
    """

    X = [x[0].split('||') for x in table_list]
    timeseries = [x[1] for x in table_list]
    d = {}
    for index in range(len(X)):
        path = X[index]
        current_level = d
        for i, part in enumerate(path):
            if i < (len(path) - 1):
                if i == (len(path) - 2):
                    if timeseries[index] is True:
                        parameter = path[i]
                        technology = path[i - 2]
                        if (i - 4 > 0):
                            location = path[i - 4]
                            current_level[part] = \
                                "file={}--{}--{}.csv:value".format(
                                    location, technology, parameter)
                        else:
                            current_level[part] = \
                                "file={}--{}.csv:value".format(
                                    technology, parameter)
                    elif path[i + 1] == "":
                        current_level[part] = None
                    elif path[i + 1] == 'True':
                        current_level[part] = True
                    elif path[i + 1] == 'False':
                        current_level[part] = False
                    else:
                        try:
                            string = path[i + 1].replace(", ", ",")
                            for char in ['\'', '“', '”', '‘', '’']:
                                string = string.replace(char, '\"')
                            current_level[part] = json.loads(string)
                        except Exception:
                            try:
                                current_level[part] = float(path[i + 1])
                            except ValueError:
                                current_level[part] = path[i + 1]
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
    with open(filename, 'w') as outfile:
        yaml.dump(d, outfile, default_flow_style=False)
        return True


def get_cols_from_csv(filename):
    """
    Read the columns from a csv
    """

    df = pd.read_csv(filename)
    return df.columns


def load_timeseries_from_csv(filename, t_index, v_index, has_header=False):
    """
    Build a timeseries as a pandas dataframe from a csv file
    """

    t_index = int(t_index)
    v_index = int(v_index)
    date_format = None  # just use pd.to_datetime if None
    df = pd.DataFrame()

    # Cache date format for large files (sample 20th row):
    if filename.size > 2e6:  # 2 MB
        read_df = pd.read_csv(filename.path, header=None, skiprows=20,
                              usecols=[t_index, v_index],
                              skipinitialspace=True, nrows=1)
        test_date = read_df.iloc[0, t_index]
        date_format = get_date_format(test_date)

    # Load Full Data
    skiprows = 0
    if has_header:
        skiprows = 1
    read_df = pd.read_csv(filename.path, header=None, skiprows=skiprows,
                          usecols=[t_index, v_index],
                          skipinitialspace=True, chunksize=100000)

    # Convert to Timestamps
    for chunk_df in read_df:
        if date_format is None:
            # Slow: We didn't find the strptime format:
            chunk_dates = pd.to_datetime(chunk_df.loc[:, t_index])
        else:
            # Fast: Try using strptime
            try:
                chunk_dates = chunk_df[[t_index]].astype(str).iloc[:, 0].apply(
                    lambda x: make_aware(datetime.strptime(x, date_format)))
            except (ValueError, AttributeError):
                chunk_dates = pd.to_datetime(chunk_df.loc[:, t_index])

            chunk_df.iloc[:, t_index] = chunk_dates

        # Filter out NaN values
        chunk_df = chunk_df[pd.notnull(chunk_df)]
        chunk_df = chunk_df[pd.notnull(chunk_df)]

        df = df.append(chunk_df)

    # Clean
    df = df.set_index(t_index)
    df.index.name = 'datetime'
    df.columns = ['value']

    return df


def hourly_timeseries(df):
    """
    Set the timestamp and resample to hourly in a pandas dataframe
    """

    if type(df.index) is not pd.core.indexes.datetimes.DatetimeIndex:
        df.index = pd.to_datetime(df.index, utc=True)

    df = df.resample(rule='h').mean()
    df[np.isnan(df.value)] = 0
    return df


def pad_timeseries(df, start, end):
    """
    Add padding to a pandas dataframe timeseries

    start = '2019-01-01 00:00'
    end = '2019-01-02 00:00'
    """
    idx = pd.date_range(start=start, end=end, freq='h')
    ts = pd.DataFrame(index=idx)
    df = ts.join(df).fillna(0).reset_index()
    return df


class DateTrunc(Func):
    """
    To support using DATE_TRUNC('text', "field") in SQL

    Example::

        order_totals = (orders
            .annotate(
                period=DateTrunc('month', 'date_placed'),
            )
            .values("period")  # Needs to be in between for a correct GROUP_BY
            .order_by('period')
            .annotate(
                order_count=Count('id'),
                shipping_excl_tax=Sum('shipping_excl_tax'),
                shipping_incl_tax=Sum('shipping_incl_tax'),
            ))

    SQL DateTrunc function (for grouping by day, hour, month, etc.):
    https://gist.github.com/vdboor/f3ebe5e20c0882d39053
    """
    function = 'DATE_TRUNC'

    def __init__(self, trunc_type, field_expression, **extra):
        super(DateTrunc, self).__init__(
            Value(trunc_type), field_expression, **extra)

def initialize_units():
    ureg = pint.UnitRegistry()
    ureg.define('percent = 0.01 = percentage')
    ureg.define('MMBTU = 1000000 BTU = mmbtu = mbtu')
    ureg.define('Calorie = 1000 calorie = Calories')
    ureg.define('dollar = 1 = dollars')
    ureg.define('cent = .01 dollar = cent = cents')
    ureg.define('units = 1 = unit')

    return ureg

user_defined_units = [
  {
    "name": "Gravity[9.81m/s^2]",
    "value": "9.81 m/s^2"
  },
  {
    "name": "Fresh_Water_Density[1000kg/m^3]",
    "value": "1000 kg/m^3"
  },
  {
    "name": "Surface_Seawater_Density[1023.6kg/m^3]",
    "value": "1023.6 kg/m^3"
  },
  {
    "name": "Crude_Oil_Low_Volume_Energy[28MJ/L]",
    "value": "28 MJ/L"
  },
  {
    "name": "Crude_Oil_High_Volume_Energy[31.4MJ/L]",
    "value": "31.4 MJ/L"
  },
  {
    "name": "Dried_Plants_Low_Volume_Energy[1.6MJ/L]",
    "value": "1.6 MJ/L"
  },
  {
    "name": "Dried_Plants_High_Volume_Energy[16.64MJ/L]",
    "value": "16.64 MJ/L"
  },
  {
    "name": "Wood_Fuel_Low_Volume_Energy[2.56MJ/L]",
    "value": "2.56 MJ/L"
  },
  {
    "name": "Wood_Fuel_High_Volume_Energy[21.84MJ/L]",
    "value": "21.84 MJ/L"
  },
  {
    "name": "Pyrolysis_Oil_Volume_Energy[21.35MJ/L]",
    "value": "21.35 MJ/L"
  },
  {
    "name": "Methanol_Mass_Energy[15.9MJ/L]",
    "value": "15.9 MJ/L"
  },
  {
    "name": "Ethanol_Low_Volume_Energy[18.4MJ/L]",
    "value": "18.4 MJ/L"
  },
  {
    "name": "Ethanol_High_Volume_Energy[21.2MJ/L]",
    "value": "21.2 MJ/L"
  },
  {
    "name": "Ecalene_Volume_Energy[22.7MJ/L]",
    "value": "22.7 MJ/L"
  },
  {
    "name": "Butanol_Volume_Energy[29.2MJ/L]",
    "value": "29.2 MJ/L"
  },
  {
    "name": "Fat_Volume_Energy[31.68MJ/L]",
    "value": "31.68 MJ/L"
  },
  {
    "name": "Biodiesel_Low_Volume_Energy[33.3MJ/L]",
    "value": "33.3 MJ/L"
  },
  {
    "name": "Biodiesel_High_Volume_Energy[35.7MJ/L]",
    "value": "35.7 MJ/L"
  },
  {
    "name": "Sunflower_Oil_Volume_Energy[33.18MJ/L]",
    "value": "33.18 MJ/L"
  },
  {
    "name": "Castor_Oil_Volume_Energy[33.21MJ/kg]",
    "value": "33.21 MJ/kg"
  },
  {
    "name": "Olive_Oil_Low_Volume_Energy[33.00MJ/L]",
    "value": "33.00 MJ/L"
  },
  {
    "name": "Olive_Oil_High_Volume_Energy[33.48MJ/L]",
    "value": "33.48 MJ/L"
  },
  {
    "name": "Methane_Liquified_Low_Volume_Energy[23.00MJ/L]",
    "value": "23.00 MJ/L"
  },
  {
    "name": "Methane_Liquified_High_Volume_Energy[23.3MJ/L]",
    "value": "23.3 MJ/L"
  },
  {
    "name": "Hydrogen__Liquified_Low_Volume_Energy[8.5MJ/L]",
    "value": "8.5 MJ/L"
  },
  {
    "name": "Hydrogen_Liquified_High_Volume_Energy[10.1MJ/L]",
    "value": "10.1 MJ/L"
  },
  {
    "name": "Coal_Low_Volume_Energy[39.85MJ/L]",
    "value": "39.85 MJ/L"
  },
  {
    "name": "Coal_High_Volume_Energy[74.43MJ/L]",
    "value": "74.43 MJ/L"
  },
  {
    "name": "Gasoline_Low_Volume_Energy[32MJ/L]",
    "value": "32 MJ/L"
  },
  {
    "name": "Gasoline_High_Volume_Energy[34.8MJ/L]",
    "value": "34.8 MJ/L"
  },
  {
    "name": "Diesel_Volume_Energy[40.3MJ/L]",
    "value": "40.3 MJ/L"
  },
  {
    "name": "Natural_Gas_Liquified_Low_Volume_Energy[25.5MJ/L]",
    "value": "25.5 MJ/L"
  },
  {
    "name": "Natural_Gas_Liquified_High_Volume_Energy[28.7MJ/L]",
    "value": "28.7 MJ/L"
  },
  {
    "name": "Ethane_Liquified_Volume_Energy[24MJ/L]",
    "value": "24 MJ/L"
  },
  {
    "name": "Propane_Lpg_Volume_Energy[91330BTU/gal]",
    "value": "91330 BTU/gal"
  },
  {
    "name": "Propane_Gas_60_Deg_Volume_Energy[2550/ft^3]",
    "value": "2550/ft^3"
  },
  {
    "name": "Butane_Volume_Energy[3200BTU/ft^3]",
    "value": "3200 BTU/ft^3"
  },
  {
    "name": "Fuel_Oil_No_1_Volume_Energy[137400BTU/gal]",
    "value": "137400 BTU/gal"
  },
  {
    "name": "Fuel_Oil_No_2_Volume_Energy[139600BTU/gal]",
    "value": "139600 BTU/gal"
  },
  {
    "name": "Fuel_Oil_No_3_Volume_Energy[141800BTU/gal]",
    "value": "141800 BTU/gal"
  },
  {
    "name": "Fuel_Oil_No_4_Volume_Energy[145100BTU/gal]",
    "value": "145100 BTU/gal"
  },
  {
    "name": "Fuel_Oil_No_5_Volume_Energy[148800BTU/gal]",
    "value": "148800 BTU/gal"
  },
  {
    "name": "Fuel_Oil_No_6_Volume_Energy[152400BTU/gal]",
    "value": "152400 BTU/gal"
  },
  {
    "name": "Heating_Oil_Volume_Energy[139000BTU/gal]",
    "value": "139000 BTU/gal"
  },
  {
    "name": "Kerosene_Volume_Energy[135000BTU/gal]",
    "value": "135000 BTU/gal"
  },
  {
    "name": "Residual_Fuel_Oil_Volume_Energy[6287000BTU/oilbarrel]",
    "value": "6287000 BTU/oilbarrel"
  },
  {
    "name": "Bagasse_Cane_Stalk_Mass_Energy[9.6MJ/kg]",
    "value": "9.6 MJ/kg"
  },
  {
    "name": "Chaff_Seed_Casings_Mass_Energy[14.6MJ/kg]",
    "value": "14.6 MJ/kg"
  },
  {
    "name": "Animal_Dung_Manure_Low_Mass_Energy[10MJ/kg]",
    "value": "10 MJ/kg"
  },
  {
    "name": "Animal_Dung_Manure_High_Mass_Energy[15MJ/kg]",
    "value": "15 MJ/kg"
  },
  {
    "name": "Dried_Plants_Low_Mass_Energy[10MJ/kg]",
    "value": "10 MJ/kg"
  },
  {
    "name": "Dried_Plants_High_Mass_Energy[16MJ/kg]",
    "value": "16 MJ/kg"
  },
  {
    "name": "Wood_Fuel_Low_Mass_Energy[16MJ/kg]",
    "value": "16 MJ/kg"
  },
  {
    "name": "Wood_Fuel_High_Mass_Energy[21MJ/kg]",
    "value": "21 MJ/kg"
  },
  {
    "name": "Charcoal_Mass_Energy[30MJ/kg]",
    "value": "30 MJ/kg"
  },
  {
    "name": "Dry_Cow_Dung_Mass_Energy[15MJ/kg]",
    "value": "15 MJ/kg"
  },
  {
    "name": "Dry_Wood_Mass_Energy[19MJ/kg]",
    "value": "19 MJ/kg"
  },
  {
    "name": "Pyrolysis_Oil_Mass_Energy[17.5MJ/kg]",
    "value": "17.5 MJ/kg"
  },
  {
    "name": "Methanol_Low_Mass_Energy[19.9MJ/kg]",
    "value": "19.9 MJ/kg"
  },
  {
    "name": "Methanol_High_Mass_Energy[22.7MJ/kg]",
    "value": "22.7 MJ/kg"
  },
  {
    "name": "Ethanol_Low_Mass_Energy[23.4MJ/kg]",
    "value": "23.4 MJ/kg"
  },
  {
    "name": "Ethanol_High_Mass_Energy[26.8MJ/kg]",
    "value": "26.8 MJ/kg"
  },
  {
    "name": "Ecalene_Mass_Energy[28.4MJ/kg]",
    "value": "28.4 MJ/kg"
  },
  {
    "name": "Butanol_Mass_Energy[36MJ/kg]",
    "value": "36 MJ/kg"
  },
  {
    "name": "Fat_Mass_Energy[37.656MJ/kg]",
    "value": "37.656 MJ/kg"
  },
  {
    "name": "Biodiesel_Mass_Energy[37.8MJ/kg]",
    "value": "37.8 MJ/kg"
  },
  {
    "name": "Sunflower_Oil_Mass_Energy[39.49MJ/kg]",
    "value": "39.49 MJ/kg"
  },
  {
    "name": "Castor_Oil_Mass_Energy[39.5MJ/kg]",
    "value": "39.5 MJ/kg"
  },
  {
    "name": "Olive_Oil_Low_Mass_Energy[39.25MJ/kg]",
    "value": "39.25 MJ/kg"
  },
  {
    "name": "Olive_Oil_High_Mass_Energy[39.82MJ/kg]",
    "value": "39.82 MJ/kg"
  },
  {
    "name": "Methane_Low_Mass_Energy[55.00MJ/kg]",
    "value": "55.00 MJ/kg"
  },
  {
    "name": "Methane_High_Mass_Energy[55.7MJ/kg]",
    "value": "55.7 MJ/kg"
  },
  {
    "name": "Hydrogen_Low_Mass_Energy[120MJ/kg]",
    "value": "120 MJ/kg"
  },
  {
    "name": "Hydrogen_High_Mass_Energy[142MJ/kg]",
    "value": "142 MJ/kg"
  },
  {
    "name": "Coal_Low_Mass_Energy[29.3MJ/kg]",
    "value": "29.3 MJ/kg"
  },
  {
    "name": "Coal_High_Mass_Energy[33.5MJ/kg]",
    "value": "33.5 MJ/kg"
  },
  {
    "name": "Crude_Oil_Mass_Energy[41.868MJ/kg]",
    "value": "41.868 MJ/kg"
  },
  {
    "name": "Gasoline_Low_Mass_Energy[45MJ/kg]",
    "value": "45 MJ/kg"
  },
  {
    "name": "Gasoline_High_Mass_Energy[48.3MJ/kg]",
    "value": "48.3 MJ/kg"
  },
  {
    "name": "Diesel_Mass_Energy[48.1MJ/kg]",
    "value": "48.1 MJ/kg"
  },
  {
    "name": "Natural_Gas_Low_Mass_Energy[38MJ/kg]",
    "value": "38 MJ/kg"
  },
  {
    "name": "Natural_Gas_High_Mass_Energy[50MJ/kg]",
    "value": "50 MJ/kg"
  },
  {
    "name": "Ethane_Mass_Energy[51.9MJ/kg]",
    "value": "51.9 MJ/kg"
  },
  {
    "name": "Household_Waste_Mass_Energy[9.5MJ/kg]",
    "value": "9.5 MJ/kg"
  },
  {
    "name": "Plastic_Mass_Energy[30MJ/kg]",
    "value": "30 MJ/kg"
  },
  {
    "name": "Car_Tires_Mass_Energy[35MJ/kg]",
    "value": "35 MJ/kg"
  },
  {
    "name": "Oil_Mass_Energy[2.4e7J/lbm]",
    "value": "2.4e7 J/lbm"
  },
  {
    "name": "Natural_Uranium_LWR_Mass_Energy[650GJ/kg]",
    "value": "650 GJ/kg"
  },
  {
    "name": "Natural_Uranium_FNR_Mass_Energy[28000GJ/kg]",
    "value": "28000 GJ/kg"
  },
  {
    "name": "Enriched_Uranium_LWR_Mass_Energy[3900GJ/kg]",
    "value": "3900 GJ/kg"
  },
  {
    "name": "Firewood_Mass_Energy[16MJ/kg]",
    "value": "16 MJ/kg"
  },
  {
    "name":"Therm[100,000 BTU]",
    "value":"100000 BTU"
  },
  {
    "name":"thm[100,000 BTU]",
    "value":"100000 BTU"
  },
  {
    "name":"cf[ft^3]",
    "value":"1 ft^3"
  },
  {
    "name":"Gasoline_Gallon_Equivalent[114,118.8 BTU]",
    "value":"114118.8 BTU"
  },
  {
    "name":"GGE[114,118.8 BTU]",
    "value":"114118.8 BTU"
  },
  {
    "name":"gge[114,118.8 BTU]",
    "value":"114118.8 BTU"
  }
]

def convert_units(ureg,val,target):
    ur_v = str(val).replace('%',' percent ').replace('$',' dollar ').replace('<sup>','^').replace('</sup>','')
    for u in user_defined_units:
        ur_v = ur_v.replace(u['name'],u['value'])
    ur_v = ureg.Quantity(ur_v)
    if str(ur_v.units) == 'dimensionless':
        if val != str(ur_v.magnitude):
            return str(ur_v.magnitude)+'||'+str(val)
        return str(ur_v.magnitude)
    else:
        conv_v = ur_v.to(target.replace('%',' percent ').replace('$',' dollar ')).magnitude
        return str(conv_v)+'||'+str(val)
    
noconv_units = ['<sub>ABC</sub>','<sup>T</sup>/<sub>F</sub>','&#8593;','']
