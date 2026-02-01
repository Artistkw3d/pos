#!/bin/bash
# Quick diagnosis script

echo "========================================="
echo "🔍 POS Server Diagnosis"
echo "========================================="
echo ""

echo "1️⃣ Container Status:"
docker ps | grep pos || echo "❌ Container not running!"
echo ""

echo "2️⃣ Container Logs (last 20 lines):"
docker logs pos --tail 20 2>&1
echo ""

echo "3️⃣ Python Process:"
docker exec pos ps aux | grep python 2>/dev/null || echo "❌ Cannot check process"
echo ""

echo "4️⃣ Database File:"
docker exec pos ls -lh database/pos.db 2>/dev/null || echo "❌ Database not found"
echo ""

echo "5️⃣ Port 8080:"
netstat -tulpn 2>/dev/null | grep 8080 || ss -tulpn | grep 8080 || echo "❌ Port check failed"
echo ""

echo "6️⃣ Test Server (GET /api/inventory):"
curl -s -o /dev/null -w "%{http_code}" http://192.168.8.21:8080/api/inventory 2>/dev/null || echo "❌ Server not responding"
echo ""

echo "========================================="
echo "✅ Diagnosis Complete"
echo "========================================="
