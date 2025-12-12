import argparse
import json
import os
import sys

# -----------------------------
# CONFIG
# -----------------------------

VALID_ROLES = {
    'Serving-System',
    'Receiving-System',
    'XIS-Server',
    'Serving-XIS',
    'Validation-Serving-XIS',
    'Receiving-XIS'
}

EXCLUDE_DIRS = {'_LoadResources', '_reference'}

OUTPUT_FILENAME = "unieke_combinaties_all.json"


# -----------------------------
# UTILS
# -----------------------------

def walk_properties_files(root_dir):
    """Yield all properties.json files under a directory, skipping excluded dirs."""
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        if "properties.json" in filenames:
            yield os.path.join(dirpath, "properties.json")


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# -----------------------------
# EXTRACTOR
# -----------------------------

def extract_name_field(value):
    """Extract value['name'] if dict, otherwise return value (string or None)."""
    if isinstance(value, dict):
        return value.get("name")
    return value  # string or None


def extract_combination(path, branch):
    """Return normalized combination dict or None."""
    data = load_json(path)
    if not data:
        return None

    combo = {
        'branch' : branch, 
        'goal': data.get('goal'),
        'fhirVersion': data.get('fhirVersion'),
        'informationStandard': data.get('informationStandard'),
        'usecase': data.get('usecase'),
        'role': extract_name_field(data.get('role')),
        'category': data.get('category'),
        'subcategory': data.get('subcategory'),
        'serverAlias': data.get('serverAlias'),
        'variant': extract_name_field(data.get('variant'))
    }

    # Valid combo must have role and serverAlias
    if combo['role'] and combo['serverAlias'] is not None:
        return combo

    return None


def combination_key(combo):
    """Generate a unique key for deduplication."""
    return (
        combo['goal'],
        combo['fhirVersion'],
        combo['informationStandard'],
        combo['usecase'],
        combo['role'],
        combo['category'],
        combo['subcategory'],
        combo['serverAlias']
    )


# -----------------------------
# PROCESSOR
# -----------------------------

def process_folders(root, folders, branch, debug=False):
    combined = {}
    stats = {
        'scanned': 0,
        'accepted': 0,
        'rejected_no_combo': 0,
        'rejected_role': 0
    }

    for folder in folders:
        folder_path = os.path.join(root, folder)
        files = list(walk_properties_files(folder_path))

        print(f"[{folder}] gevonden properties.json: {len(files)}")

        for file in files:
            stats['scanned'] += 1

            combo = extract_combination(file, branch=branch)
            if debug:
                print(f"DEBUG: file={file} -> combo={combo}")

            if not combo:
                stats['rejected_no_combo'] += 1
                continue

            if combo['role'] not in VALID_ROLES:
                stats['rejected_role'] += 1
                if debug:
                    print(f"DEBUG: skipping role '{combo['role']}' in {file}")
                continue

            key = combination_key(combo)
            is_preferred = combo['variant'] == "Nictiz-intern"

            if key not in combined or is_preferred:
                combined[key] = combo
                stats['accepted'] += 1

    return combined.values(), stats


# -----------------------------
# CLI / MAIN
# -----------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract unique testset combinations from properties.json files."
    )
    parser.add_argument('--root', '-r', required=True,
                        help='Base root folder to look in.')
    parser.add_argument('--branch', '-b', default='main',
                        help='Branch naam om aan elk record toe te voegen (default: main)')
    parser.add_argument('--folders', '-f', nargs='+', required=True,
                        help='List of folders under root to process.')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging.')
    return parser.parse_args()


def validate_folders(root, folders):
    missing = []
    for folder in folders:
        path = os.path.join(root, folder)
        if not os.path.isdir(path):
            missing.append((folder, path))

    if missing:
        for folder, path in missing:
            print(f"ERROR: Folder not found: {folder} -> {path}")
        sys.exit(1)


def main():
    args = parse_args()
    root = os.path.abspath(args.root)

    print(f"Using root: {root}")
    validate_folders(root, args.folders)

    results, stats = process_folders(root, args.folders, branch=args.branch, debug=args.debug)

    # Write output
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FILENAME)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(list(results), f, indent=2, ensure_ascii=False)

    print(f"[ALL] Gevonden combinaties: {stats['accepted']} -> {out_path}")

    if args.debug:
        print("\nDEBUG SUMMARY")
        for key, value in stats.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
