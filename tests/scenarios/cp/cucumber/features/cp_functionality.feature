Feature: Copying files using the CLI app

  Scenario: Copy a file successfully
    Given a file named "source.txt" with content "Hello, world!"
    When I run "cli-copy source.txt destination.txt"
    Then a file named "destination.txt" should exist
    And its content should be "Hello, world!"

  Scenario: Fail to copy a non-existent file
    Given no file named "missing.txt" exists
    When I run "cli-copy missing.txt destination.txt"
    Then the command should fail

  Scenario: Overwrite an existing file
    Given a file named "source.txt" with content "New content"
    And a file named "destination.txt" with content "Old content"
    When I run "cli-copy source.txt destination.txt"
    Then the content of "destination.txt" should be "New content" 