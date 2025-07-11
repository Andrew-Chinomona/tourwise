from django import template

register = template.Library()

def clean_location(property):
    # Get fields, ignore None/empty
    parts = [
        (getattr(property, 'street_address', '') or '').strip(),
        (getattr(property, 'suburb', '') or '').strip(),
        (getattr(property, 'city', '') or '').strip(),
    ]
    # Remove empty and deduplicate while preserving order
    seen = set()
    clean = []
    for part in parts:
        if part and part.lower() not in seen:
            clean.append(part)
            seen.add(part.lower())
    return ', '.join(clean)

register.filter('clean_location', clean_location)