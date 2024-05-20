ELEM_ID_TMPL_ROW2 = 'aw-api-data-tmpl-row2';
ELEM_ID_TMPL_FIELD_TEXT = 'aw-api-data-tmpl-exec-text';
ELEM_ID_TMPL_FIELD_BOOL = 'aw-api-data-tmpl-exec-bool';
ELEM_ID_TMPL_FIELD_VERB = 'aw-api-data-tmpl-exec-verbosity';
EXEC_BOOL_FIELDS = ['mode_check', 'mode_diff'];

function buildExecutionFields(data, required = false) {
    let prompts = [];

    if (is_set(data)) {
        let promptsRequired = data.split(',');
        for (field of promptsRequired) {
            let tmplElem = ELEM_ID_TMPL_FIELD_TEXT;
            if (EXEC_BOOL_FIELDS.includes(field)) {
                tmplElem = ELEM_ID_TMPL_FIELD_BOOL;
            } else if (field == 'verbosity') {
                tmplElem = ELEM_ID_TMPL_FIELD_VERB;
            }

            let fieldHtml = document.getElementById(tmplElem).innerHTML;
            let prettyName = capitalizeFirstLetter(field);
            prettyName = prettyName.replaceAll('_', ' ');

            if (required) {
                fieldHtml = fieldHtml.replaceAll('${attrs}', 'required');
            }
            if (field.includes('var=')) {
                let varName = field.split('=')[1];
                if (field.includes('#')) {
                    [varName, prettyName] = varName.split('#');
                }
                fieldHtml = fieldHtml.replaceAll('${FIELD}', 'var=' + varName);

            } else {
                fieldHtml = fieldHtml.replaceAll('${FIELD}', field);
            }
            fieldHtml = fieldHtml.replaceAll('${PRETTY}', prettyName);
            prompts.push(fieldHtml);
        }
    }

    return prompts;
}

function updateApiTableDataJob(row, row2, entry) {
    // job
    row.innerHTML = document.getElementById(ELEM_ID_TMPL_ROW).innerHTML;
    row.cells[0].innerText = entry.name;
    row.cells[1].innerText = entry.inventory_file;
    row.cells[2].innerText = entry.playbook_file;

    if (entry.comment == "") {
        row.cells[3].innerText = '-';
    } else {
        row.cells[3].innerText = entry.comment;
    }
    if (entry.schedule == "") {
        row.cells[4].innerText = '-';
    } else {
        let scheduleHtml = entry.schedule;
        if (!entry.enabled) {
            scheduleHtml += '<br><i>(disabled)</i>';
        }
        row.cells[4].innerHTML = scheduleHtml;
    }

    if (entry.executions.length == 0) {
        var lastExecution = null;
        row.cells[5].innerText = '-';
        row.cells[6].innerText = '-';
    } else {
        var lastExecution = entry.executions[0];
        row.cells[5].innerHTML = shortExecutionStatus(lastExecution);

        if (entry.next_run == null) {
            row.cells[6].innerText = '-';
        } else {
            row.cells[6].innerText = entry.next_run;
        }
    }

    let actionsTemplate = document.getElementById(ELEM_ID_TMPL_ACTIONS).innerHTML;
    actionsTemplate = actionsTemplate.replaceAll('${ID}', entry.id);
    if (lastExecution != null) {
        actionsTemplate = actionsTemplate.replaceAll('${EXEC_ID_1}', lastExecution.id);
    } else {
        actionsTemplate = actionsTemplate.replaceAll('${EXEC_ID_1}', 0);
    }
    row.cells[7].innerHTML = actionsTemplate;

    // custom execution
    row2.setAttribute("id", "aw-spoiler-" + entry.id);
    row2.setAttribute("hidden", "hidden");
    let execTemplate = document.getElementById(ELEM_ID_TMPL_ROW2).innerHTML;
    execTemplate = execTemplate.replaceAll('${ID}', entry.id);
    row2.innerHTML = execTemplate;
    let prompts = buildExecutionFields(entry.execution_prompts_required, true);
    prompts.push(...buildExecutionFields(entry.execution_prompts_optional));

    console.log(prompts);

    let execForm = document.getElementById('aw-job-exec-' + entry.id);
    execForm.innerHTML = prompts.join('<br>') + execForm.innerHTML;
    execForm.addEventListener('submit', function(e) {
        e.preventDefault();
        customExecution(this.elements);
    })
}

function customExecution(formElements) {
    let data = {};
    let cmdArgs = '';
    let job_id = undefined;
    for (elem of formElements) {
        if (elem.hasAttribute('name')) {
            if (elem.name == 'job_id') {
                job_id = elem.value;
            } else if (elem.name.startsWith('var')) {
                let varName = elem.name.split('=')[1];
                cmdArgs += ' -e "' + varName + '=' + elem.value + '"';
            } else {
                data[elem.name] = elem.value;
            }
        }
    }
    if ('cmd_args' in data) {
        cmdArgs += data['cmd_args'];
    }
    data['cmd_args'] = cmdArgs;

    $.ajax({
        type: "post",
        url: "/api/job/" + job_id,
        data: data,
        success: function (result) { apiActionSuccess(result); },
        error: function (result, exception) { apiActionError(result, exception); },
    });

}

$( document ).ready(function() {
    apiEndpoint = "/api/job?executions=true&execution_count=1";
    fetchApiTableData(apiEndpoint, updateApiTableDataJob, true);
    setInterval('fetchApiTableData(apiEndpoint, updateApiTableDataJob, true)', (DATA_REFRESH_SEC * 1000));
});
