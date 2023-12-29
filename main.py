from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, PreferencesEvent, PreferencesUpdateEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from subprocess import Popen, PIPE
from typing import List
# &uname= means i can add username as default
class Meeting:
    def __init__(self, name, id, password):
        self.name = name
        self.id = id
        self.password = password

saved_meetings = []

class ZoomExtension(Extension):

    def __init__(self):
        super(ZoomExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(PreferencesEvent, PreferencesLoadListener())
        self.subscribe(PreferencesUpdateEvent, PreferencesUpdateListener())

class PreferencesLoadListener(EventListener):
    def on_event(self, event, extension):
        update_saved_meetings(event.preferences['saved_meetings'])

class PreferencesUpdateListener(EventListener):
    def on_event(self, event, extension):
        if event.id == 'saved_meetings':
            update_saved_meetings(event.new_value)

def update_saved_meetings(meetings_string: str) -> List[Meeting]:
    global saved_meetings
    saved_meetings.clear()
    try:
        for meeting_info in meetings_string.split(';'):
            meeting_details = meeting_info.split(':')
            if len(meeting_details) == 2:
                name = meeting_details[0]
                id = meeting_details[1]
                password = ""  # No password provided
                saved_meetings.append(Meeting(name, id, password))
            elif len(meeting_details) == 3:
                name = meeting_details[0]
                id = meeting_details[1]
                password = meeting_details[2]
                saved_meetings.append(Meeting(name, id, password))
            else:
                Popen(['notify-send', "Invalid Format", "Saved meeting format is incorrect. Please use zoom_meeting_name:meeting_id:hashed_password format."], stdout=PIPE, stderr=PIPE)
    except Exception as e:
        Popen(['notify-send', "Error", f"An error occurred while updating saved meetings: {e}"], stdout=PIPE, stderr=PIPE)
        saved_meetings = []


def in_saved_meeting(string: str, meeting: Meeting) -> bool:
    return (
        string.lower() in meeting.name.lower()
        or string.lower() in meeting.id.lower()
        or string.lower() in meeting.password.lower()
    )

class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items = []

        user_inputs = event.get_query().split()

        if len(user_inputs) == 1 or user_inputs[1] in 'new':
            items.append(ExtensionResultItem(icon='images/icon.png',
                                             name='New',
                                             description='Start new meeting',
                                             on_enter=OpenUrlAction('https://zoom.us/startmeeting')))

        if len(user_inputs) == 1:
            for meeting in saved_meetings:
                items.append(ExtensionResultItem(icon='images/icon.png', name='Join %s' % meeting.name,
                                                 description='Join Zoom meeting %s' % meeting.id,
                                                 on_enter=OpenUrlAction(f'zoommtg://zoom.us/join?action=join&confno={meeting.id}&pwd={meeting.password}')))

        if len(user_inputs) > 1:
            meeting_id = user_inputs[1]
            if saved_meetings is None:
                Popen(['notify-send', "Error", "Saved meetings are not properly formatted. Please check the settings."], stdout=PIPE, stderr=PIPE)
            else:
                for meeting in saved_meetings:
                    if in_saved_meeting(meeting_id, meeting):
                        items.append(ExtensionResultItem(icon='images/icon.png', name='Join %s' % meeting.name,
                                                         description='Join Zoom meeting %s' % meeting.id,
                                                         on_enter=OpenUrlAction(f'zoommtg://zoom.us/join?action=join&confno={meeting.id}&pwd={meeting.password}')))

                items.append(ExtensionResultItem(icon='images/icon.png',
                                                 name='Join meeting',
                                                 description='Join Zoom meeting %s' % meeting_id,
                                                 on_enter=OpenUrlAction(f'zoommtg://zoom.us/join?action=join&confno={meeting_id}&pwd={meeting.password}')))

        return RenderResultListAction(items)

if __name__ == '__main__':
    ZoomExtension().run()



