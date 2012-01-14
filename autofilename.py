import sublime, sublime_plugin, os, re

class FileNameComplete(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        completions = []
        sel = view.sel()[0].a

        if "string" in view.syntax_name(sel):
            pass
        elif "./" in view.substr(sublime.Region(sel-3,sel)):
            pass
        else:
            return []

        this_file = view.file_name()
        dir_len = this_file.rfind('/') #(for OSX)

        if not dir_len > 0:
            dir_len = this_file.rfind('\\') #(for Windows)
        
        this_dir = this_file[:(dir_len + 1)] # + 1 for the '/'
        this_dir += view.substr(view.extract_scope(sel-1)).replace('\"','') # strings are quoted

        print this_dir

        dir_files = os.listdir(this_dir)
        for d in dir_files:
            if not '.' in d:
                d += '/'
            completions.append(d)

        return [(x, x) for x in list(set(completions))]