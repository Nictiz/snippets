# Wrap in Bundle

Tool to wrap a set of FHIR resources in a `transaction` Bundle that can be used to bulk POST a set of resources on a server (vibe coded).

The following features are supported:

* Takes either a set of XML of JSON files as input (no mixing).
* Creates a Bundle of type `transaction` in the same format as the input files.
* Strips all resource `id`'s.
* Rewrites all references using "Resource/id" format to the `fullUrl`'s in the Bundle.

Usage:

> python3 wrap_in_bundle.py -o [output.json/xml] [input_files]