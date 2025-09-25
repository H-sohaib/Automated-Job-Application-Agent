import fs from "fs";
import path from "path";
import { JobData } from "../types/jobData";

export const saveJobs = (jobs: JobData[], filename: string): void => {
  const filePath = path.isAbsolute(filename)
    ? filename
    : path.join(__dirname, "../../data", filename);
  const dir = path.dirname(filePath);

  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  fs.writeFileSync(filePath, JSON.stringify(jobs, null, 2), "utf-8");
};

export const readJobs = (filename: string): JobData[] => {
  const filePath = path.isAbsolute(filename)
    ? filename
    : path.join(__dirname, "../../data", filename);

  if (!fs.existsSync(filePath)) {
    return [];
  }

  const data = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(data);
};

// Legacy functions for compatibility
export const saveToFile = saveJobs;
export const readFromFile = readJobs;
