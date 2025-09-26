"""Generate the code reference pages and navigation."""

from pathlib import Path
import mkdocs_gen_files
import ast

verbose = False


def get_module_functions(module_path):
    """Extract function names from a Python file."""
    if verbose:
        print(f"Trying to parse: {module_path}")
    try:
        with open(module_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            if verbose:
                print(f"  -> File is empty")
            return [], []

        tree = ast.parse(content)

        functions = []
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith("_"):
                    functions.append(node.name)
                    if verbose:
                        print(f"  -> Found function: {node.name}")
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith("_"):
                    classes.append(node.name)
                    if verbose:
                        print(f"  -> Found class: {node.name}")

        return functions, classes
    except Exception as e:
        print(f"  -> Error parsing {module_path}: {e}")
        return [], []


nav = mkdocs_gen_files.Nav()

package_name = "neptoon"

for path in sorted(Path(package_name).rglob("*.py")):
    if verbose:
        print(f"\nProcessing: {path}")

    module_path = path.relative_to(package_name).with_suffix("")
    doc_path = path.relative_to(package_name).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = list(module_path.parts)
    if verbose:
        print(f"Original parts: {parts}")

    if not parts:
        if verbose:
            print("Skipping: empty parts")
        continue

    if parts[-1] == "__init__":
        if len(parts) == 1:
            parts = ["index"]
            doc_path = Path("index.md")
            full_doc_path = Path("reference", "index.md")
        else:
            parts = parts[:-1]
            doc_path = doc_path.with_name("index.md")
            full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__":
        if verbose:
            print("Skipping: __main__")
        continue

    if not parts:
        if verbose:
            print("Skipping: parts empty after processing")
        continue

    if verbose:
        print(f"Final parts: {parts}")
        print(f"Doc path: {doc_path}")

    nav[tuple(parts)] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        if parts == ["index"]:
            page_path = package_name
            breadcrumps = ""
            title = package_name
        else:
            page_path = ".".join([package_name] + parts)
            breadcrumps = ".".join([package_name] + parts[:-1])
            title = parts[-1]

        if verbose:
            print(f"Writing page for: {title}")

        fd.write(f"{breadcrumps}\n\n")
        fd.write(f"# {title}\n\n")

        # Get functions and classes for TOC
        functions, classes = get_module_functions(path)

        if functions or classes:
            # fd.write("## Contents\n\n")
            if classes:
                fd.write("**Classes:**\n\n")
                for cls in classes:
                    full_cls_path = f"{page_path}.{cls}".lower()
                    fd.write(f"- [{cls}](#{full_cls_path})  \n")
                fd.write("\n")
            if functions:
                fd.write("**Functions:**\n\n")
                for func in functions:
                    full_func_path = f"{page_path}.{func}".lower()
                    fd.write(f"- [{func}](#{full_func_path})  \n")
                fd.write("\n")

        fd.write(f"::: {page_path}\n")
        fd.write("    options:\n")
        fd.write("      heading_level: 3\n")

        if verbose:
            print(f"Successfully wrote page for {title}")

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())

print("Generation complete!")
