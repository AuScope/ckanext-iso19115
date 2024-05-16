import logging
log = logging.getLogger(__name__)

from typing import Any

from ckanext.iso19115.converter import Converter as ParentConverter

from . import helpers as h
from ..types import cit, mri, mrl

class Converter(ParentConverter):

    def __init__(self, data_dict: dict[str, Any]):
        super().__init__(data_dict)

    def process(self):
        log.info(f"{self.pkg=}")
        self._add_identifier()
        self._add_default_locale()
        self._add_parent()
        self._add_scope()

        self.add_contacts()
        self._add_dates()

        self._add_standard()
        self._add_profile()
        self._add_alternative_reference()
        self._add_other_locale()
        self._add_linkage()
        self._add_spatial_representation()
        self._add_reference_system()
        self._add_metadata_extension()

        self._add_identification()

        self._add_content()
        self._add_distribution()
        self._add_dq()
        self.add_lineage()
        self._add_catalogue()
        self._add_constraints()
        self._add_schema()
        self._add_maintenance()
        self._add_acquisition()


    def add_contacts(self):
        # Create CI_Organisation
        log.info("add_contacts()")
        org = h.org(
            self.pkg.get("primary_contact_name", "AuScope Pty Ltd"),
            contactInfo=[
                cit.CI_Contact(
                    address=[h.address(email=h.cs(self.pkg.get("primary_contact_email", "")))],
                )
            ],
        )
        resp = cit.CI_Responsibility("publisher", [org])
        self.data.add_contact(resp)
         
        for contact in self._extra_contacts():
            self.data.add_contact(contact)

    def add_lineage(self):
        lin_str = self.pkg.get("lineage","")
        if len(lin_str) > 0:
            lin = mrl.LI_Lineage(statement=lin_str)
            self.data.resourceLineage.append(lin)

    def add_license(self):
        lic_id_str = self.pkg.get("license_id", "")
        if len(lic_id_str) > 0:
            lic_title = self.pkg.get("license_title", "")
            lic_url = self.pkg.get("license_url", "")
        

    def add_identification(self):
        #mcc.Abstract_ResourceDescription
        #mri.MD_DataIdentification
        #srv.SV_ServiceIdentification

        citation: cit.CI_Citation = h.citation(
            self.pkg["title"], identifier=h.id(self.pkg["id"])
        )
        kw = [
            h.keyword(t if isinstance(t, str) else t["name"]) for t in self.pkg["tags"]
        ]
        ident: mri.MD_DataIdentification = mri.MD_DataIdentification(
            citation,
            self.pkg["notes"],
            descriptiveKeywords=kw,
        )
        self.data.add_identificationInfo(ident)
