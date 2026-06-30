"""
fetch_geojson.py
================
Downloads Odisha district-level GeoJSON boundaries from public sources,
normalizes district names, simplifies coordinates, and writes the result
as a JavaScript ES module for the frontend.

Usage:
    python fetch_geojson.py
"""

import json
import os
import sys
import textwrap

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package is required. Install with: pip install requests")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GEOJSON_URLS = [
    "https://raw.githubusercontent.com/datta07/INDIAN-SHAPEFILES/master/STATE_WISE/ODISHA/DISTRICT/ODISHA_DISTRICTS.geojson",
    "https://raw.githubusercontent.com/udit-001/india-maps-data/main/geojson/states/odisha.geojson",
    "https://raw.githubusercontent.com/shuklaneerajdev/IndiaStateTopojsonFiles/master/Orissa.geojson",
]

OUTPUT_JS = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "src", "data", "odishaGeoJSON.js")
)

# Canonical district names (30 districts of Odisha)
STANDARD_NAMES = [
    "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Boudh",
    "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam",
    "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal",
    "Kendrapara", "Keonjhar", "Khurda", "Koraput", "Malkangiri",
    "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada", "Puri",
    "Rayagada", "Sambalpur", "Sonepur", "Sundargarh",
]

# Explicit alias map: UPPERCASE alias -> standard name
_ALIASES: dict[str, str] = {
    # Exact standard names (upper-cased for lookup)
    **{n.upper(): n for n in STANDARD_NAMES},
    # Known alternate spellings / census names
    "ANUGUL":          "Angul",
    "ANGUL":           "Angul",
    "KENDUJHAR":       "Keonjhar",
    "KENDUJHAR (KEONJHAR)": "Keonjhar",
    "KEONJHAR":        "Keonjhar",
    "BALESHWAR":       "Balasore",
    "BALESWAR":        "Balasore",
    "BALESHWAR (BALASORE)": "Balasore",
    "KHORDHA":         "Khurda",
    "KHORDA":          "Khurda",
    "JAJAPUR":         "Jajpur",
    "SUBARNAPUR":      "Sonepur",
    "SUBARNAPUR (SONEPUR)": "Sonepur",
    "SONEPUR":         "Sonepur",
    "BOLANGIR":        "Balangir",
    "BOLANGIR (BALANGIR)": "Balangir",
    "DEBAGARH":        "Deogarh",
    "DEBAGARH (DEOGARH)": "Deogarh",
    "JAGATSINGHAPUR":  "Jagatsinghpur",
    "NAWARANGPUR":     "Nabarangpur",
    "NAWRANGPUR":      "Nabarangpur",
    "NAWARANGPUR (NABARANGPUR)": "Nabarangpur",
    "KANDHAMAL":       "Kandhamal",
    "PHULBANI":        "Kandhamal",
    "KANDHAMAL (PHULBANI)": "Kandhamal",
    "PHULABANI":       "Kandhamal",
    "BARAGARH":        "Bargarh",
    "BARGAD":          "Bargarh",
    "BOUDH (DEOGARH)": "Boudh",
    "BAUDH":           "Boudh",
    "SUNDARGARH":      "Sundargarh",
    "SUNDERGARH":      "Sundargarh",
    "SUNDARGAD":       "Sundargarh",
    "KORAPUT":         "Koraput",
    "MALKANGIRI":      "Malkangiri",
    "MALKANAGIRI":     "Malkangiri",
    "MAYURBHANJ":      "Mayurbhanj",
    "MAYURABHANJ":     "Mayurbhanj",
    "JHARSUGUDA":      "Jharsuguda",
    "JHARSUGDA":       "Jharsuguda",
    "KENDRAPADA":      "Kendrapara",
    "KENDRAPARA":      "Kendrapara",
    "NAYAGARH":        "Nayagarh",
    "NUAPADA":         "Nuapada",
    "NOWRANGPUR":      "Nabarangpur",
    "NABARANGAPUR":    "Nabarangpur",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def download_geojson() -> dict:
    """Try each URL in order; return parsed GeoJSON on first success."""
    for url in GEOJSON_URLS:
        print(f"  Trying: {url}")
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if data.get("type") == "FeatureCollection" and data.get("features"):
                print(f"  [OK] Success — {len(data['features'])} features downloaded.")
                return data
            else:
                print(f"  [FAIL] Response is not a valid FeatureCollection (or has no features).")
        except requests.exceptions.RequestException as exc:
            print(f"  [FAIL] Network error: {exc}")
        except json.JSONDecodeError as exc:
            print(f"  [FAIL] JSON parse error: {exc}")

    print("\nERROR: All source URLs failed. Cannot proceed.")
    sys.exit(1)


def _extract_raw_name(props: dict) -> str | None:
    """Pull a district name from whichever property key the source uses."""
    # Common property keys across different GeoJSON sources
    candidates = [
        "NAME_2", "name_2",         # GADM level-2
        "DISTRICT", "district",
        "dtname", "DTNAME",
        "NAME_1", "name_1",
        "name", "NAME",
        "Name",
        "ST_NM", "st_nm",
    ]
    for key in candidates:
        val = props.get(key)
        if val and isinstance(val, str) and val.strip():
            return val.strip()
    # Fallback: return first non-empty string value
    for val in props.values():
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def normalize_name(raw: str) -> str | None:
    """Map a raw district name to the canonical standard name, or None."""
    lookup = raw.strip().upper()
    if lookup in _ALIASES:
        return _ALIASES[lookup]
    # Fuzzy: strip parentheticals, e.g. "Kandhamal (Phulbani)"
    base = lookup.split("(")[0].strip()
    if base in _ALIASES:
        return _ALIASES[base]
    return None


def round_coords(obj, decimals: int = 4):
    """Recursively round all coordinate numbers in a GeoJSON geometry."""
    if isinstance(obj, list):
        # If leaf is a coordinate pair/triple of numbers, round them
        if obj and isinstance(obj[0], (int, float)):
            return [round(v, decimals) for v in obj]
        return [round_coords(item, decimals) for item in obj]
    return obj


def simplify_geometry(geometry: dict, decimals: int = 4) -> dict:
    """Return geometry with coordinates rounded to `decimals` places."""
    if geometry is None:
        return geometry
    return {
        "type": geometry["type"],
        "coordinates": round_coords(geometry["coordinates"], decimals),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  Odisha District GeoJSON Fetcher & Normalizer")
    print("=" * 60)

    # 1. Download
    print("\n[1/4] Downloading GeoJSON …")
    geojson = download_geojson()

    # 2. Process features
    print("\n[2/4] Normalizing district names & simplifying geometry …")
    standard_set = set(STANDARD_NAMES)
    matched: dict[str, dict] = {}
    unmatched_raw: list[str] = []

    for feat in geojson["features"]:
        props = feat.get("properties", {})
        raw = _extract_raw_name(props)
        if raw is None:
            print(f"  [WARN] Feature with no recognizable name property — skipped.")
            continue

        std = normalize_name(raw)
        if std is None:
            print(f"  [WARN] Unmatched name: '{raw}'")
            unmatched_raw.append(raw)
            continue

        if std in matched:
            # Duplicate — keep first occurrence
            continue

        simplified_geom = simplify_geometry(feat.get("geometry"))
        matched[std] = {
            "type": "Feature",
            "properties": {"name": std},
            "geometry": simplified_geom,
        }
        print(f"  [OK] {raw:30s} -> {std}")

    # 3. Summary
    print(f"\n[3/4] Summary")
    print(f"  Matched districts : {len(matched)} / {len(STANDARD_NAMES)}")
    missing = sorted(standard_set - set(matched.keys()))
    if missing:
        print(f"  Missing districts : {', '.join(missing)}")
    if unmatched_raw:
        print(f"  Unmatched names   : {', '.join(unmatched_raw)}")

    # 4. Write JS module
    print(f"\n[4/4] Writing JS module -> {OUTPUT_JS}")
    os.makedirs(os.path.dirname(OUTPUT_JS), exist_ok=True)

    features_ordered = [matched[n] for n in STANDARD_NAMES if n in matched]
    collection = {
        "type": "FeatureCollection",
        "features": features_ordered,
    }

    js_json = json.dumps(collection, ensure_ascii=False, separators=(",", ":"))
    js_content = f"export const odishaGeoJSON = {js_json};\n"

    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write(js_content)

    size_kb = os.path.getsize(OUTPUT_JS) / 1024
    print(f"  [OK] Written {size_kb:.1f} KB ({len(features_ordered)} districts)")
    print("\nDone.")


if __name__ == "__main__":
    main()
