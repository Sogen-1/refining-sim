"""
油脂精炼工艺模拟引擎 - Web API
"""

import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from flask import Flask, jsonify, request, send_from_directory, Response
import io, csv

import config
if config.SUPPRESS_PRINT:
    import degumming, neutralization, bleaching, deodorization, winterization
    for m in [degumming, neutralization, bleaching, deodorization, winterization]:
        m.print = lambda *a, **k: None

from core import CrudeOil, ProcessConditions, OilType, CRUDE_OIL_TYPICAL
from engine import run_refining
from advisor import analyze_results
from cost import estimate_cost
from optimizer import get_smart_defaults, build_optimized_params, compare_params
from advanced import monte_carlo_sim, calculate_carbon_footprint, radar_scoring
from chokepoint import analyze_chokepoints
from pareto import pareto_optimize
from standards import check_gb_compliance, byproduct_deep_processing
from auto_calibrate import auto_calibrate, generate_comparison_report
from contaminants import predict_ge_formation, predict_3mcpd_formation, predict_pahs_removal, predict_pesticide_removal
from process_sheet import generate_process_sheet, water_footprint, byproduct_process_params

app = Flask(__name__, static_folder='.', static_url_path='')
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
import threading, uuid, time
_task_store = {}  # task_id -> {status, progress, result}

OIL_MAP = {
    "大豆油": OilType.SOYBEAN, "菜籽油": OilType.RAPESEED,
    "花生油": OilType.PEANUT, "葵花籽油": OilType.SUNFLOWER,
    "玉米油": OilType.CORN, "棉籽油": OilType.COTTONSEED,
    "棕榈油": OilType.PALM, "米糠油": OilType.RICE_BRAN,
}


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/run', methods=['POST'])
def run_simulation():
    """Run full 4-stage refining simulation (with optional async progress)"""
    data = request.json or {}
    async_mode = data.get('async', False)

    if async_mode:
        task_id = str(uuid.uuid4())[:8]
        _task_store[task_id] = {"status": "running", "progress": 0, "stage": "准备中...", "result": None}
        def _run_async():
            try:
                _task_store[task_id].update({"progress": 5, "stage": "脱胶工段..."})
                result = _run_sim_internal(data)
                _task_store[task_id].update({"progress": 40, "stage": "碱炼脱酸..."})
                _task_store[task_id].update({"progress": 55, "stage": "脱色工段..."})
                _task_store[task_id].update({"progress": 70, "stage": "脱臭工段..."})
                _task_store[task_id].update({"progress": 85, "stage": "生成优化建议..."})
                _task_store[task_id].update({"progress": 95, "stage": "完成..."})
                _task_store[task_id].update({"status": "done", "progress": 100, "result": result})
            except Exception as e:
                _task_store[task_id].update({"status": "error", "error": str(e)})
        threading.Thread(target=_run_async, daemon=True).start()
        return jsonify({"task_id": task_id})

    return jsonify(_run_sim_internal(data))


@app.route('/api/task/<task_id>')
def task_status(task_id):
    t = _task_store.get(task_id)
    if not t: return jsonify({"error": "Task not found"}), 404
    return jsonify({"status": t["status"], "progress": t["progress"],
                    "stage": t.get("stage",""), "result": t.get("result"),
                    "error": t.get("error")})


def _run_sim_internal(data):
    """内部模拟执行函数"""
    oil_name = str(data.get('oil', '大豆油'))
    oil_type = OIL_MAP.get(oil_name, OilType.SOYBEAN)
    typical = CRUDE_OIL_TYPICAL.get(oil_type, {"AV": 2.0, "P": 200, "NHP": 0.10, "Wax": 0})
    oil = CrudeOil(oil_type=oil_type, batch_name=oil_name,
                   mass_kg=data.get('mass', 100) * 1000,
                   acid_value=data.get('av') or typical["AV"],
                   phosphorus_ppm=data.get('p') or typical["P"],
                   nhp_ratio=data.get('nhp', typical["NHP"]),
                   wax_content_ppm=data.get('wax', typical.get("Wax", 0)))
    degum_type = data.get('degum', 'acid'); excess_lye = data.get('excess', 0.12)
    route = data.get('route', 'chemical'); include_wax = data.get('wax', False)

    result = run_refining(oil, pa_pct=data.get('pa_pct', 0.10),
                          excess_lye=excess_lye, degum_type=degum_type,
                          route=route, include_wax=include_wax)
    stages = result["stages"]; current_oil = result["final_oil"]
    total_loss = result["total_loss_kg"]; yield_pct = result["yield_pct"]
    stages_dict = {s["name"]: s for s in stages}
    advice = analyze_results(oil_type, stages_dict, oil.mass_kg / 1000)
    cost = estimate_cost(oil_type, oil.mass_kg / 1000, stages, stages_dict)

    return {
        "input": {"oil": oil_name, "mass_ton": round(oil.mass_kg/1000, 1),
                  "av": round(oil.acid_value, 2), "p_ppm": round(oil.phosphorus_ppm, 0),
                  "degum_type": degum_type, "excess_lye_pct": round(excess_lye, 3),
                  "route": route, "mass_kg": round(oil.mass_kg, 0)},
        "output": {"product_kg": round(current_oil.mass_kg, 1),
                   "product_av": round(current_oil.acid_value, 2),
                   "product_p_ppm": round(current_oil.phosphorus_ppm, 1),
                   "product_color_r": round(current_oil.color_red, 1),
                   "product_color_y": round(current_oil.color_yellow, 1),
                   "product_ve_ppm": round(current_oil.tocopherol_ppm, 0),
                   "total_loss_kg": round(total_loss, 1),
                   "total_loss_pct": round(total_loss/oil.mass_kg*100, 1),
                   "yield_pct": round(yield_pct, 1)},
        "stages": stages, "advisor": advice, "cost": cost,
    }


@app.route('/api/smart-defaults')
def smart_defaults():
    """根据油种返回推荐工艺参数"""
    oil_name = request.args.get('oil', '大豆油')
    oil_type = OIL_MAP.get(oil_name, OilType.SOYBEAN)
    return jsonify(get_smart_defaults(oil_type))


@app.route('/api/optimize', methods=['POST'])
def optimize_params():
    """一键优化：基于当前参数和模拟结果给出优化建议"""
    data = request.json
    oil_name = data.get('oil', '大豆油')
    oil_type = OIL_MAP.get(oil_name, OilType.SOYBEAN)

    current = {
        "degum": data.get("degum", "acid"),
        "pa_pct": data.get("pa_pct", 0.10),
        "excess_lye": data.get("excess", 0.12),
        "deodorization_temp_c": 245,
        "route": data.get("route", "chemical"),
        "wax": data.get("wax", False),
    }

    optimized = build_optimized_params(current, oil_type)
    diffs = compare_params(current, optimized)
    smart = get_smart_defaults(oil_type)

    # Remove internal keys
    suggestion_degum = optimized.pop("_degum_suggestion", current["degum"])

    return jsonify({
        "current": current,
        "optimized": optimized,
        "degum_suggestion": suggestion_degum,
        "changes": diffs,
        "smart_defaults": smart,
    })


@app.route('/api/advanced/monte-carlo', methods=['POST'])
def monte_carlo():
    """蒙特卡洛模拟"""
    d = request.json or {}
    result = monte_carlo_sim(
        OIL_MAP.get(d.get('oil','大豆油'), OilType.SOYBEAN),
        d.get('mass', 100), d.get('av', 2.0), d.get('av_std', 0.3),
        d.get('p', 800), d.get('p_std', 50), d.get('nhp', 0.15), 0.02,
        d.get('degum', 'acid'), d.get('excess', 0.12), d.get('runs', 50)
    )
    return jsonify(result)


@app.route('/api/advanced/carbon', methods=['POST'])
def carbon_footprint():
    """碳足迹核算"""
    d = request.json
    stages_dict = {s["name"]: s for s in d.get("stages", [])}
    result = calculate_carbon_footprint(d.get('mass_ton', 100), stages_dict)
    return jsonify(result)


@app.route('/api/advanced/radar', methods=['POST'])
def radar():
    """五维雷达评分"""
    d = request.json
    oil_type = OIL_MAP.get(d.get('oil','大豆油'), OilType.SOYBEAN)
    stages_dict = {s["name"]: s for s in d.get("stages", [])}
    result = radar_scoring(oil_type, stages_dict, d.get('mass_ton', 100))
    return jsonify(result)


@app.route('/api/advanced/chokepoint', methods=['POST'])
def chokepoint_analysis():
    d = request.json
    oil_type = OIL_MAP.get(d.get('oil','大豆油'), OilType.SOYBEAN)
    stages_dict = {s["name"]: s for s in d.get("stages", [])}
    result = analyze_chokepoints(oil_type, d.get('mass', 100),
                                  d.get('degum','acid'), d.get('route','chemical'),
                                  stages_dict)
    return jsonify(result)


@app.route('/api/process-sheet', methods=['POST'])
def process_sheet_api():
    d = request.json or {}
    sheet = generate_process_sheet(d.get('params', {}),
                                   OIL_MAP.get(d.get('oil', '大豆油'), OilType.SOYBEAN),
                                   d.get('mass', 100))
    return jsonify(sheet)


@app.route('/api/water-footprint', methods=['POST'])
def water_fp_api():
    d = request.json or {}
    stages_dict = {s["name"]: s for s in d.get("stages", [])}
    return jsonify(water_footprint(d.get('mass', 100), stages_dict))


@app.route('/api/byproduct-params', methods=['POST'])
def byproduct_params_api():
    d = request.json or {}
    return jsonify(byproduct_process_params(d.get('mass', 100)))


@app.route('/api/contaminants', methods=['POST'])
def contaminants_api():
    d = request.json or {}
    return jsonify({
        "GE": predict_ge_formation(d.get('temp', 245), d.get('time', 90)),
        "MCPD": predict_3mcpd_formation(d.get('temp', 245), d.get('time', 90)),
        "PAHs": predict_pahs_removal(d.get('earth', 1.2), d.get('carbon', 0.2)),
        "农药塑化剂": predict_pesticide_removal(d.get('degum', 'acid'), d.get('earth', 1.2), d.get('temp', 245)),
    })


@app.route('/api/calibrate', methods=['POST'])
def calibrate():
    """自动校准 - 输入工厂实测数据, 返回最优校准系数"""
    d = request.json or {}
    oil_type = OIL_MAP.get(d.get('oil', '大豆油'), OilType.SOYBEAN)
    plant_data = d.get('data', [])
    result = auto_calibrate(oil_type, plant_data)
    return jsonify(result)


@app.route('/api/compare-report', methods=['POST'])
def compare_report():
    """生成模型 vs 实测对比报告"""
    d = request.json or {}
    oil_type = OIL_MAP.get(d.get('oil', '大豆油'), OilType.SOYBEAN)
    plant_data = d.get('data', [])
    result = generate_comparison_report(oil_type, plant_data)
    return jsonify(result)


@app.route('/api/advanced/pareto', methods=['POST'])
def pareto():
    """帕累托多目标优化"""
    d = request.json or {}
    result = pareto_optimize(
        OIL_MAP.get(d.get('oil', '大豆油'), OilType.SOYBEAN),
        d.get('mass', 100), d.get('av', 2.0), d.get('p', 800),
        d.get('nhp', 0.15), d.get('obj', 'yield_vs_quality'), d.get('steps', 6)
    )
    return jsonify(result)


@app.route('/api/gb-check', methods=['POST'])
def gb_check():
    d = request.json or {}
    oil_name = d.get('oil', '大豆油')
    output = d.get('output', {})
    result = check_gb_compliance(oil_name, output)
    return jsonify(result)


@app.route('/api/byproducts', methods=['POST'])
def byproducts():
    d = request.json or {}
    stages_dict = {s["name"]: s for s in d.get("stages", [])}
    result = byproduct_deep_processing(d.get('mass', 100), stages_dict)
    return jsonify(result)


@app.route('/api/export/csv', methods=['POST'])
def export_csv():
    """导出模拟结果为CSV(Excel可打开)"""
    data = request.json
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(['工段', '参数', '数值'])
    for s in data.get('stages', []):
        for k, v in s.get('results', {}).items():
            w.writerow([s['name'], k, v])
    # Add summary
    o = data.get('output', {})
    w.writerow([])
    w.writerow(['汇总', '精炼得率', f"{o.get('yield_pct', 0)}%"])
    w.writerow(['汇总', '总油损', f"{o.get('total_loss_kg', 0)/1000:.1f} T"])
    w.writerow(['汇总', '成品酸价', o.get('product_av', '')])
    w.writerow(['汇总', '成品色泽', f"R{o.get('product_color_r','')}/Y{o.get('product_color_y','')}"])

    csv_data = output.getvalue()
    output.close()
    return Response(
        csv_data.encode('utf-8-sig'),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=refining_report.csv'}
    )


@app.errorhandler(500)
def handle_500(e):
    return jsonify({"error": "Internal server error", "detail": str(e)}), 500

@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(Exception)
def handle_all(e):
    return jsonify({"error": str(e), "type": type(e).__name__}), 500


if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
