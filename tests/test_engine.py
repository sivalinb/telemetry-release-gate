import copy
from pathlib import Path
import pytest
from labcore.config import load_config
from engine import validate,fixture

@pytest.fixture
def config(): return load_config(Path(__file__).resolve().parents[1])[0]

def test_healthy_fixture_has_three_series(config):
    result=validate(fixture(),config)
    assert result['passed']
    assert result['series']=={'lab_requests_total':2,'lab_queue_depth':1}

@pytest.mark.parametrize('case,check',[('cardinality','cardinality_budget'),('unexpected_label','unexpected_label'),('missing_metric','missing_metric')])
def test_bad_telemetry_rejected(config,case,check):
    result=validate(fixture(case),config)
    assert not result['passed']
    assert check in {f['check'] for f in result['findings']}

def test_wrong_metric_type(config):
    text=fixture().replace('lab_requests_total counter','lab_requests_total gauge')
    assert 'wrong_type' in {f['check'] for f in validate(text,config)['findings']}

def test_nonfinite_counter_rejected(config):
    import json
    text=fixture().replace(' 100\n',' NaN\n')
    report=validate(text,config)
    assert 'invalid_value' in {f['check'] for f in report['findings']}
    json.dumps(report,allow_nan=False)

def test_duplicate_samples_not_hidden_by_set(config):
    text=fixture()+'lab_requests_total{route="/route/0",status="200"} 101\n'
    assert 'duplicate_series' in {f['check'] for f in validate(text,config)['findings']}

def test_unknown_service_metric_rejected(config):
    text=fixture()+'# TYPE lab_unowned gauge\nlab_unowned 1\n'
    assert 'unknown_metric' in {f['check'] for f in validate(text,config)['findings']}

def test_contract_rejects_impossible_required_labels(config):
    config['metrics'][0]['requiredLabels'].append('undeclared')
    with pytest.raises(ValueError): validate(fixture(),config)

def test_duplicate_contract_name(config):
    config['metrics'].append(copy.deepcopy(config['metrics'][0]))
    with pytest.raises(ValueError,match='Duplicate'): validate(fixture(),config)

def test_explicit_contract_outside_default_namespace(config):
    config['metrics'][0]['name']='http_requests_total'
    r=validate(fixture().replace('lab_requests_total','http_requests_total'),config)
    assert r['passed']

def test_generated_rules_follow_contract(config):
    from engine import generate_rules,generate_configs
    config['metrics'][0]['maxSeries']=12
    rules=generate_rules(config)['groups'][0]['rules']
    assert any(r['expr']=='count(lab_requests_total) > 12' for r in rules)
    assert generate_configs(dict(config,batchTimeoutMs=200))['processors']['batch']['timeout']=='200ms'
