#!/usr/bin/env python3
"""
Wrap a set of FHIR resource files in a FHIR Bundle of type `transaction`.

Supported inputs:
- JSON (.json)
- XML (.xml)

Output format rule:
- If all inputs are JSON → emit a JSON Bundle
- If all inputs are XML → emit an XML Bundle
- If inputs are mixed → exit with an error (no output)

Behavior:
- Always uses `request.method`: POST
- Always strips `id` fields
- Uses `request.url`: `<resourceType>`
- Adds `fullUrl`: `urn:uuid:<uuid4>`
- Automatically rewrites internal references (`ResourceType/id`) to the matching `fullUrl`
- Warns when a reference cannot be resolved to any resource in the input

Examples:
  python bundle_transaction.py ./json-resources -o bundle.json
  python bundle_transaction.py ./xml-resources -o bundle.xml
  python bundle_transaction.py patients.json observations.xml -o bundle.any
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import uuid
import xml.etree.ElementTree as ET
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

FHIR_JSON_EXTS = {".json"}
FHIR_XML_EXTS = {".xml"}

_REF_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,63}/[A-Za-z0-9\-.]{1,64}$")

ET.register_namespace("", "http://hl7.org/fhir")

@dataclass
class Options:
    output: Optional[Path]

@dataclass
class ResourceItem:
    kind: str  # 'json' | 'xml'
    resourceType: str
    id: Optional[str]
    payload: Any  # dict for JSON, ET.Element for XML

# ------------------------- Loaders -------------------------

def _validate_resource_dict(res: Dict[str, Any], source: str) -> None:
    if not isinstance(res, dict) or not res.get("resourceType"):
        raise ValueError(f"Not a FHIR resource in {source}: missing resourceType")


def load_json_items(path: Path) -> Iterable[ResourceItem]:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if isinstance(obj, dict) and obj.get("resourceType") == "Bundle":
        for j, e in enumerate(obj.get("entry") or [], start=1):
            r = e.get("resource")
            _validate_resource_dict(r, f"{path} (bundle entry {j})")
            yield ResourceItem("json", r["resourceType"], r.get("id"), r)
    else:
        _validate_resource_dict(obj, str(path))
        yield ResourceItem("json", obj["resourceType"], obj.get("id"), obj)


def _local(tag: str) -> str:
    return tag.split('}', 1)[-1]


def _ns(tag: str) -> Optional[str]:
    return tag.split('}', 1)[0][1:] if tag.startswith('{') else None


def _find_child(elem: ET.Element, local: str) -> Optional[ET.Element]:
    for c in list(elem):
        if _local(c.tag) == local:
            return c
    return None


def _read_id_from_xml(root: ET.Element) -> Optional[str]:
    id_el = _find_child(root, "id")
    if id_el is None:
        return None
    return id_el.attrib.get("value")


def _iter_bundle_resources_from_xml(bundle_root: ET.Element) -> Iterable[ET.Element]:
    for entry in bundle_root.findall(".//{*}entry"):
        res_container = entry.find("{*}resource")
        if res_container is None:
            continue
        for child in list(res_container):
            yield child


def load_xml_items(path: Path) -> Iterable[ResourceItem]:
    tree = ET.parse(path)
    root = tree.getroot()
    rtype = _local(root.tag)
    if rtype == "Bundle":
        for res_el in _iter_bundle_resources_from_xml(root):
            yield ResourceItem("xml", _local(res_el.tag), _read_id_from_xml(res_el), res_el)
    else:
        yield ResourceItem("xml", rtype, _read_id_from_xml(root), root)


def iter_input_paths(inputs: Sequence[Path]) -> Iterable[Path]:
    for p in inputs:
        if p.is_dir():
            for child in sorted(p.rglob("*")):
                if child.is_file() and child.suffix.lower() in (FHIR_JSON_EXTS | FHIR_XML_EXTS):
                    yield child
        elif p.is_file() and p.suffix.lower() in (FHIR_JSON_EXTS | FHIR_XML_EXTS):
            yield p

# ------------------------- Bundle builders -------------------------

def _assign_fullurls(items: Iterable[ResourceItem]) -> Tuple[List[ResourceItem], Dict[str, str], Dict[int, str]]:
    items_list: List[ResourceItem] = list(items)
    refmap: Dict[str, str] = {}
    index_to_fullurl: Dict[int, str] = {}
    for i, it in enumerate(items_list):
        fu = f"urn:uuid:{uuid.uuid4()}"
        index_to_fullurl[i] = fu
        if it.id:
            refmap[f"{it.resourceType}/{it.id}"] = fu
    return items_list, refmap, index_to_fullurl


def _rewrite_references_json(node: Any, refmap: Dict[str, str], unresolved: List[str]) -> Any:
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k == "reference" and isinstance(v, str) and _REF_KEY_RE.match(v):
                if v in refmap:
                    out[k] = refmap[v]
                else:
                    unresolved.append(v)
                    out[k] = v
            else:
                out[k] = _rewrite_references_json(v, refmap, unresolved)
        return out
    if isinstance(node, list):
        return [_rewrite_references_json(x, refmap, unresolved) for x in node]
    return node


def build_json_bundle(items: Iterable[ResourceItem]) -> Dict[str, Any]:
    items_list, refmap, index_to_fullurl = _assign_fullurls(items)
    entries = []
    unresolved: List[str] = []
    for i, it in enumerate(items_list):
        res = copy.deepcopy(it.payload)
        res.pop("id", None)
        res = _rewrite_references_json(res, refmap, unresolved)
        entry = {
            "fullUrl": index_to_fullurl[i],
            "resource": res,
            "request": {"method": "POST", "url": it.resourceType},
        }
        entries.append(entry)

    if unresolved:
        print("Warning: unresolved references detected:", file=sys.stderr)
        for r in sorted(set(unresolved)):
            print(f"  - {r}", file=sys.stderr)

    return {"resourceType": "Bundle", "type": "transaction", "entry": entries}


def _rewrite_references_xml(elem: ET.Element, refmap: Dict[str, str], unresolved: List[str]) -> None:
    for ref_el in elem.findall(".//{*}reference"):
        val = ref_el.attrib.get("value")
        if not val:
            continue
        if _REF_KEY_RE.match(val):
            if val in refmap:
                ref_el.set("value", refmap[val])
            else:
                unresolved.append(val)


def build_xml_bundle(items: Iterable[ResourceItem], namespace: Optional[str]) -> ET.ElementTree:
    items_list, refmap, index_to_fullurl = _assign_fullurls(items)
    ns = namespace or "http://hl7.org/fhir"
    def T(local: str) -> str:
        return f"{{{ns}}}{local}"

    bundle = ET.Element(T("Bundle"))
    type_el = ET.SubElement(bundle, T("type"))
    type_el.set("value", "transaction")

    unresolved: List[str] = []

    for i, it in enumerate(items_list):
        entry = ET.SubElement(bundle, T("entry"))
        full = ET.SubElement(entry, T("fullUrl"))
        full.set("value", index_to_fullurl[i])

        res_container = ET.SubElement(entry, T("resource"))
        res_el = copy.deepcopy(it.payload)
        for child in list(res_el):
            if _local(child.tag) == "id":
                res_el.remove(child)
                break
        _rewrite_references_xml(res_el, refmap, unresolved)
        res_container.append(res_el)

        req = ET.SubElement(entry, T("request"))
        m_el = ET.SubElement(req, T("method"))
        m_el.set("value", "POST")
        u_el = ET.SubElement(req, T("url"))
        u_el.set("value", it.resourceType)

    if unresolved:
        print("Warning: unresolved references detected:", file=sys.stderr)
        for r in sorted(set(unresolved)):
            print(f"  - {r}", file=sys.stderr)

    return ET.ElementTree(bundle)

# ------------------------- CLI / Orchestration -------------------------

def parse_args(argv: List[str]) -> Tuple[List[Path], Options]:
    p = argparse.ArgumentParser(description="Wrap FHIR resources into a transaction Bundle")
    p.add_argument("inputs", nargs="+", help="Input files or directories (.json/.xml)")
    p.add_argument("-o", "--output", type=Path, help="Output file (json or xml, determined by inputs)")
    args = p.parse_args(argv)
    return [Path(s) for s in args.inputs], Options(args.output)


def main(argv: List[str]) -> int:
    inputs, opts = parse_args(argv)

    files = list(iter_input_paths(inputs))
    if not files:
        print("No input files found (accepted: .json, .xml)", file=sys.stderr)
        return 1

    kinds = set("xml" if f.suffix.lower() in FHIR_XML_EXTS else "json" for f in files)
    if len(kinds) > 1:
        print("Error: Mixed input types (JSON and XML). Provide only one kind.", file=sys.stderr)
        return 2

    kind = kinds.pop()

    if kind == "json":
        items: List[ResourceItem] = []
        for f in files:
            items.extend(load_json_items(f))
        bundle = build_json_bundle(items)
        out = json.dumps(bundle, indent=2, ensure_ascii=False)
        if opts.output:
            try:
                opts.output.parent.mkdir(parents=True, exist_ok=True)
                opts.output.write_text(out + "\n", encoding="utf-8")
            except OSError as e:
                print(f"Failed to write {opts.output}: {e}", file=sys.stderr)
                return 3
        else:
            print(out)
        return 0

    # XML path
    xml_items: List[ResourceItem] = []
    first_ns: Optional[str] = None
    for f in files:
        for it in load_xml_items(f):
            xml_items.append(it)
            if first_ns is None:
                first = it.payload
                first_ns = _ns(first.tag)
    tree = build_xml_bundle(xml_items, first_ns)

    if opts.output:
        try:
            opts.output.parent.mkdir(parents=True, exist_ok=True)
            tree.write(opts.output, encoding="utf-8", xml_declaration=True)
        except OSError as e:
            print(f"Failed to write {opts.output}: {e}", file=sys.stderr)
            return 3
    else:
        sys.stdout.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        sys.stdout.write(ET.tostring(tree.getroot(), encoding="unicode"))
        sys.stdout.write("\n")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
