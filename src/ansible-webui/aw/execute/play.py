import traceback

from ansible_runner import RunnerConfig, Runner

from aw.config.main import config
from aw.model.job import Job, JobExecution, JobExecutionResult
from aw.execute.play_util import runner_cleanup, runner_prep, parse_run_result, failure, runner_logs, job_logs
from aw.execute.util import get_path_run, is_execution_status
from aw.utils.util import datetime_w_tz, is_null, timed_lru_cache  # get_ansible_versions
from aw.utils.handlers import AnsibleConfigError
from aw.utils.debug import log


class AwRunnerConfig(RunnerConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.quiet = True
        self.runner_mode = 'subprocess'
        self.project_dir = config['path_play']
        self.timeout = config['run_timeout']


def ansible_playbook(job: Job, execution: (JobExecution, None)):
    time_start = datetime_w_tz()
    path_run = get_path_run()
    if is_null(execution):
        execution = JobExecution(user=None, job=job, comment='Scheduled')

    result = JobExecutionResult(time_start=time_start)
    result.save()

    log_files = job_logs(job=job, execution=execution)
    execution.log_stdout = log_files['stdout']
    execution.log_stderr = log_files['stderr']

    @timed_lru_cache(seconds=1)  # check actual status every N seconds; lower DB queries
    def _cancel_job() -> bool:
        return is_execution_status(execution, 'Stopping')

    try:
        opts = runner_prep(job=job, execution=execution, path_run=path_run)
        execution.save()

        runner_cfg = AwRunnerConfig(**opts)
        runner_logs(cfg=runner_cfg, log_files=log_files)
        runner_cfg.prepare()
        command = ' '.join(runner_cfg.command)
        log(msg=f"Running job '{job.name}': '{command}'", level=5)
        execution.command = command
        execution.save()

        runner = Runner(config=runner_cfg, cancel_callback=_cancel_job)
        runner.run()

        parse_run_result(
            result=result,
            execution=execution,
            runner=runner,
        )
        del runner

        runner_cleanup(path_run)

    except (OSError, AnsibleConfigError) as err:
        tb = traceback.format_exc(limit=1024)
        failure(
            execution=execution, path_run=path_run, result=result,
            error_s=str(err), error_m=tb,
        )
        raise
