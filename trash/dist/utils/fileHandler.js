"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.readFromFile = exports.saveToFile = exports.readJobs = exports.saveJobs = void 0;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const saveJobs = (jobs, filename) => {
    const filePath = path_1.default.isAbsolute(filename)
        ? filename
        : path_1.default.join(__dirname, "../../data", filename);
    const dir = path_1.default.dirname(filePath);
    if (!fs_1.default.existsSync(dir)) {
        fs_1.default.mkdirSync(dir, { recursive: true });
    }
    fs_1.default.writeFileSync(filePath, JSON.stringify(jobs, null, 2), "utf-8");
};
exports.saveJobs = saveJobs;
const readJobs = (filename) => {
    const filePath = path_1.default.isAbsolute(filename)
        ? filename
        : path_1.default.join(__dirname, "../../data", filename);
    if (!fs_1.default.existsSync(filePath)) {
        return [];
    }
    const data = fs_1.default.readFileSync(filePath, "utf-8");
    return JSON.parse(data);
};
exports.readJobs = readJobs;
// Legacy functions for compatibility
exports.saveToFile = exports.saveJobs;
exports.readFromFile = exports.readJobs;
