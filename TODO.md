- Send Area
  - Bindings: ctrl-w/a/e, alt-shift-i/a
  - Markdown
  - Spell check?
  - Fix first line break hiding first line
  - Send, upload and other buttons

- Chat
  - Room name changes: rename tabs
  - Instant message display when sending one without waiting for server
  - Smooth animated scroll
  - up/down normal scroll, alt+up/down or something for message-message scroll
  - fix blank lines
  - fix scroll up history
  - Fix crash when trying to chat with System Alert or having to accept its room
    invite for new account
  - Rooms topic

- Accounts
  - Fix the freeze when logging in,
    thread everywhere where cache info retrieval is needed
  - Delete account from right click
  - Handle user display name changes
  - Room-specific display names
  - Don't expand rows if user collapsed manually
  - Multiple selections
  - Drag and drop to reorder

- Global
  - Float/close dock title bar buttons and bindings
  - Alt+things for invite msg box buttons
  - Lower icons brightness to match the text
  - Window icons
  - Focused chat dock in window title
  - Handle errors, avoid crashes
  - Fix floating docks opacity
  - QMainWindow Storing State
  - Tabs middle click to close

- Actions
  - Join and leave room
  - View button shows open/close docks menu
  - Prevent create/join/etc actions if no account logged in,
    gray out buttons and disable shortcuts

Idea to solve freezes:  
Execute whatever we want in threads and emit a signal with a list of args
and kwargs that will be processed by the main thread when we need to modify
the GUI.
