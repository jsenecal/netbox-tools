from .constants import USEFUL_TYPES, DEFAULT_TYPES
from pycountry import countries, subdivisions
import logging
logger = logging.getLogger(__name__)


class GeocodeResultError(ValueError):
    pass


class GeocodeResult:
    def __init__(self, geocode_result, expected_types=DEFAULT_TYPES):
        self.raw = geocode_result
        self.expected_types = expected_types

    @property
    def location(self):
        filtered_results = list(
            result for result in self.raw if set(result['types']).issubset(self.expected_types)
        )
        if len(filtered_results) == 0:
            raise GeocodeResultError(
                'No valid location of the types %s' % self.expected_types)
        logger.debug(filtered_results)
        return filtered_results[0]

    @property
    def street_address(self):
        return "{street_number} {route}".format(**self.long_address_components)

    @property
    def city(self):
        return self.long_address_components['locality']

    @property
    def postal_code(self):
        return self.long_address_components['postal_code']

    @property
    def address_components(self):
        filtered_components = {component['types'][0]: {'short_name': component['short_name'], 'long_name': component['long_name']}
                               for component in self.location['address_components'] if not set(component['types']).isdisjoint(set(USEFUL_TYPES))}
        return filtered_components

    @property
    def short_address_components(self):
        return {key: value['short_name'] for key, value in self.address_components.items()}

    @property
    def long_address_components(self):
        return {key: value['long_name'] for key, value in self.address_components.items()}

    @property
    def iso3166_1(self):
        return countries.get(name=self.long_address_components['country'])

    @property
    def iso3166_2(self):
        code = self.short_address_components['country']+'-'+self.short_address_components['administrative_area_level_1']
        return subdivisions.get(code=code)



