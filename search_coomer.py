def find_matches(files, thumb_data, match_type, threshold):
    # Dummy match generator for testing
    import json
    thumbs = json.loads(thumb_data)
    matches = []
    for thumb in thumbs:
        matches.append({
            "similarity": 0.75,
            "match_type": match_type,
            "thumbnail": thumb["thumbnail"],
            "post_url": thumb["post"]
        })
    return matches
