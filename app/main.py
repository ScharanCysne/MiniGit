import os
import sys
import zlib

from hashlib import sha1
from typing import List


def init_command():
    os.mkdir(".git")
    os.mkdir(".git/objects")
    os.mkdir(".git/refs")
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/master\n")

    sys.stdout.write("Initialized git directory!\n")


def catfile_command(args: List[str]):
    # Retrieve type and object name of cat-file command
    cmd_type, object_name = args
    object_path = f".git/objects/{object_name[:2]}/{object_name[2:]}"

    with open(object_path, "rb") as file:
        # Read git object and decompress zlib
        file_binary_content = file.read()
        file_content = zlib.decompress(file_binary_content).decode("utf-8")

        # Split contents given pattern: blob <size>\0<content>
        object_metadata, object_content = file_content.split("\0")
        object_type, object_size = object_metadata.split(" ")

        if cmd_type == "-t":
            sys.stdout.write(object_type)

        if cmd_type == "-s":
            sys.stdout.write(object_size)

        if cmd_type == "-p":
            sys.stdout.write(object_content)


def hashobject_command(args: List[str]):
    # Read contents of file
    if len(args) == 2:
        cmd_type, file_path = args
    else:
        cmd_type = ""
        file_path = args[0]

    with open(file_path, "r") as file:
        file_content = file.read()
        file_content = f"blob {len(file_content)}\0{file_content}"

        file_binary_content = file_content.encode("utf-8")
        file_compressed_content = zlib.compress(file_binary_content)

        file_sha = sha1(file_binary_content).hexdigest()
        object_path = f".git/objects/{file_sha[:2]}/{file_sha[2:]}"
        sys.stdout.write(file_sha)

        if cmd_type == "-w":
            os.makedirs(f".git/objects/{file_sha[:2]}", exist_ok=True)
            with open(object_path, mode="wb") as new_object:
                new_object.write(file_compressed_content)


def lstree_command(args: List[str]):
    # Read contents of file
    if len(args) == 2:
        cmd_type, tree_sha = args
    else:
        cmd_type = ""
        tree_sha = args[0]

    # Tree object path
    object_path = f".git/objects/{tree_sha[:2]}/{tree_sha[2:]}"

    with open(object_path, "rb") as file:
        # Read git object and decompress zlib
        file_binary_content = file.read()
        file_content = zlib.decompress(file_binary_content)

        # Parse each line and print it in desired format
        modes = [b"040000", b"100644", b"100755", b"120000"]
        pos = min(
            file_content.find(mode) for mode in modes if file_content.find(mode) != -1
        )
        file_content = file_content[pos:]

        while file_content:
            next_pos = [
                file_content[1:].find(mode)
                for mode in modes
                if file_content[1:].find(mode) != -1
            ]

            if not next_pos:
                next_pos = 0
                file_mode, file_name_sha = file_content.split(b" ")
                file_name, file_sha = file_name_sha.split(b"\0")
            else:
                next_pos = min(next_pos)
                file_mode, file_name_sha = file_content[:next_pos].split(b" ")
                file_name, file_sha = file_name_sha.split(b"\0")

            file_sha = file_sha.hex()
            file_mode = file_mode.decode("utf-8")
            file_name = file_name.decode("utf-8")
            file_type = "tree" if file_mode == "040000" else "blob"

            if cmd_type == "--name-only":
                sys.stdout.write(file_name + "\n")
            else:
                sys.stdout.write(f"{file_mode} {file_type} {file_sha} {file_name}\n")

            if next_pos == 0:
                break

            pos = next_pos
            file_content = file_content[pos:]


def main():
    command = sys.argv[1]
    args = sys.argv[2:]

    # Command: git init
    if command == "init":
        init_command()
    elif command == "cat-file":
        catfile_command(args)
    elif command == "hash-object":
        hashobject_command(args)
    elif command == "ls-tree":
        lstree_command(args)
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
