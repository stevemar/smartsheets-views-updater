# smartsheets-views-updater

A bit of Python that runs on AWS Lambda and uses the Smartsheet and Google SDKs. It's assumed that there's two columns in a table, one for storing a YouTube URL (`Video Link`) and another for storing views from that video (`Views`).

The code is broken down into a few interesting parts:

1. It accepts the webhook challenge response from Smartsheet.
2. It checks if `Video Link` has been updated with a new URL.
3. It uses the Google SDK to get the views on that video.
4. It uses the Smartsheet SDK to update the `Views` column on the affected row.
