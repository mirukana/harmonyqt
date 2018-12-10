- Send Area
  - Bindings: ctrl-w/a/e, alt-shift-i/a
  - Markdown
  - Spell check?
  - Fix first line break hiding first line
  - Send, upload and other buttons

- Chat
  - Instant message display when sending one without waiting for server
  - Smooth animated scroll
  - up/down normal scroll, alt+up/down or something for message-message scroll
  - fix blank lines
  - fix scroll up history
  - Rooms topic

- Accounts
  - Fix the freeze when logging in,
    thread everywhere where cache info retrieval is needed
  - Don't expand rows if user collapsed manually
  - Drag and drop to reorder
  - Show error box when accepting invite for a gone room 
  - Accept/decline invite in context menu
  - Confirmation dialog when leaving a private room
  - Del key
  - Change display name (+F2)

- Global
  - Properly log off accounts when closing the client
  - Use rgba opacity instead of black levels for CSS
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
  - Join room & direct chat dialogs
  - View button shows open/close docks menu
  - Prevent create/join/etc actions if no account logged in,
    gray out buttons and disable shortcuts

Idea to solve freezes:  
Execute whatever we want in threads and emit a signal with a list of args
and kwargs that will be processed by the main thread when we need to modify
the GUI.
