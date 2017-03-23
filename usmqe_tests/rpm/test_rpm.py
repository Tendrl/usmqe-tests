# -*- coding: utf8 -*-

import pytest
import subprocess
import tempfile


LOGGER = pytest.get_logger(__name__, module=True)


def test_repoclosure(rpm_repo, centos_repos):
    cmd = ["repoclosure", "--newest"]
    # configure systemd default repositories
    for name, url in centos_repos.items():
        cmd.append("--repofrompath")
        cmd.append("{},{}".format(name, url))
        cmd.append("--lookaside={}".format(name))
    # configure tendrl repository (passed via rpm_repo fixture)
    cmd.append("--repofrompath")
    cmd.append("tendrl,{}".format(rpm_repo))
    cmd.append("--repoid=tendrl")
    # running repoclosure
    LOGGER.info(" ".join(cmd))
    with tempfile.TemporaryDirectory() as tmpdirname:
        cp = subprocess.run(
            cmd,
            cwd=tmpdirname,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    LOGGER.debug("STDOUT: %s", cp.stdout)
    LOGGER.debug("STDERR: %s", cp.stderr)
    check_msg = "repoclosure return code should be 0 indicating no errors"
    pytest.check(cp.returncode == 0, msg=check_msg)
    # when the check fails, report the error in readable way
    if cp.returncode != 0:
        for line in cp.stdout.splitlines():
            LOGGER.failed(line.decode())
        for line in cp.stderr.splitlines():
            LOGGER.failed(line.decode())


def test_rpmlint(rpm_package):
    rpm_name, rpm_path = rpm_package
    cmd = ["rpmlint", rpm_path]
    # running rpmlint
    LOGGER.info(" ".join(cmd))
    cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    LOGGER.debug("STDOUT: %s", cp.stdout)
    LOGGER.debug("STDERR: %s", cp.stderr)
    # when the check fails, report the error in readable way
    if cp.returncode != 0:
        for line in cp.stdout.splitlines():
            line_str = line.decode()
            if "E: unknown-key" in line_str or line_str.startswith("1 packages"):
                continue
            LOGGER.failed(line_str)


@pytest.mark.parametrize("check_command", [
    # TODO: enable check-sat again when we understand what we are doing wrong
    # "check-sat",
    "check-conflicts",
    ])
def test_rpmdeplint(rpm_package, check_command, rpm_repo, centos_repos):
    rpm_name, rpm_path = rpm_package
    cmd = ["rpmdeplint", check_command]
    # configure systemd default repositories
    for name, url in centos_repos.items():
        cmd.append("--repo")
        cmd.append("{},{}".format(name, url))
    # configure tendrl repository (passed via rpm_repo fixture)
    cmd.append("--repo")
    cmd.append("tendrl,{}".format(rpm_repo))
    # and last but not least: specify the package
    cmd.append(rpm_path)
    # running rpmdeplint
    LOGGER.info(" ".join(cmd))
    cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    LOGGER.debug("STDOUT: %s", cp.stdout)
    LOGGER.debug("STDERR: %s", cp.stderr)
    check_msg = "rpmdeplint return code should be 0 indicating no errors"
    pytest.check(cp.returncode == 0, msg=check_msg)
    # when the check fails, report the error in readable way
    if cp.returncode != 0:
        for line in cp.stderr.splitlines():
            LOGGER.failed(line.decode())