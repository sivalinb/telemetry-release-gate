from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from labcore.config import load_config
from labcore.observability import Recorder
config,meta=load_config(ROOT)
parser=argparse.ArgumentParser()
parser.add_argument('--live',action='store_true')
recorder=Recorder(ROOT,ROOT.name)
with recorder.span('cli_run'):
    from engine import fixture,validate,run_live
    parser.add_argument('--case',default='healthy',choices=['healthy','unexpected_label','missing_metric','cardinality'])
    args=parser.parse_args()
    report=run_live(ROOT,config,args.case) if args.live else dict(validate(fixture(args.case),config),mode='synthetic fixture')
report['config_provenance']=meta
recorder.save(report)
(ROOT/'artifacts/cli-latest.json').write_text(json.dumps(report,indent=2,allow_nan=False))
print(json.dumps(report,indent=2,allow_nan=False))
if report.get('passed') is False: raise SystemExit(1)
