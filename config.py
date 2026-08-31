"""
Central configuration for the Africa Tech Jobs scraper suite.
Keep every scraper importing from here so the output schema and
crawl politeness settings stay consistent across all sites.
"""

# ---------------------------------------------------------------------------
# Canonical output schema (matches the capstone's target columns exactly)
# ---------------------------------------------------------------------------
SCHEMA_COLUMNS = [
    "job_id",
    "source",
    "source_job_id",
    "job_title",
    "company",
    "job_description",
    "location",
    "country",
    "work_mode",
    "remote_scope",
    "job_field",
    "industry",
    "employment_type",
    "experience_required",
    "education_required",
    "salary",
    "currency",
    "date_posted",
    "application_deadline",
    "tech_category",
    "vacancy_url",
    "scraped_at",
]

# Values we normalize work_mode into
WORK_MODES = {"remote", "hybrid", "onsite", "unknown"}

# African countries we care about (used for filtering / tagging generic
# "Africa" or global boards like RemoteOK / WeWorkRemotely / LinkedIn)
AFRICAN_COUNTRIES = [
    "Kenya", "Nigeria", "Ghana", "South Africa", "Uganda", "Tanzania",
    "Rwanda", "Ethiopia", "Egypt", "Morocco", "Senegal", "Zambia",
    "Zimbabwe", "Botswana", "Namibia", "Cote d'Ivoire", "Cameroon",
    "Algeria", "Tunisia", "Mozambique", "Malawi", "Mauritius",
]

# ISO 3166-1 alpha-2 codes for African countries. ONLY safe to use for
# an EXACT match against a confirmed, dedicated "country" column —
# never for substring-searching free text, since several collide with
# common non-African abbreviations (MA=Massachusetts, GA=Georgia state,
# IN=Indiana, etc.). This is what merge_public_datasets.py hit: a huge
# dataset returning 0 matches almost always means the country field is
# coded, not full-text, and a naive text search silently misses it all.
AFRICAN_COUNTRY_CODES = {
    "DZ": "Algeria", "AO": "Angola", "BJ": "Benin", "BW": "Botswana",
    "BF": "Burkina Faso", "BI": "Burundi", "CV": "Cabo Verde",
    "CM": "Cameroon", "CF": "Central African Republic", "TD": "Chad",
    "KM": "Comoros", "CG": "Congo", "CD": "DR Congo",
    "CI": "Cote d'Ivoire", "DJ": "Djibouti", "EG": "Egypt",
    "GQ": "Equatorial Guinea", "ER": "Eritrea", "SZ": "Eswatini",
    "ET": "Ethiopia", "GA": "Gabon", "GM": "Gambia", "GH": "Ghana",
    "GN": "Guinea", "GW": "Guinea-Bissau", "KE": "Kenya", "LS": "Lesotho",
    "LR": "Liberia", "LY": "Libya", "MG": "Madagascar", "MW": "Malawi",
    "ML": "Mali", "MR": "Mauritania", "MU": "Mauritius", "MA": "Morocco",
    "MZ": "Mozambique", "NA": "Namibia", "NE": "Niger", "NG": "Nigeria",
    "RW": "Rwanda", "ST": "Sao Tome and Principe", "SN": "Senegal",
    "SC": "Seychelles", "SL": "Sierra Leone", "SO": "Somalia",
    "ZA": "South Africa", "SS": "South Sudan", "SD": "Sudan",
    "TZ": "Tanzania", "TG": "Togo", "TN": "Tunisia", "UG": "Uganda",
    "ZM": "Zambia", "ZW": "Zimbabwe",
}
# ISO 3166-1 alpha-3 codes, same exact-match-only caveat.
AFRICAN_COUNTRY_CODES_ALPHA3 = {
    "DZA": "Algeria", "AGO": "Angola", "BEN": "Benin", "BWA": "Botswana",
    "BFA": "Burkina Faso", "BDI": "Burundi", "CPV": "Cabo Verde",
    "CMR": "Cameroon", "CAF": "Central African Republic", "TCD": "Chad",
    "COM": "Comoros", "COG": "Congo", "COD": "DR Congo",
    "CIV": "Cote d'Ivoire", "DJI": "Djibouti", "EGY": "Egypt",
    "GNQ": "Equatorial Guinea", "ERI": "Eritrea", "SWZ": "Eswatini",
    "ETH": "Ethiopia", "GAB": "Gabon", "GMB": "Gambia", "GHA": "Ghana",
    "GIN": "Guinea", "GNB": "Guinea-Bissau", "KEN": "Kenya", "LSO": "Lesotho",
    "LBR": "Liberia", "LBY": "Libya", "MDG": "Madagascar", "MWI": "Malawi",
    "MLI": "Mali", "MRT": "Mauritania", "MUS": "Mauritius", "MAR": "Morocco",
    "MOZ": "Mozambique", "NAM": "Namibia", "NER": "Niger", "NGA": "Nigeria",
    "RWA": "Rwanda", "STP": "Sao Tome and Principe", "SEN": "Senegal",
    "SYC": "Seychelles", "SLE": "Sierra Leone", "SOM": "Somalia",
    "ZAF": "South Africa", "SSD": "South Sudan", "SDN": "Sudan",
    "TZA": "Tanzania", "TGO": "Togo", "TUN": "Tunisia", "UGA": "Uganda",
    "ZMB": "Zambia", "ZWE": "Zimbabwe",
}

# Keywords used to decide if a job is "tech" when a site doesn't have a
# dedicated tech/IT category filter (e.g. generic boards like Jobberman)
TECH_KEYWORDS = [
    "developer", "engineer", "software", "data", "devops", "cloud",
    "frontend", "backend", "full stack", "fullstack", "python", "java",
    "javascript", "react", "node", "android", "ios", "mobile app",
    "machine learning", "ai ", "artificial intelligence", "cybersecurity",
    "security analyst", "network engineer", "systems admin", "sysadmin",
    "database", "sql", "product manager", "ux", "ui designer",
    "qa engineer", "quality assurance", "it support", "helpdesk",
    "scrum", "technical", "programmer", "web developer", "site reliability",
    # broadened for more coverage / hit-rate:
    "ict", "information technology", "computer science", "system analyst",
    "network administrator", "it officer", "it manager", "it technician",
    "solutions architect", "business analyst", "data engineer",
    "cloud architect", "infrastructure engineer", "telecom", "telecoms",
    "erp", "sap consultant", "salesforce", "digital transformation",
    "automation", "robotics", "blockchain", "fintech engineer",
    "game developer", "embedded systems", "firmware", "technical support",
    "help desk", "it consultant", "application developer", ".net developer",
    "php developer", "ruby developer", "golang", "c++ developer",
]

# Rough tech sub-category buckets, used by utils.helpers.classify_tech_category
TECH_CATEGORY_MAP = {
    "Software Development": ["developer", "software engineer", "programmer",
                              "full stack", "fullstack", "backend", "frontend",
                              "web developer", "mobile app", "android", "ios"],
    "Data & AI": ["data scientist", "data analyst", "data engineer",
                  "machine learning", "artificial intelligence", "ai ",
                  "business intelligence", "bi analyst"],
    "DevOps & Cloud": ["devops", "site reliability", "cloud engineer",
                       "cloud architect", "kubernetes", "sre"],
    "Cybersecurity": ["cybersecurity", "security analyst", "penetration",
                       "infosec", "security engineer"],
    "IT Support & Networking": ["it support", "helpdesk", "network engineer",
                                 "systems admin", "sysadmin", "desktop support"],
    "Product & Design": ["product manager", "ux designer", "ui designer",
                          "product owner", "ux/ui"],
    "QA & Testing": ["qa engineer", "quality assurance", "test engineer",
                      "sdet"],
}

# Broad matrix of tech search terms, shared across every search-based
# scraper. More distinct queries = more distinct result sets surfaced
# on sites that only expose postings through a search box (rather than
# a browsable "all jobs" listing) — this directly drives up total
# volume, since each query can return a different slice of their index.
BROAD_TECH_SEARCH_TERMS = [
    "software developer", "software engineer", "web developer",
    "mobile developer", "android developer", "ios developer",
    "full stack developer", "backend developer", "frontend developer",
    "data analyst", "data scientist", "data engineer",
    "business intelligence analyst", "machine learning engineer",
    "devops engineer", "cloud engineer", "site reliability engineer",
    "systems administrator", "network engineer", "network administrator",
    "it support", "it officer", "it manager", "it technician",
    "cybersecurity analyst", "security engineer",
    "database administrator", "solutions architect",
    "qa engineer", "quality assurance analyst", "test engineer",
    "product manager", "ux designer", "ui designer",
    "java developer", "python developer", "php developer",
    ".net developer", "javascript developer", "react developer",
    "technical support", "erp consultant", "sap consultant",
    "business analyst", "telecom engineer", "ict officer",
]

# ---------------------------------------------------------------------------
# Crawl politeness
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT = 20          # seconds
MIN_DELAY = 1.5                # seconds between requests (per scraper)
MAX_DELAY = 3.5
MAX_RETRIES = 3
DEFAULT_MAX_PAGES = 15          # override per-scraper via CLI/args ("as many as possible")
# Hard safety ceiling so a mis-detected "always has a next page" bug
# can't spin forever even if you pass a very high --max-pages.
HARD_PAGE_CAP = 60

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

OUTPUT_DIR = "output"
