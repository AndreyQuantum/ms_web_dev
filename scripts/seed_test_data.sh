#!/usr/bin/env bash
set -euo pipefail

PRODUCTS_URL="${PRODUCTS_URL:-http://localhost:8002}"
ORDERS_URL="${ORDERS_URL:-http://localhost:8003}"

SUFFIX="$(date +%s)-${RANDOM}"

# ----- helpers -----------------------------------------------------------------

die() { echo "ERROR: $*" >&2; exit 1; }

require_bin() {
    command -v "$1" >/dev/null 2>&1 || die "missing required binary: $1"
}

http_request() {
    local method=$1 url=$2 body=$3 response status payload
    response=$(curl -sS -X "$method" "$url" \
        -H "Content-Type: application/json" \
        -w $'\n%{http_code}' \
        -d "$body")
    status=${response##*$'\n'}
    payload=${response%$'\n'*}
    if [[ "$status" -lt 200 || "$status" -ge 300 ]]; then
        die "$method $url -> HTTP $status: $payload"
    fi
    printf '%s' "$payload"
}

post_json()  { http_request POST  "$1" "$2"; }
patch_json() { http_request PATCH "$1" "$2"; }

extract_id() { python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])'; }

ping_health() {
    local url=$1
    curl -fsS -o /dev/null --max-time 3 "$url/health" || die "service not reachable: $url/health"
}

create_dict() {
    local path=$1 name=$2
    post_json "$PRODUCTS_URL/api/v1/$path" "{\"name\":\"$name\"}" | extract_id
}

create_promo() {
    local name=$1 percent=$2
    post_json "$PRODUCTS_URL/api/v1/promos" \
        "{\"name\":\"$name\",\"discount_percent\":$percent}" | extract_id
}

create_product() {
    local payload=$1
    post_json "$PRODUCTS_URL/api/v1/products" "$payload" | extract_id
}

create_review() {
    local product_id=$1 rating=$2 text=$3
    post_json "$PRODUCTS_URL/api/v1/reviews" \
        "{\"product_id\":\"$product_id\",\"rating\":$rating,\"text\":\"$text\"}" | extract_id
}

create_order() {
    local payload=$1
    post_json "$ORDERS_URL/api/v1/orders" "$payload" | extract_id
}

set_order_status() {
    local order_id=$1 new_status=$2
    patch_json "$ORDERS_URL/api/v1/orders/$order_id" \
        "{\"status\":\"$new_status\"}" >/dev/null
}

# ----- pre-flight --------------------------------------------------------------

require_bin curl
require_bin python3
ping_health "$PRODUCTS_URL"
ping_health "$ORDERS_URL"

echo "Seeding against:"
echo "  products: $PRODUCTS_URL"
echo "  orders:   $ORDERS_URL"
echo "  suffix:   $SUFFIX"
echo

# ----- dictionaries ------------------------------------------------------------

echo "Creating categories..."
CAT_LED=$(create_dict categories     "LED-$SUFFIX")
CAT_HAL=$(create_dict categories     "Halogen-$SUFFIX")
CAT_SMART=$(create_dict categories   "Smart-$SUFFIX")
CAT_SPECIAL=$(create_dict categories "Specialty-$SUFFIX")

echo "Creating bulb types..."
BT_FIL=$(create_dict bulb-types "Filament-$SUFFIX")
BT_COB=$(create_dict bulb-types "COB-$SUFFIX")
BT_SMD=$(create_dict bulb-types "SMD-$SUFFIX")
BT_HAL=$(create_dict bulb-types "HalogenCap-$SUFFIX")

echo "Creating bulb shapes..."
BS_A60=$(create_dict bulb-shapes "A60-$SUFFIX")
BS_G45=$(create_dict bulb-shapes "G45-$SUFFIX")
BS_T8=$(create_dict bulb-shapes  "T8-$SUFFIX")
BS_ST64=$(create_dict bulb-shapes "ST64-$SUFFIX")

echo "Creating sockets..."
SOCK_E14=$(create_dict sockets  "E14-$SUFFIX")
SOCK_E27=$(create_dict sockets  "E27-$SUFFIX")
SOCK_GU10=$(create_dict sockets "GU10-$SUFFIX")
SOCK_B22=$(create_dict sockets  "B22-$SUFFIX")
SOCK_GU53=$(create_dict sockets "GU5.3-$SUFFIX")

echo "Creating suppliers..."
SUP_ACME=$(create_dict suppliers    "Acme-$SUFFIX")
SUP_GLOBEX=$(create_dict suppliers  "Globex-$SUFFIX")
SUP_INITECH=$(create_dict suppliers "Initech-$SUFFIX")
SUP_BRIGHT=$(create_dict suppliers  "BrightCo-$SUFFIX")

echo "Creating promos..."
PROMO_SUMMER=$(create_promo "Summer-$SUFFIX"      15)
PROMO_BF=$(create_promo     "BlackFriday-$SUFFIX" 50)
PROMO_WHOLE=$(create_promo  "Wholesale-$SUFFIX"   10)

# ----- products ----------------------------------------------------------------
# Spread across categories so `?category_id=X` returns multiple results per category.
# Some products are archived so `?is_archived=true` returns results too
# (default `?is_archived=false` already returns the active majority).
# Total >10 so default pagination (size=10) shows page=2 has tail items.

echo "Creating products..."
make_product_payload() {
    local title=$1 price=$2 qty=$3 brightness=$4 \
          cat=$5 bt=$6 bs=$7 sock=$8 sup=$9 \
          promo=${10:-null} archived=${11:-false}
    cat <<JSON
{
  "title": "${title}-${SUFFIX}",
  "description": "Seeded test product ${title}",
  "price": "${price}",
  "quantity": ${qty},
  "brightness_lm": ${brightness},
  "is_archived": ${archived},
  "category_id": ${cat},
  "bulb_type_id": ${bt},
  "bulb_shape_id": ${bs},
  "socket_id": ${sock},
  "supplier_id": ${sup},
  "promo_id": ${promo}
}
JSON
}

# LED category (5 products)
P_LED_A60_WARM=$(create_product "$(make_product_payload 'LED-A60-Warm'    '4.50'  120 800  "$CAT_LED" "$BT_SMD" "$BS_A60" "$SOCK_E27" "$SUP_ACME"   "$PROMO_SUMMER")")
P_LED_A60_COOL=$(create_product "$(make_product_payload 'LED-A60-Cool'    '4.70'   90 850  "$CAT_LED" "$BT_SMD" "$BS_A60" "$SOCK_E27" "$SUP_ACME")")
P_LED_G45=$(create_product      "$(make_product_payload 'LED-G45-Cool'    '3.20'   80 470  "$CAT_LED" "$BT_SMD" "$BS_G45" "$SOCK_E14" "$SUP_GLOBEX")")
P_LED_TUBE=$(create_product     "$(make_product_payload 'LED-Tube-T8'     '8.40'   25 1800 "$CAT_LED" "$BT_SMD" "$BS_T8"  "$SOCK_B22" "$SUP_GLOBEX" "$PROMO_SUMMER")")
P_LED_FIL=$(create_product      "$(make_product_payload 'LED-Filament-A60' '6.10' 110 600  "$CAT_LED" "$BT_FIL" "$BS_A60" "$SOCK_E27" "$SUP_BRIGHT")")

# Halogen category (3 products, one archived)
P_HAL_A60=$(create_product      "$(make_product_payload 'Halogen-A60'     '2.10'   50 700  "$CAT_HAL" "$BT_HAL" "$BS_A60" "$SOCK_E27"  "$SUP_ACME")")
P_HAL_GU10=$(create_product     "$(make_product_payload 'Halogen-GU10'    '2.80'   40 650  "$CAT_HAL" "$BT_HAL" "$BS_G45" "$SOCK_GU10" "$SUP_BRIGHT")")
P_HAL_VINTAGE=$(create_product  "$(make_product_payload 'Halogen-Vintage' '3.50'   10 500  "$CAT_HAL" "$BT_FIL" "$BS_ST64" "$SOCK_E27" "$SUP_BRIGHT" null true)")

# Smart category (4 products)
P_SMART_E27=$(create_product    "$(make_product_payload 'Smart-RGB-E27'   '18.90'  40 1100 "$CAT_SMART" "$BT_COB" "$BS_A60" "$SOCK_E27"  "$SUP_INITECH" "$PROMO_BF")")
P_SMART_GU10=$(create_product   "$(make_product_payload 'Smart-Spot-GU10' '12.50'  60 600  "$CAT_SMART" "$BT_COB" "$BS_G45" "$SOCK_GU10" "$SUP_INITECH")")
P_SMART_E14=$(create_product    "$(make_product_payload 'Smart-Bulb-E14'  '14.20'  35 700  "$CAT_SMART" "$BT_COB" "$BS_G45" "$SOCK_E14"  "$SUP_INITECH" "$PROMO_WHOLE")")
P_SMART_STRIP=$(create_product  "$(make_product_payload 'Smart-Strip-RGB' '24.00'  20 900  "$CAT_SMART" "$BT_SMD" "$BS_T8"  "$SOCK_GU53" "$SUP_INITECH")")

# Specialty category (2 products, one archived)
P_SPEC_EDISON=$(create_product  "$(make_product_payload 'Specialty-Edison' '9.90'   30 350 "$CAT_SPECIAL" "$BT_FIL" "$BS_ST64" "$SOCK_E27" "$SUP_BRIGHT")")
P_SPEC_UV=$(create_product      "$(make_product_payload 'Specialty-UV'    '15.00'   5 200  "$CAT_SPECIAL" "$BT_FIL" "$BS_A60"  "$SOCK_E14" "$SUP_GLOBEX" null true)")

# ----- reviews -----------------------------------------------------------------
# At least one product (Smart-RGB-E27) gets multiple reviews so
# GET /api/v1/reviews?product_id=<that one> returns several rows.

echo "Creating reviews..."
create_review "$P_LED_A60_WARM" 5 "Bright and warm, exactly as described."   >/dev/null
create_review "$P_LED_A60_WARM" 4 "Good value for money."                    >/dev/null
create_review "$P_LED_G45"      3 "Decent but a bit dim."                    >/dev/null
create_review "$P_LED_G45"      4 "Works fine in the bathroom fixture."      >/dev/null
create_review "$P_LED_TUBE"     2 "Flickers on a dimmer."                    >/dev/null
create_review "$P_LED_FIL"      5 "Looks great in an open fixture."          >/dev/null
create_review "$P_SMART_E27"    5 "App pairing was painless."                >/dev/null
create_review "$P_SMART_E27"    4 "Color accuracy could be slightly better." >/dev/null
create_review "$P_SMART_E27"    3 "Loses Wi-Fi every few weeks."             >/dev/null
create_review "$P_SMART_GU10"   4 "Great for the kitchen spotlights."        >/dev/null
create_review "$P_SMART_STRIP"  5 "Adhesive holds well, colors are vivid."   >/dev/null
create_review "$P_HAL_A60"      3 "Standard halogen, nothing remarkable."    >/dev/null
create_review "$P_SPEC_EDISON"  4 "Pretty filament glow."                    >/dev/null

# ----- orders ------------------------------------------------------------------
# Mix that exercises every status filter AND pagination.
# 12 orders total: enough for default-size=10 to spill onto page=2.
# End states: NEW>=4, IN_PROGRESS>=1, DELIVERED>=1, CANCELLED>=2.

echo "Creating orders..."
make_order_payload() {
    local email=$1 phone=$2 comment=$3 items_json=$4
    cat <<JSON
{
  "client_email": "${email}",
  "client_phone": "${phone}",
  "comment": "${comment}",
  "items": ${items_json}
}
JSON
}

ORDER_ALICE=$(create_order "$(make_order_payload \
    "alice-${SUFFIX}@example.com" "+1-555-0101" "single-item order" \
    "[{\"product_id\":\"$P_LED_A60_WARM\",\"quantity\":3}]")")

ORDER_BOB=$(create_order "$(make_order_payload \
    "bob-${SUFFIX}@example.com" "+1-555-0202" "mixed cart" \
    "[
        {\"product_id\":\"$P_HAL_A60\",\"quantity\":2},
        {\"product_id\":\"$P_SMART_E27\",\"quantity\":1},
        {\"product_id\":\"$P_LED_TUBE\",\"quantity\":4}
    ]")")

ORDER_CAROL=$(create_order "$(make_order_payload \
    "carol-${SUFFIX}@example.com" "+1-555-0303" "smart bundle" \
    "[
        {\"product_id\":\"$P_SMART_E27\",\"quantity\":2},
        {\"product_id\":\"$P_SMART_GU10\",\"quantity\":4}
    ]")")

ORDER_DAN=$(create_order "$(make_order_payload \
    "dan-${SUFFIX}@example.com" "+1-555-0404" "office refit" \
    "[
        {\"product_id\":\"$P_LED_A60_COOL\",\"quantity\":10},
        {\"product_id\":\"$P_LED_G45\",\"quantity\":6}
    ]")")

ORDER_EVE=$(create_order "$(make_order_payload \
    "eve-${SUFFIX}@example.com" "+1-555-0505" "vintage display" \
    "[{\"product_id\":\"$P_SPEC_EDISON\",\"quantity\":2}]")")

ORDER_FRED=$(create_order "$(make_order_payload \
    "fred-${SUFFIX}@example.com" "+1-555-0606" "kitchen lights" \
    "[
        {\"product_id\":\"$P_HAL_GU10\",\"quantity\":4},
        {\"product_id\":\"$P_SMART_GU10\",\"quantity\":2}
    ]")")

ORDER_GRACE=$(create_order "$(make_order_payload \
    "grace-${SUFFIX}@example.com" "+1-555-0707" "smart-strip mood lighting" \
    "[{\"product_id\":\"$P_SMART_STRIP\",\"quantity\":3}]")")

ORDER_HENRY=$(create_order "$(make_order_payload \
    "henry-${SUFFIX}@example.com" "+1-555-0808" "warehouse tubes" \
    "[{\"product_id\":\"$P_LED_TUBE\",\"quantity\":12}]")")

ORDER_IVY=$(create_order "$(make_order_payload \
    "ivy-${SUFFIX}@example.com" "+1-555-0909" "filament aesthetic" \
    "[
        {\"product_id\":\"$P_LED_FIL\",\"quantity\":5},
        {\"product_id\":\"$P_SPEC_EDISON\",\"quantity\":3}
    ]")")

ORDER_JACK=$(create_order "$(make_order_payload \
    "jack-${SUFFIX}@example.com" "+1-555-1010" "mixed kitchen + bedroom" \
    "[
        {\"product_id\":\"$P_SMART_E14\",\"quantity\":4},
        {\"product_id\":\"$P_LED_A60_WARM\",\"quantity\":2}
    ]")")

ORDER_KATE=$(create_order "$(make_order_payload \
    "kate-${SUFFIX}@example.com" "+1-555-1111" "to be cancelled" \
    "[{\"product_id\":\"$P_HAL_A60\",\"quantity\":1}]")")

ORDER_LIAM=$(create_order "$(make_order_payload \
    "liam-${SUFFIX}@example.com" "+1-555-1212" "to be cancelled mid-progress" \
    "[{\"product_id\":\"$P_SMART_GU10\",\"quantity\":1}]")")

# Status transitions
echo "Transitioning order statuses..."
# DELIVERED chain: NEW -> IN_PROGRESS -> DELIVERED
set_order_status "$ORDER_BOB" IN_PROGRESS
set_order_status "$ORDER_BOB" DELIVERED

# IN_PROGRESS only
set_order_status "$ORDER_CAROL" IN_PROGRESS

# CANCELLED from NEW
set_order_status "$ORDER_KATE" CANCELLED

# CANCELLED via IN_PROGRESS
set_order_status "$ORDER_LIAM" IN_PROGRESS
set_order_status "$ORDER_LIAM" CANCELLED

# Remaining 8 stay NEW: alice, dan, eve, fred, grace, henry, ivy, jack

# ----- summary -----------------------------------------------------------------

cat <<SUMMARY

Done. Created:
  categories=4 bulb_types=4 bulb_shapes=4 sockets=5 suppliers=4 promos=3
  products=14 (12 active + 2 archived) reviews=13 orders=12

Status distribution after transitions:
  NEW=8 IN_PROGRESS=1 DELIVERED=1 CANCELLED=2

Try the filters:
  # by category (LED has 5 products):
  curl -s "$PRODUCTS_URL/api/v1/products?category_id=$CAT_LED"           | python3 -m json.tool | head -30
  # archived products only:
  curl -s "$PRODUCTS_URL/api/v1/products?is_archived=true"               | python3 -m json.tool | head -30
  # pagination (page 2 with default size=10):
  curl -s "$PRODUCTS_URL/api/v1/products?page=2"                         | python3 -m json.tool | head -30
  # reviews of one product (Smart-RGB-E27 has 3 reviews):
  curl -s "$PRODUCTS_URL/api/v1/reviews?product_id=$P_SMART_E27"         | python3 -m json.tool

  # orders by status:
  curl -s "$ORDERS_URL/api/v1/orders?status=NEW"                         | python3 -m json.tool | head -30
  curl -s "$ORDERS_URL/api/v1/orders?status=IN_PROGRESS"                 | python3 -m json.tool
  curl -s "$ORDERS_URL/api/v1/orders?status=DELIVERED"                   | python3 -m json.tool
  curl -s "$ORDERS_URL/api/v1/orders?status=CANCELLED"                   | python3 -m json.tool
  # orders pagination (12 total, page 2 with default size=10 has 2):
  curl -s "$ORDERS_URL/api/v1/orders?page=2"                             | python3 -m json.tool

Sample IDs:
  CAT_LED:        $CAT_LED
  CAT_SMART:      $CAT_SMART
  P_SMART_E27:    $P_SMART_E27
  ORDER_BOB:      $ORDER_BOB    (now DELIVERED)
  ORDER_LIAM:     $ORDER_LIAM   (now CANCELLED)
SUMMARY
