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
var playwright_1 = require("playwright");
var BrowserManager = /** @class */ (function () {
    function BrowserManager() {
        this.browser = null;
        this.context = null;
        this.page = null;
    }
    BrowserManager.prototype.start = function () {
        return __awaiter(this, void 0, void 0, function () {
            var _a, _b, _c;
            return __generator(this, function (_d) {
                switch (_d.label) {
                    case 0:
                        console.log("🚀 Starting browser...");
                        _a = this;
                        return [4 /*yield*/, playwright_1.chromium.launch({
                                headless: false,
                                args: [
                                    "--no-sandbox",
                                    "--disable-dev-shm-usage",
                                    "--start-maximized",
                                    "--disable-blink-features=AutomationControlled", // Disable automation detection
                                ],
                            })];
                    case 1:
                        _a.browser = _d.sent();
                        // Create a new browser context with a custom user agent
                        _b = this;
                        return [4 /*yield*/, this.browser.newContext({
                                userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                                viewport: { width: 1920, height: 1080 },
                            })];
                    case 2:
                        // Create a new browser context with a custom user agent
                        _b.context = _d.sent();
                        _c = this;
                        return [4 /*yield*/, this.context.newPage()];
                    case 3:
                        _c.page = _d.sent();
                        // Set additional headers to mimic a real browser
                        return [4 /*yield*/, this.page.setExtraHTTPHeaders({
                                "Accept-Language": "en-US,en;q=0.9",
                            })];
                    case 4:
                        // Set additional headers to mimic a real browser
                        _d.sent();
                        // Add stealth-like behavior
                        return [4 /*yield*/, this.addStealthFeatures()];
                    case 5:
                        // Add stealth-like behavior
                        _d.sent();
                        console.log("✅ Browser opened!");
                        // Navigate to Google
                        console.log("🌐 Navigating to Google...");
                        return [4 /*yield*/, this.page.goto("https://www.google.com", {
                                waitUntil: "domcontentloaded",
                            })];
                    case 6:
                        _d.sent();
                        console.log("📝 Navigate to your target page, then press ENTER to start scraping...");
                        return [4 /*yield*/, this.waitForUserInput()];
                    case 7:
                        _d.sent();
                        console.log("🤖 Starting scraping logic...");
                        if (this.page) {
                            // await startScraping(this.page);
                        }
                        return [4 /*yield*/, this.close()];
                    case 8:
                        _d.sent();
                        return [2 /*return*/];
                }
            });
        });
    };
    BrowserManager.prototype.addStealthFeatures = function () {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        if (!this.context)
                            return [2 /*return*/];
                        // Remove WebDriver property
                        return [4 /*yield*/, this.context.addInitScript(function () {
                                Object.defineProperty(navigator, "webdriver", { get: function () { return undefined; } });
                            })];
                    case 1:
                        // Remove WebDriver property
                        _a.sent();
                        // Mock plugins and languages
                        return [4 /*yield*/, this.context.addInitScript(function () {
                                Object.defineProperty(navigator, "plugins", {
                                    get: function () { return [1, 2, 3]; },
                                });
                                Object.defineProperty(navigator, "languages", {
                                    get: function () { return ["en-US", "en"]; },
                                });
                            })];
                    case 2:
                        // Mock plugins and languages
                        _a.sent();
                        console.log("🛡️ Stealth features added.");
                        return [2 /*return*/];
                }
            });
        });
    };
    BrowserManager.prototype.waitForUserInput = function () {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                return [2 /*return*/, new Promise(function (resolve) {
                        process.stdin.setRawMode(true);
                        process.stdin.resume();
                        process.stdin.on("data", function () {
                            process.stdin.setRawMode(false);
                            process.stdin.pause();
                            resolve();
                        });
                    })];
            });
        });
    };
    BrowserManager.prototype.close = function () {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        if (!this.browser) return [3 /*break*/, 2];
                        console.log("🔒 Closing browser...");
                        return [4 /*yield*/, this.browser.close()];
                    case 1:
                        _a.sent();
                        _a.label = 2;
                    case 2: return [2 /*return*/];
                }
            });
        });
    };
    return BrowserManager;
}());
// Main execution
function main() {
    return __awaiter(this, void 0, void 0, function () {
        var manager, error_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    console.log("🎯 Job Scraper Starting...");
                    manager = new BrowserManager();
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 3, , 5]);
                    return [4 /*yield*/, manager.start()];
                case 2:
                    _a.sent();
                    return [3 /*break*/, 5];
                case 3:
                    error_1 = _a.sent();
                    console.error("❌ Error:", error_1);
                    return [4 /*yield*/, manager.close()];
                case 4:
                    _a.sent();
                    return [3 /*break*/, 5];
                case 5: return [2 /*return*/];
            }
        });
    });
}
process.on("SIGINT", function () {
    console.log("\n👋 Shutting down...");
    process.exit(0);
});
main();
