metadata = {
    "sample_name": "",
    "group_name": "",
    "file_names": "",
    "sequencing_platform": "",
    "sequencing_type": "",
    "pre_assembled": "",
    "sample_type": "",
    "organism": "",
    "strain": "",
    "subtype": {},
    "country": "",
    "region": "",
    "city": "",
    "zip_code": "",
    "longitude": "",
    "latitude": "",
    "location_note": "",
    "isolation_source": "",
    "source_note": "",
    "pathogenic": "",
    "pathogenicity_note": "",
    "collection_date": "",
    "collected_by": "",
    "usage_restrictions": "",
    "release_date": "",
    "email_address": "",
    "notes": "",
    "batch": "true"
}

default = {
    "mandatory": [
        "sequencing_platform",
        "sequencing_type",
        "collection_date"
    ],
    "seed": {
        "pre_assembled": "no",
        "country": "unknown",
        "isolation_source": "unknown",
        "sample_type": "isolate",
        "organism": "",
        "pathogenic": "yes",
        "usage_restrictions": "public"
    }
}
