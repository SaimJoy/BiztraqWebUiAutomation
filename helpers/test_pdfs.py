import os
import shutil

PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "testdata", "pdfs")


def ensure_test_pdfs(count):
    os.makedirs(PDF_DIR, exist_ok=True)
    paths = []
    for i in range(1, count + 1):
        name = f"test_{i:03d}.pdf"
        path = os.path.abspath(os.path.join(PDF_DIR, name))
        payload = (
            "%PDF-1.1\n"
            f"% {name}\n"
            "1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
            "2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n"
            "3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>endobj\n"
            "trailer<< /Root 1 0 R >>\n"
            "%%EOF\n"
        ).encode("ascii")
        with open(path, "wb") as f:
            f.write(payload)
        paths.append(path)
    return paths


def copies_for(folder_name, source_paths):
    dest_dir = os.path.abspath(os.path.join(PDF_DIR, "copies"))
    os.makedirs(dest_dir, exist_ok=True)
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in folder_name)
    out = []
    for i, src in enumerate(source_paths, 1):
        dest = os.path.join(dest_dir, f"{safe}_{i:02d}.pdf")
        shutil.copyfile(src, dest)
        out.append(dest)
    return out
