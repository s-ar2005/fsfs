# fsfs — File-Sub-Filesystem

A clean, lightweight virtual filesystem packed into a single `.fsfs` file.  
No kernel modules or FUSE needed, built with Python.

---

## Features

- Pack any directory structure into one `.fsfs` archive  
- List contents with full nested directory support  
- Extract (mount) entire archives or specific files/folders without deleting the original  
- Create, write, rename, and delete files and directories inside the `.fsfs` container  
- Simple, extensible binary format designed for easy hacking and customization  

---

## Usage

```bash
# Pack a directory into fsfs container
python3 main.py create archive.fsfs /path/to/dir

# List contents of an fsfs archive
python3 main.py ls archive.fsfs

# Extract entire archive contents to a directory (mount)
python3 main.py mount archive.fsfs /path/to/mountdir

# Extract single file or directory from fsfs
python3 main.py extract archive.fsfs docs/readme.md /tmp/out

# Write or overwrite a file inside fsfs
python3 main.py write archive.fsfs docs /home/user/file.txt

# Create a new directory inside fsfs (you’ll be prompted for the name, or just use echo to type it in stdin)
python3 main.py mkdir archive.fsfs docs

# Rename a file or directory inside fsfs
python3 main.py rename archive.fsfs docs/readme.md README.md

# Delete a file or empty directory inside fsfs
python3 main.py delete archive.fsfs docs/oldfile.txt
````

---

## How it works

* Starts with a simple magic header and versioning
* Maintains an entries table describing files and directories, including parent-child relationships
* Stores file data blobs sequentially after metadata
* Allows nested directories and easy traversal

---

## Why use fsfs?

* No extra system dependencies, no root access needed
* Portable single-file container makes backups and transfers easy
* Mutable virtual filesystem with full CRUD support
* Written in Python for flexibility and easy integration
* Great for projects that need embedded virtual filesystems or custom archive formats

---

## License

MIT — use it however you want. Built by Sarah <3.
