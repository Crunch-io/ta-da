About adminreport
-------------------

AdminReport is a script meant to report content from the CrunchAdmin.

You can point it to any admin page and keyword returned by that page and
it will send a message to slack with a link to the admin page and the count
of entries reported.

for example to report the first 10 entries out of ``/dataset_integrity`` admin page
previewing the ``dataset_id`` and ``status`` keys of those we could use::

    adminreport /dataset_integrity broken --env=alpha -k dataset_id -k status --top=10

The output would be::

    AUTOMATIC REPORT OF https://alpha.superadmin.crint.net/dataset_integrity
    3 entries currently in broken

    dataset_id=bb9f768cb5eb469d8d980c4543b9c4df status=Corrupt
    dataset_id=7b739f3dd2bb40598fc2fd075247b34b status=Corrupt
    dataset_id=7225d8fc96c54029baf1e7bca17a83af status=Corrupt

Output can be sent to a slack channel by passing ``--slack=CHANNEL`` option.

See ``--help`` for further usage info::

    Report content of a Crunch Admin Page.

    Usage:
      /Users/amol/wrk/crunch/venv/bin/adminreport <urlpath> <contentkey> [--env=ENV] [--slack=CHANNEL] [--top=TOPCOUNT] [--key=KEY]...
      /Users/amol/wrk/crunch/venv/bin/adminreport (-h | --help)

    Arguments:
      urlpath                The admin page for which the report has to be sent.
      contentkey             The admin page response key to report.

    Options:
      -h --help              Show this screen
      --env=ENV              Environment against which to run the commands [default: eu]
      --slack=CHANNEL        Send messages to slack CHANNEL instead of writing it to stdout
      --top=TOPCOUNT         Number of entries to preview from the content [default: 10]
      -k=KEY --key=KEY       One ore more keys to report out of contentkey in preview.
