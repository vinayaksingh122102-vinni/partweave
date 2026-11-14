import base64, io, os, uuid
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from flask_cors import CORS
import qrcode

app = Flask(__name__)
CORS(app)

def now(): return datetime.now(timezone.utc).isoformat()
def ident(prefix): return f"{prefix}_{uuid.uuid4().hex[:8]}"

devices = [
    {"id":"dev_1","manufacturer":"Lenovo","model":"ThinkPad T480","family":"ThinkPad","ram_types":["DDR4 SO-DIMM"],"max_ram_gb":32,"storage_interfaces":["M.2 2280 NVMe","2.5in SATA"],"notes":"Two SO-DIMM slots; NVMe boot support depends on BIOS configuration."},
    {"id":"dev_2","manufacturer":"Dell","model":"Latitude 5490","family":"Latitude","ram_types":["DDR4 SO-DIMM"],"max_ram_gb":32,"storage_interfaces":["M.2 2280 NVMe","2.5in SATA"],"notes":"DDR4-2400 target; lower speed modules downclock."},
    {"id":"dev_3","manufacturer":"HP","model":"EliteBook 840 G5","family":"EliteBook","ram_types":["DDR4 SO-DIMM"],"max_ram_gb":32,"storage_interfaces":["M.2 2280 NVMe"],"notes":"Single-sided M.2 2280 clearance preferred."},
]
components = [
    {"id":"cmp_1","title":"16GB DDR4 SO-DIMM 2666MHz","component_type":"RAM","brand":"Samsung","model":"M471A2K43CB1","specs":{"ram_type":"DDR4 SO-DIMM","capacity_gb":16,"speed_mhz":2666,"voltage":1.2},"condition":"Tested","price":28,"quantity":3,"location":"Bengaluru, IN","seller":"ReLoop Labs","seller_role":"supplier","status":"available","created_at":now()},
    {"id":"cmp_2","title":"512GB NVMe M.2 SSD","component_type":"SSD","brand":"WD","model":"SN570","specs":{"interface":"NVMe PCIe 3.0","form_factor":"M.2 2280","capacity_gb":512},"condition":"Pulled · health 94%","price":34,"quantity":1,"location":"Pune, IN","seller":"Aarav Repairs","seller_role":"technician","status":"available","created_at":now()},
    {"id":"cmp_3","title":"8GB DDR4 SO-DIMM 2400MHz","component_type":"RAM","brand":"Micron","model":"MTA8ATF1G64HZ","specs":{"ram_type":"DDR4 SO-DIMM","capacity_gb":8,"speed_mhz":2400,"voltage":1.2},"condition":"Tested","price":14,"quantity":6,"location":"Delhi, IN","seller":"CircuitCycle","seller_role":"supplier","status":"available","created_at":now()},
    {"id":"cmp_4","title":"1TB M.2 SATA SSD","component_type":"SSD","brand":"Crucial","model":"MX500 M.2","specs":{"interface":"SATA III","form_factor":"M.2 2280","capacity_gb":1000},"condition":"Good · health 88%","price":31,"quantity":1,"location":"Mumbai, IN","seller":"Nisha Tech","seller_role":"technician","status":"available","created_at":now()},
]
repairs = [{"id":"rep_1","component_id":"cmp_1","device_id":"dev_1","outcome":"successful","notes":"Passed 4-hour memory test","created_at":now()}]

@app.get('/api/health')
def health(): return jsonify({"status":"ok","service":"partweave-api","database":"postgresql" if os.getenv('DATABASE_URL') else "demo-memory"})

@app.get('/api/summary')
def summary():
    return jsonify({"listed_components": 1248, "available_now": len(components), "devices_indexed": 387, "repairs_enabled": 932, "reuse_rate": 78, "successful_repairs": 932, "impact":{"co2_kg":1840,"e_waste_kg":612,"value_recovered":28400}, "activity":[{"label":"Successful repairs","value":932,"tone":"cyan"},{"label":"Parts listed","value":1248,"tone":"violet"},{"label":"Devices indexed","value":387,"tone":"gold"}]})

@app.get('/api/components')
def list_components():
    q = request.args.get('q','').lower(); kind = request.args.get('type','all'); sort = request.args.get('sort','newest')
    data = [c for c in components if (not q or q in (c['title']+' '+c['brand']+' '+c['model']).lower()) and (kind == 'all' or c['component_type'] == kind)]
    if sort == 'price-low': data.sort(key=lambda x:x['price'])
    elif sort == 'price-high': data.sort(key=lambda x:-x['price'])
    return jsonify({"items":data,"total":len(data)})

@app.post('/api/components')
def create_component():
    payload = request.get_json(force=True)
    required = ['title','component_type','specs']
    missing = [key for key in required if not payload.get(key)]
    if missing: return jsonify({"error":"Missing fields","fields":missing}), 400
    item = {"id":ident('cmp'),"title":payload['title'],"component_type":payload['component_type'],"brand":payload.get('brand','Unbranded'),"model":payload.get('model','Unknown'),"specs":payload['specs'],"condition":payload.get('condition','Tested'),"price":float(payload.get('price',0)),"quantity":int(payload.get('quantity',1)),"location":payload.get('location','Remote'),"seller":payload.get('seller','Demo Seller'),"seller_role":payload.get('seller_role','technician'),"status":"available","created_at":now()}
    components.insert(0,item); return jsonify(item), 201

@app.get('/api/components/<component_id>')
def component(component_id):
    item = next((c for c in components if c['id']==component_id),None)
    return jsonify(item) if item else (jsonify({"error":"Component not found"}),404)

@app.delete('/api/components/<component_id>')
def delete_component(component_id):
    global components
    before = len(components); components = [c for c in components if c['id'] != component_id]
    return (jsonify({"deleted":True}),200) if len(components) < before else (jsonify({"error":"Not found"}),404)

@app.put('/api/components/<component_id>')
def update_component(component_id):
    payload = request.get_json(force=True)
    item = next((c for c in components if c['id'] == component_id), None)
    if not item: return jsonify({"error":"Not found"}), 404
    for key in ('title','condition','location','quantity','price','specs','status'):
        if key in payload: item[key] = payload[key]
    return jsonify(item)

@app.get('/api/devices')
def list_devices(): return jsonify({"items":devices})

def explain(component, device):
    c, d = component.get('specs',{}), device
    reasons=[]; unknown=[]; status='compatible'
    if component['component_type']=='RAM':
        if not c.get('ram_type'): unknown.append('RAM type')
        elif c['ram_type'] not in d['ram_types']: reasons.append(f"{c['ram_type']} is not supported; device expects {', '.join(d['ram_types'])}")
        if not c.get('capacity_gb'): unknown.append('capacity')
        elif c['capacity_gb'] > d['max_ram_gb']: reasons.append(f"module capacity exceeds the {d['max_ram_gb']} GB device limit")
    elif component['component_type']=='SSD':
        if not c.get('interface'): unknown.append('storage interface')
        elif not any(x.lower() in c['interface'].lower() or c['interface'].lower() in x.lower() for x in d['storage_interfaces']): reasons.append(f"{c['interface']} does not match {', '.join(d['storage_interfaces'])}")
        if not c.get('form_factor'): unknown.append('form factor')
    if reasons: status='incompatible'
    elif unknown: status='potential'
    else: reasons.append('all supplied specifications match the device compatibility profile')
    return {"status":status,"reasons":reasons,"unknown":unknown,"device":d['manufacturer']+' '+d['model'],"component":component['title']}

@app.post('/api/compatibility/check')
def compatibility():
    p=request.get_json(force=True); c=next((x for x in components if x['id']==p.get('component_id')),None); d=next((x for x in devices if x['id']==p.get('device_id')),None)
    if not c or not d: return jsonify({"error":"Choose a valid component and device"}),400
    return jsonify(explain(c,d))

@app.get('/api/graph')
def graph():
    nodes=[{"data":{"id":d['id'],"label":d['manufacturer']+' '+d['model'],"kind":"device"}} for d in devices] + [{"data":{"id":c['id'],"label":c['title'],"kind":"component"}} for c in components]
    edges=[]
    for c in components:
        for d in devices:
            result=explain(c,d)
            if result['status'] != 'incompatible': edges.append({"data":{"id":c['id']+'_'+d['id'],"source":c['id'],"target":d['id'],"status":result['status']}})
    return jsonify({"nodes":nodes,"edges":edges})

@app.post('/api/repairs')
def repair():
    p=request.get_json(force=True); item={"id":ident('rep'),"component_id":p.get('component_id'),"device_id":p.get('device_id'),"outcome":p.get('outcome','successful'),"notes":p.get('notes',''),"created_at":now()}; repairs.append(item); return jsonify(item),201

@app.post('/api/components/<component_id>/passport')
def passport(component_id):
    item=next((c for c in components if c['id']==component_id),None)
    if not item: return jsonify({"error":"Component not found"}),404
    qr=qrcode.make(f"https://partweave.local/passport/{component_id}"); buf=io.BytesIO(); qr.save(buf,format='PNG'); encoded=base64.b64encode(buf.getvalue()).decode()
    return jsonify({"component_id":component_id,"passport_url":f"https://partweave.local/passport/{component_id}","qr_data_url":"data:image/png;base64,"+encoded})

if __name__ == '__main__': app.run(host='0.0.0.0',port=int(os.getenv('PORT',5000)),debug=True)
