NUMBER = "number"
CHOICE = "choice"
BOOLEAN = "boolean"

# Allowed fields
FIELD_SPECS = {
    "age": {"label": "Age (years)", "type": NUMBER},
    "annual_income": {"label": "Annual family income (INR)", "type": NUMBER},
    "land_acres": {"label": "Land owned (acres)", "type": NUMBER},
    "occupation": {"label": "Occupation", "type": CHOICE},
    "state": {"label": "State", "type": CHOICE},
    "gender": {"label": "Gender", "type": CHOICE},
    "category": {"label": "Social category", "type": CHOICE},
    "is_income_tax_payer": {"label": "Income tax payer", "type": BOOLEAN},
}


# Operators meaning
OPERATORS = {
    "eq": "equals",
    "neq": "not equals",
    "gt": "greater than",
    "gte": "greater than or equal",
    "lt": "less than",
    "lte": "less than or equal",
    "in": "is one of",
    "not_in": "is not one of",
}

# Allowed operations on fields
ALLOWED_OPERATORS = {
    NUMBER: {"eq", "neq", "gt", "gte", "lt", "lte"},
    CHOICE: {"eq", "neq", "in", "not_in"},
    BOOLEAN: {"eq"},
}
