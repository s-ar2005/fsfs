import os
import struct
MAGIC = b'FSFSYS'
VERSION = 1
PARENT_NONE = 0xFFFFFFFF
class FsfsEntry:
    def __init__(self, name, is_dir, parent_idx, size=0, offset=0):
        self.name = name
        self.is_dir = is_dir
        self.parent_idx = parent_idx
        self.size = size
        self.offset = offset

class Fsfs:
    def __init__(self):
        self.entries = []
        self.file_data = b''

    def pack_dir(self, root_path):
        self.entries = []
        self.file_data = b''
        self._add_dir(root_path, PARENT_NONE)

    def _add_dir(self, path, parent_idx):
        idx = len(self.entries)
        name = os.path.basename(path.rstrip('/'))
        self.entries.append(FsfsEntry(name, True, parent_idx))
        for entry in sorted(os.listdir(path)):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                self._add_dir(full_path, idx)
            else:
                self._add_file(full_path, idx)

    def _add_file(self, filepath, parent_idx):
        with open(filepath, 'rb') as f:
            data = f.read()
        offset = len(self.file_data)
        size = len(data)
        name = os.path.basename(filepath)
        self.entries.append(FsfsEntry(name, False, parent_idx, size, offset))
        self.file_data += data

    def save(self, fsfs_path):
        with open(fsfs_path, 'wb') as f:
            f.write(MAGIC)
            f.write(struct.pack('B', VERSION))
            f.write(struct.pack('<I', len(self.entries)))
            for e in self.entries:
                name_bytes = e.name.encode('utf-8')
                f.write(struct.pack('B', len(name_bytes)))
                f.write(name_bytes)
                f.write(struct.pack('B', 1 if e.is_dir else 0))
                f.write(struct.pack('<I', e.parent_idx))
                f.write(struct.pack('<I', e.size))
                f.write(struct.pack('<I', e.offset))
            f.write(self.file_data)

    def load(self, fsfs_path):
        self.entries = []
        with open(fsfs_path, 'rb') as f:
            magic = f.read(6)
            assert magic == MAGIC, "Invalid FSFS magic"
            version = struct.unpack('B', f.read(1))[0]
            assert version == VERSION, "Unsupported FSFS version"
            count = struct.unpack('<I', f.read(4))[0]
            for _ in range(count):
                name_len = struct.unpack('B', f.read(1))[0]
                name = f.read(name_len).decode('utf-8')
                is_dir = struct.unpack('B', f.read(1))[0] == 1
                parent_idx = struct.unpack('<I', f.read(4))[0]
                size = struct.unpack('<I', f.read(4))[0]
                offset = struct.unpack('<I', f.read(4))[0]
                self.entries.append(FsfsEntry(name, is_dir, parent_idx, size, offset))
            self.file_data = f.read()

    def list_dir(self, parent_idx=PARENT_NONE):
        return [e for e in self.entries if e.parent_idx == parent_idx]

    def print_tree(self, parent_idx=PARENT_NONE, indent=0):
        for e in self.list_dir(parent_idx):
            print('  ' * indent + ('[D] ' if e.is_dir else '[F]') + e.name)
            if e.is_dir:
                self.print_tree(self.entries.index(e), indent + 1)

    def extract(self, outdir, parent_idx=PARENT_NONE):
        os.makedirs(outdir, exist_ok=True)
        for e in self.list_dir(parent_idx):
            path = os.path.join(outdir, e.name)
            if e.is_dir:
                self.extract(path, self.entries.index(e))
            else:
                with open(path, 'wb') as f:
                    start = e.offset
                    end = start + e.size
                    f.write(self.file_data[start:end])

    def extract_path(self, internal_path, outdir):
        parts = internal_path.strip('/').split('/')
        idx = None
        candidates = [i for i, e in enumerate(self.entries) if e.parent_idx == PARENT_NONE and e.name == parts[0]]
        if not candidates:
            raise FileNotFoundError(internal_path)
        idx = candidates[0]
        for part in parts[1:]:
            children = [i for i, e in enumerate(self.entries) if e.parent_idx == idx and e.name == part]
            if not children:
                raise FileNotFoundError(internal_path)
            idx = children[0]
        entry = self.entries[idx]
        if entry.is_dir:
            self._extract_dir(idx, outdir)
        else:
            os.makedirs(outdir, exist_ok=True)
            path = os.path.join(outdir, entry.name)
            with open(path, 'wb') as f:
                start = entry.offset
                end = start + entry.size
                f.write(self.file_data[start:end])

    def _extract_dir(self, parent_idx, outdir):
        os.makedirs(outdir, exist_ok=True)
        for e in self.list_dir(parent_idx):
            path = os.path.join(outdir, e.name)
            if e.is_dir:
                self._extract_dir(self.entries.index(e), path)
            else:
                with open(path, 'wb') as f:
                    start = e.offset
                    end = start + e.size
                    f.write(self.file_data[start:end])

    def add_file(self, internal_dir_path, filename, data):
        dir_idx = self._get_dir_index(internal_dir_path)
        if dir_idx is None:
            raise FileNotFoundError(f"Directory '{internal_dir_path}' not found")
        existing_idx = None
        for i, e in enumerate(self.entries):
            if e.parent_idx == dir_idx and e.name == filename and not e.is_dir:
                existing_idx = i
                break
        if existing_idx is not None:
            self.entries[existing_idx].size = len(data)
            self.entries[existing_idx].offset = -1
            self._replace_file_data(existing_idx, data)
        else:
            self.entries.append(FsfsEntry(filename, False, dir_idx, len(data), -1))
            self._replace_file_data(len(self.entries)-1, data)

    def _replace_file_data(self, entry_idx, data):
        files = [(i, e) for i, e in enumerate(self.entries) if not e.is_dir]
        new_file_data = bytearray()
        offset_map = {}
        for i, e in files:
            if i == entry_idx:
                offset_map[i] = len(new_file_data)
                new_file_data.extend(data)
            else:
                start = e.offset
                end = start + e.size
                old_data = self.file_data[start:end]
                offset_map[i] = len(new_file_data)
                new_file_data.extend(old_data)
        for i, e in files:
            e.offset = offset_map[i]
            if i == entry_idx:
                e.size = len(data)
        self.file_data = bytes(new_file_data)

    def _get_dir_index(self, internal_dir_path):
        if internal_dir_path in ('', '/', None):
            return PARENT_NONE
        parts = internal_dir_path.strip('/').split('/')
        idx_candidates = [i for i, e in enumerate(self.entries) if e.parent_idx == PARENT_NONE and e.name == parts[0] and e.is_dir]
        if not idx_candidates:
            return None
        idx = idx_candidates[0]
        for part in parts[1:]:
            children = [i for i, e in enumerate(self.entries) if e.parent_idx == idx and e.name == part and e.is_dir]
            if not children:
                return None
            idx = children[0]
        return idx
    def create_dir(self, internal_dir_path, dirname):
        parent_idx = self._get_dir_index(internal_dir_path)
        if parent_idx is None:
            raise FileNotFoundError(f"Directory '{internal_dir_path}' not found")
        for e in self.entries:
            if e.parent_idx == parent_idx and e.name == dirname:
                raise FileExistsError(f"Entry '{dirname}' already exists in '{internal_dir_path}'")
        self.entries.append(FsfsEntry(dirname, True, parent_idx))


    def delete(self, internal_path):
        idx = self._get_entry_index(internal_path)
        if idx is None:
            raise FileNotFoundError(f"Path '{internal_path}' not found")
        entry = self.entries[idx]
        if entry.is_dir:
            if any(e.parent_idx == idx for e in self.entries):
                raise IsADirectoryError(f"Directory '{internal_path}' is not empty")
        del self.entries[idx]
        self._rebuild_file_data()


    def rename(self, internal_path, new_name):
        idx = self._get_entry_index(internal_path)
        if idx is None:
            raise FileNotFoundError(f"Path '{internal_path}' not found")
        entry = self.entries[idx]
        parent_idx = entry.parent_idx
        for e in self.entries:
            if e.parent_idx == parent_idx and e.name == new_name:
                raise FileExistsError(f"Name '{new_name}' already exists in directory")
        entry.name = new_name

    def _get_entry_index(self, internal_path):
        parts = internal_path.strip('/').split('/')
        candidates = [i for i, e in enumerate(self.entries) if e.parent_idx == PARENT_NONE and e.name == parts[0]]
        if not candidates:
            return None
        idx = candidates[0]
        for part in parts[1:]:
            children = [i for i, e in enumerate(self.entries) if e.parent_idx == idx and e.name == part]
            if not children:
                return None
            idx = children[0]
        return idx

    def _rebuild_file_data(self):
        files = [(i, e) for i, e in enumerate(self.entries) if not e.is_dir]
        new_file_data = bytearray()
        offset_map = {}
        for i, e in files:
            start = e.offset
            end = start + e.size
            old_data = self.file_data[start:end]
            offset_map[i] = len(new_file_data)
            new_file_data.extend(old_data)
        for i, e in files:
            e.offset = offset_map[i]
        self.file_data = bytes(new_file_data)
