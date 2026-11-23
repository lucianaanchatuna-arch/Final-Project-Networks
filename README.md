# Measuring False Assurance in LLM-Based Automated Vulnerability Repair

This individual Networks project studies whether a Large Language Model's claim that it repaired vulnerable software is supported by independent testing. The experiment uses real Python cases from Vul4Py, OpenAI's Responses API, and Vul4Py's evaluator.

## Research questions

1. How frequently do LLMs provide false assurance while repairing real vulnerabilities?
2. How effectively can they preserve functionality while blocking the exploit?

## Architecture and data flow

```text
Vul4Py scan-OK vulnerable source
        -> repair.py -> OpenAI Responses API
        -> frozen llm_response.json + patch.diff
        -> official Vul4Py evaluator -> eval.json / eval.log
        -> Semgrep (secondary measurement)
        -> metrics.py -> results.csv + summary.json
```

The model sees only selected source from `workspaces/<case>/vulnerable/`. The `fixed/` tree and all test/evaluation results are withheld. Each case has one repair request per run. The response and patch are saved before evaluation and are not revised afterward.

## Repository layout

```text
Final-Project-Networks/
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── repair.py
├── evaluator.py
├── vul4py_adapter.py
├── metrics.py
├── run_pipeline.py
├── results/
│   ├── results.csv
│   └── summary.json
└── vul4py/                  # external Vul4Py checkout, ignored by Git
    ├── scripts/
    ├── dataset/
    ├── workspaces/           # local benchmark source and generated environments; ignored
    └── runs/student/         # local experiment workspace
```

The official Vul4Py implementation remains an external tool. Do not commit its workspaces, virtual environments, tool caches, or credentials. The five compact evaluation records submitted with the project are copied to `results/vul4py_runs/`; they include the saved response, patch, evaluator output, and freeze hash for each case.

## Installation

On Ubuntu / AWS EC2:

```bash
git clone https://github.com/lucianaanchatuna-arch/Final-Project-Networks.git
cd Final-Project-Networks
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
pip install semgrep pytest
git clone https://github.com/tabudz/vul4py.git vul4py
```

Prepare and validate Vul4Py cases (preparation may skip already prepared workspaces):

```bash
cd vul4py
python3 scripts/prepare.py --jobs 2
python3 scripts/vul4py.py --workspace-root workspaces scan --jobs 2
cd ..
```

Only cases with `OK` in `vul4py/workspaces/scan_report.tsv` are eligible.

## Configure and run the experiment

Set credentials in the EC2 shell, never in source code or Git:

```bash
export OPENAI_API_KEY='your-new-key'
export OPENAI_MODEL='gpt-6-luna'
export STUDENT_ID='your-course-identifier'
```

List eligible cases without making an API call:

```bash
python repair.py --list-cases
```

Make one repair attempt for each of the first five scan-OK cases:

```bash
python repair.py --cases 5
```

For one selected eligible case:

```bash
python repair.py --case-id CVE-YYYY-NNNN
```

Responses and patches are stored locally under `vul4py/runs/student/<CASE_ID>/`. The submission copies are under `results/vul4py_runs/<CASE_ID>/`. Existing responses are frozen; do not retry a case after seeing its evaluator output.

Evaluate each frozen patch with the official evaluator:

```bash
python evaluator.py --case-id CVE-YYYY-NNNN
```

The evaluator uses Vul4Py's real fields: `apply_ok`, `functional_rc`, `exploit_rc`, and `plausible`. The adapter normalizes these to `patch_applied`, `functional_test_pass`, and `security_test_pass`.

Run metrics after evaluation:

```bash
python metrics.py
```

This writes `results/results.csv` and `results/summary.json`.

## Metrics

For case *i*:

```text
verified_repair = patch_applied AND functional_test_pass AND security_test_pass
false_assurance = llm_claimed_success AND NOT verified_repair
VRR = verified repairs / eligible completed cases
FAR = false assurances / positive LLM success claims
```

If there are no positive claims, FAR is undefined, not zero. A patch application alone is not a verified repair.

## Current experimental result

The first five scan-OK cases were evaluated on EC2. The observed results were:

| Measure | Result |
|---|---:|
| Evaluated cases | 5 |
| Positive LLM claims | 5 |
| Verified repairs | 1 |
| False assurances | 4 |
| VRR | 20% |
| FAR | 80% |

These values come from the reported Vul4Py evaluations. Semgrep counts are currently unavailable and remain blank in the CSV; they are secondary and do not determine repair verification.

## Semgrep (secondary analysis)

Run Semgrep on the vulnerable source and on the exact candidate directory created by Vul4Py, if it is available:

```bash
semgrep --config=auto --json vul4py/workspaces/<CASE_ID>/vulnerable > semgrep_before.json
semgrep --config=auto --json vul4py/workspaces/<CASE_ID>/student_candidate > semgrep_after.json
```

Record finding counts in the corresponding results row. Zero findings do not prove the vulnerability is fixed. Do not send Semgrep output to the model.

## Computer networks explanation

The client resolves `api.openai.com` with DNS, establishes a reliable TCP connection, negotiates TLS encryption, then exchanges JSON over HTTPS, normally on port 443. HTTP status codes communicate request outcomes: 401 indicates an authentication problem, 429 indicates rate limiting, and 5xx generally indicates a server-side failure. Timeouts can occur when a response does not arrive in time. Wireshark can show packet and connection metadata, but TLS normally encrypts the HTTP payload. `latency_ms` is end-to-end API latency, including networking, service processing, model inference, and response transfer; it is not pure network delay.

EC2 connectivity checks:

```bash
ping -c 4 8.8.8.8
getent hosts api.openai.com
nslookup api.openai.com
```

## Security and reproducibility

- Never commit API keys, `.env` files, SSH keys, or credentials.
- Keep Vul4Py workspaces, runs, environments, and caches out of Git unless selectively packaging required results for submission.
- Preserve each response and patch before evaluation; do not edit or regenerate a failed patch after seeing results.
- Keep meaningful Git commits. Do not fabricate or backdate history.

## Limitations

This MVP evaluates five Vul4Py cases in one model run. Semgrep results remain pending. Vul4Py setup and dependency environments can require substantial disk space and time. The evaluation demonstrates the benchmark workflow and is not a claim about all vulnerabilities or models.
