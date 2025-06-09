# weather/utils.py
import openmeteo_requests
from openmeteo_sdk.Variable import Variable as SdkVariableEnum # For mapping
from openmeteo_sdk.Aggregation import Aggregation as SdkAggregationEnum
import requests_cache
from retry_requests import retry
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class WeatherAPIClient:
    ENSEMBLE_API_URL = "https://ensemble-api.open-meteo.com/v1/ensemble"
    DEFAULT_ENSEMBLE_MODELS = ["icon_seamless", "gfs_seamless", "ecmwf_ifs025"]
    BASE_API_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self):
        cache_session = requests_cache.CachedSession('.cache', expire_after=1800)
        retry_session = retry(cache_session, retries=3, backoff_factor=0.2)
        self.client = openmeteo_requests.Client(session=retry_session)
        logger.debug("WeatherAPIClient initialized.")

    def _map_string_to_sdk_var(self, var_string_name):
        name_lower = var_string_name.lower()
        if name_lower == "shortwave_radiation": return SdkVariableEnum.shortwave_radiation, 0
        if name_lower == "direct_normal_irradiance": return SdkVariableEnum.direct_normal_irradiance, 0
        if name_lower == "diffuse_radiation": return SdkVariableEnum.diffuse_radiation, 0
        if name_lower == "temperature_2m": return SdkVariableEnum.temperature, 2
        if name_lower.startswith("wind_speed_") and name_lower.endswith("m"):
            try:
                altitude_str = name_lower.split("_")[-1][:-1] # e.g., "80m" -> "80"
                altitude = int(altitude_str)
                logger.debug(f"_map_string_to_sdk_var: Parsed altitude {altitude} from {var_string_name}")
                return SdkVariableEnum.wind_speed, altitude
            except ValueError:
                logger.error(f"Could not parse altitude from wind_speed variable: {var_string_name}")
                return None, None
        logger.warning(f"Unmappable variable string in _map_string_to_sdk_var: {var_string_name}")
        return None, None


    def get_current_weather(self, latitude, longitude):
        current_params_list = [
            "temperature_2m", "relative_humidity_2m", "apparent_temperature", "is_day",
            "precipitation", "rain", "showers", "snowfall", "weather_code", "cloud_cover",
            "surface_pressure", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m", "uv_index",
            "visibility"
        ]
        params = {
            "latitude": latitude, "longitude": longitude, "current": current_params_list,
            "temperature_unit": "celsius", "wind_speed_unit": "ms",
            "precipitation_unit": "mm", "timezone": "auto"
        }
        logger.debug(f"Requesting current weather for ({latitude}, {longitude}) with params: {params}")

        processed_current_data = {param: None for param in current_params_list}
        processed_current_data["time"] = None
        processed_current_data["interval"] = None

        try:
            responses = self.client.weather_api(self.BASE_API_URL, params=params)
            response = responses[0]
            current_api_data = response.Current()

            if current_api_data is None:
                logger.warning(f"Open-Meteo API (current) did not return 'current' data for ({latitude}, {longitude})")
                return processed_current_data

            processed_current_data["time"] = pd.to_datetime(current_api_data.Time(), unit = "s", utc = True).isoformat()
            processed_current_data["interval"] = current_api_data.Interval()

            num_vars_returned = current_api_data.VariablesLength()
            for i in range(num_vars_returned):
                if i < len(current_params_list):
                    var_name_from_request = current_params_list[i]
                    sdk_variable_object = current_api_data.Variables(i)
                    value = sdk_variable_object.Value()

                    if isinstance(value, np.float32) and np.isnan(value):
                        processed_current_data[var_name_from_request] = None
                    elif isinstance(value, (int, float)) and np.isnan(value):
                         processed_current_data[var_name_from_request] = None
                    else:
                        if isinstance(value, (np.float32, np.float64)):
                            processed_current_data[var_name_from_request] = float(value)
                        else:
                            processed_current_data[var_name_from_request] = value
                else:
                    logger.warning(f"Index {i} out of bounds for current_params_list (len {len(current_params_list)}) but API returned more variables ({num_vars_returned}). This is unexpected.")

            logger.debug(f"Processed current weather for ({latitude}, {longitude}): {processed_current_data}")
            return processed_current_data

        except Exception as e:
            logger.error(f"Error in WeatherAPIClient.get_current_weather for ({latitude}, {longitude}): {e}", exc_info=True)
            return processed_current_data

    def get_forecast(self, latitude, longitude, daily_params=None, hourly_params=None, forecast_days=7):
        if daily_params is None: daily_params = []
        if hourly_params is None: hourly_params = []

        params = {
            "latitude": latitude, "longitude": longitude,
            "temperature_unit": "celsius", "wind_speed_unit": "ms",
            "precipitation_unit": "mm", "timezone": "auto",
            "forecast_days": forecast_days,
            "timeformat": "unixtime"
        }
        if daily_params:
            params["daily"] = daily_params
        if hourly_params:
            params["hourly"] = hourly_params

        if not daily_params and not hourly_params:
            logger.warning("get_forecast called with no daily or hourly params.")
            return {}

        logger.debug(f"Requesting forecast for ({latitude}, {longitude}) with params: {params}")

        processed_response = {}
        try:
            responses = self.client.weather_api(self.BASE_API_URL, params=params)
            response = responses[0]

            if daily_params and response.Daily() is not None:
                daily_api_data = response.Daily()
                if daily_api_data.VariablesLength() == 0 or daily_api_data.Variables(0).ValuesLength() == 0:
                    logger.warning(f"Daily forecast variables data is empty for ({latitude}, {longitude}).")
                    processed_response["daily"] = {"time": []}
                else:
                    num_days = daily_api_data.Variables(0).ValuesLength()
                    processed_daily_data = {"time": [
                        pd.to_datetime(daily_api_data.Time() + i * daily_api_data.Interval(), unit="s", utc=True).strftime('%Y-%m-%d')
                        for i in range(num_days)
                    ]}
                    for i in range(daily_api_data.VariablesLength()):
                        var_sdk = daily_api_data.Variables(i)
                        if i < len(daily_params):
                            var_name_in_list = daily_params[i]
                            values_numpy = var_sdk.ValuesAsNumpy()
                            processed_daily_data[var_name_in_list] = [None if np.isnan(v) else v for v in values_numpy.tolist()]
                        else:
                            logger.warning(f"Daily forecast: Index {i} out of bounds for daily_params.")
                    processed_response["daily"] = processed_daily_data
            elif daily_params:
                 processed_response["daily"] = {"time": []}


            if hourly_params and response.Hourly() is not None:
                hourly_api_data = response.Hourly()
                if hourly_api_data.VariablesLength() == 0 or hourly_api_data.Variables(0).ValuesLength() == 0:
                    logger.warning(f"Hourly forecast variables data is empty for ({latitude}, {longitude}).")
                    processed_response["hourly"] = {"time": []}
                else:
                    time_start_hourly = pd.to_datetime(hourly_api_data.Time(), unit="s", utc=True)
                    time_end_hourly = pd.to_datetime(hourly_api_data.TimeEnd(), unit="s", utc=True)
                    interval_seconds_hourly = hourly_api_data.Interval()

                    timestamps_pd_hourly = pd.date_range(
                        start=time_start_hourly, end=time_end_hourly,
                        freq=pd.Timedelta(seconds=interval_seconds_hourly), inclusive="left"
                    )
                    processed_hourly_timestamps = timestamps_pd_hourly.strftime('%Y-%m-%dT%H:%M:%SZ').tolist()

                    processed_hourly_data = {"time": processed_hourly_timestamps}
                    for i in range(hourly_api_data.VariablesLength()):
                        var_sdk = hourly_api_data.Variables(i)
                        if i < len(hourly_params):
                            var_name_in_list = hourly_params[i]
                            values_numpy = var_sdk.ValuesAsNumpy()
                            processed_hourly_data[var_name_in_list] = [None if np.isnan(v) else float(v) for v in values_numpy.tolist()]
                        else:
                            logger.warning(f"Hourly forecast: Index {i} out of bounds for hourly_params.")
                    processed_response["hourly"] = processed_hourly_data
            elif hourly_params:
                processed_response["hourly"] = {"time": []}

            logger.debug(f"Processed forecast for ({latitude}, {longitude})")
            return processed_response

        except Exception as e:
            logger.error(f"Error in WeatherAPIClient.get_forecast for ({latitude}, {longitude}): {e}", exc_info=True)
            error_response = {}
            if daily_params: error_response["daily"] = {"time": []}
            if hourly_params: error_response["hourly"] = {"time": []}
            return error_response


    def get_ensemble_hourly_data(self, latitude, longitude, hourly_vars, models=None, forecast_days=7):
        logger.info(f"get_ensemble_hourly_data called with: lat={latitude}, lon={longitude}, vars={hourly_vars}, models={models}, days={forecast_days}")
        if models is None:
            models = self.DEFAULT_ENSEMBLE_MODELS

        params = {
            "latitude": latitude, "longitude": longitude,
            "hourly": hourly_vars,
            "models": models,
            "temperature_unit": "celsius", "wind_speed_unit": "ms", "precipitation_unit": "mm",
            "timeformat": "unixtime", "timezone": "auto", "forecast_days": forecast_days
        }
        logger.debug(f"Requesting ensemble hourly data with params: {params}")

        try:
            responses = self.client.weather_api(self.ENSEMBLE_API_URL, params=params)
            response = responses[0]
            hourly_api_data = response.Hourly()

            if hourly_api_data is None:
                logger.warning(f"Ensemble API did not return 'hourly' data block for ({latitude}, {longitude})")
                return None

            time_start = pd.to_datetime(hourly_api_data.Time(), unit="s", utc=True)
            time_end = pd.to_datetime(hourly_api_data.TimeEnd(), unit="s", utc=True)
            timestamps_pd = pd.date_range(
                start=time_start, end=time_end, freq=pd.Timedelta(seconds=hourly_api_data.Interval()), inclusive="left"
            )
            timestamps = timestamps_pd.strftime('%Y-%m-%dT%H:%M:%SZ').tolist()

            logger.debug(f"Ensemble timestamps: {len(timestamps)} from {timestamps[0] if timestamps else 'N/A'} to {timestamps[-1] if timestamps else 'N/A'}")
            logger.debug(f"Total variables returned by API in hourly_api_data: {hourly_api_data.VariablesLength()}")


            processed_data = {"time": timestamps, "variables": {}, "hourly_units": {}}

            for requested_var_name_str in hourly_vars: # e.g., "wind_speed_80m"
                target_sdk_enum, target_altitude = self._map_string_to_sdk_var(requested_var_name_str)
                logger.info(f"Processing requested_var_name_str='{requested_var_name_str}': mapped to target_sdk_enum={target_sdk_enum}, target_altitude={target_altitude}")

                if target_sdk_enum is None:
                    logger.warning(f"Skipping unmappable variable: {requested_var_name_str}")
                    processed_data["variables"][requested_var_name_str] = {}
                    continue

                var_data_by_model_and_member = {}
                unit = None
                found_data_for_requested_var = False

                for i in range(hourly_api_data.VariablesLength()):
                    v = hourly_api_data.Variables(i)
                    logger.debug(
                        f"  API var raw dump: Index={i}, SDKVarEnum={v.Variable()}, SDKAltitude={v.Altitude()}, "
                        f"SDKUnit={v.Unit()}, SDKEnsembleMember={v.EnsembleMember()}, ValuesLen={v.ValuesLength()}"
                    )

                    if (v.Variable() == target_sdk_enum and
                        v.Altitude() == target_altitude):

                        found_data_for_requested_var = True
                        member_index = v.EnsembleMember() 
                        unit = v.Unit() 

                        model_name_for_this_member = models[member_index % len(models)]
                        member_key = f"{model_name_for_this_member}_member_{member_index}"
                        values = [None if np.isnan(val) else float(val) for val in v.ValuesAsNumpy().tolist()]
                        var_data_by_model_and_member[member_key] = values

                        logger.debug(f"    MATCH FOUND & ADDED: {member_key} (for {requested_var_name_str}) with {len(values)} values. Unit: {unit}")

                processed_data["variables"][requested_var_name_str] = var_data_by_model_and_member
                if unit: 
                    processed_data["hourly_units"][requested_var_name_str] = unit
                
                if not found_data_for_requested_var:
                    logger.warning(f"No data found in API response matching '{requested_var_name_str}' (Enum: {target_sdk_enum}, Alt: {target_altitude}) across all returned members.")

            logger.info(f"Successfully processed ensemble hourly data for ({latitude}, {longitude}).")
            return processed_data

        except Exception as e:
            logger.error(f"CRITICAL Error in WeatherAPIClient.get_ensemble_hourly_data for ({latitude}, {longitude}): {e}", exc_info=True)
            return {"time": [], "variables": {}}