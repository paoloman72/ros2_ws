#!/usr/bin/env python3
"""Generate bt_manifest.yaml + the bundle ZIP for a bt_devkit mission.

The manifest is not maintained by hand: it is derived at bundle time from
the project's sources of truth:

  nodes:            registerNodeType<...>("...") in src/register_nodes.cpp
  node headers:     the include/*.hpp file declaring each class
  dependencies:     <depend> entries in package.xml (minus bt_devkit)
  plugin.name:      target arg of bt_devkit_add_mission() in CMakeLists.txt
  tree.main:        behavior_trees/main.xml (or -t <tree>)
  monitoring:       navigate_to_pose, if the tree uses <NavigateToPose .../>

The staged bundle contains only what the platform needs (manifest + tree +
include/ + src/). Local-only files (register_nodes.cpp, CMakeLists.txt,
package.xml, a hand-written manifest) are never copied.

Examples:
  python3 bt_make_bundle.py src/my_mission
      # -> ./my_mission_bundle.zip  (stage dir ./my_mission_bundle/)
  python3 bt_make_bundle.py src/my_mission -o bundles/my_mission_bundle.zip
  python3 bt_make_bundle.py src/my_mission --dry-run
  python3 bt_make_bundle.py src/my_mission -t behavior_trees/hello.xml --vendor
"""

import argparse
import os
import re
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET

BT_BUILTINS = {
    "Action", "Control", "Decorator", "Sequence", "SequenceStar", "Fallback",
    "FallbackStar", "Reactor", "Inverter", "ForceSuccess", "ForceFailure",
    "RetryUntilSuccessful", "Repeat", "RateController", "SetBlackboardValue",
    "SetInput", "GetInput", "ComputeExpression", "WaitForBlackboardValue",
    "Log", "Tree", "SubTree",
}

REGISTER_RE = re.compile(r'registerNodeType\s*<\s*([^>]+?)\s*>\s*\(\s*"([^"]+)"\s*\)')


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def warn(msg):
    print(f"warning: {msg}", file=sys.stderr)


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def parse_register_file(path):
    """[(class, id)] for every registerNodeType<...>("...") in the file.

    An unqualified class is qualified with the nearest preceding namespace
    (e.g. 'ExampleNode' under 'namespace bt_devkit' -> 'bt_devkit::ExampleNode').
    """
    text = read(path)
    ns_re = re.compile(r"^\s*namespace\s+(\w+)\s*[\{;]", re.M)
    pairs = []
    for m in REGISTER_RE.finditer(text):
        cls = m.group(1)
        if "::" not in cls:
            namespaces = [n.group(1) for n in ns_re.finditer(text[:m.start()])]
            if namespaces:
                cls = namespaces[-1] + "::" + cls
        pairs.append((cls, m.group(2)))
    if not pairs:
        die(f"no registerNodeType<...>(\"...\") calls found in {path}")
    return pairs


def parse_package_xml(path):
    root = ET.parse(path).getroot()
    name_el = root.find("name")
    if name_el is None or not name_el.text:
        die(f"package.xml has no <name>: {path}")
    deps = [d.text.strip() for d in root.findall("depend") if d.text and d.text.strip()]
    return name_el.text.strip(), deps


def parse_tree_tags(path):
    root = ET.parse(path).getroot()
    return {el.tag for el in root.iter() if el.tag not in ("root", "BehaviorTree")}


def resolve_headers(nodes, include_dir):
    """{node_id: (class, header_name)} — the single include/ header declaring the class."""
    files = {}
    if os.path.isdir(include_dir):
        for fn in sorted(os.listdir(include_dir)):
            if fn.endswith((".hpp", ".h")):
                files[fn] = read(os.path.join(include_dir, fn))
    resolved = {}
    for cls, nid in nodes:
        base = cls.split("::")[-1]
        decl = re.compile(r"\bclass\s+" + re.escape(base) + r"\b")
        matches = [fn for fn, content in files.items() if decl.search(content)]
        if len(matches) != 1:
            die(f"cannot resolve header for class '{cls}' (node '{nid}'): "
                f"expected exactly 1 match in {include_dir}, got {matches}")
        resolved[nid] = (cls, matches[0])
    return resolved


def parse_plugin_name(cmake_path, fallback):
    if os.path.isfile(cmake_path):
        m = re.search(r"bt_devkit_add_mission\s*\(\s*(\w+)", read(cmake_path))
        if m:
            return m.group(1)
    warn(f"bt_devkit_add_mission(<target>) not found in {cmake_path}; "
         f"using plugin name '{fallback}'")
    return fallback


def build_deps(pkg_deps):
    deps = ["rclcpp", "behaviortree_cpp"]
    for d in pkg_deps:
        if d not in deps and d not in ("bt_devkit", "ament_cmake"):
            deps.append(d)
    return deps


def derive_monitoring(tree_text):
    actions = []
    if re.search(r"<NavigateToPose\b", tree_text):
        actions.append("navigate_to_pose")
    return actions


def find_header_for_class(base, header_dir):
    """Name of the header in header_dir declaring 'class <base>' (None if absent)."""
    if not os.path.isdir(header_dir):
        return None
    decl = re.compile(r"\bclass\s+" + re.escape(base) + r"\b")
    for fn in sorted(os.listdir(header_dir)):
        if fn.endswith((".hpp", ".h")) and decl.search(read(os.path.join(header_dir, fn))):
            return fn
    return None


def locate_flow_a(explicit_prefix):
    """Locate the Flow A (extra node) register file + header dir.

    Checks installed devkit prefixes first (a prefix is accepted only if its
    register file is a *real* readable file — installs built inside a
    container may contain dangling symlinks to the container path), then
    falls back to the bt_devkit source tree that contains this script.
    """
    prefixes = []
    if explicit_prefix:
        prefixes.append(explicit_prefix)
    prefixes += [p for p in os.environ.get("AMENT_PREFIX_PATH", "").split(os.pathsep) if p]
    for p in prefixes:
        reg = os.path.join(p, "share", "bt_devkit", "extra_nodes_src",
                           "register_extra_nodes.cpp")
        if os.path.isfile(reg):
            return reg, os.path.join(p, "include", "bt_devkit", "extra_nodes")
    src_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reg = os.path.join(src_root, "extra_nodes", "src", "register_extra_nodes.cpp")
    if os.path.isfile(reg):
        return reg, os.path.join(src_root, "extra_nodes", "include",
                                 "bt_devkit", "extra_nodes")
    return None, None


def render_manifest(tree_rel, plugin, deps, node_entries, actions):
    lines = [
        "# bt_manifest.yaml — GENERATED by bt_devkit/scripts/bt_make_bundle.py.",
        "# Do not edit by hand: it is derived from register_nodes.cpp,",
        "# package.xml, CMakeLists.txt and the behavior trees.",
        "version: 1",
        "",
        "tree:",
        f"  main: {tree_rel}",
        "",
        "plugin:",
        f"  name: {plugin}",
        "",
        "dependencies:",
    ]
    lines += [f"  - {d}" for d in deps]
    lines += ["", "nodes:"]
    for e in node_entries:
        lines += [f"  - id: {e['id']}",
                  f"    class: {e['class']}",
                  f"    header: {e['header']}"]
    if actions:
        lines += ["", "monitoring:", "  actions:"]
        lines += [f"    - {a}" for a in actions]
    return "\n".join(lines) + "\n"


def stage_bundle(stage_dir, project, tree_rel, manifest, resolved, vendored):
    """Copy exactly the bundle contents into stage_dir; return the file list."""
    if os.path.isdir(stage_dir):
        shutil.rmtree(stage_dir)
    for sub in ("behavior_trees", "include", "src"):
        os.makedirs(os.path.join(stage_dir, sub))
    with open(os.path.join(stage_dir, "bt_manifest.yaml"), "w", encoding="utf-8") as fh:
        fh.write(manifest)
    staged = ["bt_manifest.yaml"]

    def put(src, dst):
        if not os.path.isfile(src):
            die(f"missing file: {src}")
        shutil.copy2(src, os.path.join(stage_dir, dst))
        staged.append(dst)

    put(os.path.join(project, tree_rel),
        os.path.join("behavior_trees", os.path.basename(tree_rel)))
    for nid, (cls, hdr) in resolved.items():
        put(os.path.join(project, "include", hdr), os.path.join("include", hdr))
        put(os.path.join(project, "src", os.path.splitext(hdr)[0] + ".cpp"),
            os.path.join("src", os.path.splitext(hdr)[0] + ".cpp"))
    for v in vendored:
        put(v["hpp"], os.path.join("include", v["header"]))
        put(v["cpp"], os.path.join("src", os.path.splitext(v["header"])[0] + ".cpp"))
    return sorted(staged)


def make_zip(zip_path, stage_dir):
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, fns in os.walk(stage_dir):
            dirs.sort()
            for fn in sorted(fns):
                full = os.path.join(root, fn)
                zf.write(full, os.path.relpath(full, stage_dir))


def main():
    ap = argparse.ArgumentParser(
        description="Generate bt_manifest.yaml + bundle ZIP for a bt_devkit mission.")
    ap.add_argument("project", help="mission project directory (e.g. src/my_mission)")
    ap.add_argument("-t", "--tree", default="behavior_trees/main.xml",
                    help="tree the platform will run (default: behavior_trees/main.xml)")
    ap.add_argument("-o", "--output", default=None,
                    help="output zip (default: <package>_bundle.zip in the current directory)")
    ap.add_argument("--stage", default=None,
                    help="bundle staging dir (default: <output> without .zip)")
    ap.add_argument("--dry-run", action="store_true",
                    help="derive everything and print the manifest; write nothing")
    ap.add_argument("--vendor", action="store_true",
                    help="vendor Flow A (bt_devkit extra) nodes into the bundle")
    ap.add_argument("--devkit-prefix", default=None,
                    help="installed bt_devkit prefix (default: auto from AMENT_PREFIX_PATH "
                         "or the devkit source tree)")
    args = ap.parse_args()

    project = os.path.abspath(args.project)
    if not os.path.isdir(project):
        die(f"project directory not found: {project}")
    pkg, pkg_deps = parse_package_xml(os.path.join(project, "package.xml"))
    zip_path = os.path.abspath(args.output or os.path.join(os.getcwd(), f"{pkg}_bundle.zip"))
    zip_parent = os.path.dirname(zip_path)
    if zip_parent:
        os.makedirs(zip_parent, exist_ok=True)
    stage_dir = os.path.abspath(
        args.stage or (zip_path[:-4] if zip_path.lower().endswith(".zip")
                       else zip_path + "_stage"))

    register = os.path.join(project, "src", "register_nodes.cpp")
    if not os.path.isfile(register):
        die(f"missing {register}")
    nodes = parse_register_file(register)
    if len({i for _, i in nodes}) != len(nodes):
        die("duplicate node id in register_nodes.cpp")
    resolved = resolve_headers(nodes, os.path.join(project, "include"))

    tree_path = os.path.join(project, args.tree)
    if not os.path.isfile(tree_path):
        die(f"tree not found: {tree_path}")
    tree_text = read(tree_path)
    actions = derive_monitoring(tree_text)

    # Gate 1-lite: every node the tree uses must be registered (or built-in);
    # Flow A (bt_devkit extra) nodes must be vendored to stay self-contained.
    vendored = []
    unknown = sorted(parse_tree_tags(tree_path) - {i for _, i in nodes} - BT_BUILTINS)
    if unknown:
        reg_file, hdr_dir = locate_flow_a(args.devkit_prefix)
        flow_a = {}
        if reg_file:
            flow_a = {nid: cls for cls, nid in parse_register_file(reg_file)}
        for uid in unknown:
            if uid in flow_a:
                if not args.vendor:
                    die(f"tree uses Flow A node '{uid}' (lives in bt_devkit, not in the "
                        f"project): bundles must be self-contained — re-run with --vendor")
                base = flow_a[uid].split("::")[-1]
                hdr = find_header_for_class(base, hdr_dir)
                if hdr is None:
                    die(f"cannot find a header declaring class '{base}' in {hdr_dir} "
                        f"(bt_devkit headers missing — re-install bt_devkit)")
                vendored.append({
                    "id": uid,
                    "class": flow_a[uid],
                    "header": hdr,
                    "hpp": os.path.join(hdr_dir, hdr),
                    "cpp": os.path.join(os.path.dirname(reg_file),
                                        os.path.splitext(hdr)[0] + ".cpp"),
                })
            else:
                warn(f"tree uses node '{uid}' that is neither registered in "
                     f"src/register_nodes.cpp nor a BehaviorTree.CPP built-in — "
                     f"Gate 1 on the platform will reject it")

    plugin = parse_plugin_name(os.path.join(project, "CMakeLists.txt"), f"{pkg}_nodes")
    node_entries = [{"id": i, "class": c, "header": resolved[i][1]} for c, i in nodes]
    node_entries += [{"id": v["id"], "class": v["class"], "header": v["header"]}
                     for v in vendored]
    manifest = render_manifest(args.tree, plugin, build_deps(pkg_deps),
                               node_entries, actions)

    print("=== generated bt_manifest.yaml ===")
    print(manifest, end="")

    if args.dry_run:
        print("=== dry run: nothing written ===")
        return

    staged = stage_bundle(stage_dir, project, args.tree, manifest, resolved, vendored)
    make_zip(zip_path, stage_dir)
    print(f"=== staged bundle ({stage_dir}) ===")
    for f in staged:
        print(f"  {f}")
    print(f"=== zip ===\n  {zip_path}")
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            print(f"  {info.filename} ({info.file_size} bytes)")
    print("\nUpload this zip; the platform runs Gate 1 on it and builds the plugin "
          "from the manifest.")


if __name__ == "__main__":
    main()


