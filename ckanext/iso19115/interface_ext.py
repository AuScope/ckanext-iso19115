import logging
log = logging.getLogger(__name__)
from typing import Any

import ckan.plugins as p

from ckanext.iso19115.interfaces import IIso19115
from ckanext.iso19115.converter.AuScopeConverter import Converter

class Iso19115(IIso19115):
    #p.implements(IIso19115, inherit=True)
    pass

    def iso19115_metadata_converter(self, data_dict: dict[str, Any]):
        log.info("Calling CHILD iso19115_metadata_converter")
        return Converter(data_dict)
