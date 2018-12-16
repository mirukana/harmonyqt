- Major version goals:
  - 0.5: E2E
  - 0.6: Room members pane, avatars
  - 0.7: Status, presence, receipts

- General
  - Rename project to Harmony, forget about old harmony
  - Handle bad events
  - Handle errors, avoid crashes
  - Properly log off accounts when closing the client
  - QMainWindow Storing State
  - Tabs middle click to close

- Appearance
  - Background and alignment for chat bubbles
  - Use [Sass](https://pyscss.readthedocs.io/en/latest/) for stylesheet
  - [Application font](https://stackoverflow.com/a/48242138)
  - Use rgba opacity instead of black levels for CSS
  - Always display tabs when there are multiple chats in a window
  - Float/close dock title bar buttons and bindings
  - Lower icons brightness to match the text
  - Window icons
  - Focused chat dock in window title
  - Fix floating docks opacity

- Actions/dialogs
  - Better user ID verifications (@ŧ...)
  - Join room & direct chat dialogs
  - View button should show the open/close docks menu
  - Gray out dialog accept button if creator/sender combo box has no value
  - Multiline fields: modifier+enter = accept dialog

- Chat
  - Max message width when window is bigger than x px
  - Parse links even in HTML messages (e.g. in system alert's greeting)
  - Warn on unknown message format
  - Handle msgtype other than m.text
  - Stylesheet for content, also pygments code blocks:
    <https://github.com/trentm/python-markdown2/wiki/fenced-code-blocks>
  - Smooth animated scroll
  - Rooms topic
  - Invite to current room action binding
  - Check for Matrix max mesage size

  - Send Area
    - Bindings: ctrl-w/a/e, alt-shift-i/a
    - Spell check?
    - Send, upload and other buttons

- Accounts
  - Confirmation dialogs for leave/decline/remove account entries
  - Del key
  - Show error box when accepting invite for a gone room 

  - Don't expand rows if user collapsed manually
  - Drag and drop to reorder

  - Fix the small freeze when logging in,
    thread everywhere where cache info retrieval is needed
