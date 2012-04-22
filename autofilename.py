import sublime, sublime_plugin, os, re

class FileNameComplete(sublime_plugin.EventListener):

    def prev_has(self, view, string):
        sel = view.sel()[0].a
        return string in view.substr(sublime.Region(sel-1, sel))

    def is_empty_string(self,view,sel):
        string = view.substr(view.extract_scope(sel))
        return len(string) < 3

    def on_query_completions(self, view, prefix, locations):
        completions = []
        valid_scopes = ["string", "css", "sass", "scss"]
        backup = []
        sel = view.sel()[0].a

        for x in view.find_all("[a-zA-Z]+"):
                    backup.append(view.substr(x))

        if not any(s in view.scope_name(sel) for s in valid_scopes):
            return backup
        if not (self.is_empty_string(view,sel) or self.prev_has(view, '/') or self.prev_has(view, '\\\\')):
            return backup

        this_dir = os.path.split(view.file_name())[0] + os.path.sep
        cur_path = view.substr(view.extract_scope(sel-1)).replace('\r\n', '\n').split('\n')[0]

        if cur_path.startswith(("'","\"","(")):
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
            return backup