from retrying import retry
import smart_fact_crawler as sfc

kwargs = {
    'stop_max_attempt_number': 10,
    'wait_exponential_multiplier': 30,
    'wait_exponential_max': 2000
}


@retry(**kwargs)
def smartfact(url=None):
    return sfc.smartfact(url=url)


@retry(**kwargs)
def status(url=None):
    return sfc.status(url=url)


@retry(**kwargs)
def drive_tracking(url=None):
    return sfc.drive_tracking(url=url)


@retry(**kwargs)
def drive_pointing(url=None):
    return sfc.drive_pointing(url=url)


@retry(**kwargs)
def sqm(url=None):
    return sfc.sqm(url=url)


@retry(**kwargs)
def sun(url=None):
    return sfc.sun(url=url)


@retry(**kwargs)
def weather(url=None):
    return sfc.weather(url=url)


@retry(**kwargs)
def sipm_currents(url=None):
    return sfc.sipm_currents(url=url)


@retry(**kwargs)
def sipm_voltages(url=None):
    return sfc.sipm_voltages(url=url)


@retry(**kwargs)
def container_temperature(url=None):
    return sfc.container_temperature(url=url)


@retry(**kwargs)
def current_source(url=None):
    return sfc.current_source(url=url)


@retry(**kwargs)
def camera_climate(url=None):
    return sfc.camera_climate(url=url)


@retry(**kwargs)
def main_page(url=None):
    return sfc.main_page(url=url)


@retry(**kwargs)
def trigger_rate(url=None):
    return sfc.trigger_rate(url=url)


@retry(**kwargs)
def errorhist(url=None):
    return sfc.errorhist(url=url)
