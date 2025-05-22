import { spawn, type ChildProcessWithoutNullStreams } from "child_process";
import puppeteer from "puppeteer";

const SCREENSHOT_FILE = "langgraph-test-result.png";

/**
 * Simple smoke test for langgraph CLI
 * This script:
 * 1. Launches the langgraph CLI
 * 2. Uses Puppeteer to test that orchestrator stops at human input from gatherer
 */
async function runTest(): Promise<void> {
  console.log("Starting langgraph CLI smoke test...");

  // Launch the langgraph CLI
  langgraphProcessRef = spawn(
    "uv",
    [
      "run",
      "--env-file",
      ".env",
      "--",
      "langgraph",
      "dev",
      "--port",
      "8080",
      "--no-browser",
      "--no-reload",
    ],
    {
      cwd: "../../../",
      stdio: ["pipe", "pipe", "pipe"],
      shell: true,
    }
  );

  // Collect stdout
  let output = "";
  langgraphProcessRef.stdout.on("data", (data: Buffer) => {
    output += data.toString();
    console.log(`CLI Output: ${data}`);
  });

  // Collect stderr
  langgraphProcessRef.stderr.on("data", (data: Buffer) => {
    console.error(`CLI Error: ${data}`);
  });

  langgraphProcessRef.on("close", (code, signal) => {
    console.log(`child process terminated due to receipt of signal ${signal}`);
  });

  // Wait for CLI to initialize and server to start (adjust timeout as needed)
  console.log("Waiting for langgraph server to start...");
  await new Promise((resolve) => setTimeout(resolve, 5000));

  try {
    // Launch browser for testing
    console.log("Launching browser for testing...");
    const viewport = { width: 2000, height: 1000 };
    const browser = await puppeteer.launch({
      headless: true,
      slowMo: 10,
      args: [
        "--no-sandbox",
        `--window-size=${viewport.width},${viewport.height}`,
      ],
      defaultViewport: viewport,
    });

    const page = await browser.newPage();

    // Navigate to the langgraph server
    console.log(
      "Navigating to https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8080"
    );
    await page.goto(
      "https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8080",
      {
        waitUntil: "networkidle2",
        timeout: 30_000,
      }
    );
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // Verify the page loaded successfully
    const pageTitle = await page.title();
    console.log(`Page title: ${pageTitle}`);

    let testPassed = false;

    await page.waitForSelector("div ::-p-text('agent_template')", {
      timeout: 10_000,
    });
    await page.screenshot({ path: SCREENSHOT_FILE });
    await page.click("text=agent_template");
    await new Promise((resolve) => setTimeout(resolve, 2000));

    await page.screenshot({ path: SCREENSHOT_FILE });
    await page.click("text=orchestrator");
    await new Promise((resolve) => setTimeout(resolve, 2000));

    await page.screenshot({ path: SCREENSHOT_FILE });
    await page.click("text=Message");
    await page.type("div[contenteditable=true]", "I want to build a website");

    await page.screenshot({ path: SCREENSHOT_FILE });
    await page.click("text=Submit");
    await new Promise((resolve) => setTimeout(resolve, 5000));

    await page.screenshot({ path: SCREENSHOT_FILE });
    try {
      // Look for the Humnan Interrupt label
      await page.waitForSelector(
        "span ::-p-text('Interrupt')"
      );

      // Look for the Continue or Resume button
      try {
        await page.waitForSelector("button ::-p-text('Continue')", {
          timeout: 10_000,
        });
      } catch (e) {
        await page.waitForSelector("button ::-p-text('Resume')", {
          timeout: 10_000,
        });
      }
      testPassed = true;
    } catch (e) {
      testPassed = false;
      console.error(`Graph was not interrupted with human feedback: ${e}`);
    }

    console.log(testPassed ? "TEST PASSED ✅" : "TEST FAILED ❌");

    await browser.close();

    // Kill the langgraph process
    await ensureProcessKilled();

    process.exit(testPassed ? 0 : 1);
  } catch (error) {
    console.error("Test error:", error);
    await ensureProcessKilled();
    process.exit(1);
  }
}

// Process reference to ensure it can be killed from anywhere
let langgraphProcessRef: ChildProcessWithoutNullStreams | null = null;

// Function to ensure the process is killed
function ensureProcessKilled(): Promise<void> {
  return new Promise<void>((resolve) => {
    if (langgraphProcessRef) {
      console.log("Killing langgraph process...");
      try {
        // Try to kill the process with SIGTERM first
        langgraphProcessRef.kill("SIGTERM");

        // Also try to kill any child processes that might have been spawned
        if (langgraphProcessRef.pid !== undefined) {
          console.log(
            `Killing process tree for PID ${langgraphProcessRef.pid}...`
          );
          if (process.platform === "win32") {
            // On Windows, use taskkill to kill the process tree
            spawn("taskkill", [
              "/pid",
              langgraphProcessRef.pid.toString(),
              "/f",
              "/t",
            ]);
          } else {
            // On Unix-like systems, use pkill to kill the process group
            // Try multiple approaches to ensure the process is killed
            spawn("pkill", ["-P", langgraphProcessRef.pid.toString()]);
            spawn("kill", ["-9", langgraphProcessRef.pid.toString()]);

            // Also try to kill any processes using port 8080
            const lsofProcess = spawn("lsof", ["-ti:8080"]);
            lsofProcess.stdout.on("data", (data) => {
              const pids = data.toString().trim().split("\n");
              pids.forEach((pid: string) => {
                if (pid) {
                  console.log(`Killing process on port 8080: ${pid}`);
                  spawn("kill", ["-9", pid]);
                }
              });
            });
          }
        }

        // If process is still running after a short delay, force kill with SIGKILL
        setTimeout(() => {
          try {
            if (langgraphProcessRef) {
              console.log(
                "Process still running, force killing with SIGKILL..."
              );
              langgraphProcessRef.kill("SIGKILL");
            }
          } catch (innerError) {
            console.error("Error force killing process:", innerError);
          } finally {
            langgraphProcessRef = null;
            resolve();
          }
        }, 2000);
      } catch (error) {
        console.error("Error killing process:", error);
        langgraphProcessRef = null;
        resolve();
      }
    } else {
      resolve();
    }
  });
}

// Handle unexpected termination
process.on("SIGINT", async () => {
  console.log("Received SIGINT. Cleaning up...");
  await ensureProcessKilled();
  process.exit(0);
});

process.on("SIGTERM", async () => {
  console.log("Received SIGTERM. Cleaning up...");
  await ensureProcessKilled();
  process.exit(0);
});

process.on("uncaughtException", async (error) => {
  console.error("Uncaught exception:", error);
  await ensureProcessKilled();
  process.exit(1);
});

// Run the test
runTest().catch(async (error) => {
  console.error("Unhandled error:", error);
  await ensureProcessKilled();
  process.exit(1);
});
