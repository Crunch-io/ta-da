from __future__ import print_function
import argparse
import csv
import subprocess

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import requests
import webbrowser
from paramiko.client import SSHClient, WarningPolicy


class tunnel(object):
    JUMP_HOSTS = {
        "alpha": "ec2-user@jump.eu.crint.net",
        "eu": "ec2-user@jump.eu.crint.net",
        "unstable": "ubuntu@c3po.aws.crunch.io",
        "stable": "ubuntu@c3po.aws.crunch.io",
    }

    def __init__(self, target, target_port, local_port, killonexit=True):
        self.target = target
        self.target_port = target_port
        self.local_port = local_port
        self.killonexit = killonexit

    def __enter__(self):
        if not self.killonexit:
            # There might be a previous instance running, quit it.
            self._kill_running()
        hostgroup = self.target.split("-", 1)[0]
        jumphost = self.JUMP_HOSTS[hostgroup]
        subprocess.call(
            "ssh -A -f -N -L %s:%s:%s %s"
            % (self.local_port, self.target, self.target_port, jumphost),
            shell=True,
        )
        return ("127.0.0.1", self.local_port)

    def __exit__(self, *args, **kwargs):
        if self.killonexit:
            self._kill_running()

    def _kill_running(self):
        """Kills currently running portforwarding"""
        subprocess.call('pkill -f "ssh -A -f -N -L %s"' % self.local_port, shell=True)


def gather_servers(kind="eu", role="dbservers"):
    req = requests.get(
        "http://dev.crunch.io/ec2-hosts.txt", auth=("paster", "youseeit")
    )
    servers = []
    for server in csv.DictReader(StringIO(req.text), delimiter="\t"):
        if kind != server["System"]:
            continue
        if role not in server["Ansible Role"]:
            continue
        if server["State"] != "running":
            continue
        servers.append(server["Name"])
    return servers


def gather_tags(kind="eu"):
    req = requests.get(
        "http://dev.crunch.io/ec2-hosts.txt", auth=("paster", "youseeit")
    )
    tags = set()
    for server in csv.DictReader(StringIO(req.text), delimiter="\t"):
        for role in server["Ansible Role"].split(","):
            tags.add(role.strip())
    return tags


def open_admin(kind="eu"):
    admin_servers = gather_servers(kind=kind, role="webservers")
    if not admin_servers:
        raise ValueError("Unable to identify a valid webserver.")

def set_user(args):
    if args.USER is None:
        if args.ROLE in ("db", "dbservers") and args.environment == "eu":
            args.USER = "centos"
        else:
            args.USER = "ec2-user"


def main():
    parser = argparse.ArgumentParser(description="List or connect to Crunch Hosts")
    parser.add_argument(
        "-e",
        "--environment",
        default="eu",
        help="For which environment to act (alpha, eu, ...)",
    )

    subparsers = parser.add_subparsers(
        title="subcommands",
        description="valid subcommands",
        help="additional help",
        dest="subcommand",
    )

    tagsparser = subparsers.add_parser("tags")

    listparser = subparsers.add_parser("list")
    listparser.add_argument(
        "ROLE",
        help="List existing hosts for given ROLE " "(dbservers, webservers, ...)",
    )

    tunnelparser = subparsers.add_parser("connect")
    tunnelparser.add_argument(
        "ROLE", help="Work on hosts for given ROLE " "(dbservers, webservers, ...)"
    )
    tunnelparser.add_argument(
        "INDEX",
        help="Tunnel to the given server "
        "as listed by list subcommand "
        "(or to server matching a predicate "
        "in the form namespace:name. IE: mongodb:primary)",
    )
    tunnelparser.add_argument(
        "-i", dest="IDENTITY", help="Which SSH key to use (IE: ~/.ssh/id_rsa)"
    )
    tunnelparser.add_argument(
        "-p",
        "--port",
        dest="PORT",
        default="2222",
        help="Tunnel to the given local port",
    )
    tunnelparser.add_argument(
        "-u",
        "--user",
        dest="USER",
        default=None,
        help="User that should be used to connect " "to the remote host.",
    )

    adminparser = subparsers.add_parser("admin")
    adminparser.add_argument(
        "-p",
        "--port",
        dest="PORT",
        default="28081",
        help="Tunnel to the given local port",
    )

    args = parser.parse_args()
    if args.subcommand == "tags":
        tags = gather_tags(args.environment)
        for tag in tags:
            print("\t", tag)
    elif args.subcommand == "list":
        servers = gather_servers(args.environment, args.ROLE)
        for idx, s in enumerate(servers):
            print("\t", idx, s)
    elif args.subcommand == "connect":
        set_user(args)
        servers = gather_servers(args.environment, args.ROLE)
        try:
            server_index = int(args.INDEX)
        except ValueError:
            # User requested a predicate
            server = HostPropertyDetector(args).detect(servers, args.INDEX)
            if server is None:
                print("No server matched predicate")
                return
        else:
            # User requested a specific index
            try:
                server = servers[server_index]
            except IndexError:
                print("Invalid Server, valid indexes are:")
                for idx, s in enumerate(servers):
                    print("\t", idx, s)
                return

        print("> Connecting to", server)
        with tunnel(server, 22, args.PORT) as dest:
            command = (
                "ssh"
                " -o UserKnownHostsFile=/dev/null"
                " -o StrictHostKeyChecking=no"
                " -p {}"
                " {}@{}".format(dest[1], args.USER, dest[0])
            )
            if args.IDENTITY:
                command += " -i {}".format(args.IDENTITY)
            print(command)
            subprocess.call(command, shell=True)
    elif args.subcommand == "admin":
        admin_servers = gather_servers(kind=args.environment, role="webservers")
        if not admin_servers:
            print("Unable to identify a webserver.")
            return
        server = admin_servers[0]
        print("Connecting to", server)
        with tunnel(server, 8081, args.PORT, killonexit=False) as dest:
            webbrowser.open("http://{}:{}/".format(*dest))


class HostPropertyDetector(object):
    """Detects properties of an host you are trying to connect to.

    The ``connect`` command allows connecting to a host that has
    a specific property instead of connecting to a given index.

    That is supported by this property detector that checks the host
    properties.

    Each method implemented in this class is a predicate that
    returns ``False`` or ``True`` to verify if the host has
    that property or not.

    All methods accept a ``dest`` argument, which is the pair (address, port)
    you should connect to to reach the host (after tunneling is already in place)
    and a ``user`` argument, which is the user you must use to connect.
    Methods also receive a ``command`` argument, which is the ssh command
    that must be executed to connect to that host. You can append to this
    command to execute scripts on the remote host.
    """

    PARAMETRIC_PREDICATES = {
        "zz9dataset": lambda arg: HostPropertyDetector._DetectHotZZ9Dataset(arg)
    }

    def __init__(self, args):
        set_user(args)
        self._args = args

    def detect(self, servers, predicate):
        """Detect a server out of the provided that matches predicate.

        Predicates are provided in the form ``namespace:name`` and
        are verified by ``_namespace_name`` method of this object
        or by looking them up in ``PARAMETRIC_PREDICATES``.
        In case of parametric ones, the ``name`` is passed
        to the predicate initializer.
        """
        predicate_namespace = predicate.split(":", 1)[0]
        if predicate_namespace in self.PARAMETRIC_PREDICATES:
            predicate_arg = predicate.split(":", 1)[1]
            predicate = self.PARAMETRIC_PREDICATES[predicate_namespace](predicate_arg)
        else:
            try:
                predicate = getattr(self, "_" + predicate.replace(":", "_"))
            except AttributeError:
                raise ValueError("Predicate %s not supported" % predicate)

        for server in servers + [None]:
            if server is None:
                # None is a guard that signals our predicate
                # that we want to consume the final response
                # if they had to analyse all servers to come up with one.
                return predicate(None, None, None, None)

            print("> Checking", server)
            with tunnel(server, 22, self._args.PORT) as dest:
                command = (
                    "ssh"
                    " -o UserKnownHostsFile=/dev/null"
                    " -o StrictHostKeyChecking=no"
                    " -p {}"
                    " {}@{}".format(dest[1], self._args.USER, dest[0])
                )
                if self._args.IDENTITY:
                    command += " -i {}".format(self._args.IDENTITY)
                if predicate(server, dest, self._args.USER, command) is True:
                    return server

    def _mongodb_secondary(self, server, dest, user, command):
        """Check that the host we are trying to connect to is a mongodb secondary."""
        if server is None:
            raise RuntimeError("Unable to detect any mongodb secondary")

        command = (
            command
            + """ 'mongo --ssl --sslAllowInvalidCertificates --quiet --eval "rs.status()[\\\""myState\\\""]"'"""
        )
        res = (
            subprocess.check_output(command, shell=True)
            .strip()
            .splitlines()[-1]
            .decode("ascii")
        )
        return res == "2"

    def _mongodb_primary(self, server, dest, user, command):
        """Check that the host we are trying to connect to is a mongodb primary."""
        if server is None:
            raise RuntimeError("Unable to detect any mongodb primary")

        command = (
            command
            + """ 'mongo --ssl --sslAllowInvalidCertificates --quiet --eval "rs.status()[\\\""myState\\\""]"'"""
        )
        res = (
            subprocess.check_output(command, shell=True)
            .strip()
            .splitlines()[-1]
            .decode("ascii")
        )
        return res == "1"

    class _DetectHotZZ9Dataset(object):
        """Check that the host has the most recent dataset hot copy."""

        def __init__(self, dataset_id):
            self._dataset_id = dataset_id
            self._timestamps = []

        def __call__(self, server, dest, user, command):
            # Caller provided a dataset to analyse
            dataset_path = "/scratch0/zz9data/hot/%s/%s" % (
                self._dataset_id[:2],
                self._dataset_id,
            )

            if server == dest == user == command == None:
                # Caller asked for which of all the analysed servers
                # owns the most recent lease.
                try:
                    timestamp, server = sorted(self._timestamps, reverse=True)[0]
                except IndexError:
                    print("\n>>> no hot copy of dataset available\n")
                    return None
                else:
                    print(
                        "\n>>> Dataset available in %s at %s\n" % (dataset_path, server)
                    )
                    return server

            # Stat dataset copy itself.
            try:
                stat_command = command + """ "sudo bash -c 'stat -c %Y {}'" """.format(
                    dataset_path
                )
                res = subprocess.check_output(stat_command, shell=True).strip()
            except subprocess.CalledProcessError:
                # no hot copy of the dataset.
                return None
            last_modified = max(res.split())
            self._timestamps.append((last_modified, server))

            # Then stat dataset dirty files, to check most recent modification.
            try:
                stat_command = (
                    command
                    + """ "sudo bash -c 'stat -c %Y {}/__zz9_dirty__*'" """.format(
                        dataset_path
                    )
                )
                res = subprocess.check_output(stat_command, shell=True).strip()
            except subprocess.CalledProcessError:
                # no hot copy of the dataset.
                return None
            last_modified = max(res.split())
            self._timestamps.append((last_modified, server))

            return None
