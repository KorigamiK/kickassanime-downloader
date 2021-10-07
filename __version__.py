version = 4.5

if __name__ == "__main__":
    print(f"Updating version from {version}")
    version += 0.1
    version = float(f'{version:.1f}')
    print(f"Version updated to {version}")

    new_version = f"version = {version}"

    def replace_first_line(target_filename, replacement_line):
        with open("./__version__.py") as f:
            first_line, remainder = f.readline(), f.read()
            t = open(target_filename, "w")
            t.write(replacement_line + "\n")
            t.write(remainder)
            t.close()

    replace_first_line("./__version__.py", new_version)
