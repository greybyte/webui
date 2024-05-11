.. _usage_alerts:

.. include:: ../_include/head.rst

.. include:: ../_include/warn_develop.rst


======
Alerts
======

You can use the UI at :code:`Settings - Alerts` to create alerting rules for your jobs.

Options are:

* **User** specific rule - only you are notified

* **Group** rules - all members of a specific group are notified (*if they have the privilege to view the job*)

* **Global** rules - all users are notified (*if they have the privilege to view the job*)

----

Media
*****

There are currently two types of alerts.

E-Mail and plugins.

----

E-Mail
======

You need to configure your mailserver at the :code:`System - Config` page.

After that you can receive e-mails on job finish/failure.

----

Plugins
=======

There is a generic alert-plugin interface for custom solutions.

**Usage**:

* Create a script that can be called by AW

   It will receive a file-path as system-argument 1 that points to a JSON file containing data you might want to use.

    Example JSON:

    .. code-block:: json

        {
          "alert": {
            "type": "user",
            "condition": "always"
          },
          "user": {
            "name": "ansible",
            "first_name": "",
            "last_name": "",
            "email": "ansible@localhost",
            "phone": "",
            "description": "",
            "is_active": true,
            "last_login": 1715445321,
            "groups": []
          },
          "execution": {
            "failed": false,
            "status": "Finished",
            "job_name": "test2",
            "user_name": "ansible",
            "time_start": 1715450650,
            "time_start_pretty": "2024-05-11 18:04:10 CEST",
            "time_fin": 1715450651,
            "time_fin_pretty": "2024-05-11 18:04:11 CEST",
            "error_short": null,
            "error_med": null,
            "log_stdout": "/home/guy/.local/share/ansible-webui/test2_2024-05-11_18-04-10_ansible_stdout.log",
            "log_stdout_url": "http://localhost:8000/api/job/1/17/log?type=stdout",
            "log_stderr": null,
            "log_stderr_url": null,
            "log_stdout_repo": null,
            "log_stdout_repo_url": null,
            "log_stderr_repo": null,
            "log_stderr_repo_url": null
          },
          "stats": {}
        }

* Create a plugin at :code:`Settings - Alerts` that points to your executable

* Link the plugin in alerts

* Test it
