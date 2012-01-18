import sublime, sublime_plugin, os, re

class FileNameComplete(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        completions = []
        sel = view.sel()[0].a

        if "string" in view.syntax_name(sel):
            pass
        elif "/" in view.substr(sublime.Region(sel-2,sel)):
            pass
        else:
            return []

        this_dir = os.path.split(view.file_name())[0] + "/"

        this_dir += view.substr(view.extract_scope(sel-1)).replace('\"','') # strings are returned in quotes

        dir_files = os.listdir(this_dir)
        for d in dir_files:
            if not '.' in d:
                d += '/'
            completions.append(d)

        return [(x, x) for x in list(set(completions))]