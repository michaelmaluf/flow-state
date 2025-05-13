#!/bin/bash

# Get the currently active application
active_app=$(osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true')

# Check if the active application is Google Chrome
if [[ "$active_app" == "Google Chrome" ]]; then
    # Get the current URL from Chrome
    chrome_url=$(osascript -e 'tell application "Google Chrome" to get URL of active tab of front window')

    # Extract domain from URL
    if [[ $chrome_url =~ ^https?://([^/]+) ]]; then
        # Get the full domain
        full_domain="${BASH_REMATCH[1]}"
        # Remove www. prefix if present
        clean_domain=${full_domain#www.}
        # Extract base domain without TLD
        base_domain=$(echo "$clean_domain" | sed -E 's/\.[^.]+$//')

        # Special handling for YouTube watch pages
        if [[ $clean_domain == *"youtube.com"* && $chrome_url == *"/watch"* ]]; then
            # Get the title of the video
            video_title=$(osascript -e '
                tell application "Google Chrome"
                    set theTitle to title of active tab of front window
                end tell
            ')
            # Clean up the title (remove " - YouTube" suffix if present)
            video_title=${video_title% - YouTube}
            echo "WEBAPP:$base_domain:$video_title"

        # Special handling for Reddit subreddit pages
        elif [[ $clean_domain == *"reddit.com"* && $chrome_url =~ /r/([^/]+) ]]; then
            # Extract the subreddit name from the regex match
            subreddit_name="${BASH_REMATCH[1]}"
            echo "WEBAPP:$base_domain:$subreddit_name"

        # Default handling for all other websites
        else
            echo "WEBAPP:$base_domain"
        fi
    else
        # Fallback if URL parsing fails
        echo "WEBAPP:Chrome"
    fi
else
    # Output APP: followed by the application name for non-Chrome applications
    echo "APP:$active_app"
fi