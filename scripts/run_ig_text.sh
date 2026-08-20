#!/bin/bash
# FitXMatt IG TEXT-CAROUSEL auto-publisher.
# Renders the next post from ig_text_carousels.json as a 3-slide carousel
# (render_text_carousel.py), hosts the 3 PNGs on the brand site, and publishes
# them to IG as a CAROUSEL (3 images). No model dependency. Email (REST) +
# Telegram best-effort. Pointer advances.
set -uo pipefail
FX="/Users/matus/FitXMatt"
ENV="/Users/matus/.hermes/.env"
[ -f "$ENV" ] && { set -a; source "$ENV" 2>/dev/null; set +a; }

IG_USER_ID="${IG_USER_ID:-}"
IG_TOKEN="${IG_ACCESS_TOKEN:-}"
BANK="$FX/ig_text_carousels.json"
PTR="$FX/.ig_text_pointer"
PY="$FX/.venv/bin/python"
RENDER="$PY $FX/render_text_carousel.py"
CARO="/tmp/fitxmatt_text_carousel"

fail(){ echo "IG_TEXT_FAIL: $1"; exit 1; }
[ -n "$IG_USER_ID" ] || fail "IG_USER_ID missing"
[ -n "$IG_TOKEN" ] || fail "IG_ACCESS_TOKEN missing"
[ -f "$BANK" ] || fail "bank missing"

# --- read pointer (0-based index) ---
IDX=$(cat "$PTR" 2>/dev/null | tr -d '[:space:]')
IDX="${IDX:-0}"
N=$(( IDX + 1 ))
# short hook (for email subject) + FULL caption (for the IG post text under the slides)
HOOK=$(/Users/matus/FitXMatt/.venv/bin/python - "$BANK" "$IDX" <<'PY'
import sys,json
d=json.load(open(sys.argv[1])); c=d["carousels"][int(sys.argv[2])%len(d["carousels"])]
s1=c.get("slide1","").replace("\n"," ").strip()
print((s1[:80]+"…") if len(s1)>80 else s1)
PY
)
CAPTION=$(/Users/matus/FitXMatt/.venv/bin/python - "$BANK" "$IDX" <<'PY'
import sys,json
d=json.load(open(sys.argv[1])); c=d["carousels"][int(sys.argv[2])%len(d["carousels"])]
cta=d.get("brand",{}).get("cta_word","SYSTEM")
body="\n\n".join(c[k] for k in ("slide1","slide2","slide3")).strip()
print(body + f"\n\nComment {cta} and I'll send you my free framework.\n\nCheck client results here: https://fitxmatt.com/")
PY
)

# --- render 3-slide carousel ---
$RENDER "$IDX" >/dev/null 2>&1 || fail "render failed"
[ -f "$CARO/slide1.png" ] && [ -f "$CARO/slide2.png" ] && [ -f "$CARO/slide3.png" ] || fail "slides missing"

# --- email copy (REST) from the 3 slide texts ---
$PY - "$BANK" "$IDX" > /tmp/ig_text_body.txt <<'PY'
import sys,json
d=json.load(open(sys.argv[1])); c=d["carousels"][int(sys.argv[2])%len(d["carousels"])]
L=[f"FitXMatt IG Carousel #{int(sys.argv[2])+1}/{len(d['carousels'])} — {c.get('label','')}"]
L+=[f"\n=== SLIDE 1 ===\n{c['slide1']}","\n=== SLIDE 2 ===\n{c['slide2']}","\n=== SLIDE 3 ===\n{c['slide3']}"]
print("\n".join(L))
PY
bash /Users/matus/.hermes/tools/send_email_rest.sh "FitXMatt IG Carousel #$N" /tmp/ig_text_body.txt >/tmp/ig_text_rest.log 2>&1 && echo "EMAIL_SENT #$N" || { echo "EMAIL_FAIL"; cat /tmp/ig_text_rest.log; }

# --- host 3 images on brand site (flat path, matches working slide1.png) ---
SITE_BASE="${IG_SITE_BASE:-https://raw.githubusercontent.com/kovokilla/fitxmatt/main}"
SITE_REPO="${IG_SITE_REPO:-https://github.com/kovokilla/fitxmatt.git}"
SITE_CACHE="${IG_SITE_CACHE:-/tmp/ig_site_fitxmatt}"
# Clone fresh if missing OR if the existing clone is broken (e.g. missing HEAD)
if [ ! -d "$SITE_CACHE/.git" ] || ! git -C "$SITE_CACHE" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  rm -rf "$SITE_CACHE"
  git clone --depth 1 "$SITE_REPO" "$SITE_CACHE" >/dev/null 2>&1 || fail "SITE_CLONE_FAIL"
fi
git -C "$SITE_CACHE" pull --ff-only >/dev/null 2>&1 || true
mkdir -p "$SITE_CACHE/assets/ig"
declare -a URLS=()
for s in 1 2 3; do
  cp "$CARO/slide$s.png" "$SITE_CACHE/assets/ig/text_${IDX}_$s.png"
  git -C "$SITE_CACHE" add "assets/ig/text_${IDX}_$s.png" 2>/dev/null
  URLS+=("$SITE_BASE/assets/ig/text_${IDX}_$s.png")
done
if git -C "$SITE_CACHE" diff --cached --quiet; then :; else
  git -C "$SITE_CACHE" -c user.name="FitXMatt Bot" -c user.email="kovokilla@gmail.com" commit -m "ig text carousel #$N" >/dev/null 2>&1
  git -C "$SITE_CACHE" push >/dev/null 2>&1 || fail "site push failed"
fi
for u in "${URLS[@]}"; do
  for i in $(seq 1 24); do
    code=$(curl -sS -o /dev/null -w "%{http_code}" "$u" 2>/dev/null); [ "$code" = "200" ] && break; sleep 5
  done
  [ "$code" = "200" ] || fail "image not live ($u -> $code)"
done

# --- publish CAROUSEL (3 media items -> carousel container -> publish) ---
API="https://graph.facebook.com/v22.0"
mk_child(){
  curl -sS -m 90 -F "image_url=$1" -F "is_carousel_item=true" \
    "$API/$IG_USER_ID/media?access_token=$IG_TOKEN" 2>/dev/null
}
MIDS=()
for u in "${URLS[@]}"; do
  RESP=$(mk_child "$u")
  MID=$(echo "$RESP" | $PY -c "import sys,json;print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
  [ -n "$MID" ] || fail "media create: $RESP"
  MIDS+=("$MID")
done
# carousel container referencing the 3 children
CRESP=$(curl -sS -m 60 -F "media_type=CAROUSEL" \
  -F "children=${MIDS[0]},${MIDS[1]},${MIDS[2]}" \
  -F "caption=$CAPTION" \
  "$API/$IG_USER_ID/media?access_token=$IG_TOKEN" 2>/dev/null)
CAROUSEL=$(echo "$CRESP" | $PY -c "import sys,json;print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
[ -n "$CAROUSEL" ] || fail "carousel container: $CRESP"
# wait for container to finish
for i in $(seq 1 20); do
  ST=$(curl -sS -m 30 "$API/$CAROUSEL?fields=status_code&access_token=$IG_TOKEN" 2>/dev/null | $PY -c "import sys,json;print(json.load(sys.stdin).get('status_code',''))" 2>/dev/null)
  [ "$ST" = "FINISHED" ] && break; sleep 3
done
[ "$ST" = "FINISHED" ] || fail "carousel container not ready ($ST)"
RESP=$(curl -sS -m 60 -F "creation_id=$CAROUSEL" "$API/$IG_USER_ID/media_publish?access_token=$IG_TOKEN" 2>/dev/null)
PID=$(echo "$RESP" | $PY -c "import sys,json;print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
[ -n "$PID" ] && echo "IG_PUBLISHED #$N post_id=$PID" || fail "publish: $RESP"

# --- advance pointer (wrap at bank size) ---
TOTAL=$($PY -c "import json;print(len(json.load(open('$BANK'))['carousels']))")
NEXT=$(( (IDX + 1) % TOTAL ))
printf '%s\n' "$NEXT" > "$PTR"
echo "DONE ig text carousel #$N next=#$(( NEXT + 1 ))"
