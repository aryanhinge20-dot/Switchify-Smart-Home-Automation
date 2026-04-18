import speech_recognition as sr
import threading
import time
import re
from flask import Flask, render_template_string, jsonify, request
import control
from datetime import datetime, timedelta

app = Flask(__name__)

# ---------------- DEVICE STATE ----------------
devices = {
    "light1": {"on": False, "start": 0, "time": 0, "power": 10},
    "light2": {"on": False, "start": 0, "time": 0, "power": 10},
    "fan": {"on": False, "start": 0, "time": 0, "power": 60}
}

# ---------------- GLOBAL ----------------
auto_mode = False
sequence_log = []
trained_sequences = []
final_sequence = []
avg_time = None
generation = 0

# ---------------- SCENARIOS ----------------
scenarios = []

# ---------------- CLOCK ----------------
BASE_TIME = datetime(2026,4,18,18,0,0)
SET_AT = time.time()

def get_time():
    return BASE_TIME + timedelta(seconds=(time.time()-SET_AT))

def reset_time():
    global SET_AT
    SET_AT = time.time()

# ---------------- HELPERS ----------------
def time_to_seconds(t):
    h,m,s = map(int,t.split(":"))
    return h*3600+m*60+s

# ---------------- CONTROL ----------------
def on(dev, func, user=True):
    func()
    if not devices[dev]["on"]:
        devices[dev]["on"] = True
        devices[dev]["start"] = time.time()

        if user:
            t = get_time().strftime("%H:%M:%S")
            sequence_log.append((dev+"_on", t))

            if auto_mode and final_sequence:
                if dev+"_on" == final_sequence[0][0]:
                    now = time_to_seconds(t)
                    if avg_time and abs(now - avg_time) <= 300:
                        run_markov()

def off(dev, func, user=True):
    func()
    if devices[dev]["on"]:
        devices[dev]["time"] += time.time() - devices[dev]["start"]
        devices[dev]["on"] = False

        if user:
            t = get_time().strftime("%H:%M:%S")
            sequence_log.append((dev+"_off", t))

# ---------------- MARKOV ----------------
def run_markov():
    base = time_to_seconds(final_sequence[0][1])

    for action,t in final_sequence[1:]:
        dev,state = action.split("_")
        delay = time_to_seconds(t)-base

        def delayed(d=dev,s=state,w=delay):
            time.sleep(w)
            if auto_mode:
                if s=="on":
                    on(d,getattr(control,f"{d}_on"),False)
                else:
                    off(d,getattr(control,f"{d}_off"),False)

        threading.Thread(target=delayed).start()

# ---------------- TRAIN ----------------
@app.route('/change_date')
def change_date():
    global sequence_log, trained_sequences, final_sequence, avg_time, generation

    if len(sequence_log)>1:
        trained_sequences.append(sequence_log.copy())

    if len(trained_sequences)>=3:
        final_sequence = trained_sequences[-1]
        times=[time_to_seconds(x[0][1]) for x in trained_sequences[-3:]]
        avg_time=sum(times)//len(times)

    sequence_log=[]
    generation+=1
    reset_time()

    for s in scenarios:
        s["triggered"]=False

    for d in devices:
        off(d,getattr(control,f"{d}_off"),False)

    return "OK"

# ---------------- AUTO TOGGLE ----------------
@app.route('/toggle_auto')
def toggle_auto():
    global auto_mode, generation
    auto_mode = not auto_mode
    generation += 1
    return jsonify({"auto": auto_mode})

# ---------------- SCENARIO ----------------
@app.route('/add_scenario',methods=['POST'])
def add_scenario():
    data=request.json
    scenarios.append({
        "time":data["time"],
        "devices":data["devices"],
        "duration":int(data["duration"]),
        "triggered":False
    })
    return "OK"

@app.route('/get_scenarios')
def get_scenarios():
    return jsonify(scenarios)

@app.route('/delete_scenario/<int:i>')
def delete_scenario(i):
    if i<len(scenarios):
        scenarios.pop(i)
    return "OK"

def scenario_runner():
    while True:
        now=get_time().strftime("%H:%M")

        for s in scenarios:
            if s["time"]==now and not s["triggered"]:
                for d in s["devices"]:
                    on(d,getattr(control,f"{d}_on"),False)

                def offlater(devs=s["devices"],dur=s["duration"]):
                    time.sleep(dur*60)
                    for d in devs:
                        off(d,getattr(control,f"{d}_off"),False)

                threading.Thread(target=offlater).start()
                s["triggered"]=True

        time.sleep(1)

# ---------------- VOICE ----------------

def clean(cmd):
    cmd = cmd.lower()

    rep = {
        # numbers
        "one":"1","two":"2","to":"2","too":"2",

        # Hindi / Marathi devices
        "batti":"light","lighta":"light",
        "pankha":"fan",

        # actions
        "chalu":"on","chala":"on","start":"on",
        "band":"off","bandh":"off","stop":"off",

        # modes
        "tej":"bright",
        "halka":"dim",
        "normal":"normal"
    }

    for k,v in rep.items():
        cmd = cmd.replace(k,v)

    return cmd


def get_devices(cmd):
    devs = []

    if "light 1" in cmd or "light1" in cmd:
        devs.append("light1")

    if "light 2" in cmd or "light2" in cmd:
        devs.append("light2")

    if "fan" in cmd:
        devs.append("fan")

    return devs


def extract_time_cmd(cmd):
    m = re.search(r"(\d+)\s*(second|seconds|minute|minutes)", cmd)
    if m:
        val = int(m.group(1))
        if "minute" in m.group(2):
            return val * 60
        return val
    return None


def run_timer(dev, duration):
    on(dev, getattr(control, f"{dev}_on"))
    time.sleep(duration)
    off(dev, getattr(control, f"{dev}_off"))


# ---------- 3-IN-1 LIGHT (LIGHT2) ----------
current_mode = 1  # 1=bright, 2=dim, 3=normal

def set_mode(target):
    global current_mode

    # ensure ON
    on("light2", control.light2_on)

    steps = (target - current_mode) % 3

    for _ in range(steps):
        control.light2_off()
        time.sleep(0.3)
        control.light2_on()
        time.sleep(0.3)

    current_mode = target
    print("Mode:", target)


def listen():
    r = sr.Recognizer()
    mic = sr.Microphone()

    print("🎤 Ready")

    while True:
        try:
            with mic as s:
                audio = r.listen(s)

            cmd = clean(r.recognize_google(audio, language="en-IN"))
            print("You:", cmd)

            # -------- GOOD NIGHT --------
            if "good night" in cmd or "all off" in cmd:
                control.all_off()
                for d in devices:
                    devices[d]["on"] = False
                print("All OFF")
                continue

            # -------- LIGHT MODES --------
            if "bright" in cmd:
                set_mode(1)
                continue

            if "dim" in cmd:
                set_mode(2)
                continue

            if "normal" in cmd:
                set_mode(3)
                continue

            # -------- TIMER --------
            duration = extract_time_cmd(cmd)

            # -------- MULTI DEVICE --------
            devs = get_devices(cmd)

            if devs:
                for d in devs:
                    if duration:
                        threading.Thread(target=run_timer, args=(d, duration)).start()
                    elif "on" in cmd:
                        on(d, getattr(control, f"{d}_on"))
                    elif "off" in cmd:
                        off(d, getattr(control, f"{d}_off"))

        except Exception as e:
            print("VOICE ERROR:", e)

# ---------------- USAGE ----------------
@app.route("/usage")
def usage():
    data={}
    total=0
    for d,v in devices.items():
        t=v["time"]
        if v["on"]:
            t+=time.time()-v["start"]
        p=(t/3600)*v["power"]
        total+=p
        data[d]={"power":round(p,2)}
    data["total"]=round(total,2)
    return jsonify(data)

# ---------------- MAIN UI ----------------
HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
body{background:#0f172a;color:white;text-align:center;font-family:Arial}
.card{background:#1e293b;padding:20px;margin:20px;border-radius:15px}
button{padding:12px;margin:10px;border-radius:10px}
</style>
</head>
<body>

<h1>⚡ Smart Home</h1>
<h2 id="clock"></h2>

<div class="card">
<button onclick="toggle('light1')" id="light1">Light1</button>
<button onclick="toggle('light2')" id="light2">Light2</button>
<button onclick="toggle('fan')" id="fan">Fan</button>
</div>

<div class="card">
<h3>Auto Mode</h3>
<button onclick="auto()">Toggle Auto</button>
<p id="auto">OFF</p>
</div>

<div class="card">
<button onclick="fetch('/change_date')">Change Date</button>
<button onclick="window.location='/scenario'">Scenario</button>
<button onclick="window.location='/usage_page'">Usage</button>
<input type ="time"  id="settime">
<button onclick ="setTime()">Set Time</button>
</div>

<script>
function toggle(d){ fetch('/toggle/'+d) }

function auto(){
 fetch('/toggle_auto').then(r=>r.json()).then(d=>{
   document.getElementById("auto").innerText = d.auto ? "ON":"OFF"
 })
}

setInterval(()=>{
 fetch('/status').then(r=>r.json()).then(d=>{
  for(let k in d){
   document.getElementById(k).innerText=k+" "+(d[k].on?"ON":"OFF")
  }
 })

 fetch('/time').then(r=>r.json()).then(t=>{
  document.getElementById("clock").innerText=t.time
 })
},1000)
function setTime(){
 let t = document.getElementById("settime").value
 fetch('/set_time',{
  method:'POST',
  headers:{'Content-Type':'application/json'},
  body:JSON.stringify({time:t})
 })
}
</script>

</body>
</html>
"""

# ---------------- SCENARIO UI ----------------
SCENARIO_HTML = """
<!DOCTYPE html>
<html>
<body style="background:#0f172a;color:white;text-align:center">

<h1>📅 Scenario</h1>

<input type="time" id="time"><br><br>

<label><input type="checkbox" value="light1">Light1</label><br>
<label><input type="checkbox" value="light2">Light2</label><br>
<label><input type="checkbox" value="fan">Fan</label><br><br>

<input type="number" id="dur" placeholder="Duration (min)"><br><br>

<button onclick="add()">Add Scenario</button>

<h2>Saved</h2>
<div id="list"></div>

<br><a href="/">Back</a>

<script>
function add(){
 let devs=[]
 document.querySelectorAll("input:checked").forEach(x=>devs.push(x.value))

 fetch('/add_scenario',{
  method:'POST',
  headers:{'Content-Type':'application/json'},
  body:JSON.stringify({
   time:document.getElementById("time").value,
   devices:devs,
   duration:document.getElementById("dur").value
  })
 }).then(load)
}

function del(i){
 if(confirm("Delete?")){
  fetch('/delete_scenario/'+i).then(load)
 }
}

function load(){
 fetch('/get_scenarios').then(r=>r.json()).then(data=>{
  let h=""
  data.forEach((s,i)=>{
   h+=`${s.time} → ${s.devices.join(",")} (${s.duration}m)
   <button onclick="del(${i})">Delete</button><br>`
  })
  document.getElementById("list").innerHTML=h
 })
}

load()
</script>

</body>
</html>
"""

# ---------------- ROUTES ----------------
@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/scenario')
def scenario():
    return render_template_string(SCENARIO_HTML)

@app.route('/usage_page')
def usage_page():
    return render_template_string("""
    <html><body style="background:#0f172a;color:white;text-align:center">
    <h1>⚡ Usage</h1>
    <h2 id="clock"></h2>
    <div id="data"></div>
    <br><button onclick="window.location='/'">Back</button>

    <script>
    setInterval(()=>{
        fetch('/usage').then(r=>r.json()).then(d=>{
            document.getElementById('data').innerHTML =
            "Light1: "+d.light1.power+" Wh<br>"+
            "Light2: "+d.light2.power+" Wh<br>"+
            "Fan: "+d.fan.power+" Wh<br><br>"+
            "Total: "+d.total+" Wh"
        })
        fetch('/time').then(r=>r.json()).then(t=>{
            document.getElementById("clock").innerText = t.time
        })
    },1000)
    </script>
    </body></html>
    """)

@app.route('/toggle/<d>')
def toggle(d):
    if devices[d]["on"]:
        off(d,getattr(control,f"{d}_off"))
    else:
        on(d,getattr(control,f"{d}_on"))
    return "OK"

@app.route('/status')
def status():
    return jsonify(devices)

@app.route('/time')
def time_api():
    return jsonify({"time":get_time().strftime("%H:%M:%S")})



@app.route('/set_time', methods=['POST'])
def set_time():
    global BASE_TIME, SET_AT
    data = request.json
    h, m = map(int, data["time"].split(":"))
    BASE_TIME = BASE_TIME.replace(hour=h, minute=m, second=0)
    SET_AT = time.time()
    return "OK"
# ---------------- MAIN ----------------
if __name__=="__main__":
    threading.Thread(target=listen,daemon=True).start()
    threading.Thread(target=scenario_runner,daemon=True).start()
    app.run(host="0.0.0.0",port=5000)
