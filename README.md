# De Kamer - La Chambre Scraper
This library provides a scraper based on the Python library Beautiful Soup for the website and meeting notes of the Belgian Federal Parliament. The scraper can currently provide information on the plenary meetings for the sessions between 2007 and now, details on the votes that occurred and the members.

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

## Imminent To-Do's
- [ ] Complete the files in /data/composition to also contain information on members who didn't serve a full term in the parliament
- [ ] Improve the class structure of Votes
- [ ] Additional documentation