#!/bin/bash
# Qdrant Health Check
QDRANT="http://[HOST]:6333"
ERRORS=0

echo "=== Qdrant Health Check $(date '+%Y-%m-%d %H:%M') ==="

# Service check
curl -sf "$QDRANT/collections" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Qdrant service DOWN"
    exit 1
fi
echo "✅ Service: OK"

for COL in hermes_vault hermes_financial hermes_trading; do
    INFO=$(curl -sf "$QDRANT/collections/$COL" 2>&1)
    if [ $? -ne 0 ]; then
        echo "❌ $COL: NOT FOUND"
        ERRORS=$((ERRORS + 1))
        continue
    fi
    STATUS=$(echo "$INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['status'])")
    POINTS=$(echo "$INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['points_count'])")
    INDEXED=$(echo "$INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['indexed_vectors_count'])")
    SEGMENTS=$(echo "$INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['segments_count'])")
    
    if [ "$STATUS" = "green" ] && [ "$POINTS" = "$INDEXED" ]; then
        echo "✅ $COL: $POINTS pts | $INDEXED idx | $SEGMENTS seg"
    else
        echo "⚠️  $COL: $STATUS | $POINTS pts | $INDEXED idx | $SEGMENTS seg"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
[ $ERRORS -eq 0 ] && echo "All collections healthy." || echo "$ERRORS issue(s) found."
exit $ERRORS
