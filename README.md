AutoFileName: Autocomplete Filenames in Sublime Text
=====================================================
Do you ever find yourself sifting through folders in the sidebar trying to remember what you named that file? Can't remember if it was a jpg or a png? Maybe you just wish you could type filenames faster. *No more.*

Whether your making a `img` tag in html, setting a background image in css, or linking a `.js` file to your html (or whatever else people use filename paths for these days...), you can now autocomplete the filename. Plus, it uses the built-in autocomplete, so no need to learn another *pesky* shortcut.

Usage
=====
If you are looking to autocomplete an image path in an HTML `<img>` tag:
```html
    <img src="../|" />
```

Pressing <kbd>ctrl</kbd>+<kbd>space</kbd>, will activate AutoFileName.  I list of available files where be ready to select.

*Looking for an even more automatic and seemless completion?*  Add the following to your User Settings file:
    
    "auto_complete_triggers":
    [
      {
         "characters": "<",
         "selector": "text.html"
      },
      {
         "characters": "/",
         "selector": "string.quoted.double.html,string.quoted.single.html, source.css"
      }
    ]

With this, there's no need to worry about pressing <kbd>ctrl</kbd>+<kbd>space</kbd>, autocompletion with appear upon pressing /.
