- Major goals:
  - E2E with device verification
  - Custom "tilling widget manager" to replace docking system
  - Make non-core modules work as addon subpackages that can be disabled
  - Room members pane, avatars
  - Status, presence, receipts

- General
  - Indicator when connection drops
  - Turn `<pre>` tags into normal paragraphs with a custom class,
    to prevent Qt's styling which doesn't respect word wrapping
  - Turn `<blockquote>` into table cells so we can apply border
  - Fix "replay attack" when opening the same encrypted room in two clients
  - Move stuff to App instead of MainWindow when it makes sense
  - Use os.PathLike
  - Fix click on tree arrow
  - Handle bad events
  - Properly log off accounts when closing the client
  - QMainWindow Storing State
  - `--help` for [opts](http://doc.qt.io/qt-5/qapplication.html#QApplication),
   [opts](http://doc.qt.io/qt-5/qguiapplication.html#QGuiApplication)

- Commands
  - Update commands module docstring
  - Don't parse links in code blocks
  - Support `--` option
  - Room power levels, kick, ban, leave, join, set canon alias, set avatar,
    set "who can read history"
  - Fingerprints/devices
  - autorun: error line number

- Appearance
  - MessageDisplay left-right padding
  - Dialog box icons to replace ugly system ones
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
  - Better user ID verifications (@ŧ...), same function for /eval, login, etc
  - Join room & direct chat dialogs
  - View button should show the open/close docks menu
  - Gray out dialog accept button if creator/sender combo box has no value
  - Multiline fields: modifier+enter = accept dialog

- Chat
  - Max message width when window is bigger than x px
  - Keep x most recent messages loaded, pop out oldests unless user is
    scrolled up enough
  - Warn on unknown message format
  - Handle msgtype other than m.text
  - Stylesheet for content, also pygments code blocks:
    <https://github.com/trentm/python-markdown2/wiki/fenced-code-blocks>
  - Smooth animated scroll
  - Rooms topic
  - Invite to current room action binding
  - Check for Matrix max mesage size
  - Linkify Matrix user IDs

  - Send Area
    - Catch and store messages that can't be sent yet due to connection issue

    - More keybinds
    - Spell check?
    - Send, upload and other buttons
    - Up/down for last messages

- Accounts
  - Heartbeat, detect when matrix sync is hanging after net drop
  - Confirmation dialogs for leave/decline/remove account entries
  - Del key
  - Show error box when accepting invite for a gone room 

  - Don't expand rows if user collapsed manually
  - Drag and drop to reorder
