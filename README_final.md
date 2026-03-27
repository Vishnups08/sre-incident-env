---
title: SRE Incident Env
sdk: docker
app_port: 7860
emoji: 🔥
colorFrom: red
colorTo: orange
pinned: false
---

# Model Card for Model ID

<!-- Provide a quick summary of what the model is/does. -->



## Model Details

### Model Description

<!-- Provide a longer summary of what this model is. -->



- **Developed by:** [More Information Needed]
- **Funded by [optional]:** [More Information Needed]
- **Shared by [optional]:** [More Information Needed]
- **Model type:** [More Information Needed]
- **Language(s) (NLP):** [More Information Needed]
- **License:** [More Information Needed]
- **Finetuned from model [optional]:** [More Information Needed]

### Model Sources [optional]

<!-- Provide the basic links for the model. -->

- **Repository:** [More Information Needed]
- **Paper [optional]:** [More Information Needed]
- **Demo [optional]:** [More Information Needed]

## Uses

<!-- Address questions around how the model is intended to be used, including the foreseeable users of the model and those affected by the model. -->

### Direct Use

<!-- This section is for the model use without fine-tuning or plugging into a larger ecosystem/app. -->

[More Information Needed]

### Downstream Use [optional]

<!-- This section is for the model use when fine-tuned for a task, or when plugged into a larger ecosystem/app -->

[More Information Needed]

### Out-of-Scope Use

<!-- This section addresses misuse, malicious use, and uses that the model will not work well for. -->

[More Information Needed]

## Bias, Risks, and Limitations

<!-- This section is meant to convey both technical and sociotechnical limitations. -->

[More Information Needed]

### Recommendations

<!-- This section is meant to convey recommendations with respect to the bias, risk, and technical limitations. -->

Users (both direct and downstream) should be made aware of the risks, biases and limitations of the model. More information needed for further recommendations.

## How to Get Started with the Model

Use the code below to get started with the model.

[More Information Needed]

## Training Details

### Training Data

<!-- This should link to a Dataset Card, perhaps with a short stub of information on what the training data is all about as well as documentation related to data pre-processing or additional filtering. -->

[More Information Needed]

### Training Procedure

<!-- This relates heavily to the Technical Specifications. Content here should link to that section when it is relevant to the training procedure. -->

#### Preprocessing [optional]

[More Information Needed]


#### Training Hyperparameters

- **Training regime:** [More Information Needed] <!--fp32, fp16 mixed precision, bf16 mixed precision, bf16 non-mixed precision, fp16 non-mixed precision, fp8 mixed precision -->

#### Speeds, Sizes, Times [optional]

<!-- This section provides information about throughput, start/end time, checkpoint size if relevant, etc. -->

[More Information Needed]

## Evaluation

<!-- This section describes the evaluation protocols and provides the results. -->

### Testing Data, Factors & Metrics

#### Testing Data

<!-- This should link to a Dataset Card if possible. -->

[More Information Needed]

#### Factors

<!-- These are the things the evaluation is disaggregating by, e.g., subpopulations or domains. -->

[More Information Needed]

#### Metrics

<!-- These are the evaluation metrics being used, ideally with a description of why. -->

[More Information Needed]

### Results

[More Information Needed]

#### Summary



## Model Examination [optional]

<!-- Relevant interpretability work for the model goes here -->

[More Information Needed]

## Environmental Impact

<!-- Total emissions (in grams of CO2eq) and additional considerations, such as electricity usage, go here. Edit the suggested text below accordingly -->

Carbon emissions can be estimated using the [Machine Learning Impact calculator](https://mlco2.github.io/impact#compute) presented in [Lacoste et al. (2019)](https://arxiv.org/abs/1910.09700).

- **Hardware Type:** [More Information Needed]
- **Hours used:** [More Information Needed]
- **Cloud Provider:** [More Information Needed]
- **Compute Region:** [More Information Needed]
- **Carbon Emitted:** [More Information Needed]

## Technical Specifications [optional]

### Model Architecture and Objective

[More Information Needed]

### Compute Infrastructure

[More Information Needed]

#### Hardware

[More Information Needed]

#### Software

[More Information Needed]

## Citation [optional]

<!-- If there is a paper or blog post introducing the model, the APA and Bibtex information for that should go in this section. -->

**BibTeX:**

[More Information Needed]

**APA:**

[More Information Needed]

## Glossary [optional]

<!-- If relevant, include terms and calculations in this section that can help readers understand the model or model card. -->

[More Information Needed]

## More Information [optional]

[More Information Needed]

## Model Card Authors [optional]

[More Information Needed]

## Model Card Contact

[More Information Needed]

# 🚨 SRE Incident Response Environment

An [OpenEnv](https://github.com/openenv)-compatible environment that simulates real-world production incident response. AI agents must diagnose, investigate, and resolve system incidents like a Site Reliability Engineer (SRE).

## 🎯 Why This Environment?

On-call incident response is one of the most critical and costly activities in software engineering:

- **$50B+ industry** around incident management (PagerDuty, Datadog, OpsGenie)
- Engineers spend **17+ hours/month** on incident response on average
- **Mean Time To Resolution (MTTR)** is a top KPI for every tech company
- Requires **multi-step reasoning**, hypothesis testing, and careful decision-making
- An AI agent that can handle incidents would save thousands of engineering hours

This environment provides a realistic training ground for AI agents to learn incident investigation and resolution skills.

## 🏗️ Environment Design

### Observation Space

| Field | Type | Description |
|---|---|---|
| `alerts` | `List[Alert]` | Production alerts that triggered the incident |
| `available_services` | `List[str]` | Services the agent can investigate |
| `logs` | `str \| None` | Service logs (populated after `check_logs`) |
| `metrics` | `Dict[str, ServiceMetrics] \| None` | CPU, memory, latency, error rate, etc. |
| `service_status` | `Dict[str, str] \| None` | Health check results for all services |
| `config` | `Dict \| None` | Service configuration |
| `diagnostic_result` | `str \| None` | Output of diagnostic commands |
| `action_history` | `List[Dict]` | All actions taken so far |
| `steps_taken` | `int` | Current step count |
| `steps_remaining` | `int` | Steps remaining before episode ends |
| `message` | `str` | Human-readable result of last action |

### Action Space

| Action | Description | When to Use |
|---|---|---|
| `check_logs` | View recent logs of a service | Investigating errors and events |
| `check_metrics` | View CPU/memory/latency/error_rate | Checking resource utilization |
| `check_status` | Health check all services | Getting overview of system state |
| `check_config` | View service configuration | Checking versions, settings |
| `restart_service` | Restart a service | When service is crashed/stuck |
| `rollback_deploy` | Rollback to previous version | When bad deployment detected |
| `scale_up` | Add more instances | When overloaded |
| `update_config` | Change configuration | Tuning parameters |
| `run_diagnostic` | Run diagnostic command | Deep investigation |
| `resolve` | Declare root cause + close | When you've identified and fixed |

### Reward Function

The reward function provides **rich partial credit signals**:

- **+0.05** for investigating relevant services
- **+0.02** for investigating affected (but not root cause) services  
- **-0.01** for investigating red herring services
- **+0.25** for applying the correct fix
- **+0.30** for correctly identifying the root cause
- **-0.10** for restarting healthy services (destructive unnecessary action)
- **-0.08** for destructive actions on wrong targets
- **Time efficiency bonus** for resolving quickly

This ensures agents get meaningful learning signal at every step, not just binary end-of-episode feedback.

## 📋 Tasks

### Task 1: Crashed After Deploy (Easy)
**Max Steps:** 10 | **Optimal Steps:** 3

> The payment-service was deployed 10 minutes ago and is now returning HTTP 500 errors at 78%. 

**What happened:** Bad deployment (v2.4.1) introduced a NullPointerException.
**Fix:** Rollback the deployment.
**Key signals:** Recent deployment in logs, NullPointerException stack traces.

### Task 2: Slow API Responses (Medium)  
**Max Steps:** 12 | **Optimal Steps:** 5

> Users reporting extremely slow page loads. API P99 latency at 8+ seconds. No recent deployments.

**What happened:** A massive analytics query was accidentally run on the production database, consuming all 200 connection pool slots.
**Fix:** Kill the long-running analytics query.
**Key signals:** Database CPU at 92%, connections at 200/200, analytics query visible in diagnostics.
**Red herrings:** Multiple services appear slow (they're all victims, not the cause).

### Task 3: Cascading Failure (Hard)
**Max Steps:** 15 | **Optimal Steps:** 8

> Multiple alerts firing: auth failures (65%), API timeouts (40%), notification queue backup (50K), cache eviction spike.

**What happened:** Memory leak in `user-session-service` → OOM crash → auth-service can't validate sessions → API retries → notification queue floods → cache hammered by retry storms.
**Fix:** Restart `user-session-service`.
**Key signals:** `user-session-service` is DOWN but has **no alert**. OOM killer in its logs. Auth logs show dependency failure.
**Red herrings:** cache-redis, notification-service, database, load-balancer all look suspicious but are symptoms.

## 🚀 Setup & Usage

### Docker (Recommended)
```bash
docker build -t sre-env .
docker run -p 7860:7860 sre-env
```

### Local Development
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## 🌐 Deployment to Hugging Face Spaces

This environment is fully prepared for Hugging Face Spaces.

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and click "Create new Space".
2. Set Space name (e.g., `sre-incident-env`).
3. Select **Docker** as the Space SDK and choose "Blank" template.
4. Set Space hardware to standard (CPU).
5. Add your `OPENAI_API_KEY` in the Space's Settings -> Variables and secrets (optional, for LLM baseline).
6. Push this repository to the Space using git:
   ```bash
   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/sre-incident-env
   git push hf main
   ```
7. Your environment will be live at `https://your-username-sre-incident-env.hf.space`!

## 🤖 Testing with an Agent

You can test your deployed environment using the provided baseline inference script:

```bash
# Test against your deployed space
python baseline/inference.py --task easy_crashed_deploy --server https://your-username-sre-incident-env.hf.space
```