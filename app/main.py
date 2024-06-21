import os
import sys
import time
import zlib

from hashlib import sha1
from typing import List, Tuple


def init_command():
    os.mkdir(".git")
    os.mkdir(".git/objects")
    os.mkdir(".git/refs")
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/master\n")

    sys.stdout.write("Initialized git directory!\n")


def hash_object(data: bytes, obj_type="blob"):
    # Create header
    header = f"{obj_type} {len(data)}\0"
    # Combine header with file data
    store = header.encode() + data
    # Calculate SHA-1 hash of the combined content (uncompressed)
    object_sha = sha1(store).hexdigest()
    # Create storage path based on hash
    path = os.path.join(".git", "objects", object_sha[:2], object_sha[2:])
    # Create necessary directories
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Store the compressed file
    with open(path, "wb") as f:
        f.write(zlib.compress(store))

    return object_sha


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


def hashobject_command(args: List[str], log_sha: bool = True) -> Tuple[int, str, str]:
    # Read contents of file
    if len(args) == 2:
        cmd_type, file_path = args
    else:
        cmd_type = ""
        file_path = args[0]

    # Get file mode
    file_mode = str(oct(os.stat(file_path).st_mode))[2:]

    with open(file_path, "r") as file:
        file_content = file.read()
        file_content = f"blob {len(file_content)}\0{file_content}"

        file_binary_content = file_content.encode("utf-8")
        file_compressed_content = zlib.compress(file_binary_content)

        file_sha = sha1(file_binary_content).hexdigest()
        object_path = f".git/objects/{file_sha[:2]}/{file_sha[2:]}"
        if log_sha:
            sys.stdout.write(file_sha)

        if cmd_type == "-w":
            os.makedirs(f".git/objects/{file_sha[:2]}", exist_ok=True)
            with open(object_path, mode="wb") as new_object:
                new_object.write(file_compressed_content)

        return len(file_content), file_sha, file_mode


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


def writetree_command(
    working_directory: str = "", log_sha: bool = True
) -> Tuple[int, str, str]:
    # Iterate over the files/directories in the working directory
    if not working_directory:
        working_directory = os.getcwd()

    tree_size = 0
    tree_content = ""

    paths = [path for path in sorted(os.listdir(working_directory)) if path != ".git"]
    paths = [path for path in paths if os.path.isdir(path)] + [
        path for path in paths if os.path.isfile(path)
    ]

    for path in paths:
        if os.path.isdir(path):
            # If the entry is a directory, create a tree object and record its SHA hash
            blob_len, blob_sha, blob_mode = writetree_command(path, False)
        else:
            # If the entry is a file, create a blob object and record its SHA hash
            blob_len, blob_sha, blob_mode = hashobject_command(["-w", path], False)

        tree_size += blob_len
        blob_name = os.path.basename(path)
        tree_content += f"{blob_mode} {blob_name}\0{blob_sha}"

    # Once you have all the entries and their SHA hashes, write the tree object to
    # the .git/objects directory
    header = f"tree {tree_size}\0"
    tree_content = header + tree_content

    # Compress and convert
    tree_binary_content = tree_content.encode("utf-8")
    tree_compressed_content = zlib.compress(tree_binary_content)

    tree_40c_sha = sha1(tree_compressed_content).hexdigest()
    tree_20c_sha = str(sha1(tree_compressed_content).digest())[2:-1]
    object_path = f".git/objects/{tree_40c_sha[:2]}/{tree_40c_sha[2:]}"
    if log_sha:
        sys.stdout.write(tree_40c_sha)

    os.makedirs(f".git/objects/{tree_40c_sha[:2]}", exist_ok=True)
    with open(object_path, mode="wb") as new_object:
        new_object.write(tree_compressed_content)

    return tree_size, tree_20c_sha, "040000"


def committree_command(args: List[str]):
    tree_sha = args[0]
    parent_sha = None
    message = None
    if "-p" in args:
        parent_index = args.index("-p") + 1
        parent_sha = args[parent_index]
    if "-m" in args:
        message_index = args.index("-m") + 1
        message = args[message_index]
    if not message:
        raise RuntimeError("Message is required for commit-tree")

    # Header
    author_name = "Your Name"
    author_email = "your.email@example.com"
    timestamp = int(time.time())
    timezone = time.strftime("%z")
    commit_data = f"tree {tree_sha}\n"
    if parent_sha:
        commit_data += f"parent {parent_sha}\n"
    commit_data += f"author {author_name} <{author_email}> {timestamp} {timezone}\n"
    commit_data += (
        f"committer {author_name} <{author_email}> {timestamp} {timezone}\n\n"
    )
    commit_data += f"{message}\n"
    commit_binary = commit_data.encode("utf-8")
    commit_sha = hash_object(commit_binary, "commit")
    sys.stdout.write(commit_sha)


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
    elif command == "write-tree":
        writetree_command()
    elif command == "commit-tree":
        committree_command(args)
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
