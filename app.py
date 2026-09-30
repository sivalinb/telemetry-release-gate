from pathlib import Path
import json
import pandas as pd
import streamlit as st
import yaml
from labcore.config import load_config
from labcore.observability import Recorder
from labcore.ui import header, evidence, sources_panel, ai_panel, docs_panel
from engine import fixture, validate, run_live, generate_configs, generate_rules

ROOT = Path(__file__).resolve().parent
config, meta = load_config(ROOT)
header("Telemetry Release Gate", "Turn metric contracts into measurable release decisions.", meta)

@st.cache_resource
def recorder():
    return Recorder(ROOT, "telemetry-release-gate")

tabs = st.tabs(["Release gate", "Generated config", "Evidence", "AI reviewer", "Public sources", "Guide"])
with tabs[0]:
    mode = st.radio("Execution mode", ["Fixture analysis", "Uploaded exposition", "Live Apple Container"], horizontal=True)
    case = st.selectbox("Scenario", ["healthy", "unexpected_label", "missing_metric", "cardinality"])
    uploaded = st.file_uploader("Prometheus exposition", type=["prom", "txt"]) if mode == "Uploaded exposition" else None
    with st.expander("Edit service contract"):
        contract_text = st.text_area("Metric contract JSON", json.dumps(config, indent=2), height=260)
    if st.button("Run release gate", type="primary"):
        try:
            contract = json.loads(contract_text)
            with recorder().span("release_gate", mode=mode, case=case):
                if mode == "Live Apple Container":
                    report = run_live(ROOT, contract, case)
                else:
                    if mode == "Uploaded exposition" and not uploaded:
                        raise ValueError("Upload an exposition file first")
                    text = uploaded.getvalue().decode() if uploaded else fixture(case)
                    report = {**validate(text, contract), "mode":"uploaded observation" if uploaded else "synthetic fixture", "case":case}
                report["config_provenance"] = meta
                recorder().save(report)
                st.session_state["report"] = report
        except Exception as e:
            st.error(f"Gate could not complete: {e}")
    if "report" in st.session_state:
        report = st.session_state["report"]
        a,b,c = st.columns(3)
        a.metric("Release decision", "PASS" if report["passed"] else "BLOCK")
        b.metric("Violations", len(report["findings"]))
        c.metric("Observed series", sum(report["series"].values()))
        st.caption(report["mode"])
        if report["findings"]:
            st.dataframe(pd.DataFrame(report["findings"]), hide_index=True)
        else:
            st.success("All declared service telemetry checks passed.")
        st.bar_chart(pd.DataFrame.from_dict(report["series"], orient="index", columns=["series"]))
with tabs[1]:
    st.code(yaml.safe_dump(generate_configs(config)), language="yaml")
    st.download_button("Download Collector config", yaml.safe_dump(generate_configs(config)), "collector.yaml")
    st.code(yaml.safe_dump(generate_rules(config)),language="yaml")
    st.download_button("Download Prometheus rules",yaml.safe_dump(generate_rules(config)),"rules.yaml")
    st.code((ROOT / "config/default.pkl").read_text(), language="text")
with tabs[2]:
    evidence(st.session_state.get("report"))
with tabs[3]:
    ai_panel(ROOT, st.session_state.get("report"))
with tabs[4]:
    sources_panel(ROOT)
with tabs[5]:
    docs_panel(ROOT)
