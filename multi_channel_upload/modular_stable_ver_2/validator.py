import json

def validate_news_json(file_path):
    # Required top-level fields
    required_fields = ["day", "date", "location", "type", "headline", "hook_text", "details", "description", "metadata"]
    
    # Approved Channels Mapping
    approved_types = ["cricket", "bollywood", "space", "education", "facts"]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return False, f"❌ Failed to load JSON: {str(e)}"
    
    if not isinstance(data, list):
        return False, "❌ JSON must be a list of objects."

    for i, item in enumerate(data):
        # 1. Check all fields
        for field in required_fields:
            if field not in item or not str(item[field]).strip():
                return False, f"❌ Scene {i+1} missing or empty field: '{field}'"
        
        # 2. Check if 'type' is valid for channel routing
        if item['type'] not in approved_types:
            return False, f"❌ Scene {i+1} has invalid type '{item['type']}'. Must be one of: {approved_types}"
        
        # 3. CTA Constraint Check
        has_cta = "tune with us" in item['details'].lower()
        if i < len(data) - 1 and has_cta:
             return False, f"❌ Scene {i+1} has CTA! 'Tune with us' must ONLY be in the last scene."
        if i == len(data) - 1 and not has_cta:
             return False, f"⚠️ Warning: Last Scene details is missing 'Tune with us'."

    return True, "✅ JSON Validated: Ready for Channel-Specific Processing."