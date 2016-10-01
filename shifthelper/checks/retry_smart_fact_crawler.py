from retrying import retry
import smart_fact_crawler as sfc

kwargs = {
	'stop_max_attempt_number': 10, 
	'wait_exponential_multiplier': 30, 
	'wait_exponential_max': 2000
}

smartfact = retry(sfc.smartfact, **kwargs)

status = retry(sfc.status, **kwargs)
drive_tracking = retry(sfc.drive_tracking, **kwargs)
drive_pointing = retry(sfc.drive_pointing, **kwargs)
sqm = retry(sfc.sqm, **kwargs)
sun = retry(sfc.sun, **kwargs)
weather = retry(sfc.weather, **kwargs)
sipm_currents = retry(sfc.sipm_currents, **kwargs)
sipm_voltages = retry(sfc.sipm_voltages, **kwargs)
container_temperature = retry(sfc.container_temperature, **kwargs)
current_source = retry(sfc.current_source, **kwargs)
camera_climate = retry(sfc.camera_climate, **kwargs)
main_page = retry(sfc.main_page, **kwargs)
trigger_rate = retry(sfc.trigger_rate, **kwargs)
errorhist = retry(sfc.errorhist, **kwargs)
