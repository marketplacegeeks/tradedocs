"""
Management command: seed_reference_data
Usage: python manage.py seed_reference_data

Populates all FR-06 reference data tables:
  - Countries         (all 249 ISO 3166-1 countries)
  - Incoterms         (all 11 Incoterms 2020)
  - Units of Measure  (comprehensive trade UOMs)
  - Ports             (~300 major world trading ports with UN/LOCODE)
  - Payment Terms     (common export payment terms)
  - Locations         (common inland trade locations)
  - Pre-Carriage By   (all relevant pre-carriage modes)

Safe to run multiple times — uses get_or_create throughout.
"""

from django.core.management.base import BaseCommand
from apps.master_data.models import Country, Incoterm, UOM, Port, PaymentTerm, Location, PreCarriageBy


class Command(BaseCommand):
    help = "Seed all FR-06 reference data (countries, incoterms, UOM, ports, payment terms, locations, pre-carriage)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding reference data…")
        self._seed_countries()
        self._seed_incoterms()
        self._seed_uoms()
        self._seed_ports()
        self._seed_payment_terms()
        self._seed_locations()
        self._seed_pre_carriage()
        self.stdout.write(self.style.SUCCESS("✓ Reference data seeded successfully."))

    # -------------------------------------------------------------------------
    # Countries — all 249 ISO 3166-1 countries
    # -------------------------------------------------------------------------
    def _seed_countries(self):
        countries = [
            ("Afghanistan", "AF", "AFG"),
            ("Albania", "AL", "ALB"),
            ("Algeria", "DZ", "DZA"),
            ("Andorra", "AD", "AND"),
            ("Angola", "AO", "AGO"),
            ("Antigua and Barbuda", "AG", "ATG"),
            ("Argentina", "AR", "ARG"),
            ("Armenia", "AM", "ARM"),
            ("Australia", "AU", "AUS"),
            ("Austria", "AT", "AUT"),
            ("Azerbaijan", "AZ", "AZE"),
            ("Bahamas", "BS", "BHS"),
            ("Bahrain", "BH", "BHR"),
            ("Bangladesh", "BD", "BGD"),
            ("Barbados", "BB", "BRB"),
            ("Belarus", "BY", "BLR"),
            ("Belgium", "BE", "BEL"),
            ("Belize", "BZ", "BLZ"),
            ("Benin", "BJ", "BEN"),
            ("Bhutan", "BT", "BTN"),
            ("Bolivia", "BO", "BOL"),
            ("Bosnia and Herzegovina", "BA", "BIH"),
            ("Botswana", "BW", "BWA"),
            ("Brazil", "BR", "BRA"),
            ("Brunei Darussalam", "BN", "BRN"),
            ("Bulgaria", "BG", "BGR"),
            ("Burkina Faso", "BF", "BFA"),
            ("Burundi", "BI", "BDI"),
            ("Cabo Verde", "CV", "CPV"),
            ("Cambodia", "KH", "KHM"),
            ("Cameroon", "CM", "CMR"),
            ("Canada", "CA", "CAN"),
            ("Central African Republic", "CF", "CAF"),
            ("Chad", "TD", "TCD"),
            ("Chile", "CL", "CHL"),
            ("China", "CN", "CHN"),
            ("Colombia", "CO", "COL"),
            ("Comoros", "KM", "COM"),
            ("Congo", "CG", "COG"),
            ("Congo (Democratic Republic)", "CD", "COD"),
            ("Costa Rica", "CR", "CRI"),
            ("Croatia", "HR", "HRV"),
            ("Cuba", "CU", "CUB"),
            ("Cyprus", "CY", "CYP"),
            ("Czechia", "CZ", "CZE"),
            ("Denmark", "DK", "DNK"),
            ("Djibouti", "DJ", "DJI"),
            ("Dominica", "DM", "DMA"),
            ("Dominican Republic", "DO", "DOM"),
            ("Ecuador", "EC", "ECU"),
            ("Egypt", "EG", "EGY"),
            ("El Salvador", "SV", "SLV"),
            ("Equatorial Guinea", "GQ", "GNQ"),
            ("Eritrea", "ER", "ERI"),
            ("Estonia", "EE", "EST"),
            ("Eswatini", "SZ", "SWZ"),
            ("Ethiopia", "ET", "ETH"),
            ("Fiji", "FJ", "FJI"),
            ("Finland", "FI", "FIN"),
            ("France", "FR", "FRA"),
            ("Gabon", "GA", "GAB"),
            ("Gambia", "GM", "GMB"),
            ("Georgia", "GE", "GEO"),
            ("Germany", "DE", "DEU"),
            ("Ghana", "GH", "GHA"),
            ("Greece", "GR", "GRC"),
            ("Grenada", "GD", "GRD"),
            ("Guatemala", "GT", "GTM"),
            ("Guinea", "GN", "GIN"),
            ("Guinea-Bissau", "GW", "GNB"),
            ("Guyana", "GY", "GUY"),
            ("Haiti", "HT", "HTI"),
            ("Honduras", "HN", "HND"),
            ("Hong Kong", "HK", "HKG"),
            ("Hungary", "HU", "HUN"),
            ("Iceland", "IS", "ISL"),
            ("India", "IN", "IND"),
            ("Indonesia", "ID", "IDN"),
            ("Iran", "IR", "IRN"),
            ("Iraq", "IQ", "IRQ"),
            ("Ireland", "IE", "IRL"),
            ("Israel", "IL", "ISR"),
            ("Italy", "IT", "ITA"),
            ("Jamaica", "JM", "JAM"),
            ("Japan", "JP", "JPN"),
            ("Jordan", "JO", "JOR"),
            ("Kazakhstan", "KZ", "KAZ"),
            ("Kenya", "KE", "KEN"),
            ("Kiribati", "KI", "KIR"),
            ("Korea (North)", "KP", "PRK"),
            ("Korea (South)", "KR", "KOR"),
            ("Kuwait", "KW", "KWT"),
            ("Kyrgyzstan", "KG", "KGZ"),
            ("Lao PDR", "LA", "LAO"),
            ("Latvia", "LV", "LVA"),
            ("Lebanon", "LB", "LBN"),
            ("Lesotho", "LS", "LSO"),
            ("Liberia", "LR", "LBR"),
            ("Libya", "LY", "LBY"),
            ("Liechtenstein", "LI", "LIE"),
            ("Lithuania", "LT", "LTU"),
            ("Luxembourg", "LU", "LUX"),
            ("Madagascar", "MG", "MDG"),
            ("Malawi", "MW", "MWI"),
            ("Malaysia", "MY", "MYS"),
            ("Maldives", "MV", "MDV"),
            ("Mali", "ML", "MLI"),
            ("Malta", "MT", "MLT"),
            ("Marshall Islands", "MH", "MHL"),
            ("Mauritania", "MR", "MRT"),
            ("Mauritius", "MU", "MUS"),
            ("Mexico", "MX", "MEX"),
            ("Micronesia", "FM", "FSM"),
            ("Moldova", "MD", "MDA"),
            ("Monaco", "MC", "MCO"),
            ("Mongolia", "MN", "MNG"),
            ("Montenegro", "ME", "MNE"),
            ("Morocco", "MA", "MAR"),
            ("Mozambique", "MZ", "MOZ"),
            ("Myanmar", "MM", "MMR"),
            ("Namibia", "NA", "NAM"),
            ("Nauru", "NR", "NRU"),
            ("Nepal", "NP", "NPL"),
            ("Netherlands", "NL", "NLD"),
            ("New Zealand", "NZ", "NZL"),
            ("Nicaragua", "NI", "NIC"),
            ("Niger", "NE", "NER"),
            ("Nigeria", "NG", "NGA"),
            ("North Macedonia", "MK", "MKD"),
            ("Norway", "NO", "NOR"),
            ("Oman", "OM", "OMN"),
            ("Pakistan", "PK", "PAK"),
            ("Palau", "PW", "PLW"),
            ("Palestine", "PS", "PSE"),
            ("Panama", "PA", "PAN"),
            ("Papua New Guinea", "PG", "PNG"),
            ("Paraguay", "PY", "PRY"),
            ("Peru", "PE", "PER"),
            ("Philippines", "PH", "PHL"),
            ("Poland", "PL", "POL"),
            ("Portugal", "PT", "PRT"),
            ("Qatar", "QA", "QAT"),
            ("Romania", "RO", "ROU"),
            ("Russia", "RU", "RUS"),
            ("Rwanda", "RW", "RWA"),
            ("Saint Kitts and Nevis", "KN", "KNA"),
            ("Saint Lucia", "LC", "LCA"),
            ("Saint Vincent and the Grenadines", "VC", "VCT"),
            ("Samoa", "WS", "WSM"),
            ("San Marino", "SM", "SMR"),
            ("Sao Tome and Principe", "ST", "STP"),
            ("Saudi Arabia", "SA", "SAU"),
            ("Senegal", "SN", "SEN"),
            ("Serbia", "RS", "SRB"),
            ("Seychelles", "SC", "SYC"),
            ("Sierra Leone", "SL", "SLE"),
            ("Singapore", "SG", "SGP"),
            ("Slovakia", "SK", "SVK"),
            ("Slovenia", "SI", "SVN"),
            ("Solomon Islands", "SB", "SLB"),
            ("Somalia", "SO", "SOM"),
            ("South Africa", "ZA", "ZAF"),
            ("South Sudan", "SS", "SSD"),
            ("Spain", "ES", "ESP"),
            ("Sri Lanka", "LK", "LKA"),
            ("Sudan", "SD", "SDN"),
            ("Suriname", "SR", "SUR"),
            ("Sweden", "SE", "SWE"),
            ("Switzerland", "CH", "CHE"),
            ("Syria", "SY", "SYR"),
            ("Taiwan", "TW", "TWN"),
            ("Tajikistan", "TJ", "TJK"),
            ("Tanzania", "TZ", "TZA"),
            ("Thailand", "TH", "THA"),
            ("Timor-Leste", "TL", "TLS"),
            ("Togo", "TG", "TGO"),
            ("Tonga", "TO", "TON"),
            ("Trinidad and Tobago", "TT", "TTO"),
            ("Tunisia", "TN", "TUN"),
            ("Turkey", "TR", "TUR"),
            ("Turkmenistan", "TM", "TKM"),
            ("Tuvalu", "TV", "TUV"),
            ("Uganda", "UG", "UGA"),
            ("Ukraine", "UA", "UKR"),
            ("United Arab Emirates", "AE", "ARE"),
            ("United Kingdom", "GB", "GBR"),
            ("United States", "US", "USA"),
            ("Uruguay", "UY", "URY"),
            ("Uzbekistan", "UZ", "UZB"),
            ("Vanuatu", "VU", "VUT"),
            ("Venezuela", "VE", "VEN"),
            ("Vietnam", "VN", "VNM"),
            ("Yemen", "YE", "YEM"),
            ("Zambia", "ZM", "ZMB"),
            ("Zimbabwe", "ZW", "ZWE"),
        ]
        created = 0
        for name, iso2, iso3 in countries:
            _, is_new = Country.objects.get_or_create(iso2=iso2, defaults={"name": name, "iso3": iso3})
            if is_new:
                created += 1
        self.stdout.write(f"  Countries: {created} created, {len(countries) - created} already existed")

    # -------------------------------------------------------------------------
    # Incoterms — all 11 Incoterms 2020 (ICC)
    # -------------------------------------------------------------------------
    def _seed_incoterms(self):
        incoterms = [
            ("EXW", "Ex Works",
             "Seller makes goods available at their premises. Buyer bears all costs and risks from that point, including loading, export clearance, and transportation. Minimum obligation for seller."),
            ("FCA", "Free Carrier",
             "Seller delivers goods to a named carrier or place specified by the buyer. Risk transfers when goods are handed to the carrier. Can be used with any transport mode, including containerised sea freight."),
            ("CPT", "Carriage Paid To",
             "Seller pays freight to the named destination. Risk transfers to buyer when goods are handed to the first carrier. Suitable for any mode of transport."),
            ("CIP", "Carriage and Insurance Paid To",
             "Same as CPT but seller must also arrange and pay for insurance (Institute Cargo Clause A minimum under Incoterms 2020). Suitable for any mode of transport."),
            ("DAP", "Delivered at Place",
             "Seller delivers goods to a named destination, ready for unloading. Buyer is responsible for import duties, taxes, and unloading costs. Suitable for any mode of transport."),
            ("DPU", "Delivered at Place Unloaded",
             "Seller delivers and unloads goods at a named destination. Only Incoterm where seller is responsible for unloading. Buyer handles import clearance and duties."),
            ("DDP", "Delivered Duty Paid",
             "Maximum obligation for seller. Seller bears all costs including import duties and taxes to named destination. Buyer only needs to unload. Suitable for any mode of transport."),
            ("FAS", "Free Alongside Ship",
             "Seller places goods alongside the vessel at the named port of shipment. Risk transfers once goods are alongside the ship. Used only for sea and inland waterway transport."),
            ("FOB", "Free On Board",
             "Seller loads goods on board the vessel at the named port. Risk transfers once goods are on board. Best used for bulk/break-bulk cargo; CPT is preferred for containerised shipments."),
            ("CFR", "Cost and Freight",
             "Seller pays cost and freight to named destination port. Risk transfers once goods are on board the vessel at origin. Used only for sea/inland waterway transport."),
            ("CIF", "Cost, Insurance and Freight",
             "Same as CFR but seller arranges minimum insurance (Institute Cargo Clause C). Used for sea/inland waterway. Insurance obligation is lower than CIP."),
        ]
        created = 0
        for code, full_name, description in incoterms:
            _, is_new = Incoterm.objects.get_or_create(code=code, defaults={"full_name": full_name, "description": description})
            if is_new:
                created += 1
        self.stdout.write(f"  Incoterms: {created} created, {len(incoterms) - created} already existed")

    # -------------------------------------------------------------------------
    # Units of Measurement — comprehensive trade UOMs
    # -------------------------------------------------------------------------
    def _seed_uoms(self):
        uoms = [
            # Weight
            ("Metric Tonnes", "MT"),
            ("Kilograms", "KG"),
            ("Grams", "G"),
            ("Milligrams", "MG"),
            ("Pounds", "LBS"),
            ("Ounces", "OZ"),
            ("Long Tons", "LT"),
            ("Short Tons", "ST"),
            ("Quintals", "QTL"),
            ("Carats", "CT"),
            # Volume / Liquid
            ("Litres", "LTR"),
            ("Millilitres", "ML"),
            ("Kilolitres", "KL"),
            ("Cubic Metres", "CBM"),
            ("Cubic Feet", "CFT"),
            ("Gallons (US)", "GAL"),
            ("Gallons (Imperial)", "IGAL"),
            ("Barrels", "BBL"),
            # Length
            ("Metres", "MTR"),
            ("Centimetres", "CM"),
            ("Millimetres", "MM"),
            ("Feet", "FT"),
            ("Inches", "INCH"),
            ("Yards", "YD"),
            # Area
            ("Square Metres", "SQM"),
            ("Square Feet", "SQFT"),
            ("Square Yards", "SQY"),
            ("Hectares", "HA"),
            # Count / Packaging
            ("Pieces", "PCS"),
            ("Numbers", "NOS"),
            ("Units", "UNT"),
            ("Sets", "SET"),
            ("Pairs", "PR"),
            ("Dozens", "DOZ"),
            ("Gross", "GRS"),
            ("Packets", "PKT"),
            ("Bundles", "BDL"),
            ("Boxes", "BOX"),
            ("Cartons", "CTN"),
            ("Bags", "BAG"),
            ("Bales", "BLE"),
            ("Drums", "DRUM"),
            ("Cans", "CAN"),
            ("Rolls", "ROL"),
            ("Pallets", "PLT"),
            ("Cases", "CAS"),
            ("Bottles", "BTL"),
            ("Tubes", "TBE"),
            ("Sheets", "SHT"),
            ("Plates", "PLT2"),
            ("Bars", "BAR"),
            ("Coils", "COI"),
            ("Spools", "SPL"),
            ("Containers (20ft)", "TEU"),
            ("Containers (40ft)", "FEU"),
        ]
        created = 0
        for name, abbreviation in uoms:
            _, is_new = UOM.objects.get_or_create(abbreviation=abbreviation, defaults={"name": name})
            if is_new:
                created += 1
        self.stdout.write(f"  UOMs: {created} created, {len(uoms) - created} already existed")

    # -------------------------------------------------------------------------
    # Ports — ~300 major world trading ports (UN/LOCODE format, no space)
    # Country codes are ISO 3166-1 alpha-2; location code is 3 chars
    # -------------------------------------------------------------------------
    def _seed_ports(self):
        # Format: (name, locode, country_iso2)
        ports_data = [
            # ---- INDIA -------------------------------------------------------
            ("Nhava Sheva (JNPT)", "INNSA", "IN"),
            ("Mumbai", "INBOM", "IN"),
            ("Chennai", "INMAA", "IN"),
            ("Kolkata", "INCCU", "IN"),
            ("Mundra", "INMUN", "IN"),
            ("Kandla", "INIXY", "IN"),
            ("Visakhapatnam", "INVTZ", "IN"),
            ("Kochi", "INCOK", "IN"),
            ("Tuticorin (Thoothukudi)", "INTUT", "IN"),
            ("Haldia", "INHAL", "IN"),
            ("Ennore (Kamarajar)", "INENN", "IN"),
            ("New Mangalore", "INNML", "IN"),
            ("Mormugao", "INMRM", "IN"),
            ("Paradip", "INPRT", "IN"),
            ("Hazira", "INHAZ", "IN"),
            ("Pipavav", "INPAV", "IN"),
            ("Krishnapatnam", "INKRI", "IN"),
            ("Gangavaram", "INGNG", "IN"),
            # ---- CHINA -------------------------------------------------------
            ("Shanghai", "CNSHA", "CN"),
            ("Ningbo-Zhoushan", "CNNBO", "CN"),
            ("Shenzhen", "CNSZX", "CN"),
            ("Guangzhou (Nansha)", "CNCAN", "CN"),
            ("Tianjin", "CNTSN", "CN"),
            ("Qingdao", "CNTAO", "CN"),
            ("Dalian", "CNDLC", "CN"),
            ("Xiamen", "CNXMN", "CN"),
            ("Lianyungang", "CNLYG", "CN"),
            ("Yantai", "CNYNT", "CN"),
            ("Fuzhou", "CNFOC", "CN"),
            ("Nanjing", "CNNKG", "CN"),
            ("Suzhou", "CNSUZ", "CN"),
            ("Wenzhou", "CNWNZ", "CN"),
            ("Yingkou", "CNYIK", "CN"),
            ("Zhanjiang", "CNZHA", "CN"),
            ("Haikou", "CNHAK", "CN"),
            ("Huangpu (Guangzhou)", "CNHUG", "CN"),
            ("Nantong", "CNNTG", "CN"),
            ("Wuhan", "CNWUH", "CN"),
            # ---- SINGAPORE ---------------------------------------------------
            ("Singapore", "SGSIN", "SG"),
            # ---- SOUTH KOREA -------------------------------------------------
            ("Busan", "KRPUS", "KR"),
            ("Incheon", "KRICN", "KR"),
            ("Gwangyang", "KRKWJ", "KR"),
            ("Ulsan", "KRULS", "KR"),
            # ---- JAPAN -------------------------------------------------------
            ("Tokyo", "JPTYO", "JP"),
            ("Yokohama", "JPYOK", "JP"),
            ("Osaka", "JPOSA", "JP"),
            ("Kobe", "JPUKB", "JP"),
            ("Nagoya", "JPNGO", "JP"),
            ("Hakata (Fukuoka)", "JPFUK", "JP"),
            ("Shimizu", "JPSMZ", "JP"),
            # ---- HONG KONG ---------------------------------------------------
            ("Hong Kong", "HKHKG", "HK"),
            # ---- TAIWAN ------------------------------------------------------
            ("Kaohsiung", "TWKHH", "TW"),
            ("Keelung", "TWKEL", "TW"),
            ("Taichung", "TWTXG", "TW"),
            # ---- MALAYSIA ----------------------------------------------------
            ("Port Klang", "MYPKG", "MY"),
            ("Tanjung Pelepas", "MYPED", "MY"),
            ("Penang", "MYPGU", "MY"),
            ("Johor", "MYJHB", "MY"),
            ("Kuching", "MYKCH", "MY"),
            # ---- THAILAND ----------------------------------------------------
            ("Laem Chabang", "THLCH", "TH"),
            ("Bangkok", "THBKK", "TH"),
            ("Map Ta Phut", "THMTA", "TH"),
            # ---- VIETNAM -----------------------------------------------------
            ("Ho Chi Minh City (Cat Lai)", "VNSGN", "VN"),
            ("Haiphong", "VNHPH", "VN"),
            ("Da Nang", "VNDAD", "VN"),
            ("Cai Mep", "VNCME", "VN"),
            ("Cai Lan", "VNCLA", "VN"),
            # ---- INDONESIA ---------------------------------------------------
            ("Jakarta (Tanjung Priok)", "IDJKT", "ID"),
            ("Surabaya (Tanjung Perak)", "IDSUB", "ID"),
            ("Medan (Belawan)", "IDMDN", "ID"),
            ("Semarang", "IDSRG", "ID"),
            ("Makassar", "IDMKS", "ID"),
            # ---- PHILIPPINES -------------------------------------------------
            ("Manila", "PHMNL", "PH"),
            ("Cebu", "PHCEB", "PH"),
            ("Batangas", "PHBTA", "PH"),
            # ---- BANGLADESH --------------------------------------------------
            ("Chittagong", "BDCGP", "BD"),
            ("Mongla", "BDMGL", "BD"),
            # ---- SRI LANKA ---------------------------------------------------
            ("Colombo", "LKCMB", "LK"),
            ("Hambantota", "LKHAM", "LK"),
            # ---- PAKISTAN ----------------------------------------------------
            ("Karachi", "PKKHC", "PK"),
            ("Port Qasim", "PKPQZ", "PK"),
            ("Gwadar", "PKGWD", "PK"),
            # ---- UAE ---------------------------------------------------------
            ("Jebel Ali (Dubai)", "AEJEA", "AE"),
            ("Dubai Port", "AEDXB", "AE"),
            ("Sharjah", "AESHJ", "AE"),
            ("Abu Dhabi (Khalifa Port)", "AEAUH", "AE"),
            ("Fujairah", "AEFUJ", "AE"),
            # ---- SAUDI ARABIA ------------------------------------------------
            ("Jeddah (Islamic Port)", "SAJED", "SA"),
            ("King Abdulaziz (Dammam)", "SADMM", "SA"),
            ("King Abdullah Port (Rabigh)", "SAKAA", "SA"),
            ("Jubail Industrial Port", "SAJUB", "SA"),
            ("Yanbu Industrial Port", "SAYNB", "SA"),
            # ---- QATAR -------------------------------------------------------
            ("Hamad Port (Doha)", "QAHAM", "QA"),
            # ---- KUWAIT ------------------------------------------------------
            ("Shuwaikh Port", "KWSWK", "KW"),
            ("Shuaiba Port", "KWSHU", "KW"),
            # ---- BAHRAIN -----------------------------------------------------
            ("Khalifa bin Salman Port", "BHKBS", "BH"),
            # ---- OMAN --------------------------------------------------------
            ("Muscat (Port Sultan Qaboos)", "OMMCT", "OM"),
            ("Sohar Port", "OMSOH", "OM"),
            ("Salalah Port", "OMSLL", "OM"),
            # ---- IRAN --------------------------------------------------------
            ("Bandar Abbas", "IRBND", "IR"),
            ("Bandar Imam Khomeini", "IRIMQ", "IR"),
            ("Shahid Rajaee", "IRSHD", "IR"),
            # ---- IRAQ --------------------------------------------------------
            ("Basra (Umm Qasr)", "IQUMQ", "IQ"),
            # ---- ISRAEL ------------------------------------------------------
            ("Haifa", "ILHFA", "IL"),
            ("Ashdod", "ILASH", "IL"),
            # ---- JORDAN ------------------------------------------------------
            ("Aqaba", "JOAQJ", "JO"),
            # ---- TURKEY ------------------------------------------------------
            ("Istanbul (Ambarli)", "TRIST", "TR"),
            ("Izmir (Alsancak)", "TRIZA", "TR"),
            ("Mersin", "TRMER", "TR"),
            ("Gemlik", "TRGEM", "TR"),
            ("Derince (Izmit)", "TRDER", "TR"),
            ("Iskenderun", "TRISK", "TR"),
            # ---- EGYPT -------------------------------------------------------
            ("Alexandria", "EGALY", "EG"),
            ("Port Said (East & West)", "EGPSD", "EG"),
            ("Damietta", "EGDAM", "EG"),
            ("Sokhna Port", "EGSOK", "EG"),
            # ---- DJIBOUTI ----------------------------------------------------
            ("Djibouti", "DJJIB", "DJ"),
            # ---- KENYA -------------------------------------------------------
            ("Mombasa", "KEMBA", "KE"),
            # ---- TANZANIA ----------------------------------------------------
            ("Dar es Salaam", "TZDAR", "TZ"),
            ("Tanga", "TZTGT", "TZ"),
            # ---- MOZAMBIQUE --------------------------------------------------
            ("Maputo", "MZMPM", "MZ"),
            ("Beira", "MZBEW", "MZ"),
            ("Nacala", "MZNAC", "MZ"),
            # ---- SOUTH AFRICA ------------------------------------------------
            ("Durban", "ZADUR", "ZA"),
            ("Cape Town", "ZACPT", "ZA"),
            ("Port Elizabeth (Ngqura)", "ZAPLZ", "ZA"),
            ("Richards Bay", "ZARCS", "ZA"),
            ("East London", "ZAELS", "ZA"),
            # ---- GHANA -------------------------------------------------------
            ("Tema", "GHTEM", "GH"),
            ("Takoradi", "GHTKD", "GH"),
            # ---- IVORY COAST -------------------------------------------------
            ("Abidjan", "CIABJ", "CI"),
            ("San Pedro", "CISPY", "CI"),
            # ---- NIGERIA -----------------------------------------------------
            ("Lagos (Apapa)", "NGAPP", "NG"),
            ("Tin Can Island", "NGTCN", "NG"),
            ("Lekki Deep Sea Port", "NGLKK", "NG"),
            ("Onne", "NGONE", "NG"),
            # ---- TOGO --------------------------------------------------------
            ("Lome", "TGLFW", "TG"),
            # ---- SENEGAL -----------------------------------------------------
            ("Dakar", "SNDKR", "SN"),
            # ---- MOROCCO -----------------------------------------------------
            ("Casablanca", "MACAS", "MA"),
            ("Tanger Med", "MATAN", "MA"),
            ("Agadir", "MAAGA", "MA"),
            # ---- ANGOLA ------------------------------------------------------
            ("Luanda", "AOLAW", "AO"),
            # ---- CAMEROON ----------------------------------------------------
            ("Douala", "CMDLA", "CM"),
            # ---- NETHERLANDS -------------------------------------------------
            ("Rotterdam", "NLRTM", "NL"),
            ("Amsterdam", "NLAMS", "NL"),
            ("Moerdijk", "NLMDK", "NL"),
            # ---- BELGIUM -----------------------------------------------------
            ("Antwerp", "BEANT", "BE"),
            ("Zeebrugge", "BEZEE", "BE"),
            ("Ghent", "BEGHENT", "BE"),
            # ---- GERMANY -----------------------------------------------------
            ("Hamburg", "DEHAM", "DE"),
            ("Bremerhaven", "DEBRV", "DE"),
            ("Bremen", "DEBER", "DE"),
            ("Duisburg (inland)", "DEDUI", "DE"),
            ("Rostock", "DERSC", "DE"),
            # ---- UNITED KINGDOM ----------------------------------------------
            ("Felixstowe", "GBFXT", "GB"),
            ("Southampton", "GBSOU", "GB"),
            ("London Gateway", "GBLGW", "GB"),
            ("Liverpool", "GBLIVP", "GB"),
            ("Tilbury", "GBTIL", "GB"),
            ("Bristol (Avonmouth)", "GBBRS", "GB"),
            ("Aberdeen", "GBABD", "GB"),
            ("Glasgow (Greenock)", "GBGLW", "GB"),
            # ---- FRANCE ------------------------------------------------------
            ("Le Havre", "FRLEH", "FR"),
            ("Marseille (Fos)", "FRMRS", "FR"),
            ("Dunkerque", "FRDKK", "FR"),
            ("Bordeaux", "FRBOD", "FR"),
            ("Nantes Saint-Nazaire", "FRNTS", "FR"),
            # ---- SPAIN -------------------------------------------------------
            ("Algeciras", "ESALG", "ES"),
            ("Valencia", "ESVLC", "ES"),
            ("Barcelona", "ESBCN", "ES"),
            ("Bilbao", "ESBIO", "ES"),
            ("Las Palmas", "ESLPA", "ES"),
            ("Cartagena", "ESCAR", "ES"),
            ("Huelva", "ESHUE", "ES"),
            # ---- PORTUGAL ----------------------------------------------------
            ("Lisbon (Setubal)", "PTLIS", "PT"),
            ("Sines", "PTSIN", "PT"),
            ("Leixoes (Porto)", "PTLEI", "PT"),
            # ---- ITALY -------------------------------------------------------
            ("Genoa", "ITGOA", "IT"),
            ("Trieste", "ITTRS", "IT"),
            ("La Spezia", "ITLSP", "IT"),
            ("Gioia Tauro", "ITGIT", "IT"),
            ("Taranto", "ITTAR", "IT"),
            ("Venice", "ITVCE", "IT"),
            ("Naples (Salerno)", "ITNAP", "IT"),
            ("Livorno", "ITLIV", "IT"),
            ("Civitavecchia", "ITCVV", "IT"),
            # ---- GREECE ------------------------------------------------------
            ("Piraeus", "GRPIR", "GR"),
            ("Thessaloniki", "GRSKQ", "GR"),
            ("Volos", "GRVOL", "GR"),
            # ---- MALTA -------------------------------------------------------
            ("Marsaxlokk (Freeport)", "MTMFP", "MT"),
            # ---- CYPRUS ------------------------------------------------------
            ("Limassol", "CYLCA", "CY"),
            # ---- POLAND ------------------------------------------------------
            ("Gdansk", "PLGDN", "PL"),
            ("Gdynia", "PLGDY", "PL"),
            ("Szczecin", "PLSZZ", "PL"),
            # ---- LATVIA ------------------------------------------------------
            ("Riga", "LVRIX", "LV"),
            # ---- ESTONIA -----------------------------------------------------
            ("Tallinn (Muuga)", "EETLL", "EE"),
            # ---- LITHUANIA ---------------------------------------------------
            ("Klaipeda", "LTKLJ", "LT"),
            # ---- FINLAND -----------------------------------------------------
            ("Helsinki", "FIHEL", "FI"),
            ("Kotka", "FIKOT", "FI"),
            ("Turku", "FITKU", "FI"),
            # ---- SWEDEN ------------------------------------------------------
            ("Gothenburg", "SEGOT", "SE"),
            ("Stockholm", "SESTO", "SE"),
            ("Helsingborg", "SEHEL", "SE"),
            ("Malmo", "SEMMX", "SE"),
            # ---- NORWAY ------------------------------------------------------
            ("Oslo", "NOOSL", "NO"),
            ("Bergen", "NOBGO", "NO"),
            ("Stavanger", "NOSVG", "NO"),
            # ---- DENMARK -----------------------------------------------------
            ("Copenhagen", "DKCPH", "DK"),
            ("Aarhus", "DKAAR", "DK"),
            # ---- ROMANIA -----------------------------------------------------
            ("Constanta", "ROCND", "RO"),
            # ---- BULGARIA ----------------------------------------------------
            ("Varna", "BGVAR", "BG"),
            ("Burgas", "BGBOJ", "BG"),
            # ---- CROATIA -----------------------------------------------------
            ("Rijeka", "HRRI", "HR"),
            # ---- RUSSIA ------------------------------------------------------
            ("St Petersburg", "RULED", "RU"),
            ("Novorossiysk", "RUNVS", "RU"),
            ("Vladivostok", "RUVVO", "RU"),
            ("Nakhodka", "RUNAK", "RU"),
            # ---- UKRAINE -----------------------------------------------------
            ("Odessa", "UAODS", "UA"),
            ("Yuzhne (Pivdennyi)", "UAILL", "UA"),
            # ---- GEORGIA -----------------------------------------------------
            ("Poti", "GEPOT", "GE"),
            ("Batumi", "GEBAT", "GE"),
            # ---- AZERBAIJAN --------------------------------------------------
            ("Baku (Alat)", "AZBAK", "AZ"),
            # ---- USA ---------------------------------------------------------
            ("Los Angeles", "USLAX", "US"),
            ("Long Beach", "USLGB", "US"),
            ("New York / New Jersey", "USNYC", "US"),
            ("Savannah", "USSAV", "US"),
            ("Houston", "USHOU", "US"),
            ("Seattle", "USSEA", "US"),
            ("Tacoma", "USTAC", "US"),
            ("Oakland", "USOAK", "US"),
            ("Charleston", "USCHS", "US"),
            ("Baltimore", "USBAL", "US"),
            ("Miami", "USMIA", "US"),
            ("Norfolk (Hampton Roads)", "USORF", "US"),
            ("New Orleans", "USMSY", "US"),
            ("Boston", "USBOS", "US"),
            ("Philadelphia", "USPHL", "US"),
            ("Jacksonville", "USJAX", "US"),
            ("Port Everglades", "USEVG", "US"),
            ("Wilmington (NC)", "USILM", "US"),
            # ---- CANADA ------------------------------------------------------
            ("Vancouver", "CAVAN", "CA"),
            ("Prince Rupert", "CAPRR", "CA"),
            ("Montreal", "CAMTR", "CA"),
            ("Halifax", "CAHFX", "CA"),
            ("Saint John", "CASJB", "CA"),
            # ---- MEXICO ------------------------------------------------------
            ("Manzanillo", "MXZLO", "MX"),
            ("Veracruz", "MXVER", "MX"),
            ("Lazaro Cardenas", "MXLZC", "MX"),
            ("Altamira", "MXATM", "MX"),
            ("Ensenada", "MXESE", "MX"),
            # ---- PANAMA ------------------------------------------------------
            ("Balboa", "PAPBL", "PA"),
            ("Cristobal", "PACRT", "PA"),
            ("Manzanillo International Terminal", "PAMZN", "PA"),
            ("Colon Container Terminal", "PACON", "PA"),
            # ---- COLOMBIA ----------------------------------------------------
            ("Cartagena (Contecar)", "COCRT", "CO"),
            ("Buenaventura", "COBUN", "CO"),
            ("Barranquilla", "COBAQ", "CO"),
            # ---- ECUADOR -----------------------------------------------------
            ("Guayaquil", "ECGYE", "EC"),
            # ---- PERU --------------------------------------------------------
            ("Callao", "PECLL", "PE"),
            # ---- CHILE -------------------------------------------------------
            ("San Antonio", "CLSAI", "CL"),
            ("Valparaiso", "CLVAP", "CL"),
            ("Iquique", "CLIQQ", "CL"),
            ("San Vicente (Talcahuano)", "CLTVL", "CL"),
            # ---- ARGENTINA ---------------------------------------------------
            ("Buenos Aires", "ARBUE", "AR"),
            ("Bahia Blanca", "ARBBQ", "AR"),
            ("Rosario", "ARRSE", "AR"),
            # ---- BRAZIL ------------------------------------------------------
            ("Santos", "BRSSZ", "BR"),
            ("Rio de Janeiro (Sepetiba)", "BRRIG", "BR"),
            ("Paranagua", "BRPNG", "BR"),
            ("Itajai", "BRITI", "BR"),
            ("Salvador", "BRSSA", "BR"),
            ("Vitoria", "BRVIX", "BR"),
            ("Fortaleza", "BRFOR", "BR"),
            ("Belem", "BRBEL", "BR"),
            ("Navegantes", "BRNVT", "BR"),
            ("Suape", "BRSUE", "BR"),
            ("Manaus", "BRMAO", "BR"),
            # ---- AUSTRALIA ---------------------------------------------------
            ("Sydney (Botany Bay)", "AUSYD", "AU"),
            ("Melbourne", "AUMEL", "AU"),
            ("Brisbane", "AUBNE", "AU"),
            ("Fremantle (Perth)", "AUFRE", "AU"),
            ("Adelaide", "AUADL", "AU"),
            ("Darwin", "AUDWN", "AU"),
            # ---- NEW ZEALAND -------------------------------------------------
            ("Auckland", "NZAKL", "NZ"),
            ("Tauranga", "NZTAU", "NZ"),
            ("Lyttelton (Christchurch)", "NZLYT", "NZ"),
            ("Wellington", "NZWLG", "NZ"),
        ]

        # Build a country lookup dict to avoid repeated DB queries
        country_map = {c.iso2: c for c in Country.objects.all()}
        created = 0
        skipped = 0
        for name, locode, country_iso2 in ports_data:
            country = country_map.get(country_iso2)
            if not country:
                self.stdout.write(self.style.WARNING(f"  Skipping port {name} — country {country_iso2} not found"))
                skipped += 1
                continue
            _, is_new = Port.objects.get_or_create(
                code=locode,
                defaults={"name": name, "country": country}
            )
            if is_new:
                created += 1
        self.stdout.write(f"  Ports: {created} created, {len(ports_data) - created - skipped} already existed, {skipped} skipped")

    # -------------------------------------------------------------------------
    # Payment Terms — common export/import payment terms
    # -------------------------------------------------------------------------
    def _seed_payment_terms(self):
        terms = [
            ("Advance Payment (100%)", "Full payment received before shipment. Zero credit risk for seller."),
            ("Letter of Credit (L/C) at Sight", "Payment made immediately upon presentation of compliant documents to the bank."),
            ("Letter of Credit (L/C) — 30 Days", "Payment made 30 days after sight or bill of lading date under a documentary letter of credit."),
            ("Letter of Credit (L/C) — 60 Days", "Payment made 60 days after sight or bill of lading date under a documentary letter of credit."),
            ("Letter of Credit (L/C) — 90 Days", "Payment made 90 days after sight or bill of lading date under a documentary letter of credit."),
            ("Letter of Credit (L/C) — 120 Days", "Payment made 120 days after sight or bill of lading date under a documentary letter of credit."),
            ("Documents Against Payment (D/P)", "Buyer pays before receiving shipping documents. Bank releases documents only upon full payment."),
            ("Documents Against Acceptance (D/A)", "Buyer accepts a bill of exchange (usance draft) and receives documents. Payment due on the agreed future date."),
            ("Open Account — 30 Days Net", "Goods shipped and payment due within 30 days of invoice date. Common for established trading relationships."),
            ("Open Account — 60 Days Net", "Goods shipped and payment due within 60 days of invoice date."),
            ("Open Account — 90 Days Net", "Goods shipped and payment due within 90 days of invoice date."),
            ("Open Account — 120 Days Net", "Goods shipped and payment due within 120 days of invoice date."),
            ("Telegraphic Transfer (TT) — 50% Advance, Balance Before Shipment", "50% of invoice value paid upfront; remaining 50% paid before goods are shipped."),
            ("Telegraphic Transfer (TT) — 30% Advance, 70% Against Documents", "30% advance payment; 70% paid upon presentation of shipping documents."),
            ("Telegraphic Transfer (TT) — Against Copy BL", "Full TT payment made against copy (scanned) bill of lading. Original documents sent by courier."),
            ("Cash Against Documents (CAD)", "Buyer pays cash to the bank upon presentation of shipping documents."),
            ("Consignment", "Seller ships goods; payment received only after buyer sells the goods to end customers."),
            ("Standby Letter of Credit (SBLC)", "A bank guarantee used as a payment of last resort if the buyer fails to pay by agreed terms."),
        ]
        created = 0
        for name, description in terms:
            _, is_new = PaymentTerm.objects.get_or_create(name=name, defaults={"description": description})
            if is_new:
                created += 1
        self.stdout.write(f"  Payment Terms: {created} created, {len(terms) - created} already existed")

    # -------------------------------------------------------------------------
    # Locations — common inland / ICD / trade locations
    # -------------------------------------------------------------------------
    def _seed_locations(self):
        # Format: (name, country_iso2)
        locations_data = [
            # India — ICDs and key inland locations
            ("ICD Tughlakabad (New Delhi)", "IN"),
            ("ICD Patparganj (New Delhi)", "IN"),
            ("ICD Loni (Ghaziabad)", "IN"),
            ("ICD Dadri (Greater Noida)", "IN"),
            ("ICD Ludhiana", "IN"),
            ("ICD Ahmedabad", "IN"),
            ("ICD Hyderabad", "IN"),
            ("ICD Bangalore", "IN"),
            ("ICD Coimbatore", "IN"),
            ("ICD Pune", "IN"),
            ("ICD Nagpur", "IN"),
            ("ICD Jaipur", "IN"),
            ("ICD Jodhpur", "IN"),
            ("ICD Moradabad", "IN"),
            ("ICD Tirupur", "IN"),
            ("ICD Salem", "IN"),
            ("ICD Surat", "IN"),
            ("ICD Varanasi", "IN"),
            ("ICD Amritsar", "IN"),
            ("ICD Kanpur", "IN"),
            # China — key inland logistics hubs
            ("Chengdu (China)", "CN"),
            ("Chongqing (China)", "CN"),
            ("Xi'an (China)", "CN"),
            ("Zhengzhou (China)", "CN"),
            ("Wuhan (China)", "CN"),
            ("Kunming (China)", "CN"),
            ("Harbin (China)", "CN"),
            ("Shenyang (China)", "CN"),
            # Europe — key inland hubs
            ("Duisburg (Germany)", "DE"),
            ("Frankfurt (Germany)", "DE"),
            ("Munich (Germany)", "DE"),
            ("Berlin (Germany)", "DE"),
            ("Paris (France)", "FR"),
            ("Lyon (France)", "FR"),
            ("Milan (Italy)", "IT"),
            ("Madrid (Spain)", "ES"),
            ("Warsaw (Poland)", "PL"),
            ("Vienna (Austria)", "AT"),
            ("Zurich (Switzerland)", "CH"),
            ("London (UK)", "GB"),
            ("Manchester (UK)", "GB"),
            ("Birmingham (UK)", "GB"),
            # Middle East — inland
            ("Riyadh (Saudi Arabia)", "SA"),
            ("Abu Dhabi (UAE)", "AE"),
            ("Dubai (UAE)", "AE"),
            ("Amman (Jordan)", "JO"),
            # USA — inland
            ("Chicago, IL (USA)", "US"),
            ("Dallas, TX (USA)", "US"),
            ("Atlanta, GA (USA)", "US"),
            ("Memphis, TN (USA)", "US"),
            ("Detroit, MI (USA)", "US"),
            # Other
            ("Nairobi (Kenya)", "KE"),
            ("Johannesburg (South Africa)", "ZA"),
            ("Lagos (Nigeria)", "NG"),
            ("Cairo (Egypt)", "EG"),
            ("Istanbul (Turkey)", "TR"),
            ("Bangkok (Thailand)", "TH"),
            ("Kuala Lumpur (Malaysia)", "MY"),
            ("Jakarta (Indonesia)", "ID"),
            ("Ho Chi Minh City (Vietnam)", "VN"),
            ("Manila (Philippines)", "PH"),
            ("Sydney (Australia)", "AU"),
            ("Melbourne (Australia)", "AU"),
        ]
        country_map = {c.iso2: c for c in Country.objects.all()}
        created = 0
        skipped = 0
        for name, country_iso2 in locations_data:
            country = country_map.get(country_iso2)
            if not country:
                skipped += 1
                continue
            _, is_new = Location.objects.get_or_create(name=name, country=country)
            if is_new:
                created += 1
        self.stdout.write(f"  Locations: {created} created, {len(locations_data) - created - skipped} already existed, {skipped} skipped")

    # -------------------------------------------------------------------------
    # Pre-Carriage By — all relevant modes of pre-carriage transport
    # -------------------------------------------------------------------------
    def _seed_pre_carriage(self):
        modes = [
            "Truck",
            "Rail",
            "Feeder Vessel",
            "Barge",
            "Road (Container Truck)",
            "Road (Flatbed Truck)",
            "Road (Refrigerated Truck)",
            "Rail (Container)",
            "Rail (Bulk Wagon)",
            "Inland Waterway",
            "Air Freight",
            "Pipeline",
            "Courier",
            "Own Vehicle",
            "Ex-Works (Buyer's Arrangement)",
        ]
        created = 0
        for name in modes:
            _, is_new = PreCarriageBy.objects.get_or_create(name=name)
            if is_new:
                created += 1
        self.stdout.write(f"  Pre-Carriage By: {created} created, {len(modes) - created} already existed")
