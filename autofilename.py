import sublime, sublime_plugin, os, re

class FileNameComplete(sublime_plugin.EventListener):

    def prev_has(self, view, string):
        sel = view.sel()[0].a
        return string in view.substr(sublime.Region(sel-1, sel))

    def on_query_completions(self, view, prefix, locations):
        completions = []
        sel = view.sel()[0].a

        if self.prev_has(view, '/') or self.prev_has(view, '\\\\'):
            if "string" in view.scope_name(sel):
                pass
            elif "css" in view.scope_name(sel):
                pass
            elif "sass" in view.scope_name(sel):
                pass
            else:
                return []
        else:
            return []

        this_dir = os.path.split(view.file_name())[0] + os.path.sep

        cur_path = view.substr(view.extract_scope(sel-1))

        if cur_path.startswith(("'","\"")):
            cur_path = cur_path[1:-1]

        this_dir = os.path.join(this_dir, cur_path)

        try:
            dir_files = os.listdir(this_dir)
            for d in dir_files:
                if not '.' in d:
                    d += '/'
                completions.append(d.decode('utf-8'))
            return [(x, x) for x in list(set(completions))]
        except OSError:
            print "AutoFileName: could not find " + this_dir
            return []