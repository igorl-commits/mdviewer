# File association: "Open with" entry only, never the default .md handler

`install.bat` registers mdviewer under `HKCU\Software\Classes\Applications\mdviewer.exe`
(shows up in "Open with" for `.md` files) rather than setting it as the
default handler for `.md`. This is deliberate: a viewer tool shouldn't
silently take over an association a user may already have pointed at
another app (VS Code, Obsidian, Typora, etc.). `HKCU`-scoped registration
also means no admin rights are required and no other user account on the
machine is affected.
