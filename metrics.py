"""Generate assignment CSV and VRR/FAR from real frozen Vul4Py evidence."""
import csv, json, os
from pathlib import Path
from vul4py_adapter import normalize_eval

ROOT=Path(__file__).resolve().parent
LOCAL_RUNS=ROOT/"vul4py"/"runs"/"student"
SUBMITTED_RUNS=ROOT/"results"/"vul4py_runs"
RESULTS=ROOT/"results"
FIELDS="student_id case_id model timestamp llm_claimed_success llm_confidence patch_applied security_test_pass functional_test_pass verified_repair false_assurance latency_ms input_tokens output_tokens semgrep_findings_before semgrep_findings_after api_success error_type".split()

def calculate(rows):
    total=len(rows); verified=sum(bool(r["verified_repair"]) for r in rows); claims=sum(bool(r["llm_claimed_success"]) for r in rows); false=sum(bool(r["false_assurance"]) for r in rows)
    return {"cases_completed":total,"positive_claims":claims,"verified_repairs":verified,"false_assurances":false,"VRR":None if not total else verified/total,"FAR":None if not claims else false/claims}

def main():
    rows=[]
    runs=LOCAL_RUNS if LOCAL_RUNS.exists() else SUBMITTED_RUNS
    for run in sorted(runs.iterdir()) if runs.exists() else []:
        if not run.is_dir(): continue
        response, evaluation=run/"llm_response.json",run/"eval.json"
        if not response.exists() or not evaluation.exists(): continue
        llm=json.loads(response.read_text()); ev=normalize_eval(evaluation); complete=all(ev[k] is not None for k in ("patch_applied","functional_test_pass","security_test_pass")); verified=complete and all(ev[k] for k in ("patch_applied","functional_test_pass","security_test_pass")); claim=llm.get("claimed_success")
        rows.append({"student_id":os.getenv("STUDENT_ID",""),"case_id":run.name,"model":llm.get("model",""),"timestamp":llm.get("timestamp",""),"llm_claimed_success":claim,"llm_confidence":llm.get("confidence",""),"patch_applied":ev["patch_applied"],"security_test_pass":ev["security_test_pass"],"functional_test_pass":ev["functional_test_pass"],"verified_repair":verified,"false_assurance":bool(claim) and not verified,"latency_ms":llm.get("latency_ms",""),"input_tokens":llm.get("input_tokens",""),"output_tokens":llm.get("output_tokens",""),"semgrep_findings_before":"","semgrep_findings_after":"","api_success":llm.get("api_success",False),"error_type":llm.get("error_type","")})
    RESULTS.mkdir(exist_ok=True)
    with (RESULTS/"results.csv").open("w",newline="",encoding="utf-8") as f: w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator="\n");w.writeheader();w.writerows(rows)
    summary=calculate(rows); (RESULTS/"summary.json").write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))
if __name__=="__main__": main()
