"""
 Dataloy Interface (see http://dataloy.com/ddt-server/)

 $Id$

"""
import urllib
from oxylib.xmlTree import *


class DataloyInterface(object):
    """
    @class xmlDDT
    @brief Query DDT database for Ports and Distances.
    @details
    Method are the same as specified at http://dataloy.com/ddt-server/
    """
    _Base='http://www.dataloy.com/ddt-server'

    _URLs= { 'XmlPort':             { 'base': 'XmlPort',
                                      'param': [ 'port' ] },
             'XmlPortUNLocode':     { 'base': 'XmlPortUNLocode',
                                      'param': [ 'port' ] },
             'XmlDistance':         { 'base': 'XmlDistance',
                                      'param': [ 'from', 'to' ] },
             'XmlDistanceUNLocode': { 'base': 'XmlDistance',
                                      'param': ['from', 'to'],
                                      'plus': 'unlocode=true' } }

    def __init__(self, username, password):
        """
        @brief Create object, call with your DDT username and password
        @param username your DDT username
        @param password your DDT password
        """
        self.username = username
        self.password = password

    def __repr__(self):
        return r"<%s(username='%s', password='%s')>" % (self.__class__.__name__, self.username, self.password)

    def _buildQuery(self, queryName, params):
        URL=self._URLs[queryName]
        base=URL['base']
        params=dict(zip(URL['param'], params))
        params['username']=self.username
        params['password']=self.password
        paramsUrl=urllib.urlencode(params)
        if URL.has_key('plus'): paramsUrl= '%s&%s' % (paramsUrl, URL['plus'])
        url='%s/%s?%s' % (self._Base, base, paramsUrl)
        return url

    # ------------------------------------------------------------------------------------------------

    def getPort(self, portName):
        """
        @brief Query port database by portName
        @details Query DDT for a port.
        @return None on no match
        @return An array of dictionaries, with only one element in case of exact match
        @param portName name
        """
        return self._getport(port=portName, unlocode=False)

    def getPortUN(self, portUN):
        """
        @brief Query port database by portUN
        @details Query DDT for a port.
        @return None on no match
        @return An array of dictionaries, with only one element in case of exact match
        @param portUN port UNLocode
        """
        return self._getport(port=portUN, unlocode=True)

    def _getport(self, port, unlocode):

        if unlocode: #BY unlocode
            url = self._buildQuery('XmlPortUNLocode', [port])
        else: #BY portname
            url = self._buildQuery('XmlPort', [port])
        xml = urllib.urlopen(url)
        response = xmlTree(xml.read())
        xml.close()
        try:
            resp=response.parsed['PORTS']['PORT']
            if type(resp) != list: resp = [ resp ]
            for el in resp:
                el['COUNTRY_CODE'] = self._dlISO3166.get(el['COUNTRY_NAME'],"")
                if not el.has_key('UN_LOCODE'): el['UN_LOCODE'] = ""
                if not el['UN_LOCODE'] and el['COUNTRY_CODE'] and el['LOCATION_CODE']:
                    #add UN_LOCODE in "by portname" requests
                    el['UN_LOCODE'] = "%s%s" % (el['COUNTRY_CODE'], el['LOCATION_CODE'])
            return resp
        except:
            return []

    # ------------------------------------------------------------------------------------------------

    def getDistance(self, fromPortId, toPortId):
        """
        @brief Query DDT for a distance
        @details Query port database for distance between two ports, given their DataloyID
        @return None on no match
        @return A dictionary on a single match
        @param fromPortId DataloyID of the "from port"
        @param toPortId DataloyID of the "to port"
        """
        return self._getdistance(fromPort=fromPortId, toPort=toPortId, unlocode=False)

    def getDistanceUN(self, fromPortUN, toPortUN):
        """
        @brief Query DDT for a distance
        @details Query port database for distance between two ports, given their UNLocode
        @return None on no match
        @return A dictionary on a single match
        @param fromPortId UNLocode of the "from port"
        @param toPortId UNLocode of the "to port"
        """
        return self._getdistance(fromPort=fromPortUN, toPort=toPortUN, unlocode=True)

    def _getdistance(self, fromPort, toPort, unlocode):

        if unlocode: #BY unlocode
            url = self._buildQuery('XmlDistanceUNLocode', [fromPort, toPort])
        else: #BY portid
            url = self._buildQuery('XmlDistance', [fromPort, toPort])
        xml = urllib.urlopen(url)
        response = xmlTree(xml.read())
        xml.close()
        try:
            resp=response.parsed['PORT_DISTANCE']
            if type(resp) == list:
                return resp
            else:
                return [ resp ]
        except:
            return None

    # ------------------------------------------------------------------------------------------------

    _dlISO3166 =   {'ANDORRA':'AD', 'UNITED ARABS EMIRATES':'AE', 'AFGHANISTAN':'AF', 'ANTIGUA AND BARBUDA':'AG', 'ANGUILLA':'AI', 'ALBANIA':'AL', 'ARMENIA':'AM', 'NETHERLANDS ANTILLES':'AN', 'ANGOLA':'AO', 'ANTARCTICA':'AQ', 'ARGENTINA':'AR', 'AMERICAN SAMOA':'AS', 'AUSTRIA':'AT', 'AUSTRALIA':'AU', 'ARUBA':'AW', 'ALAND ISLANDS':'AX', 'AZERBAIJAN':'AZ', 'BOSNIA AND HERZEGOVINA':'BA', 'BARBADOS':'BB', 'BANGLADESH':'BD', 'BELGIUM':'BE', 'BURKINA FASO':'BF', 'BULGARIA':'BG', 'BAHRAIN':'BH', 'BURUNDI':'BI', 'BENIN':'BJ', 'SAINT BARTHELEMY':'BL', 'BERMUDA':'BM', 'BRUNEI':'BN', 'BOLIVIA':'BO', 'BRAZIL':'BR', 'BAHAMAS':'BS', 'BHUTAN':'BT', 'BOUVET ISLAND':'BV', 'BOTSWANA':'BW', 'BELARUS':'BY', 'BELIZE':'BZ', 'CANADA':'CA', 'COCOS (KEELING) ISLANDS':'CC', 'CENTRAL AFRICAN REPUBLIC':'CF', 'CONGO':'CG', 'SWITZERLAND':'CH', 'COTE D\'IVOIRE':'CI', 'COOK ISLANDS':'CK', 'CHILE':'CL', 'CAMEROON':'CM', 'CHINA, PEOPLES REP':'CN', 'COLOMBIA':'CO', 'COSTA RICA':'CR', 'CUBA':'CU', 'CAPE VERDE':'CV', 'CHRISTMAS ISLAND':'CX', 'CYPRUS':'CY', 'CZECH REPUBLIC':'CZ', 'GERMANY':'DE', 'DJIBOUTI':'DJ', 'DENMARK':'DK', 'DOMINICA':'DM', 'DOMINICAN REPUBLIC':'DO', 'ALGERIA':'DZ', 'ECUADOR':'EC', 'ESTONIA':'EE', 'EGYPT':'EG', 'WESTERN SAHARA':'EH', 'ERITREA':'ER', 'SPAIN':'ES', 'ETHIOPIA':'ET', 'FINLAND':'FI', 'FIJI':'FJ', 'FALKLAND ISLANDS':'FK', 'FEDERATED STATES OF MICRONESIA':'FM', 'FAROE ISLANDS':'FO', 'FRANCE':'FR', 'GABON':'GA', 'UNITED KINGDOM':'GB', 'GRENADA':'GD', 'GEORGIA':'GE', 'FRENCH GUIANA':'GF', 'GUERNSEY':'GG', 'GHANA':'GH', 'GIBRALTAR':'GI', 'GREENLAND':'GL', 'THE GAMBIA':'GM', 'GUINEA':'GN', 'GUADELOUPE':'GP', 'EQUATORIAL GUINEA':'GQ', 'GREECE':'GR', 'SOUTH GEORGIA AND THE SOUTH SANDWICH ISLANDS':'GS', 'GUATEMALA':'GT', 'GUAM':'GU', 'GUINEA-BISSAU':'GW', 'GUYANA':'GY', 'HONG KONG':'HK', 'HEARD ISLAND AND MCDONALD ISLANDS':'HM', 'HONDURAS':'HN', 'CROATIA':'HR', 'HAITI':'HT', 'HUNGARY':'HU', 'INDONESIA':'ID', 'IRELAND':'IE', 'ISRAEL':'IL', 'ISLE OF MAN':'IM', 'INDIA':'IN', 'BRITISH INDIAN OCEAN TERRITORY':'IO', 'IRAQ':'IQ', 'IRAN':'IR', 'ICELAND':'IS', 'ITALY':'IT', 'JERSEY':'JE', 'JAMAICA':'JM', 'JORDAN':'JO', 'JAPAN':'JP', 'KENYA':'KE', 'KYRGYZSTAN':'KG', 'CAMBODIA':'KH', 'KIRIBATI':'KI', 'COMOROS':'KM', 'SAINT KITTS AND NEVIS':'KN', 'KOREA, NORTH':'KP', 'KOREA, SOUTH':'KR', 'KUWAIT':'KW', 'CAYMAN ISLANDS':'KY', 'KAZAKHSTAN':'KZ', 'LAOS':'LA', 'LEBANON':'LB', 'SAINT LUCIA':'LC', 'LIECHTENSTEIN':'LI', 'SRI LANKA':'LK', 'LIBERIA':'LR', 'LESOTHO':'LS', 'LITHUANIA':'LT', 'LUXEMBOURG':'LU', 'LATVIA':'LV', 'LIBYAN ARAB JAMAHIRIYA':'LY', 'MOROCCO':'MA', 'MONACO':'MC', 'MOLDOVA':'MD', 'MONTENEGRO':'ME', 'COLLECTIVITY OF SAINT MARTIN':'MF', 'MADAGASCAR':'MG', 'MARSHALL ISLANDS':'MH', 'REPUBLIC OF MACEDONIA':'MK', 'MALI':'ML', 'MYANMAR':'MM', 'MONGOLIA':'MN', 'MACAU|MACAO':'MO', 'NORTHERN MARIANA ISLANDS':'MP', 'MARTINIQUE':'MQ', 'MAURITANIA':'MR', 'MONTSERRAT':'MS', 'MALTA':'MT', 'MAURITIUS':'MU', 'MALDIVES':'MV', 'MALAWI':'MW', 'MEXICO':'MX', 'MALAYSIA':'MY', 'MOZAMBIQUE':'MZ', 'NAMIBIA':'NA', 'NEW CALEDONIA':'NC', 'NIGER':'NE', 'NORFOLK ISLAND':'NF', 'NIGERIA':'NG', 'NICARAGUA':'NI', 'NETHERLANDS':'NL', 'NORWAY':'NO', 'NEPAL':'NP', 'NAURU':'NR', 'NIUE':'NU', 'NEW ZEALAND':'NZ', 'OMAN':'OM', 'PANAMA':'PA', 'PERU':'PE', 'FRENCH POLYNESIA':'PF', 'PAPUA NEW GUINEA':'PG', 'PHILIPPINES':'PH', 'PAKISTAN':'PK', 'POLAND':'PL', 'SAINT PIERRE AND MIQUELON':'PM', 'PITCAIRN ISLANDS':'PN', 'PUERTO RICO':'PR', 'PALESTINIAN TERRITORIES':'PS', 'PORTUGAL':'PT', 'PALAU':'PW', 'PARAGUAY':'PY', 'QATAR':'QA', 'REUNION':'RE', 'ROMANIA':'RO', 'SERBIA':'RS', 'RUSSIA':'RU', 'RWANDA':'RW', 'SAUDI ARABIA':'SA', 'SOLOMON ISLANDS':'SB', 'SEYCHELLES':'SC', 'SUDAN':'SD', 'SWEDEN':'SE', 'SINGAPORE':'SG', 'SAINT HELENA':'SH', 'SLOVENIA':'SI', 'SVALBARD AND JAN MAYEN':'SJ', 'SLOVAKIA':'SK', 'SIERRA LEONE':'SL', 'SAN MARINO':'SM', 'SENEGAL':'SN', 'SOMALIA':'SO', 'SURINAME':'SR', 'EL SALVADOR':'SV', 'SYRIA|SYRIAN ARAB REPUBLIC':'SY', 'SWAZILAND':'SZ', 'TURKS AND CAICOS ISLANDS':'TC', 'CHAD':'TD', 'FRENCH SOUTHERN AND ANTARCTIC LANDS':'TF', 'TOGO':'TG', 'THAILAND':'TH', 'TAJIKISTAN':'TJ', 'TOKELAU':'TK', 'EAST TIMOR':'TL', 'TURKMENISTAN':'TM', 'TUNISIA':'TN', 'TONGA':'TO', 'TURKEY':'TR', 'TRINIDAD AND TOBAGO':'TT', 'TUVALU':'TV', 'TAIWAN':'TW', 'TANZANIA':'TZ', 'UKRAINE':'UA', 'UGANDA':'UG', 'UNITED STATES MINOR OUTLYING ISLANDS':'UM', 'UNITED STATES':'US', 'URUGUAY':'UY', 'UZBEKISTAN':'UZ', 'VATICAN CITY':'VA', 'SAINT VINCENT AND THE GRENADINES':'VC', 'VENEZUELA':'VE', 'BRITISH VIRGIN ISLANDS':'VG', 'UNITED STATES VIRGIN ISLANDS':'VI', 'VIETNAM':'VN', 'VANUATU':'VU', 'WALLIS AND FUTUNA':'WF', 'SAMOA':'WS', 'YEMEN':'YE', 'MAYOTTE':'YT', 'SOUTH AFRICA':'ZA', 'ZAMBIA':'ZM', 'ZIMBABWE':'ZW' }

    # ------------------------------------------------------------------------------------------------
