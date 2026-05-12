import json
import os


def find_properties_json_files(root_dir):
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename == 'properties.json':
                yield os.path.join(dirpath, filename)


def extract_combinations(file_path):
    with open(file_path, encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception:
            return None
    goal = data.get('goal')
    role = data.get('role')
    if isinstance(role, dict):
        role = role.get('name')
    category = data.get('category')
    subcategory = data.get('subcategory')
    server_alias = data.get('serverAlias')
    variant = data.get('variant')
    if isinstance(variant, dict):
        variant = variant.get('name')
    # Add when role and serverAlias are filled (category/subcategory/variant may be empty).
    if role and server_alias is not None:
        return {
            'goal': goal,
            'role': role,
            'category': category,
            'subcategory': subcategory,
            'serverAlias': server_alias,
            'variant': variant
        }
    return None


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root = os.path.join(script_dir, '..', '..', '..', 'Nictiz-testscripts', 'output', 'R4', 'MP9-3-0-0-beta')
    root = os.path.abspath(root)
    print(root)

    # Process MedMij and MO separately.
    for folder in ['MedMij', 'MO']:
        folder_path = os.path.join(root, folder)
        combinations = {}
        for file in find_properties_json_files(folder_path):
            combo = extract_combinations(file)
            if combo and combo['role'] in ['Serving-System', 'Receiving-System']:
                key = (combo['goal'], combo['role'], combo['category'], combo['subcategory'], combo['serverAlias'])
                variant = combo['variant']
                if key not in combinations or variant == "Nictiz-intern":
                    combinations[key] = combo
        result = list(combinations.values())
        outname = f'unique_combinations_{folder.lower()}.json'
        with open(os.path.join(script_dir, outname), 'w', encoding='utf-8') as out:
            json.dump(result, out, indent=2, ensure_ascii=False)
        print(f'[{folder}] Found combinations: {len(result)}')

if __name__ == '__main__':
    main()
