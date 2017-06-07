
Changelog
=========

1.2.3
-----

- Changed reports to generate as asynchronous background tasks
- Changed reports to be sent via the password email instead of downloaded through browser
- Added new fields to reports
- Various changes and fixes to reports
- Changed Aggregates - Rewards Data Per Streak Type to match clarified spec
- Added a whole lot of translations
- Added campaign information to shared badges

1.2.2
-----

- Changed challenge push notification conditions and serializable name
- Include Twitter attribution info in badges page
- Removed tags from tip articles
- Added styling and download buttons to shared badge pages
- Removed debug prints to prevent spamming logs
- Added initial savings value to Goal model
- Sorted tips by last edit date instead of last published date
- Return 404 instead of errors if free text challenge participants are not found

1.2.0
-----

- Added more backend support for budgeting feature
- Changes and fixes to reports

1.0.4
-----

- Implemented Budget retrieve

1.0.3
-----

- Fixes to reporting and zipping

1.0.2
-----

- Changes to Budget to allow for Expense creation
- Implemented encrypted report export and password emailing functionality

1.0.1
-----

- Added Challenge Prize field
- Added Budget and Expenses models
- Implemented Wagtail report pages

1.0.0
-----

- Public release

0.1.4
-----

- Implemented Ad Hoc Notifications
- Implemented Challenge Reminder Notification
- Implemented Challenge Completion Reminder Notification
- Implemented Goal Deadline Missed Notification
- Changed Weekly Target from calculated property to db field

0.1.3
-----

- Implemented endpoint for use in pre-fetching badge images
- Changed weekly calculations from Monday-Sunday window to counted from starting date

0.1.2
-----

- Implemented On Track Badges
- Implemented Challenge Participation Badge
- Implemented Challenge Winning Badge

0.1.1
-----

- Implemented Survey drafts
- Aggregating users who have selected a Goal Prototype 
- Implemented Participant admin interface for reviewing Challenge entries

0.0.15
------

- Fixed HTTP 500 when removing Tips from favourites

0.0.14
------

- Tips Navigation arrow looks active even if there is only one page
- Added tests for updating User first name
- Exposing Picture Challenge question text via endpoint
