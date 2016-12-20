from freezegun import freeze_time
import datetime
import smart_fact_crawler


class fake_smartfact:

    def __init__(self, directory, baseurl='file:tests/resources/smartfact'):
        self.url = smart_fact_crawler.smartfacturl
        smart_fact_crawler.smartfacturl = baseurl + '/' + directory + '/'

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        smart_fact_crawler.smartfacturl = self.url


def test_is_main_js_not_running():
    from shifthelper.conditions import is_mainjs_not_running

    with fake_smartfact('no_main_js'):
        assert is_mainjs_not_running()

    with fake_smartfact('all_good'):
        assert not is_mainjs_not_running()


def test_outdatet():
    from shifthelper.conditions import is_smartfact_outdatet, is_magic_weather_outdatet

    with fake_smartfact('all_good'):
        assert is_smartfact_outdatet()
        assert is_magic_weather_outdatet()

        with freeze_time('2016-09-28 03:11:03'):
            assert not is_smartfact_outdatet()
            assert not is_magic_weather_outdatet()


def test_wind():
    from shifthelper.conditions import is_high_windgusts, is_high_windspeed

    with fake_smartfact('all_good'):
        assert not is_high_windgusts()
        assert not is_high_windspeed()

    with fake_smartfact('strong_wind'):
        assert is_high_windgusts()
        assert is_high_windspeed()


def test_currents():
    from shifthelper.conditions import is_median_current_high, is_maximum_current_high

    with fake_smartfact('all_good'):
        assert not is_median_current_high()
        assert not is_maximum_current_high()

    with fake_smartfact('high_currents'):
        assert is_median_current_high()
        assert is_maximum_current_high()


