# Google Jobs Scraper

This project is a web scraper designed to extract job listings from Google Job Search using Playwright. It is built with TypeScript and aims to operate in a realistic mode to avoid detection by anti-bot measures.

## Features

- Scrapes job listings from Google Job Search.
- Handles CAPTCHA challenges.
- Extracts job data including title, company, location, and posted date.
- Configurable settings for scraping behavior.
- Unit tests for core functionalities.

## Project Structure

```
google-jobs-scraper
├── src
│   ├── scrapers
│   │   ├── googleJobsScraper.ts      # Main scraper for Google Jobs
│   │   └── baseScraper.ts             # Base class for scrapers
│   ├── types
│   │   ├── jobData.ts                 # Job data structure
│   │   └── scraperConfig.ts            # Scraper configuration settings
│   ├── utils
│   │   ├── selectors.ts                # CSS selectors for scraping
│   │   ├── browserConfig.ts            # Browser configuration for Playwright
│   │   └── fileHandler.ts              # File handling utilities
│   ├── config
│   │   └── settings.ts                 # Configuration settings
│   └── index.ts                        # Entry point of the application
├── tests
│   ├── scrapers
│   │   └── googleJobsScraper.test.ts   # Unit tests for GoogleJobsScraper
│   └── utils
│       └── fileHandler.test.ts         # Unit tests for file handling utilities
├── data
│   └── .gitkeep                        # Keeps the data directory in version control
├── package.json                        # NPM configuration file
├── tsconfig.json                       # TypeScript configuration file
├── playwright.config.ts                # Playwright configuration settings
└── README.md                           # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/google-jobs-scraper.git
   cd google-jobs-scraper
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Ensure you have Playwright installed:
   ```
   npx playwright install
   ```

## Usage

To run the scraper, execute the following command:

```
npx ts-node src/index.ts --query "your job query" --location "your location"
```

Replace `"your job query"` and `"your location"` with your desired search terms.

## Running Tests

To run the unit tests, use the following command:

```
npm test
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.