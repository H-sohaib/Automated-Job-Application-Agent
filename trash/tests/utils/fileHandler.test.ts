import { saveJobs, readJobs } from '../../src/utils/fileHandler';
import fs from 'fs';

describe('File Handler Utility Functions', () => {
    const testFilePath = 'testJobs.json';
    const testJobsData = [
        {
            title: 'Software Engineer',
            company: 'Tech Corp',
            location: 'Remote',
            link: 'http://example.com/job1',
            posted_date: '2023-10-01'
        },
        {
            title: 'Data Scientist',
            company: 'Data Inc',
            location: 'New York',
            link: 'http://example.com/job2',
            posted_date: '2023-10-02'
        }
    ];

    afterEach(() => {
        if (fs.existsSync(testFilePath)) {
            fs.unlinkSync(testFilePath);
        }
    });

    test('should save jobs to a JSON file', () => {
        saveJobs(testJobsData, testFilePath);
        expect(fs.existsSync(testFilePath)).toBe(true);
        
        const savedData = JSON.parse(fs.readFileSync(testFilePath, 'utf-8'));
        expect(savedData).toEqual(testJobsData);
    });

    test('should read jobs from a JSON file', () => {
        fs.writeFileSync(testFilePath, JSON.stringify(testJobsData));
        
        const readData = readJobs(testFilePath);
        expect(readData).toEqual(testJobsData);
    });

    test('should return an empty array if the file does not exist', () => {
        const readData = readJobs('nonExistentFile.json');
        expect(readData).toEqual([]);
    });
});