import os
import sys
import zlib

from typing import List


def init_command():
    os.mkdir(".git")
    os.mkdir(".git/objects")
    os.mkdir(".git/refs")
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/master\n")

    print("Initialized git directory!\n")


def catfile_command(args: List[str]):
    # Retrieve type and object name of cat-file command
    cmd_type, object_name = args
    object_path = f".git/objects/{object_name[:2]}/{object_name[2:]}"

    with open(object_path, "rb") as file:
        # Read git object and decompress zlib
        file_binary_content = file.read()
        file_content = zlib.decompress(file_binary_content).decode("utf-8")

        # Split contents given pattern: blob <size>\0<content>
        object_metadata, object_content = file_content.strip("\n").split("\0")
        object_type, object_size = object_metadata.split(" ")

        if cmd_type == "-t":
            print(object_type)

        if cmd_type == "-s":
            print(object_size)

        if cmd_type == "-p":
            print(object_content)


def main():
    command = sys.argv[1]
    args = sys.argv[2:]

    # Command: git init
    if command == "init":
        init_command()
    elif command == "cat-file":
        catfile_command(args)
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
