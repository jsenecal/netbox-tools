from . import PayloadException

class DelegationKeyPayload:
    """ Delegation Key Payload"""
    def __init__(self, algorithm, digest, ttl, digestType, keyTag):
        if digestType not in (1, 2):
            raise PayloadException("Invalid digestType")
        if algorithm not in (5,7,8):
            raise PayloadException("Invalid algorithm")

        self.algorithm = algorithm
        self.digest = digest
        self.ttl = ttl
        self.digestType = digestType
        self.keyTag = keyTag

    def __str__(self):
        return """<delegationKey xmlns="http://www.arin.net/regrws/core/v1">
                    <algorithm>%s</algorithm>
                    <digest>%s</digest>
                    <ttl>%s</ttl>
                    <digestType>%s</digestType>
                    <keyTag>%s</keyTag>
                </delegationkey>""" % (self.algorithm, self.digest, self.ttl, self.digestType, self.keyTag)


class AttachmentPayload:
    """Attachment Payload"""
    def __init__(self, data, filename):
        self.data = data
        self.filename = filename

    def __str__(self):
        return """<attachment xmlns="http://www.arin.net/regrws/core/v1">
                    <data>%s</data>
                    <filename>%s</filename>
                </attachment>""" % (self.data, self.filename)


class PhonePayload:
    """Phone Payload"""
    def __init__(self, description, code, number, extension=None):
        if code not in ("O", "F", "M"):
            raise PayloadException("Invalid code")

        self.description = description
        self.code = code
        self.number = number
        self.extension = extension

    def __str__(self):
        return """<phone xmlns="http://www.arin.net/regrws/core/v1">
                    <type>
                        <description>%s</description>
                        <code>%s</code>
                    </type>
                    <number>%s</number>
                    <extensions>%s</extension>
                </phone>""" % (self.description, self.code, self.number, self.extension)


class CustomerPayload:
    """Customer Payload"""
    def __init__(self, customerName, iso3166_1name, iso3166_1code2, iso3166_1code3, iso3166_1e164, streetAddress, city, iso3166_2, postalCode, comment, parentOrgHandle=None, privateCustomer=True):
        self.customerName = customerName
        self.iso3166_1name = iso3166_1name
        self.iso3166_1code2 = iso3166_1code2
        self.iso3166_1code3 = iso3166_1code3
        self.iso3166_1e164 = iso3166_1e164
        self.streetAddress = streetAddress
        self.city = city
        self.iso3166_2 = iso3166_2
        self.postalCode = postalCode
        self.comment = comment
        self.parentOrgHandle = parentOrgHandle
        self.privateCustomer = privateCustomer

    def __str__(self):
        return """<customer xmlns="http://www.arin.net/regrws/core/v1" >
                    <customerName>%s</customerName>
                    <iso3166-1>
                        <name>UNITED STATES</name>
                        <code2>US</code2>
                        <code3>USA</code3>
                        <e164>1</e164>
                    </iso3166-1>
                    <handle></handle>
                    <streetAddress>
                        <line number = "1">%s</line>
                    </streetAddress>
                    <city>%s</city>
                    <iso3166-2>%s</iso3166-2>
                    <postalCode>%s</postalCode>
                    <comment>
                        <line number = "1">%s</line>
                    </comment>
                    <parentOrgHandle>%s</parentOrgHandle>
                    <registrationDate></registrationDate>
                    <privateCustomer>%s</privateCustomer>
                </customer>""" % (self.customerName, self.streetAddress, self.city, self.iso3166_2, self.postalCode, self.comment, self.parentOrgHandle, self.privateCustomer)



class OrganizationPayload:
    """Organization Payload"""
    def __init__(self, iso3166_1name, iso3166_1code2, iso3166_1code3, iso3166_1e164, streetAddress, city, iso3166_2, postalCode, comment, orgName, dbaName, taxId, orgUrl):
        self.iso3166_1name = iso3166_1name
        self.iso3166_1code2 = iso3166_1code2
        self.iso3166_1code3 = iso3166_1code3
        self.iso3166_1e164 = iso3166_1e164
        self.streetAddress = streetAddress
        self.city = city
        self.iso3166_2 = iso3166_2
        self.postCode = postalCode
        self.comment = comment
        self.orgName = orgName
        self.dbaName = dbaName
        self.taxId = taxId
        self.orgUrl = orgUrl

    def __str__(self):
        return """<org xmlns="http://www.arin.net/regrws/core/v1">
                    <handle></handle>
                    <registrationDate></registrationDate>
                    <iso3166-1>
                        <name>UNITED STATES</name>
                        <code2>US</code2>
                        <code3>USA</code3>
                        <e164>1</e164>
                    </iso3166-1>
                    <streetAddress>
                        <line number = "1">%s</line>
                    </streetAddress>
                    <city>%s</city>
                    <iso3166-2>%s</iso3166-2>
                    <postalCode>%s</postalCode>
                    <comment>
                        <line number = "1">%s</line>
                    </comment>
                    <orgName>%s</orgName>
                    <dbaName>%s</dbaName>
                    <taxId>%s</taxId>
                    <orgUrl>%s</orgUrl>
                </org>""" % (self.streetAddress, self.city, self.iso3166_2, self.postCode, self.comment, self.orgName, self.dbaName, self.orgUrl)


class RoaPayload:
    """Route Origin Authorization Payload"""
    def __init__(self, signature, roaData):
        self.signature = signature
        self.roaData = roaData

    def __str__(self):
        return """<roa xmlns="http://www.arin.net/regrws/rpki/v1">
                    <signature>%s</signature>
                    <roaData>%s</roaData>
                </roa>""" % (self.signature, self.roaData)


class NetBlockPayload:
    """Net Block Payload"""
    def __init__(self, net_type, description, startAddress, endAddress, cidrLength):
        valid_types = ['A', 'AF', 'AP', 'AR', 'AV', 'DA', 'DS', 'FX', 'IR', 'IU', 'LN', 'LX', 'PV', 'PX', 'RD', 'RN', 'RV', 'RX', 'S']
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


class MessagePayload:
    """Message Payload"""
    def __init__(self, subject, text, category="NONE", attachment=None):
        valid_categories = ["NONE", "JUSTIFICATION"]
        if category not in valid_categories:
            raise PayloadException("Invalid category")

        self.subject = subject
        self.text = text
        self.category = category
        self.attachment = attachment

    def __str__(self):
        return """<message xmlns="http://www.arin.net/regrws/core/v1">
                    <subject>%s</subject>
                    <text>
                        <line number="1">%s</line>
                    </text>
                    <category>%s</category>
                    <attachments>%s</attachments>
                </message""" % (self.subject, self.text, self.category, self.attachment)