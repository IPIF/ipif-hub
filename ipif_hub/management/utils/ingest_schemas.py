DEFAULT_FIELDS = {
    "@id": {"type": "string"},
    "createdWhen": {
        "type": "string",
        "format": "date",
    },
    "createdBy": {"type": "string"},
    "modifiedWhen": {
        "type": "string",
        "format": "date",
    },
    "modifiedBy": {"type": "string"},
}

DEFS = {
    "factoid_object": {
        "type": "object",
        "required": [*DEFAULT_FIELDS, "person-ref", "source-ref", "statement-refs"],
        "properties": {
            **DEFAULT_FIELDS,
            "person-ref": {"$ref": "#/$defs/p_s_st_ref_object"},
            "source-ref": {"$ref": "#/$defs/p_s_st_ref_object"},
            "statement-refs": {
                "type": "array",
                "items": {"$ref": "#/$defs/p_s_st_ref_object"},
            },
        },
    },
    "person_source_object": {
        "type": "object",
        "required": [*DEFAULT_FIELDS],
        "properties": {
            **DEFAULT_FIELDS,
            "label": {"type": "string"},
            "uris": {
                "type": "array",
                "items": {"type": "string", "format": "uri"},
            },
        },
    },
    "statement_object": {
        "type": "object",
        "required": [*DEFAULT_FIELDS],
        "properties": {
            **DEFAULT_FIELDS,
            "statementType": {"$ref": "#/$defs/uri_label_object"},
            "statementText": {"type": "string"},
            "name": {"type": "string"},
            "role": {"$ref": "#/$defs/uri_label_object"},
            "memberOf": {"$ref": "#/$defs/uri_label_object"},
            "date": {
                "type": "object",
                "properties": {
                    "sort_date": {"type": "string", "format": "date"},
                    "label": {"type": "string"},
                },
            },
            "places": {
                "type": "array",
                "items": {"$ref": "#/$defs/uri_label_object"},
            },
            "relatesToPerson": {
                "type": "array",
                "items": {"$ref": "#/$defs/uri_label_object"},
            },
        },
    },
    "p_s_st_ref_object": {
        "type": "object",
        "required": ["@id"],
        "properties": {
            "@id": {"type": "string"},
            "label": {"type": "string"},
        },
    },
    "uri_label_object": {
        "type": "object",
        "properties": {
            "uri": {"type": "string", "format": "uri"},
            "label": {"type": "string"},
        },
    },
}

FACTOID_SCHEMA = {"$ref": "#/$defs/factoid_object", "$defs": DEFS}
PERSON_SOURCE_SCHEMA = {"$ref": "#/$defs/person_source_object", "$defs": DEFS}
STATEMENT_SCHEMA = {"$ref": "#/$defs/statement_object", "$defs": DEFS}

FLAT_LIST_SCHEMA = {
    "type": "object",
    "required": ["factoids", "persons", "sources", "statements"],
    "properties": {
        "factoids": {
            "type": "array",
            "items": {"$ref": "#/$defs/factoid_object"},
            "minItems": 1,
        },
        "persons": {
            "type": "array",
            "items": {"$ref": "#/$defs/person_source_object"},
            "minItems": 1,
        },
        "sources": {
            "type": "array",
            "items": {"$ref": "#/$defs/person_source_object"},
            "minItems": 1,
        },
        "statements": {
            "type": "array",
            "items": {"$ref": "#/$defs/statement_object"},
            "minItems": 1,
        },
    },
    "$defs": DEFS,
}
