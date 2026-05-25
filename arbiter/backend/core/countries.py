"""
countries.py — Arbiter multi-jurisdiction country registry.

Defines legal systems, key statutes, court hierarchies, complaint authorities,
limitation periods, and compliance notes for the top 5 supported countries.

Country codes follow ISO 3166-1 alpha-2 standard.
"""
from __future__ import annotations

from typing import Any

# ── Supported country definitions ──────────────────────────────────────────────────
SUPPORTED_COUNTRIES: dict[str, dict[str, Any]] = {
    "IN": {
        "name": "India",
        "flag": "🇮🇳",
        "legal_system": "Common Law (British colonial legacy), codified statutes",
        "currency": "INR",
        "currency_symbol": "₹",
        "primary_language": "en",
        "secondary_languages": ["hi", "ta", "te", "mr", "bn"],
        "key_statutes": [
            "Indian Penal Code 1860 (IPC)",
            "Code of Civil Procedure 1908 (CPC)",
            "Consumer Protection Act 2019",
            "Right to Information Act 2005 (RTI)",
            "Information Technology Act 2000 (IT Act)",
            "Digital Personal Data Protection Act 2023 (DPDP)",
            "Industrial Disputes Act 1947",
            "Transfer of Property Act 1882",
            "Contract Act 1872",
            "Negotiable Instruments Act 1881",
            "Prevention of Money Laundering Act 2002",
            "Protection of Women from Domestic Violence Act 2005",
            "Scheduled Castes and Scheduled Tribes (Prevention of Atrocities) Act 1989",
            "The Employees' Provident Funds and Miscellaneous Provisions Act 1952",
        ],
        "court_hierarchy": [
            "Supreme Court of India (apex)",
            "High Courts (one per state/UT)",
            "District and Sessions Courts",
            "Civil Courts (Munsiff/Sub-Judge)",
            "Consumer Disputes Redressal Commissions (National/State/District)",
            "Labour Courts and Industrial Tribunals",
            "Family Courts",
            "Lok Adalats (settlement courts)",
        ],
        "complaint_authorities": {
            "consumer": "District Consumer Disputes Redressal Commission (DCDRC)",
            "employment": "Labour Commissioner / PF Commissioner",
            "tenant": "Rent Controller (state-specific)",
            "rti": "Central/State Information Commission",
            "cyber_crime": "Cyber Crime Cell / www.cybercrime.gov.in",
            "banking": "Banking Ombudsman (RBI)",
            "insurance": "Insurance Ombudsman (IRDAI)",
            "tax": "Income Tax Ombudsman",
        },
        "limitation_periods": {
            "consumer_complaint_days": 730,
            "civil_suit_days": 1095,
            "criminal_complaint_days": None,
            "rti_first_appeal_days": 30,
        },
        "compliance_notes": [
            "IT Act 2000 governs digital communication and electronic records",
            "DPDP Act 2023 governs personal data processing — mandatory consent",
            "Bar Council of India Rules — AI cannot provide legal advice, only document assistance",
            "Consumer Protection Act 2019 covers e-commerce disputes explicitly",
            "Aadhaar-based identity verification may be required for some authorities",
        ],
        "constitution_url": "https://legislative.gov.in/constitution-of-india",
        "legal_aid_url": "https://nalsa.gov.in",
        "time_zone": "Asia/Kolkata",
        "emergency_number": "112",
        "document_types": [
            "demand_letter", "legal_notice", "rti_application",
            "consumer_complaint", "cease_and_desist", "employment_complaint",
        ],
    },
    "US": {
        "name": "United States",
        "flag": "🇺🇸",
        "legal_system": "Common Law (federal + state dual system); some civil law in Louisiana",
        "currency": "USD",
        "currency_symbol": "$",
        "primary_language": "en",
        "secondary_languages": ["es"],
        "key_statutes": [
            "Fair Debt Collection Practices Act (FDCPA)",
            "Fair Housing Act (FHA)",
            "Title VII of the Civil Rights Act 1964",
            "Americans with Disabilities Act (ADA)",
            "Consumer Financial Protection Act (CFPA)",
            "Fair Credit Reporting Act (FCRA)",
            "Family and Medical Leave Act (FMLA)",
            "Occupational Safety and Health Act (OSHA)",
            "Electronic Communications Privacy Act (ECPA)",
            "California Consumer Privacy Act (CCPA) — California only",
            "Tenant Protection Act (state-specific varies)",
            "Uniform Commercial Code (UCC)",
        ],
        "court_hierarchy": [
            "US Supreme Court (apex)",
            "US Courts of Appeals (13 circuits)",
            "US District Courts (federal trial courts)",
            "State Supreme Courts",
            "State Appellate Courts",
            "State Trial Courts (General Jurisdiction)",
            "Small Claims Courts (limits vary by state: $2,500–$25,000)",
            "Administrative Law Courts (EEOC, NLRB hearings)",
        ],
        "complaint_authorities": {
            "consumer": "FTC (Federal Trade Commission), CFPB, State Attorney General",
            "employment": "EEOC (Equal Employment Opportunity Commission)",
            "tenant": "Local Housing Authority, HUD (Fair Housing)",
            "civil_rights": "Department of Justice (DOJ)",
            "banking": "CFPB, OCC, FDIC (depending on bank type)",
            "securities": "SEC (Securities and Exchange Commission)",
            "antitrust": "FTC / Department of Justice Antitrust Division",
        },
        "limitation_periods": {
            "civil_complaint_days": 1095,
            "employment_eeoc_days": 180,
            "federal_tort_days": 730,
            "small_claims_days": 730,
        },
        "compliance_notes": [
            "State laws vary significantly — always specify the state",
            "Unauthorized Practice of Law (UPL) rules strictly enforced",
            "CCPA applies to California residents — special data privacy rights",
            "HIPAA applies to health information",
            "Miranda rights apply in criminal contexts",
            "ADA reasonable accommodation requirements for employers 15+ employees",
        ],
        "constitution_url": "https://constitution.congress.gov",
        "legal_aid_url": "https://www.lawhelp.org",
        "time_zone": "America/New_York",
        "emergency_number": "911",
        "document_types": [
            "demand_letter", "cease_and_desist", "employment_complaint",
            "small_claims_filing", "ftc_complaint", "eeoc_charge",
        ],
    },
    "GB": {
        "name": "United Kingdom",
        "flag": "🇬🇧",
        "legal_system": "Common Law (England & Wales, Scotland has separate system)",
        "currency": "GBP",
        "currency_symbol": "£",
        "primary_language": "en",
        "secondary_languages": ["cy"],
        "key_statutes": [
            "Consumer Rights Act 2015",
            "Employment Rights Act 1996",
            "Equality Act 2010",
            "Landlord and Tenant Act 1985",
            "Renters (Reform) Act 2024",
            "UK GDPR (General Data Protection Regulation)",
            "Data Protection Act 2018",
            "Human Rights Act 1998",
            "Unfair Contract Terms Act 1977",
            "Sale of Goods Act 1979",
            "Supply of Goods and Services Act 1982",
            "Protection from Harassment Act 1997",
        ],
        "court_hierarchy": [
            "Supreme Court of the United Kingdom (apex)",
            "Court of Appeal (Civil and Criminal Divisions)",
            "High Court of Justice (Queen's/King's Bench, Chancery, Family)",
            "Crown Court (serious criminal)",
            "County Courts (civil)",
            "Magistrates' Courts (minor criminal + some civil)",
            "Employment Tribunals",
            "First-tier Tribunal (various chambers)",
            "Small Claims Court (within County Court, up to £10,000)",
        ],
        "complaint_authorities": {
            "consumer": "Citizens Advice, Trading Standards, Consumer Ombudsman",
            "employment": "Employment Tribunal, ACAS (Advisory, Conciliation and Arbitration Service)",
            "tenant": "Landlord Deposit Protection Scheme, Housing Ombudsman",
            "data_privacy": "ICO (Information Commissioner's Office)",
            "financial": "Financial Ombudsman Service (FOS)",
            "energy": "Energy Ombudsman",
        },
        "limitation_periods": {
            "civil_claim_days": 1825,
            "employment_tribunal_days": 91,
            "personal_injury_days": 1095,
            "small_claims_days": 1825,
        },
        "compliance_notes": [
            "UK GDPR applies post-Brexit — similar to EU GDPR but UK-specific",
            "Scotland has a separate legal system (Scots law)",
            "Pre-action protocols must be followed before court proceedings",
            "ACAS Early Conciliation is mandatory before employment tribunal claims",
            "Legal aid is limited — means-tested",
        ],
        "constitution_url": "https://www.legislation.gov.uk/ukpga/1998/42/contents",
        "legal_aid_url": "https://www.gov.uk/legal-aid",
        "time_zone": "Europe/London",
        "emergency_number": "999",
        "document_types": [
            "demand_letter", "cease_and_desist", "employment_complaint",
            "consumer_complaint", "data_subject_access_request", "formal_grievance",
        ],
    },
    "CA": {
        "name": "Canada",
        "flag": "🇨🇦",
        "legal_system": "Common Law (federal + provincial); Quebec uses civil law",
        "currency": "CAD",
        "currency_symbol": "CA$",
        "primary_language": "en",
        "secondary_languages": ["fr"],
        "key_statutes": [
            "Canadian Human Rights Act",
            "Canada Labour Code",
            "Privacy Act",
            "Personal Information Protection and Electronic Documents Act (PIPEDA)",
            "Consumer Protection Acts (provincial)",
            "Residential Tenancies Acts (provincial)",
            "Canadian Anti-Spam Legislation (CASL)",
            "Employment Standards Acts (provincial)",
            "Criminal Code of Canada",
            "Charter of Rights and Freedoms",
            "Civil Code of Quebec (Quebec only)",
        ],
        "court_hierarchy": [
            "Supreme Court of Canada (apex)",
            "Federal Court of Appeal",
            "Federal Court",
            "Provincial Courts of Appeal",
            "Superior Courts (provincial — general jurisdiction)",
            "Provincial Courts (provincial — limited jurisdiction)",
            "Small Claims Courts (limits: $5,000–$50,000 depending on province)",
            "Administrative Tribunals (Human Rights, Labour, etc.)",
        ],
        "complaint_authorities": {
            "consumer": "Provincial Consumer Protection Office, Competition Bureau",
            "employment": "Provincial Labour Standards Board / Employment Standards Branch",
            "human_rights": "Canadian Human Rights Commission (federal) / Provincial commissions",
            "privacy": "Office of the Privacy Commissioner of Canada (OPC)",
            "tenant": "Landlord and Tenant Board (Ontario) / Provincial Residential Tenancy Branch",
            "spam": "Canadian Anti-Spam Legislation (CASL) enforcement by CRTC",
        },
        "limitation_periods": {
            "civil_claim_days": 730,
            "employment_complaint_days": 365,
            "human_rights_complaint_days": 365,
        },
        "compliance_notes": [
            "Laws vary significantly by province — specify province",
            "Quebec uses civil law system (based on Napoleonic Code)",
            "PIPEDA applies to private sector personal data federally",
            "French language rights in Quebec — documents may need French",
            "CASL is one of the world's strictest anti-spam laws",
        ],
        "constitution_url": "https://laws-lois.justice.gc.ca/eng/Const/",
        "legal_aid_url": "https://www.legalaid.ca",
        "time_zone": "America/Toronto",
        "emergency_number": "911",
        "document_types": [
            "demand_letter", "cease_and_desist", "employment_complaint",
            "consumer_complaint", "human_rights_complaint", "privacy_breach_notice",
        ],
    },
    "AU": {
        "name": "Australia",
        "flag": "🇦🇺",
        "legal_system": "Common Law (federal + state/territory)",
        "currency": "AUD",
        "currency_symbol": "A$",
        "primary_language": "en",
        "secondary_languages": [],
        "key_statutes": [
            "Australian Consumer Law (Competition and Consumer Act 2010)",
            "Privacy Act 1988",
            "Fair Work Act 2009",
            "Residential Tenancies Acts (state-specific)",
            "Corporations Act 2001",
            "Anti-Discrimination Acts (state-specific)",
            "Human Rights and Equal Opportunity Commission Act 1986",
            "Spam Act 2003",
            "Electronic Transactions Act 1999",
            "Retail Leases Acts (state-specific)",
        ],
        "court_hierarchy": [
            "High Court of Australia (apex)",
            "Federal Court of Australia",
            "Federal Circuit and Family Court of Australia",
            "Supreme Courts (state/territory — apex state)",
            "District/County Courts (state — intermediate)",
            "Magistrates' Courts / Local Courts (state — minor civil/criminal)",
            "Small Claims Tribunals (VCAT, NCAT, QCAT etc. — up to $25,000–$100,000)",
            "Fair Work Commission",
        ],
        "complaint_authorities": {
            "consumer": "ACCC (Australian Competition and Consumer Commission), State Fair Trading",
            "employment": "Fair Work Commission, Fair Work Ombudsman",
            "privacy": "Office of the Australian Information Commissioner (OAIC)",
            "human_rights": "Australian Human Rights Commission (AHRC)",
            "tenant": "State Tenancy Tribunals (NCAT/VCAT/QCAT)",
            "financial": "Australian Financial Complaints Authority (AFCA)",
        },
        "limitation_periods": {
            "civil_claim_days": 1825,
            "employment_unfair_dismissal_days": 21,
            "consumer_complaint_days": 1095,
        },
        "compliance_notes": [
            "State/territory laws vary — specify the state",
            "Australian Consumer Law (ACL) provides strong consumer protections nationally",
            "Privacy Act 1988 requires Privacy Impact Assessments for agencies",
            "Spam Act 2003 strictly governs commercial electronic messages",
            "Legal Professional Privilege must be respected",
        ],
        "constitution_url": "https://www.aph.gov.au/About_Parliament/Senate/Powers_practice_n_procedures/Constitution",
        "legal_aid_url": "https://www.legalaid.nsw.gov.au",
        "time_zone": "Australia/Sydney",
        "emergency_number": "000",
        "document_types": [
            "demand_letter", "cease_and_desist", "employment_complaint",
            "consumer_complaint", "privacy_breach_notice", "tribunal_application",
        ],
    },
}

DEFAULT_COUNTRY = "IN"

# ── Helper functions ─────────────────────────────────────────────────────────────

def get_country(code: str) -> dict[str, Any] | None:
    """Return country data by ISO code. Returns None if not supported."""
    return SUPPORTED_COUNTRIES.get(code.upper())


def get_country_name(code: str) -> str:
    """Return display name for a country code, or the code itself if unknown."""
    c = get_country(code)
    return c["name"] if c else code


def get_country_flag(code: str) -> str:
    """Return flag emoji for a country code."""
    c = get_country(code)
    return c["flag"] if c else "🌍"


def get_supported_country_list() -> list[dict[str, str]]:
    """Return a list of {code, name, flag} dicts for use in frontend selectors."""
    return [
        {"code": code, "name": data["name"], "flag": data["flag"]}
        for code, data in SUPPORTED_COUNTRIES.items()
    ]


def get_key_statutes(code: str) -> list[str]:
    """Return list of key statutes for a country."""
    c = get_country(code)
    return c["key_statutes"] if c else []


def get_complaint_authority(code: str, dispute_type: str) -> str | None:
    """Return the relevant complaint authority for a country + dispute type."""
    c = get_country(code)
    if not c:
        return None
    return c.get("complaint_authorities", {}).get(dispute_type)


def get_limitation_period(code: str, claim_type: str) -> int | None:
    """Return limitation period in days for a country + claim type. None if unknown."""
    c = get_country(code)
    if not c:
        return None
    return c.get("limitation_periods", {}).get(claim_type)


def build_country_context(code: str) -> str:
    """
    Build a concise legal context string for injection into AI system prompts.

    This tells the AI what country's laws to research and apply.
    """
    c = get_country(code)
    if not c:
        return f"Country: {code} (unknown — use general international legal principles)"

    statutes_preview = ", ".join(c["key_statutes"][:5])
    return (
        f"JURISDICTION: {c['flag']} {c['name']}\n"
        f"Legal system: {c['legal_system']}\n"
        f"Key statutes: {statutes_preview} (and others)\n"
        f"Currency: {c['currency']} ({c['currency_symbol']})\n"
        f"Compliance: {'; '.join(c['compliance_notes'][:2])}\n"
        f"Apex court: {c['court_hierarchy'][0] if c['court_hierarchy'] else 'N/A'}"
    )


def is_supported(code: str) -> bool:
    """Check if a country code is supported."""
    return code.upper() in SUPPORTED_COUNTRIES
