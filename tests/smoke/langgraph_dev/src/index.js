"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
Object.defineProperty(exports, "__esModule", { value: true });
var child_process_1 = require("child_process");
var puppeteer_1 = require("puppeteer");
/**
 * Simple smoke test for langgraph CLI
 * This script:
 * 1. Launches the langgraph CLI
 * 2. Uses Puppeteer to test the output
 */
function runTest() {
    return __awaiter(this, void 0, void 0, function () {
        var langgraphProcess, output, browser, page, pageTitle, pageContent, testPassed, error_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    console.log('Starting langgraph CLI smoke test...');
                    langgraphProcess = (0, child_process_1.spawn)('uv run --env-file .env -- langgraph dev --port 8080 --no-browser --no-reload', ['serve'], {
                        stdio: ['pipe', 'pipe', 'pipe'],
                        shell: true
                    });
                    output = '';
                    langgraphProcess.stdout.on('data', function (data) {
                        output += data.toString();
                        console.log("CLI Output: ".concat(data));
                    });
                    // Collect stderr
                    langgraphProcess.stderr.on('data', function (data) {
                        console.error("CLI Error: ".concat(data));
                    });
                    // Wait for CLI to initialize and server to start (adjust timeout as needed)
                    console.log('Waiting for langgraph server to start...');
                    return [4 /*yield*/, new Promise(function (resolve) { return setTimeout(resolve, 5000); })];
                case 1:
                    _a.sent();
                    _a.label = 2;
                case 2:
                    _a.trys.push([2, 10, , 11]);
                    // Launch browser for testing
                    console.log('Launching browser for testing...');
                    return [4 /*yield*/, puppeteer_1.default.launch({
                            headless: false,
                            args: ['--no-sandbox']
                        })];
                case 3:
                    browser = _a.sent();
                    return [4 /*yield*/, browser.newPage()];
                case 4:
                    page = _a.sent();
                    // Navigate to the langgraph server
                    console.log('Navigating to http://localhost:8080');
                    return [4 /*yield*/, page.goto('http://localhost:8080', {
                            waitUntil: 'networkidle2',
                            timeout: 30000
                        })];
                case 5:
                    _a.sent();
                    // Take a screenshot for verification
                    return [4 /*yield*/, page.screenshot({ path: 'langgraph-test-result.png' })];
                case 6:
                    // Take a screenshot for verification
                    _a.sent();
                    console.log('Screenshot saved to langgraph-test-result.png');
                    return [4 /*yield*/, page.title()];
                case 7:
                    pageTitle = _a.sent();
                    console.log("Page title: ".concat(pageTitle));
                    return [4 /*yield*/, page.content()];
                case 8:
                    pageContent = _a.sent();
                    testPassed = pageContent.length > 0;
                    console.log(testPassed ? 'TEST PASSED ✅' : 'TEST FAILED ❌');
                    return [4 /*yield*/, browser.close()];
                case 9:
                    _a.sent();
                    // Kill the langgraph process
                    langgraphProcess.kill();
                    process.exit(testPassed ? 0 : 1);
                    return [3 /*break*/, 11];
                case 10:
                    error_1 = _a.sent();
                    console.error('Test error:', error_1);
                    langgraphProcess.kill();
                    process.exit(1);
                    return [3 /*break*/, 11];
                case 11: return [2 /*return*/];
            }
        });
    });
}
// Run the test
runTest().catch(function (error) {
    console.error('Unhandled error:', error);
    process.exit(1);
});
