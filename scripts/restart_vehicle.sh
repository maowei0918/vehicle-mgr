PID=$(ps -eo pid,args | awk '/[u]vicorn main:app/{print $1; exit}')
if [ -n "$PID" ]; then
  kill "$PID"
fi
sleep 2
cd /vol1/@appcenter/vehicle-mgr/后端
nohup /vol1/@appcenter/vehicle-mgr/Python/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8700 --workers 1 >> /vol1/@appdata/vehicle-mgr/info.log 2>&1 &
