# Belgian Federal Parliament Scraper & API
[![Netlify Status](https://api.netlify.com/api/v1/badges/2cbbf08b-eacf-400e-9fcd-ebaafd7ebb5e/deploy-status)](https://app.netlify.com/sites/sleepy-albattani-62fa38/deploys)
[![Build the API, Create Release and Deploy to Netlify](https://github.com/laurensdeb/Federal-Parliament-Scraper/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/laurensdeb/Federal-Parliament-Scraper/actions/workflows/main.yml)

This library provides a scraper based on the Python library Beautiful Soup for the website and meeting notes of the Belgian Federal Parliament. The scraper can currently provide information on the plenary meetings for the sessions between 2007 and now, details on the votes that occurred and the members. We also provide a [hosted version](https://parlement.thundr.be) of the JSON API generated using this library, documentation on this API still is a work-in-progress but the code can serve as documentation if necessary?
## Functionality
- Obtain an overview of all the plenary meetings for a given session
- Get the party affiliation, province and language for the members in the federal parliament during a specified session.
- For each plenary meeting, obtain the meeting topics and votes that occurred during the meeting.
- Support for general votes and votes per language group (i.e. for cases where a majority in both groups is needed).
- Get the names and party affiliation of voters.

## Future functionality
- Get committee meetings and votes in a similar API interface
- Provide statistical information on the occurence of the names of the different parliament members in a specific meeting.
- Allow end users to not only get titles of the meeting topics but also the notes of the discussion itself.

## Getting started
Have a look at `demo.py` to get started.

## Sponsors
The Federal Parliament API is hosted by Netlify and Cloudflare, without the free services provided by these valued partners we wouldn't be able to exist.

  <a href="https://www.netlify.com">
    <img src="https://www.netlify.com/img/global/badges/netlify-color-accent.svg" alt="Deploys by Netlify" />
  </a>
