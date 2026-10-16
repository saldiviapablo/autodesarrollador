"""Observer regression only: no model, GUI, approval or real Runner start."""
import importlib.util,json,pathlib,subprocess,unittest
from unittest.mock import patch

R=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('observer',R/'tests/observe-launcher-manual-smoke.py')
observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)

def info(remaining=2700,plan=None):
    return {'remaining_seconds':remaining,'admission':{'plan':{'phase_timeout_seconds':300} if plan is None else plan}}

class Observer(unittest.TestCase):
    def test_full_phase_and_model_start_allowed(self):
        self.assertGreaterEqual(observer.smoke_window(info(),180),480)
    def test_remaining_clock_never_extended(self):
        self.assertEqual(observer.smoke_window(info(45),180),45)
    def test_finite_window_below_global(self):
        self.assertLess(observer.smoke_window(info(),180),2700)
    def test_expired_clock_not_revived(self):
        self.assertEqual(observer.smoke_window(info(-1),180),0)
    def test_default_phase_supported(self):
        self.assertGreaterEqual(observer.smoke_window(info(plan={}),180),360)
    def test_historical_start_not_reused(self):
        self.assertEqual(observer.new_run_events([{'seq':1,'type':'RUN_STARTED'},{'seq':2,'type':'PROCESS_EXITED'}],2),[])
    def test_only_continuation_events_evaluated(self):
        events=[{'seq':1,'type':'RUN_STARTED'},{'seq':2,'type':'PROCESS_EXITED'},{'seq':3,'type':'RUN_RECOVERED_FROM_DISK'},{'seq':4,'type':'RUN_STARTED'},{'seq':5,'type':'PROCESS_STARTED'}]
        self.assertEqual([x['seq'] for x in observer.new_run_events(events,2)],[4,5])
    def test_recovery_alone_is_not_start(self):
        self.assertEqual(observer.new_run_events([{'seq':3,'type':'RUN_RECOVERED_FROM_DISK'}],2),[])
    def test_utf8_cim_preserves_unicode(self):
        rows=[{'ProcessId':123,'ParentProcessId':12,'CommandLine':'á ñ € ° 中文'}]
        raw=subprocess.CompletedProcess([],0,json.dumps(rows,ensure_ascii=False).encode('utf-8'),b'')
        with patch.object(observer.subprocess,'run',return_value=raw) as call:
            self.assertEqual(observer.cim_process_rows(),rows)
            self.assertIn('[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)',call.call_args.args[0][-1])
    def test_cim_failure_is_not_empty_success(self):
        with patch.object(observer.subprocess,'run',return_value=subprocess.CompletedProcess([],1,b'',b'failure')):
            with self.assertRaisesRegex(ValueError,'CIM_PROCESS_SNAPSHOT_FAILED'):observer.cim_process_rows()
    def test_error_requests_only_owned_stop(self):
        with patch.object(observer.data,'read',return_value={'run_id':'same','status':'RUNNING'}),patch.object(observer.ui,'active_stop',return_value={'status':'STOP_REQUESTED'}) as stop:
            self.assertEqual(observer.stop_on_observer_error(R/'sandbox/fixture','same')['status'],'STOP_REQUESTED')
            stop.assert_called_once_with(R/'sandbox/fixture')
    def test_foreign_run_never_stopped(self):
        with patch.object(observer.data,'read',return_value={'run_id':'different','status':'RUNNING'}),patch.object(observer.ui,'active_stop') as stop:
            with self.assertRaisesRegex(ValueError,'FOREIGN_RUN_PRESERVED'):observer.stop_on_observer_error(R/'sandbox/fixture','same')
            stop.assert_not_called()
    def test_terminal_run_never_stopped_again(self):
        with patch.object(observer.data,'read',return_value={'run_id':'same','status':'ABORTED'}),patch.object(observer.ui,'active_stop') as stop:
            self.assertEqual(observer.stop_on_observer_error(R/'sandbox/fixture','same')['status'],'ALREADY_TERMINAL')
            stop.assert_not_called()

if __name__=='__main__':unittest.main(verbosity=2)
