from .exceptions import PayloadException

class CustomerPayload:
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

    def __init__(self, customer_name, iso3166_1_name, iso3166_1_code2, iso3166_1_code3, iso3166_1_e164, street_address, city, iso3166_2, postal_code, comment, parent_org_handle, private_customer, handle="", registration_date=""):
        self.customer_name = customer_name
        self.iso3166_1_name = iso3166_1_name
        self.iso3166_1_code2 = iso3166_1_code2
        self.iso3166_1_code3 = iso3166_1_code3
        self.iso3166_1_e164 = iso3166_1_e164
        self.street_address = street_address
        self.city = city
        self.iso3166_2 = iso3166_2
        self.postal_code = postal_code
        self.comment = comment
        self.parent_org_handle = parent_org_handle
        self.private_customer = private_customer
        self.handle = handle
        self.registration_date = registration_date

    def __str__(self):
        return """<customer xmlns="http://www.arin.net/regrws/core/v1">
                <customerName>{customer_name}</customerName>
                <iso3166-1>
                    <name>{iso3166_1_name}</name>
                    <code2>{iso3166_1_code2}</code2>
                    <code3>{iso3166_1_code3}</code3>
                    <e164>{iso3166_1_e164}</e164>
                </iso3166-1>
                <handle>{handle}</handle>
                <streetAddress>
                    <line number = "1">{street_address}</line>
                </streetAddress>
                <city>{city}</city>
                <iso3166-2>{iso3166_2}</iso3166-2>
                <postalCode>{postal_code}</postalCode>
                <comment>
                    <line number = "1">{comment}</line>
                </comment>
                <parentOrgHandle>{parent_org_handle}</parentOrgHandle>
                <registrationDate>{registration_date}</registrationDate>
                <privateCustomer>{private_customer}</privateCustomer>
            </customer>""".format(**self.__dict__)


class NetBlockPayload:
    """Net Block Payload"""

    def __init__(self, net_type, description, startAddress, endAddress, cidrLength):
        valid_types = ['A', 'AF', 'AP', 'AR', 'AV', 'DA', 'DS', 'FX',
                       'IR', 'IU', 'LN', 'LX', 'PV', 'PX', 'RD', 'RN', 'RV', 'RX', 'S']
        if net_type not in valid_types:
            raise PayloadException("Invalid net_type")

        self.net_type = net_type
        self.description = description
        self.startAddress = startAddress
        self.endAddress = endAddress
        self.cidrLength = cidrLength

    def __str__(self):
        return """<netBlock>
                <type>%s</type>
                <description>%s</description>
                <startAddress>%s</startAddress>
                <endAddress>%s</endAddress>
                <cidrLength>%s</cidrLength>
            </netBlock>""" % (self.net_type, self.description, self.startAddress, self.endAddress, self.cidrLength)


class NetPayload:
    """Net Payload"""

    def __init__(self, comment, orgHandle, customerHandle, parentNetHandle, netName, originAS, netBlocks):
        self.comment = comment
        self.orgHandle = orgHandle
        self.customerHandle = customerHandle
        self.parentNetHandle = parentNetHandle
        self.netName = netName
        self.netBlocks = netBlocks
        self.originAS = originAS

    def __str__(self):
        return """<net xmlns="http://www.arin.net/regrws/core/v1">
                    <version>4</version>
                    <registrationDate></registrationDate>
                    <comment>
                        <line number="1">%s</line>
                    </comment>
                    <orgHandle>%s</orgHandle>
                    <handle></handle>
                    <customerHandle>%s</customerHandle>
                    <parentNetHandle>%s</parentNetHandle>
                    <netName>%s</netName>
                    <originASes>
                        <originAS>%s</originAS>
                    </originASes>
                    <netBlocks>%s   </netBlocks>
                </net>""" % (self.comment, self.orgHandle, self.customerHandle, self.parentNetHandle, self.netName, self.originAS, self.netBlocks)
