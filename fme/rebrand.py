#!/usr/bin/env python3
"""Ap nhan dien FME-CAD len cay ma nguon CADCraft goc. IDEMPOTENT: chay lai nhieu lan van ra cung ket qua.

Nguyen tac (de cap nhat theo CADCraft ma khong xung dot):
  * Moi tuy bien cua FME nam trong thu muc fme/. Khong sua tay file ngoai fme/ - lan dong bo sau se ghi de.
  * Chi doi nhung gi nguoi dung NHIN THAY (ten, icon, gioi thieu, kenh cap nhat, ID ung dung).
  * GIU NGUYEN dinh danh noi bo va dinh dang file (ten crate, ten font "CADCraft Stroke",
    ten may in "CADCraft PNG/PDF/SVG", bien moi truong CADCRAFT_*) de file ban ve tuong thich 2 chieu.
  * Moi "patch dich" phai khop chinh xac; neu CADCraft doi ma lam patch khong khop -> script DUNG va bao loi
    (thay vi doi sai im lang). Khi do sua patch trong file nay.

Moi lan chay, script KHOI PHUC ma CADCraft goc (commit ghi trong fme/upstream.lock, do sync.sh cap nhat)
roi moi ap nhan dien -> doi ten/mau/ID trong brand.toml bao nhieu lan cung ra ket qua dung.

Chay:  python3 fme/rebrand.py            (tu thu muc goc repo; dung lai neu co file ngoai fme/ chua commit)
       python3 fme/rebrand.py --force    (bo qua kiem tra tren - MAT thay doi chua commit ngoai fme/)
       python3 fme/rebrand.py --check    (kiem tra cay da commit dung bang rebrand(CADCraft goc), khong ghi)
"""
import os, re, sys, shutil, subprocess, tempfile, tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FME = os.path.join(ROOT, "fme")
B = tomllib.load(open(os.path.join(FME, "brand.toml"), "rb"))
BR = B["brand"]
NAME, ID, BUNDLE, DEV = BR["name"], BR["id"], BR["bundle_id"], BR["developer"]
OLD_BUNDLE = "ai.storyteller.cadcraft"
CHECK = "--check" in sys.argv
changed = []


class PatchError(Exception):
    pass


def rel(p):
    return os.path.relpath(p, ROOT)


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, text):
    if read(p) != text:
        changed.append(rel(p))
        if not CHECK:
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(text)


def walk(dirs, exts):
    for d in dirs:
        base = os.path.join(ROOT, d)
        if os.path.isfile(base):
            yield base; continue
        for root, dnames, files in os.walk(base):
            dnames[:] = [x for x in dnames if x not in (".git", "target", "fme")]
            for fn in files:
                if fn.endswith(exts) or fn in exts:
                    yield os.path.join(root, fn)


# --------------------------------------------------------------------------- 1. doi ten hien thi
# "CADCraft" -> NAME, tru dinh danh dinh dang file / tuong thich.
KEEP = r"(?! (?:PNG|PDF|SVG|Stroke|Static Test))"
NAME_RE = re.compile(r"(?<!Based on )CADCraft" + KEEP)  # "Based on CADCraft" = dong ghi nguon, giu nguyen
TEXT_SCOPE = ["apps", "crates", "xtask", "packaging"]
TEXT_EXT = (".rs", ".tsv", ".toml", ".sh", ".ps1", ".wxs", ".wxi", ".json", ".in", ".xml", ".desktop",
            ".yml", ".yaml", ".plist", ".html", ".md")


def rename_text():
    for p in walk(TEXT_SCOPE, TEXT_EXT):
        t = read(p)
        n = NAME_RE.sub(NAME, t).replace(OLD_BUNDLE, BUNDLE)
        if n != t:
            write(p, n)
    packaging()
    # ATTRIBUTION: duong dan icon doi theo bundle id
    p = os.path.join(ROOT, "ATTRIBUTION.md")
    write(p, read(p).replace(OLD_BUNDLE, BUNDLE))


def packaging():
    """Bo cai: nha phat hanh, thu muc cai dat, trang chu, va UpgradeCode Windows RIENG.
    UpgradeCode trung voi CADCraft se lam Windows coi FME-CAD la ban nang cap cua CADCraft (ghi de nhau)."""
    import uuid
    upgrade = str(uuid.uuid5(uuid.NAMESPACE_DNS, BUNDLE)).upper()
    home = BR["website"] or f"https://github.com/{BR['release_repo']}"
    dev_id = ".".join(BUNDLE.split(".")[:2])
    reps = [("119D7D76-0167-4A9E-8F37-09DA0235F68E", upgrade),
            ("Learning Machines LLC", DEV),
            ("https://getartcraft.com/apps/cadcraft", home),
            ('<developer id="ai.storyteller">', f'<developer id="{dev_id}">'),
            ("FME-CAD maintainers <cadcraft@storyteller.ai>", BR["maintainer"])]
    for p in walk(["packaging"], TEXT_EXT):
        t = read(p); n = t
        for a, b in reps:
            n = n.replace(a, b)
        n = re.sub(r"\bArtCraft\b", DEV, n)   # thu muc bo ung dung: Programs\ArtCraft\... -> Programs\FME\...
        if n != t:
            write(p, n)


# --------------------------------------------------------------------------- 2. patch dich (phai khop)
def patch(path, old, new, count=1):
    p = os.path.join(ROOT, path)
    t = read(p)
    if new in t and old not in t:
        return  # da ap
    if t.count(old) != count:
        raise PatchError(f"{path}: doan can sua xuat hien {t.count(old)} lan (can {count}):\n---\n{old}\n---")
    write(p, t.replace(old, new))


def rs(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def targeted():
    acc = BR["accent"]
    # 2a. kenh tu cap nhat: tro ve kho phat hanh cua FME, khong phai ArtCraft
    patch("crates/ui-egui/src/lib.rs",
          "    accent: Some([0x3e, 0xa6, 0xe8]),\n    ..craft_update::suite::CADCRAFT\n};",
          f"    accent: Some([0x{acc[0]:02x}, 0x{acc[1]:02x}, 0x{acc[2]:02x}]),\n"
          f"    // FME-CAD: ban cai va kenh cap nhat rieng (fme/brand.toml).\n"
          f"    developer: \"{rs(DEV)}\",\n"
          f"    ..craft_update::app::App::new(\"{ID}\", \"{rs(NAME)}\", \"{rs(BR['tagline'])}\", \"{rs(BR['release_repo'])}\")\n}};")
    # 2b. hop thoai About: bo thuong hieu ArtCraft, ghi ro nguon goc (duoc phep theo LICENSE-brand)
    about_old = ('                    ui.label(RichText::new(crate::tl!("One of the Crafting Apps by the ArtCraft team and community.")).color(t.text_dim));\n'
                 '                    ui.hyperlink_to("getartcraft.com/apps/cadcraft", "https://getartcraft.com/apps/cadcraft");\n'
                 '                    ui.hyperlink_to(crate::tl!("Join us on Discord"), "https://discord.gg/artcraft");\n')
    about_new = f'                    ui.label(RichText::new("{rs(DEV)}").color(t.text_dim));\n'
    if BR["website"]:
        about_new += f'                    ui.hyperlink_to("{rs(BR["website"])}", "{rs(BR["website"])}");\n'
    about_new += ('                    ui.label(RichText::new("Based on CADCraft by the ArtCraft team and community.").small().color(t.text_dim));\n'
                  '                    ui.hyperlink_to("github.com/storytold/cadcraft", "https://github.com/storytold/cadcraft");\n')
    patch("crates/ui-egui/src/dialogs.rs", about_old, about_new)
    # 2c. menu macOS: muc "Join the ArtCraft Discord" -> trang ho tro FME (hoac an neu chua co)
    url = BR["support_url"]
    patch("apps/cadcraft/src/native_menu.rs",
          'ctx.open_url(egui::OpenUrl::new_tab("https://discord.gg/artcraft"));',
          f'ctx.open_url(egui::OpenUrl::new_tab("{rs(url)}"));' if url else
          'let _ = &ctx; // FME-CAD: chua co trang ho tro (fme/brand.toml support_url)')
    patch("apps/cadcraft/src/native_menu.rs", '"Join the ArtCraft Discord…"', f'"{rs(NAME)} Support…"', count=2)
    if not url:
        patch("apps/cadcraft/src/native_menu.rs",
              "&about, &discord, &PredefinedMenuItem::separator()", "&about, &PredefinedMenuItem::separator()")
    # 2d. thong tin file .exe Windows
    patch("apps/cadcraft/build.rs", '.set("CompanyName", "Learning Machines LLC")', f'.set("CompanyName", "{rs(DEV)}")')
    patch("apps/cadcraft/build.rs",
          f'.set("LegalCopyright", "Copyright (c) 2026 ArtCraft Team and the {NAME} contributors. MIT OR Apache-2.0.")',
          f'.set("LegalCopyright", "{rs(BR["copyright"])}")')
    # 2e. thu muc cau hinh Linux rieng (macOS/Windows da doi qua ten hien thi) -> khong dung chung voi CADCraft
    patch("crates/engine/src/settings_dir.rs", '.map(|c| c.join("cadcraft"))', f'.map(|c| c.join("{ID}"))')
    # 2f. dong dich ArtCraft trong catalog ngon ngu: xoa (roi ve tieng Anh)
    for p in walk(["crates/ui-egui/src/i18n"], (".tsv",)):
        lines = read(p).split("\n")
        keep = [l for l in lines if not (l.startswith("\t") and "ArtCraft" in l)]
        write(p, "\n".join(keep))
    # 2g. workspace metadata
    patch("Cargo.toml", 'repository = "https://github.com/storytold/cadcraft"',
          f'repository = "https://github.com/{BR["release_repo"]}"')


def fix_settings_tests():
    """Test cua settings_dir ky vong '.config/cadcraft' -> doi theo ID."""
    p = os.path.join(ROOT, "crates/engine/src/settings_dir.rs")
    t = read(p)
    write(p, re.sub(r'(\.config/|/)cadcraft"', lambda m: f'{m.group(1)}{ID}"', t))


# --------------------------------------------------------------------------- 3. tai nguyen
def assets():
    src = os.path.join(FME, "assets", "app-icon")
    dst = os.path.join(ROOT, "assets", "app-icon")
    pairs = {"fme-1024.png": "cadcraft-1024.png", "fme-256.png": "cadcraft-256.png", "fme-64.png": "cadcraft-64.png",
             "fme-macos-512.png": "cadcraft-macos-512.png", "fme.ico": "cadcraft.ico", "fme.icns": "cadcraft.icns"}
    for s, d in pairs.items():
        copy(os.path.join(src, s), os.path.join(dst, d))
    hic = os.path.join(dst, "hicolor")
    for size_dir in sorted(os.listdir(hic)):
        apps = os.path.join(hic, size_dir, "apps")
        old = os.path.join(apps, OLD_BUNDLE + ".png")
        new = os.path.join(apps, BUNDLE + ".png")
        size = size_dir.split("x")[0]
        copy(os.path.join(src, f"hicolor-{size}.png"), new)
        if os.path.exists(old) and old != new:
            changed.append(rel(old) + " (xoa)")
            if not CHECK: os.remove(old)
    # file packaging mang bundle id trong ten
    for root, _, files in os.walk(os.path.join(ROOT, "packaging")):
        for fn in files:
            if OLD_BUNDLE in fn:
                o = os.path.join(root, fn); n = os.path.join(root, fn.replace(OLD_BUNDLE, BUNDLE))
                changed.append(f"{rel(o)} -> {rel(n)}")
                if not CHECK: os.replace(o, n)
    # ATTRIBUTION: tac gia icon la FME
    p = os.path.join(ROOT, "ATTRIBUTION.md")
    out = []
    for line in read(p).split("\n"):
        if line.startswith("| `assets/app-icon/") and "CADCraft contributors" in line:
            line = line.replace("CADCraft contributors", f"{DEV} (fme/assets/app-icon, fme/make_icons.py)").replace("MIT OR Apache-2.0", "LicenseRef-FME-Trademark")
        out.append(line)
    text = "\n".join(out)
    # Logo FME va icon sinh tu logo: nhan hieu cua FME, KHONG thuoc MIT/Apache. Muc nay duoc tao lai moi lan chay.
    lic = "LicenseRef-FME-Trademark"
    marker = "## FME-CAD brand assets"
    rows = []
    for sub in ("logo", "app-icon"):
        d = os.path.join(FME, "assets", sub)
        if os.path.isdir(d):
            rows += [f"| `fme/assets/{sub}/{fn}` | {DEV} | " + ("FME logo" if sub == "logo" else "fme/make_icons.py from the FME logo")
                     + f" | {lic} | FME trademark, not covered by MIT OR Apache-2.0 |" for fn in sorted(os.listdir(d))]
    section = (marker + "\n\nThe FME name and logo are trademarks of " + DEV + ". They are not open source.\n\n"
               "| File | Author | Source | Licence | Notes |\n|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
    if marker in text:
        text = text[:text.index(marker)].rstrip("\n")
    text = text.rstrip("\n") + "\n\n" + section
    write(p, text)


def copy(s, d):
    if not os.path.exists(d) or open(s, "rb").read() != open(d, "rb").read():
        changed.append(rel(d))
        if not CHECK:
            os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copyfile(s, d)


# --------------------------------------------------------------------------- 3b. tinh nang rieng cua FME
def overlay_and_patches():
    """fme/overlay/** -> chep de len goc (file MOI cua FME, vd crate rieng: fme/overlay/crates/fme-xxx/).
    fme/patches/*.patch -> git apply theo thu tu ten (SUA file cua CADCraft). Patch hong -> dung, bao loi."""
    ov = os.path.join(FME, "overlay")
    if os.path.isdir(ov):
        for root, _, files in os.walk(ov):
            for fn in files:
                if fn == ".gitkeep":
                    continue
                s = os.path.join(root, fn)
                copy(s, os.path.join(ROOT, os.path.relpath(s, ov)))
    pd = os.path.join(FME, "patches")
    if os.path.isdir(pd):
        import subprocess
        for fn in sorted(f for f in os.listdir(pd) if f.endswith(".patch")):
            pp = os.path.join(pd, fn)
            if subprocess.run(["git", "apply", "--reverse", "--check", pp], cwd=ROOT, capture_output=True).returncode == 0:
                continue  # da ap
            r = subprocess.run(["git", "apply", "--check", pp], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                raise PatchError(f"fme/patches/{fn} khong con ap duoc len CADCraft moi:\n{r.stderr}")
            changed.append(f"patch {fn}")
            if not CHECK:
                subprocess.run(["git", "apply", pp], cwd=ROOT, check=True)


# --------------------------------------------------------------------------- 4. tai lieu & thuong hieu ArtCraft
def docs():
    copy(os.path.join(FME, "README.md"), os.path.join(ROOT, "README.md"))
    # Logo ArtCraft la nhan hieu, khong duoc dung trong ban phan phoi cua ben khac (docs/brand/LICENSE-brand.txt)
    brand = os.path.join(ROOT, "docs", "brand")
    if os.path.isdir(brand):
        for fn in os.listdir(brand):
            if fn.startswith("artcraft"):
                changed.append(f"docs/brand/{fn} (xoa)")
                if not CHECK: os.remove(os.path.join(brand, fn))
    # NOTICE: them phan FME o dau, GIU NGUYEN thong bao goc (bat buoc theo Apache-2.0)
    p = os.path.join(ROOT, "NOTICE")
    head = read(os.path.join(FME, "NOTICE.fme"))
    t = read(p)
    if not t.startswith(head):
        write(p, head + "\n" + t)
    # Dich vu chi danh cho repo goc (can secret cua ArtCraft): bo khoi ban FME
    for f in [".github/workflows/sonarcloud.yml", ".github/workflows/release.yml", ".github/workflows/windows-arm64.yml",
              ".github/workflows/freebsd.yml", ".github/workflows/nix.yml", ".github/workflows/house-rules.yml",
              ".coderabbit.yaml", "sonar-project.properties",
              # Phien ban thu vien do CADCraft quan ly (Cargo.lock di theo upstream); Dependabot cua FME se tao
              # PR nang cap bi ghi de o lan dong bo sau -> tat.
              ".github/dependabot.yml"]:
        fp = os.path.join(ROOT, f)
        if os.path.exists(fp):
            changed.append(f + " (xoa)")
            if not CHECK: os.remove(fp)
    # Workflow rieng cua FME
    src = os.path.join(FME, "github-workflows")
    for fn in os.listdir(src):
        copy(os.path.join(src, fn), os.path.join(ROOT, ".github", "workflows", fn))


def git(*args, **kw):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True, **kw).stdout


def reset_to_upstream():
    """Dua moi file ngoai fme/ ve dung CADCraft goc tai commit trong fme/upstream.lock."""
    base = read(os.path.join(FME, "upstream.lock")).strip()
    if subprocess.run(["git", "cat-file", "-e", base + "^{commit}"], cwd=ROOT).returncode != 0:
        up = B["upstream"]
        subprocess.run(["git", "fetch", "--no-tags", f"https://github.com/{up['repo']}", up["branch"]], cwd=ROOT, check=True)
    dirty = [l for l in git("status", "--porcelain", "--", ".", ":(exclude)fme").splitlines() if l.strip()]
    if dirty and "--force" not in sys.argv:
        print("Dung: co thay doi chua commit ngoai fme/ (se bi ghi de). Commit/bo chung, hoac chay voi --force:",
              *dirty[:10], sep="\n  ", file=sys.stderr)
        sys.exit(3)
    upstream_files = set(git("ls-tree", "-r", "--name-only", base).splitlines())
    present = set(git("ls-files").splitlines()) | set(git("ls-files", "--others", "--exclude-standard").splitlines())
    for f in sorted(present - upstream_files):
        if not f.startswith("fme/") and os.path.exists(os.path.join(ROOT, f)):
            os.remove(os.path.join(ROOT, f))
    git("checkout", base, "--", ".")
    git("reset", "-q")   # checkout tren co the stage file; tra ve trang thai chua stage


def check():
    """Ap rebrand vao mot ban sao (worktree tam) cua HEAD voi fme/ hien tai; so voi HEAD."""
    tmp = tempfile.mkdtemp(prefix="fme-check-")
    wt = os.path.join(tmp, "wt")
    git("worktree", "add", "--detach", wt, "HEAD")
    try:
        shutil.rmtree(os.path.join(wt, "fme"), ignore_errors=True)
        shutil.copytree(FME, os.path.join(wt, "fme"))
        r = subprocess.run([sys.executable, os.path.join(wt, "fme", "rebrand.py"), "--force"], cwd=wt, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout, r.stderr, file=sys.stderr); sys.exit(r.returncode)
        diff = [l for l in subprocess.run(["git", "status", "--porcelain", "--", ".", ":(exclude)fme"], cwd=wt,
                                          capture_output=True, text=True).stdout.splitlines() if l.strip()]
        if diff:
            print(f"[check] cay da commit KHAC rebrand(CADCraft goc): {len(diff)} file", *diff[:20], sep="\n  ")
            sys.exit(1)
        print("[check] OK: cay da commit = rebrand(CADCraft goc).")
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", wt], cwd=ROOT)
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    os.chdir(ROOT)
    if CHECK:
        check(); return
    reset_to_upstream()
    try:
        rename_text(); targeted(); fix_settings_tests(); assets(); overlay_and_patches(); docs()
    except PatchError as e:
        print("LOI: CADCraft da thay doi, patch khong con khop. Sua patch trong fme/rebrand.py.\n", e, file=sys.stderr)
        sys.exit(2)
    left = [l for p in walk(["apps", "crates"], (".rs",)) for l in read(p).splitlines()
            if ("ArtCraft" in l or "getartcraft" in l or "discord.gg/artcraft" in l)
            and "Based on CADCraft" not in l]
    if left:
        print("CANH BAO: con nhac den ArtCraft trong ma:", *left[:10], sep="\n  ")
    print(f"Da ap nhan dien FME ({len(changed)} muc) len CADCraft {read(os.path.join(FME, 'upstream.lock')).strip()[:12]}.")


if __name__ == "__main__":
    main()
