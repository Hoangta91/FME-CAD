#!/usr/bin/env bash
# Dong bo FME-CAD voi CADCraft goc.
#
# Cach lam (khong bao gio xung dot merge):
#   1. lay CADCraft moi nhat (upstream)
#   2. tao nhanh sync/upstream-<sha> tu CADCraft moi, chep thu muc fme/ hien tai vao, chay fme/rebrand.py
#   3. `git merge -s ours <nhanh hien tai>`: giu NGUYEN cay vua tao (CADCraft moi + nhan dien FME),
#      va noi lich su FME vao -> nhanh sync/... fast-forward duoc vao main qua pull request.
# Vi vay: MOI thay doi cua FME phai nam trong fme/ (brand.toml, overlay/, patches/, rebrand.py).
# File sua tay ngoai fme/ se bi thay the o lan dong bo sau.
#
#   bash fme/sync.sh          # chay tay, tu nhanh main
#   bash fme/sync.sh --ci     # trong GitHub Actions: in ra changed=/branch= cho GITHUB_OUTPUT
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
CI_MODE=${1:-}
cfg() { python3 -c "import tomllib;print(tomllib.load(open('fme/brand.toml','rb'))['upstream']['$1'])"; }
UP_REPO=$(cfg repo); UP_BRANCH=$(cfg branch)

git remote get-url upstream >/dev/null 2>&1 || git remote add upstream "https://github.com/$UP_REPO"
git fetch --no-tags upstream "$UP_BRANCH"
if [ -n "$(git status --porcelain)" ]; then echo "Thu muc lam viec con thay doi chua commit." >&2; exit 1; fi

BASE=$(git rev-parse --abbrev-ref HEAD)
UP_SHA=$(git rev-parse --short=12 "upstream/$UP_BRANCH")
if git merge-base --is-ancestor "upstream/$UP_BRANCH" HEAD; then
  echo "Da cap nhat: CADCraft $UP_SHA da nam trong $BASE."
  [ "$CI_MODE" = "--ci" ] && echo "changed=false" >> "${GITHUB_OUTPUT:-/dev/null}"
  exit 0
fi

BR="sync/upstream-$UP_SHA"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
cp -a fme "$TMP/fme"
git checkout -B "$BR" "upstream/$UP_BRANCH"
rm -rf fme && cp -a "$TMP/fme" fme
git rev-parse "upstream/$UP_BRANCH" > fme/upstream.lock
python3 fme/rebrand.py
git add -A
git commit -q -m "FME-CAD: ap nhan dien len CADCraft $UP_SHA"
git merge -q -s ours --no-edit -m "Dong bo CADCraft $UP_SHA vao FME-CAD" "$BASE"
echo "Xong: nhanh $BR (CADCraft $UP_SHA + nhan dien FME)."
echo "Kiem tra: cargo check --workspace && cargo test -p cadcraft-engine; roi mo pull request $BR -> $BASE."
if [ "$CI_MODE" = "--ci" ]; then
  { echo "changed=true"; echo "branch=$BR"; echo "upstream_sha=$UP_SHA"; } >> "${GITHUB_OUTPUT:-/dev/null}"
fi
