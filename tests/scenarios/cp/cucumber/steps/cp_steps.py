import subprocess
from pathlib import Path

from behave import given, then, when


@given('a file named "{filename}" with content "{content}"')
def step_impl_given_file_with_content(context, filename, content):
    Path(filename).write_text(content)


@given('no file named "{filename}" exists')
def step_impl_no_file(context, filename):
    if Path(filename).exists():
        Path(filename).unlink()


@when('I run "cli-copy {src} {dest}"')
def step_impl_run_cli_copy(context, src, dest):
    try:
        context.result = subprocess.run(
            ["cargo", "run", "--", src, dest],
            text=True,
            capture_output=True,
            check=False,
        )
    except Exception as e:
        context.result = e


@then('a file named "{filename}" should exist')
def step_impl_file_should_exist(context, filename):
    assert Path(filename).exists(), f"{filename} does not exist"


@then('its content should be "{expected_content}"')
def step_impl_check_file_content(context, expected_content):
    with open("destination.txt", "r") as f:
        content = f.read()
    assert (
        content == expected_content
    ), f"Expected '{expected_content}', got '{content}'"


@then("the command should fail")
def step_impl_command_should_fail(context):
    assert context.result.returncode != 0, "Expected non-zero exit code"


@then('the content of "{filename}" should be "{expected_content}"')
def step_impl_specific_file_content(context, filename, expected_content):
    content = Path(filename).read_text()
    assert (
        content == expected_content
    ), f"Expected '{expected_content}', got '{content}'"
