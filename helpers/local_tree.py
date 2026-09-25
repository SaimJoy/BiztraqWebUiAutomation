import os
import shutil

from config import (
    BIZDRIVE_FOLDER_COUNT,
    BIZDRIVE_LOCAL_ROOT,
    BIZDRIVE_NESTED_PER_FOLDER,
    BIZDRIVE_TOTAL_FILES,
)


def _write_pdf(path, label):
    payload = (
        "%PDF-1.1\n"
        f"% {label}\n"
        "1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
        "2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n"
        "3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>endobj\n"
        "trailer<< /Root 1 0 R >>\n"
        "%%EOF\n"
    ).encode("ascii")
    with open(path, "wb") as f:
        f.write(payload)


def pdfs_in(folder):
    names = sorted(n for n in os.listdir(folder) if n.lower().endswith(".pdf"))
    return [os.path.join(folder, n) for n in names]


def nested_dirs(folder):
    names = sorted(
        n for n in os.listdir(folder) if os.path.isdir(os.path.join(folder, n))
    )
    return [os.path.join(folder, n) for n in names]


def parent_dirs(root):
    if not os.path.isdir(root):
        return []
    names = sorted(
        n for n in os.listdir(root) if os.path.isdir(os.path.join(root, n))
    )
    return [os.path.join(root, n) for n in names]


def count_pdf_files(root):
    if not os.path.isdir(root):
        return 0
    return sum(
        1
        for current, _, files in os.walk(root)
        for name in files
        if name.lower().endswith(".pdf")
    )


def build_local_tree(
    root=None,
    folder_count=None,
    nested_count=None,
    total_files=None,
):
    root = os.path.abspath(root or BIZDRIVE_LOCAL_ROOT)
    folder_count = BIZDRIVE_FOLDER_COUNT if folder_count is None else folder_count
    nested_count = BIZDRIVE_NESTED_PER_FOLDER if nested_count is None else nested_count
    total_files = BIZDRIVE_TOTAL_FILES if total_files is None else total_files

    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(root, exist_ok=True)

    template = os.path.join(root, "_template.pdf")
    _write_pdf(template, "template")

    folders = 0
    upload_folders = []
    for i in range(1, folder_count + 1):
        parent = os.path.join(root, f"Folder_{i:03d}")
        os.makedirs(parent, exist_ok=True)
        folders += 1
        for j in range(1, nested_count + 1):
            nested = os.path.join(parent, f"Nested_{j:02d}")
            os.makedirs(nested, exist_ok=True)
            folders += 1
            upload_folders.append(nested)
        if i % 50 == 0 or i == folder_count:
            print(f"Local tree progress: {i}/{folder_count} parent folders")

    if not upload_folders:
        upload_folders = parent_dirs(root)
    base, extra = divmod(total_files, len(upload_folders))
    files = 0
    for index, folder in enumerate(upload_folders):
        file_count = base + (1 if index < extra else 0)
        for p in range(1, file_count + 1):
            shutil.copyfile(template, os.path.join(folder, f"test_{p:02d}.pdf"))
            files += 1

    os.remove(template)
    print(f"Local tree ready at {root}")
    print(f"Created {folders} folders and {files} PDF files")
    return root
