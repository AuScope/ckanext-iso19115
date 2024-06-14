import logging
log = logging.getLogger(__name__)

from typing import Any, Dict

import pyproj

from ckanext.iso19115.converter import Converter as ParentConverter

from . import helpers as h
from ..types import cit, mri, mrl, mco, gex, gml, gco, mcc, mrs

class Converter(ParentConverter):

    def __init__(self, data_dict: Dict[str, Any]):
        super().__init__(data_dict)


    def process(self):
        """ Functions without _ are local
        """
        log.info(f"{self.pkg=}")

        # Call parent functions
        self._add_identifier()
        self._add_default_locale()
        self._add_scope()
        self._add_standard()
        self._add_spatial_representation()
        self._add_dq()

        # Call local functions
        self.add_contacts()
        self.add_lineage()
        self.add_metadata_linkage()
        self.add_identification()
        self.add_dates()
        self.add_reference_system_info()

    def add_reference_system_info(self):
        """ Add CRS information
        """
        self.data.referenceSystemInfo = mrs.MD_ReferenceSystem(
            referenceSystemIdentifier=mcc.MD_Identifier(code=gco.CharacterString("EPSG:4326"),
                                                        authority=cit.CI_Citation(title=gco.CharacterString("WGS 84")),
                                                        codeSpace=gco.CharacterString("European Petroleum Survey Group Geodetic Parameter Dataset"),
                                                        description=gco.CharacterString("WGS 84 - World Geodetic System 1984")
                                                        )
        )


    def add_contacts(self):
        """ Create CI_Organisation from CKAN primary info
        """
        org = h.org(
            self.pkg.get("primary_contact_name", "AuScope Ltd"),
            contactInfo=[
                cit.CI_Contact(
                    address=[
                        h.address(email=h.cs(self.pkg.get("primary_contact_email", "info@auscope.org.au")))
                    ]
                )
            ]
            
        )
        resp = cit.CI_Responsibility("publisher", [org])
        self.data.add_contact(resp)
         
        for contact in self._extra_contacts():
            self.data.add_contact(contact)


    def add_lineage(self):
        """ Add lineage information
        """
        lin_str = self.pkg.get("lineage","")
        if len(lin_str) > 0:
            lin = mrl.LI_Lineage(statement=lin_str)
            self.data.resourceLineage = [lin]


    def add_metadata_linkage(self):
        """ Add metadata lineage - i.e. Data Repository information
        """
        onlineRes = cit.CI_OnlineResource(
            linkage="https://sample.data.auscope.org.au",
            protocol="WWW:LINK-1.0-http--link",
            description="Metadata landing page URL",
            name="AuScope Data Repository",
            function=[cit.CI_OnLineFunctionCode("completeMetadata")]
        )
        self.data.metadataLinkage = [onlineRes]


    def get_constraints(self) -> "list[mco.MD_Constraints]|None":
        """ Create licensing constraints
        """
        lic_id_str = self.pkg.get("license_id", "")
        if len(lic_id_str) > 0:
            lic_title = self.pkg.get("license_title", "")
            lic_url = self.pkg.get("license_url", "")
            return [
                mco.MD_Constraints(
                    useLimitation=[lic_id_str],
                    reference=[
                        cit.CI_Citation(
                            title=lic_title,
                            onlineResource=[
                                cit.CI_OnlineResource(
                                    linkage=lic_url,
                                    protocol="WWW:LINK-1.0-http--link"
                                )
                            ]
                        )
                    ]
                )
            ]
        return None


    def get_gcmd_keywords(self):
        """ Add GCMD keywords """
        kw_list = h.safe_eval(self.pkg.get("gcmd_keywords", "?"))
        kwcode_list = self.pkg.get("gcmd_keywords_code", "").split(",")
        if kw_list is not None and len(kw_list) == len(kwcode_list):
            thes = cit.CI_Citation(
                title="GCMD Science Keywords",
                otherCitationDetails="Global Change Master Directory (2021): GCMD Keywords. Version 11.3. Greenbelt, MD: Earth Science Data and Information System, Earth Science Projects Division, Goddard Space Flight Center (GSFC) National Aeronautics and Space Administration (NASA). URL (GCMD Keyword Forum Page): https://earthdata.nasa.gov/gcmd-forum",
                onlineResource=cit.CI_OnlineResource(
                    linkage="https://gcmd.earthdata.nasa.gov/kms/concepts/concept_scheme/sciencekeywords",
                    protocol="WWW:LINK-1.0-http--link",
                    function=h.make("cit:CI_OnLineFunctionCode", "information")
                )
            )
            kw_type = h.make("mri:MD_KeywordTypeCode", "theme")
            return h.uri_keyword(kw_list, kwcode_list, ktype=kw_type, thesaurusName=thes)
        return None


    def get_anzsrc_keywords(self):
        """ Add ANZSRC keywords
        Source: https://vocabs.ardc.edu.au/repository/api/lda/anzsrc-2020-for/concept
        """
        uri_base = "https://linked.data.gov.au/def/anzsrc-for/2020/"
        kw_list = h.safe_eval(self.pkg.get("fields_of_research", "?"))
        kwcode_list = self.pkg.get("fields_of_research_code", "").split(',')
        if kw_list is not None and len(kw_list) == len(kwcode_list):
            kwcode_list = [uri_base + kwcode for kwcode in kwcode_list]
            thes = cit.CI_Citation(
                title="ANZSRC Fields of Research",
                otherCitationDetails="Australian Bureau of Statistics (2020): Australian and New Zealand Standard Research Classification (ANZSRC). https://www.abs.gov.au",
                onlineResource=cit.CI_OnlineResource(
                    linkage="https://www.abs.gov.au/statistics/classifications/australian-and-new-zealand-standard-research-classification-anzsrc/2020",
                    protocol="WWW:LINK-1.0-http--link",
                    function=h.make("cit:CI_OnLineFunctionCode", "information")
                )
            )
            kw_type = h.make("mri:MD_KeywordTypeCode", "theme")
            return h.uri_keyword(kw_list, kwcode_list, ktype=kw_type, thesaurusName=thes)
        return None


    def make_author_resp(self, auth: Any, role_code_name: str):
        """ Make CI_Responsibility objects from author data
        """
        role_code = cit.CI_RoleCode(role_code_name)
        party = cit.CI_Organisation(name=auth["author_affiliation"],
                                    partyIdentifier=[
                                            mcc.MD_Identifier(
                                                code=auth["author_affiliation_identifier"],
                                                codeSpace=auth["author_affiliation_identifier_type"]
                                        )
                                    ],
                                    individual=[
                                        cit.CI_Individual(
                                            name=auth["author_name"],
                                            contactInfo=[
                                                cit.CI_Contact(
                                                    address=h.address(
                                                        email=[auth["author_email"]]
                                                    )
                                                )
                                            ],
                                            partyIdentifier=[
                                                mcc.MD_Identifier(
                                                    code=auth["author_identifier"],
                                                    codeSpace=auth["author_identifier_type"]
                                                )
                                            ]
                                        )
                                    ]
        )
        return cit.CI_Responsibility(role=[role_code], party=party)


    def make_funder(self):
        """ Make AuScope funder
        """
        role_code = cit.CI_RoleCode("funder")
        org = self.make_auscope_org()
        return [cit.CI_Responsibility(role=[role_code], party=[org])]


    def make_publisher(self):
        """ Make AuScope publisher
        """
        role_code = cit.CI_RoleCode("publisher")
        org = self.make_auscope_org()
        return [cit.CI_Responsibility(role=[role_code], party=[org])]


    def make_auscope_org(self):
        """ Create AuScope Organisation
        """
        return h.org(
            "AuScope",
            contactInfo=[
                self.make_auscope_contact()
            ],
            # AuScope Logo
            logo=[mcc.MD_BrowseGraphic(fileName=gco.CharacterString("https://images.squarespace-cdn.com/content/v1/5b440dc18ab722131f76b631/1544673461662-GWIIUQIW3A490WP1RHBV/AuScope+Logo_no+space_+-+horizontal+tagline_+-+horizontal+tagline.png"),
                                       fileDescription=gco.CharacterString("AuScope Logo"),
                                       fileType=gco.CharacterString("PNG")
                )
            ],
            # AuScope motto
            partyIdentifier=[mcc.MD_Identifier(description=self.pkg.get("organization",{}).get("description",""))]
        )
    
    def make_auscope_contact(self):
        """ Create AuScope Contact info
        """
        return cit.CI_Contact(
                    address=[
                        cit.CI_Address(
                            deliveryPoint=[
                                gco.CharacterString("Melbourne Connect Co-working Level 2, 700 Swanston Street")
                            ],
                            city=gco.CharacterString("Carlton"),
                            administrativeArea=gco.CharacterString("Victoria"),
                            postalCode=gco.CharacterString("3053"),
                            country=gco.CharacterString("Australia"),
                            electronicMailAddress=[gco.CharacterString("info@auscope.org.au")]
                        )
                    ]
                )


    def get_authors(self) -> "list[cit.CI_Responsibility]":
        """ Get author information

        :returns: list of CI_Responsibility objects
        """
        # First author is "author", the remainder are "coAuthor"
        auth_list = h.safe_eval(self.pkg.get("author", "?"))
        resp_list: list[cit.CI_Responsibility] = []
        if auth_list is not None and len(auth_list) > 0:
            resp_list.append(self.make_author_resp(auth_list[0], "author"))
            if len(auth_list) > 1:
                for auth in auth_list[1:]:
                    resp_list.append(self.make_author_resp(auth, "coAuthor"))
        return resp_list


    def get_related_resources(self) -> "list[mri.MD_AssociatedResource]|None":
        """
        'related_resource': '[{"related_resource_title": "Related Resource", "related_resource_type": "physicalobject", "related_resource_url": "https://related.resource.com", "relation_type": "IsCitedBy"}]',
        """
        res_list = h.safe_eval(self.pkg.get("related_resource", "?"))
        if res_list is not None:
            return [self.make_assoc_res(res) for res in res_list]
        return None


    def make_assoc_res(self, res: Any):
        """
        [{"related_resource_title": "Related Resource",
          "related_resource_type": "physicalobject",
          "related_resource_url": "https://related.resource.com", 
          "relation_type": "IsCitedBy"}]
        
        ISO 19115 Definitions:
        ----------------------
        crossReference: 	reference from one dataset to another 	Use to identify related documents or related resources.
        dependency: 	associated through a dependency 	
        isComposedOf: 	reference to resources that are parts of this resource 	
        largerWorkCitation: 	reference to a master dataset of which this one is a part 	Use to identify parent collections, programs for which this resource is a part of, cruises or surveys from which the data was collected, etc.
        revisionOf: 	resource is a revision of associated resource 	
        series: 	associated through a common heritage such as produced to a common product specification 		
        """
        # Map CKAN's relation types to ISO 19115-3
        rel_type = res.get("relation_type", None)
        if rel_type is not None:
            if rel_type in ['IsNewVersionOf', 'Obsoletes', 'IsOriginalFormOf', 'PreviousVersionOf', 'IsObsoletedBy', 'IsVersionOf']:
                rel_type = 'revisionOf'
            elif rel_type in ['Continues', 'IsContinuedBy']:
                rel_type = 'series'
            elif rel_type in ['HasPart']:
                rel_type = 'isComposedOf'
            elif rel_type in ['Requires']:
                rel_type = 'dependency'
            else:
                rel_type = 'crossReference'

        # Create MD_AssociatedResource object
        return mri.MD_AssociatedResource(
            name=cit.CI_Citation(
                title=res.get("related_resource_title", None),
                identifier=[
                    mcc.MD_Identifier(
                        code=res.get("related_resource_url", None)
                    )
                ]
            ),
            associationType=[
                mri.DS_AssociationTypeCode(rel_type)
            ],
        )


    def add_identification(self):
        """ Add identification information
        """
        # Use the DOI as id if it exists
        id = h.id(self.pkg["id"])
        doi = self.pkg.get("doi", None)
        if doi is not None:
            id = "https://doi.org/" + doi
        date_list = []

        # Use the date the DOI was published as publication date
        published_date = self.pkg.get("doi_date_published", None)
        if published_date is not None:
            date_list.append(cit.CI_Date(h.date(published_date), cit.CI_DateTypeCode("published")))

        # Use the deposit date as dataset created date
        deposit_date = self.pkg.get("deposit_date", None)
        if deposit_date is not None:
            date_list.append(cit.CI_Date(h.date(deposit_date), cit.CI_DateTypeCode("creation")))

        # Create citation for data
        citation: cit.CI_Citation = h.citation(
            title=self.pkg.get("title",""),
            identifier = h.id(id, codeSpace="doi.org"),
            date=date_list,
            citedResponsibleParty=self.get_authors() + self.make_funder() + self.make_publisher(),
        )
        # Add plain text keywords
        kw_list = [
            h.keyword(t if isinstance(t, str) else t["name"]) for t in self.pkg.get("tags", [])
        ]

        # Add "AuScope Data Repository" keyword
        kw_list.append(h.keyword("AuScope Data Repository"))

        # Add ANZSRC keywords
        kw_list.append(self.get_anzsrc_keywords())

        # Add GCMD keywords
        kw_list.append(self.get_gcmd_keywords())

        # Create identification for data
        ident: mri.MD_DataIdentification = mri.MD_DataIdentification(
            citation=citation,
            # Credit
            credit=[self.pkg.get("credit", "")],
            # Description or abstract
            abstract=self.pkg.get("notes", ""),
            # Plain keywords
            descriptiveKeywords=kw_list,
            # Licensing constraints
            resourceConstraints=self.get_constraints(),
            # Coordinates, elevation and time period
            extent=self.get_extent(),
            # Associated resources
            associatedResource=self.get_related_resources()
        )

        # Supplemental Information
        if self.pkg.get("supplementation_information", "") != "":
            ident.supplementalInformation = self.pkg["supplementation_information"]

        # Add identification to record
        self.data.add_identificationInfo(ident)


    def add_dates(self):
        """ Add metadata dates, e.g. when this record was created
        """
        # cit.CI_Date
        has_date_info = False
        for date in self.pkg.get("date_info", []):
            self.data.add_dateInfo(
                cit.CI_Date(h.date(date["date"]), cit.CI_DateTypeCode(date["type"]))
            )
            if date["type"] == "creation":
                has_date_info = True

        # "metadata_created" maps to "creation"
        if not has_date_info:
            creation = self.pkg.get("metadata_created", None)
            if creation is not None:
                self.data.add_dateInfo(
                    cit.CI_Date(h.date(creation), cit.CI_DateTypeCode("creation"))
                )

        # "metadata_modified" maps to "revision"
        revision = self.pkg.get("metadata_modified", None)
        if revision is not None:
            self.data.add_dateInfo(
                cit.CI_Date(h.date(creation), cit.CI_DateTypeCode("revision"))
            )


    def get_extent(self):
        """ Create extent object, including time period and elevation
        """
        geo_elems = []
        vert_elem = None
        # If there is a locality name, create a geographic description
        if self.pkg.get("locality", "") != "":
            geoDesc = gex.EX_GeographicDescription(geographicIdentifier=mcc.MD_Identifier(
                description=self.pkg["locality"]
            ))
            geo_elems.append(geoDesc)

        transformer = None
        epsg_code = self.pkg.get("epsg_code", "X")
        if epsg_code.isnumeric():
            try:
                transformer = pyproj.Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
            except pyproj.exceptions.CRSError:
                transformer = None
        location_type = self.pkg.get("location_choice", None)
        # Only produce coords if can find location type and EPSG is known
        if location_type is not None and transformer is not None:

            # If it is a series of points
            if location_type == "point":
                """
                'location_choice': 'point',
                'location_data': {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [143.81180739405886, -36.63316209558656]}, 'properties': {}}]},
                """
                try:
                    for feat in self.pkg["location_data"]["features"]:
                        if feat["geometry"]["type"] == 'Point':
                            coords = feat["geometry"]["coordinates"]
                            # Convert coords to WGS 84
                            x, y = transformer.transform(coords[0], coords[1])
                            # Implement point as bbox
                            geoBBox = gex.EX_GeographicBoundingBox(
                                westBoundLongitude=gco.Decimal(str(x)),
                                eastBoundLongitude=gco.Decimal(str(x)),
                                southBoundLatitude=gco.Decimal(str(y)),
                                northBoundLatitude=gco.Decimal(str(y)),
                                extentTypeCode=gco.Boolean(True)
                            )
                            geo_elems.append(geoBBox)
                except (KeyError, IndexError):
                    pass

            # If it is a series of areas i.e. bounding boxes
            elif location_type == "area":
                """
                'location_choice': 'area',
                'location_data': {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': [[[118.28367920080382, -43.6503840909574], [118.28367920080382, -23.491459553314552], [154.50148095853297, -23.491459553314552], [154.50148095853297, -43.6503840909574], [118.28367920080382, -43.6503840909574]]]}, 'properties': {}}]},
                """
                try:
                    for feat in self.pkg["location_data"]["features"]:
                        if feat["geometry"]["type"] == 'Polygon':
                            coord_list = feat["geometry"]["coordinates"][0]
                            x0, y0 = transformer.transform(coord_list[0][0], coord_list[0][1]) 
                            x1, y1 = transformer.transform(coord_list[1][0], coord_list[1][1])
                            x2, y2 = transformer.transform(coord_list[2][0], coord_list[2][1])
                            x3, y3 = transformer.transform(coord_list[3][0], coord_list[3][1])
                            geoBBox=gex.EX_GeographicBoundingBox(
                                westBoundLongitude=gco.Decimal(str(x0)),
                                eastBoundLongitude=gco.Decimal(str(x2)),
                                southBoundLatitude=gco.Decimal(str(y0)),
                                northBoundLatitude=gco.Decimal(str(y1)),
                                extentTypeCode=gco.Boolean(True)
                            )
                            geo_elems.append(geoBBox)
                except (KeyError, IndexError):
                    pass

            # Only output vert extent for area and point
            if location_type in ["area", "point"]:
                # Assume sea level for a vertical element if there is no 'elevation' value
                elevation = 0.0
                if self.pkg.get("elevation", "") != "":
                    try:
                        elevation = float(self.pkg["elevation"])
                    except ValueError:
                        pass
                # There is no CRS for elevation so use the lowest common denominator
                vert_elem = [gex.EX_VerticalExtent(
                    minimumValue=gco.Real(elevation),
                    maximumValue=gco.Real(elevation),
                    verticalCRSId=mrs.MD_ReferenceSystem(referenceSystemType=mrs.MD_ReferenceSystemTypeCode("vertical"),
                                                    referenceSystemIdentifier=mcc.MD_Identifier(
                                                        authority=cit.CI_Citation(title=gco.CharacterString("MSL Height")),
                                                        codeSpace=gco.CharacterString("European Petroleum Survey Group Geodetic Parameter Dataset"),
                                                        code=gco.CharacterString("EPSG:5714"),
                                                        description=gco.CharacterString("Mean Sea Level Height")
                                                        )
                    )
                )]

        # Return gex.EX_Extent
        extent = gex.EX_Extent(
            temporalElement=[gex.EX_TemporalExtent(
                extent=gml.TimePeriod(
                    beginPosition=self.pkg.get("start_date", ""),
                    endPosition=self.pkg.get("end_date", ""),
                )
            )],
            geographicElement=geo_elems
        )
        if vert_elem is not None:
            extent.verticalElement = vert_elem
        return [extent]