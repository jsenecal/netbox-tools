from .exceptions import PayloadException
import xmltodict
from collections import OrderedDict


class ArinPayload:

    fields = ()

    def __init__(self, *args, **kwargs):
        self._parse_args(*args)
        self._parse_kwargs(**kwargs)

    @classmethod
    def from_xml(cls, xml):
        raise NotImplementedError

    def _parse_args(self, *args):
        pos = 0
        for field in self.fields:
            try:
                setattr(self, field, args[pos])
            except IndexError:
                setattr(self, field, None)
            pos += 1

    def _parse_kwargs(self, **kwargs):
        for field in self.fields:
            value = kwargs.get(field)
            if getattr(self, field) is None:
                setattr(self, field, value)

    @property
    def schema(self):
        raise NotImplementedError

    def __str__(self):
        return xmltodict.unparse(self.schema, full_document=False)


class CustomerPayload(ArinPayload):
    """
        Customer Payload

        https://www.arin.net/resources/manage/regrws/payloads/#customer-payload

        The Customer Payload contains details about a customer.

        The main difference between the ORG Payload and Customer Payload is the privateCustomer field. If true, the name and address fields will not be publicly visible when the Org is displayed. If false or not provided, the customer will be visible as if it were an Org. Additionally, the Customer Payload does not have a dbaName, taxId, or orgUrl field, nor does it have any related POCs. Note that dbaName denotes an organization’s “Doing Business As” name, and exists for organizations who conduct business and would like to appear in Whois as a name other than their legal organization name.

        The comment field can be used to display operational information about the customer (NOC hours, website, etc.). All comments must be accurate and operational in nature. ARIN reserves the right to edit or remove public comments.

        The parentOrgHandle field must contain the handle of the Org from which this customer has been reallocated/reassigned resources.

        A customer record consists of at least a name and street address. For United States and Canada customers, a state/province (iso3166-2) and postalCode are required. For all other country codes, the iso3166-2 and postalCode fields may be included but are not required.

        The following fields are automatically filled in once you submit the payload, and should be left blank:
         * handle
         * registrationDate

        When performing a modify, if you include these fields with a different value from the original, omit them entirely, or leave them blank, it will return an error.
    """

    fields = [
        'customer_name',
        'iso3166_1_name',
        'iso3166_1_code2',
        'iso3166_1_code3',
        'iso3166_1_e164',
        'street_address',
        'city',
        'iso3166_2',
        'postal_code',
        'comment',
        'parent_org_handle',
        'private_customer',
        'handle',
        'registration_date'
    ]

    @property
    def schema(self):
        return {'customer': {'@xmlns': 'http://www.arin.net/regrws/core/v1',
                             'city': self.city,
                             'iso3166-1': {
                                 'code2': self.iso3166_1_code2,
                                 'code3': self.iso3166_1_code3,
                                 'e164': self.iso3166_1_e164,
                                 'name': self.iso3166_1_name

                             },
                             'handle': self.handle,
                             'streetAddress': OrderedDict(
                                 [
                                     ('line', {
                                         '@number': '1',
                                         '#text': self.street_address
                                     })
                                 ]
                             ),
                             'customerName': self.customer_name,
                             'parentOrgHandle': self.parent_org_handle,
                             'comment': OrderedDict(
                                 [
                                     ('line', {
                                         '@number': '1',
                                         '#text': self.comment
                                     })
                                 ]
                             ),
                             'postalCode': self.postal_code,
                             'privateCustomer': self.private_customer,
                             'registrationDate': self.registration_date,
                             'iso3166-2': self.iso3166_2}
                }

    @classmethod
    def from_xml(cls, xml):
        document = xmltodict.parse(xml)
        payload = cls()
        document_root = document['customer']
        payload.customer_name = document_root['customerName']
        payload.iso3166_1_name = document_root['iso3166-1']['name']
        payload.iso3166_1_code2 = document_root['iso3166-1']['code2']
        payload.iso3166_1_code3 = document_root['iso3166-1']['code3']
        payload.iso3166_1_e164 = document_root['iso3166-1']['e164']
        payload.street_address = document_root['streetAddress']['line']['#text']
        payload.city = document_root['city']
        payload.iso3166_2 = document_root['iso3166-2']
        payload.postal_code = document_root['postalCode']
        if document_root.get('comment'):
            payload.comment = document_root['comment']['line']['#text']
        payload.parent_org_handle = document_root['parentOrgHandle']
        payload.private_customer = document_root['privateCustomer']
        payload.handle = document_root['handle']
        payload.registration_date = document_root['registrationDate']
        return payload


class NetBlockPayload(ArinPayload):
    """
        Net Block Payload

        https://www.arin.net/resources/manage/regrws/payloads/#net-block-payload

        The NET Block Payload contains details on the NET block of the network specified. The NET Block Payload is a nested element of a NET Payload. See NET Payload for additional details.

        When submitting a NET Block Payload as part of the NET Payload, the IP addresses provided in the startAddress and endAddress elements can be non-zero-padded (for example, 10.0.0.255) or zero-padded (for example, 010.000.000.255). The payload returned will always express IP addresses as zero-padded.

        The description field will be determined by the type you specify, and may be left blank.

    """

    def __init__(self, start_address, description, end_address=None, cidr_length=None, net_type=None, version=None):

        valid_types = ['A', 'AF', 'AP', 'AR', 'AV', 'DA', 'DS', 'FX',
                       'IR', 'IU', 'LN', 'LX', 'PV', 'PX', 'RD', 'RN', 'RV', 'RX', 'S']

        if net_type and net_type not in valid_types:
            raise PayloadException("Invalid net_type")

        if end_address and cidr_length:
            raise PayloadException(
                "Only one of the endAddress or the cidrLength fields are required; not both")

        self.version = version
        self.net_type = net_type
        self.description = description
        self.start_address = start_address
        self.end_address = end_address
        self.cidr_length = cidr_length

    @property
    def schema(self):
        schema = {'netBlock': {'@xmlns': 'http://www.arin.net/regrws/core/v1',
                               'description': self.description,
                               'startAddress': self.start_address
                               }
                  }
        if self.net_type:
            schema['netBlock']['type'] = self.net_type

        if self.end_address:
            schema['netBlock']['endAddress'] = self.end_address

        if self.cidr_length:
            schema['netBlock']['cidrLength'] = self.cidr_length

        if self.version:
            schema['netBlock']['version'] = self.version

        return schema

    # @classmethod
    # def from_xml(cls, xml):
    #     document = xmltodict.parse(xml)
    #     payload = cls()
    #     document_root = document['netBlock']

    #     import ipdb
    #     ipdb.set_trace()

    #     # self.version = version
    #     # self.net_type = net_type
    #     # self.description = description
    #     # self.start_address = start_address
    #     # self.end_address = end_address
    #     # self.cidr_length = cidr_length


class NetPayload(ArinPayload):
    """
        Net Payload

         https://www.arin.net/resources/manage/regrws/payloads/#net-payload

        The NET Payload contains details about an IPv4 or IPv6 network.

        If you send a NET Payload and need to fill in the netBlock field, only one of the endAddress or the cidrLength fields are required; not both. Reg-RWS will calculate the other for you, and the details for both will be returned in any call resulting in a NET Payload.

        If you specify a NET type, it must be one of the valid codes located in the table under NET Block Payload. If you do not provide a type, Reg-RWS will determine it for you, depending on which call you are using. The version field may contain a value of “4” or “6,” depending on the type of NET you are referring to. If left blank, this field will be completed for you based on the startAddress.

        When submitting a NET Payload, the IP addresses provided in the startAddress and endAddress fields can be non-zero-padded (i.e., 10.0.0.255) or zero-padded (i.e., 010.000.000.255). The payload returned will always express IP addresses as zero-padded.

        The comment field can be used to display operational information about the customer (NOC hours, website, etc.). All comments must be accurate and operational in nature. ARIN reserves the right to edit or remove public comments.


        The following fields are automatically filled in once you submit the payload, and should be left blank:
         * handle
         * registrationDate

        If you alter or omit these fields when performing a NET Modify, you will receive an error.

        The orgHandle and customerHandle elements are mutually exclusive. Depending on the type of the call this payload is being used for, you are required to assign either a customer or an Org. One of the two values will be present at all times.

        Simple reassignments require that you complete the customerHandle field (remove the orgHandle field).
        Reallocations and detailed reassignments require you to complete the orgHandle field (remove the customerHandle field).
        Note that the originASes and pocLinks fields will not autopopulate. These items must be manually added.

        The following fields may not be modified during a NET Modify:
         * version
         * orgHandle
         * netBlock
         * customerHandle
         * parentNetHandle

        If you alter or omit these fields when performing a NET Modify, you will receive an error.
    """

    def __init__(self,
                 version,
                 comment,
                 parent_net_handle,
                 net_name,
                 origin_ases=None,
                 net_blocks=None,
                 handle=None,
                 registration_date=None,
                 org_handle=None,
                 customer_handle=None,
                 poc_links=None):

        self.version = version
        self.comment = comment
        self.org_handle = org_handle
        self.customer_handle = customer_handle
        self.parent_net_handle = parent_net_handle
        self.net_name = net_name
        self.origin_ases = origin_ases
        self.net_blocks = net_blocks
        self.handle = handle
        self.registration_date = registration_date
        self.poc_links = poc_links

    @property
    def schema(self):
        if not self.origin_ases:
            self.origin_ases = list()

        if not self.poc_links:
            self.poc_links = list()

        schema = {'net': {'@xmlns': 'http://www.arin.net/regrws/core/v1',
                          'version': self.version,
                          'comment': OrderedDict(
                              [
                                  ('line', {
                                      '@number': '0',
                                      '#text': self.comment
                                  })
                              ]
                          ),
                          'registrationDate': self.registration_date,
                          'handle': self.handle,
                          'netBlocks': [net_block.schema for net_block in self.net_blocks],
                          'parentNetHandle': self.parent_net_handle,
                          'netName': self.net_name,
                          'originASes': OrderedDict(
                              [('originAS', origin_as)
                               for origin_as in self.origin_ases]
                          ),
                          'pocLinks': self.poc_links
                          }
                  }

        if self.org_handle:
            schema['net']['orgHandle'] = self.org_handle
        if self.customer_handle:
            schema['net']['customerHandle'] = self.customer_handle

        return schema

    @classmethod
    def from_xml(cls, xml):
        document = xmltodict.parse(xml)
        document_root = document['net']
        
        version = document_root['version']
        if document_root.get('comment'):
            comment = document_root['comment']['line']['#text']
        else:
            comment = None

        parent_net_handle = document_root['parentNetHandle']
        net_name = document_root['netName']

        payload = cls(version,
                      comment,
                      parent_net_handle,
                      net_name)

        if document_root.get('customerHandle'):
            payload.customer_handle = document_root['customerHandle']
        if document_root.get('orgHandle'):
            payload.org_handle = document_root['orgHandle']
        if document_root.get('comment'):
            payload.comment = document_root['comment']['line']['#text']

        payload.handle = document_root['handle']
        payload.registration_date = document_root['registrationDate']

        payload.origin_ases = list()
        if document_root.get('origin_ases'):
            for origin_as in document_root['origin_ases']['originAS']:
                payload.origin_ases.append(origin_as)

        payload.net_blocks = list()
        if document_root.get('net_blocks'):
            for net_block in document_root['net_blocks']:
                payload.net_blocks.append(NetBlockPayload.from_xml(net_block))

        return payload


class PocLinkPayload:
    """Poc Link Payload"""

    def __init__(self, poc_handle, link_type):
        valid_types = ['AD', 'AB', 'N', 'T']
        if link_type not in valid_types:
            raise PayloadException("Invalid link_type")

        self.poc_handle = poc_handle
        self.link_type = link_type

    def __str__(self):
        return """<pocLinkRef xmlns="http://www.arin.net/regrws/core/v1" description="" handle="%s" function="%s"></pocLinkRef>""" % (self.poc_handle, self.link_type)


class TicketedRequestPayload(ArinPayload):
    def __init__(self):
        pass

    @classmethod
    def from_xml(cls, xml):
        document = xmltodict.parse(xml)
        document_root = document['ticketedRequest']
        if document_root.get('net'):
            return NetPayload.from_xml(xmltodict.unparse({'net': document['ticketedRequest']['net']}))
