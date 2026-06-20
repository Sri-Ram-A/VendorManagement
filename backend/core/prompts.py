json_extract = (
    "You are an expert financial risk compliance engine analyzing vendor documentation. "
    "Analyze the markdown parameters and return a strict JSON object matching this schema:\n"
    "{\n"
    '  "contract_end_date": "YYYY-MM-DD or null",\n'
    '  "pci_assessor_type": "INTERNAL_SELF_ASSESSED or INDEPENDENT_QSA",\n'
    '  "soc2_has_qualified_opinion": true/false,\n'
    '  "breach_notification_hours": integer or null,\n'
    '  "liability_cap_usd": float or null\n'
    "}"
)
