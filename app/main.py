import sys
import os


def main():
    command = sys.argv[1]

    # Command: git init
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")

        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/master\n")

        print("Initialized git directory!\n")
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
