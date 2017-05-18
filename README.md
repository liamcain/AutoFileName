AutoFileName Improved
============

Autocomplete Filenames in Sublime Text
--------------------------------------
Do you ever find yourself sifting through folders in the sidebar trying to remember what you named that file? Can't remember if it was a jpg or a png? Maybe you just wish you could type filenames faster. *No more.*

Whether you're making a `img` tag in html, setting a background image in css, or linking a `.js` file to your html (or whatever else people use filename paths for these days...), you can now autocomplete the filename. Plus, it uses the built-in autocomplete, so no need to learn another pesky shortcut.

Features
--------

- Display filenames and folders
- Show dimensions next to image files
- Autoinsert dimensions in img tags (can be disabled in settings)
- Support for both '/' and '\' for all you Windows hooligans

Installation
------------
To install this custom build of AutoFileName using package control<sup>[1](#pc-add-repo)</sup>

1. Open up the command palette (`ctrl+shift+p`), and find `Package Control: Add Repository`. Then enter the URL of this repo: `https://github.com/jsilvermist/AutoFileName/tree/afn-i` in the input field.
2. Open up the command palette again and find `Package Control: Install Package`, and just search for `AutoFileName`. (just a normal install)

If you want to remove this and go back to the default version of AutoFileName, find `Package Control: Remove Repository`, and select the repository to remove it. You can now reinstall the default version.

Usage
-----
**Nothing!**

For example:

If you are looking to autocomplete an image path in an HTML `<img>` tag:
    `<img src="../|" />`

AutoFileName will display a list of files without you having to do anything. As you type, the results will narrow. The list will automatically update as you enter a new directory so you don't have to do a thing.

Settings
--------
There are some options now.

Perhaps you're working on a website and all the image files are relative to the project root instead of the Computer's root directory. No worries. Just tell AutoFileName the project root. (More info in the settings file.)

Additionally, if you hate awesomeness, you can turn off some of the automagicalness and use a boring keybinding to activate AutoFileName.

How Can I help?
---------------
- **Got a feature request? Something bugging you and you're about to uninstall it?** Submit a bug report with all your fears, desires, and vulgarity. I'll heartily try to fix the plugin to your specifications... well, I'll consider it.

<a name="pc-add-repo">1</a>: Instructions originally by [math2001](https://github.com/math2001)
