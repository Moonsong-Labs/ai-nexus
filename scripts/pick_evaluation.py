"""Pick an evaluation."""

import os
import re
import subprocess
import sys

from anytree import Node, RenderTree
from pickpack import pickpack

# ruff: noqa: D103 T201


def find_evaluations(filepath):
    evaluations = []
    with open(filepath) as f:
        for line in f:
            match = re.search(r"def (test_\w+)", line)
            if match:
                evaluations.append(match.group(1))
    return evaluations


def get_evaluations(directory):
    """Recursively walks through a directory and collects evaluations."""
    try:
        children = []
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)

            if (
                os.path.isfile(full_path)
                and not item.startswith("_")
                and item.endswith(".py")
            ):
                if evaluations := find_evaluations(full_path):
                    children.append(
                        Node(item, children=map(lambda e: Node(f"<{e}>"), evaluations))
                    )

            if os.path.isdir(full_path) and not (
                item.startswith("_") or item.startswith(".")
            ):
                nested_children = get_evaluations(full_path)
                child = Node(item, children=nested_children)
                children.append(child)

        return children
    except OSError as e:
        print(f"Cannot access {directory}: {e}")
        sys.exit(1)


ROOT_NAME = "EXIT"
# NONE_NAME = "<< NONE >>"
ALL_NAME = "<< ALL >>"

evaluation_tree = get_evaluations("./tests/evaluations")
options = RenderTree(
    Node(ROOT_NAME, children=[Node(ALL_NAME, children=evaluation_tree)])
)
selected, _index = pickpack(options, "Select an evaluation:")

if selected.name in [ROOT_NAME]:
    sys.exit(0)

test_path = []
test_name = None

parent = selected.parent.name if selected.name != ALL_NAME else None
if parent is not None:
    test_path = [node.name for node in selected.parent.path if node.name != ALL_NAME]
    if parent.endswith(".py"):
        test_name = selected.name.strip("<>")
    else:
        test_path.append(selected.name)

path = os.path.join(
    "tests",
    "evaluations",
    *test_path,
)
if test_name:
    path = f"{path}::{test_name}"

cmd = ["uv", "run", "--", "pytest", "-s", path]
print(" ".join(cmd))
subprocess.run(cmd)
