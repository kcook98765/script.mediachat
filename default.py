import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib.request
import urllib.parse
import json
import os
import logging

# Define the addon id and get the addon settings
ADDON_ID = 'script.mediachat'
addon = xbmcaddon.Addon(ADDON_ID)
addon_path = addon.getAddonInfo('path')

# Define the ChatGPT endpoint
CHATGPT_ENDPOINT = 'https://api.openai.com/v1/completions'


# Define the function to send the request to ChatGPT
def send_request(title, year, media_type, search_string):
    # Set up logger
    logging.basicConfig(level=logging.INFO)
        
    # Define the prompt for the ChatGPT request
    prompt = f"Please provide information about {media_type} '{title}' ({year}) based on the following prompt: {search_string}"
   
    temperature = int(addon.getSetting('temperature'))
    max_tokens = int(addon.getSetting('max_tokens'))
    api_key = addon.getSetting('api_key')
    
    # Define the request headers and body
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    data = {
        "model": "text-davinci-003",
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    
    # Encode the data as bytes before sending the request
    data_bytes = json.dumps(data).encode('utf-8')
    
    # Send the request to ChatGPT
    req = urllib.request.Request(CHATGPT_ENDPOINT, data_bytes, headers)
    
    log_request(req)
    
    response = urllib.request.urlopen(req)
    
    # Decode the response body into a string
    response_body = response.read().decode('utf-8')
    
    # Parse the response body as JSON
    response_data = json.loads(response_body)
    
    # Concatenate all the choices' text values with a newline character
    response_text = "\n".join([choice['text'] for choice in response_data['choices']])
    
    # Return the concatenated response text
    return response_text

# Define the function to display the search history
def show_search_history(media_type):
    # Define the search history file for the given media_type
    SEARCH_HISTORY_FILE = addon_path + '/search_history_' + media_type + '.txt'
    DEFAULT_SEARCH_HISTORY_FILE = addon_path + '/default_search_history_' + media_type + '.txt'
    
    # Check if the search history file exists
    if not os.path.exists(SEARCH_HISTORY_FILE):
        # if the file does not exist, see if there is a default file to set it up
        if os.path.exists(DEFAULT_SEARCH_HISTORY_FILE):
            # copy the contents of the DEFAULT_SEARCH_HISTORY_FILE to the SEARCH_HISTORY_FILE
            with open(DEFAULT_SEARCH_HISTORY_FILE, 'r') as default_file:
                with open(SEARCH_HISTORY_FILE, 'w') as search_file:
                    search_file.write(default_file.read())
        else:
            # If the file does not exist, create an empty file
            with open(SEARCH_HISTORY_FILE, 'w') as f:
                pass
    # Load the search history from the file
    with open(SEARCH_HISTORY_FILE, 'r') as f:
        search_history = f.read().splitlines()
    
    # Always include a "Type in a new entry..." item at the top of the list
    listitems = [xbmcgui.ListItem("Type in a new entry...")]
    listitems += [xbmcgui.ListItem(search_string) for search_string in search_history]

   
    # Create a list dialog to display the search history
    dialog = xbmcgui.Dialog()
    index = dialog.select('Search History, cancel to enter a new one.', listitems)

    if index is None or index == -1:
        # user canceled
        return 'Exit'

    # If the "Type in a new entry..." item is selected, return None
    if index == 0:
        return None

    # Subtract 1 from the index to account for the "Type in a new entry..." item at the top of the list
    index -= 1
    
    # Return the selected search history item or None
    return search_history[index] if index >= 0 else None


# Define the function to add a search string to the search history
def add_to_search_history(search_string, media_type):
    # Define the search history file for the given media_type
    SEARCH_HISTORY_FILE = addon_path + '/search_history_' + media_type + '.txt'
    
    # Load the search history from the file
    with open(SEARCH_HISTORY_FILE, 'r') as f:
        search_history = f.read().splitlines()
    
    # Check if the search string is already in the search history
    if search_string not in search_history:
        # Add the search string to the search history if it's not already in the list
        search_history.append(search_string)
    
        # Save the updated search history to the file
        with open(SEARCH_HISTORY_FILE, 'w') as f:
            f.write('\n'.join(search_history))



# Define the function to handle the context menu item
def handle_context_menu(title, year, media_type):
    # Define the search history file for the given media_type
    SEARCH_HISTORY_FILE = addon_path + '/search_history_' + media_type + '.txt'
    
    # Display the search history and allow the user to enter a new search string
    search_string = show_search_history(media_type) or xbmcgui.Dialog().input('Enter search string')
    
    if search_string == 'Exit':
        return ''
    
    # Add the search string to the search history
    add_to_search_history(search_string, media_type)
    
    # Send the request to ChatGPT and display the results
    response = send_request(title, year, media_type, search_string)
    dialog = xbmcgui.Dialog()
    dialog.textviewer('MediChat Results', f'{media_type} Title: {title} ({year})\n\nSearch String: {search_string}\n\nResponse: {response}')


def log_request(request):
    xbmc.log(f"Sending request to {request.full_url}", level=xbmc.LOGINFO)  
#    xbmc.log(f"Headers: {request.headers}", level=xbmc.LOGINFO)  
    xbmc.log(f"Body: {request.data}", level=xbmc.LOGINFO)  


if __name__ == '__main__':
    media_type = sys.listitem.getVideoInfoTag().getMediaType()
    title = sys.listitem.getVideoInfoTag().getTitle()
    year = sys.listitem.getVideoInfoTag().getYear()
    handle_context_menu(title, year, media_type)
    
 