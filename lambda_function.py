import json
import os

import googleapiclient.discovery
import smartsheet
from smartsheet.models import Cell, Row, Column

# Set up the Smartsheet client
SMARTSHEET_LINK_COLUMN_ID=123
SMARTSHEET_VIEWS_COLUMN_ID=456
SMARTSHEET_SHEET_ID="789"
smartsheet_token = os.environ.get('SMARTSHEET_TOKEN')
smartsheet_client = smartsheet.Smartsheet(smartsheet_token)

# Set up the YouTube API client
youtube_api_key = os.environ.get('YOUTUBE_API_KEY')
youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=youtube_api_key)


def _handle_challenge_verification(event):
    print("in the challenge")
    return {
        'statusCode': 200,
        'headers': {
            'Smartsheet-Hook-Response':
                event['headers']['smartsheet-hook-challenge'],
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,GET,POST'
        }
    }


def _handle_unsupported_method():
    return {
        'statusCode': 401,
        'body': json.dumps('Unsupported non-POST method used.')
    }


def _get_view_count_from_google_api(video_link):
    video_id = video_link.split('v=')[1]

    # Get the video details from the YouTube API
    video_response = youtube.videos().list(
        part='statistics',
        id=video_id
    ).execute()

    # Extract the number of views from the video details
    video_stats = video_response['items'][0]['statistics']
    view_count = int(video_stats['viewCount'])

    return view_count


def _update_views_cell(view_count, row_id):
    cell = Cell()
    cell.column_id = SMARTSHEET_VIEWS_COLUMN_ID
    cell.value = view_count
    cell.strict = False

    row = Row()
    row.id = row_id
    row.cells.append(cell)
    
    return smartsheet_client.Sheets.update_rows(SMARTSHEET_SHEET_ID, [row])


def _get_youtube_link_from_row(row_id):
    livestream_sheet = smartsheet_client.Sheets.get_sheet(SMARTSHEET_SHEET_ID)
    cell = None

    for r in livestream_sheet.rows:
        if r.id == row_id:
            for c in r.cells:
                if c.column_id == SMARTSHEET_LINK_COLUMN_ID:
                    cell = c

    # The API says it returns no value if it's empty
    return cell.value


def lambda_handler(event, context):

    print("Received event:" + str(event))
    print("Received context:" + str(context))

    try:
        operation = event['requestContext']['http']['method']

        if operation != 'POST':
            _handle_unsupported_method()
            
        if 'smartsheet-hook-challenge' in event['headers']:
            _handle_challenge_verification(event)
        else:
            # At this point the changed data are stored in event.body.events, here's a sample:
            # {
            # 	"webhookId": 3620337624606596,
            # 	"scopeObjectId": 123,
            # 	"events": [{
            # 		"objectType": "cell",
            # 		"eventType": "updated",
            # 		"rowId": 456,
            # 		"columnId": 789
            # 	}]
            # }

            try:
                body = json.loads(event['body'])
                webhook_events = body['events']
                
                # check if list is empty, do nothing if it is
                for webhook_event in webhook_events:                    
                    row_id = webhook_event['rowId']
                    youtube_link = _get_youtube_link_from_row(row_id)

                    if 'youtube' in youtube_link:
                        view_count = _get_view_count_from_google_api(youtube_link)
                        result = _update_views_cell(view_count, row_id)

            except Exception:
                pass

    except KeyError:
        print("Did not see an HTTP method or request in the context.")
        pass

    
    return {
        'statusCode': 400,
        'body': json.dumps('Did not see an HTTP method or request in the context.')
    }
