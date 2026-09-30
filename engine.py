"""Telemetry contract enforcement and an actual OTLP -> Collector -> Prometheus test."""
from collections import defaultdict
import json
import math
from pathlib import Path
import tempfile
import time
from typing import Literal
from prometheus_client.parser import text_string_to_metric_families
from pydantic import BaseModel, Field, model_validator
import requests
import yaml
from labcore.runtime import AppleContainer


class Metric(BaseModel):
    name: str = Field(pattern=r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")
    kind: Literal["counter", "gauge"]
    owner: str = Field(min_length=1)
    allowedLabels: list[str]
    requiredLabels: list[str]
    maxSeries: int = Field(gt=0, le=10000)

    @model_validator(mode="after")
    def labels(self):
        if not set(self.requiredLabels) <= set(self.allowedLabels):
            raise ValueError("requiredLabels must be a subset of allowedLabels")
        return self


class Pipeline(BaseModel):
    cpus: int = Field(default=1,ge=1,le=8)
    memoryMb: int = Field(default=512,ge=256,le=8192)
    timeoutSeconds: int = Field(default=60,ge=5,le=180)
    batchTimeoutMs: int = Field(default=1000,ge=100,le=10000)
    scrapeIntervalSeconds: int = Field(default=1,ge=1,le=60)


def validate(exposition: str, contract: dict):
    metrics = [Metric.model_validate(m) for m in contract["metrics"]]
    if len({m.name for m in metrics}) != len(metrics):
        raise ValueError("Duplicate metric contract name")
    expected = {m.name: m for m in metrics}
    seen = defaultdict(set)
    findings = []
    samples = []
    families = list(text_string_to_metric_families(exposition))
    for family in families:
        for sample in family.samples:
            # Collector and Prometheus metadata series are outside this service's namespace.
            if (sample.name not in expected and not sample.name.startswith("lab_")) or sample.name.endswith("_created"):
                continue
            samples.append({"name": sample.name, "value": sample.value if math.isfinite(sample.value) else str(sample.value), **sample.labels})
            schema = expected.get(sample.name)
            if not schema:
                findings.append({"check":"unknown_metric", "metric":sample.name, "detail":"No declared contract"})
                continue
            identity = tuple(sorted(sample.labels.items()))
            if identity in seen[sample.name]:
                findings.append({"check":"duplicate_series", "metric":sample.name, "detail":str(identity)})
            seen[sample.name].add(identity)
            for check, values in [("unexpected_label", set(sample.labels)-set(schema.allowedLabels)),
                                  ("missing_label", set(schema.requiredLabels)-set(sample.labels))]:
                for value in sorted(values):
                    findings.append({"check":check,"metric":sample.name,"detail":value})
            if family.type != schema.kind:
                findings.append({"check":"wrong_type","metric":sample.name,"detail":f"Expected {schema.kind}, observed {family.type}"})
            if not math.isfinite(sample.value) or (schema.kind == "counter" and sample.value < 0):
                findings.append({"check":"invalid_value","metric":sample.name,"detail":str(sample.value)})
    for metric in metrics:
        count = len(seen[metric.name])
        if count == 0:
            findings.append({"check":"missing_metric","metric":metric.name,"detail":"Required metric absent"})
        if count > metric.maxSeries:
            findings.append({"check":"cardinality_budget","metric":metric.name,"detail":f"{count} > {metric.maxSeries}"})
    return {"passed": not findings, "findings": findings, "series": {m.name: len(seen[m.name]) for m in metrics},
            "samples": samples, "scope": "All declared contract metrics plus undeclared lab_* metrics; unrelated namespaces excluded", "contract": contract}


def fixture(case="healthy"):
    lines = ["# HELP lab_requests_total Number of requests", "# TYPE lab_requests_total counter"]
    for i in range(20 if case == "cardinality" else 2):
        extra = ',user_id="person-42"' if case == "unexpected_label" else ""
        lines.append(f'lab_requests_total{{route="/route/{i}",status="200"{extra}}} {100+i}')
    if case != "missing_metric":
        lines += ["# HELP lab_queue_depth Queue depth", "# TYPE lab_queue_depth gauge", 'lab_queue_depth{queue="default"} 3']
    return "\n".join(lines) + "\n"


def generate_configs(config=None):
    settings=Pipeline.model_validate(config or {})
    collector = {"receivers":{"otlp":{"protocols":{"http":{"endpoint":"0.0.0.0:4318"}}}},
                 "processors":{"batch":{"timeout":f"{settings.batchTimeoutMs}ms"}},
                 "exporters":{"prometheus":{"endpoint":"0.0.0.0:9464","resource_to_telemetry_conversion":{"enabled":False}}},
                 "service":{"pipelines":{"metrics":{"receivers":["otlp"],"processors":["batch"],"exporters":["prometheus"]}}}}
    return collector


def generate_rules(contract):
    rules=[]
    for raw in contract['metrics']:
        metric=Metric.model_validate(raw)
        rules.extend([
            {'alert':'Missing_'+metric.name,'expr':f'absent({metric.name})','for':'1m','labels':{'severity':'warning','owner':metric.owner}},
            {'alert':'Cardinality_'+metric.name,'expr':f'count({metric.name}) > {metric.maxSeries}','for':'1m','labels':{'severity':'warning','owner':metric.owner}},
        ])
    return {'groups':[{'name':'telemetry-contract','rules':rules}]}


def _ip(runtime, name):
    result = runtime.call(["inspect", name])
    if result.returncode:
        raise RuntimeError(result.stderr)
    data = json.loads(result.stdout)[0]
    # Current CLI represents each attachment with an IPv4 CIDR.
    for network in data.get("status", {}).get("networks", data.get("networks", [])):
        value = network.get("ipv4Address") or network.get("address")
        if value:
            return value.split("/")[0]
    raise RuntimeError("Runtime did not report a container IPv4 address")


def run_live(root: Path, config: dict, case: str):
    settings=Pipeline.model_validate(config)
    runtime = AppleContainer()
    names = [runtime.name("collector"), runtime.name("prometheus")]
    collector_image = "otel/opentelemetry-collector-contrib:0.120.0"
    prometheus_image = "prom/prometheus:v3.2.1"
    with tempfile.TemporaryDirectory(prefix="telemetry-gate-") as directory:
        temp = Path(directory)
        temp.chmod(0o755)
        (temp / "collector.yaml").write_text(yaml.safe_dump(generate_configs(config)))
        (temp / "rules.yaml").write_text(yaml.safe_dump(generate_rules(config)))
        try:
            result = runtime.call(["run", "-d", "--name", names[0], "--cpus", str(settings.cpus), "--memory", f"{settings.memoryMb}m",
                                   "--volume", f"{temp}:/config:ro", collector_image, "--config=/config/collector.yaml"], timeout=120)
            if result.returncode:
                raise RuntimeError(result.stderr)
            collector_ip = _ip(runtime, names[0])
            prom_config = {"global":{"scrape_interval":f"{settings.scrapeIntervalSeconds}s"}, "rule_files":["/config/rules.yaml"], "scrape_configs":[{"job_name":"gate", "static_configs":[{"targets":[f"{collector_ip}:9464"]}]}]}
            (temp / "prometheus.yaml").write_text(yaml.safe_dump(prom_config))
            result = runtime.call(["run", "-d", "--name", names[1], "--cpus", "1", "--memory", "512m",
                                   "--volume", f"{temp}:/config:ro", prometheus_image, "--config.file=/config/prometheus.yaml"], timeout=120)
            if result.returncode:
                raise RuntimeError(result.stderr)
            prometheus_ip = _ip(runtime, names[1])
            producer = runtime.run("python:3.12-slim", ["python", "/work/produce.py", f"http://{collector_ip}:4318/v1/metrics", case],
                                   mounts=[(root / "workloads", "/work", "ro")], network="default", timeout=90)
            if producer.returncode:
                raise RuntimeError(producer.stderr)
            session = requests.Session()
            session.trust_env = False
            exposition = ""
            query_data = None
            for _ in range(settings.timeoutSeconds*2):
                try:
                    response = session.get(f"http://{collector_ip}:9464/metrics", timeout=2)
                    response.raise_for_status()
                    exposition = response.text
                    response = session.get(f"http://{prometheus_ip}:9090/api/v1/query", params={"query":"lab_requests_total"}, timeout=2)
                    response.raise_for_status()
                    query_data = response.json()
                    if query_data.get("data", {}).get("result"):
                        break
                except requests.RequestException:
                    pass
                time.sleep(0.5)
            if not query_data or not query_data.get("data", {}).get("result"):
                raise RuntimeError("Prometheus did not ingest the producer's metric within the deadline")
            report = validate(exposition, config)
            report.update({"mode":"live Apple Container / real OTLP pipeline", "case":case,
                           "prometheus_query":query_data, "images":[collector_image,prometheus_image,"python:3.12-slim"]})
            return report
        finally:
            for name in reversed(names):
                runtime.cleanup(name)
