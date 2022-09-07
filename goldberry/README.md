# Goldberry

Goldberry handles cross-cutting concerns and interfaces with Slack.
These include lab management, data organization, job prioritization, lab-level logging, and complex user requests.
It is the only project that interacts with the filesystem on Valinor (aside from miscellaneous scripts).

Goldberry manages the following aspects:
- a priority queue of SauronX submissions to insert into Valar
- announcing events and sending reminders on Slack
- managing raw data on Valinor
